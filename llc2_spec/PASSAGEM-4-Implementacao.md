# LLC 2.0 — Passagem 4: Especificação de Implementação e Integração

**Status:** especificação executável + integração ao repositório real.
**Artefatos:** `llc2_spec/contracts.py` (v2), `llc2_spec/test_invariants.py`
(**73 testes, todos passando**), `llc2_spec/jev_adapter.py`,
`llc2_spec/macro_projection.py`, `llc2_spec/decision-policy.v1.yaml`,
`llc2_spec/question-sets.v1.yaml`.

```
$ PYTHONPATH=llc2_spec pytest llc2_spec/test_invariants.py -q
73 passed in 1.79s
```

**Nenhum arquivo do runtime do LLC foi alterado.** Foram criados apenas
arquivos novos em `llc2_spec/`.

---

## 0. Resumo executivo

As Passagens 1–3 estavam corretas em suas alegações factuais — verifiquei
todas as principais contra `origin/master`. O que esta passagem entrega não é
uma nova arquitetura, e sim **a correção de sete defeitos que a tornariam
inexecutável ou insegura**, mais a reconciliação de uma contradição
arquitetural e o contrato que faltava (adapter Jev).

| # | Achado | natureza |
|---|---|---|
| **A** | Dois "núcleos determinísticos" coexistindo (`NodeMachine` × `LLCPipeline`) | contradição com P1 §3.5 e P2 §0.3 |
| **B** | `decide()` fail-open: semântica esperada e ausente ⇒ `AUTO` | viola INV-005 e o próprio YAML |
| **C** | Noul avaliado só por força (`|2p−1|`), nunca por direção | inverte o significado de `needs_human_review` |
| **D** | `Classification` nunca populada; teste que deveria cobrir §14 é tautológico | invariante sem cobertura |
| **E** | Subestados das regiões paralelas fora da matriz de capacidade e do join | `KeyError` em runtime |
| **F** | Guards com assinaturas heterogêneas resolvidas por `**ctx` | `TypeError` em runtime |
| **G** | Replay não comparava `input_hash` | "replay" poderia reproduzir outra entrada |
| **H** | `POLICY_TABLE` duplicava os thresholds do YAML; `thresholds_hash="sha256:pending"` | viola §7 |
| **I** | Matriz de capacidade sem ponto de mediação — e o agente é subprocess CLI | INV-008 não é executável como está |
| **J** | `model: jev-latest` em todos os question sets | destrói drift analysis |

Os sete primeiros (A–G) estão corrigidos e cobertos por teste. **I é o único
que a especificação não resolve sozinha** — exige uma decisão de runtime
(§5).

---

## 1. Validação das Passagens 1–3 contra o repositório real

### 1.1 Achado prévio: o _working tree_ local está 56 commits atrás

```
HEAD (local)     b22188a  "Commit changes"
origin/master    aaad99f  (tag v2.0.0)
git rev-list --count HEAD..origin/master  =>  56
```

O checkout local **não contém** `llc_graph/`, `llc_evals/` nem `llc_wizard/`
(0 arquivos em `git ls-files`). Esses pacotes existem em `origin/master`, que
tem **443 arquivos** — exatamente o número declarado na Passagem 1. Ou seja:
**as passagens anteriores não inventaram componentes**; foram escritas contra
a versão correta. Qualquer implementação começa por sincronizar o checkout
(decisão do usuário — não executei `git pull`).

### 1.2 Alegações verificadas (CONFERE)

