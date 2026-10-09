# LLC 2.0 — Passagem 3: Especificação Formal

**Status:** especificação executável. Nenhum arquivo do LLC foi alterado.  
**Artefatos desta passagem:** `llc2_spec/contracts.py` (tipos + funções puras + tabelas),  
`llc2_spec/test_invariants.py` (**49 testes, todos passando**),  
`llc2_spec/decision-policy.v1.yaml`, `llc2_spec/question-sets.v1.yaml`.

```
$ pytest llc2_spec/test_invariants.py -q
49 passed in 0.22s
```

---

## Correções absorvidas da revisão

### C1 — Noul: `p_true` ≠ `decision_strength` ≠ `confidence`

A revisão está correta e a correção é adotada integralmente. Contrato agora:

| Conceito                               | Fonte            | Significado                                                              |
| -------------------------------------- | ---------------- | ------------------------------------------------------------------------ |
| `p_true`                               | modelo           | probabilidade de a afirmação ser verdadeira. **Valor primário.**         |
| `decision_strength = \|2·p_true − 1\|` | derivado por nós | transformação da distribuição. **Não** é probabilidade de estar correto. |
| `confidence`                           | modelo           | existe **apenas** em Choice e Score. Noul **não** tem.                   |

`JevNoul` não expõe `.confidence` (testado). `JevResult.confidence_of()` normaliza Noul para o mesmo eixo **exclusivamente para comparação de thresholds**, e o Decision Record registra `p_true` e `decision_strength` como campos distintos.

### C2 — Replay ≥ 40% é **KPI econômico**, não invariante

Removido do conjunto de invariantes. Vira critério de sucesso da migração (§16).  
Invariante é apenas: *replay não requer inferência* (INV-006) — que é lógico, não estatístico.

Métricas obrigatórias do painel: `replay_hit_rate`, `replay_success_rate`,  
`replay_rollback_rate`, `LLM_calls_avoided`, `Jev_calls_avoided`,  
`tokens_avoided`, `cost_avoided`.

### C3 — Cascata econômica com 4 alavancas

A revisão está certa: fan-out sozinho não resolve. As alavancas, em ordem de prioridade:

| Alavanca                                  | O que reduz                        | Como                                                                                                     |
| ----------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------- |
| **1. Deterministic pre-filter**           | decisões semânticas desnecessárias | Hard EVAL resolve antes de qualquer chamada                                                              |
| **2. Context reuse / input minimization** | tokens por chamada                 | **o custo do Jev é dominado por input** — nunca reenviar o mesmo artefato; `DecisionState.inputs` mínimo |
| **3. Replay / cache**                     | chamadas                           | hit por `input_hash`                                                                                     |
| **4. Fan-out**                            | round trips                        | 1 chamada com N perguntas                                                                                |

---

# 1. Contrato `NodeMachine`

```python
class NodeMachine:
    """Uma instância por nó (step/PRP/gate). Biblioteca alvo:
    python-statemachine >= 3.2 (StateChart, State.Compound, State.Parallel,
    HistoryState, done.state). Verificado executando na Passagem 2."""

    # ── ciclo de vida ──────────────────────────────────────────────
    def start(self) -> None: ...
    def send(self, event: Event) -> None: ...
    @property
    def configuration(self) -> frozenset[str]: ...

    # ── autoridade ─────────────────────────────────────────────────
    @property
    def capabilities(self) -> frozenset[str]:   # CAPABILITY_MATRIX[state]
        return capabilities_for_state(self.state_id)

    # ── persistência ───────────────────────────────────────────────
    def snapshot(self) -> dict: ...             # serializável
    @classmethod
    def restore(cls, snapshot: dict) -> "NodeMachine": ...
```

**Propriedades exigidas:** determinística (mesmos eventos → mesma configuração),  
puramente testável sem IA, sem rede dentro de guards.

---

# 2. Catálogo de estados e eventos

## Estados

| Estado                        | Tipo              | Significado                     |
| ----------------------------- | ----------------- | ------------------------------- |
| `idle`                        | atômico           | nó existe, deps não satisfeitas |
| `active`                      | **composto**      | nó em trabalho                  |
| `active.preparing`            | atômico (initial) | monta Decision State            |
| `active.agent_running`        | atômico           | agente executando               |
| `active.verifying`            | **paralelo**      | verificação                     |
| `active.verifying.hard`       | composto          | Hard EVAL                       |
| `active.verifying.semantic`   | composto          | Jev (ou desnecessário)          |
| `active.deciding`             | atômico           | Policy produz Decision          |
| `active.applying`             | atômico           | efeito via Tools                |
| `governance`                  | composto          | governança                      |
| `governance.auto_approved`    | atômico (initial) | liberado                        |
| `governance.awaiting_human`   | atômico           | **AWAITING_HUMAN**              |
| `governance.rework`           | atômico           | retentativa                     |
| `done` / `failed` / `skipped` | final             | terminais                       |

