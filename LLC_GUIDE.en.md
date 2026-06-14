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

## Step by Step

### 📋 Pipeline Overview (14 steps + security)

```
Step 0   → Document Ingestion
Step 0.1 → Markdown Conversion (Docling)
Step 0.5 → Strategic Vision + Modules        👤 Gate 1
Step 1   → 7 Specifications                   👤 Gate 2
Step 2   → PRDs (Executive + Technical)       👤 Gate 3
Step 3   → PRPs                                👤 Gate 4
Step 4   → Planning                            👤 Gate 5
Step 5   → Architecture                        👤 Gate 6
Step 6   → Tasks                               👤 Gate 7
Step 7   → Design System                       👤 Gate 8
Step 8   → Setup + Mock Data                   👤 Gate 9
Step 9   → Testing Docs                        👤 Gate 10
Step 10  → Project Docs + Steering Files       👤 Gate 11
Step 10.5 → User Guide                         👤 Gate 11.5
Step 11-Security → Audit (SCA+SAST+Secrets)    👤 Gate 11-SEC
Step 12-Null-Safety → Data Contracts           👤 Gate 12-NULL
Step 11  → Execution (PRPs)                    QA Checkpoints
Step 11-OWASP → Hardening (post-code)          👤 Gate 11-OWASP
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

### Step 11-Security: Security Audit 🆕

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

### Step 12-Null-Safety: Data Contract Validation 🆕

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

### Step 11: Execution

**Now development begins.** You have two tracks:

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
Step 4 ──👤──→ Step 5 ──👤──→ Step 6 ──👤──→ Step 7 ──👤──→
Step 8 ──👤──→ Step 9 ──👤──→ Step 10 ──👤──→ Step 11-Security ──👤──→ Step 12-Null-Safety ──👤──→

Step 11:
  ├── Non-UI PRPs → direct agent
  └── UI PRPs → F1→F2→F3→F4─🔴─→F5→F6
```

**Golden rule:** No step advances without the previous gate approved.

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

The script monitors 4 metrics:
- **% Moved Code:** rate of code reorganized into modules (alert if < 10%)
- **Copy/Paste vs Moved:** duplication exceeding reuse (alert if copy > moved)
- **% Legacy Touch:** old code being refactored (alert if < 20%)

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
| Jump to a specific step | `Execute the skill docs/skills/llc-step-N.md` ensuring previous gates are approved |
| Prototype a module | `Execute the skill docs/skills/llc-subflow-prototyping.md --module MOD-PLN-001` |
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
