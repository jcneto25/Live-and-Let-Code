# Plano para complementar a implementação LLC 2.0

## 0. Status de execução verificado (2026-10-09)

> **Origem desta seção:** verificação do **código real** (não de mensagens de commit nem de afirmações registradas em sessão) contra as Fases 1–6 deste plano, para permitir a continuidade. Toda afirmação abaixo tem arquivo/comando de evidência. O commit `d4801e3` ("LLC 2.0: complement integration (Fases 1-6)") foi tratado como **hipótese, não como prova**.

**Método.** Inspeção direta de `.ace/scripts/**` (busca por símbolos) + execução das 3 suítes de teste do §8.2 com o *exit code* preservado (`PIPESTATUS`).

### 0.1 Resultado por fase

| Fase | Objetivo | Status real | Evidência |
|---|---|---|---|
| **F1** | R-2 — replay → Decision Engine | ❌ **Esqueleto; não integra** | `llc_harness/replay.py` define `_USE_LLC2_REPLAY` (L51) e `_classify_v2_routing()` (L79) e importa `decide`, `DecisionState`, `HardEvalResult` (L40-45) — mas a busca por `decide(` / `DecisionState(` / `_classify_v2_routing(` só encontra a própria `def`. **Zero chamadas**: tarefas 1.3–1.7 não implementadas. |
| **F2** | R-4 — `impact_of`-first no Delta | ❌ **Não iniciada** | `should_use_semantic_impact` e `residual_impact` **não existem em `.py` algum** (a premissa deste plano está errada — ver §0.2). `llc_delta/report.py` importa apenas `re`/`unicodedata`/`.paths`; nenhum `GraphEngine`/`impact_of`. Existe `llc2/delta.py::delta_semantic_impact()`, mas ela só é chamada pelos próprios testes. |
| **F3** | R-5 — DecisionRecord versionado | 🔶 **Parcial** | Infra pronta: `llc_trace/{decisions,events,hashing,stats}.py`. Porém `replay.py::_trace_early_commitment` grava **sem** `policy_version`, `thresholds_hash` e `question_set.hash` — exatamente os campos exigidos pelo critério GO de §4.2. |
| **F4** | R-3 — whitelist NodeMachine | ✅ **Mantido global — decisão humana (2026-10-09, ver §5)** | `NODEMACHINE_WHITELIST`/`NODEMACHINE_PILOT_STEPS` inexistentes. A guarda do piloto `canonical_id(step) == "11.2"` foi **removida** e `LLC2_STATECHART` tem default **`"1"`** em `llc_harness/pipeline.py:205` → NodeMachine é criada para **todos** os steps. **Aceito pela decisão de 2026-10-09** (maior controle determinístico); o critério "Sem habilitar global" do §5.2 é superado. |
| **F5** | R-6 — capabilities tool-agnostic + doc | 🔶 **Parcial** | `llc2/capabilities.py` mapeia **somente `claude-code`** (8 ocorrências; **0** de `opencode`/`codex`/`cursor`) → tarefa 5.1 não feita. `generate_permission_profile()` **existe** (L115) mas **não é chamada** por `pipeline.py` (0 ocorrências de `profile`) → tarefa 5.2 não feita. `detect_modified_file_violations` **não existe** → tarefa 5.3 apoiada em premissa falsa. O doc foi criado, mas é placeholder (§0.3). |
| **F6** | R-7 baseline + R-1 auditoria | ❌ **Não feito** | Nenhuma ocorrência de `LLC2_BASELINE` nem de `baseline.jsonl` no código → tarefas 7.1/7.2 ausentes. `docs/audit/llc2-integration-audit.md` existe, mas é placeholder (§0.3) → tarefa 7.3 não cumprida. |

**Resumo (atualizado):** F4 **decidida** (manter NodeMachine — §5). Ainda sem critério GO cumprido: **F1, F2, F6** ❌/divergentes e **F3, F5** parciais. O bloqueio de testes foi **removido** (§0.4, 224/224).

### 0.2 Premissas deste plano que se revelaram falsas

| Onde o plano assume | Realidade verificada | Impacto |
|---|---|---|
| §3 (F2) — "`llc_delta/skip.py` já tem `should_use_semantic_impact()` e `residual_impact()` (prontos)" | **Não existem.** `skip.py` só tem `ALWAYS_RUN` e `is_step_skipped` | F2 precisa **criar** os helpers antes de plugá-los (ou usar `GraphEngine.impact_of()` diretamente) |
| §6 (F5.3) — "Manter `detect_modified_file_violations()` após agent" | **Não existe** em nenhum `.py` | A "rede de segurança" declarada em §6.2 não está no código |
| §8.2 — "Testes existentes: 193 passed" | Medido: **224 coletados, 219 passando, 5 falhando** | O baseline numérico do plano está errado |