Região paralela `verifying` tem filhos **final** (`hard_passed/hard_failed`,  
`sem_ready/sem_not_needed`) para disparar `done.state`. **Ids únicos entre regiões**,  
senão `done.state` não dispara — verificado executando.

## Eventos

`START` · `AGENT_RETURNED` · `HARD_EVAL_DONE` · `SEMANTIC_NOT_NEEDED` ·  
`SEMANTIC_READY` · `DECIDED` · `APPLIED` · `RETRY` · `HUMAN_APPROVED` ·  
`HUMAN_REJECTED` · `SKIP` · `FAIL`

`DECIDED` carrega `Decision` vinda da Policy — nunca uma decisão tomada pelo chamador.

---

# 3. Tabela `STATE + EVENT + GUARD → NEXT`

Codificada em `contracts.py::TRANSITIONS` (executável). Resolução em **ordem de declaração**.

| Estado                      | Evento                | Guard                 | Próximo                     | Action                  |
| --------------------------- | --------------------- | --------------------- | --------------------------- | ----------------------- |
| `idle`                      | `START`               | `deps_satisfied`      | `active.preparing`          | `build_decision_state`  |
| `idle`                      | `SKIP`                | —                     | `skipped`                   | `write_decision_record` |
| `active.preparing`          | `AGENT_RETURNED`      | —                     | `active.agent_running`      | `invoke_agent`          |
| `active.agent_running`      | `HARD_EVAL_DONE`      | —                     | `active.verifying`          | `run_hard_eval`         |
| `active.verifying`          | `SEMANTIC_NOT_NEEDED` | `semantic_not_needed` | `active.deciding`           | —                       |
| `active.verifying`          | `SEMANTIC_READY`      | —                     | `active.deciding`           | `call_jev`              |
| `active.deciding`           | `DECIDED`             | `is_auto`             | `governance.auto_approved`  | `apply_policy`          |
| `active.deciding`           | `DECIDED`             | `is_review`           | `governance.awaiting_human` | `open_gate`             |
| `active.deciding`           | `DECIDED`             | `is_human`            | `governance.awaiting_human` | `open_gate`             |
| `governance.auto_approved`  | `APPLIED`             | `gate_has_evidence`   | `active.applying`           | `apply_changes`         |
| `governance.awaiting_human` | `HUMAN_APPROVED`      | —                     | `governance.auto_approved`  | —                       |
| `governance.awaiting_human` | `HUMAN_REJECTED`      | `retries_left`        | `governance.rework`         | `increment_retries`     |
| `governance.awaiting_human` | `HUMAN_REJECTED`      | —                     | `failed`                    | `write_decision_record` |
| `governance.rework`         | `RETRY`               | —                     | `active.preparing`          | `rollback`              |
| `active.applying`           | `APPLIED`             | `hard_eval_passed`    | `done`                      | `write_decision_record` |
| `active.applying`           | `FAIL`                | `retries_left`        | `governance.rework`         | `rollback`              |
| `active.applying`           | `FAIL`                | —                     | `failed`                    | `rollback`              |

---

# 4. Contrato `DecisionState`

```python
@dataclass(frozen=True)
class DecisionState:
    node_id: str              # "step-2" | "prp-004" | "gate-3"
    state_id: str             # "active.verifying.semantic"
    decision_kind: str        # "D-CLASSIFY-TASK"
    question_set_id: str | None
    question_set_version: str | None
    question_set_hash: str | None
    inputs: Mapping[str, Any] # MÍNIMO necessário — nunca o repositório
    risk_class: RiskClass
    retry_count: int = 0
    derived: Mapping[str, Any] = field(default_factory=dict)

    @property
    def input_hash(self) -> str:   # sha256 do JSON canônico de inputs
```

**Cadeia:** `Raw State → (reducers determinísticos) → Derived State → (projeção mínima + hash) → DecisionState`.  
`state_hash` = sha256 da configuração da máquina + hashes dos artefatos referenciados.

---

# 5. Contrato `DecisionRecord`