| Alegação (P1/P2) | Evidência em `origin/master` |
|---|---|
| `llc_classify.py` descarta abaixo de 0.80 | `llc_classify.py:30` `CONFIDENCE_THRESHOLD = 0.80`; `:93-94` `if confidence < …: return None` |
| `match.py` threshold 0.60 | `llc_replay/match.py:34` `threshold = 0.60` |
| XML + regex + confidence textual | `re.search(r"<type>…")`, `<confidence>`, `<reasoning>` |
| gates.json: 31 chaves, 133 itens, 0 output_files | medido: `31 / 133 / 0` |
| replay 0% hit | `.ace/logs/replay.jsonl`: **18 eventos, 18 `llm_fallback`, 18 `reason=no_classify`** |
| `.ace/cache/` não existe | 0 arquivos sob `.ace/cache/` |
| 30 `StepSpec` | 30 chamadas `_spec(` em `registry.py` |
| `GraphEngine` é read-only | `engine.py:104` "NÃO executa nada, NÃO invoca runtime" |
| `gate_check(step, _output)` ignora output | parâmetro `_output` nunca usado no corpo |
| `doc_judge` usa JSON + regex | `re.sub` de bloco ```json```, `json.loads`, fallback `re.search(r"\{.*\}")` |
| PyYAML já é dependência | `import yaml` em 21 arquivos ⇒ adotar YAML **não** adiciona dependência |

### 1.3 Cadeia causal de G1 (antes inferida, agora medida)

`llc_harness/replay.py:65` é o **único** chamador de `classify_task`:

```python
classification = classify_task(task_description, client)   # :65
...
log_replay_event("llm_fallback", …, reason="no_classify")  # :131-134
```

O classificador retornou `None` nas 18 execuções ⇒ o harness nem chegou a
consultar `llc_replay` ⇒ `replay_hit` nunca foi logado. **O subsistema de
replay não está "quase pronto": ele está atrás de um classificador que falha
sempre.** A Fase 1 (Jev no Early Commitment) é portanto pré-requisito da
Fase 7 (replay), não uma otimização independente.

### 1.4 Correções às Passagens 1–3

| Item | Correção |
|---|---|
| **G7** ("fail-open em CI") | Reescopo. `gate_check(step, _output=None, auto_approve=False)`: o padrão é `False`; o caminho interativo **já é fail-closed** (E-13: entrada ambígua re-pergunta, nunca aprova; sem timeout = bloqueia, que é o comportamento correto de um gate humano). O fail-open real é só: (a) `auto_approve=True` em CI e (b) `return "approved"` quando o step não tem gate definido. |
| **G6** | Confirmado (`_output` ignorado), mas "timeout não existe" foi classificado como defeito e **não é** — é fail-closed por design. |
| **`doc_judge`** | Mais robusto que o descrito: `aggregate_score` pondera por dimensão, faz clamp em `[0,100]` e ignora score malformado sem crash (RF-EF3.2/EF3.6). A Fase 3 precisa preservar a semântica `aggregate ∈ [0,100]` para que a comparação com o baseline seja válida. |
| **P3 §17 (custo)** | Premissas declaradas como estimativa — correto. Continuam não medidas. |

---

## 2. Decisão D-A — reconciliação dos dois statecharts

### 2.1 O problema

A Passagem 3 produziu dois "núcleos determinísticos":

1. `contracts.py::TRANSITIONS` — `NodeMachine`, uma instância por nó. Micro,
   puro, **zero dependências**, testável.
2. `llc_statechart_corrigido.py::LLCPipeline` — máquina macro
   (`discovery → planning → implementation → deployed`), com `human_gate`,
   `self_heal` e região paralela `quality_gates`. Depende de
   `python-statemachine >= 3.2` (**não instalado** neste ambiente).

Dois statecharts = duas autoridades de transição. É exatamente a falha que a
P1 §3.5 ("duas fontes de verdade de orquestração") e a P2 §0.3 proíbem.

Além disso, o chart macro contém estados que **não têm origem no registry do
LLC**: `discovery.use_cases` (não existe step de casos de uso), `self_heal`
(é `governance.rework` na `NodeMachine`) e `deployed` (`deploy` é
`FORBIDDEN_EVERYWHERE`).

### 2.2 Decisão

> **O chart macro é rebaixado a PROJEÇÃO DERIVADA.** Não transiciona, não
> guarda estado próprio, não é fonte de verdade. É uma função pura das
> configurações das `NodeMachine`.

```
macro_view({node_id: state_id}) -> MacroView      # puro, determinístico
```