### 0.3 Artefatos placeholders (defeito de escrita)

Dois documentos entregues como "feitos" contêm uma única linha, com `\n` **literais** (sequências de escape não interpretadas — sintoma de geração sem escape correto):

| Arquivo | Conteúdo atual |
|---|---|
| `docs/architecture/capability-control.md` | `# Capability Control\n\nPrevenção via perfil por estado + detecção post-hoc...\n` (1 linha física) |
| `docs/audit/llc2-integration-audit.md` | 5 linhas físicas, incluindo `Estado: Fase 1-5 complementadas. 248 testes verdes.` — **afirmação falsa** (medido: 219/224 com 5 falhas) |

Ambos precisam ser **reescritos** para satisfazer as tarefas 5.4 e 7.3.

### 0.4 Suíte de replay — ✅ RESOLVIDA (era o bloqueio)

> ✅ **Resolvida em 2026-10-09 (sessão `2026-10-09-002`):** `20 passed`, exit 0. Causas encontradas: (1) `_dict_to_decision_record` (em `llc_replay/verify.py`) passava `policy=config` sem a chave `version`, exigida por `is_replayable()` — **todo** registro virava "não replayável"; (2) `_dict_to_jev_result` usava assinaturas inexistentes (`JevChoice` sem `probabilities`, `JevScore` sem `levels`, `JevNoul` com `confidence`, `JevResult` com `probabilities`); (3) o replay ignorava a evidência **gravada no próprio registro** (Passagem 3 §12: `decide(record.hard_eval, record.jev, …)`); (4) `attempt_replay` devolvia a decisão recomputada em vez da **decisão do registro** (Passagem 2 §1.5); e (5) `classify_task_v2` não integrava replay nem expunha a key `replayed`. Abaixo, o diagnóstico original (mantido como histórico).

`llc_replay/tests/test_verify.py` → ~~**5 failed / 15 passed**~~ → **20 passed** (exit code 0). O arquivo de teste foi **adicionado no mesmo commit** `d4801e3` que implementou o replay (`git log --diff-filter=A`), ou seja: os testes foram escritos e a implementação **nunca chegou ao GREEN**. É o pré-requisito de qualquer avanço.

| Testes | Causa raiz |
|---|---|
| 4 testes (`test_replay_integration_with_classifier`, `test_replay_fallback_to_jev_when_no_record`, `test_replay_fallback_to_jev_when_hash_mismatch`, `test_replay_with_different_automation_levels`) | `TypeError: FakeJevTransport.__init__() got an unexpected keyword argument 'choice'` — o teste chama `FakeJevTransport(choice=..., confidence=...)`, mas `llc2/jev_adapter.py:209` exige `FakeJevTransport(answers, model=..., usage=..., fail_times=..., drop=...)`. **Contrato teste↔implementação desalinhado.** |
| `test_attempt_replay_success` | `assert False is True` em `test_verify.py:309` → `verification["ok"]` é `False` (`input_hash`/`decision` não conferem) |

### 0.5 Medições desta verificação (2026-10-09)

| Suíte | Resultado medido | exit |
|---|---|---|
| `llc2_spec/test_invariants.py` + `.ace/scripts/llc2/tests/` | 169 passed | 0 |
| `llc_replay/tests/test_verify.py` | ✅ **20 passed** (era 15 passed + 5 failed) | 0 |
| `llc_graph/tests/test_engine.py` | 35 passed | 0 |
| **Total** | ✅ **224 passed / 224 coletados** (era 219/224) | — |

Da raiz: `python -m pytest llc2_spec/test_invariants.py .ace/scripts/llc2/tests/ -q`; em `.ace/scripts/`: `python -m pytest llc_replay/tests/test_verify.py -q` e `python -m pytest llc_graph/tests/test_engine.py -q`.

### 0.6 Próximos passos recomendados (ordem)

1. ~~**Destravar o vermelho** (§0.4)~~ ✅ **feito** (20/20 em 2026-10-09, sessão `2026-10-09-002`).
2. **F1 real:** consumir `_USE_LLC2_REPLAY` + `_classify_v2_routing` + `decide()` no fluxo de replay (hoje código morto).
3. **F2:** criar os helpers de impacto no `llc_delta` (a premissa do §3 é falsa) ou usar `GraphEngine.impact_of()` diretamente.
4. ~~**F4:** decidir formalmente entre (a) reverter para whitelist + default `0` (como este plano escreve) ou (b) assumir a adoção global já implementada — **decisão arquitetural, requer validação humana**.~~ ✅ **Decidido (2026-10-09): manter o NodeMachine** em adoção ampla para maior controle determinístico (a opção (a) foi rejeitada). Ver §5.
5. **F3/F5/F6:** completar os campos versionados do DecisionRecord; expandir clientes; reescrever os 2 docs placeholders; instrumentar `LLC2_BASELINE`.

