# LLC 2.0 — Passagem 2: Especificação de Arquitetura

**Status:** especificação. **Nenhum código do LLC foi alterado.**  
**Regra explícita:** não implementar nada enquanto as interfaces  
`Jev → Decision Policy → Statechart → Tools → Decision Record` não estiverem formalizadas. Esta passagem fecha essas interfaces.

---

## BLOCO 0 — Decisão pendente da revisão: A, B ou C?

### 0.1 Evidência medida (não inferida)

Grafo construído do repositório real via `GraphBuilder.build()` + `GraphEngine`:

```
NÓS: 97        por kind: step=23, gate=31, prp=43
ARESTAS: 176   por kind: depends_on=155, blocks=21, rework=0
requires_human=31 · auto_parallelizable=44
ESTADOS DERIVADOS: pending=76, done=13, awaiting_human=5, ready=3
FRONTEIRA PARALELA REAL: ['ingestion_raw', 'step-11']   ← 2 nós
CAMINHO CRÍTICO: 45 nós (step-0.5 → gate-1 → step-1 → gate-2 → ...)
GraphNode campos: id, kind, requires_human, auto_parallelizable,
                  depends_on, produces, retry_of
```

E o teste fatal sobre REWORK:

```
add_rework_node("step-9") → step-9-retry-1  (depends_on=('step-9',))

original FAILED  (é exatamente o gatilho de rework) → rework fica PENDING | ready=[]
original DONE                                        → rework fica READY
original SKIPPED                                     → rework fica READY
```

**REWORK está estruturalmente morto.** `_state_satisfied()` exige `DONE|SKIPPED`; o rework só é criado quando o original **falhou**. Uma aresta estrutural foi usada para expressar uma transição comportamental — e não funciona.

### 0.2 Teste dos 15 requisitos contra o `llc_graph` atual

| #  | Requisito Statechart    | `llc_graph` hoje                                                                                                          | Veredito                         |
| -- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| 1  | Estados compostos       | Não. Grafo plano, `GraphNode` não tem `parent`                                                                            | **requer Core**                  |
| 2  | Regiões paralelas       | Parcial. `parallel_frontier()` calcula independência, mas não é região ortogonal com `done.state`; fronteira real = 2 nós | **requer Core**                  |
| 3  | Eventos                 | Não existe. Estado é *derivado* por leitura de arquivo                                                                    | **requer Core**                  |
| 4  | Guards puras            | Só `_deps_satisfied` (estrutural). Sem guarda de decisão                                                                  | **Core + DAG fornece predicado** |
| 5  | Actions                 | Não existem — engine é read-only por design (CQS)                                                                         | **requer Core**                  |
| 6  | entry/exit actions      | Não existem                                                                                                               | **requer Core**                  |
| 7  | Transições condicionais | Não existem (só precedência)                                                                                              | **requer Core**                  |
| 8  | Retries                 | Declarado, **inviável** (provado acima)                                                                                   | **requer Core**                  |
| 9  | REWORK                  | `EdgeKind.REWORK` existe; **0 ocorrências** no grafo real                                                                 | **requer Core**                  |
| 10 | AWAITING_HUMAN          | Existe e funciona (31 nós, 5 derivados)                                                                                   | **manter conceito no Core**      |
| 11 | Histórico               | Não. `AceStateReader` lê só a última sessão                                                                               | **requer Core + event log**      |
| 12 | Persistência            | Funciona: `.ace/index.json` + sessões                                                                                     | **manter**                       |
| 13 | Recovery pós-crash      | Funciona por derivação de disco                                                                                           | **manter + persistir config**    |
| 14 | Deterministic replay    | Módulo à parte (`llc_replay`), 0% hit                                                                                     | **ortogonal**                    |
| 15 | Capability por estado   | Não existe                                                                                                                | **requer Core**                  |

**Escore: 1,5 / 15.** (10 parcial, 12 e 13 atendidos.)

### 0.3 Veredito: **B — Separação de responsabilidades**

> **Não recomendo A (evolução direta).** `llc_graph` é um **modelo de dependência e impacto**: DAG, arestas `DEPENDS_ON/BLOCKS`, `impact_of`, `critical_path`. Um DAG não tem noção de **configuração ativa** — todos os 97 nós existem simultaneamente com estados independentes. Statecharts têm `configuration` (o conjunto do que está ativo agora), hierarquia, orthogonalidade e eventos. Adaptar o DAG a isso produziria exatamente a **abstração híbrida** que a revisão quer evitar, e o bug do REWORK é a prévia do resultado.