```python
@dataclass(frozen=True)
class DecisionRecord:          # append-only, JSONL
    decision_id: str
    timestamp: str             # ISO-8601
    node_id: str
    state_id: str
    event: str
    input_hash: str
    state_hash: str
    policy: Mapping            # id, version, thresholds_hash, decision, automation, reason
    decision: Decision
    question_set: Mapping | None   # id, version, hash
    jev: Mapping | None            # model, request_id, answers, probabilities, usage
    hard_eval: Mapping | None
    statechart: Mapping | None     # version, from, to, guard, guard_result
    action: Mapping | None
    human: Mapping | None
    artifact_hashes: tuple[str, ...]

    def is_replayable(self) -> bool   # requer policy.version + thresholds_hash + statechart.to
```

Regras: `jev.probabilities` é **obrigatório** quando Jev foi usado (permite recomputar  
qualquer medida). `model` no formato real (`jev-1.13.0`).

---

# 6. Decision Policy — YAML + schema

Arquivo: `llc2_spec/decision-policy.v1.yaml` (conteúdo completo entregue).

```yaml
risk:
  R0: {auto_min: 0.50, audit_min: null, review_min: 0.50}
  R1: {auto_min: 0.70, audit_min: 0.50, review_min: 0.50}
  R2: {auto_min: 0.85, audit_min: null, review_min: 0.70}
  R3: {auto_min: null, audit_min: null, review_min: 0.90}   # nunca AUTO
noul: {true_at: 0.80, false_at: 0.20}
fallback:
  hard_eval_failed: HUMAN_REQUIRED       # Jev não pode override
  semantic_unavailable: HUMAN_REQUIRED
  semantic_partial: DOWNGRADE_ONE_LEVEL
  replay_hash_mismatch: REEVALUATE
routing: {preserve_label_always: true, downgrade_only: true}
```

`thresholds_hash` = sha256 do YAML canônico; registrado em cada Decision Record.  
**Nenhum threshold literal fora deste arquivo** (testado indiretamente por INV-005).

---

# 7. Catálogo de Question Sets Jev

Arquivo: `llc2_spec/question-sets.v1.yaml`. Três conjuntos iniciais:

| ID                      | Versão | Risco | Perguntas                                                                                              | Uso                                            |
| ----------------------- | ------ | ----- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| `task-classification`   | 2.0.0  | R1    | Choice `task_type` (5 opções c/ `unknown`) + Score `complexity` (4 níveis) + Noul `needs_human_review` | Early Commitment — substitui `llc_classify.py` |
| `prd-gate`              | 1.0.0  | R1    | Score `prd_quality` (4 níveis) + 3 Noul derivados do checklist do gate 3                               | substitui `doc_judge.py` no step 2             |
| `delta-semantic-impact` | 1.0.0  | R2    | Choice `semantic_impact` + Noul `scope_creep`                                                          | **só após** `impact_of()` ser inconclusivo     |

Regras: 1 question set = 1 chamada fan-out; todo Choice tem fallback explícito;  
trocar `version`/`model` invalida apenas decisões futuras.

---

# 8. Capability Matrix

Codificada em `contracts.py::CAPABILITY_MATRIX` (executável).

| Estado                      | Capacidades                                 | Negado explicitamente         |
| --------------------------- | ------------------------------------------- | ----------------------------- |
| `idle`                      | `read_index`, `read_artifacts`              | tudo mais                     |
| `active.preparing`          | + `build_decision_state`, `jev_eval`        | escrita de código             |
| `active.agent_running`      | + `write_artifacts`, `run_tests`            | `git_commit`, `deploy`        |
| `active.verifying`          | + `run_hard_eval`, `jev_eval`               | escrita                       |
| `active.deciding`           | + `apply_policy`                            | **qualquer efeito**           |
| `active.applying`           | + `apply_changes`, `git_commit`, `rollback` | `deploy`                      |
| `governance.awaiting_human` | + `show_evidence`, `request_approval`       | escrita, `jev_eval`, `deploy` |
| `governance.rework`         | + `build_decision_state`                    | efeito                        |
| `done`/`failed`/`skipped`   | leitura                                     | tudo mais                     |


`FORBIDDEN_EVERYWHERE = {deploy, force_push, delete_session}` — subtraído de todos os estados (testado).

---

# 9. Contrato DAG ↔ NodeMachine

