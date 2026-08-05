# PRP: [GRAPH-2B] — `critical_path()` + Métricas de Gargalo

> **ID:** PRP-GRAPH-2B | **Trilha:** Graph Engineering | **Onda:** 3
> **Owner:** jcneto25 | **Estimativa:** 0,5 semana | **Status:** ⏳ Pending
> **Prioridade:** Baixo | **ADR de origem:** ADR-0004 §2.7, §2.10

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com o grafo completo e `parallel_frontier()` funcionando, a pergunta "onde está o gargalo do pipeline?" tem resposta formal: o caminho crítico do DAG. Este PRP entrega `critical_path()` — o caminho mais longo do grafo, que determina a duração mínima possível do pipeline mesmo com paralelismo máximo.

### 1.2 O que é entregue

- [ ] `GraphEngine.critical_path()` — algoritmo de caminho crítico em DAG (topological sort + longest path)
- [ ] Integração com `PRP-EVALS-F5` — `EfficiencyScore` pode ponderar o caminho crítico
- [ ] `to_critical_path()` em `projections.py` (stub de PRP-GRAPH-1C agora implementado)

### 1.3 O que NÃO está no escopo

- ❌ Dashboard visual do caminho crítico (futuro)
- ❌ Otimização automática baseada no critical path (futuro)

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-G2B.1 | `critical_path()` retorna caminho mais longo do DAG | **Dado** grafo com 2 caminhos de comprimento 3 e 5, **Quando** `critical_path()`, **Então** retorna o de comprimento 5 | Must | ⏳ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G2B.2 | Caminho crítico inclui gates (eles têm custo de espera) | **Dado** DAG com gates no caminho, **Quando** `critical_path()`, **Então** gates incluídos | Must | ⏳ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G2B.3 | `critical_path()` é puro (sem side-effects) | **Dado** chamadas múltiplas, **Quando** `critical_path()`, **Então** estado inalterado | Must | ⏳ | `tests/test_engine.py` | `llc_graph/engine.py` |
| RF-G2B.4 | `to_critical_path()` em `projections.py` retorna lista de IDs | **Dado** engine, **Quando** `to_critical_path(engine)`, **Então** lista de node_ids em ordem | Should | ⏳ | `tests/test_projections.py` | `llc_graph/projections.py` |

---

## 3. Algoritmo (DAG longest path)

```python
def critical_path(self) -> list[GraphNode]:
    """Caminho crítico = caminho mais longo no DAG.
    Algoritmo: topological sort + relaxação de arestas (O(V+E)).
    Nós SKIPPED têm peso 0 (não contribuem para o comprimento).
    Gates têm peso = tempo médio de espera humana (estimado ou do histórico ACE).
    """
```

---

## 4. Dependências

### Bloqueado por
- PRP-GRAPH-2A

### Desbloqueia
- Dashboard de fábrica (futuro)
- Análise de gargalo integrada ao `code-health.py`

---

## 5. Definition of Done

- [ ] Todos os 4 RF com testes verdes
- [ ] Algoritmo O(V+E) — não O(V²)
- [ ] `critical_path()` puro e determinístico
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