> **Não recomendo C (unificação).** Unificar grafos de dependência com semântica de execução num só modelo foi o que o próprio ADR-0004 §1.1 diagnosticou como fracasso ("fragmentados e não usados como fonte de verdade da execução"). Unificar não resolve a fragmentação — apenas desloca o acoplamento para dentro de um artefato só.

**Recomendação — B com uma precisão adicional:**

```
llc_graph  ──► DAG / dependency & impact model   (ADVISOR, read-only)
                 │  deps_satisfied · impact_of · critical_path · requires_human
                 ▼
Statechart ──► DETERMINISTIC CORE                (AUTHORITY)
                 │  states · events · guards · actions · capabilities
                 ▼
              Runtime (harness)
```

O DAG **não é um segundo orquestrador**. Ele é um **modelo de consulta que o Core consulta dentro das guards**. Uma única autoridade de transição — que era a preocupação legítima da Passagem 1.

**Granularidade:** não um statechart de 97 nós. São **N instâncias de uma `NodeMachine`** (uma por step/PRP), escalonadas pelo DAG. Paralelismo no LLC é **múltiplas instâncias**, não regiões ortogonais de uma máquina só. Regiões ortogonais são usadas *dentro* de um nó (ex.: `fitness ∥ coverage`).

---

## BLOCO 0.4 — Formalizar: Decision Pipeline ≠ Execution Runtime

A revisão está correta: o desenho anterior misturava as duas coisas.

```
═══ DECISION ENGINE (produz EVIDENCE + DECISION; não transiciona) ═══

  Candidate (proposta do agente / artefato)
        ↓
  [1] Hard EVAL — determinístico, barato        fitness·pytest·coverage·AST·semgrep·prp_verify
        ↓  resolveu? ──────────────► DECISION (sem Jev)
        ↓  não resolveu
  [2] Replay / Cached Decision — sem inferência
        ↓  hit? ─────────────────► DECISION (0 tokens)
        ↓  miss
  [3] Jev — semântica tipada (1 fan-out por Decision State)
        ↓
  [4] Decision Policy — evidência + risco + estado + retry → DECISION
        ↓
     Decision{ action, automation_level, reason, policy_version }
        ↓
     EVENT  ◄── única saída do Decision Engine
═══════════════════════════════════════════════════════════════════
                            │
═══ DETERMINISTIC CORE (executa; não avalia) ═══════════════════════

  State ──EVENT──► Guard(pura) ──► Transition ──► Action ──► New State
                            │
                            └──► Decision Record (append-only)
                                        │
                                        ▼
                              Deterministic Replay
```

**Invariante de fronteira:** o Decision Engine nunca escreve estado; o Core nunca chama LLM nem Jev.

---

# BLOCO 1 — DECISION POLICY

## 1.1 Interface

```python
@dataclass(frozen=True)
class Decision:
    action: Action            # enum
    automation: AutomationLevel   # AUTO | AUTO_AUDIT | REVIEW_REQUIRED | HUMAN_REQUIRED
    reason: str               # código estável, ex. "classification_confident"
    confidence: float | None  # min dos confidences envolvidos; None se só hard facts
    policy_id: str            # ex. "early-commitment"
    policy_version: str       # ex. "3.0.0"
    thresholds_hash: str      # sha256 do YAML de thresholds
    evidence_refs: tuple[str, ...]  # ids de HardEvalResult / JevAnswer usados


def decide(state: DecisionState,
           hard: HardEvalResult,
           semantic: JevResult | None,
           policy: PolicySpec) -> Decision: ...   # PURA, sem rede, sem IO
```

`decide()` é **pura e síncrona**. Testável sem Jev, sem LLM, sem disco.

## 1.2 Classificação ≠ Roteamento (§14)

```python
@dataclass(frozen=True)
class Classification:
    label: str                    # "crud_endpoint" | ... | "unknown"
    probabilities: dict[str, float]
    confidence: float

@dataclass(frozen=True)
class RoutingDecision:
    classification: Classification   # preservada SEMPRE
    action: Action
    automation: AutomationLevel
```

**Regra:** baixa confiança **nunca** descarta o rótulo — só rebaixa o roteamento.  
`confidence=0.61, label="BUG_FIX"` → `RoutingDecision(action=IMPLEMENT_WITH_REVIEW, automation=REVIEW_REQUIRED)`.  
Isto corrige `llc_classify.py:93`, que hoje retorna `None` abaixo de 0.80.