```python
class DagView(Protocol):        # llc_graph = ADVISOR, read-only
    def deps_satisfied(self, node_id: str) -> bool: ...
    def requires_human(self, node_id: str) -> bool: ...
    def risk_class(self, node_id: str) -> RiskClass: ...
    def impact_of(self, node_id: str) -> frozenset[str]: ...
    def frontier(self) -> tuple[str, ...]: ...
```

**Fronteira de autoridade:** o DAG responde *"o quê pode"*; o Core decide *"o que acontece"*.
O DAG **nunca** é chamado para transicionar — apenas dentro de guards.

Mapeamento para o código existente:

| Método do contrato | Origem em `llc_graph` |
|---|---|
| `deps_satisfied` | `GraphEngine._deps_satisfied` |
| `requires_human` | `GraphNode.requires_human` (31 nós hoje) |
| `impact_of` | `GraphEngine.impact_of` |
| `frontier` | `GraphEngine.parallel_frontier` |
| `risk_class` | **novo** — derivado de `target_files` + `RED_ZONE_PATTERNS` + `NodeKind` |

---

# 10. Contrato Event Bus interno

```python
class EventBus(Protocol):
    def publish(self, event: Event) -> None: ...
    def subscribe(self, handler: Callable[[Event], None]) -> None: ...
    def history(self, node_id: str) -> tuple[Event, ...]: ...
```

| Propriedade | Requisito |
|---|---|
| Ordenação | estável por `(node_id, seq)`; não depende de clock |
| Idempotência | `event_id` único; reenvio do mesmo `event_id` é ignorado |
| Durabilidade | append em `.ace/logs/events.jsonl` **antes** do processamento |
| Replay | `history(node_id)` alimenta o Core sem LLM/Jev |

`Event = {event_id, type, node_id, payload}`. `payload` pode carregar `Decision`,
nunca uma decisão tomada fora da Policy.

---

# 11. Modelo de persistência

```
.ace/state/nodes/<node_id>.json     configuração + contadores (por nó)
.ace/logs/events.jsonl              eventos (append-only, durável)
.ace/logs/decisions.jsonl           Decision Records (append-only)
.ace/logs/replay.jsonl              (existente; estendido com decision_id)
```

Snapshot do nó:
```json
{ "node_id": "step-2", "machine": "NodeMachine", "version": "1.0.0",
  "configuration": ["active", "active.deciding"],
  "retries": 1, "gate_id": "3", "policy_version": "1.0.0",
  "last_event": "DECIDED", "updated_at": "2026-10-07T19:00:00Z" }
```

**Recovery:** ler snapshot + último Decision Record. **Não** re-derivar apenas da
última sessão (fecha G3). `.ace/sessions/` permanece imutável — nenhum formato muda.

---

# 12. Modelo de replay

```
para cada DecisionRecord (ordem estável):
  1. input_hash == hash(DecisionState atual)?  senão → RE-EVAL, não replay
  2. decision' = decide(record.hard_eval, record.jev, policy@record.version)
  3. assert decision' == record.policy.decision
  4. event = to_event(decision')
  5. machine.send(event)
  6. assert machine.configuration == record.statechart.to
```

**0 chamadas Jev, 0 chamadas LLM.** Implementado e testado em
`contracts.py::replay_decision` (INV-006).

Garantias:
- *Reproducible execution* — mesmos eventos → mesmos estados ✅
- *Reproducible decision* — mesmo registro → mesma decisão ✅
- *Reproducible inference* — **não garantida, não perseguida** ❌

---

# 13. Modelo de drift

Modo separado e **intencionalmente** com re-inferência:

```
registro antigo + mesmo question_set + modelo/policy novos
   ↓
comparar: decisão mudou? → DECISION_DRIFT (bloqueia promoção)
          automação mudou ou L1 > 0? → CONFIDENCE_DRIFT (reportar)
          nada mudou? → STABLE
```

`l1_distance()` e `DriftReport.kind` implementados e testados.

---

# 14. Invariantes + testes executáveis

`llc2_spec/test_invariants.py` — **49 testes, todos passando**.

| ID | Invariante | Testes |
|---|---|---|
| INV-001 | LLM não muta estado de workflow | 2 (capacidades; rollback nunca avança) |
| INV-002 | Toda transição é representada por evento | 2 |
| INV-003 | Transição automática tem guarda pura | 3 (registro, sem IO, retorno bool) |
| INV-004 | Falha de Hard EVAL não é overridden por Jev | 2 (inclusive em R0) |
| INV-005 | Ação crítica exige humano | 5 (R3 nunca AUTO; tabela escala com risco) |
| INV-006 | Replay não requer inferência | 3 (reprodução, pureza, hash) |
| INV-007 | Toda decisão tem registro versionado | 3 |
| INV-008 | Capacidades limitadas pelo estado | 5 (completude da matriz, `deploy`, desconhecido) |
| INV-009 | Gate consome evidência | 3 |
| INV-010 | Rejeição gera rework, não aborta | 4 |
| INV-011 | Jev nunca é chamado dentro de guard | 3 (assinaturas) |
| — | Noul `p_true` ≠ `decision_strength` | 5 |
| — | classificação ≠ roteamento | 2 |
| — | drift | 2 |

