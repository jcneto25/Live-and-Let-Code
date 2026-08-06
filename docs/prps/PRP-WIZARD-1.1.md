# PRP: [WIZARD-1.1] — Kanban UI Board Completo (Toggle K + SLA + WIP)

> **ID:** PRP-WIZARD-1.1 | **Trilha:** Wizard | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 2 semanas | **Status:** ⏳ Pending
> **Prioridade:** Alto | **ADR de origem:** ADR-0002 §2.5, §2.7

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O PRP-WIZARD-1A entrega o modelo de dados Kanban (`KanbanCard`, `KanbanBoardBuilder`) mas sem UI. Este PRP entrega a segunda lente do Wizard: o painel Kanban interativo acessível via toggle `K`, com SLA visual para cards em `AWAITING_HUMAN` e WIP limits. É o artefato que transforma o Wizard de "pipeline view" em "flow visibility tool".

### 1.2 O que é entregue

- [ ] `kanban_board.py` widget — board com 6 colunas, cards, WIP indicators
- [ ] Toggle `K` — alterna entre modo Pipeline e modo Kanban (tela exclusiva)
- [ ] SLA visual — card stale após N minutos recebe borda vermelha (`card-stale`)
- [ ] Header Kanban — WIP total, Block Time, Stale count
- [ ] `QualityScore` e `EfficiencyScore` do PRP-EVALS-F1/F2 exibidos no card (se disponíveis)
- [ ] Coluna `SKIPPED` colapsada por padrão, expandível

### 1.3 O que NÃO está no escopo

- ❌ Drag & drop no backlog → PRP-WIZARD-1.2
- ❌ `--export-flow-metrics` → PRP-WIZARD-1.2
- ❌ Projeção via GraphEngine → PRP-GRAPH-1C (refatora este componente depois)

---

## 2. Requisitos Funcionais (FTDD)

| ID | Estado | Trigger | UI esperada | Arquivo de teste |
|----|--------|---------|-------------|------------------|
| RF-W1.1.1 | board inicial | App abre em modo Kanban | 6 colunas, steps distribuídos, SKIPPED colapsada | `test_app.py` |
| RF-W1.1.2 | card RUNNING | Step com `in_progress` | Card em RUNNING com nome e ícone 🔄 | `test_app.py` |
| RF-W1.1.3 | card AWAITING_HUMAN | Gate pendente | Card em AWAITING_HUMAN com ícone ⚠️ | `test_app.py` |
| RF-W1.1.4 | card stale | Card em AWAITING_HUMAN > SLA | Borda vermelha, `card-stale` CSS class | `test_app.py` |
| RF-W1.1.5 | DONE após aprovação | Gate aprovado | Card move para DONE ✅ | `test_app.py` |
| RF-W1.1.6 | REWORK após rejeição | Gate rejeitado | Card move para REWORK ❌ | `test_app.py` |
| RF-W1.1.7 | SKIPPED colapsado | Smart skip | Coluna SKIPPED visível como `▸` | `test_app.py` |
| RF-W1.1.8 | WIP limit visual | REWORK tem 3 cards | Indicador `2/2 WIP` vermelho | `test_app.py` |
| RF-W1.1.9 | toggle K preserva seleção | Volta do Kanban | Step selecionado antes do toggle mantido | `test_app.py` |
| RF-W1.1.10 | scores no card | PRP-EVALS-F1 dados disponíveis | `Q:86 $0.08` visível no card se dados existirem | `test_app.py` |

---

## 2.1 Fonte de dados dos cards N2 (ADR-0007 / GOV-003 R5)

Cards de PRPs paralelos (múltiplos `RUNNING`) são derivados do **campo `prp` em
`.ace/index.json`** — gravado por `update_index()` quando a sessão é iniciada com
`--prp` (já implementado; **zero mudança de código**). Regras:

- **Agrupamento:** sessões com o mesmo valor de `prp` formam o card N2 daquele PRP.
- **Coluna:** derivada do `status` da sessão + `<gate_result>` (mesma tabela de
  derivação do PRP-WIZARD-1A §7.6, aplicada por sessão-PRP).
- **Corroboração opcional:** `git worktree list` (convenção `prp-{id}/wave-{n}`)
  confirma cards `RUNNING` — fallback de leitura, nunca fonte primária.
- **Degradação graciosa:** sem sessões com `prp`, o board exibe apenas cards N1.

## 3. Dependências

### Bloqueado por
- PRP-WIZARD-1A (modelo Kanban + PipelineDataSource Protocol)
- PRP-EVALS-F1 (instrumentação de tokens — para exibir scores no card)

### Desbloqueia
- PRP-WIZARD-1.2 (drag & drop)
- PRP-GRAPH-1C (refatora KanbanBoardBuilder para usar GraphEngine)

---

## 4. Definition of Done

- [ ] Todos os 10 estados FTDD com testes verdes
- [ ] Toggle `K` funcional — Pipeline ↔ Kanban sem crash
- [ ] SLA configurable via `gates.json → wizard.hitl_sla_minutes`
- [ ] `SKIPPED` colapsada por padrão (D1 do ADR-0002)
- [ ] Múltiplos cards `RUNNING` renderizados corretamente (N2 — derivados do campo `prp` no `index.json`, §2.1 / ADR-0007)
- [ ] Scores de eval exibidos apenas se `PRP-EVALS-F1` dados disponíveis (graceful ausência)
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