## 1.3 Risco

```python
class RiskClass(str, Enum):
    R0 = "R0"   # leitura / informacional — sem efeito
    R1 = "R1"   # escrita de artefato reversível (docs, PRP, ADR)
    R2 = "R2"   # mudança de código-fonte
    R3 = "R3"   # irreversível: migration, schema, auth, CI, secrets, deploy
```

Risco é derivado **deterministicamente** de `target_files` + `NodeKind` + zonas 🔴 (`llc_replay/zones.py`) — nunca pedido ao Jev.

## 1.4 Thresholds — centralizados, por (risco × primitiva)

Arquivo: `.ace/config/decision-policy.yaml` (versionado, hash registrado no Decision Record).  
**Nenhum threshold literal no código.**

| Risco | Choice/Score — AUTO | AUTO_AUDIT           | REVIEW_REQUIRED      | HUMAN_REQUIRED |
| ----- | ------------------- | -------------------- | -------------------- | -------------- |
| R0    | `conf >= 0.50`      | —                    | —                    | `conf < 0.50`  |
| R1    | `conf >= 0.70`      | `0.50 ≤ conf < 0.70` | —                    | `conf < 0.50`  |
| R2    | `conf >= 0.85`      | —                    | `0.70 ≤ conf < 0.85` | `conf < 0.70`  |
| R3    | **nunca AUTO**      | —                    | `conf >= 0.90`       | `conf < 0.90`  |

| Primitiva | Métrica de confiança                     | Decisão booleana                                           |
| --------- | ---------------------------------------- | ---------------------------------------------------------- |
| Choice    | `confidence` (docs)                      | `choice == esperado`                                       |
| Score     | `confidence` (docs)                      | `score >= nível_requerido` (índice 0..n-1)                 |
| Noul      | `\|2p − 1\|` (Noul não tem `confidence`) | `p ≥ 0.80` verdadeiro · `p ≤ 0.20` falso · entre = incerto |

**Thresholds escalam com risco** — é a recomendação explícita da documentação do Jev, não invenção.

## 1.5 Fallback e falha fechada

| Situação                                           | Decisão                                                                                      |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Hard EVAL falhou                                   | `HUMAN_REQUIRED`, `reason="hard_eval_failed"`. **Jev não pode override.**                    |
| Jev indisponível / timeout / schema inválido       | `HUMAN_REQUIRED`, `reason="semantic_unavailable"`. **Nunca AUTO por ausência de evidência.** |
| Resposta parcial do Jev (alguma pergunta faltando) | rebaixa um nível de automação                                                                |
| `confidence` ausente em Noul                       | usa `\|2p−1\|`; se `0.20 < p < 0.80` → `REVIEW_REQUIRED`                                     |
| Replay hit com `input_hash` igual                  | DECISION do registro, sem inferência                                                         |
| Replay hit com hash divergente                     | reavalia (drift)                                                                             |

**Isso fecha G7:** `auto_approve=True` global deixa de existir. Aprovação automática passa a exigir `automation == AUTO` **e** evidência anexada.

## 1.6 Catálogo de decisões

| ID                    | Pergunta                     | Risco típico | Pré-filtro determinístico           |
| --------------------- | ---------------------------- | ------------ | ----------------------------------- |
| `D-CLASSIFY-TASK`     | tipo da task                 | R0/R1        | —                                   |
| `D-GATE-CHECKLIST`    | item do gate satisfeito?     | R1           | `prp_verify`, `consistency-check`   |
| `D-DOC-QUALITY`       | qualidade do artefato        | R1           | schema, seções obrigatórias         |
| `D-SEMANTIC-IMPACT`   | impacto semântico no Δ       | R1/R2        | `GraphEngine.impact_of()`           |
| `D-ARCH-FIT`          | aderência arquitetural       | R2           | `fitness_functions` (6 checks arch) |
| `D-SECURITY-SEMANTIC` | risco semântico de segurança | R3           | semgrep, `checks_security` (5)      |
| `D-NEEDS-HUMAN`       | exige revisão humana?        | R0           | —                                   |



---

# BLOCO 2 — JEV SEMANTIC LAYER

## 2.1 Regra de ouro

> **Jev não é determinístico.** Ele fornece `Choice`, `Score`, `Noul`, `probabilities`, `confidence`. O determinismo é produzido por `Decision Policy + Statechart + Hard Evaluators + Replay`.

