---
name: llc-step-5c-clean-code
description: LLC Pipeline Step 5c — Consolidated Clean Code Enforcement (Functions, Classes, Naming, Errors, Smells, ReadModels). Based on Clean Code (R. Martin), Clean Architecture, Software Design & Architecture (Stemmler). 21+ automated fitness functions.
version: 1.0.0
tags: [clean-code, functions, classes, naming, errors, smells, readmodels, solid, dip, srp, llc-pipeline, code-quality]
---

# LLC Skill: Step 5c — Clean Code Enforcement (Mandatory)

**Pipeline:** Live and Let Code (LLC)  
**Phase:** Architecture (sub-step of Step 5 — after Step 5b API Design Enforcement)  
**Depends on:** Step 5a (Architecture Patterns), Step 5b (API Design Enforcement)  
**Executes before:** Step 6 (Tasks) and Step 8 (Setup + Mock)  
**Maintainer:** LLC Team

---

## 🛠️ How to Use This Skill

1. Place this file in `.claude/skills/` or the project's `docs/skills/` folder.
2. Invoke in chat using: `@llc-step-5c-clean-code` or "Execute the skill llc-step-5c-clean-code".
3. Via Thin Harness (recommended): `python .ace/scripts/llc.py run --step 5c --task "Enforce Clean Code"`.

---

## 📋 PREREQUISITES

- [ ] `docs/architecture/ARCHITECTURE.md` — architectural overview (Step 5)
- [ ] `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` — architectural patterns (Step 5a)
- [ ] `docs/api/openapi.yaml` — OpenAPI spec (Step 5b)
- [ ] `docs/templates/CONTROLLER_TEMPLATE.ts` — base template for controllers (Step 5b)
- [ ] `.ace/arch-config.yaml` — fitness functions configuration (modules core, thresholds)
- [ ] Component skills (available in `docs/skills/`):
    - `llc-step-clean-code-functions.md`
    - `llc-step-clean-code-classes.md`
    - `llc-step-clean-code-naming.md`
    - `llc-step-clean-code-errors.md`
    - `llc-step-clean-code-smells.md`
    - `llc-step-clean-code-readmodels.md`

---

## 🔄 DELTA MODE — Smart Skip Check

**If `docs/planning/DELTA_REPORT.md` exists and is approved (Gate Δ.0):**

1. Read section §5.3 (Steps to Skip) of DELTA_REPORT.md.
2. If **Step 5c** is listed as "skip":
   - Generate skip note in `docs/delta/skip-notes/step-5c.md`:
     ```markdown
     # Skip Note: Step 5c — Clean Code Enforcement
     **Decision:** Step skipped — Clean Code patterns unchanged since last execution.
     **Evidence:** Fitness functions `--check-clean-code` pass without new violations.
     **Validator:** [Name] | **Date:** [YYYY-MM-DD]
     ```
   - Record in session `index.json`: `llc_step_id: "5.3"`, `status: "skipped"`, `reason: "delta-smart-skip"`.
   - **Do not execute** the remaining checks nor wait for Gate 8.5.
   - Advance to Step 6.

---

## 🎯 OBJECTIVE

Consolidate and execute **all Clean Code verifications** through **21+ automated fitness functions**, covering 6 dimensions:

| Dimension | Component Skill | Fitness Functions | Reference |
|-----------|-----------------|-------------------|-----------|
| **Functions** | `llc-step-clean-code-functions` | `function-max-lines`, `function-max-params`, `no-generic-names`, `no-side-effects` | Clean Code Ch.3 |
| **Classes** | `llc-step-clean-code-classes` | `class-max-lines`, `class-max-deps`, `dip-violation`, `anemic-domain`, `use-case-per-operation` | Clean Code Ch.10, Clean Arch |
| **Naming** | `llc-step-clean-code-naming` | `naming-consistency`, `no-generic-names` | Clean Code Ch.2 |
| **Errors** | `llc-step-clean-code-errors` | `no-empty-exceptions`, `no-empty-catch`, `result-pattern` | Clean Code Ch.7 |
| **Smells** | `llc-step-clean-code-smells` | `no-magic-numbers`, `no-dead-code`, `no-noise-comments`, `prefer-const` | Clean Code Ch.17 |
| **ReadModels** | `llc-step-clean-code-readmodels` | `readmodel-exists`, `repo-returns-readmodel`, `no-any-in-public`, `no-as-any` | Clean Architecture |