> **Nota de processo:** o commit `d4801e3` avançou até a "Fase 6" enquanto este plano ainda dizia "Aguardando aprovação para iniciar Fase 1" (§11). O plano **não foi atualizado** durante a execução; esta seção restaura a correspondência entre plano e código.

## 1. Objetivo

Complementar a integração parcial existente, evoluindo-a para **adoção completa e universal** sem quebrar o comportamento legado. O foco está em fechar os pontos restantes identificados na verificação:

- **R-2 (Alta):** Integrar `llc_harness/replay.py` ao Decision Engine (llc2) para destravar `replay_hit_rate ≥ 40%`.
- **R-4 (Alta):** Ligar `should_use_semantic_impact()` + `GraphEngine.impact_of()` no fluxo de Delta (aplicar política **impact_of-first**).
- **R-5 (Alta):** Universalizar `DecisionRecord` versionado em todos os caminhos com llc2 v2.
- **R-3 (Média-Alta):** Expandir adoção do `NodeMachine` incrementalmente, além do piloto `11.2`.
- **R-6 (Média):** Tornar geração de Capability Profile **tool-agnostic** (claude/opencode/codex/cursor) + documentar limitação (prevenção via perfil + detecção post-hoc).
- **R-7 (Baixa):** Capturar **baseline real** de métricas (LLM calls/tokens/latência). + **R-1 (Baixa):** Gerar auditoria formal da integração.

**Premissa:** Manter 100% dos testes existentes verdes (`193 passed`). Usar feature flags, preservar fallback legado e garantir rollback seguro por fase.

## 2. Fase 1 — R-2: Integrar `llc_harness/replay.py` ao Decision Engine (Prioridade ALTA)

**Motivo:** Hoje `llc_harness/replay.py` não tem referências a `llc2`. Com `llc_classify.py` já delegando para `classify_task_v2` (com `LLC2_CLASSIFY=1` por padrão), o caminho de replay ainda fica no legado e impede elevar `replay_hit_rate ≥ 40%` (além de não popular `decision_id/policy_version/input_hash` nesse fluxo).

### 2.1 Tarefas

| ID | Tarefa | Arquivos | Detalhamento |
|---|---|---|---|
| **1.1** | Adicionar imports condicionais llc2 | `.ace/scripts/llc_harness/replay.py` | Importar `classify_task_v2`, `load_policy`, `load_question_sets`, `decide`, `DecisionState`, `JevResult`, `HardEvalResult`, `Check` com `try/except ImportError`. Criar flags `_LLC2_AVAILABLE`, `_USE_LLC2_REPLAY` (ler `LLC2_REPLAY` env var). |
| **1.2** | Introduzir flag `LLC2_REPLAY` | `.ace/scripts/llc_harness/replay.py` | `_USE_LLC2_REPLAY = _LLC2_AVAILABLE and os.environ.get("LLC2_REPLAY","0").strip().lower() not in ("0","false","no","")` **sugerido iniciar em `0`** (desligado por padrão) para validação em smoke, com possibilidade de virar `1` após validação dos critérios GO. |
| **1.3** | Criar helper `classify_v2_routing()` | `.ace/scripts/llc_harness/replay.py` | Encapsular chamada a `classify_task_v2`. Retornar estrutura com `type`, `confidence`, `reasoning`, `routing`, `policy_version`, `question_set_hash`, `input_hash`, `decision_id`. Nunca retornar `None` (alinha com F4). |
| **1.4** | Integrar Decision Engine no fluxo de replay | `.ace/scripts/llc_harness/replay.py` | No ramo com `_USE_LLC2_REPLAY`: usar `classify_task_v2` (preserva rótulo + `routing`). Construir `DecisionState` mínimo (via `QuestionSet` `task-classification` quando disponível). Usar `HardEvalResult` determinístico (checks conhecidos) + `JevResult` derivado das respostas quando aplicável. Chamar `llc2.contracts.decide()`/ou delegar via llc2.policy. **Não** descartar classificação por threshold — respeitar `routing`. |
| **1.5** | Conectar com `llc_replay.verify_replay_from_record` | `.ace/scripts/llc_harness/replay.py` | Quando houver `DecisionRecord`/caminho versionado, aproveitar `llc_replay.verify_replay_from_record` (já integra com `contracts.verify_replay` F7). Garantir passagem de `input_hash`, `semantic_result`, `policy`, `ctx_builder`. |
| **1.6** | Popular cache + métricas de replay | `.ace/scripts/llc_harness/replay.py` | Garantir que hits/misses sejam logados em `.ace/logs/replay.jsonl` com campos: `event` (`replay_hit`/`replay_miss`/`llm_fallback`), `reason`, `decision_id`, `input_hash`, `question_set_hash`, `policy_version`, `state_hash` (quando disponível). Evitar sobrescrever lógica existente de rollback determinístico. |
| **1.7** | Preservar fallback legado 100% | `.ace/scripts/llc_harness/replay.py` | Se `_USE_LLC2_REPLAY` falso OU qualquer exceção no ramo v2: cair **imediatamente** no caminho legado (sem alterar comportamento). Logar fallback com razão clara (`llc2_replay_disabled` ou `llc2_replay_error`). |