A documentação mede desvio-padrão run-to-run de 0.0 na maioria das perguntas, mas **não** garante bit-determinismo (2 de 13 Noul num benchmark carregavam ruído de amostragem). Nunca afirmar "mesma entrada ⇒ mesma classificação".

## 2.2 Primitivas e quando usar

| Primitiva | Retorna | Uso no LLC |
|---|---|---|
| **Choice** | `choice`, `probabilities`, `confidence` | `task_type`, `semantic_impact`, `risk_category`, diagnóstico de falha |
| **Score** | `score` (**índice do nível 0..n-1**), `legend`, `probabilities`, `confidence` | qualidade, severidade, alinhamento, completude |
| **Noul** | `noul` (0..1). **Sem `confidence`** | requisito satisfeito? precisa revisão? há conflito? |

**Armadilhas já confirmadas na API real:**
- `Score` não é "nota 1–5". Define-se `criteria` como lista ordenada; recebe-se o índice.
- `Noul` **não** retorna `confidence`. Usar `|2p − 1|` para colocá-lo no mesmo eixo.
- `confidence` é **por resposta**, nunca um campo único no topo.

## 2.3 Fan-out — uma chamada por Decision State

```
1 chamada  = Choice(task_type) + Choice(semantic_impact) + Score(complexity)
           + Score(quality) + Noul(needs_human_review) + Noul(security_impact)
```

Benchmark documentado (13 perguntas, documento de ~54k chars): **12.2× mais barato e 10.0× mais rápido** ($0.000497/0.27s vs $0.006090/2.71s). O ganho escala com o tamanho do documento — para artefatos curtos é menor. O custo é dominado por **input**; output é ínfimo (65 tokens p/ 3 perguntas).

**Não** colocar toda pergunta em toda chamada. O `Decision State` determina o conjunto mínimo.

## 2.4 Question Sets versionados

```yaml
# .ace/config/question-sets/task-classification:v2.yaml
id: task-classification
version: 2.0.0
model: jev-latest
questions:
  task_type:
    type: choice
    instructions: "..."
    criteria: { crud_endpoint: "...", ui_component: "...",
                validation_rule: "...", test_write: "...",
                unknown: "Não se encaixa em nenhuma" }   # fallback explícito
  complexity:
    type: score
    criteria: ["Trivial", "Pequena", "Média", "Grande"]
  needs_human_review:
    type: noul
    instructions: "..."
```

- `question_set.hash` entra no Decision Record.
- `fallback option` (`unknown`) é obrigatório em todo `Choice` — nunca deixar o modelo sem saída tipada.
- Trocar o modelo ou o question set **invalida apenas decisões futuras**; as antigas ficam reproduzíveis porque o registro carrega `model` + `question_set.hash` (responde "Evolução" do §31).

## 2.5 Contrato — testes de contrato obrigatórios

```
schema válido · options respeitadas · score dentro de 0..n-1 · noul dentro de 0..1
resposta faltando · API failure · timeout · modelo divergente do pin
```

---

# BLOCO 3 — STATECHART / RUNTIME

## 3.1 Duas máquinas, não uma

| Máquina | Instâncias | Papel |
|---|---|---|
| `NodeMachine` | uma por nó (step/PRP/gate) | ciclo de vida do nó |
| `Scheduler` | uma (usa `llc_graph`) | quais `NodeMachine` podem iniciar |

Biblioteca alvo: `python-statemachine ≥ 3.2` (`StateChart`, `State.Compound`, `State.Parallel`, `HistoryState`, `done.state`, `cond`/`unless`, composição com `|`). Python ≥ 3.10 — compatível com o LLC.

## 3.2 `NodeMachine` — estados

```python
class NodeMachine(StateChart):
    idle = State(initial=True)

    class active(State.Compound):
        preparing      = State(initial=True)
        agent_running  = State()

        class verifying(State.Parallel):        # regiões ortogonais
            class hard(State.Compound):
                hard_running = State(initial=True)
                hard_passed  = State(final=True)
                hard_failed  = State(final=True)
            class semantic(State.Compound):
                sem_running   = State(initial=True)
                sem_ready     = State(final=True)
                sem_not_needed= State(final=True)   # Jev desnecessário

        deciding   = State()
        applying   = State()               # executa efeito via Tools
        verifying_final = State(final=True)

    class governance(State.Compound):
        auto_approved    = State(initial=True)
        awaiting_human   = State()          # AWAITING_HUMAN
        h = HistoryState()
        rework           = State()

    done    = State(final=True)
    failed  = State(final=True)
    skipped = State(final=True)
```

