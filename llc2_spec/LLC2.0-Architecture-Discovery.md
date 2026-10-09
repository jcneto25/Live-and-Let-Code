# LLC 2.0 — Architecture Discovery (Passagem 1)

**Escopo desta passagem:** AS-IS → GAP → TARGET ARCHITECTURE.  
**Sem alteração de código.** Fonte de verdade: clone de `jcneto25/Live-and-Let-Code` @ `master` (443 arquivos).

---

## 0. Método

Todo componente citado abaixo foi lido no repositório. Nada foi inferido do README.  
Onde o README diverge do código, **o código é a fonte** e a divergência é registrada.

| Fonte                                                                 | Uso                                          |
| --------------------------------------------------------------------- | -------------------------------------------- |
| `.ace/scripts/**` (28 módulos Python)                                 | Inventário de runtime                        |
| `llc-pipeline-design.md`, `LLC_GUIDE.md`                              | Intenção declarada                           |
| `docs/architecture/adr/ADR-0004`, `ADR-0005`                          | Decisões aceitas (grafo, eval harness)       |
| `.ace/logs/replay.jsonl`, `.ace/index.json`, `.ace/config/gates.json` | **Evidência empírica** de comportamento real |

---

## 1. AS-IS — Arquitetura Atual

### 1.1 Fluxo ponta a ponta e classificação de mecanismo

```
ENTRADA
  task / documentos
        │
        ▼
CLASSIFICAÇÃO                                    [PROBABILISTIC]
  llc_harness/replay.py::agent_invoke
    └─ llc_classify.py::classify_task
         LLM CLI → XML textual → regex → confidence float → threshold 0.80
        │
        ▼
SELEÇÃO DE STEP                                  [DETERMINISTIC]
  llc_steps/registry.py (30 StepSpec) → pipeline_steps(from,to)
  llc_harness/pipeline.py::pipeline_run  → for-loop linear
        │
        ▼
CONTEXTO (ACE)                                   [HYBRID]
  initialize_session.py → context_seed (do índice)
  skill_load() → prompt
  _llm_invoke() → regex sobre output p/ extrair novo context_seed
        │
        ▼
AGENTE                                           [PROBABILISTIC]
  subprocess CLI via STDIN, timeout 600s, output = texto livre
        │
        ▼
FERRAMENTAS                                      [HUMAN-ENFORCED]
  Sem allowlist por estado. Restrição é documental (AGENTS.md)
  + imutabilidade de .ace/sessions (initialize/finalize/decisions)
        │
        ▼
EVAL                                             [HYBRID]
  Hard:  fitness_functions (41 checks), llm-validation.sh (8),
         prp_verify, consistency-check.py, code-health.py
  Soft:  llc_evals/evaluators/doc_judge.py (LLM-as-judge + rubric YAML → JSON → regex)
         llc_evals/evaluators/code_evaluator.py, efficiency_meter.py
        │
        ▼
GATE                                             [HUMAN]
  llc_harness/gates.py::gate_check → input() "a"/"r" no terminal
  UserDecisionWriter → <gate_result step decision waiver> (append)
  auto_approve=True em CI  ← FAIL-OPEN
        │
        ▼
ARTEFATOS + ESTADO DERIVADO                      [DETERMINISTIC]
  .ace/sessions/*.md (imutável) → .ace/index.json
  AceStateReader → NodeState (PENDING/READY/RUNNING/AWAITING_HUMAN/DONE/FAILED/SKIPPED)
  GraphEngine: ready_nodes / parallel_frontier / critical_path / impact_of  (read-only)
        │
        ▼
REPLAY                                           [DETERMINISTIC — INERTE]
  llc_replay/: find_best_script(threshold 0.60) → stale/arch/red-zone/preflight
  → deterministic_replay() com rollback via git
  ❌ NUNCA executou um hit (evidência na §1.4)
        │
        ▼
SMART SKIP / DELTA                               [PROBABILISTIC]
  DELTA_REPORT.md (escrito por LLM) → parse_delta_report() com regex → is_step_skipped
  GraphEngine.impact_of() existe e é determinístico, mas NÃO é usado aqui
```

### 1.2 Inventário de componentes

Formato exigido pela missão: **arquivo / função / responsabilidade / dependências / entrada / saída / problema**.

#### `.ace/scripts/llc_steps/registry.py`

