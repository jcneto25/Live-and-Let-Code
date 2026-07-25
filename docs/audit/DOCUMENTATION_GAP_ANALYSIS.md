# Documentation Gap Analysis — Post F-01..F-14

**Auditor:** Senior Developer (análise cruzada docs × código)
**Data:** 2026-07-10
**Baseline:** Repo state após correções F-01 a F-14 do `WORKFLOW_LOGIC_AUDIT.md`
**Suíte:** 153 passed
**Escopo:** Verificar se a documentação (LLC_GUIDE, pipeline-design, FAQ, README, AGENTS.md, skills) reflete o estado atual do código (REGISTRY com 29 entries, gates.json com 26 gates, CLI com sub-steps 5a/5b/5c/5d/8b/11a/11b wired).

---

## 1. Sumário Executivo

A auditoria identificou **7 defeitos HIGH**, **11 MEDIUM** e **8 LOW** distribuídos em 9 arquivos de documentação. Os HIGH concentram-se em:

1. **Contagens stale** ("14 steps", "15 gates", "21 skills") em 6 arquivos
2. **Sub-steps 5b/5c ausentes** de tabelas/diagramas em pipeline-design (PT+EN) e llc-step-5.md
3. **Numeração deprecated** ("Step 11-Security", "Step 12") em FAQ (PT+EN) e llc-step-11.md
4. **Comando inexistente** (`--check repository-pattern`) em llc-step-8.md
5. **AGENTS.md Index** sem routing para as 6 sub-step skills

---

## 2. Achados por Severidade

### HIGH (7)

| ID | Arquivo | Linha(s) | Problema | Correção |
|----|---------|----------|----------|----------|
| D-01 | `llc-step-5.md` | 11, 111-127 | Declara apenas 5a como sub-step obrigatório; **5b (API Design) e 5c (Clean Code) não são mencionados** | Adicionar 5b/5c como sub-steps obrigatórios + comandos `llc run --step 5b/5c` |
| D-02 | `llc-pipeline-design.md` | 367-408 | Tabela §3.2 omita rows para **5b (gate 6b), 5c (gate 8.5), 10.8, Δ.0, Δ.1** | Adicionar rows faltantes |
| D-03 | `llc-pipeline-design.md` | 549-572 | Tabela §6.1 de gates omita **6a, 6b, 8.5, 9b, 11-PRE** (5 gates que existem em gates.json) | Adicionar 5 rows |
| D-04 | `llc-pipeline-design.en.md` | 301-343, 435-454 | Versão EN (v1.5.0) desatualizada: omita 5b, 5c, 10.8, 11.2, Δ.0/Δ.1 da tabela de steps; omita 9 gates da tabela de gates; catalog de skills sem 5b/5c/11.1-OWASP | Atualizar para v1.7.0 (sync com PT) |
| D-05 | `FAQ.md` + `FAQ.en.md` | 542-548, 484-488 | Skills table usa **"Step 11" e "Step 12"** para Security/Null-Safety; canônico é **10.6 e 10.7** | Renumerar para 10.6/10.7 |
| D-06 | `llc-step-8.md` | 297 | Instrui `fitness-functions.py --check repository-pattern` — **flag não existe** | Corrigir para `--check-deps` (DIP) |
| D-07 | `AGENTS.md` | 118-142 | Documentation Index sem routing entries para **5a/5b/5c/8b/11a/11b** + skills transversais (smart-skip, delta-impact, delta-grill, 10.8, 11.2) | Adicionar entries |

### MEDIUM (11)

| ID | Arquivo | Linha(s) | Problema |
|----|---------|----------|----------|
| D-08 | `LLC_GUIDE.md` | 173-201 | Diagrama overview omita 8.1 (Repository Pattern) e 10.9 (Domain Modeling) |
| D-09 | `LLC_GUIDE.md` | 867-890 | Passo 11b folda arch-fitness em "Gate 11.2"; código tem step separado 11.3 com gate 11-ARCH |
| D-10 | `LLC_GUIDE.md` | 17-27 | Quickstart diz "3 gates (1, 4, 11)"; atual = 21 steps com todos os gates |
| D-11 | `LLC_GUIDE.md` | 170 | Header "14 principais + 5 auxiliares + 2 delta" (=21); atual = 23 pipeline + 2 delta = 25 |
| D-12 | `llc-pipeline-design.md` + `.en.md` | 569, 452 | Gate "10-COVERAGE" em vez de gates.json key "10.8" |
| D-13 | `llc-step-8.md` | 222-231 | Confla Gate 9 com Gate 9b (são gates separados no código) |
| D-14 | `llc-step-11.md` | 12, 28-29 | Pré-requisitos usam "Step 11-Security"/"Step 12-Null-Safety" (deprecated); canônico 10.6/10.7 |
| D-15 | `llc-step-11.md` | 22-34 | Pré-requisitos não incluem Test Coverage Gate (10.8) |
| D-16 | `llc-step-11.md` | 288 | Não referencia step 11.3 (11-ARCH) como requisito de fechamento |
| D-17 | `AGENTS.md` | 446 | "12+ steps, 20 gates" — stale (29 steps, 26 gates) |
| D-18 | `FAQ.md` + `FAQ.en.md` | 11, 22, 348, 753 | "21 skills, 15 human gates" — stale (≈27 skills, 26 gates) |