> **Ids únicos entre regiões paralelas.** Com dois filhos chamados `passed`, `done.state` **não dispara** — verificado executando.

## 3.3 Eventos

`START` · `AGENT_RETURNED` · `HARD_EVAL_DONE` · `SEMANTIC_READY` · `SEMANTIC_NOT_NEEDED` · `DECIDED(decision)` · `APPLIED` · `RETRY` · `HUMAN_APPROVED` · `HUMAN_REJECTED` · `SKIP` · `FAIL`

Evento carrega dados; **nunca** decisão tomada pelo chamador (o chamador só entrega `Decision` vinda da Policy).

## 3.4 Guards (puras — sem rede, sem Jev, sem side effect)

| Guard | Fonte | Assinatura |
|---|---|---|
| `deps_satisfied` | **llc_graph** `impact_of`/`_deps_satisfied` | `(node_id) -> bool` |
| `hard_eval_passed` | `HardEvalResult` | `(hard) -> bool` |
| `semantic_required` | `HardEvalResult` + `question_set` | `(hard) -> bool` |
| `is_auto` / `is_auto_audit` / `is_review_required` / `is_human_required` | `Decision` | `(decision) -> bool` |
| `retries_left` | contador do nó | `(retries) -> bool` |
| `risk_requires_human` | `RiskClass` | `(decision) -> bool` |
| `gate_has_evidence` | `Decision.evidence_refs` | `(decision) -> bool` |

Contador de retry é **atributo da máquina incrementado por action** — nunca dentro de guard.

## 3.5 Actions e classificação de efeito

| Action | Idempotente | Retriable | Nota |
|---|---|---|---|
| `build_decision_state` | sim | sim | puro |
| `run_hard_eval` | sim | sim | read-only |
| `call_jev` | não | sim | custa tokens; cache por `input_hash` |
| `apply_policy` | sim | sim | puro |
| `invoke_agent` | não | sim | subprocess CLI, timeout 600s |
| `apply_changes` | não | **não** | requer rollback |
| `rollback` | sim | — | `git checkout` + `git clean` (padrão já usado em `llc_replay`) |
| `open_gate` | sim (por `gate_id`) | — | append `<gate_result …>` |
| `write_decision_record` | sim (por `decision_id`) | — | append-only JSONL |
| `increment_retries` | não | — | |

## 3.6 Transições — `STATE + EVENT + GUARD = NEXT`

| Atual | Evento | Guard | Próximo |
|---|---|---|---|
| `idle` | `START` | `deps_satisfied` | `active.preparing` |
| `idle` | `SKIP` | — | `skipped` |
| `active.preparing` | `AGENT_RETURNED` | — | `active.agent_running` |
| `active.agent_running` | `HARD_EVAL_DONE` | — | `active.verifying` |
| `active.verifying.hard` | `HARD_EVAL_DONE` | `hard_eval_passed` | `hard.hard_passed` |
| `active.verifying.hard` | `HARD_EVAL_DONE` | `not hard_eval_passed` | `hard.hard_failed` |
| `active.verifying.semantic` | `SEMANTIC_NOT_NEEDED` | `not semantic_required` | `semantic.sem_not_needed` |
| `active.verifying.semantic` | `SEMANTIC_READY` | — | `semantic.sem_ready` |
| `active.verifying` | `done.state` (ambas final) | — | `active.deciding` |
| `active.deciding` | `DECIDED` | `is_auto` | `governance.auto_approved` |
| `active.deciding` | `DECIDED` | `is_review_required` | `governance.awaiting_human` |
| `active.deciding` | `DECIDED` | `is_human_required` | `governance.awaiting_human` |
| `active.deciding` | `DECIDED` | `is_auto_audit` | `governance.auto_approved` (+flag audit) |
| `governance.auto_approved` | `APPLIED` | — | `active.applying` |
| `governance.awaiting_human` | `HUMAN_APPROVED` | — | `governance.auto_approved` |
| `governance.awaiting_human` | `HUMAN_REJECTED` | `retries_left` | `governance.rework` |
| `governance.awaiting_human` | `HUMAN_REJECTED` | `not retries_left` | `failed` |
| `governance.rework` | `RETRY` | — | `active.preparing` (via `HistoryState` se aplicável) |
| `active.applying` | `APPLIED` | `hard_eval_passed` | `active.verifying_final` → `done` |
| `active.applying` | `FAIL` | — | `governance.rework` ou `failed` |

**Diferença crítica vs. hoje:** rejeição → `rework`, **não** `return False` (fecha G11).