- **função:** `REGISTRY: dict[str, StepSpec]`
- **responsabilidade:** fonte única dos steps (id canônico, nome, skill, gate, `in_pipeline`, `auto_worktree`, aliases)
- **dependências:** `llc_steps/models.py::StepSpec` (frozen dataclass)
- **entrada:** — (estático) / **saída:** `StepSpec`
- **problema:** a ordem do pipeline é `float(id)` — arestas de dependência são **implícitas na ordenação numérica**, não declaradas. Não há `depends_on` (confirmado por errata GOV-003/R2 no ADR-0004).

#### `.ace/scripts/llc_harness/pipeline.py`

- **função:** `pipeline_run(from_step, to_step, delta, auto_approve)`
- **responsabilidade:** loop sequencial: `step_run` → `gate_check` → `session_end` → `consistency-check`
- **dependências:** `llc_steps`, `llc_delta`, `.gates`, `.replay`, `.session`, `.skill`
- **entrada:** range de steps / **saída:** `bool` (sucesso) — **para no primeiro gate rejeitado**
- **problema:** (a) sequencial, ignora `llc_graph.parallel_frontier`; (b) rejeição = aborta o pipeline, não há transição de rework; (c) `auto_approve` falha aberto.

#### `.ace/scripts/llc_graph/engine.py`

- **função:** `GraphEngine.node_state / ready_nodes / parallel_frontier / critical_path / impact_of`
- **responsabilidade:** scheduler **read-only** do DAG (ADR-0004 §2.7)
- **dependências:** `llc_graph/model.py`, `llc_graph/state.py`, `.ace/index.json`, `.ace/sessions`
- **entrada:** grafo + estado derivado / **saída:** listas de nós (queries puras, CQS)
- **problema:** **não dirige a execução** — o próprio docstring diz "NÃO executa nada, NÃO invoca runtime". É uma camada de consulta sobre um executor que ainda é um `for`.

#### `.ace/scripts/llc_graph/state.py`

- **função:** `AceStateReader.node_state(node_id)`
- **responsabilidade:** derivar `NodeState` de `.ace/index.json`
- **entrada:** node_id / **saída:** `NodeState`
- **problema:** lê apenas a **última** sessão do step (`max(timestamp)`); não há histórico de transições nem eventos.

#### `.ace/scripts/llc_classify.py`

- **função:** `classify_task(task_description, client)`
- **responsabilidade:** Early Commitment — classificar task em 4 tipos
- **dependências:** `subprocess` p/ CLI (`claude|opencode|codex|cursor`)
- **entrada:** texto da task / **saída:** `{type, confidence, reasoning}` **ou `None`**
- **problema:** `CONFIDENCE_THRESHOLD = 0.80`; **abaixo do limiar retorna `None` e a classificação é descartada** — exatamente o anti-padrão do §14 da missão. Confidence é um número **pedido ao LLM e extraído por regex**, não uma distribuição. Usa `client --prompt` (via argv) enquanto `llc_harness` usa STDIN — dois caminhos de invocação inconsistentes.

#### `.ace/scripts/llc_replay/*` (`cache`, `match`, `zones`, `execute`)

- **função:** `find_best_script`, `deterministic_replay`, `log_replay_event`
- **responsabilidade:** reexecutar scripts parametrizados em vez de chamar LLM
- **dependências:** `.ace/cache` (**inexistente**), `CLAUDE.md` (arch version), git
- **entrada:** `task_type` + descrição / **saída:** replay ou fallback p/ LLM
- **problema:** match por interseção de palavras com `threshold = 0.60`; **zero hits registrados** (§1.4).

#### `.ace/scripts/llc_evals/evaluators/doc_judge.py`

- **função:** `DocJudge.judge(...)`, `should_run(phase)`
- **responsabilidade:** LLM-as-judge sobre rubrics YAML por step
- **dependências:** LLM injetado (tool-agnostic), `rubrics/rubric-step-{0.5,1,2,3,5}.yaml`
- **entrada:** artefato + upstream / **saída:** `{step_id, scores, aggregate, error}`
- **problema:** prompt pede "APENAS JSON", `parse_response` usa regex + fallback; score é 0–100 livre; **não há confidence nem distribuição**; roda só em `{gate, sampling}` por restrição de custo (D10).

#### `.ace/scripts/llc_evals/instrument.py`

- **função:** `capture_tokens`, `build_eval_metrics`
- **responsabilidade:** medir tokens/custo em 3 níveis (log nativo / bloco estruturado / estimativa heurística 75-25)
- **problema:** nível 3 é estimativa (`tiktoken` opcional); precisão degrada conforme o cliente de IA (tool-agnostic).