### 2.2 Critério GO (Fase 1)

| Métrica | Baseline | Alvo | Verificação |
|---|---|---|---|
| `llm_fallback/no_classify` | 18/18 | **0** (com `LLC2_REPLAY=1`) | Inspecionar `.ace/logs/replay.jsonl` após execução controlada. |
| `replay_hit_rate` | 0% | **≥ 40%** (tasks repetidas/semântica idêntica) | Medir em cenário com inputs repetidos (mesmo `input_hash`). |
| Parsing errors | > 0 | **0** | Logs execução. |
| Regressões legacy | — | **0** | Com `LLC2_REPLAY=0`, comportamento idêntico ao atual. |
| Testes existentes | 193 | **193 passed** | `python -m pytest llc2_spec/test_invariants.py .ace/scripts/llc2/tests/ -q` |

### 2.3 Risco/Rollback

- **Risco:** Baixo–Médio (ramo novo sob flag). **Rollback:** Desligar `LLC2_REPLAY` (0) ou reverter arquivo.

## 3. Fase 2 — R-4: Ligar Smart Skip (impact_of-first) no fluxo de Delta (Prioridade ALTA)

**Motivo:** `llc_delta/skip.py` já tem `should_use_semantic_impact()` e `residual_impact()` (prontos). `llc_graph/engine.py` tem `impact_of()` funcional. Falta o **wiring** em `llc_delta/report.py` (e garantir uso consistente) para aplicar a política: **impact_of primeiro → skip determinístico fora do residual → Jev só no residual afetado**.

### 3.1 Tarefas

| ID | Tarefa | Arquivos | Detalhamento |
|---|---|---|---|
| **2.1** | Importar helpers + GraphEngine no report | `.ace/scripts/llc_delta/report.py` | Adicionar imports condicionais: `should_use_semantic_impact`, `residual_impact` de `llc_delta.skip`. Importar `GraphEngine`, `GraphBuilder` (ou `build_graph`) de `llc_graph` com `try/except`. |
| **2.2** | Calcular `affected_nodes` via `impact_of()` | `.ace/scripts/llc_delta/report.py` | Ao gerar/avaliar skip semântico para steps candidatos: construir grafo (`GraphBuilder.build()` ou API existente), obter `affected_nodes = engine.impact_of(changed_node_id)` para nós raiz do delta (ou iterar steps afetados). Tratar `KeyError` (nó inexistente) com fallback conservador (`return True` — não pular avaliação semântica). |
| **2.3** | Aplicar `should_use_semantic_impact()` antes de avaliação semântica | `.ace/scripts/llc_delta/report.py` | Substituir/encapsular decisão de "disparar avaliação semântica do delta": **só** quando `should_use_semantic_impact(step_id, affected_nodes)` for `True`. Fora do conjunto afetado → **não** invocar Jev/LLM (skip determinístico). Isso materializa "impact_of-first, Jev só no residual". |
| **2.4** | Usar `residual_impact()` para granularidade | `.ace/scripts/llc_delta/report.py` | Preferir `residual_impact(step_id, affected_nodes, direct_impact=...)` quando disponível para distinguir impacto direto vs propagado. Manter comportamento backward se helpers não disponíveis (try/except). |
| **2.5** | Flag de segurança (opcional) | `.ace/scripts/llc_delta/report.py` | Adicionar `LLC2_DELTA_IMPACT_FIRST` (default `1` recomendado após validação). Permitir desativar temporariamente com fallback legado. |
| **2.6** | Cobrir edge cases | `.ace/scripts/llc_delta/report.py`, `.ace/scripts/llc_delta/skip.py` | Garantir `affected_nodes` vazio → `should_use_semantic_impact` retorna `False` (sem avaliação semântica desnecessária). Preservar `ALWAYS_RUN` (já existente em `skip.py`). |

### 3.2 Critério GO (Fase 2)

| Critério | Alvo | Verificação |
|---|---|---|
| Política impact_of-first aplicada | **100%** dos caminhos de skip semântico | Código usa helpers antes de chamada semântica. Logs/trace sem Jev em steps fora de `impact_of()`. |
| Zero regressão de skip vs baseline | **0 regressões** | Comparar lista `execute_steps/skip_steps` com baseline em cenário controlado (sem delta vs com delta conhecido). |
| Preserva `ALWAYS_RUN` | **Sem violação** | Steps 10,10.6,10.7,10.8,11,11.1,11.2 nunca pulados. |
| Testes existentes | **193 passed** | Suite completa verde. |
| Comportamento legado intacto | **Idêntico** | Com flag desligada (se usado), sem alteração. |