---

# 15. Mapa arquivo-a-arquivo da migração

| Arquivo (`.ace/scripts/`) | Ação | Motivo |
|---|---|---|
| `llc_steps/registry.py`, `models.py` | **KEEP** | fonte única de steps; adicionar `depends_on` declarativo |
| `llc_graph/model.py`, `state.py`, `builder.py`, `projections.py` | **KEEP** | DAG é advisor |
| `llc_graph/engine.py` | **MODIFY** | expor `DagView` (`risk_class`, `frontier`); **não** adicionar transições |
| `llc_harness/pipeline.py` | **REPLACE** | for-loop → scheduler sobre NodeMachines |
| `llc_harness/gates.py` | **MODIFY** | consumir `Decision.evidence_refs`; remover `auto_approve` global |
| `llc_harness/replay.py` | **MODIFY** | usar Decision Engine; registrar `decision_id` |
| `llc_harness/session.py`, `skill.py`, `common.py` | **KEEP** | ACE intacto |
| `llc_classify.py` | **MODIFY** | caller → Jev `Choice`; interface preservada |
| `llc_replay/*` | **MODIFY** | popular cache; hit rate é KPI |
| `llc_evals/evaluators/doc_judge.py` | **MODIFY** | caller → Jev `Score`/`Noul` por dimensão |
| `llc_evals/instrument.py`, `aggregate.py`, `report.py` | **KEEP** | medição |
| `llc_evals/rubrics/*.yaml` | **KEEP** | viram base dos question sets |
| `fitness_functions/**` | **KEEP** | 41 checks determinísticos, intocáveis |
| `llc_delta/report.py`, `skip.py` | **MODIFY** | `impact_of` primeiro; Jev só no residual |
| `llc_wizard/decisions.py` | **MODIFY** | `<gate_result>` + `decision_id`, `policy_version` |
| `llc_wizard/**` (TUI) | **KEEP** | exibir Decision/Policy |
| `prp_verify/**`, `consistency-check.py`, `code-health.py` | **KEEP** | Hard EVAL |
| **novo** `llc_core/` | **CREATE** | `NodeMachine`, `Capabilities`, `EventBus`, `Scheduler` |
| **novo** `llc_policy/` | **CREATE** | `decide()`, loader de YAML, `thresholds_hash` |
| **novo** `llc_semantic/` | **CREATE** | cliente Jev + question sets versionados |

---

# 16. Critérios GO/NO-GO

| Fase | GO | NO-GO (rollback) |
|---|---|---|
| 0 — instrumentação | 100% dos steps com `input_hash` | < 90% |
| 1 — Jev no classify | acurácia ≥ baseline LLM; 0 erro de parsing | acurácia < baseline |
| 2 — Policy | 0 threshold literal fora do YAML; `decide()` 100% coberto | qualquer threshold hardcoded |
| 3 — Semantic EVAL | concordância ≥ 80% com humano no golden set | < 70% |
| 4 — NodeMachine (piloto) | transições reproduzíveis em replay (100%) | qualquer divergência |
| 5 — Capability | 0 tool call fora da matriz em 100 execuções | ≥ 1 violação |
| 6 — Decision Record | 100% das decisões com policy+statechart versionados | < 95% |
| 7 — Replay | replay sem Jev em 100% dos casos com hash igual | qualquer re-inferência indevida |
| 8 — Smart Skip semântico | 0 regressão de skip vs. baseline | regressão |

**KPIs econômicos (não invariantes):** `replay_hit_rate ≥ 40%`, `replay_success_rate ≥ 95%`,
`replay_rollback_rate ≤ 5%`, `LLM_calls_avoided`, `Jev_calls_avoided`, `tokens_avoided`, `cost_avoided`.

---

# 17. Benchmark de custo e latência

