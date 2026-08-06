# Próximos Passos — Pós-Roadmap PRP (100% entregue)

> **Data:** 2026-08-06 · **Status:** 📋 Plano — nenhum item iniciado
> **Contexto:** Roadmap núcleo (Governança + Wizard 5/5 + Evals 5/5 + Graph 5/5) 100% entregue.
> **Referências:** `PRP-MAP.md`, `DELIVERY_SUMMARY.md`, `factory-evolution.md` v0.2.0

---

## 1. Estado atual (verificado no repo)

| Item | Status |
|------|--------|
| 15 PRPs entregues (Wizard 5/5, Evals 5/5, Graph 5/5) + Trilha 0 | ✅ |
| `BaselineManager` (EVALS-F4) com `DEFAULT_WARMUP = {n_min: 5, n_stable: 10}` | ✅ construído, **ocioso** |
| `.ace/evals/baselines/` | **vazio** — nenhuma execução real registrada |
| `GraphPipelineDataSource` (GRAPH-1C) implementa o Protocol | ✅ existe |
| `WizardApp` (`app.py:53`) | ainda usa `PipelineDataReader` |
| `flow_metrics.py` (WIZARD-1.2) grava YAML | ✅ grava, **ninguém consome** |
| Trilhas 4 (Wave Coordinator) e 5 (Herdr) | 🔒 condicionais — gates não atingidos |

---

## 2. Prioridades

### 🥇 P1 — Warm-up de baselines (EVALS-F4 em produção) — ✅ Done (2026-08-06)

**Por quê:** único gargalo funcional real. Toda a cadeia Evals (Pareto, regressão, alertas) está
construída mas ociosa porque nenhum step atingiu `N_MIN=5`. Sem dados, o dashboard permanece
vazio (`llc eval report` → `steps_analyzed: 0`).

**O que foi feito (sessão 2026-08-06-024):**
- ✅ `llc_evals/ingest.py` — `parse_eval_metrics()` (extrai blocos `<eval_metrics>`), `quality_from_gate()`
  (quality determinístico via `<gate_result>` real, ignorando placeholders comentados) e
  `ingest_sessions()` (alimenta `record_run()` com idempotência por session_id + migração de
  estado legado)
- ✅ `llc evals ingest` (CLI, flags `--dry-run` / `--project-root`)
- ✅ **Resultado real no repo:** 13 runs ingeridos → 2 baselines em warmup (step 10.9 eff 31.25,
  step 10.8 eff 31.57) — **dashboard Pareto populado de verdade** (`Steps com baseline: 2`)
- ✅ 22 testes (17 RF + 5 regressão review), cobertura 90%, fitness 41/41, suite 542 passed

**Restante do P1:** cada step precisa de **5 runs** (collecting) → **10 runs** (stable) para sair do
warm-up — basta continuar executando `llc run` e re-rodar `llc evals ingest`.

**Estimativa restante:** 0 · **Risco:** baixo

---

### 🥈 P2 — Integração Graph → Wizard definitiva

**Por quê:** GRAPH-1C entregou o adapter com paridade §7.6 100%, mas o Wizard ainda usa
`PipelineDataReader`. É o "último metro" do investimento em Graph — trocar a fonte dá acesso a
`ready_nodes()`, `critical_path()`, `parallel_frontier()` dentro da TUI.

**O que fazer:**
1. Trocar `app.py:53` (`PipelineDataReader`) pelo `GraphPipelineDataSource` + `GraphEngine` como fonte
2. Benefícios colaterais: coluna BACKLOG pode usar `ready_nodes()` (RF-W1A.7); exibir
   `critical_path()` no board
3. **Cuidado (DIP):** manter o Protocol `PipelineDataSource` como contrato — a troca é transparente
   para `KanbanBoardBuilder` e `flow_metrics.py`
4. Manter `PipelineDataReader` como fallback (feature flag `--source graph|index`)

**Estimativa:** 1 semana · **Risco:** médio (regressão de paridade — mitigada pelos testes de
paridade §7.6 do GRAPH-1C)

---

### 🥉 P3 — PRP-WIZARD-2.0 (swimlanes por wave)

**Por quê:** foi explicitamente excluído do escopo do WIZARD-1.2 (§1.3: "Swimlanes por wave →
PRP-WIZARD-2.0"). É o natural "v1.1" do Wizard — enriquece o Kanban com a dimensão de ondas que o
pipeline já conhece (`EXECUTION_WAVES.md`).

**O que fazer (mini-PRP ~1 sem):**
- `KanbanBoardWidget` ganha agrupamento por wave (RF análogo ao FTDD do 1.1)
- Fonte de dados: `parse_execution_waves()` (já existe em `llc_wave`)
- Colapsar/expandir wave, WIP por wave
- **Nota:** único item que adiciona features novas à UI — os outros 3 são integrações/ativação

**Estimativa:** 1 semana · **Risco:** baixo

---

### 🏅 P4 — Métricas de fluxo em ação (consumir `flow-metrics-*.yaml`)

**Por quê:** WIZARD-1.2 grava as métricas, GRAPH-2B calcula o caminho crítico — mas ninguém cruza
os dois. O valor real está em "quais steps bloqueiam o caminho crítico E estão stale/em rework".

**O que fazer (extensão leve de GRAPH-2B ou PRP novo pequeno):**
- `critical_path()` + `flow_metrics.yaml` → tabela "gargalos reais": steps no caminho crítico com
  `stale_rate` alto ou `rework_count > 0`
- Alimenta o `llc eval report` ou um novo `llc flow report`
- Critério de saída: relatório identifica ≥1 gargalo acionável por execução

**Estimativa:** 0.5–1 semana · **Risco:** baixo

---

## 3. Fora de escopo agora (condicionais — gates não atingidos)

| Item | Gate de entrada | Status |
|------|----------------|--------|
| **PRP-WAVE-COORD** (Trilha 4) | ≥3 sessões com retrabalho por `DEPENDENCY_MATRIX` estático | 🔒 não atingido |
| **PRP-HERDR-SKILL** (Trilha 5) | ≥4 semanas de uso + dor multi-agente registrada | 🔒 não atingido |
| **Fase 2/3 da factory-evolution** | Evidência de dor (paralelismo já existe via worktrees — o gap é visibilidade) | 🔒 condicional |

---

## 4. Sequência recomendada

```
Semana 1-2:  P1 Warm-up baselines (desbloqueia toda a cadeia Evals)
Semana 3:    P2 Graph→Wizard (consolida investimento Graph)
Semana 4:    P3 WIZARD-2.0 swimlanes (feature UI)
Em paralelo: P4 pode entrar quando P1 gerar dados reais
```

**Rationale:** P1 primeiro porque transforma infraestrutura ociosa em valor observável (e o
próprio P4 depende dos dados de P1). P2 antes de P3 porque é integração barata com teste de
paridade já existente, enquanto P3 é feature nova.

---

## 5. DoD deste plano

- [x] P1 (2026-08-06): `llc evals ingest` entregue — elo sessão→`record_run()` fechado; 13 runs ingeridos, 2 steps em warmup; ~[ ] 2 steps em fase `stable` (aguarda mais runs de `llc run`)
- [ ] P2: Wizard com `GraphPipelineDataSource` por padrão + fallback `--source index`
- [ ] P3: swimlanes por wave renderizando corretamente no `KanbanBoardWidget`
- [ ] P4: relatório de gargalos reais (caminho crítico × flow metrics) com ≥1 achado acionável
- [ ] Todos os itens: TDD/FTDD, cobertura ≥85%, `fitness-functions.py --all --strict` verde,
      sessão ACE registrada