### 3.3 Risco/Rollback

- **Risco:** Baixo (apenas restringe quando dispara semântica, não altera lógica de execução). **Rollback:** Desligar flag ou reverter `report.py`.

## 4. Fase 3 — R-5: Universalizar DecisionRecord versionado (Prioridade ALTA)

**Motivo:** `DecisionRecord` completo existe em `llc2/contracts.py` (evidence_refs, hashes, policy_version, thresholds_hash, question_set.hash, input_hash/state_hash). `llc_wizard/decisions.py` já popula esses campos. Falta garantir **100% dos caminhos v2** produzam `DecisionRecord` versionado, com instrumentação consistente em `pipeline.py`/`replay.py`.

### 4.1 Tarefas

| ID | Tarefa | Arquivos | Detalhamento |
|---|---|---|---|
| **3.1** | Garantir gravação DecisionRecord em caminhos v2 (replay) | `.ace/scripts/llc_harness/replay.py` | Quando `LLC2_REPLAY=1`: após obter decisão via llc2, chamar `llc_trace.record_decision` (se disponível) com metadados completos: `decision_id`, `policy_id/version`, `thresholds_hash`, `question_set_id/version/hash`, `input_hash`, `state_hash` (quando disponível), `automation`, `reason`, `action`, `evidence_refs`, `classification`. Não quebrar se `record_decision` ausente (graceful). |
| **3.2** | Fortalecer instrumentação em pipeline (NodeMachine paths) | `.ace/scripts/llc_harness/pipeline.py` | Em caminhos com `machine` (NodeMachine) + `LLC2_RECORD=1`: garantir `_record_node_state`/`log_event` populam `decision_id`, `policy_version`, `thresholds_hash`, `question_set.hash`, `input_hash`, `state_hash`, `configuration`. Evitar duplicados (já há chamada dupla em bloco piloto — remover duplicidade redundante sem alterar semântica). |
| **3.3** | Unificar uso de `verify_replay`/records | `.ace/scripts/llc_harness/replay.py` | Priorizar `llc_replay.verify_replay_from_record` quando DecisionRecord estiver disponível. Garantir `input_hash` comparado **antes** de reproduzir (F7). |
| **3.4** | Garantir gates populam metadados completos | `.ace/scripts/llc_harness/gates.py` | Já usa `DecisionPolicyContext` + `submit_policy_decision_interactive`. Verificar que `evidence_refs` é passado/registrado consistentemente em todos os ramos (legacy + policy-aware). Sem alterar fallback. |
| **3.5** | Flag de instrumentação global | `.ace/scripts/llc_harness/replay.py`, `.ace/scripts/llc_harness/pipeline.py` | Respeitar `LLC2_RECORD=1` para escrita append-only. Default `0` (conforme existente) — manter assim, habilitar apenas em validação quando necessário. |

### 4.2 Critério GO (Fase 3)

| Critério | Alvo | Verificação |
|---|---|---|
| Decisões v2 com DecisionRecord versionado | **100%** (caminhos com `LLC2_REPLAY=1` ou NodeMachine v2) | Amostrar `.ace/logs/decisions.jsonl` + eventos: todos têm `decision_id`, `policy_version`, `thresholds_hash`, `question_set.hash`, `input_hash`, `state_hash` (quando aplicável), `evidence_refs`. |
| input_hash verificado em replay | **100%** (hits) | Divergências de hash geram erro explícito (não replay indevido) — conforme F7. |
| Compat backward | **Sem alteração** | Com flags desligadas, formato/semântica inalterados. |
| Testes existentes | **193 passed** | Verde. |

### 4.3 Risco/Rollback

- **Risco:** Baixo (apenas enriquecimento de metadados append-only). **Rollback:** Reverter arquivos.

## 5. Fase 4 — R-3: Expandir NodeMachine além de 11.2 (Prioridade MÉDIA-ALTA)

**Motivo:** Hoje adoção é **apenas piloto `11.2`** (`canonical_id(step) == "11.2"`). Expandir incrementalmente com whitelist controlada, sob `LLC2_STATECHART`, sem habilitar global de uma vez.