A hierarquia continua existindo (é hierarquia de Harel legítima), mas a
composição é explícita: **o estado macro é função do estado micro, nunca o
contrário**. `llc_statechart_corrigido.py` permanece como documentação
executável, com suas divergências declaradas em
`macro_projection.divergences()` — não silenciadas.

Implementado em `llc2_spec/macro_projection.py`; coberto por 5 testes
(determinismo, precedência `governance > ativo > terminal`, mapeamento de
fases, `unmapped` explícito, divergências declaradas).

**Consequência para o plano:** `python-statemachine` deixa de ser
pré-requisito. Se o time quiser a máquina macro como runtime (não como
projeção), isso é um ADR novo, com dependência nova — não recomendado.

---

## 3. Correções normativas F1–F7

Cada correção tem o teste que a prova. Todos em
`llc2_spec/test_invariants.py`.

### F1 — Thresholds são dados, não literais

`POLICY_TABLE`/`AUTO_AUDIT_BAND` (0.50/0.70/0.85/0.90 hardcoded em
`contracts.py`) foram **removidos**. Agora: `load_policy()` lê
`decision-policy.v1.yaml` e `thresholds_hash` é
`sha256(canonical_json{risk, noul, fallback, routing, limits})` de verdade.

Teste que falharia antes:

```python
def test_f1_changing_yaml_changes_automation(tmp_path):
    # troca auto_min: 0.85 -> 0.99 no YAML; se o limiar estivesse no código,
    # o resultado não mudaria
    assert automation_for(p, RiskClass.R2, 0.90) is not Automation.AUTO
```

### F2 — Fecha o fail-open de `decide()`

Antes: `semantic is None` ⇒ `AUTO / "resolved_deterministically"`,
**mesmo quando havia question set esperado**. E o teste
`test_inv005_fail_closed_when_jev_unavailable` **assertava esse
comportamento** — um teste que consagrava o fail-open.

Agora, `decide()` recebe `semantic_expected` (derivado de
`state.expected_answers`):

| situação | antes | agora |
|---|---|---|
| semântica esperada e ausente | `AUTO` | `HUMAN_REQUIRED / semantic_unavailable` |
| semântica não esperada e ausente | `AUTO` | `AUTO / resolved_deterministically` (decisão estrutural explícita) |
| resposta parcial | sem tratamento | `DOWNGRADE_ONE_LEVEL / semantic_partial` |

### F3 — Noul: direção antes de força

`confidence_of()` mapeia Noul para `|2p−1|`. Um `needs_human_review` com
`p_true = 0.97` ("sim, precisa de humano") vira **confiança 0.94** e
empurra a decisão para `AUTO`. O significado da pergunta fica invertido.

Correção: question sets ganham `raises_risk_when_true: true`; a política
avalia a **direção** (`decided()`) antes da força e aplica um piso:

| Noul de risco | efeito |
|---|---|
| `p_true >= 0.80` (afirmativo) | piso `REVIEW_REQUIRED` ( `HUMAN_REQUIRED` em R3 ) |
| `0.20 < p_true < 0.80` (incerto) | `decision_strength` baixo ⇒ eixo de confiança colapsa ⇒ fail-closed |
| `p_true <= 0.20` (negativo) | sem piso |

Noul de **qualidade** (ex.: `tecnico_cobre_requisitos`) não leva a flag e
não interfere — teste `test_f3_non_risk_noul_high_stays_auto`.

### F4 — Classificação nunca é descartada (§14)

`Classification` é agora sempre populada a partir do primeiro `Choice`. O
teste antigo (`assert d.classification is None or True`) era tautológico e
foi substituído por um que **exige** `label == "BUG_FIX"` com `confidence
0.22` e automação rebaixada.

### F5 — Regiões paralelas na tabela e na matriz

- Subestados `active.verifying.hard.*` e `active.verifying.semantic.*`
  entram em `TRANSITIONS` e em `CAPABILITY_MATRIX`.
