# Execution Guide — Live and Let Code (LLC)

**Version:** 1.5.0
**Audience:** Developers, Product Owners, Tech Leads
**Prerequisite:** Read [`llc-pipeline-design.en.md`](llc-pipeline-design.en.md) (methodology overview)

---

## Before You Start

### What You Need

- A terminal AI client (Claude Code, opencode, Codex, Cursor CLI, etc.)
- Git installed and configured
- A software project to be developed
- Business domain documents (manuals, meeting minutes, regulations, transcripts, operational guides)

### Initial Setup

Clone the LLC repository or copy the directory structure to your project:

```bash
git clone https://github.com/jcneto25/Live-and-Let-Code.git your-project
cd your-project
```

The `docs/` directory contains all necessary templates and skills.

### Configuring Skills for Your AI Client

LLC skills are Markdown files with YAML frontmatter. Each terminal AI client has its own skills directory. Copy (or symlink) the files from `docs/skills/` to the appropriate directory:

| AI Client | Skills Directory | Setup Command |
|-----------|-----------------|---------------|
| **Claude Code** | `.claude/skills/` | `cp docs/skills/llc-*.md .claude/skills/` |
| **opencode** | `.opencode/skills/<name>/SKILL.md` | `mkdir -p .opencode/skills/llc-step-0-1 && cp docs/skills/llc-step-0-1.md .opencode/skills/llc-step-0-1/SKILL.md` (repeat for each skill) |
| **Codex** | `.codex/skills/` | `cp docs/skills/llc-*.md .codex/skills/` |
| **Cursor** | `.cursor/skills/` | `cp docs/skills/llc-*.md .cursor/skills/` |
| **GitHub Copilot CLI** | `.github/copilot/skills/` | `cp docs/skills/llc-*.md .github/copilot/skills/` |
| **Other** | `.skills/` (default) | `cp docs/skills/llc-*.md .skills/` |

**Alternative — no copy needed:** Most clients accept the direct path. Example:

```
Execute the skill docs/skills/llc-step-0-1.md
```

**Alias invocation:** If the client supports skill aliases (e.g., `@llc-step-0-1`), the name in the YAML frontmatter is used automatically.

**Quick script for opencode (bash):**
```bash
for f in docs/skills/llc-*.md; do
  name=$(basename "$f" .md)
  mkdir -p ".opencode/skills/$name"
  cp "$f" ".opencode/skills/$name/SKILL.md"
done
```

---

### LLM Operation Mode

The LLC pipeline has two distinct moments that benefit from different operation modes:

| Stages | Recommended Mode | Reason |
|--------|-----------------|--------|
| **Steps 0–10** (spec and planning) | **Thinking / Reasoning** | Documents require deep analysis, multi-step reasoning, and cross-artifact consistency. Thinking mode reduces hallucinations and produces more coherent specs. |
| **Post-validation fixes** | **Thinking / Reasoning** | Corrections after a rejected gate require full context understanding and impact analysis across interdependent artifacts. |
| **Step 11 — Execution** (dev and tests) | **Regular / Default** | PRP and task implementation benefits from faster responses. Generated code is validated by automated tests, reducing hallucination risk. |
| **Subflow F1-F4** (prototyping) | **Thinking / Reasoning** | Discovery, tokens, wireframes, and hi-fi phases require design judgment and Design System consistency. |
| **Subflow F5-F6** (code and validation) | **Regular / Default** | Component generation and test execution follow already-approved specs. |

**In practice:** Enable thinking/extended reasoning mode for Steps 0–10 and any post-validation adjustments. Use normal mode for code execution and testing.

---


### Using the Thin Harness (recommended)

LLC includes a CLI orchestrator that automates the lifecycle of each step:

```bash
# Install single dependency
pip install click

# Execute a complete step
python .ace/scripts/llc.py run --step 5 --task "System Architecture"

# Full pipeline (stops at each gate)
python .ace/scripts/llc.py pipeline --from 0

# Check progress
python .ace/scripts/llc.py status
```

The harness automatically manages: ACE session, context_seed, skill loading,
agent invocation, validation gate, and session finalization. If a CLI client
is available (claude, opencode, codex, cursor), invocation is automatic. Otherwise,
the prompt is displayed for manual copy/paste.