> ✅ **DECISÃO (2026-10-09 — Equipe LLC): manter o `NodeMachine` ativo em adoção ampla.**
>
> **Motivo:** adotar o statechart no máximo de steps possível dá **maior controle determinístico** — toda transição passa por guarda pura, por `CAPABILITY_MATRIX` e gera registro versionado.
>
> **O que muda neste documento:**
> 1. A premissa "adoção é apenas piloto `11.2`" (abaixo) fica **obsoleta**; a alternativa "reverter para whitelist + default `0`" foi **rejeitada**.
> 2. O critério **"Sem habilitar global"** (§5.2) é **superado**; o critério passa a ser **"graceful degradation sempre + `LLC2_STATECHART` como kill-switch efetivo"**.
> 3. `LLC2_STATECHART` mantém default `"1"` (`llc_harness/pipeline.py:205`).
> 4. O `LLC2_NODEMACHINE_STEPS` (tarefa 4.1) **opcional**: implementar apenas se surgir necessidade operacional de *escape hatch* por ambiente — como **exceção**, nunca como restrição de cobertura.

### 5.1 Tarefas

| ID | Tarefa | Arquivos | Detalhamento |
|---|---|---|---|
| **4.1** | Definir whitelist incremental | `.ace/scripts/llc_harness/pipeline.py` | Criar `NODEMACHINE_PILOT_STEPS = frozenset({"11.2"})` + `NODEMACHINE_WHITELIST` extensível (ler opcional `LLC2_NODEMACHINE_STEPS` env var, CSV). Lógica: `statechart_pilot = statechart_enabled and (canonical_id(step) in NODEMACHINE_WHITELIST or canonical_id(step) in NODEMACHINE_PILOT_STEPS)`. |
| **4.2** | Expandir whitelist de forma incremental | `.ace/scripts/llc_harness/pipeline.py` | Adicionar steps com boa cobertura/testes (sugerido: `11.1`, `11-VERIFY`, `10.8`) **um por vez**, validando critérios GO a cada adição. **Nunca** remover guarda `statechart_enabled`. |
| **4.3** | Hardening de inicialização | `.ace/scripts/llc_harness/pipeline.py` | Ao criar `NodeMachine`, validar `question_set` existe (já há). Em caso de falha: logar warning, `machine = None`, **não bloquear pipeline** (graceful degradation mantido). Remover duplicidade de `_record_node_state` (chamadas redundantes nas linhas piloto). |
| **4.4** | Verificar DagView/consistência (opcional) | `.ace/scripts/llc_harness/pipeline.py` | Quando aplicável, preparar terreno para expor/usar `DagView` (conforme Passagem 4) sem acoplar agora. Sem alterar GraphEngine. |
| **4.5** | Validação por step expandido | — | Executar smoke por step adicionado com `LLC2_STATECHART=1`, `LLC2_RECORD=1` (quando testando). |

### 5.2 Critério GO (Fase 4)

| Critério | Alvo | Verificação |
|---|---|---|
| Adoção incremental controlada | Whitelist explícita + flag | Apenas steps whitelistados usam NodeMachine. Outros inalterados. |
| Transições reproduzíveis | **100%** (steps piloto/whitelist) | Snapshots `.ace/state/nodes/*.json` coerentes com eventos. Testes NodeMachine (23+ do llc2/tests/test_nodemachine.py) verdes. |
| Graceful degradation | **Sempre** | Falha na init não aborta pipeline. |
| Sem habilitar global | ~~**Garantido**~~ **SUPERADO pela decisão de 2026-10-09 (ver §5)** — adotar globalmente **é** o objetivo | Adoção ampla mantida; `LLC2_STATECHART` preservado como kill-switch. |
| Testes existentes | **193 passed** | Verde. |

### 5.3 Risco/Rollback

- **Risco:** Baixo–Médio. **Rollback:** Remover step da whitelist ou desligar `LLC2_STATECHART`.

## 6. Fase 5 — R-6: Capabilities tool-agnostic + Documentação (Prioridade MÉDIA)

**Motivo:** Geração de perfil hoje limitada a `client == "claude"`. Expandir mapeamento para `opencode/codex/cursor`. Documentar limitação explicitamente (prevenção via perfil + detecção post-hoc como rede de segurança), conforme D-C.

### 6.1 Tarefas

| ID | Tarefa | Arquivos | Detalhamento |
|---|---|---|---|
| **5.1** | Estender mapeamento tool-agnostic | `.ace/scripts/llc2/capabilities.py` | Ampliar `CAPABILITY_TO_CLIENT_TOOLS` / `ClientPermissionProfile` para cobrir `opencode`, `codex`, `cursor` (mapeamentos realistas por cliente). Manter Claude existente. Não quebrar estrutura atual. |
| **5.2** | Gerar perfil por cliente detectado (pipeline) | `.ace/scripts/llc_harness/pipeline.py` | Em vez de `if client == "claude"`: gerar profile para `client` detectado (`detect_agent_client()`) quando `generate_permission_profile` existir. Aplicar apenas se cliente suportar perfis (ou tentar e fallback gracioso). Manter `LLC2_APPLY_CAPABILITY_PROFILE`. |
| **5.3** | Preservar detecção post-hoc | `.ace/scripts/llc_harness/pipeline.py` | Manter `detect_modified_file_violations()` após agent (rede de segurança). Funciona independente de geração de perfil. |
| **5.4** | Documentar limitação (obrigatório) | `docs/architecture/capability-control.md` (novo) | Criar documento declarando: (a) subprocess CLI **não vê tool calls** do agente → prevenção limitada; (b) abordagem adotada: **perfil de permissão por estado (prevenção) + verificação post-hoc (detecção)**; (c) clientes suportados; (d) quando vira apenas detecção (cliente sem suporte a perfis). Alinhar com D-C. |
| **5.5** | Testes smoke por cliente | — | Smoke com clientes mapeados (sem execução real de agente). Validar geração de perfil não quebra. |