#### `.ace/scripts/llc_delta/report.py` + `skip.py`

- **função:** `parse_delta_report`, `is_step_skipped`, `generate_skip_note`
- **responsabilidade:** Smart Skip — decidir quais steps executar/pular
- **entrada:** `DELTA_REPORT.md` / **saída:** `{change_type, execute_steps, skip_steps, iteration}`
- **problema:** o plano é **escrito por um LLM em markdown** e lido por regex sobre tabelas (com normalização de acentos). A decisão de skip é portanto probabilística e frágil — e o determinístico (`GraphEngine.impact_of`) já existe.

#### `.ace/scripts/llc_harness/gates.py`

- **função:** `gate_check(step, _output, auto_approve)`
- **responsabilidade:** exibir checklist e coletar A/R humano
- **entrada:** step / **saída:** `"approved" | "rejected"`
- **problema:** `_output` é ignorado (assinatura legacy) — **o gate não consome evidência do EVAL**; `auto_approve=True` aprova sem evidência; timeout não existe (bloqueia indefinidamente).

#### `.ace/scripts/llc_wizard/decisions.py`

- **função:** `UserDecisionWriter.write_gate_decision`
- **responsabilidade:** mutador sancionado p/ append de `<gate_result step decision waiver>`
- **problema:** é o ÚNICO registro estruturado de decisão humana — mas não tem hash, policy version nem evidência anexada.

### 1.3 Onde está o quê (matriz exigida pela missão)

| Pergunta                   | Onde                                                                                    | Mecanismo                              |
| -------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------- |
| Onde existe LLM            | `_llm_invoke` (step), `classify_task`, `doc_judge`                                      | subprocess CLI                         |
| Parsing de texto de LLM    | `classify.py` (XML), `_llm_invoke` (context_seed), `doc_judge` (JSON), `report.py` (MD) | `re.search`                            |
| Confidence é **produzida** | `llc_classify.py` — número pedido ao LLM                                                | textual                                |
| Confidence é **usada**     | `llc_classify.py:93` (threshold 0.80) e `match.py:34` (0.60)                            | 2 pontos, hardcoded                    |
| Decisão direta por LLM     | DELTA_REPORT.md → Smart Skip                                                            | indireta, via markdown                 |
| Side effect                | `execute.py` (write/insert/replace/run), `finalize_session`, git                        | não classificado idempotente/retriable |
| Estado implícito           | `context_seed` em `.ace/sessions/*.md`                                                  | texto                                  |
| Estado persistível         | `.ace/index.json`, `.ace/evals/state.yaml`, `.ace/sessions`                             | JSON/YAML/MD                           |
| Replay                     | `llc_replay/` + `.ace/logs/replay.jsonl`                                                | determinístico, inerte                 |
| Replay pode divergir       | sim: `stale` (sha8), `arch_changed` (string de CLAUDE.md), `preflight_fail`             | heurístico                             |



### 1.4 Evidência empírica (medida, não inferida)

```
.ace/logs/replay.jsonl  → 18 eventos, TODOS "llm_fallback" (reason=no_classify)
                           0 "replay_hit", 0 "replay_success", 0 "replay_rollback"
.ace/cache/             → NÃO EXISTE no repositório
```

**Conclusão: o subsistema de replay do LLC tem hit rate 0%.** Ele não está "quase pronto" — nunca disparou. Qualquer proposta de "Deterministic Replay" para LLC 2.0 começa aqui, não do zero.

```
gates.json: 31 gate keys, 133 itens de checklist, 0 gates com output_files
registry.py: 30 StepSpec (23 in_pipeline, 2 delta, 5 pós-execução/advisory)
fitness: 41 checks (arch 6, clean 16, deep-clean 8, governance 1, security 5, ux 5)
rubrics_doc_judge: 5 (steps 0.5, 1, 2, 3, 5)
```

> Divergência: README declara "24 pipeline + 2 Δ steps, 26 gates". O código tem **23 in_pipeline + 2 Δ** e **31 gate keys**. Os números do README são aproximações de marketing; o registry é a fonte.

---

## 2. GAPS