### LOW (8)

| ID | Arquivo | Linha(s) | Problema |
|----|---------|----------|----------|
| D-19 | `LLC_GUIDE.md` | 182-184, 396-867 | Usa numeração antiga (5a/5b/5c/8b/11a/11b) em vez de canônica (5.1/5.2/5.3/8.1/10.9/11.3) — aliases resolvem |
| D-20 | `LLC_GUIDE.md` | 193, 764, 1094 | "Gate 10-COVERAGE" (display name) em vez de "10.8" (gates.json key) |
| D-21 | `LLC_GUIDE.md` | 419, 461, 499, 608, 803 | "(novo gate)" — gates já estabelecidos |
| D-22 | `llc-pipeline-design.md` | 499-507 | Tags `[NOVO]` em features estabelecidas |
| D-23 | `llc-pipeline-design.en.md` | 744-751 | Version table para em 1.6.0; sem entry 1.7.0 |
| D-24 | `FAQ.en.md` | — | Seção Δ (delta flow) inteira ausente na versão EN |
| D-25 | `llc-step-8.md` | 293 | Hardcode Prisma em exemplo (pipeline é tool-agnostic) |
| D-26 | `LLC_GUIDE.md` | 804-840 | Inconsistência `llc` vs `python .ace/scripts/llc.py` |

---

## 3. Matriz de Contagens Stale

| Arquivo | Linha | Diz | Deveria ser |
|---------|-------|-----|-------------|
| `LLC_GUIDE.md` | 170 | "14 principais + 5 aux + 2 delta" (=21) | 23 pipeline + 2 delta = 25 |
| `llc-pipeline-design.md` | 30 | "14 etapas principais" | 23 pipeline steps |
| `llc-pipeline-design.md` | 51 | "14 steps, 15 human gates" | 23 steps, 26 gates |
| `llc-pipeline-design.en.md` | 32 | "14 main steps" | 23 pipeline steps |
| `llc-pipeline-design.en.md` | 52 | "14 steps, 15 human gates" | 23 steps, 26 gates |
| `FAQ.md` | 11 | "21 skills, 15 human gates" | ≈27 skills, 26 gates |
| `FAQ.md` | 22 | "14 steps, 15 human gates" | 23 steps, 26 gates |
| `FAQ.md` | 753 | "14+5+2=21 total, 23 skills" | 23+2=25 total, ≈27 skills |
| `FAQ.en.md` | 11 | "21 skills, 15 human gates" | ≈27 skills, 26 gates |
| `FAQ.en.md` | 22 | "14 steps, 15 human gates" | 23 steps, 26 gates |
| `README.md` | 11, 20 | "5 auxiliares, 23 skills" | 7 auxiliares (5a/5b/5c/5d/8b/10.5/10.8/10.9), ≈27 skills |
| `AGENTS.md` | 446 | "12+ steps, 20 gates" | 29 steps, 26 gates |

---

## 4. Matriz de Numeração Deprecated

| Arquivo | Linha(s) | Diz | Canônico REGISTRY |
|---------|----------|-----|-------------------|
| `FAQ.md` | 542-548 | "Step 11" (Security) | 10.6 |
| `FAQ.md` | 542-548 | "Step 12" (Null Safety) | 10.7 |
| `FAQ.md` | 759-783 | "11-SEC" / "12-NULL" como step IDs | São gate keys; step IDs são 10.6/10.7 |
| `FAQ.en.md` | 484-488 | "Step 11" / "Step 12" | 10.6 / 10.7 |
| `llc-step-11.md` | 12, 28-29 | "Step 11-Security" / "Step 12-Null-Safety" | 10.6 / 10.7 |
| `LLC_GUIDE.md` | 182-184 | "Step 5a/5b/5c" | 5.1/5.2/5.3 (aliases OK) |
| `LLC_GUIDE.md` | 583 | "Passo 8b" | 8.1 (alias OK) |
| `LLC_GUIDE.md` | 786 | "Passo 11a" | 10.9 (alias OK) |