### 6.2 Critério GO (Fase 5)

| Critério | Alvo | Verificação |
|---|---|---|
| Suporte tool-agnostic expandido | claude, opencode, codex, cursor (mínimo) | Perfis gerados sem erro para cada cliente detectado. Estrutura válida. |
| Prevenção + detecção coexistem | **Sempre** | Geração de perfil tenta por cliente; post-hoc roda após agent. |
| Documentação criada | **Presente** | `docs/architecture/capability-control.md` existe com limitação explícita declarada. |
| Zero violações detectadas (smoke) | **0** | Com perfis gerados + cenário controlado. |
| Testes existentes | **193 passed** | Verde. |

### 6.3 Risco/Rollback

- **Risco:** Baixo. **Rollback:** Reverter mapeamentos/pipeline, remover doc se desejado.

## 7. Fase 6 — R-7: Métricas baseline + R-1: Auditoria formal (Prioridade BAIXA)

### 7.1 R-7: Capturar baseline real

| ID | Tarefa | Arquivos | Detalhamento |
|---|---|---|---|
| **7.1** | Instrumentar captura de baseline | `.ace/scripts/llc_harness/pipeline.py`, `.ace/scripts/llc_harness/replay.py` | Quando `LLC2_BASELINE=1`: medir LLM calls/sessão, tokens/sessão (input/output), latência (wall time) por step/sessão. Escrever em `.ace/logs/baseline.jsonl` (append-only) com `session_id`, `step`, `phase`, `tokens_in/out`, `calls_llm/jev`, `latency_ms`, `replay_hit/miss`. Reutilizar `llc_evals/instrument.py` quando disponível (graceful se ausente). |
| **7.2** | Registrar métricas de replay | `.ace/scripts/llc_harness/replay.py` | Garantir contadores `replay_hit/replay_success/replay_miss/replay_rollback`, `Jev_calls_avoided/LLM_calls_avoided`, `tokens_avoided/cost_avoided` (quando possível estimar com baseline). |

**Critério GO R-7:** Baseline gravado em `.ace/logs/baseline.jsonl` com campos mínimos; sem impacto em execução normal (`LLC2_BASELINE` default 0).

### 7.2 R-1: Auditoria formal

| ID | Tarefa | Arquivos | Detalhamento |
|---|---|---|---|
| **7.3** | Gerar auditoria de integração LLC2 | Criar `docs/audit/llc2-integration-audit.md` | Consolidar A-1.1–A-1.4: (1) Pontos de integração existentes (pipeline/classify/__init__/replay/verify), (2) Comparação `llc2_spec/` vs `.ace/scripts/llc2/` (marcadores F1–F7), (3) Estado por fase (Feito/Parcial/Falta), (4) Flags (`LLC2_CLASSIFY/RECORD/STATECHART/APPLY_CAPABILITY_PROFILE/BASELINE`), (5) Divergências resolvidas vs remanescentes. |

**Critério GO R-1:** Arquivo criado, completo e rastreável.

## 8. Ordem de execução e validação

### 8.1 Ordem recomendada

```text
Fase 1 (R-2 — Replay harness)  → smoke + métricas replay
  ↓
Fase 2 (R-4 — Delta wiring)    → validação skip vs baseline
  ↓
Fase 3 (R-5 — DecisionRecord)  → verificar .ace/logs/decisions.jsonl
  ↓
Fase 4 (R-3 — NodeMachine whitelist) → expandir incremental (11.2 → +1 por vez)
  ↓
Fase 5 (R-6 — Capabilities tool-agnostic + doc) → perfis por cliente
  ↓
Fase 6 (R-7+R-1 — Métricas + Auditoria) → baseline + doc
```

**Regra:** Cada fase exige **Critério GO** cumprido + **193 testes passando** antes de avançar.

### 8.2 Validação final (global)

