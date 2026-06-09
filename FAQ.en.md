# FAQ — Live and Let Code (LLC)

**Version:** 1.2.0 — June 2026

---

## Fundamental Concepts

### What is an agentic development workflow?

A structured methodology that uses specialized AI agents collaborating throughout the software lifecycle — from analysis and requirements through architecture, implementation, and quality assurance. Unlike "vibe coding" (informal prompt-based coding), agentic workflows define roles, artifacts, quality gates, and agent handoffs. LLC materializes this in 13 skills, 11 human gates, and a context continuity protocol (ACE).

### What is "vibe coding" and why do I need a structured workflow?

Vibe coding is an informal AI coding approach where requirements are ad hoc and context easily gets lost. It works for quick experiments but generates technical debt, inconsistent code, and lack of governance. Structured workflows like LLC replace this with formal Grill Me-generated specifications, specialized per-stage agents, persistent git-versioned artifacts, and quality gates with mandatory human validation.

### What is "context rot"?

The phenomenon where AI quality drops as the context window fills up: 0-30% = peak quality; 50%+ = starts rushing and cutting corners; 70%+ = hallucinations and forgotten requirements. LLC solves this via the **ACE** protocol (`<context_seed>` of ~300 tokens vs full history of ~22,000 tokens) and **self-contained PRPs** — each implementation agent receives only the PRP it needs to execute, not the entire project.

### What is Spec-Driven Development (SDD)?

The practice of front-loading structured, machine-readable specifications (strategic vision, specs, PRDs, PRPs) so AI agents can contribute reliably to the codebase. In LLC, Steps 0-GF through 3 produce specifications in cascade with full traceability — from strategic vision to PRP, each artifact references its origin. Grill Me ensures gaps are exposed before generation, not discovered after.

### What is PRRS (Prismatic Ranked Recursive Summarization)?

The architectural pattern where the same data source is analyzed from **multiple simultaneous angles** (prisms) and then converges into layers of increasing granularity. In LLC: Step 1's 7 specs are 7 prisms over the ingestion docs; Step 2's 2 PRDs are 2 prisms over the specs (executive vs technical); Step 3's N PRPs are N prisms over the technical PRD.

### What is ACE (Agentic Context Engineering)?

LLC's cross-session continuity protocol. Combines Markdown (human readability), XML tags (machine parseability), and YAML front matter (metadata). Each session produces an append-only file in `.ace/sessions/` that is never rewritten. At the end, a 4-field `<context_seed>` compresses session state into ~300 tokens. The next session loads only this seed, not the full history.

### What are Human Gates?

Mandatory human validation points in the LLC pipeline. No step advances without explicit user approval. LLC has 11 human gates + 1 visual checkpoint (prototyping subflow) + QA checkpoints during execution. A rejected gate returns the flow to the previous step with `<gate_result decision="rejected">` logged in ACE.

### What is Grill Me?

The mandatory questioning protocol the AI runs in Steps 0.5, 1, 2, and 3 BEFORE generating any artifact. The AI analyzes input documents, identifies ambiguities, and presents up to 8 questions ranked by criticality (🔴 blocking, 🟡 high, 🟢 medium). The user answers selectively and the AI then generates artifacts based on those answers. Eliminates the main vibe coding failure point: unvalidated assumptions.

### What is a PRD? Why is there an Executive PRD and a Technical PRD?

A PRD (Product Requirements Document) formalizes a software product's requirements, serving as a contract between stakeholders and the development team. LLC generates two PRDs because each audience needs a different level of detail:

| PRD | Audience | Content | Typical length |
|-----|----------|---------|----------------|
| **Executive** | Managers, sponsors, non-technical stakeholders | Vision, business objectives, macro scope, expected benefits, success metrics | ~100 lines |
| **Technical** | Architects, developers, QA | Proposed stack, detailed requirements, API contracts, data model, integrations, constraints | ~400 lines |

The Executive PRD answers "why are we building this?" and "what's the value?". The Technical PRD answers "how will we build it?" and "what are the constraints?". Both are generated from the same 7 specs from Step 1 — PRRS in action: same source, two different prisms.

### What is a PRP?

A PRP (Project Requirement Proposal) is LLC's self-contained implementation contract. Unlike a loose task, a PRP contains EVERYTHING an AI agent needs to implement a work unit without ambiguity:

- Unit context and objective
- Functional requirements in Gherkin format (Given/When/Then)
- API contracts (endpoints, payloads, authentication, errors)
- Component specifications (props, states: loading, empty, error, success)
- Database changes (tables, fields, indexes, migrations)
- Test strategy (unit, integration, E2E)
- Dependencies (which PRPs block this one and which this one blocks)
- Risks and mitigations
- Definition of Done (acceptance checklist)

A typical PRP has 2 to 8 days of estimated effort. It's granular enough for an agent to execute, yet complete enough that the agent doesn't need to consult other documents during implementation.

### How does a PRP differ from a user story?

| Dimension | User Story (Agile) | PRP (LLC) |
|-----------|-------------------|-----------|
| **Format** | "As a [role], I want [action], so that [benefit]" | Markdown document with 9 mandatory sections |
| **Context** | Depends on Product Owner and sprint for details | Self-contained — the agent reads only the PRP |
| **Requirements** | Acceptance criteria in natural language | Executable Gherkin (Given/When/Then) |
| **API** | Not specified — defined during development | Documented API contracts (method, endpoint, payload, errors) |
| **Components** | Not specified | Props, states, and Design System reference |
| **Database** | Not specified | Tables, fields, indexes, and migrations |
| **Tests** | Not specified | Full strategy (unit, integration, E2E) |
| **Dependencies** | Implicit in the backlog | Explicit: "blocked by PRP-002, blocks PRP-005" |
| **Estimation** | Story points (relative, subjective) | Days (absolute, calibrated with historical data) |
| **Validation** | Human review at sprint review | DoD checklist + `<gate_result>` in ACE + automated tests |

A user story is a **promise to have a conversation** — the team fills in the gaps during the sprint. A PRP is an **executable contract** — the agent receives it, implements it, and tests it without needing to ask anything. One PRP equals one user story + technical specification + test plan + risk analysis, all in one document.

### Which agents does LLC use?

The LLC pipeline defines roles by stage, not by person. Each role is exercised by the AI when the corresponding skill is executed:

| Role | LLC Skill | Responsibility |
|------|-----------|----------------|
| **Business Analyst** | `llc-step-0-greenfield`, `llc-step-0-5` | Extracts knowledge via interview or documents, generates strategic vision and modules |
| **Spec Writer** | `llc-step-1`, `llc-step-2` | Generates specs, glossary, and PRDs (executive + technical) with Grill Me |
| **Architect** | `llc-step-5` | Defines stack, C4 diagrams, ADRs, security, and CI/CD |
| **UX/UI Designer** | `llc-step-7`, Subflow F1-F4 | Design System, wireframes, hi-fi prototypes |
| **Planner** | `llc-step-3`, `llc-step-4` | Decomposes into PRPs, generates dependency matrix and execution waves |
| **Developer** | `llc-step-8`, Step 11, Subflow F5 | Project setup, mock data, PRP implementation |
| **QA Engineer** | `llc-step-9`, `llc-code-health` | Test strategy, thresholds, structural health metrics |
| **Tech Writer** | `llc-step-10` | README, DEPLOYMENT, CLAUDE.md, AGENTS.md |
| **Orchestrator** | `llc-impact-analyzer`, `llc-ace-context` | Traceability, context continuity, cross-PRP impact analysis |

Each agent operates with restricted context scope — receiving only the artifacts needed for their stage, not the entire project.

### Do I need to use all agents for every project?

No. Small projects (e.g., single-page app, CLI script) can condense multiple roles into fewer skills. LLC is modular — you can skip steps that don't apply. The minimum viable path is: Step 0-GF (if greenfield) or 0.5 → Step 1 → Step 6 (Tasks) → Step 11 (Execution). Enterprise or regulated projects benefit from the full pipeline.

### Do agents replace human engineers?

No. Humans define direction, negotiate scope, oversee design, and approve releases. Agents improve the return on human attention — they don't replace it. LLC formalizes this with **human-in-the-loop** at every critical phase: 11 human gates, 1 visual checkpoint, and QA checkpoints during execution. No step advances without explicit approval.

### How do agents communicate with each other?

Through **persistent artifact handoffs** (strategic vision, specs, PRDs, PRPs, architecture) versioned in Git — not through chat conversations. ACE (`<context_seed>`) compresses session state into 4 fields for the next session. `dependency-graph.yaml` + `impact-analyzer.py` ensure changes in one artifact correctly propagate to downstream artifacts. Each agent receives only what it needs for its task, optimizing context window usage.

