# PRP: [WIZARD-2.0] — Swimlanes por Wave no KanbanBoardWidget

> **ID:** PRP-WIZARD-2.0 | **Trilha:** Wizard (pós-roadmap) | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ✅ Done (2026-08-07)
> **Prioridade:** Médio | **ADR de origem:** ADR-0002 §2.5 (Kanban), ADR-0004 §2.7

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Swimlanes por wave foi **explicitamente excluído** do escopo do WIZARD-1.2
(§1.3: "Swimlanes por wave → PRP-WIZARD-2.0"). É o natural "v1.1" do Wizard:
enriquece o Kanban com a dimensão de ondas que o pipeline já conhece
(`EXECUTION_WAVES.md`, parseado por `llc_wave.parsing.parse_execution_waves`).
É o único item pós-roadmap que adiciona features novas à UI.

### 1.2 O que é entregue

- [x] `llc_wave/parsing.py::build_step_wave_map(sessions, waves)` — ponte
      step→onda via sessões ACE (`llc_step_id` + `prp` do `index.json`) ×
      PRPs de cada onda (`WaveInfo.prps`); vence a sessão **mais recente** por
      `timestamp` (determinismo — fix review)
- [x] `KanbanBoardWidget(waves=..., step_wave=...)` — sub-seções por onda em
      cada coluna (swimlanes), colapso/expansão por wave (▸/▾), swimlane
      "Sem onda" para steps sem wave (depois das ondas numeradas — fix review)
- [x] `WizardApp._load_wave_data()` + `toggle_wave()` — wiring duck-free (waves
      são dado de repo, não do reader): degradação graciosa quando
      `EXECUTION_WAVES.md` não existe → board plano (comportamento anterior)
- [x] FTDD com Spec §6 (16 testes: 8 widget + 3 app + 5 mapping/regex)

### 1.3 O que NÃO está no escopo

- ❌ WIP por wave como limite rígido → permanece indicador visual (contagem)
- ❌ Persistência do estado collapse entre toggles K → estado é por widget
- ❌ Relatório cruzando waves × flow metrics → P4
- ❌ `EXECUTION_WAVES.md` real para o repo → gerado pelo Step 4 (planejamento)

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-W2.0.1 | Board com waves renderiza sub-seções por onda em cada coluna | **Dado** `waves` + `step_wave`, **Quando** `render()`, **Então** header `▾ Onda N: Nome (count)` presente e expandido por padrão | Must | ✅ | `test_app.py` | `kanban_board.py` |
| RF-W2.0.2 | Cards agrupados sob a swimlane da sua onda | **Dado** `step_wave={step: onda}`, **Quando** `render()`, **Então** cada card aparece após o header da sua onda | Must | ✅ | `test_app.py` | `kanban_board.py` |
| RF-W2.0.3 | Step sem onda → swimlane "Sem onda" | **Dado** step fora do `step_wave`, **Quando** `render()`, **Então** agrupado sob `Sem onda` (após ondas numeradas) | Must | ✅ | `test_app.py` | `kanban_board.py` |
| RF-W2.0.4 | Wave colapsada esconde cards | **Dado** `toggle_wave(N)`, **Quando** `render()`, **Então** header `▸ Onda N: Nome (count)` e cards ocultos | Must | ✅ | `test_app.py` | `kanban_board.py` |
| RF-W2.0.5 | `toggle_wave` round-trip expande/colapsa | **Dado** toggle 2×, **Quando** estado do widget, **Então** volta ao estado inicial | Must | ✅ | `test_app.py` | `kanban_board.py` |
| RF-W2.0.6 | Sem `EXECUTION_WAVES.md` → board plano (graceful) | **Dado** arquivo ausente, **Quando** `WizardApp` monta, **Então** `_waves == []`, `_step_wave == {}`, render sem "Onda" | Must | ✅ | `test_app.py` | `app.py` |
| RF-W2.0.7 | `build_step_wave_map` liga steps a ondas via sessões | **Dado** sessões (`llc_step_id`+`prp`) e waves (`prps`), **Quando** função, **Então** `{step: onda}` correto; PRP não mapeado fica fora; sessão mais recente vence | Must | ✅ | `test_llc_wave.py` | `llc_wave/parsing.py` |

---

## 3. Design