**Premissas declaradas (medir na Fase 0 para os valores reais do LLC):**
artefato de PRD ≈ 8.000 tokens; rubric + upstream ≈ 2.500 tokens;
Jev ≈ US$ 0,042 / 1M tokens de input (jev-1.12, set/2026);
juiz generativo de referência ≈ US$ 3 / 1M input e US$ 15 / 1M output.

| Cenário | Input | Output | Custo estimado | Latência |
|---|---|---|---|---|
| **Hoje** — `doc_judge` via LLM generativo | ~10.500 | ~400 (JSON c/ justificativas) | **≈ US$ 0,037** | 10–40 s |
| Jev, 6 chamadas separadas | ~63.000 | ~360 | ≈ US$ 0,0027 | ~2,7 s |
| **Jev, 1 fan-out (6 perguntas)** | ~10.500 | ~110 | **≈ US$ 0,00044** | ~0,3–0,5 s |
| Replay (hit) | 0 | 0 | **US$ 0** | ~ms |

Conclusão: **fan-out ≈ 6× mais barato que chamadas separadas; Jev ≈ 85× mais barato que
juiz generativo no mesmo documento; replay elimina o custo.**
O benchmark documentado do Jev (13 perguntas, artigo de 54k chars) mediu
**12,2× mais barato e 10,0× mais rápido** — coerente com o modelo acima.

**O maior risco de custo não é o número de perguntas: é reenviar o mesmo artefato.**
Daí a alavanca 2 (context reuse) ser prioritária sobre fan-out.

---

# 18. Compatibilidade com o LLC atual

| Superfície | Garantia |
|---|---|
| CLI (`llc.py run/gate/eval/wizard/pipeline`) | **inalterada** |
| `.ace/sessions/*.md` | **imutáveis**; mutadores sancionados preservados |
| `.ace/index.json` | formato preservado (fonte do Derived State) |
| `gates.json` (31 gates, 133 itens) | preservado; checklists viram Noul |
| `StepSpec` (30 steps) | preservado; ganha `depends_on` |
| Fitness functions (41 checks) | intocáveis |
| `llc_replay/` | preservado; passa a ser populado |
| Novos arquivos | somente `.ace/state/`, `.ace/logs/decisions.jsonl`, `.ace/logs/events.jsonl` |

---

# Decisões em aberto — alternativas, trade-offs e recomendação

Regra da revisão: **nenhuma decisão tomada silenciosamente.**

| # | Ambiguidade | Alternativas | Trade-off | Recomendação |
|---|---|---|---|---|
| D1 | Entrega de evento | (a) `send()` síncrono; (b) log append-only + projetor; (c) fila | (a) simples, perde auditoria; (b) auditável, exige idempotência; (c) escala, adiciona infra | **(b)**, com wrapper síncrono |
| D2 | `decision_id` | (a) hash do conteúdo; (b) uuid7 | (a) idempotência nativa no replay; (b) único sempre, mas não determinístico | **(a)** — `sha256(node_id, kind, input_hash, qs_hash, attempt)` |
| D3 | Biblioteca do Core | (a) `python-statemachine ≥3.2`; (b) própria | (a) validada, menos código; (b) zero dependência, mais bugs | **(a)** |
| D4 | Persistência | (a) arquivo por nó; (b) índice único | (a) escrita atômica por nó; (b) leitura única | **(a)** + índice leve |
| D5 | Chamada Jev | (a) action com cliente injetado; (b) serviço externo | (a) testável com mock; (b) desacoplado, mais latência | **(a)** |
| D6 | Gate standalone (ex.: `11-SEC` fora do pipeline) | (a) dentro do nó gateado; (b) NodeMachine própria | (a) simples; (b) uniforme | **(b)** — uniformidade de auditoria |
| D7 | Scheduler | (a) pull (consulta `frontier`); (b) push por evento | (a) determinístico; (b) reativo, ordem menos previsível | **(a)** |
| D8 | Métrica de drift | (a) mudança de decisão; (b) L1; (c) KL | (a) acionável; (b) sensível; (c) sensível a zero | **(a)** primária, **(b)** secundária |
| D9 | `inputs` por `decision_kind` | (a) conjunto fixo por question set; (b) dinâmico | (a) auditável; (b) econômico mas instável | **(a)** |
| D10 | Migração do `doc_judge` | (a) substituir caller; (b) rodar em paralelo com flag | (a) rápido; (b) comparável | **(b)** na Fase 3, **(a)** na Fase 6 |

---

## Próximo passo

Com os 18 itens fechados, os contratos em `llc2_spec/` são a fronteira de implementação.
**Nenhuma linha do LLC foi alterada.**
