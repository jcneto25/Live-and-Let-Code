# ADR-0007: Campo `prp` em `.ace/index.json` como fonte canônica do nível N2

```yaml
---
adr: "0007"
title: "Campo prp em .ace/index.json como fonte canônica do nível N2 (Kanban multi-PRP)"
status: accepted
date: 2026-08-05
deciders:
  - jcneto25
supersedes: null
related:
  - ADR-0002   # Kanban N2 — múltiplos cards RUNNING (PRPs em worktrees)
  - ADR-0004   # Granularidade N1/N2 do grafo
  - GOV-003    # Gap G2 / ação R5
tags: [ace, schema, index-json, kanban, n2, worktree]
---
```

## 1. Contexto

O Kanban do Wizard (ADR-0002 §2.5) prevê múltiplos cards `RUNNING` no nível **N2**
(PRPs paralelos em worktrees). A auditoria GOV-003 (gap G2) verificou que nenhum PRP
especificava **de onde** os cards N2 são derivados: as sessões em `.ace/index.json`
exibiam apenas `session_id, file, status, llc_step, llc_step_id, tags, timestamp`.

Verificação do código (2026-08-05, sessão 2026-08-05-007): **a capacidade já existe** —
`initialize_session/session.py::update_index()` grava `record["prp"]` quando `--prp`
é fornecido, e `llc_harness/session.py::session_start()` propaga `--prp` ao subprocesso.
O gap era exclusivamente de **especificação** (0/26 sessões atuais usam o campo —
este repositório ainda não executou PRPs; uso real começa com o PRP-MAP).

## 2. Decisão

1. **Fonte canônica N2 = campo `prp` em `.ace/index.json`** — já implementado em
   `update_index()`; **nenhuma mudança de código necessária**.
2. **Corroboração opcional via `git worktree list`** — worktrees ativos seguem a
   convenção `prp-{id}/wave-{n}` e podem confirmar cards `RUNNING`. É fallback de
   leitura, **nunca** fonte primária (fonte primária é sempre o ACE).
3. Sessões **sem** `prp` pertencem ao nível N1 (pipeline macro). Cards N2 agrupam
   sessões por valor de `prp`.
4. Ausência de sessões com `prp` → o board exibe apenas N1 (degradação graciosa,
   não erro).

## 3. Schema do registro de sessão (documentado)

| Campo | Tipo | Presença | Significado |
|---|---|---|---|
| `session_id` | str | sempre | `YYYY-MM-DD-NNN` |
| `file` | str | sempre | arquivo da sessão em `.ace/sessions/` |
| `status` | str | sempre | `in_progress` \| `completed` |
| `llc_step` | float | sempre | projeção numérica do step |
| `llc_step_id` | str | sempre | id canônico do step |
| `tags` | list[str] | sempre | tags da sessão |
| `timestamp` | str (ISO) | sempre | criação |
| `completed_at` | str (ISO) | após finalize | encerramento |
| **`prp`** | **str** | **opcional (`--prp`)** | **PRP dono da sessão — fonte N2** |

## 4. Consequências

### Positivas
- Zero mudança de código — a fonte já existia e é sancionada (escrita por
  `initialize_session.py`, um dos mutadores permitidos).
- N2 do Kanban especificado sobre fonte derivável e auditável.
- Degradação graciosa: projetos sem PRPs paralelos não são afetados.

### Negativas / Custos
- O campo depende de callers passarem `--prp`. O fluxo de execução de PRPs já o faz
  (`llc_wave` / `llc run --step 11 --prp PRP-NNN`); sessões iniciadas "à mão" sem
  `--prp` simplesmente não geram card N2 (comportamento correto — não são PRPs).

## 5. Registro de Aprovação

| Decisor | Papel | Data |
|---|---|---|
| jcneto25 | Owner / Arquiteto | 2026-08-05 |

**Status:** `accepted`
**Origem:** GOV-003 (gap G2 → ação R5) · Consumidor: PRP-WIZARD-1.1 (cards N2)