```python
# llc_wave/parsing.py
def build_step_wave_map(sessions: list[dict], waves: list[WaveInfo]) -> dict[str, int]:
    """step_id → wave number via sessões (llc_step_id + prp) × waves (prps)."""

# kanban_board.py — render com swimlanes (waves ausentes → board plano)
#   ▾ Onda 1: Foundation (2)     ← expandida
#     ⏳ Visao
#     ⏳ Specs
#   ▸ Onda 2: Wizard (1)         ← colapsada (cards ocultos)
#   ▾ Sem onda (1)
```

**Fonte de dados (app):** `parse_execution_waves(project_root/docs/planning/EXECUTION_WAVES.md)`
+ `index.json` sessions. Qualquer arquivo ausente/malformado → `([], {})` —
degradação graciosa, nunca quebra a TUI (convenção do P2).

---

## 4. Dependências

### Bloqueado por
- PRP-WIZARD-1.2 (drag & drop + temas — escopo original excluiu swimlanes)

### Desbloqueia
- P4 (métricas de fluxo em ação — ondas × flow metrics)

---

## 5. Definition of Done

- [x] Todos os 7 RF com testes verdes (FTDD — Spec §6 primeiro)
- [x] Board plano idêntico ao anterior quando `waves` ausente (regressão)
- [x] `build_step_wave_map` coberto (PRP mapeado × não-mapeado × recente-vence)
- [x] `fitness-functions.py --all --strict` verde (41/41)
- [x] Cobertura `kanban_board.py` 98% / `app.py` 88% / `parsing.py` 90%
- [x] Sessão ACE registrada (2026-08-07-004)

---

## 6. Component Spec (FTDD) — KanbanBoardWidget swimlanes

| Estado | Render esperado |
|--------|-----------------|
| `sem_waves` (default) | Board plano — render idêntico ao pré-P3 (nenhum "Onda"/"Sem onda") |
| `expanded` | `  ▾ Onda N: Nome (count)` + cards da onda abaixo |
| `collapsed` | `  ▸ Onda N: Nome (count)` + cards ocultos |
| `ungrouped` | `  ▾ Sem onda (count)` + cards sem step_wave |
| `mixed` | Ondas ordenadas por número; "Sem onda" por último |
| Interação | `toggle_wave(N)` → colapsa/expande; round-trip volta ao inicial |
| Acessibilidade | Marcadores ▸/▾ seguem a convenção da coluna SKIPPED colapsada (D1 ADR-0002) |

**WizardApp wiring:** `_load_wave_data()` uma vez no `__init__`; `_build_kanban`
repassa `waves`/`step_wave` ao widget; `toggle_wave()` delega e sincroniza o
painel.

---

## 7. Nota de execução

**Sessão:** `2026-08-07-004` (step 10.9 Domain Modeling, wave 2) · **16 testes
novos** (8 FTDD em `test_app.py` + 5 unit em `test_llc_wave.py` + 3 fix review)
· **cobertura:** `kanban_board.py` 98%, `app.py` 88%, `llc_wave/parsing.py` 90%
(TOTAL 91%) · **fitness 41/41** · full suite **596 passed**.

**Fix review (3):** (1) `build_step_wave_map` agora vence a sessão **mais
recente** por `timestamp` — last-wins por ordem de arquivo era arbitrário;
(2) teste de ordenação "Sem onda" depois das ondas numeradas na mesma coluna;
(3) regex de PRPs ampliada não captura pontuação final (`PRP-WIZARD-1A.` →
`PRP-WIZARD-1A`).

**Achado real em campo:** `parse_execution_waves()` só extraía PRPs no formato
`PRP-\d{3,}` — os IDs reais do pipeline (PRP-WIZARD-1A, PRP-GRAPH-2B) não eram
capturados, então um `EXECUTION_WAVES.md` real geraria zero PRPs. Ampliado para
`PRP-<alnum>[-.<alnum>]` com regressão. *(Nota futura:* `parse_tasks`/
`_find_prp_headings` ainda usam o padrão antigo — `llc wave list`/`run` com IDs
reais pode não resolver tasks; fora do escopo do P3.)*

**Smoke no repo real:** sem `EXECUTION_WAVES.md` → board plano (graceful, sem
crash). Demo com `.ace` real + waves sintéticas → `step_wave {'10.8': 3,
'10.9': 2}` e swimlanes renderizando com nomes reais (`▾ Sem onda (15)` ·
`▾ Onda 2: Wizard (1)` · `▾ Onda 3: Evals (1)` · `▾ Sem onda (6)`).