## 3.7 Human gate

- `awaiting_human` é estado estacionário; **não** há timeout que auto-aprova.
- Só sai por `HUMAN_APPROVED` / `HUMAN_REJECTED`, ambos com evidência anexada.
- Gate **consome** `Decision.evidence_refs` — `gate_check` deixa de ignorar `_output` (fecha G6).
- `waiver` continua existindo, mas passa a exigir registro de motivo e responsável.

## 3.8 Capability Matrix (fecha G9)

| Estado | Permitido | Negado |
|---|---|---|
| `idle` | `read_index`, `read_artifacts` | tudo mais |
| `active.preparing` | `read_*`, `build_decision_state`, `jev_eval` | escrita de código |
| `active.agent_running` | `read_*`, `write_artifacts` (R1), `run_tests` | `git_commit`, `deploy` |
| `active.verifying` | `run_hard_eval`, `jev_eval` | escrita |
| `active.deciding` | `apply_policy` | qualquer efeito |
| `governance.awaiting_human` | `show_evidence`, `request_approval` | escrita, `jev_eval`, `deploy` |
| `active.applying` | `apply_changes`, `git_commit` (R2), `rollback` | `deploy` (R3) |
| `done` / `failed` / `skipped` | `read_*` | tudo mais |

Implementação: `Capabilities.for_state(state) -> frozenset[str]`, consultado **antes** de cada tool call. A matriz é declarativa e testada por invariante (INV-008).

## 3.9 Persistência e recovery

```json
{ "node_id": "step-2", "machine": "NodeMachine",
  "configuration": ["active", "active.deciding"],
  "retries": 1, "gate_id": "3", "policy_version": "3.0.0",
  "last_event": "DECIDED", "updated_at": "..." }
```

- Arquivo por nó em `.ace/state/nodes/<node_id>.json`.
- Recovery = ler configuração + último Decision Record; **não** re-derivar só da última sessão (fecha G3/G11).
- O DAG continua derivando o que é estrutural; o Core persiste o que é comportamental.

---

# BLOCO 4 — DECISION STATE + DECISION RECORD

## 4.1 Cadeia de estados

```
Raw State (repo, fs, artefatos)
   ↓  reducers determinísticos
Derived State (.ace/index.json, sessões, llc_graph)
   ↓  projeção mínima + hash
Decision State
   ↓  Question Set (versionado)
Jev Result
   ↓  Decision Policy
Decision → Event → Statechart → Decision Record
```