| #       | Gap                                                                                                   | Evidência                                            | Impacto                                                                                   |
| ------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **G1**  | **Replay inerte** — cache nunca populado, classificação sempre falha antes                            | 18/18 eventos = `llm_fallback`; `.ace/cache` ausente | Todo step paga LLM completo. Maior desperdício do sistema.                                |
| **G2**  | **Grafo não executa** — `GraphEngine` é query, `pipeline_run` é `for`                                 | docstring engine.py: "NÃO executa nada"              | Paralelismo (`parallel_frontier`) e caminho crítico existem mas são inúteis em runtime.   |
| **G3**  | **Sem máquina de estados** — estado é derivado por leitura de arquivo, não por transição              | `AceStateReader.node_state` lê última sessão         | Não há evento, guarda, invariante nem histórico de transição. Auditoria impossível.       |
| **G4**  | **Confidence frágil e espalhada** — número textual do LLM, 2 thresholds hardcoded                     | `classify.py:93` (0.80), `match.py:34` (0.60)        | Baixa confiança **descarta** classificação em vez de rotear (§14 violado).                |
| **G5**  | **Sem Decision Policy** — não existe camada entre avaliação e transição                               | ausência de módulo                                   | Não é possível responder "qual regra produziu esta decisão?".                             |
| **G6**  | **Gate ignora evidência** — `gate_check(step, _output)` descarta o output                             | parâmetro `_output` não usado                        | EVAL e gate humano são desconectados: o humano decide sem ver o score.                    |
| **G7**  | **Fail-open em CI** — `auto_approve=True` aprova sem humano e sem evidência                           | `gates.py:50`                                        | Viola "IA propõe, humano dispõe" em execução automatizada.                                |
| **G8**  | **Smart Skip probabilístico** — decisão vem de markdown gerado por LLM                                | `parse_delta_report` regex                           | `impact_of()` determinístico já existe e está fora do caminho.                            |
| **G9**  | **Sem controle de capacidade por estado** — AGENTS.md é advisory                                      | nenhum allowlist por estado                          | LLM pode executar ação proibida fora do replay; só zonas 🔴 são checadas, e só em replay. |
| **G10** | **Sem Decision Record versionado** — `<gate_result>` e `replay.jsonl` não têm hash nem policy version | `decisions.py:99`, `execute.py:116`                  | Replay não é reproduzível de forma verificável (falta `input_hash`/`state_hash`).         |
| **G11** | **Rejeição = abortar** — não há transição de rework                                                   | `pipeline.py:126` `return False`                     | Desperdiça todo o trabalho; ADR-0004 já prevê aresta `REWORK`.                            |
| **G12** | **Medição de custo estimada** — nível 3 heurístico (75/25)                                            | `instrument.py:77`                                   | Métricas de economia do LLC 2.0 não podem ser comparadas com segurança.                   |

---

## 3. TARGET ARCHITECTURE

### 3.1 Princípio (alinhado à missão, com uma correção de precedência)

> O agente pode propor eventos e interpretações. Somente o Deterministic Core pode aceitar eventos, executar transições e liberar capacidades.

**Correção ao diagrama da missão:** no desenho original, `EVAL` aparece *abaixo* do Core, como consumidor. Na cascata que o próprio prompt define (§21), **Hard EVAL é pré-filtro** — ele pode tornar Jev desnecessário. A ordem correta é:

```
Hard EVAL (barato, determinístico)
      ↓  só se não resolver
Replay / Cache
      ↓  só se não houver hit
Jev (semântica)
      ↓
Decision Policy
      ↓
Statechart
      ↓
Tools (capacidades liberadas pelo estado)
      ↓
Human (exceções de alto risco)
      ↓
Decision Record → Replay
```

### 3.2 Diagrama-alvo

```
                            AGENTIC SHELL (probabilístico)
                     LLM CLI: skills, geração, proposta de eventos
                                      │  propõe evento + artefato
                                      ▼
                    ┌─────────────────────────────────────┐
                    │  HARD EVAL  (pré-filtro barato)     │
                    │  fitness 41 · pytest · coverage     │
                    │  AST · semgrep · ruff · prp_verify  │
                    │  GraphEngine.impact_of (determin.)  │
                    └─────────────────────────────────────┘
                          │ resolvido? ──► vai direto ao Core
                          │ não resolvido
                          ▼
                    ┌─────────────────────────────────────┐
                    │  REPLAY / CACHED DECISION           │
                    │  llc_replay (hoje 0% hit → alvo)    │
                    └─────────────────────────────────────┘
                          │ miss
                          ▼
                    ┌─────────────────────────────────────┐
                    │  SEMANTIC LAYER — Jev               │
                    │  Choice · Score · Noul              │
                    │  + probabilities · confidence       │
                    │  1 chamada fan-out por Decision State│
                    └─────────────────────────────────────┘
                          │ resultado tipado (não-heróico)
                          ▼
                    ┌─────────────────────────────────────┐
                    │  DECISION POLICY  (nova)            │
                    │  thresholds por risco/ação/pergunta │
                    │  saída: Decision + reason + policy_v│
                    └─────────────────────────────────────┘
                          │ evento
                          ▼
        ┌─────────────────────────────────────────────────────────┐
        │            DETERMINISTIC CORE — Statechart               │
        │  estados · eventos · guards puras · actions · retries    │
        │  regiões paralelas (waves) · AWAITING_HUMAN · REWORK     │
        │  Capability Matrix: libera tools por estado              │
        └─────────────────────────────────────────────────────────┘
                     │                    │                  │
                     ▼                    ▼                  ▼
              TOOLS (efeito)      HUMAN GATE           DECISION RECORD
           idempotência classif.   A/R + waiver          hash + versões
                     │                    │                  │
                     └────────────────────┴──────────────────┘
                                      ▼
                            DETERMINISTIC REPLAY
                     (Record → Policy → Statechart → mesma transição)
```