> **⚡ Early Commitment + Deterministic Replay (v1.5.0):** The harness automatically
> classifies each task into 4 types and reuses approved execution paths for repeated
> tasks — reducing token cost by up to 99%. For details, see the [FAQ](FAQ.en.md#-early-commitment--deterministic-replay).

### Guaranteeing sessions are recorded in `.ace` (tool-agnostic)

The `llc run --step N` flow is already **AI-client-agnostic**: the harness runs
`initialize_session.py → loads the skill → invokes the CLI agent (claude/opencode/codex/cursor, or prints the prompt) → finalize_session.py`.
The problem isn't running the flow — it's **enforcing** that the agent goes through it instead of
coding "directly". Coding outside the cycle leaves `.ace/index.json` with `sessions: []`: the work
happened, but there's no history proving incremental delivery.

LLC applies **defense in depth** — layers with distinct roles:

| Layer | Mechanism | Strength | Tool-agnostic? |
|-------|-----------|----------|:---:|
| **Contract** | `AGENTS.md`/`CLAUDE.md` state "all work becomes a session" | Advisory (states the rule) | ✅ |
| **Procedure** | the step's skill (auto-loaded by `llc run`) | Advisory (operationalizes) | ✅ |
| **Guarantee** | `pre-commit.sh` + `validate-tags.py --coverage`: a commit with code but no session is **rejected** by git | **Deterministic** | ✅ |
| **Per-client UX** | a client hook (e.g. Claude Code `PreToolUse`) blocks edits with no open session | Deterministic | ❌ (per-client) |

The layer that **actually guarantees** recording is the **git pre-commit hook** — git runs it
regardless of which agent made the commit. Install it in the target project:

```bash
cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
# or, with the pre-commit framework: pre-commit install
```

For enforcement *during* the session (before commit), use your client's hook.
Ready-made snippets (Claude Code `PreToolUse` + `SessionStart`) in
[`docs/templates/hooks/claude-code-session-hooks.en.md`](docs/templates/hooks/claude-code-session-hooks.en.md).

> The pre-commit hook can be bypassed with `git commit --no-verify` (at the operator's own risk).
> No mechanism is 100% — but, layered, they shift the failure mode from "the agent forgot" to
> "someone had to actively bypass it". Details in
> [`llc-pipeline-design.en.md` §8.7](llc-pipeline-design.en.md#87-guaranteed-session-registration-enforcement).

## Step by Step

### 📋 Pipeline Overview

```
Step 0   → Document Ingestion
Step 0.1 → Markdown Conversion (Docling)
Step 0.5 → Strategic Vision + Modules        👤 Gate 1
Step 1   → 7 Specifications                   👤 Gate 2
Step 2   → PRDs (Executive + Technical)       👤 Gate 3
Step 3   → PRPs                                👤 Gate 4
Step 4   → Planning                            👤 Gate 5
Step 5   → Architecture                        👤 Gate 6
Step 5a  → Architecture Patterns               👤 Gate 6a
Step 5b  → API Design Enforcement              👤 Gate 6b
Step 5c  → Clean Code Enforcement              👤 Gate 8.5
Step 5d  → Secure-by-Design                   👤 Gate 5d
Step 6   → Tasks                               👤 Gate 7
Step 7   → Design System                       👤 Gate 8
Step 8   → Setup + Mock Data                   👤 Gate 9
Step 9   → Testing Docs                        👤 Gate 10
Step 10  → Project Docs + Steering Files       👤 Gate 11
Step 10.5 → User Guide                         👤 Gate 11.5
Step 10.6 → Audit (SCA+SAST+Secrets)    👤 Gate 11-SEC
Step 10.7 → Data Contracts           👤 Gate 12-NULL
Step 10.8 → Test Coverage                👤 Gate 10-COVERAGE
Step 11  → Execution (PRPs)                    QA Checkpoints
Step 11.1 → Hardening (post-code)          👤 Gate 11-OWASP
```

### ⚠️ Attention: Do you have existing documentation?

**If YES** (manuals, meeting minutes, regulations already exist) → go to Step 0.

**If NO** (brand new system, no documentation) → run the greenfield flow:

```
Execute the skill docs/skills/llc-step-0-greenfield.md
```

The AI will conduct a structured interview across 4 dimensions (max 15 questions) and generate the documentation baseline. Then proceed normally to Step 0.5.

---

### Step 0: Load Domain Documents

**You do:** Place all business documents in the `docs/business/ingestion/` folder.

Accepted formats: `.pdf`, `.docx`, `.pptx`, `.html`, `.txt`, images with text (PNG/JPG/TIFF).

Examples of what to include:
- Stakeholder meeting transcripts
- Organizational process manuals
- Applicable regulations and legislation
- Architectural decision records
- Operational guides from the requesting unit

---

### Step 0.1: Convert to Markdown (Docling) 🆕

**You do:** Run the conversion skill:

```
Execute the skill docs/skills/llc-step-0-1.md
```

**The AI does:**
- Detects all formats in `docs/business/ingestion/` (PDF, DOCX, PPTX, HTML)
- Converts each file to Markdown using **Docling** (or Pandoc as fallback)
- Places the converted `.md` files in `docs/business/ingestion/converted/`
- Generates `_CONVERSION_REPORT.md` with statistics and status for each file

**Prerequisite:** Python 3.10+ + `pip install docling`

**Why Markdown?** Fewer tokens, less structural noise, better AI comprehension. PDFs and DOCXs have heavy tags that consume unnecessary tokens.

---

### Step 0.5: Strategic Vision + Modules

**You do:** Run the skill in your AI client:

```
Execute the skill docs/skills/llc-step-0-5.md
```

**The AI does:**
- Reads all files in `docs/business/ingestion/converted/` (pure Markdown)
- Generates `docs/business/specs/visao_estrategica_e_negocio.md` (system vision)
- Generates `MOD-[SIGLA]-[NNN]_[name].md` files (one per identified module)

**You validate:** 👤 Gate 1
- Does the vision cover the full business scope?
- Are modules correctly identified and named?
- Any sections left with `[NOT IDENTIFIED]`? If so, supplement them.

**Only advance when approved.**

---

### Step 1: 7 Specifications

**You do:**

```
Execute the skill docs/skills/llc-step-1.md
```

**The AI does:** Generates 7 documents in `docs/business/specs/`:
1. `glossario.md`
2. `requisitos_funcionais.md`
3. `requisitos_nao_funcionais.md`
4. `regras_negocio.md`
5. `workflows_bpmn.md`
6. `perfis_permissoes.md`
7. `catalogo_integracoes.md`

**You validate:** 👤 Gate 2
- Are glossary terms consistent across documents?
- Do access profiles cover all actors?
- Do the listed integrations match reality?

**Only advance when approved.**

---

### Step 2: PRDs (Executive + Technical)

**You do:**

```
Execute the skill docs/skills/llc-step-2.md
```

**The AI does:** Generates in `docs/prd/`:
- `executive_PRD.md` — for stakeholders and managers (institutional language)
- `PRD_tecnico_institucional.md` — for the development team (technical language)

**You validate:** 👤 Gate 3
- Does the executive PRD clearly communicate the system's value?
- Does the technical PRD cover all requirements from the specs?
- Are both consistent with each other?

**Only advance when approved.**

---

### Step 3: PRPs (Project Requirement Proposals)

**You do:**

```
Execute the skill docs/skills/llc-step-3.md
```

**The AI does:** Generates `PRP-001-[name].md`, `PRP-002-[name].md`, etc. in `docs/prps/`. Each PRP is a self-contained implementation contract.

**You validate:** 👤 Gate 4
- Is PRP granularity appropriate (2–8 days each)?
- Do dependencies between PRPs make sense?
- Did any PRD requirement get left without a PRP?

**Only advance when approved.**

---

### Step 4: Planning (Matrix + Plan + Waves)

**You do:**

```
Execute the skill docs/skills/llc-step-4.md
```

**The AI does:** Generates in `docs/planning/`:
- `DEPENDENCY_MATRIX.md` — dependency graph and critical path
- `PLAN.md` — roadmap, milestones, DoD
- `EXECUTION_WAVES.md` — execution waves with grouped PRPs

**You validate:** 👤 Gate 5
- Are waves well-grouped?
- Is the critical path realistic?
- Does the total estimated time make sense?

**Only advance when approved.**

---

### Step 5: Architecture

**You do:**

```
Execute the skill docs/skills/llc-step-5.md
```

**The AI does:** Generates `docs/architecture/ARCHITECTURE.md` with:
- Technology stack (frontend, backend, database, infrastructure)
- C4 diagrams (context, containers, components)
- ADRs (justified architectural decisions)
- Security strategy and CI/CD

**You validate:** 👤 Gate 6
- Is the stack viable in your environment?
- Are architectural decisions justified?
- Are performance and security NFRs addressed?

**Only advance when approved.**

---

### Step 5a: Architecture Patterns (Mandatory Architectural Patterns)

> **⚠️ MANDATORY** — This sub-step must be executed **after Step 5 and before Step 8**.
> The patterns defined here are binding and verified by automated fitness functions.

**You do:**

```
Execute the skill docs/skills/llc-step-5a-architecture-patterns.md
```

**The AI does:** Uses the template `docs/templates/ARCHITECTURE_PATTERNS_TEMPLATE.md` to define and document:
- **Clean Architecture Layers** — `domain/`, `application/`, `infrastructure/` structure per module
- **Repository Pattern** — `I{Nome}Repository` interfaces + `Prisma{Nome}Repository` implementations
- **Pure Domain Layer** — domain entities without decorators, no framework imports
- **Use Cases** — one class per use case with `execute(dto)` method
- **Event Bus** — async inter-module communication via EventEmitter2

**Artifacts generated/updated:**
- `docs/architecture/ARCHITECTURE.md` — expanded §7, §8, §9 with code examples
- `.ace/arch-config.yaml` — complete fitness function configuration (25+ rules)
- `docs/architecture/adr/ADR-008` to `ADR-011` — ADRs for Repository Pattern, Domain Layer, Use Cases, Event Bus

**You validate:** 👤 Gate 6a (new gate)
- Are the architectural patterns appropriate for the project (greenfield vs brownfield)?
- Does `.ace/arch-config.yaml` reflect the correct core modules?
- Are ADRs 008-011 created and justified?
- Is the intra-module folder structure defined?

**Only advance when approved.**

---

### Step 5d: Secure-by-Design Enforcement (Mandatory)

> **MANDATORY** — This sub-step must run after Step 5c and before Step 6.
> Establishes 10 hard security gates that the agent loads before generating any code.

**You do:**

```
Execute the skill docs/skills/llc-step-5d-secure-by-design.md
```

**The AI does:** Establishes the Secure-by-Design framework with:

1. **10 Hard Gates** — unbreakable rules: NEVER hardcode secrets, NEVER use XOR/MD5, NEVER reuse IV, NEVER AsyncStorage for tokens, NEVER SQL with interpolation, NEVER log PII, NEVER fallback that grants privileges, NEVER validate premium client-only, NEVER AES-CBC, NEVER tables without user_id
2. **Threat Modeling Check** — 6 mandatory questions before each feature (PII data? Storage? Protection at rest? In transit? Access? Fail-closed?)
3. **4 Safe Code Templates** — piiEncryption (AES-256-GCM), secureStorage (fail-closed), parameterizedQueries (anti-injection), entitlementValidation (fail-safe)
4. **5 Security Fitness Functions** — no-hardcoded-secrets, no-sql-injection, no-asyncstorage-tokens, no-client-only-auth, user-id-in-tables

**Artifacts generated/updated:**
- `.ace/arch-config.yaml` — expanded with `security_rules`
- `docs/architecture/adr/ADR-018-secure-by-design.md`
- Fitness functions `--check-security` configured

**You validate:** 👤 Gate 5d
- Do the 10 hard gates make sense for the project domain?
- Does any template need adaptation to the specific stack?
- Do fitness functions `--check-security --strict` pass without blocks?
- Is ADR-018 created and justified?
- Are exceptions documented (e.g., project without database → rule #10 doesn't apply)?

**Only advance when you approve.**

---

### Step 6: Tasks

**You do:**

```
Execute the skill docs/skills/llc-step-6.md
```

**The AI does:** Generates `docs/planning/TASKS.md` with:
- Concrete tasks per PRP (scaffolding, backend, frontend, testing)
- Assigned agents (dev_agent, qa_agent, security_agent)
- Explicit parallelization (✅ parallel, ⚠️ after setup, ❌ sequential)
- Estimates in hours/days

**You validate:** 👤 Gate 7
- Are all tasks actionable and unambiguous?
- Are agents correctly assigned?
- Are estimates realistic?

**Only advance when approved.**

---

### Step 7: Design System

**You do:**

```
Execute the skill docs/skills/llc-step-7.md
```

**The AI does:** Generates `docs/design/DESIGN_SYSTEM.md` by filling the `Design_System_Master.md` template with:
- Design tokens (colors, typography, spacing, dark mode)
- Component library (variants, states, props)
- Interface patterns (tables, forms, navigation, dashboards)
- Micro-interactions and state matrix

**You validate:** 👤 Gate 8
- Does the color palette reflect the project identity?
- Do all components have defined states (loading, empty, error)?
- Does the Design System cover the system's flows?

**Only advance when approved.**

---

### Step 8: Setup + Mock Data Layer

**You do:**

```
Execute the skill docs/skills/llc-step-8.md
```

**The AI does:**
- Initializes the project with the defined stack (lint, type-check, dependencies)
- Creates `mocks/data/` with realistic JSONs (users per profile + entities)
- Creates `mocks/handlers/` with full CRUD via MSW
- Updates `TASKS.md` and PRPs with progress

**You validate:** 👤 Gate 9
- Does the project compile and run locally?
- Are mock data realistic and covering all profiles?
- Do handlers simulate errors correctly?

**Only advance when approved.**

---

### Step 8b: Repository Pattern (Mandatory)

> **MANDATORY** — This sub-step must be executed after Step 8 (setup + mocks) and before Step 11 (Execution).
> Implements the Repository Pattern with interfaces (Ports & Adapters) in all modules.

**You do:**

```
Execute the skill docs/skills/llc-step-8b-repository-pattern.md
```

**The AI does:** Uses the template `docs/templates/REPOSITORY_PATTERN_TEMPLATE.md` to implement:
- Repository interfaces `I{Nome}Repository` in `src/*/domain/repositories/`
- Prisma implementations `Prisma{Nome}Repository` in `src/*/infrastructure/repositories/`
- Prisma → Domain mappers in `src/*/infrastructure/mappers/`
- DI bindings in modules (`{ provide: I*Repository, useClass: Prisma*Repository }`)
- Updates Services to inject interfaces (`@Inject(I*Repository)`), not `PrismaService`

**Artifacts generated:**
- `src/*/domain/repositories/i*.repository.ts` — interfaces
- `src/*/infrastructure/repositories/prisma-*.repository.ts` — implementations
- `src/*/infrastructure/mappers/*.mapper.ts` — mappers
- `src/*/*.module.ts` — updated DI bindings
- `src/*/*.service.ts` — services updated to use interfaces

**You validate:** 👤 Gate 9b (new gate)
- `grep -r "PrismaService" src/*/domain/ src/*/application/ src/*/use-cases/` — returns empty?
- Interfaces exist for all aggregate roots?
- Prisma implementations exist and delegate correctly?
- Mappers cover all domain entity fields?
- DI bindings exist in all modules?
- Fitness function `repository-pattern` passes: `python .ace/scripts/fitness-functions.py --check repository-pattern`?

**Only advance when approved.**

---

### Step 9: Testing Documentation

**You do:**

```
Execute the skill docs/skills/llc-step-9.md
```

**The AI does:** Generates in `docs/testing/`:
- `TESTING_GUIDE.md` — philosophy, pyramid, test templates, mock strategy
- `COVERAGE_BASELINE.md` — coverage baseline (starting point)
- `COVERAGE_PROGRESS.md` — phase goals and weekly progress table

**You validate:** 👤 Gate 10
- Do test commands match the defined stack?
- Are coverage thresholds realistic (80% unit, 70% integration)?
- Are test templates reusable?

**Only advance when approved.**

---

### Step 10: Project Documentation

**You do:**

```
Execute the skill docs/skills/llc-step-10.md
```

**The AI does:**
- `README.md` at root — entry point with badges, stack, how to run, docs
- `docs/DEPLOYMENT.md` — environments, CI/CD pipeline, variables, rollback, monitoring
- `CLAUDE.md` — project steering file (stack, domain, architecture, constraints, commands)
- `AGENTS.md` — developer steering file (epistemic protocol, zones, TDD, handoff)

#### CLAUDE.md vs AGENTS.md: Which to use?

| File | Content | Used by |
|------|---------|---------|
| **CLAUDE.md** | WHAT the project is — stack, domain, DB, architecture, LLC constraints | Claude Code (exclusive) |
| **AGENTS.md** | HOW the developer works — zones, TDD, handoff, Grill Me | Emerging standard: Cursor, Codex, Copilot CLI, opencode |

**If your tool does NOT support `CLAUDE.md`:** Consolidate everything into `AGENTS.md` — add project sections (stack, domain, constraints) to the AGENTS template. The `<!-- @include AGENTS.md -->` in CLAUDE.md ensures tools supporting both won't duplicate rules.

**You validate:** 👤 Gate 11
- Can a new developer run the project in ≤ 10 min following the README?
- Does DEPLOYMENT cover rollback and monitoring?
- Are there no exposed secrets or credentials?

**Only advance when approved.**

---

### Step 10.5: User Guide 🆕

**You do:**

```
Execute the skill docs/skills/llc-user-guide.md
```

**The AI does:**
- Reads all PRPs and extracts pages declared in the `user_docs` section
- Generates `docs/user-guide/USER_GUIDE.md` — complete skeleton with index and navigation
- Generates `docs/user-guide/index.md` — user guide home page
- Generates `docs/user-guide/visao-geral.md` — system overview in end-user language
- Generates `docs/user-guide/perfis/index.md` — profile-indexed guide

**You validate:** 👤 Gate 11.5
- Does the structure cover all modules?
- Do profiles have relevant pages?
- Is the index navigable?
- Is the language end-user friendly?

**Only advance when approved.**

---

### Step 10.6: Security Audit 🆕

**You do:**

```
Execute the skill docs/skills/llc-step-11-security.md
```

**The AI does:**
- Runs **SCA** (npm audit or pip-audit) — dependency vulnerability scanning
- Runs **SAST** (Semgrep) — static code analysis
- Runs **Secret Scanning** (Gitleaks) — credential leak detection
- Classifies findings by severity (CVSS): 🔴 Critical (≥ 9.0), 🟡 High (7.0–8.9), 🟢 Medium/Low (< 7.0)
- Generates `docs/security/SECURITY_AUDIT_REPORT.md` with consolidated report and recommendations

**You validate:** 👤 Gate 11-SEC
- 0 critical vulnerabilities (CVSS ≥ 9.0)?
- No real secrets exposed (false positives in mocks/docs are OK)?
- High vulnerabilities reviewed and decision recorded?

**Only advance when approved.**

---

### Step 10.7: Data Contract Validation 🆕

**You do:**

```
Execute the skill docs/skills/llc-step-12-null-safety.md
```

**The AI does:**
- Reads all PRPs and extracts data definitions (TypeScript, Python, Prisma, Markdown tables)
- Checks that every field declares explicit nullability (`?`, `| null`, `Optional`)
- Checks that nullable fields have documented fallbacks
- Checks that endpoints declare `maxBodySize`, `rateLimit`, `maxItems` (A06 — DoS prevention)
- Checks that every POST/PUT/PATCH endpoint has an input schema (Zod, Pydantic, etc.)
- Generates `docs/security/NULL_SAFETY_REPORT.md` with complete inventory

**You validate:** 👤 Gate 12-NULL
- 0 fields without nullability specification?
- 0 endpoints without input schema?
- Payload limits declared in PRPs?

**Only advance when approved.**

---

### Step 10.8: Test Coverage Gate 🆕

**You do:**

```
Execute the skill docs/skills/llc-step-10-8-test-coverage.md
```

**The AI does:**
- Runs `python .ace/scripts/llc.py gate run --gate test-coverage`
- Checks global coverage: statements ≥ 80%, branches ≥ 70%, functions ≥ 80%, lines ≥ 80%
- Checks **zero implementation files with 0% coverage** (CRITICAL)
- Checks critical paths (auth, payments, data mutations) ≥ 90%
- Detects coverage regression > 5% vs. previous baseline
- Generates report in `docs/testing/COVERAGE_REPORT.md` in standard format

**You validate:** 👤 Gate 10-COVERAGE
- 0 implementation files with 0% coverage?
- Global thresholds met (statements ≥ 80%, branches ≥ 70%, functions ≥ 80%, lines ≥ 80%)?
- Critical paths ≥ 90%?
- No regression > 5% vs. baseline?

**Only advance when approved.**

---

### Step 11: Execution

**Now development begins.** You have two tracks:

### Step 11a: Domain Modeling (Mandatory Pre-Execution)

> **MANDATORY** — For each core PRP, execute this sub-step **before** starting implementation (Track A or B).
> Generates domain entities, use cases, and repository interfaces specific to the PRP.

**You do:**

```
Execute the skill docs/skills/llc-step-11a-domain-modeling.md --prp PRP-001
```

**The AI does:** Uses the template `docs/templates/DOMAIN_MODEL_TEMPLATE.md` (generated in Step 5a) to:
- Create `src/{module}/domain/{entity}.entity.ts` — pure domain entity (no decorators)
- Create `src/{module}/domain/repositories/i{entity}.repository.ts` — repository interface
- Create `src/{module}/application/use-cases/{action}.use-case.ts` — use cases with `execute(dto)`
- Update `docs/prps/PRP-{NNN}.md` §7 (Data Model) with definitive contracts

**Artifacts generated per PRP:**
- Domain entities in `domain/`
- Use cases in `application/use-cases/`
- Repository interfaces (if not existing from Step 8b)
- PRP updated with §7 complete

**You validate:** 👤 Gate 11-PRE (new gate)
- Do entities reflect the PRP's business rules?
- Do use cases cover all RFs from the PRP?
- Are repository interfaces consistent with Step 8b?
- Are data contracts (§7 of PRP) complete and validated in Step 12?

**Only advance to Track A/B when approved.**

#### Track A: Non-UI PRPs (backend, infra)

```
Execute tasks from TASKS.md directly with development agents.
Each non-UI PRP is implemented sequentially or in parallel (per matrix).
```

#### Track B: UI PRPs (frontend) — Prototyping Subflow

For each module or PRP involving screens, run:

```
Execute the skill docs/skills/llc-subflow-prototyping.md --module MOD-PLN-001
```

> **⚡ API-first enforcement:** Before starting F5 (Code), the harness runs automatic backend contract verification via `_verify_backend_contracts()` in `llc_wave.py`. If endpoints declared in the PRP don't exist or are stubs (`return []`), the wave **blocks** — the frontend doesn't advance on non-existent contracts. This prevents the pattern: "TASKS.md marks ✅ → agent assumes ready → creates UI with placeholder → service is still `return []`".

The subflow has 6 phases:

| Phase | What Happens | You Do |
|-------|-------------|--------|
| **F1** Discovery | AI generates personas and journey maps | Review |
| **F2** Tokens | AI generates CSS/JSON tokens from Design System | Review |
| **F3** Lo-Fi | AI generates low-fidelity wireframes | Review |
| **F4** Hi-Fi | AI generates high-fidelity prototype | 🔴 **VISUAL CHECKPOINT** — Approve the visual |
| **F5** Code | AI generates components and pages | Review |
| **F6** Validation | AI validates usability, a11y, responsiveness | Review |

---

## Approval Flow

```
                    👤 = Mandatory human gate
                    🔴 = Mandatory visual checkpoint

Step 0 ──→ Step 0.1 ──→ Step 0.5 ──👤──→ Step 1 ──👤──→ Step 2 ──👤──→ Step 3 ──👤──→
Step 4 ──👤──→ Step 5 ──👤──→ Step 5a ──👤──→ Step 5b ──👤──→ Step 5c ──👤──→ Step 5d ──👤──→ Step 6 ──👤──→ Step 7 ──👤──→
Step 8 ──👤──→ Step 9 ──👤──→ Step 10 ──👤──→
Step 10.5 ──👤──→ Step 10.6 ──👤──→ Step 10.7 ──👤──→ Step 10.8 ──👤──→

Step 11:
  ├── Non-UI PRPs → direct agent
  └── UI PRPs → F1→F2→F3→F4─🔴─→F5→F6
```

**Golden rule:** No step advances without the previous gate approved.

---

### Step 11.2: PRP Verify (Mechanical Acceptance of PRP)

**Before merging, the PRP undergoes mechanical acceptance verification.** The `prp_verify.py`
cross-references each FR declared in §2 of the PRP with the actual test and implementation files.

> **Mechanical enforcement:** The harness `session_end()` blocks the merge on CRITICAL
> (declared file missing, stub, component missing). Bypass: `LLC_PRP_NO_VERIFY=1`
> (logged — see `llc-pipeline-design.en.md §8.7`).
>
> **New:** `prp_verify.py` now runs `check_project_coverage()` — checks project-wide
> coverage (not just the PRP). Thresholds: statements ≥ 80%, branches ≥ 70%,
> functions ≥ 80%, lines ≥ 80%; **0 files with 0% coverage**; critical paths ≥ 90%.

```
Execute the skill docs/skills/llc-step-11-2-prp-verify.md
```

**The AI does:**
- Runs `python .ace/scripts/prp_verify.py --prp {ID} --strict --json`
- Emits FR-by-FR report with implementation evidence
- Records `<gate_result step="11.2">` with the decision

**Note:** `_post_wave_check()` also blocks waves with CRITICAL — verification
happens at both individual PRP level (session_end) and wave level
(post-wave). Project-wide coverage check runs as part of `prp_verify.py --all`.

### Step 11b: Arch Fitness (Architectural Fitness Functions — Mandatory in PRP Verify)

> **MANDATORY** — Executed as part of `prp_verify.py` and Gate 11.2.
> Verifies if the PRP implementation violates any architectural fitness function.

**Automatic execution:**
- `prp_verify.py` internally calls `fitness-functions.py --all --strict`
- Also manually runnable: `python .ace/scripts/fitness-functions.py --all --strict`

**Checks validated (per `.ace/arch-config.yaml`):**
- **Dependency Rule** — domain does not import infrastructure
- **Circular Dependencies** — no cycles between modules
- **Interface Coverage** — all aggregate roots have `I{Nome}Repository`
- **Domain Isolation** — `domain/` does not import `@prisma/client`, `repositories/`, `prisma/`
- **Use Case Size** — use cases ≤ 200 lines, single responsibility
- **Module Coverage** — core modules ≥ 90% coverage, others ≥ 80%

**You validate:** 👤 Gate 11.2 includes fitness functions
- Does `python .ace/scripts/fitness-functions.py --all --strict` pass (exit 0)?
- No BLOCKING violations in core modules?
- WARNING violations acceptable with documented justification?

**Only approve if fitness functions pass.**

---

## Practical Tips

### If a skill fails
- Read the error. The AI will report what went wrong.
- Fix the input (e.g., missing document, incomplete template).
- Re-run the skill.

### If a gate is rejected
- Note what needs to be adjusted.
- Ask the AI to fix it: "The glossary is inconsistent with the functional requirements. Fix it."
- Re-validate.

### Monitoring Code Health

With multiple agents working in parallel, monitoring structural metrics is essential:

```
Execute the skill docs/skills/llc-code-health.md
```

Or directly via script:

```
python .ace/scripts/code-health.py --since "30 days ago"
```

The script monitors structural metrics + test coverage:

**Structural metrics:**
- **% Moved Code:** rate of code reorganized into modules (alert if < 10%)
- **Copy/Paste vs Moved:** duplication exceeding reuse (alert if copy > moved)
- **% Legacy Touch:** old code being refactored (alert if < 20%)

**Test coverage (new):**
- **Global statements ≥ 80%**, branches ≥ 70%, functions ≥ 80%, lines ≥ 80%
- **CRITICAL:** 0 implementation files with 0% coverage
- **Critical paths** (auth, payments, data mutations) ≥ 90%
- **Coverage regression:** drop > 5% = critical alert

If critical alerts fire, schedule a cross-PRP refactoring wave.

### Cross-Cutting Pipeline Tools

Beyond the main steps, LLC includes tools that operate between stages. See [`llc-pipeline-design.en.md`](llc-pipeline-design.en.md) for full documentation:

| Tool | Skill | Function | Pipeline Design |
|------|-------|----------|:--------------:|
| **Impact Analyzer** | `llc-impact-analyzer` | Detects which downstream artifacts are affected by changes. Use before refactoring. | [§9](llc-pipeline-design.en.md#9-rastreabilidade-e-analise-de-impacto) |
| **Code Health** | `llc-code-health` | Monitors structural metrics (Moved Code, Copy/Paste, Legacy Touch). Use per wave. | [§10](llc-pipeline-design.en.md#10-saude-estrutural-do-codigo-code-health) |
| **ACE Context** | `llc-ace-context` | Cross-session continuity protocol. Managed automatically by the harness. | [§8](llc-pipeline-design.en.md#8-ace--agentic-context-engineering) |

**LLM Operation Modes:** For Steps 0-10 (specification), use Thinking/Reasoning mode. For Step 11 (execution), use Regular mode. For post-rejected-gate fixes, use Thinking mode. See the full table above in [LLM Operation Mode](#llm-operation-mode).

### If you need to restart a step
- Skills are idempotent. The AI will ask before overwriting existing files.
- Answer "yes, overwrite" or "no, create a new version with _v2 suffix."

### Working in a team
- The pipeline supports multiple users. Each gate is a natural synchronization point.
- Use Git branches to isolate each step's work if desired.
- Artifacts are Markdown files — use PRs for collaborative review.

---

## Quick Reference

| I want to... | Command |
|--------------|---------|
| Start the pipeline | `Execute the skill docs/skills/llc-step-0-1.md` (conversion) |
| Run Secure-by-Design | `Execute a skill docs/skills/llc-step-5d-secure-by-design.md` |
| Jump to a specific step | `Execute the skill docs/skills/llc-step-N.md` ensuring previous gates are approved |
| Prototype a module | `Execute the skill docs/skills/llc-subflow-prototyping.md --module MOD-PLN-001` |
| Guarantee every wave becomes an `.ace` session | Install the pre-commit hook: `cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit` (see [§8.7](llc-pipeline-design.en.md#87-guaranteed-session-registration-enforcement)) |
| Verify test coverage (Gate 10-COVERAGE) | `python .ace/scripts/llc.py gate run --gate test-coverage` |
| Run pre-wave-check (build + boot + health + coverage) | `bash .ace/scripts/pre-wave-check.sh` |
| View code health trends | `python .ace/scripts/code-health.py --since "30 days ago" --json` |
| See the full design | Read [`llc-pipeline-design.en.md`](llc-pipeline-design.en.md) |
| See the directory structure | Read [`llc-pipeline-design.en.md` §2](llc-pipeline-design.en.md#2-directory-architecture) |
| Understand a term | Read [`llc-pipeline-design.en.md` §7](llc-pipeline-design.en.md#7-glossary) |

---

## Next Steps After the Pipeline

1. Mocked MVP is running → validate with stakeholders
2. MVP CHECKPOINT approved → implement real integrations
3. Integrations working → deploy to staging
4. Acceptance tests passing → deploy to production
5. Monitor and iterate