---

## 5. Plano de Correção Sugerido

### P0 — Quebra de execução (1 item)
1. **D-06:** Corrigir `llc-step-8.md:297` — `--check repository-pattern` → `--check-deps`

### P1 — Sub-steps ausentes (3 items)
2. **D-01:** Adicionar 5b/5c como sub-steps obrigatórios em `llc-step-5.md` (seção §10 + pré-requisitos)
3. **D-02/D-03:** Adicionar rows 5b/5c/10.8/Δ.0/Δ.1 na tabela de steps e gates 6a/6b/8.5/9b/11-PRE na tabela de gates em `llc-pipeline-design.md`
4. **D-07:** Adicionar routing entries para sub-step skills no Documentation Index do `AGENTS.md`

### P2 — Numeração deprecated (2 items)
5. **D-05:** Renumerar "Step 11"/"Step 12" → "10.6"/"10.7" em `FAQ.md` e `FAQ.en.md`
6. **D-14:** Renumerar "Step 11-Security"/"Step 12-Null-Safety" → "10.6"/"10.7" em `llc-step-11.md`

### P3 — Contagens stale (6 items)
7. **D-11:** Atualizar header do `LLC_GUIDE.md` (14+5+2 → 22+2)
8. **D-18:** Atualizar contagens em `FAQ.md` e `FAQ.en.md` (21 skills/15 gates → ≈26/25)
9. Atualizar contagens em `llc-pipeline-design.md` e `.en.md`
10. Atualizar contagens em `README.md`
11. **D-17:** Atualizar `AGENTS.md` (12+ steps/20 gates → 28/25)
12. **D-10:** Atualizar quickstart description no `LLC_GUIDE.md`

### P4 — Sync EN (1 item)
13. **D-04:** Atualizar `llc-pipeline-design.en.md` para v1.7.0 (sync com PT)

### P5 — Polish (8 items LOW)
14. D-09: Separar 11b/11-ARCH de 11.2/11-VERIFY no LLC_GUIDE
15. D-12: "10-COVERAGE" → "10.8" em pipeline-design (PT+EN)
16. D-13: Separar Gate 9 de Gate 9b em llc-step-8.md
17. D-15/D-16: Adicionar 10.8 e 11.3 como pré-requisitos em llc-step-11.md
18. D-21/D-22: Remover "(novo gate)"/`[NOVO]` labels stale
19. D-23: Adicionar entry 1.7.0 na version table do pipeline-design.en
20. D-24: Traduzir seção Δ para FAQ.en.md
21. D-08: Adicionar 8.1 e 10.9 ao diagrama overview do LLC_GUIDE

---

## 6. Verificação Pós-Correção (critérios de aceite)

- `grep -rn "14 steps\|14 etapas\|14 principais\|14 main" LLC_GUIDE.md llc-pipeline-design.md llc-pipeline-design.en.md FAQ.md FAQ.en.md README.md AGENTS.md` → 0 matches
- `grep -rn "15 human gates\|15 gates\|15 human" LLC_GUIDE.md llc-pipeline-design.md llc-pipeline-design.en.md FAQ.md FAQ.en.md` → 0 matches
- `grep -rn "21 skills\|23 skills" FAQ.md FAQ.en.md README.md` → 0 matches
- `grep -rn "Step 11.Security\|Step 12.Null\|Step 11-Security\|Step 12-Null" FAQ.md FAQ.en.md docs/skills/llc-step-11.md` → 0 matches
- `grep -rn "check.repository.pattern\|check repository-pattern" docs/skills/llc-step-8.md` → 0 matches
- `grep -rn "novo gate\|\[NOVO\]" LLC_GUIDE.md llc-pipeline-design.md llc-pipeline-design.en.md` → 0 matches (ou apenas em changelog)
- `llc-step-5.md` menciona 5b e 5c como obrigatórios
- `AGENTS.md` Documentation Index tem entries para 5a/5b/5c/8b/11a/11b
- `llc-pipeline-design.md` tabela §3.2 tem rows para 5b, 5c, 10.8, Δ.0, Δ.1
- `llc-pipeline-design.md` tabela §6.1 tem rows para 6a, 6b, 8.5, 9b, 11-PRE