| Verificação | Alvo | Comando |
|---|---|---|
| Testes spec + llc2 | **169 passed** (medido 2026-10-09; o alvo anterior de 193 era estimativa — ver §0.5) | `cd <raiz> && python -m pytest llc2_spec/test_invariants.py .ace/scripts/llc2/tests/ -q` |
| Testes llc_replay/verify | 🔴 **15 passed / 5 failed** (medido 2026-10-09 — ver §0.4) | `cd <raiz>/.ace/scripts && python -m pytest llc_replay/tests/test_verify.py -q` |
| Testes llc_graph/engine | **35 passed** (medido 2026-10-09) | `cd <raiz>/.ace/scripts && python -m pytest llc_graph/tests/test_engine.py -q` |
| Smoke Fase 1 (replay) | `llm_fallback→0`, `replay_hit_rate≥40%` | Execução controlada com `LLC2_REPLAY=1` + cenário repetido |
| Smoke Fase 2 (delta) | 0 regressões skip | Comparação baseline vs com delta conhecido |
| Smoke Fase 4 (NodeMachine) | Whitelist funciona, graceful degradation OK | `LLC2_STATECHART=1` por step whitelistado |

## 9. Feature Flags (resumo)

| Flag | Default | Uso | Fase |
|---|---|---|---|
| `LLC2_CLASSIFY` | `1` | Early Commitment v2 (já existente) | F1 |
| `LLC2_REPLAY` | `0` | Replay harness → Decision Engine (novo) | F1 |
| `LLC2_DELTA_IMPACT_FIRST` | `1` | Forçar impact_of-first (novo, recomendado) | F2 |
| `LLC2_RECORD` | `0` | Gravação DecisionRecord/events/snapshots (existente) | F3 |
| `LLC2_STATECHART` | `1` | Habilita NodeMachine (existente) — alinhado à decisão §5 de 2026-10-09 (antes dizia `0`) | F4 |
| `LLC2_NODEMACHINE_STEPS` | (opcional) | CSV de steps extras p/ whitelist (novo) | F4 |
| `LLC2_APPLY_CAPABILITY_PROFILE` | `0` | Aplica perfil por estado (existente) | F5 |
| `LLC2_BASELINE` | `0` | Captura baseline métricas (novo) | F6 |

**Alignment de `LLC2_REPLAY` (2026-10-09):** os dois módulos passaram a ler a mesma env var com o **mesmo default `0`**, e agora **por chamada** (não no import):

| Ponto | Leitura | Default |
|---|---|---|
| `llc_harness/replay.py:51` | módulo (legado, ainda código morto) | `0` |
| `llc2/classifier.py` (`REPLAY_ENV`/`REPLAY_DEFAULT`) | **por chamada** em `_try_replay_classification()` | `0` |
| `llc_replay/tests/test_verify.py` | `monkeypatch.setenv("LLC2_REPLAY", "1")` no fixture `autouse` | teste roda ligado, sem vazar |

Por que *por chamada*: uma leitura em nível de módulo fica **presa no import** — se `llc2.classifier` é importado por outra suíte antes de a flag ser setada, o default é congelado e os testes falham ou passam por omissão. Verificado comportamentalmente no mesmo processo: ausente → `None`; `0` → `None`; `1` → `replayed: True`.

**Recomendação:** Manter defaults conservadores (0) para flags novos (`LLC2_REPLAY`, `LLC2_BASELINE`). Habilitar progressivamente por fase após validação dos critérios GO.

## 10. Riscos e Mitigações

| Risco | Prob. | Mitigação |
|---|---|---|
| Regressão caminho legado (replay) | Baixo | Fase 1 com fallback imediato + `LLC2_REPLAY=0` default + validação com flag desligado. |
| Alteração semântica de skip (delta) | Baixo | `impact_of-first` **restringe** disparo semântico (mais conservador/determinístico), não expande. Preserva `ALWAYS_RUN`. Flag de segurança. |
| Expansão NodeMachine muito ampla | Baixo–Médio | Whitelist explícita + 1 step por vez + graceful degradation + flag global. |
| Perfis tool-agnostic incompletos por cliente | Baixo | Fallback gracioso (não gera/aplica perfil) + detecção post-hoc permanece sempre ativa. |
| Métricas com ruído | Baixo | `LLC2_BASELINE` off por padrão, grava append-only, não impacta execução. |

## 11. Aprovação

**Aguardando aprovação para iniciar Fase 1.** Após aprovação, executar **apenas Fase 1**, validar critérios GO, apresentar resultados e solicitar aprovação para Fase 2.

> ⚠️ **Atualização (2026-10-09):** este gate de aprovação foi **ultrapassado sem atualização do plano**. O commit `d4801e3` executou Fases 1–6 em bloco, com os resultados parciais descritos em §0. O estado real (incluindo o bloqueio da suíte de replay) está consolidado em **§0** e deve ser lido antes de qualquer nova etapa. Este gate permanece aberto para as fases ainda não cumpridas (ver §0.6).