### 3.3 Matriz de responsabilidade (Component × Autoridade)

| Componente                 | Responsabilidade                                 | Autoridade                      | Pode chamar LLM? | Pode alterar estado? |
| -------------------------- | ------------------------------------------------ | ------------------------------- | ---------------- | -------------------- |
| Agentic Shell (skills/LLM) | gerar, interpretar, propor                       | **propõe**                      | sim              | **não**              |
| Hard EVAL                  | verificar fatos objetivos                        | **veta** (falha não é override) | não              | não (leitura)        |
| Replay/Cache               | reproduzir decisão conhecida                     | **resolve sem inferência**      | não              | não                  |
| Semantic Layer (Jev)       | decidir propriedades semânticas                  | **avalia** (nunca executa)      | é o modelo       | **não**              |
| Decision Policy            | converter avaliação + risco em decisão           | **decide**                      | não              | não                  |
| Statechart (Core)          | aceitar evento, transicionar, liberar capacidade | **autoriza**                    | não              | **sim — único**      |
| Tools                      | efeito colateral                                 | executa                         | não              | só artefatos         |
| Human Gate                 | aprovar/rejeitar/waiver                          | **override**                    | —                | via evento           |
| Decision Record            | auditar/reproduzir                               | **registra**                    | não              | append-only          |

### 3.4 Onde Jev entra (catálogo preliminar — passagem 2 fecha thresholds)

| Decisão                          | Primitiva                          | Substitui                          | Justificativa                                               |
| -------------------------------- | ---------------------------------- | ---------------------------------- | ----------------------------------------------------------- |
| `task_type` (Early Commitment)   | **Choice**                         | `llc_classify.py` (XML+regex+0.80) | mata parsing; devolve distribuição real                     |
| `semantic_impact` no Δ           | **Choice/Score**                   | parte do DELTA_REPORT.md           | só o residual não coberto por `impact_of()`                 |
| Qualidade de artefato documental | **Score** (por dimensão do rubric) | `doc_judge.py` (JSON+regex)        | pesos ficam no código (Composite Scoring)                   |
| Checklist do gate (133 itens)    | **Noul** (fan-out por gate)        | nada (humano lê tudo hoje)         | 1 chamada por gate aponta o item exato                      |
| `needs_human_review`             | **Noul**                           | heurística implícita               | explicita o roteamento                                      |
| Classificação × roteamento       | Choice + Policy                    | —                                  | baixa confiança → `REVIEW_REQUIRED`, **não** descarta (§14) |



**Jev NÃO entra em:** fitness functions, cobertura, AST, semgrep, `prp_verify`, `consistency-check`, `impact_of`, contagem/regra matemática.

### 3.5 Não recomendações (com motivo)

> **Não recomendo criar um Statechart novo como núcleo, substituindo `llc_graph`.**  
> O ADR-0004 já define um modelo de grafo com `NodeState` (incluindo `AWAITING_HUMAN`, `SKIPPED`), arestas `BLOCKS`/`REWORK`, `ready_nodes`, `parallel_frontier`, `critical_path` e `impact_of`. Um statechart paralelo criaria **duas fontes de verdade de orquestração** — o fracasso que o próprio ADR-0004 §1.1 diagnostica ("fragmentados e não usados como fonte de verdade da execução"). O caminho é **dar semântica de transição ao GraphEngine** (eventos + guards puras + histórico), não substituí-lo.