- `capabilities_for_state()` resolve por **prefixo mais longo**
  (`active.verifying.hard.passed` herda de `active.verifying.hard`).
- Join explícito: `VERIFICATION_COMPLETE` com guard `verification_complete`
  (ambas as regiões em estado final **e** hard passou).
- Hard EVAL falho tem transição própria para `governance.awaiting_human` —
  nunca para `auto_approved` (reforça INV-004 no nível da máquina).

### F6 — Assinatura uniforme de guard

Antes: `GUARD_REGISTRY[t.guard](**ctx)` com guards de assinaturas
diferentes (`(dag, node_id)`, `(hard)`, `(d)`, `(retries, max_retries)`) —
qualquer descasamento dava `TypeError` em runtime. Agora todas recebem um
único `GuardContext`, e há teste que **exige** `params == ["ctx"]`.

### F7 — Replay verifica `input_hash`

`verify_replay()` compara `record.input_hash` com o hash do estado atual
antes de reproduzir; divergência ⇒ erro explícito (reavaliação, não
replay). Inclui verificação de transição via `ctx_builder`.

---

## 4. Contrato do adapter Jev (`jev_adapter.py`)

Faltava inteiramente nas passagens anteriores.

| Responsabilidade | Comportamento |
|---|---|
| **Fan-out** | 1 chamada por Decision State; nunca N |
| **Modelo** | pinado; `jev-latest` ⇒ `SemanticUnavailable` |
| **Idempotência** | `idempotency_key = sha256({qs_hash, input_hash})` |
| **Cache** | por `(question_set.hash, input_hash)` — base do replay |
| **Validação** | opção dentro de `criteria`; `score ∈ 0..n-1`; `noul ∈ 0..1`; `confidence` obrigatório em Choice/Score |
| **Parcial** | resposta faltando **não** é erro: a política rebaixa um nível |
| **Indisponível** | `1 + max_retries` tentativas; depois `SemanticUnavailable` ⇒ `HUMAN_REQUIRED` |
| **Registro** | `record_payload()` sempre grava `probabilities` (permite recomputar qualquer medida em drift) |

`FakeJevTransport` é **scriptado, não mockado**: serve para testes de
contrato (opção inválida, score fora de faixa, timeout, modelo divergente,
resposta parcial) sem rede.

---

## 5. Capability control — o que é realmente executável

**Advertência (a mais importante desta passagem):** a matriz de capacidade
só existe se houver um ponto de mediação. Hoje o agente é invocado como
**subprocess CLI** (`subprocess.run([client, "--prompt", …])`): o LLC não
vê as tool calls do agente, portanto **não pode bloqueá-las**. INV-008, como
especificado, é inexecutável nesse modelo.

Três caminhos, com custo honesto:

| Opção | Como | Custo | Veredito |
|---|---|---|---|
| **1. Perfis de permissão do cliente por estado** | escrever `.claude/settings.local.json` (ou equivalente) com allow/deny antes de cada step; mediação feita pelo próprio cliente de IA | baixo; por cliente | **recomendada para as Fases 5** — é o único ponto que o subprocess respeita |
| **2. Broker in-process (SDK)** | trocar subprocess por SDK; todo tool call passa por `ToolBroker.authorize(state_id, tool)` | alto; acopla a um fornecedor | futuro, se o LLC abandonar o modelo tool-agnostic |
| **3. Verificação post-hoc** | `git diff` + `llc_replay/zones.py` + fitness, rejeitando o que saiu da matriz | baixo; já existe | **não é prevenção, é detecção** — usar como rede de segurança, não como INV-008 |

Recomendação: **1 + 3**. A matriz declara a intenção; o perfil do cliente
executa a mediação; o diff + zonas 🔴 detecta o escape. `DefaultToolBroker`
fica na especificação como o contrato que a opção 2 implementaria.

---

## 6. Mapa arquivo-a-arquivo (revisado contra `origin/master`)