---

## Workflow and Phases

### What are the typical phases of an agentic workflow?

A complete agentic workflow covers the software lifecycle in 4 macro-phases, each with specialized agents and validation gates:

| Macro-phase | LLC Steps | What happens |
|-------------|-----------|--------------|
| **1. Discovery & Specification** | 0-GF to 3 | Requirements gathering (or greenfield interview), spec generation, PRDs and PRPs with Grill Me |
| **2. Planning & Architecture** | 4 to 7 | Dependency matrix, execution waves, architecture (C4 + ADRs), Design System |
| **3. Foundation & MVP** | 8 to 10 | Project setup, mock layer (MSW), testing documentation, steering files (CLAUDE.md/AGENTS.md) |
| **4. Execution & Delivery** | 11 + Subflow | Non-UI PRPs (direct agents), UI PRPs (subflow F1-F6), code health, QA gates, deploy |

### What are "Agentic Planning" and "Context-Engineered Development"?

Two complementary LLC pillars:

| Pillar | What it is | How LLC implements it |
|--------|-----------|----------------------|
| **Agentic Planning** | Structured planning to maximize parallelism between agents | Steps 3-4: self-contained PRPs, dependency matrix, execution waves with critical path analysis |
| **Context-Engineered Development** | Development that preserves context between sessions without saturating the window | ACE (`<context_seed>`), Grill Me (questions before generation), PRPs as isolated contracts (agent doesn't need the entire project) |

Agentic Planning answers "what to do and in what order." Context-Engineered Development answers "how to do it without losing the thread between sessions."

### How does the LLC workflow work step by step?

1. **You load documents** into `docs/business/ingestion/` (or, if you have none, the AI interviews you via greenfield flow)
2. **The AI converts** everything to Markdown (Docling) and asks questions to fill gaps (Grill Me)
3. **The AI generates** strategic vision, specs, PRDs, and PRPs — each stage validated by you (human gates)
4. **The AI plans** execution waves and defines architecture, stack, Design System
5. **The AI sets up** the project, creates mock data, and testing documentation
6. **You approve** and the AI implements PRPs in parallel (UI PRPs go through the prototyping subflow with visual checkpoint)
7. **Code health** monitors structural metrics; QA gates validate before deployment

### What is "aggressive atomicity"?

The principle that each work unit should be small enough to fit within ~50% of a fresh context window, ensuring the agent always operates in the peak quality zone (0-30% fill). In LLC:

- **PRPs are sized for 2-8 days** of effort — small enough for an agent to complete without context degradation
- **Waves group PRPs** so the wave set doesn't exceed context capacity
- **Independent PRPs run in parallel** (separate worktrees); dependent PRPs wait for blockers to complete
- The 4-field `<context_seed>` ensures the agent resumes exactly where it left off, without reloading history

### What is PRP decomposition (equivalent to "epic sharding")?

The process of breaking a comprehensive PRD into focused, self-contained development units. In LLC, the decomposition chain is:

```
Technical PRD (~400 lines)
    ↓ Step 0.5: decomposed into modules (MOD-*)
Modules (~100 lines each)
    ↓ Step 3: decomposed into PRPs (PRP-*)
PRPs (~50-80 lines each)
    ↓ Step 6: decomposed into tasks (TASK-*)
Tasks (checkboxes in TASKS.md)
```

Each level preserves the full context needed for its execution, eliminating the need to consult the original PRD during implementation.

---

## Artifacts and Documents

### What artifacts does the LLC workflow produce?

The LLC pipeline generates 25+ versioned artifacts, organized by stage:

| Stage | Artifacts | Description |
|-------|-----------|-------------|
| 0.5 | `visao_estrategica_e_negocio.md`, `MOD-*.md` | System vision and module specifications |
| 1 | 7 specs (`glossario.md`, `requisitos_funcionais.md`, `requisitos_nao_funcionais.md`, `regras_negocio.md`, `workflows_bpmn.md`, `perfis_permissoes.md`, `catalogo_integracoes.md`) | Detailed specifications covering terminology, features, constraints, flows, and integrations |
| 2 | `executive_PRD.md`, `PRD_tecnico_institucional.md` | Executive PRD (stakeholders) and technical PRD (developers) |
| 3 | `PRP-*.md` | Self-contained implementation contracts |
| 4 | `DEPENDENCY_MATRIX.md`, `PLAN.md`, `EXECUTION_WAVES.md` | Planning: dependency matrix, delivery plan, and execution waves |
| 5 | `ARCHITECTURE.md` | Stack, C4 diagrams, ADRs, security, CI/CD |
| 6 | `TASKS.md` | Concrete tasks with agents, estimates, and checkboxes |
| 7 | `DESIGN_SYSTEM.md` | Tokens, components, interface patterns, and accessibility |
| 8 | `mocks/` (data + handlers) | Mock data (JSON) + MSW handlers for MVP |
| 9 | `TESTING_GUIDE.md`, `COVERAGE_BASELINE.md`, `COVERAGE_PROGRESS.md` | Test strategy, baseline, and coverage targets |
| 10 | `README.md`, `DEPLOYMENT.md`, `CLAUDE.md`, `AGENTS.md` | Project docs, deployment, and steering files |

### What is PLAN.md?

`PLAN.md` is the delivery planning document generated in Step 4. It contains:

- **Roadmap & milestones:** project phases with target dates and status
- **Deploy strategy:** environments (dev, staging, prod) and pipelines
- **Definition of Done (DoD):** 10+ criteria each delivery must satisfy
- **Master PRP List:** all PRPs with estimates (planned vs. actual)
- **Velocity tracker:** team/agent velocity tracking
- **Planning documentation:** links to design docs and PRPs

It answers "when will it be ready?" and "what has already been delivered?".

### What is TASKS.md?

`TASKS.md` is the development backlog generated in Step 6. It decomposes each PRP into concrete, actionable tasks:

- **Tasks per PRP:** scaffolding, backend, frontend, testing, documentation
- **Assigned agents:** each task specifies which agent executes it (dev, qa, security)
- **Explicit parallelization:** ✅ (parallel), ⚠️ (after setup), ❌ (sequential)
- **Checkboxes:** `[ ]` pending, `[/]` in progress, `[x]` completed
- **Estimates:** in hours or days per task

ACE's `<task_completed>` automatically updates checkboxes at the end of each session.

### What is DEPENDENCY_MATRIX.md?

`DEPENDENCY_MATRIX.md` is the PRP dependency graph generated in Step 4. It contains:

- **PRP inventory:** master table with ID, phase, estimate, complexity, status
- **Critical path:** the longest sequence of dependent PRPs determining the minimum timeline
- **Dependency matrix:** "Can Start After" → "Blocks" table for each PRP
- **Mermaid diagram:** full dependency graph visualization
- **Dependency risks:** impact analysis of delays in critical PRPs
- **Capacity allocation:** PRP distribution per wave and per agent

This is the artifact that `impact-analyzer.py` consults to propagate changes.

### What is ARCHITECTURE.md?

`ARCHITECTURE.md` is the architectural definition document generated in Step 5. It contains:

- **Technology stack:** frontend, backend, database, infrastructure with justifications and discarded alternatives
- **C4 diagrams:** context (Level 1), containers (Level 2), components (Level 3) — all in Mermaid
- **ADRs (Architecture Decision Records):** architectural decisions with context, decision, consequences, and alternatives
- **Security strategy:** authentication, authorization, encryption, compliance
- **CI/CD:** pipeline, environments, quality gates
- **Architectural risks:** risk register with probability, impact, and mitigation
- **Monitoring & observability:** business metrics, SLIs, SLOs, logging

### What is DESIGN_SYSTEM.md?

`DESIGN_SYSTEM.md` is the design system document generated in Step 7 from the expanded `Design_System_Master.md` template. It contains:

- **Design tokens:** colors (light + dark mode), typography, spacing, elevation
- **Component library:** 8+ components with variants, states, and TypeScript props
- **Interface patterns:** tables, forms, navigation, feedback, dashboards
- **Permission-aware UI:** hide, disable, read-only by profile
- **Micro-interactions:** animation catalog with duration and easing
- **State matrix:** universal states (default, hover, focus, disabled, loading, error) per component
- **Accessibility:** WCAG 2.1 AA, contrast, touch targets, aria labels

### How are artifacts versioned?

All LLC artifacts are persistent Markdown documents versioned in **Git**, treated as first-class software deliverables:

- **Semantic versioning:** each artifact has version control in its front matter or footer
- **Traceability:** `dependency-graph.yaml` maps relationships between artifacts; `impact-analyzer.py` detects which need updating when a source artifact changes
- **Human review:** each artifact passes through a human gate before being considered approved
- **Immutable history:** ACE session artifacts (`.ace/sessions/`) are append-only — never rewritten
- **PRs & code review:** artifacts can be reviewed like code, with readable diffs in git

---

## Quality & Gates

### What are "quality gates"?

Phase transition checkpoints that verify each artifact meets defined criteria before the next agent starts. In LLC, gates are formal and recorded:

- **11 human gates:** one after each generation step (0.5 through 10). The human reviews the artifact and decides: `approved`, `rejected`, or `conditional`
- **1 visual checkpoint:** in the prototyping subflow (F4 → F5). The hi-fi prototype doesn't become code without explicit visual approval
- **QA checkpoints:** during execution (Step 11): score ≥ 7.0, coverage ≥ thresholds, security audit passed

Each gate decision is recorded in ACE via `<gate_result step="N" decision="approved|rejected|conditional" reviewer="...">`. A rejected gate returns the flow to the previous step and logs a `<blocker>`.

### How to ensure AI-generated code quality?

LLC implements 6 quality assurance layers:

| Layer | LLC Mechanism |
|-------|---------------|
| **1. Specification before code** | Steps 0-GF through 3 generate detailed specs, PRDs, and PRPs with Grill Me — the AI doesn't write a single line of code before requirements are validated |
| **2. Specialized agents per phase** | Each stage has an agent with restricted context: the architect doesn't implement, the developer doesn't define requirements |
| **3. Quality gates at every transition** | 11 human gates + 1 visual checkpoint + QA gates — no artifact advances without validation |
| **4. TDD embedded in PRPs** | Each PRP defines test strategy (unit, integration, E2E). `code-health.py` monitors whether agents follow TDD |
| **5. Peer review (human and agent)** | Human `<gate_result>` + automated `llc-impact-analyzer` + pre-commit validation hooks |
| **6. Requirements-to-code traceability** | Full chain: Vision → Module → Spec → PRD → PRP → Task → Commit. `dependency-graph.yaml` + `impact-analyzer.py` ensure changes propagate correctly |

### How does TDD help prevent hallucinations?

TDD provides an **objective target** for the AI to iterate against. Without it, the AI can generate code that "looks right" but doesn't work. With TDD:

1. **Reality anchor:** the failing test is concrete proof the code doesn't work yet — the AI can't hallucinate that it's "already done"
2. **Self-healing loop:** AI writes test → runs (fails) → implements → runs (passes). If it fails again, the cycle restarts. The AI self-corrects without human intervention
3. **Overfitting prevention:** tests written before code reduce the bias of "implement just to pass the test"
4. **Regression mitigation:** every PRP has mandatory tests. If an agent breaks something, the test fails immediately — not weeks later in production

LLC enforces TDD at 3 levels: `CLAUDE.md`/`AGENTS.md` (developer golden rule), `TESTING_GUIDE.md` (coverage thresholds: ≥ 80% unit, ≥ 70% integration), and `code-health.py` (monitors whether agents add code without tests).

### What is "human-in-the-loop"?

The principle that humans remain in control of all critical development decisions. AI agents operate within human-defined guardrails — they never replace humans. In LLC:

| Where the human decides | Mechanism |
|------------------------|-----------|
| **Define objectives** | Human describes the system (ingestion) or answers the greenfield interview |
| **Negotiate scope** | Grill Me: AI asks, human answers. Unvalidated assumptions are blocked |
| **Oversee design** | VISUAL CHECKPOINT in subflow F4 → F5: prototype doesn't become code without approval |
| **Approve releases** | 11 human gates + QA checkpoints: every artifact and every wave undergoes explicit validation |
| **Record decisions** | `<gate_result>` in ACE closes the accountability loop |

Agents improve the return on human attention — they don't replace it. An engineer who used to spend 4 hours writing specs now spends 30 minutes reviewing and approving AI-generated specs.

---

## Tools & Integrations

### What tools are needed to use the LLC workflow?

**Minimum stack (required):**

| Tool | Purpose | Installation |
|------|---------|-------------|
| **Git** | Versioning all artifacts and code | `git --version` (pre-installed on most systems) |
| **Python 3.10+** | ACE scripts (sessions, impact, code-health) | `python --version` |
| **Docling** | PDF/DOCX/HTML to Markdown conversion (Step 0.1) | `pip install docling` |
| **A terminal AI client** | Executing LLC skills | Claude Code, opencode, Codex CLI, Cursor CLI — any |

**Recommended stack (optional):**

| Tool | Purpose | When to use |
|------|---------|-------------|
| **PyYAML** | `impact-analyzer.py` and ACE scripts | Included with Docling install |
| **jq** | `index.json` validation in pre-commit hook | `choco install jq` / `brew install jq` |
| **pre-commit** | Git hooks framework (automated ACE validation) | `pip install pre-commit && pre-commit install` |
| **Excalidraw MCP** | Lo-fi wireframes in prototyping subflow (F3) | https://github.com/excalidraw/excalidraw-mcp |
| **Pencil MCP** | Hi-fi prototypes in prototyping subflow (F4) | https://docs.pencil.dev |
| **Pandoc** | Conversion fallback if Docling unavailable | `choco install pandoc` / `brew install pandoc` |
| **MSW** | Mock Service Worker for mock data layer (Step 8) | `npm install msw --save-dev` |

### Which LLMs work with agentic workflows?

Any LLM supporting **tool calling** (terminal tool invocation, file read/write) and capable of **thinking/reasoning** for Steps 0-10:

| LLM | Recommendation | Notes |
|-----|---------------|-------|
| **Claude (3.5 Sonnet, 3.5 Haiku, Opus)** | ⭐⭐⭐⭐⭐ Ideal | Native thinking mode, excellent at long document analysis, consistent spec generation |
| **GPT-4o, GPT-4.1** | ⭐⭐⭐⭐ Very good | Reasoning mode (o1/o3) covers Steps 0-10; robust tool calling |
| **Gemini 2.5 Pro** | ⭐⭐⭐⭐ Very good | 1M token context window — advantage for large document ingestion |
| **Qwen (2.5, 3)** | ⭐⭐⭐ Good | Open-source, competitive code generation performance |
| **DeepSeek (V3, R1)** | ⭐⭐⭐ Good | Reasoning mode (R1) for Steps 0-10; excellent cost-benefit |
| **Mistral Large** | ⭐⭐⭐ Good | Solid in French and English; functional tool calling |

**Rule of thumb:** For Steps 0-10 (specification and planning), use an LLM with **thinking/reasoning mode**. For Step 11 (execution), regular mode is sufficient. LLC is tool-agnostic — any LLM + terminal AI client combination works, as long as it supports file read/write and command execution.

**Estimated cost per complete project (LLC pipeline):**

| Project size | Estimated tokens | Approximate cost (Claude 3.5 Sonnet) |
|-------------|-----------------|--------------------------------------|
| Small (3-5 PRPs) | ~500K tokens | $1.50 - $3.00 |
| Medium (10-15 PRPs) | ~1.5M tokens | $4.50 - $9.00 |
| Large (30+ PRPs) | ~4M tokens | $12.00 - $24.00 |

*June 2026 values. Actual cost depends on Grill Me iteration count and skill re-executions after rejected gates.* This ensures full traceability (PRP-003 → MOD-PLN-002 → Technical PRD → Strategic Vision) and allows multiple agents to work in parallel without context conflicts.

---

## Pipeline Overview

### How many steps does LLC have?

13 main skills + 1 subflow. The pipeline goes from business knowledge ingestion to production deployment:

| # | Stage | Skill | Technology / Tool |
|---|-------|-------|-------------------|
| 0 | Ingestion | — | PDF, DOCX, PPTX, HTML, TXT |
| 0-GF | Greenfield (alternative) | `llc-step-0-greenfield` | LLM in brainstorming + thinking mode |
| 0.1 | Conversion | `llc-step-0-1` | **Docling** (Python 3.10+) / Pandoc |
| 0.5 | Vision + Modules | `llc-step-0-5` | Grill Me, Markdown Templates |
| 1 | 7 Specs | `llc-step-1` | Grill Me, **PRRS** (7 analysis prisms) |
| 2 | PRDs | `llc-step-2` | Grill Me, Institutional templates |
| 3 | PRPs | `llc-step-3` | Grill Me, Gherkin contracts |
| 4 | Planning | `llc-step-4` | **Mermaid** (dependency graph), YAML |
| 5 | Architecture | `llc-step-5` | **Mermaid** (C4), ADRs, Stack decisions |
| 6 | Tasks | `llc-step-6` | **TASKS.md** with checkboxes |
| 7 | Design System | `llc-step-7` | Design tokens (CSS/JSON), Components |
| 8 | Setup + Mock | `llc-step-8` | **MSW** (Mock Service Worker), JSON |
| 9 | Testing Docs | `llc-step-9` | Jest, Vitest, Playwright, thresholds |
| 10 | Project Docs | `llc-step-10` | **CLAUDE.md**, **AGENTS.md**, README, DEPLOYMENT |
| 11 | Execution | Subflow F1-F6 | Excalidraw, Pencil, parallel agents |
| Transversal | ACE | `llc-ace-context` | **Python** (scripts), Markdown + XML, YAML |
| Transversal | Impact | `llc-impact-analyzer` | **Python**, **PyYAML**, git diff |
| Transversal | Code Health | `llc-code-health` | **Python**, git log --numstat |

---

## What if I have no documentation at all?

Use the **greenfield** flow (`llc-step-0-greenfield`). The AI conducts a structured interview across 4 dimensions (purpose, actors, features, constraints) and generates `.md` files simulating real documents in `ingestion/converted/`. Then proceed to Step 0.5 normally.

---

## Why convert documents to Markdown (Step 0.1)?

| Format | Tokens per useful info | Structural noise |
|--------|----------------------|-----------------|
| Markdown | Low | Minimal |
| JSON | Medium | Low-medium |
| XML | High | High |
| HTML | Very high | Very high |

Markdown is more efficient for LLM tokenization. **Docling** (IBM Research) converts PDF, DOCX, PPTX, and HTML to Markdown preserving structure (headings, tables, lists).

---

## What is Grill Me and when do I use it?

A mandatory question round the AI conducts **BEFORE** generating any artifact in Steps 0.5, 1, 2, and 3. The AI analyzes input documents, identifies ambiguities, gaps, and contradictions, and presents up to 8 questions ranked by criticality (🔴 blocking, 🟡 high, 🟢 medium). You can answer selectively or say "proceed with what you have."

**Enable thinking/extended reasoning mode for this phase.**

---

## What is PRRS (Prismatic Ranked Recursive Summarization)?

The architectural pattern LLC uses to analyze the same data source from **multiple simultaneous angles** (prisms) and then converge:

- Step 1: 7 specs = 7 prisms over `ingestion/converted/`
- Step 2: 2 PRDs = 2 prisms (executive vs technical) over the 7 specs
- Step 3: N PRPs = N prisms (implementation units) over the technical PRD
- Greenfield: 4 interview dimensions over the system idea

---

## What is ACE and why do I need it?

**Agentic Context Engineering** is LLC's cross-session continuity protocol. Without it, each AI session starts from scratch (model amnesia).

- **Append-only:** session files are never rewritten — only deltas are appended
- **`<context_seed>`:** at the end of each session, the AI compresses state into 4 fields (~300 tokens)
- **Savings:** ~1,500 tokens/session vs ~22,000 for full history
- **Technology:** Python (scripts), Markdown + XML tags + YAML front matter

---

## How do I maintain consistency between artifacts?

Use the **Impact Analyzer** (`llc-impact-analyzer`):

```bash
python .ace/scripts/impact-analyzer.py --files "docs/business/specs/perfis_permissoes.md" --json --skills
```

The script cross-references `git diff` with the dependency graph (`.ace/dependency-graph.yaml`) and reports:
- Which downstream artifacts are impacted
- In what order to review them
- Which skills to re-run

Integrated into the pre-commit hook as an informative check.

---

## Mermaid or ASCII for diagrams?

**Mermaid.** ASCII is universal but noisy and inefficient for LLMs. Mermaid:
- Consumes fewer tokens
- Is natively understood by the tokenizer
- Can be generated and updated by the AI itself
- Benchmarks show performance gains for open-source models on medium/hard problems

LLC uses Mermaid for: pipeline flow, dependency graph, C4 diagrams, BPMN workflows.

---

## How to prevent structural degradation with multiple agents?

Use **Code Health** (`llc-code-health`):

```bash
python .ace/scripts/code-health.py --since "30 days ago" --strict
```

Monitors 4 metrics:

| Metric | Threshold | Severity |
|--------|-----------|----------|
| % Moved Code | < 10% | 🔴 Critical |
| Copy/Paste vs Moved | copy > moved | 🟡 High |
| % Legacy Touch | < 20% | 🟡 High |

If alerts fire, schedule a cross-PRP refactoring wave.

---

## CLAUDE.md or AGENTS.md? Which to use?

| File | Content | For |
|------|---------|-----|
| `CLAUDE.md` | Stack, domain, DB, architecture, LLC constraints | Claude Code (exclusive) |
| `AGENTS.md` | Zones, TDD, handoff, Grill Me, epistemic protocol | Cursor, Codex, Copilot CLI, opencode |

**If your tool doesn't support `CLAUDE.md`:** consolidate everything into `AGENTS.md`. The `<!-- @include AGENTS.md -->` in CLAUDE.md ensures tools supporting both won't duplicate rules.

Both are auto-generated by Step 10 from templates in `docs/templates/`.

---

## How does TDD work in LLC?

1. 🔴 **RED:** Write the test first. Run — must fail.
2. 🟢 **GREEN:** Implement minimum code to pass.
3. 🔵 **REFACTOR:** Improve code while keeping tests green.

Rules:
- Tests co-located with code (`.spec.ts` alongside `.ts`)
- Factories in `test-helpers/factories/` — never hardcoded values
- Coverage: ≥ 80% unit, ≥ 70% integration
- `code-health.py` monitors whether agents are following TDD or just adding untested code

---

## How do I set up skills for my AI client?

| Client | Directory | Command |
|--------|-----------|---------|
| Claude Code | `.claude/skills/` | `cp docs/skills/llc-*.md .claude/skills/` |
| opencode | `.opencode/skills/<name>/SKILL.md` | Bash script in the guide |
| Codex | `.codex/skills/` | `cp docs/skills/llc-*.md .codex/skills/` |
| Cursor | `.cursor/skills/` | `cp docs/skills/llc-*.md .cursor/skills/` |
| Others | `.skills/` | `cp docs/skills/llc-*.md .skills/` |

Alternative: invoke by direct path — `Execute the skill docs/skills/llc-step-0-5.md`

---

## What does each Python script do?

| Script | When it runs | Function |
|--------|-------------|----------|
| `initialize_session.py` | Start of every session | Creates session file, loads `context_seed` |
| `finalize_session.py` | End of every session | Generates `context_seed`, promotes learnings, updates TASKS.md |
| `promote-learning-points.py` | Auto in finalize | Promotes learnings to `memory/` |
| `validate-tags.py` | Pre-commit hook | Validates XML tags, context_seed schema, index.json |
| `impact-analyzer.py` | Before refactoring | Propagates impact via dependency graph |
| `code-health.py` | Each wave / QA checkpoint | Monitors Moved Code, Copy/Paste, Legacy Touch |
| `pre-commit.sh` | Git pre-commit | Orchestrates ACE validation + impact analysis |

---

## Why YAML for the dependency graph instead of a database?

- Human and machine readable
- Versionable (git diff shows exactly what changed)
- Zero external dependencies
- ~600 tokens to load
- Generated and maintained by the pipeline itself (Step 4)

---

## Can I use LLC without Claude Code?

Yes. LLC is **tool-agnostic**. Each skill is a Markdown file any terminal AI client can read and execute. Specific tools (Claude Code, opencode, Cursor) are recommendations, not requirements.

---

## What happens if a human gate is rejected?

The flow returns to the previous step for correction. The AI logs the reason in ACE via `<gate_result decision="rejected">` and `<blocker>`. After the fix, the gate is re-evaluated. No step advances without explicit approval.

---

## What's the difference between dependency-graph.yaml and dependency-graph.mmd?

| File | Function | Read by |
|------|----------|---------|
| `dependency-graph.yaml` | Actual structure — used by `impact-analyzer.py` | Python scripts |
| `dependency-graph.mmd` | Documented intent — topological visualization | Humans and LLMs |

They are complementary: YAML for machines, Mermaid for visual understanding.

---

## Next steps after the pipeline?

1. Mocked MVP running → validate with stakeholders
2. MVP CHECKPOINT approved → implement real integrations
3. Integrations working → deploy to staging
4. Acceptance tests passing → deploy to production
5. Monitor code health and iterate