> **Não recomendo Temporal.io (nem qualquer workflow engine).**  
> O estado do LLC já é durável por natureza: `.ace/sessions/*.md` + `.ace/index.json` em disco, e `AWAITING_HUMAN` já é um estado estacionário que sobrevive a restart de processo sem infraestrutura alguma. Temporal adiciona servidor, workers e serialização para resolver um problema que o formato de arquivo já resolve.

> **Não recomendo Jev para Smart Skip como mecanismo primário.**  
> `GraphEngine.impact_of()` já produz a propagação determinística. Jev entra somente no impacto **semântico** residual (mudança de comportamento sem mudança estrutural), e só quando `impact_of` não for conclusivo.

> **Não recomendo construir Decision Record do zero.**  
> `.ace/logs/replay.jsonl`, `<eval_metrics>` e `<gate_result>` já existem. O que falta é **hash de entrada, hash de estado, versão de política e versão de question set** —campos, não um subsistema novo.

> **Não recomendo manter `auto_approve` como booleano global.**  
> É fail-open (G7). Precisa virar `min_automation_level` por gate, derivado do risco.

### 3.6 Invariantes propostos (passagem 2 detalha testes)

| ID      | Invariante                                         | Violado hoje?                              |
| ------- | -------------------------------------------------- | ------------------------------------------ |
| INV-001 | LLM não muta estado de workflow diretamente        | não (já ok: initialize/finalize/decisions) |
| INV-002 | Toda transição é representada por um evento        | **sim** (G3)                               |
| INV-003 | Toda transição automática tem guarda pura          | **n/a** (não há transições)                |
| INV-004 | Falha de Hard EVAL não pode ser overridden por Jev | **não testável** (sem Jev, sem policy)     |
| INV-005 | Ação crítica exige aprovação humana explícita      | **sim** (G7)                               |
| INV-006 | Replay não requer inferência de LLM/Jev            | **sim** (G1 — replay nem roda)             |
| INV-007 | Toda decisão tem Decision Record versionado        | **sim** (G10)                              |
| INV-008 | Capacidades do agente são limitadas pelo estado    | **sim** (G9)                               |
| INV-009 | Gate consome evidência do EVAL                     | **sim** (G6)                               |
| INV-010 | Rejeição gera rework, não aborta pipeline          | **sim** (G11)                              |

### 3.7 Decomposição recomendada (resumo — detalhe na passagem 2)

| Camada                                     | Situação                          | Ação                                                     |
| ------------------------------------------ | --------------------------------- | -------------------------------------------------------- |
| `llc_steps`                                | fonte única de steps              | **KEEP** (+ declarar `depends_on`)                       |
| `llc_graph`                                | query determinística, não executa | **MODIFY** → virar o executor com semântica de transição |
| `llc_harness/pipeline.py`                  | for-loop                          | **REPLACE** → driven pelo Core                           |
| `llc_classify.py`                          | LLM+XML+regex                     | **MODIFY** → caller Jev `Choice` (interface preservada)  |
| `llc_replay/`                              | determinístico, 0% hit            | **MODIFY** → popular cache, subir hit rate (G1)          |
| `llc_evals/doc_judge.py`                   | LLM+JSON+regex                    | **MODIFY** → caller Jev `Score` por dimensão             |
| `llc_evals/` (instrument/aggregate/report) | ok                                | **KEEP**                                                 |
| `fitness_functions/`                       | 41 checks determinísticos         | **KEEP** (intocável)                                     |
| `llc_delta/`                               | parse de markdown de LLM          | **MODIFY** → `impact_of` primeiro, Jev no residual       |
| `llc_harness/gates.py`                     | A/R sem evidência                 | **MODIFY** → consome Decision + evidência                |
| **Decision Policy**                        | não existe                        | **CREATE**                                               |
| **Decision Record**                        | parcial                           | **CREATE** (versionado)                                  |
| **Capability Matrix**                      | não existe                        | **CREATE**                                               |
| `llc_wizard/`                              | TUI Kanban                        | **KEEP** (+ exibir Decision/Policy)                      |

---

## 4. Próxima passagem

Fechar, nesta ordem: (1) Decision Policy + catálogo Jev com thresholds por risco; (2) Statechart concreto (estados/eventos/guards/actions/capacidades) **sobre o GraphEngine**; (3) schemas de Decision State e Decision Record; (4) desenho de replay + drift; (5) plano de migração por fase; (6) mapa arquivo-a-arquivo e estratégia de testes.

**Nenhuma alteração de código foi feita nesta passagem.**