| Arquivo | Ação | Motivo |
|---|---|---|
| `llc_steps/registry.py`, `models.py` | **KEEP** | fonte única (30 `_spec`); ganhar `depends_on` declarativo |
| `llc_graph/model.py`, `state.py`, `builder.py`, `projections.py` | **KEEP** | DAG = advisor |
| `llc_graph/engine.py` | **MODIFY** | expor `DagView` (`risk_class`, `frontier`); **não** adicionar transições |
| `llc_harness/pipeline.py` | **REPLACE** | `for`-loop ⇒ scheduler sobre `NodeMachine` |
| `llc_harness/replay.py` | **MODIFY** | usar Decision Engine; `classify_task` deixa de retornar `None` e passa a retornar roteamento |
| `llc_harness/gates.py` | **MODIFY** | consumir `Decision.evidence_refs`; `auto_approve` ⇒ `min_automation_level` por gate; fechar o `return "approved"` sem gate |
| `llc_harness/session.py`, `skill.py`, `common.py` | **KEEP** | ACE intacto |
| `llc_classify.py` | **MODIFY** | caller ⇒ Jev `Choice`; **interface preservada**, `None` substituído por rótulo + roteamento |
| `llc_replay/*` | **MODIFY** | popular `.ace/cache/`; hit rate é KPI |
| `llc_evals/evaluators/doc_judge.py` | **MODIFY** (Fase 3) | Jev `Score`/`Noul` por dimensão; preservar `aggregate ∈ [0,100]` |
| `llc_evals/instrument.py`, `aggregate.py`, `report.py` | **KEEP** | medição; baseline de custo |
| `llc_evals/rubrics/*.yaml` | **KEEP** | viram base dos question sets |
| `fitness_functions/**` | **KEEP** | 41 checks determinísticos, intocáveis |
| `llc_delta/report.py`, `skip.py` | **MODIFY** (Fase 8) | `impact_of` primeiro; Jev só no residual |
| `llc_wizard/decisions.py` | **MODIFY** | `<gate_result>` + `decision_id`, `policy_version` |
| `llc_wizard/**` (TUI) | **KEEP** | exibir Decision/Policy |
| `prp_verify/**`, `consistency-check.py`, `code-health.py` | **KEEP** | Hard EVAL |
| **novo** `llc_core/` | **CREATE** | `NodeMachine`, `Capabilities`, `EventBus`, `Scheduler` |
| **novo** `llc_policy/` | **CREATE** | `decide()`, loader YAML, `thresholds_hash` |
| **novo** `llc_semantic/` | **CREATE** | adapter Jev + question sets versionados |
| **novo** `llc2_spec/` | **CREATE (feito)** | especificação executável — não é runtime |

**Compatibilidade preservada:** CLI `llc.py run/gate/eval/wizard/pipeline`
inalterada; `.ace/sessions/*.md` imutáveis; `.ace/index.json` com formato
preservado; `gates.json` (31/133) preservado.

---

## 7. Plano de implementação

### Fase −1 (pré-requisito, decisão do usuário)

Sincronizar o checkout com `origin/master` (56 commits, tag `v2.0.0`).
Sem isso, `llc_graph/`, `llc_evals/` e `llc_wizard/` não existem no disco.

### Fase 0 — Instrumentação (sem mudança de comportamento)

| Item | Conteúdo |
|---|---|
| Arquivos | `llc_harness/pipeline.py`, `llc_harness/session.py`, `.ace/logs/` |
| Novos | `.ace/logs/events.jsonl`, `.ace/logs/decisions.jsonl`, `.ace/state/nodes/<id>.json` |
| Interfaces | `Event`, `DecisionRecord` (shim: só hashes + policy_version) |
| Risco | baixo — append-only, desligável por flag |
| Rollback | desligar flag |
| Critério GO | 100% dos steps com `input_hash`; 0 mudança de comportamento observável |
| Métrica | baseline real de LLM calls/sessão, tokens/sessão, latência (fecha G12) |

### Fase 1 — Jev `Choice` no Early Commitment

Mudança precisa em `llc_classify.py` — **a única que destrava G1**:

```python
# ANTES (retorno descarta a classificação)
if confidence < CONFIDENCE_THRESHOLD:
    return None

# DEPOIS (preserva rótulo, rebaixa roteamento)
return {
    "type": task_type,          # rótulo preservado SEMPRE, inclusive "unknown"
    "confidence": confidence,   # min das confidences do fan-out
    "reasoning": reasoning,
    "routing": routing,         # AUTO | REVIEW_REQUIRED | HUMAN_REQUIRED
    "policy_version": ...,  "question_set_hash": ...,
    "input_hash": ...,      "decision_id": ...,
}
```

`llc_harness/replay.py:65` passa a tratar `routing` em vez de `None` — é
isso que faz o fluxo chegar a `llc_replay` pela primeira vez.

| Item | Conteúdo |
|---|---|
| Arquivos | `llc_classify.py` (caller trocado), `llc_harness/replay.py` |
| Novos | `llc_semantic/` (adapter), `llc_policy/` (decide + YAML) |
| Risco | baixo — voltar o caller LLM por flag |
| Critério GO | acurácia ≥ baseline LLM; **0 erro de parsing**; `llm_fallback/no_classify` ⇒ 0 |
| NO-GO | acurácia < baseline |

Fases 2–8 permanecem as da Passagem 2 §BLOCO 6, com duas alterações:
a Fase 4 passa a usar `contracts.TRANSITIONS` (zero dependências) em vez de
`python-statemachine`, e a Fase 5 adota a **opção 1** do §5.

---

## 8. Métricas e critérios de aceitação

| Métrica | Baseline (medido) | Alvo |
|---|---|---|
| Replay hit rate | **0%** (18/18 `llm_fallback`) | ≥ 40% |
| `llm_fallback/no_classify` | **18/18** | 0 |
| Parsing errors de LLM | > 0 (XML/JSON/MD) | 0 |
| Aprovações automáticas sem evidência | possíveis (`auto_approve`) | 0 |
| Decisões sem Decision Record versionado | 100% | 0 |
| Violações de capability | não medido (sem controle) | 0 (com opção 1+3) |
| Thresholds fora do YAML | 2 (0.80, 0.60) | 0 |
| LLM/Jev calls por step | 1 LLM generativo (classify) | ≤ 1 Jev fan-out |

---

## 9. Riscos, trade-offs e decisões em aberto

| # | Decisão | Recomendação |
|---|---|---|
| **D-A** | Dois statecharts | **macro = projeção derivada** (fechado) |
| **D-B** | `python-statemachine` como dependência | **não adotar**; `TRANSITIONS` declarativa cobre o necessário |
| **D-C** | Mediação de capacidade | **perfil de permissão do cliente + verificação post-hoc** (§5) |
| **D-D** | `decide()` sem semântica esperada | **fail-closed** (`HUMAN_REQUIRED`) |
| **D-E** | Noul de risco incerto | **fail-closed** (eixo de confiança colapsa) |
| **D-F** | Modelo Jev | **pinado**; `latest` é erro de configuração |
| **D-G** | Sincronizar `origin/master` (Fase −1) | **decisão do usuário** |

Riscos remanescentes:

1. **Custo do Jev não medido** — as premissas da P3 §17 continuam sendo
   estimativas. Só a Fase 0 produz números comparáveis.
2. **Reproducible inference não é garantida** — e não é perseguida. A
   arquitetura garante _reproducible execution_ e _reproducible decision_;
   inferência é tratada por drift, não por determinismo.
3. **INV-008 depende do cliente de IA** — se o cliente não suportar perfis
   de permissão por estado, a capacidade vira detecção, não prevenção. Isso
   deve ser declarado abertamente, não prometido.

---

## 10. Como executar

```bash
cd E:/Users/Desktop/javascript/LLC
PYTHONPATH=llc2_spec pytest llc2_spec/test_invariants.py -q
# 73 passed
```

Requisitos: Python ≥ 3.10, PyYAML (já usado pelo LLC em 21 arquivos), pytest.
**Nenhuma outra dependência.**
