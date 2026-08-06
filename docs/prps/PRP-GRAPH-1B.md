# PRP: [GRAPH-1B] — `engine.py`: ready_nodes() + impact_of() + Smart Skip Delta

> **ID:** PRP-GRAPH-1B | **Trilha:** Graph Engineering | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 1,5 semanas | **Status:** ✅ Done (2026-08-06)
> **Prioridade:** Médio | **ADR de origem:** ADR-0004 §2.7, §2.11, §2.12

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com o modelo e o builder do PRP-GRAPH-1A, o grafo existe mas é estático. Este PRP entrega o `GraphEngine` — o scheduler read-only que responde "quais nós estão prontos para execução?" e "quais nós são afetados por uma mudança?". É a fundação para Smart Skip formal e para a futura coordenação reativa.

> **Relação com o `impact-analyzer.py` (GOV-003/R11):** o `GraphEngine.impact_of()` e o `impact-analyzer.py` **coexistem**, não se substituem. O `impact-analyzer.py` opera no universo de **artefatos** (`docs/prps/`, `docs/planning/`) e cobre etapas pré-código; o `GraphEngine.impact_of()` opera no universo de **nós do DAG de steps ACE** (runtime). A migração/adoção gradual para Smart Skip (ver `llc-smart-skip.md`) deve manter o `impact-analyzer.py` como fonte para análise de artefatos documentais até que a ponte artefato↔node esteja formalizada no ADR-0004.

### 1.2 O que é entregue

- [x] `llc_graph/engine.py` — `GraphEngine` com `node_state()`, `ready_nodes()`, `impact_of()`
- [x] Tratamento correto do fluxo delta (Smart Skip: `SKIPPED` equivale a `DONE` para dependências)
- [x] Teste obrigatório do caso delta: nó com deps `SKIPPED` fica `READY`
- [x] Invariante documentado: `ready_nodes()` nunca substitui gates de fitness

### 1.3 O que NÃO está no escopo

- ❌ `parallel_frontier()` → PRP-GRAPH-2A
- ❌ `critical_path()` → PRP-GRAPH-2B
- ❌ Projeção para Kanban → PRP-GRAPH-1C

---

## 2. Requisitos Funcionais (TDD — críticos)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-G1B.1 | `ready_nodes()` retorna nós com todas as deps `DONE` | **Dado** A→B, A=DONE, **Quando** `ready_nodes()`, **Então** B está na lista | Must | ✅ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G1B.2 | `ready_nodes()` **nunca** auto-avança `requires_human=True` | **Dado** gate com deps satisfeitas, **Quando** `ready_nodes()`, **Então** gate retornado como `AWAITING_HUMAN`, nunca `READY` para auto-execução | Must | ✅ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G1B.3 | `SKIPPED` equivale a `DONE` para fins de dependência | **Dado** A→B→C, B=SKIPPED via Smart Skip, **Quando** `ready_nodes()`, **Então** C está `READY` | Must | ✅ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G1B.4 | `impact_of(node_id)` propaga para todos os descendentes | **Dado** A→B→C, **Quando** `impact_of("A")`, **Então** `{"B", "C"}` retornado | Must | ✅ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G1B.5 | `impact_of()` é puro (sem side-effects) | **Dado** chamadas múltiplas, **Quando** `impact_of()` N vezes, **Então** estado do grafo inalterado | Must | ✅ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G1B.6 | Rework cria nova instância sem ciclo no DAG | **Dado** step-5 com `retry_of`, **Quando** `ready_nodes()`, **Então** step-5-retry-1 aparece, step-5 original não reaparece | Must | ✅ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G1B.7 | Determinismo: mesmo estado ACE → mesmo resultado | **Dado** estado ACE fixo, **Quando** `ready_nodes()` chamado N vezes, **Então** resultado idêntico | Must | ✅ | `tests/test_engine.py` | `llc_graph/engine.py` |

---

## 3. Invariante do Contrato (documentado em código)

```python
# engine.py — invariante obrigatório
# ready_nodes() decide ELEGIBILIDADE DE EXECUÇÃO (deps DAG satisfeitas).
# NÃO decide qualidade de merge — isso é Gate 10.8/11.3 (fitness functions).
# Os dois sistemas são camadas consecutivas, nunca alternativas.
# Um nó READY pode ainda falhar no gate de fitness — comportamento correto.
```

---

## 4. Dependências

### Bloqueado por
- PRP-GRAPH-1A

### Desbloqueia
- PRP-GRAPH-1C (projeção Kanban do engine)
- PRP-GRAPH-2A (`parallel_frontier`)

---

## 5. Definition of Done

- [x] Todos os 7 RF com testes verdes
- [x] Teste explícito do caso delta (RF-G1B.3) com comentário explicativo
- [x] `ready_nodes()` nunca retorna nó `requires_human` como auto-executável (RF-G1B.2 — crítico)
- [x] `impact_of()` puro — sem efeitos colaterais
- [x] Cobertura ≥ 85% em `engine.py` *(91% na suite do pacote — engine 89%, state 91%, TOTAL 96%)*
- [x] `fitness-functions.py --all --strict` verde
- [x] Sessão ACE registrada

---

## 7. Nota de Execução (2026-08-06)

Entregue via TDD (sessão ACE `2026-08-06-014`, step 10.9 — Domain Modeling):

- **`llc_graph/engine.py`** — `GraphEngine` com `node_state()` (precedência: ACE real →
  `<gate_result>` real da sessão do step gateado → deps → `READY`/`AWAITING_HUMAN`),
  `ready_nodes()` (determinístico, ordenado por id) e `impact_of()` (BFS descendente
  sobre todas as arestas — conservador p/ Smart Skip).
- **Contrato BLOCKS (ADR-0004 §2.4)** implementado: sucessor de gate não fica `READY`
  enquanto o gate não for aprovado; a aprovação é lida de `<gate_result decision="approved">`
  no `.md` da sessão (placeholders em comentários HTML ignorados) — espelha o padrão de
  `llc_wizard/data.py` sem importá-lo (DIP).
- **Descoberta de design:** a estrutura do DAG vive nas **arestas** (o `GraphBuilder` não
  popula `depends_on` de steps/gates — só de retries). `_deps_satisfied()` unifica
  `node.depends_on` + sources de arestas de entrada (DEPENDS_ON/REWORK/BLOCKS).
- **Suporte (`state.py`):** mapeamento `status: "skipped"` → `NodeState.SKIPPED`
  (delta flow, ADR-0004 §2.12) — 2 linhas + 1 teste.
- **13 testes novos** (12 engine + 1 state); suite do pacote 34 verdes.
  Suite completa **383 passed**, fitness **41/41**, DIP sem imports de `llc_wizard`/`llc_harness`.