## 4.2 `DecisionState` — schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DecisionState",
  "type": "object",
  "required": ["decision_id","node_id","state_id","decision_kind",
               "question_set","inputs","input_hash","state_hash",
               "risk_class","retry_count"],
  "properties": {
    "decision_id":   { "type": "string" },
    "node_id":       { "type": "string", "examples": ["step-2","prp-004","gate-3"] },
    "state_id":      { "type": "string", "examples": ["active.verifying.semantic"] },
    "decision_kind": { "type": "string", "examples": ["D-CLASSIFY-TASK"] },
    "question_set":  { "type": "object",
      "required": ["id","version","hash"],
      "properties": { "id": {"type":"string"}, "version": {"type":"string"},
                      "hash": {"type":"string"} } },
    "inputs":        { "type": "object" },
    "input_hash":    { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "state_hash":    { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "risk_class":    { "enum": ["R0","R1","R2","R3"] },
    "retry_count":   { "type": "integer", "minimum": 0 },
    "derived":       { "type": "object" }
  }
}
```

**Regra:** nunca enviar o repositório ao Jev. `inputs` contém apenas o mínimo — `task`, `changed_files`, `requirements`, `test_results`, `risk`, `retry_count`.
`input_hash` = sha256 canônico (JSON ordenado, UTF-8) de `inputs`.
`state_hash` = sha256 da configuração da máquina + hashes dos artefatos referenciados.

## 4.3 `DecisionRecord` — schema

```json
{
  "title": "DecisionRecord",
  "type": "object",
  "required": ["decision_id","timestamp","node_id","state_id","event",
               "input_hash","state_hash","policy","statechart","decision"],
  "properties": {
    "decision_id":  { "type": "string" },
    "timestamp":    { "type": "string", "format": "date-time" },
    "node_id":      { "type": "string" },
    "state_id":     { "type": "string" },
    "event":        { "type": "string" },
    "input_hash":   { "type": "string" },
    "state_hash":   { "type": "string" },
    "question_set": { "type": ["object","null"] },
    "jev": {
      "type": ["object","null"],
      "properties": {
        "model": {"type":"string","examples":["jev-1.13.0"]},
        "request_id": {"type":"string"},
        "answers": {"type":"object"},
        "probabilities": {"type":"object"},
        "usage": {"type":"object"}
      }
    },
    "hard_eval": { "type":"object" },
    "policy": {
      "type":"object",
      "required":["id","version","thresholds_hash","decision","automation","reason"],
      "properties": {
        "id":{"type":"string"}, "version":{"type":"string"},
        "thresholds_hash":{"type":"string"},
        "decision":{"type":"string"}, "automation":{"type":"string"},
        "reason":{"type":"string"}, "evidence_refs":{"type":"array"}
      }
    },
    "statechart": {
      "type":"object",
      "properties": {
        "version":{"type":"string"}, "from":{"type":"string"},
        "to":{"type":"string"}, "guard":{"type":"string"},
        "guard_result":{"type":"boolean"}
      }
    },
    "action":  { "type":["object","null"] },
    "human":   { "type":["object","null"] },
    "artifact_hashes": { "type":"array" }
  }
}
```

**Guardar `probabilities`, não só o valor final** — qualquer medida de confiança pode ser recomputada delas.
Formato do modelo é `jev-1.13.0` (não `typesafe-jev-1.13`).

## 4.4 Audit trail — respostas exigidas pelo §31

| Pergunta | Campo que responde |
|---|---|
| Como sabemos que a transição era permitida? | `statechart.from/to/guard/guard_result` + `Capabilities.for_state` |
| Por que o runtime decidiu isso? | `policy.reason` + `policy.evidence_refs` + `jev.answers` |
| Quem decidiu? | `policy.id` (máquina) ou `human.*` (pessoa) |
| Qual versão decidiu? | `policy.version`, `thresholds_hash`, `question_set.version`, `statechart.version`, `jev.model` |
| Qual evidência existia? | `hard_eval` + `jev.answers` + `artifact_hashes` |
| Qual efeito ocorreu? | `action` |

---

# BLOCO 5 — REPLAY

## 5.1 Dois modos, semanticamente distintos

| Modo | Usa Jev/LLM? | Objetivo |
|---|---|---|
| **REPLAY** | **não** | reproduzir execução e decisão a partir do Decision Record |
| **DRIFT** | sim (intencional) | medir se um modelo/policy novo mudaria decisões antigas |

## 5.2 Replay — algoritmo

```
para cada DecisionRecord (ordenação estável por decision_id/timestamp):
    1. assert input_hash == hash(DecisionState atual)   → senão: RE-EVAL, não replay
    2. decision' = decide(record.hard_eval, record.jev.answers, policy@record.policy_version)
    3. assert decision' == record.policy.decision
    4. event = to_event(decision')
    5. machine.send(event)
    6. assert machine.configuration == record.statechart.to
```

**Garantias:**
- *Reproducible execution:* mesmos eventos → mesmos estados. ✅ (statechart determinístico)
- *Reproducible decision:* mesmo Decision Record → mesma decisão. ✅ (`decide()` pura)
- *Reproducible inference:* mesma entrada → mesmo Jev. ❌ **não garantido, não perseguido.**

Custo do replay: **0 chamadas Jev, 0 chamadas LLM.**

## 5.3 Drift

```
record antigo + question_set igual + modelo novo
   ↓ re-inferência deliberada
comparar:
   - decisão mudou?            → DECISION_DRIFT   (bloqueia promoção de modelo)
   - só distribuição moveu?    → CONFIDENCE_DRIFT (reportar; limiar configurável)
   - nada mudou?               → STABLE
```

Métricas: L1 entre distribuições, delta de `confidence`, taxa de mudança de `automation_level`.

## 5.4 Relação com `llc_replay` existente

`llc_replay/` **não é substituído** — é o mecanismo de replay de *scripts*. O replay de *decisões* (BLOCO 5) é complementar e ataca o G1: hoje o cache está vazio e o hit rate é 0%. Meta mínima da Fase 7: **hit rate ≥ 40% em tasks repetidas.**

---

# BLOCO 6 — MIGRAÇÃO

## Princípio

Incremental, sem reescrita. Cada fase é reversível e termina com critério GO/NO-GO.

| Fase | Entrega | Arquivos | Risco | Rollback | Critério GO |
|---|---|---|---|---|---|
| **0** | Instrumentação: Decision Record mínimo + hashes | `llc_harness/*`, `.ace/logs/` | baixo | desligar flag | 100% dos steps com `input_hash` |
| **1** | Jev `Choice` no Early Commitment | `llc_classify.py` (caller trocado, interface preservada) | baixo | voltar caller LLM | acurácia ≥ LLM atual; 0 parsing errors |
| **2** | Decision Policy (thresholds YAML, `decide()` pura) | **novo** `llc_policy/` | médio | policy "pass-through" | 100% cobertura de testes; 0 threshold literal fora do YAML |
| **3** | Semantic EVAL: `Score`/`Noul` no `doc_judge` | `llc_evals/evaluators/doc_judge.py` | médio | manter doc_judge antigo por flag | concordância ≥ 80% com humano em golden set |
| **4** | `NodeMachine` — 1 nó piloto (step 11.2) | **novo** `llc_core/` | médio | scheduler antigo | transições reproduzíveis em replay |
| **5** | Capability Matrix | `llc_core/capabilities.py`, harness | médio | allowlist permissiva | 0 tool call fora da matriz em 100 execuções |
| **6** | Decision Record completo (versionado) | `.ace/logs/decisions.jsonl` | baixo | append-only | 100% das decisões com policy+statechart version |
| **7** | Replay + drift | **novo** `llc_decision_replay/` | médio | modo somente-leitura | hit rate ≥ 40%; replay sem Jev em 100% dos casos com hash igual |
| **8** | Smart Skip semântico (Jev só no residual) | `llc_delta/`, `llc_graph` | médio | `impact_of` puro | zero regressão de skip vs. baseline |

**Compatibilidade:** `llc.py`, `llc.py run`, `llc.py gate`, `wizard` e `eval` mantêm CLI inalterada. Nenhum formato de `.ace/sessions` muda (imutabilidade preservada).

## Métricas de sucesso (LLC 1.x → 2.0)

| Métrica | Baseline atual | Alvo |
|---|---|---|
| Replay hit rate | **0%** (18/18 fallback) | ≥ 40% |
| LLM calls / sessão | medir na Fase 0 | −30% |
| Jev calls / step | 0 | ≤ 1 (fan-out) |
| Parsing errors de LLM | > 0 (XML/JSON/MD) | 0 |
| Decisões sem evidência | 100% (gate ignora output) | 0 |
| Aprovações automáticas sem humano em R3 | possíveis (`auto_approve`) | 0 |
| Transições reproduzíveis em replay | n/a | 100% |
| Violações de capability | não medido (sem controle) | 0 |

---

## Invariantes (implementar testes na Fase 4+)

| ID | Invariante | Teste |
|---|---|---|
| INV-001 | LLM não muta estado de workflow | assert: nenhum caminho de `_llm_invoke` escreve `.ace/state/` |
| INV-002 | Toda transição vem de evento | assert `last_event` não-nulo em toda mudança de configuração |
| INV-003 | Toda transição automática tem guarda pura | guard executa sem rede/IO em teste isolado |
| INV-004 | Falha de Hard EVAL não é overridden por Jev | `hard_failed` + Jev confiante ⇒ ainda `HUMAN_REQUIRED` |
| INV-005 | Ação crítica exige humano | R3 nunca resulta em `AUTO` |
| INV-006 | Replay não requer inferência | replay roda com `jev=None`, `llm=None` |
| INV-007 | Toda decisão tem registro versionado | todo evento produz exatamente 1 DecisionRecord |
| INV-008 | Capacidades limitadas pelo estado | matriz × estados, teste exaustivo |
| INV-009 | Gate consome evidência | `gate` sem `evidence_refs` ⇒ rejeita |
| INV-010 | Rejeição gera rework, não aborta | `HUMAN_REJECTED` + `retries_left` ⇒ `rework` |
| INV-011 | Jev nunca é chamado dentro de guard | guard sem mock de rede |

---

## Resposta à revisão

| Ponto levantado | Decisão nesta passagem |
|---|---|
| A/B/C | **B** — com evidência: 1,5/15 requisitos atendidos pelo `llc_graph`; REWORK provadamente morto |
| Pipeline de decisão ≠ runtime de execução | Formalizado em BLOCO 0.4; fronteira é o **evento** |
| O que é Decision State | BLOCO 4.1–4.2: cadeia Raw → Derived → Decision + schemas + hashes |
| Não implementar antes de especificar | Schemas, interfaces, guards, actions e matriz de capacidades estão fechados acima |

**Nenhuma linha de código do LLC foi alterada.**