---

## 🔧 AUTOMATED FITNESS FUNCTIONS (21 Checks)

### Functions (4 checks)
| Check | Description | Threshold | Severity (Core/Non-core) |
|-------|-------------|-----------|--------------------------|
| `function-max-lines` | Functions ≤ 20 effective lines | 20 | block / warn |
| `function-max-params` | Functions ≤ 3 positional params | 3 | block / warn |
| `no-generic-names` | Forbids `data`, `dto`, `result`, `info`, `obj`, `item`, `entity` | list | block / warn |
| `no-side-effects` | Detects `this.*` assignments in pure functions | heuristic | warn |

### Classes (6 checks)
| Check | Description | Threshold | Severity |
|-------|-------------|-----------|----------|
| `class-max-lines` | Classes ≤ 100 effective lines | 100 | block / warn |
| `class-max-deps` | Constructor ≤ 5 injected deps | 5 | block / warn |
| `class-srp-cohesion` | Cohesion: methods use class fields | ≥ 80% | warn |
| `dip-violation` | Zero `PrismaService`, `@prisma/client` in services/use-cases | regex | block / warn |
| `anemic-domain` | Entities have business methods (not just props) | > 0 methods | warn |
| `use-case-per-operation` | Core modules have Use Cases per operation | - | block |

### Naming (1 consolidated check)
| Check | Description | Severity |
|-------|-------------|----------|
| `naming-consistency` | PT/EN mixing, camelCase vs snake_case in query params | block / warn |

### Errors (3 checks)
| Check | Description | Severity |
|-------|-------------|----------|
| `no-empty-exceptions` | Zero `throw new NotFoundException('')` or `BadRequestException('')` | block |
| `no-empty-catch` | Zero empty `catch { }` or `catch (e) { }` | block |
| `result-pattern` | Business rules return `Result<T, E>` not throw | warn |

### Smells (4 checks)
| Check | Description | Threshold | Severity |
|-------|-------------|-----------|----------|
| `no-magic-numbers` | Named constants for timeouts, limits, etc. | regex | warn |
| `no-dead-code` | Zero stubs (`throw new UnimplementedException`), unreachable code | heuristic | warn |
| `no-noise-comments` | Zero section comments (`// ── Foo ────`) | regex | warn |
| `prefer-const` | `let` only where real reassignment occurs | heuristic | warn |

### ReadModels / Type Safety (4 checks)
| Check | Description | Severity |
|-------|-------------|----------|
| `readmodel-exists` | 100% repo interfaces have `XxxReadModel` | block |
| `repo-returns-readmodel` | Repo methods return typed ReadModel (not `any`) | block |
| `no-any-in-public` | Zero `any` in public signatures (params, returns, generics) | block |
| `no-as-any` | Zero `as any` casts (except 2 allowed in global filter) | block |

---

## 📊 EXECUTION COMMAND

```bash
# Run all 21 Clean Code checks
python .ace/scripts/fitness-functions.py --check-clean-code --verbose

# By dimension
python .ace/scripts/fitness-functions.py --check-functions --check-classes --check-naming --check-errors --check-smells --check-readmodels

# Strict mode (CI/CD)
python .ace/scripts/fitness-functions.py --check-clean-code --strict
```

**Options:**
- `--strict` — fail on any block violation
- `--verbose` — per-file/module details
- `--module <name>` — filter specific module
- `--config <path>` — custom `.ace/arch-config.yaml`

---

## 📝 HUMAN VALIDATION CHECKLIST (Gate 8.5)

