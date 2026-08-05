# PRP: [GRAPH-2A] — `parallel_frontier()`: Dados Puros Agnósticos de Runtime

> **ID:** PRP-GRAPH-2A | **Trilha:** Graph Engineering | **Onda:** 3
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ⏳ Pending
> **Prioridade:** Médio | **ADR de origem:** ADR-0004 §2.7, §2.10 (Q2 resolvido)

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O paralelismo via worktrees já existe no LLC. O que falta é a resposta formal a "quais PRPs podem rodar em paralelo agora?". O `parallel_frontier()` entrega essa resposta como dados puros — uma lista de `GraphNode` independentes entre si, elegíveis para execução simultânea. Qualquer runtime (worktrees manuais, Herdr, ou nenhuma ferramenta) pode consumir essa lista.

**Princípio crítico (ADR-0004 Q2):** `parallel_frontier()` não sabe que o Herdr existe. Retorna dados; não executa nada.

### 1.2 O que é entregue

- [ ] `GraphEngine.parallel_frontier()` — retorna lista de nós `auto_parallelizable=True` mutuamente independentes
- [ ] Testes garantindo que nós com arestas entre si nunca aparecem juntos na frontier
- [ ] Integração com `wave_coordinator.py` (PRP-WAVE-COORD lê este output)

### 1.3 O que NÃO está no escopo

- ❌ Execução de PRPs (nunca — agnóstico de runtime)
- ❌ Integração com Herdr → PRP-HERDR-SKILL (condicional)
- ❌ `critical_path()` → PRP-GRAPH-2B

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-G2A.1 | `parallel_frontier()` retorna apenas nós `auto_parallelizable=True` | **Dado** mix de steps e PRPs, **Quando** `parallel_frontier()`, **Então** apenas PRPs na lista | Must | ⏳ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G2A.2 | Nós retornados são mutuamente independentes | **Dado** PRP-A → PRP-B, **Quando** `parallel_frontier()`, **Então** PRP-A e PRP-B **nunca** aparecem juntos | Must | ⏳ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G2A.3 | Frontier é subconjunto de `ready_nodes()` | **Dado** qualquer estado, **Quando** `parallel_frontier()`, **Então** todo elemento também está em `ready_nodes()` | Must | ⏳ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G2A.4 | `requires_human=True` nunca na frontier | **Dado** gate ready, **Quando** `parallel_frontier()`, **Então** gate ausente da lista | Must | ⏳ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G2A.5 | Output é lista de `GraphNode` — dados puros sem side-effects | **Dado** chamada N vezes, **Quando** `parallel_frontier()`, **Então** estado inalterado e resultado determinístico | Must | ⏳ | `tests/test_engine.py` | `llc_graph/engine.py` |

---

## 3. Contrato (agnóstico de runtime)

```python
def parallel_frontier(self) -> list[GraphNode]:
    """Retorna nós elegíveis para execução simultânea.

    Propriedades garantidas:
    - Todos têm auto_parallelizable=True
    - Nenhum tem requires_human=True
    - Nenhum par tem aresta entre si (independentes)
    - Subconjunto de ready_nodes()

    Este método retorna DADOS. Não executa, não invoca runtime,
    não sabe que Herdr, worktrees ou qualquer ferramenta existe.
    O consumidor decide o que fazer com a lista.
    """
```

---

## 4. Dependências

### Bloqueado por
- PRP-GRAPH-1B (`ready_nodes()` base)

### Desbloqueia
- PRP-GRAPH-2B (`critical_path`)
- PRP-WAVE-COORD (lê `parallel_frontier()` para sugestões)
- PRP-HERDR-SKILL (condicional — lê `parallel_frontier()` para visibilidade)

---

## 5. Definition of Done

- [ ] Todos os 5 RF com testes verdes
- [ ] Independência mútua garantida por teste (RF-G2A.2 — crítico)
- [ ] Sem side-effects, sem chamadas a runtime externo
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
