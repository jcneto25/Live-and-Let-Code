# Plano para complementar a implementação LLC 2.0

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
| Sem habilitar global | **Garantido** | Sem remoção de `LLC2_STATECHART` guard. |
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
| Testes spec + llc2 | **193 passed** | `cd E:/Users/Desktop/javascript/LLC && python -m pytest llc2_spec/test_invariants.py .ace/scripts/llc2/tests/ -q` |
| Testes llc_replay/verify | **20 passed** | `cd E:/Users/Desktop/javascript/LLC/.ace/scripts && python -m pytest llc_replay/tests/test_verify.py -q` |
| Testes llc_graph/engine | **35 passed** | `cd E:/Users/Desktop/javascript/LLC/.ace/scripts && python -m pytest llc_graph/tests/test_engine.py -q` |
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
| `LLC2_STATECHART` | `0` | Habilita NodeMachine (existente) | F4 |
| `LLC2_NODEMACHINE_STEPS` | (opcional) | CSV de steps extras p/ whitelist (novo) | F4 |
| `LLC2_APPLY_CAPABILITY_PROFILE` | `0` | Aplica perfil por estado (existente) | F5 |
| `LLC2_BASELINE` | `0` | Captura baseline métricas (novo) | F6 |

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