- [ ] Fitness functions `--check-clean-code --strict` pass with **zero blocks**?
- [ ] Zero `PrismaService` injection in services/use-cases?
- [ ] All repositories return typed `XxxReadModel` (zero `any`)?
- [ ] Domain entities have business methods (not anemic)?
- [ ] Use Cases separated per operation (no monolithic CRUD service)?
- [ ] Semantic names in all new code (`auditoriaEncontrada` vs `data`)?
- [ ] Zero empty exceptions (`NotFoundException('')`)?
- [ ] Zero `as any` in public signatures?
- [ ] ADRs 012-017 created for Clean Code decisions?

---

## 📤 ARTIFACTS GENERATED/UPDATED

| Artifact | Description |
|----------|-------------|
| `.ace/arch-config.yaml` | Clean Code rules activated/thresholds per module |
| `docs/architecture/adr/ADR-012` to `ADR-017` | ADRs for ReadModels, Use Cases, Thresholds |
| `docs/code-quality/CLEAN_CODE_REPORT.md` | Consolidated violations report by dimension |
| `docs/delta/skip-notes/step-5c.md` | Skip note if delta mode applicable |

---

## 👤 GATE 8.5 — HUMAN VALIDATION

**You validate:**
- Fitness functions `--check-clean-code` pass without **blocks**?
- `warn` violations in non-core modules have documented migration plan?
- ADRs 012-017 created and justified?
- Core modules (auditorias, achados, planos, relatórios, notificações) have **zero** block violations?
- `Result<T, E>` pattern adopted in new use cases?
- Repository interfaces return typed `XxxReadModel` (zero `any`)?
- Legacy code marked `// LEGACY` has migration plan in `docs/tech-debt/MIGRATION_PLAN.md`?

**Only proceed when approved.**

---

## 🌱 GREENFIELD vs BROWNFIELD

| Context | Application |
|---------|-------------|
| **Greenfield** | Apply to **all new code** from first commit. Folder structure already provides `domain/`, `application/`, `infrastructure/` per module. |
| **Brownfield** | Apply to **new modules** and **modified files** (PRP-A). Legacy marked `// LEGACY` — create interfaces progressively. Use `XxxService` as temporary facade if needed. |

---

## 📤 EXPECTED OUTPUT

When executing this skill, the agent must:

1. **Verify** existing (new/modified) code against 21 rules via `fitness-functions.py --check-clean-code`
2. **Report** violations with exact location (file:line), rule, and fix suggestion
3. **Group** by dimension (Functions, Classes, Naming, Errors, Smells, ReadModels)
4. **Prioritize**: block in core → block in non-core → warn
5. **Suggest** standard refactoring: extract use case, extract interface, introduce ReadModel, etc.
6. **Update** `.ace/arch-config.yaml` with core/non-core modules and thresholds
7. **Generate** ADRs 012-017 for architectural decisions
8. **Run** fitness functions `--check-clean-code --strict`
9. **Wait** for human validation (Gate 8.5) before proceeding

**DO NOT proceed to Step 6 (Tasks) without Gate 8.5 approval.**

---

## 🔗 INTEGRATION WITH OTHER STEPS

| Step | Integration |
|------|-------------|
| **5a Architecture Patterns** | Defines `domain/application/infrastructure` structure where Clean Code applies |
| **5b API Design** | Controllers follow naming, REST semantics — Clean Code validates implementation |
| **8b Repository Pattern** | Repositories already return ReadModels — Clean Code reinforces typing |
| **11a Domain Modeling** | Rich entities, Use Cases SRP — Clean Code validates SRP, DIP, anemic |
| **11b Arch Fitness** | Fitness functions include Clean Code checks — final pre-merge validation |

---

## 📚 REFERENCES

- **Clean Code** (Robert C. Martin) — Ch. 2 (Names), 3 (Functions), 7 (Errors), 10 (Classes), 17 (Smells)
- **Clean Architecture** (Robert C. Martin) — Dependency Rule, DIP
- **Software Design & Architecture** (Khalil Stemmler) — SRP, Cohesion, Domain Entities, Use Cases
- **Software Architect's Handbook** (Joseph Ingeno) — Fitness Functions, ADRs
- **Domain-Driven Design Distilled** (Vaughn Vernon) — Entities, Value Objects, Aggregates