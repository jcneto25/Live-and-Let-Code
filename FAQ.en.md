# FAQ — Live and Let Code (LLC)

**Version:** 1.5.0 — June 2026

---

## Fundamental Concepts

### What is an agentic development workflow?

A structured methodology that uses specialized AI agents collaborating throughout the software lifecycle — from analysis and requirements through architecture, implementation, and quality assurance. Unlike "vibe coding" (informal prompt-based coding), agentic workflows define roles, artifacts, quality gates, and agent handoffs. LLC materializes this in 21 skills, 15 human gates, and a context continuity protocol (ACE).

### How is LLC architecturally organized?

LLC is organized into **5 conceptual layers** from foundation to delivery:

| Layer | Responsibility | Key mechanisms |
|-------|---------------|----------------|
| **1. Context** | Manages context window, session continuity, and token compression | ACE `<context_seed>`, Document Hierarchy, compressed index, prompt caching, append-only sessions |
| **2. Knowledge** | Domain artifacts, specifications, and architectural decisions | Strategic vision, 7 specs, PRDs, PRPs, ARCHITECTURE.md (C4+ADRs), DESIGN_SYSTEM.md, USER_GUIDE.md |
| **3. Agents** | Who executes, how they reason, and with what rules | AGENTS.md (epistemic protocol, autonomy zones, TDD, handoff), per-step roles, Grill Me, CODE-REVIEW |
| **4. Workflows** | Pipeline, validation gates, and orchestration | 14 steps + subflow, 15 human gates + visual checkpoint, execution waves, PRRS, dependency matrix |
| **5. Delivery** | Parallel execution, structural quality, and deployment | Auto git worktrees, code-health.py, mock data, CI/CD, DEPLOYMENT.md |

Each layer depends on the one below: without well-managed context, knowledge won't fit in the window; without structured knowledge, agents have no direction; without well-instructed agents, workflows produce no quality; without orchestrated workflows, delivery is unreliable.

### What is "vibe coding" and why do I need a structured workflow?

Vibe coding is an informal AI coding approach where requirements are ad hoc and context easily gets lost. It works for quick experiments but generates technical debt, inconsistent code, and lack of governance. Structured workflows like LLC replace this with formal Grill Me-generated specifications, specialized per-stage agents, persistent git-versioned artifacts, and quality gates with mandatory human validation.

### What is "context rot"?

The phenomenon where AI quality drops as the context window fills up: 0-30% = peak quality; 50%+ = starts rushing and cutting corners; 70%+ = hallucinations and forgotten requirements. LLC solves this via the **ACE** protocol (`<context_seed>` of ~300 tokens vs full history of ~22,000 tokens) and **self-contained PRPs** — each implementation agent receives only the PRP it needs to execute, not the entire project.

### What is Spec-Driven Development (SDD)?

The practice of front-loading structured, machine-readable specifications (strategic vision, specs, PRDs, PRPs) so AI agents can contribute reliably to the codebase. In LLC, Steps 0-GF through 3 produce specifications in cascade with full traceability — from strategic vision to PRP, each artifact references its origin. Grill Me ensures gaps are exposed before generation, not discovered after.

### How does LLC improve upon Spec-Driven Development?

Traditional SDD has 5 legitimate criticisms. LLC was designed to address each one:

| Traditional SDD criticism | How LLC solves it |
|--------------------------|-------------------|
| **1. Rigid waterfall, too slow** — heavy documentation before any code, 10x slower | LLC **is not waterfall**. The 14 steps are a pipeline, not frozen phases. PRPs are 2-8 days and run in **parallel waves** as soon as validated. Grill Me is a short Q&A round (~15 min), not months of documentation. The mocked MVP (Step 8) delivers something functional and demonstrable in days, not months |
| **2. "Markdown Madness"** — thousands of lines of docs, 80% of time reading Markdown | ACE solves this: `<context_seed>` compresses state into **4 fields (~300 tokens)**. An implementation agent receives **only the PRP it will execute** (~50-80 lines), not the entire project. `impact-analyzer.py` tells exactly which artifacts to read, eliminating unnecessary reading |
| **3. Persistent bugs, unmaintainable code** — even with specs, generated code has trivial errors | **TDD embedded in every PRP** + `code-health.py` + self-healing loop. AI writes test → sees it fail → implements → sees it pass. If it fails, the cycle restarts. The agent doesn't deliver code without passing tests. Moved Code, Copy/Paste, and Legacy Touch metrics are monitored every wave |
| **4. Spec Drift** — manually changed code breaks the "single source of truth" | `dependency-graph.yaml` + `impact-analyzer.py` detect drift automatically: `git diff` → cross with graph → reports which artifacts are outdated. **Not manual.** Pre-commit hook alerts before commit. `<gate_result>` forces human validation before proceeding |
| **5. Obsolescence by native models** — external frameworks become redundant as LLMs evolve | LLC **is not an external framework** — it's a methodology encoded in **tool-agnostic Markdown skills**. If a model gains native planning capability, the skills evolve to leverage it. LLC doesn't compete with the LLM — it **orchestrates** it |

The result: LLC keeps SDD's benefits (traceability, formal specifications, quality gates) without falling into the waterfall, documentation fatigue, or obsolescence traps. **Specification yes, bureaucracy no.**

### What is PRRS (Prismatic Ranked Recursive Summarization)?

The architectural pattern where the same data source is analyzed from **multiple simultaneous angles** (prisms) and then converges into layers of increasing granularity. In LLC: Step 1's 7 specs are 7 prisms over the ingestion docs; Step 2's 2 PRDs are 2 prisms over the specs (executive vs technical); Step 3's N PRPs are N prisms over the technical PRD.

### What is ACE (Agentic Context Engineering)?

LLC's cross-session continuity protocol. Combines Markdown (human readability), XML tags (machine parseability), and YAML front matter (metadata). Each session produces an append-only file in `.ace/sessions/` that is never rewritten. At the end, a 4-field `<context_seed>` compresses session state into ~300 tokens. The next session loads only this seed, not the full history.

### What are Human Gates?

Mandatory human validation points in the LLC pipeline. No step advances without explicit user approval. LLC has 15 human gates + 1 visual checkpoint (prototyping subflow) + QA checkpoints during execution. A rejected gate returns the flow to the previous step with `<gate_result decision="rejected">` logged in ACE.

### What is Grill Me?

The mandatory questioning protocol the AI runs in Steps 0.5, 1, 2, and 3 BEFORE generating any artifact. The AI analyzes input documents, identifies ambiguities, and presents up to 8 questions ranked by criticality (🔴 blocking, 🟡 high, 🟢 medium). The user answers selectively and the AI then generates artifacts based on those answers. Eliminates the main vibe coding failure point: unvalidated assumptions.

> **Note:** The **greenfield** flow (Step 0-GF, for projects without documentation) uses a different
> protocol: structured interview of up to **15 questions** across 4 dimensions. Grill Me (up to 8
> questions) is for resolving ambiguities in existing documents — not for generating from scratch.

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

No. Humans define direction, negotiate scope, oversee design, and approve releases. Agents improve the return on human attention — they don't replace it. LLC formalizes this with **human-in-the-loop** at every critical phase: 15 human gates, 1 visual checkpoint, and QA checkpoints during execution. No step advances without explicit approval.

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
| **4. Execution & Delivery** | 14 + Subflow | Non-UI PRPs (direct agents), UI PRPs (subflow F1-F6), code health, QA gates, deploy |

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
Ingestion documents
    ↓ Step 0.5: decomposed into modules (MOD-*)
Modules (~100 lines each) + Technical PRD + Specs
    ↓ Step 3: decomposed into PRPs (PRP-*)
PRPs (~50-80 lines each)
    ↓ Step 6: decomposed into tasks (TASK-*)
Tasks (checkboxes in TASKS.md)
```

Each level preserves the full context needed for its execution, eliminating the need to consult the original PRD during implementation.

### Does LLC support multi-person teams?

Yes. While each session is operated by a single human, LLC scales to teams because **each gate is a natural sync point:**

| Aspect | Multi-person model |
|--------|-------------------|
| **Sequential steps (0-10)** | One operator drives; team reviews at gates. E.g.: Tech Lead runs Steps 0.5-3, team reviews Gates 1-4 |
| **Parallel PRPs (Step 11)** | Each PRP is self-contained — different devs execute PRPs in isolated worktrees simultaneously |
| **Specialty division** | Architect (Step 5), UX (Step 7), QA (Steps 9, 11-Security). Each specialist operates their step, presents the gate to the team |
| **Gate decisions** | Recorded with `<gate_result reviewer="name">`. Any authorized member can approve. Conflicts: Tech Lead decides |
| **Parallel gates** | Independent PRPs in parallel worktrees — gates of different PRPs approved simultaneously by different reviewers |

`PLAN.md` defines PRP owners. `TASKS.md` assigns agents. `<gate_result>` records who approved. Git tracks authorship.

### Can gates be automated in CI/CD?

Yes, with the `--auto-approve` flag on `llc.py`:

```bash
python .ace/scripts/llc.py pipeline --from 0 --auto-approve
```

**Default behavior (no flag):** `gate_check()` waits **indefinitely** for human decision. There is no timeout that auto-approves — that would violate the "human in control" principle.

**With `--auto-approve`:** All gates are approved automatically. Use only in CI/CD pipelines where code has already passed prior human review (e.g., PR review). The gate is still recorded in ACE with `<gate_result decision="approved" reviewer="auto-approve">`.

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

- **15 human gates:** one after each generation step and auxiliary step (0.5, 1–10, 10.5, 11-SEC, 11-OWASP, 12-NULL). The human reviews the artifact and decides: `approved`, `rejected`, or `conditional`
- **1 visual checkpoint:** in the prototyping subflow (F4 → F5). The hi-fi prototype doesn't become code without explicit visual approval
- **QA checkpoints:** during execution (Step 11): score ≥ 7.0, coverage ≥ thresholds, security audit passed

Each gate decision is recorded in ACE via `<gate_result step="N" decision="approved|rejected|conditional" reviewer="...">`. A rejected gate returns the flow to the previous step and logs a `<blocker>`.

### How to ensure AI-generated code quality?

LLC implements 6 quality assurance layers:

| Layer | LLC Mechanism |
|-------|---------------|
| **1. Specification before code** | Steps 0-GF through 3 generate detailed specs, PRDs, and PRPs with Grill Me — the AI doesn't write a single line of code before requirements are validated |
| **2. Specialized agents per phase** | Each stage has an agent with restricted context: the architect doesn't implement, the developer doesn't define requirements |
| **3. Quality gates at every transition** | 15 human gates + 1 visual checkpoint + QA gates — no artifact advances without validation |
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

### How to prevent AI agents from creating duplicate code?

The root cause of duplication is the agent not knowing what already exists in the repository — so-called "contextual blindness." LLC implements 4 defense layers:

| Strategy | LLC Mechanism | How it prevents duplication |
|----------|-------------|---------------------------|
| **1. Codebase map** | `CLAUDE.md` + `AGENTS.md` document where components, utilities, and patterns live. `dependency-graph.yaml` + `dependency-graph.mmd` map the full artifact topology | The AI consults the map before creating. It knows `src/components/ui/Button.tsx` exists and should be reused, not recreated |
| **2. Pre-execution impact analysis** | `impact-analyzer.py` cross-references `git diff` with the dependency graph. The agent runs it BEFORE implementing | The AI sees exactly which existing files are affected by the change. It won't create `UserService2.ts` if `UserService.ts` already exists |
| **3. Planning before code** | Grill Me (Steps 0.5-3) forces the AI to ask questions before generating. AGENTS.md requires "DOING/EXPECT/IF YES/IF NO" before every action | The AI announces what it will create BEFORE creating it. The human intercepts duplications in the plan, not in the code |
| **4. Metric-forced refactoring** | `code-health.py` monitors Copy/Paste vs Moved Code. If copy > moved, it fires an alert and suggests a cross-PRP refactoring wave | Duplications that escaped layers 1-3 are detected and corrected in scheduled refactoring waves |

**LLC practical rule:** before creating any new file, the agent must check whether the functionality already exists in an existing PRP, a shared module, or a utility documented in `CLAUDE.md`. `impact-analyzer.py --files "planned/path" --json` should be run as a pre-implementation check.

### How does LLC implement the "learning loop"?

The learning loop is the mechanism that transforms development experience into persistent knowledge, preventing repeated mistakes and lost decisions between sessions. LLC implements all 4 layers of the learning ecosystem:

| Learning document | LLC equivalent | Frequency | Function |
|-------------------|---------------|-----------|----------|
| **Technical decisions log** | `ARCHITECTURE.md` (ADRs) + ACE `<learning_point>` → `memory/learning_points.md` | Per stage / per discovery | Record the "why" behind decisions and promote validated learnings to cross-session memory |
| **Living spec (spec.md)** | `docs/business/specs/` + `docs/prd/` + `docs/prps/` | Per requirement change | Single source of truth about system behavior. Git-versioned artifacts, updated by the pipeline when requirements change |
| **Progress file** | ACE `<context_seed>` (4 fields) + `.ace/sessions/YYYY-MM-DD-NNN.md` | Per session | Continuity between sessions. `<context_seed>` compresses state into ~300 tokens. `finalize_session.py` updates TASKS.md automatically |
| **Project constitution** | `CLAUDE.md` + `AGENTS.md` | Per wave / when rules change | Internalize long-term patterns and lessons learned. Generated by Step 10 and updated when architecture evolves |

**The full cycle in LLC:**

```
Session N
  ↓ implements, discovers, decides
  ↓ appends <action>, <thinking>, <learning_point>
  ↓ finalize_session.py:
  ↓   → promotes <learning_point priority="high"> → memory/learning_points.md
  ↓   → generates <context_seed> with state/pending/blockers/next_action
  ↓   → updates TASKS.md (checkboxes [x])
  ↓
Session N+1
  ↓ initialize_session.py loads context_seed (~300 tokens)
  ↓ agent knows exactly: what was done, what's missing, blockers, next step
  ↓ doesn't repeat previous session's mistakes
```

### What is the "70% problem" and how does LLC help combat it?

The "70% problem" (coined by Addy Osmani, Google Chrome DX) describes a pattern in AI-assisted development: AI generates ~70% of the code in minutes — boilerplate, CRUD, known patterns — but the remaining 30% (architecture, security, edge cases, integration, error handling) requires disproportionate effort, often more than doing it all manually from scratch.

**Root causes:**

- AI optimizes for the happy path and systematically ignores edge cases
- Lack of structural grounding: AI doesn't "see" the entire project, hallucinates APIs
- No real feedback loop: error → AI guesses solution → new error → context degradation
- LLM context window gets polluted with failed attempts (lost in the middle)

**How LLC mitigates each cause:**

| Cause | LLC Mechanism |
|-------|---------------|
| AI doesn't see the full project | Code graph tools (see complementary tools section below) provide dependencies, real signatures, and impact analysis |
| Lack of structural grounding | `context_seed` compresses essential state between sessions; AGENTS.md enforces reality checks |
| No real feedback loop | Mandatory TDD: RED (understood?) → GREEN (works?) → REFACTOR (didn't break anything?) |
| Context degradation | ACE append-only: each action is atomic and verifiable; `context_seed` maintains ~300 tokens of continuity |
| Edge cases ignored | TDD + Grill Me + spec-driven generation |
| AI doesn't learn from mistakes | `<learning_point>` records lessons; `<skill_feedback>` captures structural skill improvements |
| Invisible tech debt | 15 human gates + QA checkpoints: every artifact undergoes explicit validation before proceeding |

LLC doesn't try to make AI reach 100% on its own. It combines AI + human + structural tools (graphs, tests, gates, persistent memory) so the ensemble delivers 100% value — AI covering what it does well, and the human deciding on the critical 30%.

### What is "human-in-the-loop"?

The principle that humans remain in control of all critical development decisions. AI agents operate within human-defined guardrails — they never replace humans. In LLC:

| Where the human decides | Mechanism |
|------------------------|-----------|
| **Define objectives** | Human describes the system (ingestion) or answers the greenfield interview |
| **Negotiate scope** | Grill Me: AI asks, human answers. Unvalidated assumptions are blocked |
| **Oversee design** | VISUAL CHECKPOINT in subflow F4 → F5: prototype doesn't become code without approval |
| **Approve releases** | 15 human gates + QA checkpoints: every artifact and every wave undergoes explicit validation |
| **Record decisions** | `<gate_result>` in ACE closes the accountability loop |

Agents improve the return on human attention — they don't replace it. An engineer who used to spend 4 hours writing specs now spends 30 minutes reviewing and approving AI-generated specs.

### How does LLC implement OWASP Top 10 security hardening?

LLC dedicates **Step 11-OWASP** (`docs/skills/llc-step-11-owasp-security.md`) exclusively to OWASP Top 10:2021 hardening. Unlike Step 11-Security — which runs automated tools (SCA, SAST, secrets scanning) **before** implementation — Step 11-OWASP performs manual/AI checks **after** code is written, inspecting controls that tools can't detect.

**The 10 verified categories:**

| Category | What is verified |
|----------|-----------------|
| A01 — Broken Access Control | Auth middleware on all routes, RBAC/ABAC per `perfis_permissoes.md`, ownership check (user can't access other users' resources) |
| A02 — Cryptographic Failures | Passwords with bcrypt/argon2 (never MD5/SHA1), TLS 1.2+, JWT with secure algorithm (RS256/ES256), secrets never hardcoded |
| A03 — Injection | Parameterized SQL (never string concatenation), shell injection, input validation (Zod/Pydantic), XSS (`dangerouslySetInnerHTML`) |
| A04 — Insecure Design | Rate limiting on sensitive endpoints, account lockout, secure reset tokens (expiry + single-use), documented risk analysis |
| A05 — Security Misconfiguration | HTTP security headers (CSP, HSTS, X-Frame-Options), debug mode disabled in production, stack traces not exposed |
| A06 — Vulnerable Components | Dependencies without publicly-exploitable CVEs, frameworks not EOL, updated container base images |
| A07 — Auth Failures | MFA for critical profiles, session expiry, no user enumeration, no default credentials |
| A08 — Integrity Failures | Versioned lockfiles (`package-lock.json`), CI/CD verifies artifact integrity, no `eval`/`unserialize` with user input |
| A09 — Logging Failures | Audit logs per `perfis_permissoes.md` Sec.7.1, sensitive data never in logs, immutable logs |
| A10 — SSRF | Server-side request URLs not controlled by user input, domain allowlists, internal network blocking |

**Classification and gate:**

| Severity | Meaning | Action |
|----------|---------|--------|
| 🔴 Critical | E.g.: SQL concatenated with user input, admin route without authentication | **Blocks release** — mandatory hotfix |
| 🟡 High | E.g.: `dangerouslySetInnerHTML` without sanitization, JWT with `alg: none` | **Generates ticket** — fix next sprint |
| 🟢 Medium | E.g.: Missing CSP header, no account lockout | **Improvement backlog** — prioritized by PM |
| ⚪ N/A | No code to inspect (specification phase) | **Passed** — re-execute after implementation |

**Difference from Step 11-Security (pre-implementation):** Step 11-Security finds vulnerabilities in dependencies (SCA), insecure code patterns (SAST), and exposed secrets — all automated. Step 11-OWASP complements with checks that require reasoning: "does this endpoint verify that the logged-in user owns the resource?" or "does this password reset token expire and is it single-use?" Tools can't answer these questions — OWASP hardening can.

**Report:** `docs/security/OWASP_HARDENING_REPORT.md` (generated by the skill, versioned in the repo).

**Real example — Pipeline script audit (2026-06-13):** OWASP hardening was executed against the LLC pipeline's own Python scripts (`.ace/scripts/*.py`, 9 files, ~85 KB). Results: A02 ✅ 0 hardcoded secrets; A03 ✅ 28 `subprocess.run()` calls with lists, zero `shell=True` or `eval()`; A08 ✅ `yaml.safe_load()` only; A09 ✅ structured logging with zero sensitive data; A10 ✅ zero network requests. Gate: PASSED (0 critical).

### How does the LLC security audit pipeline work?

LLC has **3 security skills** that operate at different points in the pipeline, forming a layered defense:

| Skill | Step | When it runs | What it checks | Gate |
|-------|------|-------------|----------------|------|
| `llc-step-11-security` | Step 11 | **Pre-implementation** (before coding) | SCA (dependencies), SAST (Semgrep), Secrets (Gitleaks) | Blocks on CVSS >= 9.0 or real secret |
| `llc-step-12-null-safety` | Step 12 | **Pre-implementation** (before coding) | Nullability in PRPs: fields without `?`/`Optional`, missing fallbacks, cross-PRP inconsistencies | Blocks on unspecified nullability |
| `llc-step-11-owasp-security` | Step 11-OWASP | **Post-implementation** (after coding) | OWASP Top 10 hardening: access control, crypto, injection, design, misconfig, auth, logging, SSRF | Blocks on 1+ critical finding |

**Complete security flow:**

```
Step 11-Security (pre-code)       Step 12-Null-Safety (pre-code)
        │                                    │
        ▼                                    ▼
   SCA + SAST + Secrets            Nullability in PRPs
        │                                    │
        ▼                                    ▼
   PASSED ──────────────────────────── PASSED
        │                                    │
        └──────────────┬─────────────────────┘
                       ▼
              PRP Implementation
                       │
                       ▼
          Step 11-OWASP (post-code)
                       │
                       ▼
              OWASP Top 10 Hardening
                       │
                       ▼
          PASSED → Release (via DEPLOYMENT.md + CI/CD)
```

**Why 3 separate skills?**

1. **Automated tools first (Step 11-Security):** Before writing a single line of code, the pipeline checks whether dependencies have CVEs, whether secrets are exposed, and whether existing code has insecure patterns. This prevents the team from building on a vulnerable foundation.

2. **Secure design before coding (Step 12-Null-Safety):** Fields without nullability specification are the primary cause of `NullPointerException` and `Cannot read properties of null` in production. Step 12 validates that every field in PRPs explicitly declares whether it can be null and, if so, what the fallback is. This prevents the most common class of production bugs before they're written.

3. **Manual/AI reasoning after code (Step 11-OWASP):** Automated tools cannot answer questions like "does this endpoint verify that the logged-in user owns the resource?" or "is this password reset single-use?" Step 11-OWASP inspects the implemented code against all 10 OWASP categories, requiring file:line evidence for each check.

**Generated reports:** `docs/security/SECURITY_AUDIT_REPORT.md`, `docs/security/NULL_SAFETY_REPORT.md`, `docs/security/OWASP_HARDENING_REPORT.md`.

**Tasks:** `docs/planning/TASKS.md` §4 (SEC-001, SEC-002, SEC-003, SEC-004).

**Real example — Full execution on SGI project (June 2026):** All 3 skills were executed against the LLC repository. Step 11-Security: Semgrep 340 rules on 147 files → 0 findings; SCA N/A (no dependencies); Gitleaks unavailable → manual check clean. Gate: PASSED. Step 12-Null-Safety: 0 PRPs found (specification phase) → `PRP_TEMPLATE.md` validation showed good practices (`?` for optionals, documented fallbacks). Gate: PASSED. Step 11-OWASP: manual audit of 9 `.py` scripts (~85 KB) → A02 0 secrets, A03 28 safe `subprocess.run()`, A08 `yaml.safe_load()`, A09 clean logs, A10 0 network. Gate: PASSED. Pipeline cleared for PRP implementation.

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
| **Excalidraw MCP** | Lo-fi wireframes in prototyping subflow (F3) | <https://github.com/excalidraw/excalidraw-mcp> |
| **Pencil MCP** | Hi-fi prototypes in prototyping subflow (F4) | <https://docs.pencil.dev> |
| **Pandoc** | Conversion fallback if Docling unavailable | `choco install pandoc` / `brew install pandoc` |
| **MSW** | Mock Service Worker for mock data layer (Step 8) | `npm install msw --save-dev` |

### What tools complement the LLC workflow?

Beyond the base stack, external tools can enhance the LLC pipeline by addressing specific friction points. None are mandatory — LLC works without them — but each solves a concrete bottleneck in AI-assisted development.

**Complementary tools (all optional):**

| Category | Tool | What it solves | Classification |
|----------|------|---------------|:---:|
| **Code graph** | Depwire, Graphify, Aider (tree-sitter) | Real dependency analysis, function signatures (not hallucinated), change impact — AI stops "guessing" the project structure | Optional |
| **Git bisect** | `git-bisect.py` (native ACE script) | Automates `git bisect run` — finds exact commit that introduced a regression and reports the diff | Optional |
| **Structural map** | `code-map.py` (native ACE script) | Codebase structural index (file tree, signatures, imports) for agent grounding without hallucinated APIs | Optional |
| **Worktrees** | `--worktree` in `initialize_session.py` (native) | Workspace isolation per PRP/session via git worktree — parallel branches without polluting the main workspace | Optional |
| **Context compression** | Caveman, Headroom | 60-95% token savings; reduces "lost in the middle" by keeping more useful context in the LLM window | Optional |
| **Semantic memory** | agentmemory, MemPalace | Cross-session semantic search — complements ACE with similarity-based retrieval instead of exact match | Optional |
| **Grill Me** | Native LLC skill (Steps 0.5-3) | Mandatory Q&A protocol before generating artifacts — exposes gaps and unvalidated assumptions | ✅ **Required** (LLC core) |
| **TDD + AGENTS.md** | Native LLC protocol | Autonomy zones, RED/GREEN/REFACTOR, handoff — forces verification before proceeding | ✅ **Required** (LLC core) |
| **ACE + context_seed** | `.ace/` scripts | Session continuity (~300 tokens), append-only delta, persistent learning memory | ✅ **Required** (LLC core) |

> **Note:** Required tools are already part of LLC. Optional ones are recommendations for teams wanting to go further in mitigating the "70% problem" and improving token efficiency. LLC is external-tool-agnostic — any equivalent alternative works.

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

*June 2026 values. Actual cost depends on Grill Me iteration count and skill re-executions after rejected gates.*

*Blend assumption: input-dominant traffic (≤25% output tokens) at Claude 3.5 Sonnet pricing ($3/M input, $15/M output). Steps 0-10 are output-dominant (document generation) and typically cost 2-5× more — size up accordingly.*

### CodeAgent vs ToolCallingAgent: which paradigm does LLC use?

LLC uses **both** paradigms, in different phases. The choice isn't in the AI client — it's in the **skill design**:

| Paradigm | How it works | Steps per task | Tokens |
|----------|-------------|---------------|--------|
| **ToolCallingAgent** | LLM generates JSON with tool + params. One tool at a time. Waits for result before next | 14 steps | ~29K tokens |
| **CodeAgent** | LLM generates + executes Python block. Chains multiple actions in one step. Can loop and branch | 2 steps | ~5.4K tokens |

**A well-written skill controls the paradigm — regardless of the client:**

- **Skill with pauses and gates** → the AI acts one action at a time, awaiting validation → **ToolCallingAgent-like**
- **Skill with chained instructions** → the AI executes multiple actions in sequence without pausing → **CodeAgent-like**

LLC applies each paradigm where it's most effective:

| Paradigm | Where in LLC | Why |
|----------|-------------|-----|
| **ToolCallingAgent-like** | Steps 0.5 through 10 (spec & planning) | One artifact at a time, human gate between each. Grill Me forces pause for questions. `<gate_result>` forces pause for approval. Low risk — each step is small and validated |
| **CodeAgent-like** | Step 11 (execution) + Subflow F5-F6 | An entire PRP is implemented in one continuous step. The agent creates files, writes tests, fixes bugs, commits — all chained. High throughput — the PRP is self-contained, no external consultation needed |
| **Hybrid** | Subflow F1-F4 (prototyping) | F1-F3 (discovery, tokens, wireframes) are ToolCallingAgent-like with approval between phases. F4 (hi-fi) has mandatory VISUAL CHECKPOINT. F5 (code) is CodeAgent-like |

The architectural advantage: the paradigm isn't tied to the AI client. A well-written Markdown skill produces the desired behavior in **any agent that reads files and executes commands** — Claude Code (native ToolCallingAgent), opencode, Cursor, Codex CLI. LLC doesn't depend on a specific function calling format — it depends on **clear instructions**.

### What is the "scaffold" and how does it guide the AI in LLC?

A scaffold is the initial project structure — the "skeleton" serving as the technical foundation on which the software will be built. Instead of starting from scratch, the project is born with folder conventions, code patterns, pre-configured tools, and working examples that teach the AI **how** to develop in that specific context.

In LLC, the scaffold operates across 3 complementary layers:

| Layer | What it contains | Generated by | How it guides the AI |
|-------|-----------------|-------------|---------------------|
| **Architectural** | Folder structure (monorepo), lint/type-check config, base dependencies | Step 8 (Setup) + `ARCHITECTURE.md` (Step 5) | The AI knows exactly where each file goes. It doesn't invent structures — it replicates the existing one |
| **Visual** | Design tokens (CSS/JSON), base components, interface patterns | `DESIGN_SYSTEM.md` (Step 7) | The AI generates components following the Design System. It doesn't invent colors, spacing, or variants |
| **Behavioral** | `CLAUDE.md` + `AGENTS.md` with domain rules, constraints, TDD | Step 10 | The AI knows it must write tests first, filter by tenant ID, never use `any` — the "house rules" are documented |

**Why it works:** AI learns by example. A well-structured scaffold provides concrete models to replicate — more effective than describing abstract rules in text. If the `src/components/ui/` folder already has a `Button.tsx` with variants, states, and TypeScript props, the AI generates `Input.tsx` following the same pattern — without needing to be instructed.

**In LLC, the scaffold is auto-generated:** the pipeline produces the structure, conventions, and examples as versioned artifacts. The developer doesn't need to create the scaffold manually — it emerges from Steps 5, 7, 8, and 10. This ensures full traceability (PRP-003 → MOD-PLN-002 → Technical PRD → Strategic Vision) and allows multiple agents to work in parallel without context conflicts.

### Does the LLC pipeline do automated pentesting?

No. **Step 11-Security** runs static security auditing (SCA + SAST + secret scanning) with `npm audit` (or `pip-audit`), Semgrep, and Gitleaks. These tools run locally, are open-source, and require no external infrastructure.

For pentesting and DAST (dynamic analysis of running applications), we recommend integrating complementary tools via CI/CD:

| Tool | Type | GitHub |
|------|------|--------|
| **OWASP ZAP** | DAST (dynamic scanning) | [github.com/zaproxy/zaproxy](https://github.com/zaproxy/zaproxy) |
| **Nuclei** | Vulnerability scanner | [github.com/projectdiscovery/nuclei](https://github.com/projectdiscovery/nuclei) |
| **SQLMap** | SQL injection testing | [github.com/sqlmapproject/sqlmap](https://github.com/sqlmapproject/sqlmap) |
| **Nikto** | Web server scanner | [github.com/sullo/nikto](https://github.com/sullo/nikto) |
| **Bandit** | Additional Python SAST | [github.com/PyCQA/bandit](https://github.com/PyCQA/bandit) |
| **Brakeman** | Additional Rails SAST | [github.com/presidentbeef/brakeman](https://github.com/presidentbeef/brakeman) |

These tools can be added to the CI/CD pipeline defined in `docs/DEPLOYMENT.md` (generated in Step 10). LLC is tool-agnostic — any equivalent tool works.

---

## Pipeline Overview

### How many steps does LLC have?

14 main steps + 5 auxiliary (19 total), 21 skills (including 1 composite prototyping subflow). The pipeline goes from business knowledge ingestion to production deployment:

> **Main (14):** Numbered sequential steps — 0, 0.1, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11.
> **Auxiliary (5):** 0-GF (greenfield alternative), 10.5 (user guide), 11-SEC (pre-code audit),
> 12-NULL (data contracts), 11-OWASP (post-code hardening).

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
| 10.5 | User Guide | `llc-user-guide` | Markdown, Playwright (optional) |
| 11-SEC | Security Audit (pre-code) | `llc-step-11-security` | **npm audit** / **pip-audit**, **Semgrep**, **Gitleaks** |
| 12-NULL | Null Safety (pre-code) | `llc-step-12-null-safety` | Data contracts validation |
| 11 | Execution | Subflow F1-F6 | Excalidraw, Pencil, parallel agents |
| 11-OWASP | OWASP Hardening (post-code) | `llc-step-11-owasp-security` | 10 categories manual/AI verification |
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

### Why does Grill Me stop at Step 3?

Grill Me is a **requirements clarification** protocol — it resolves ambiguity about "what to build." It stops at Step 3 because:

- **Steps 0.5-3** deal with business requirements (scope, actors, features). Only the user knows the answers.
- **Steps 4+** deal with **technical decisions** derived from already-validated requirements. The AI should decide based on NFRs and specs, not ask.

Example: "Which stack to use?" (Step 5) — the answer is in the performance, security, and scale NFRs defined in Step 1. The AI analyzes NFRs and proposes; the human validates at Gate 6. Asking the user would be outsourcing a decision the artifacts already answer.

---

## What is PRRS (Prismatic Ranked Recursive Summarization)?

The architectural pattern LLC uses to analyze the same data source from **multiple simultaneous angles** (prisms) and then converge:

- Step 1: 7 specs = 7 prisms over `ingestion/converted/`
- Step 2: 2 PRDs = 2 prisms (executive vs technical) over the 7 specs
- Step 3: N PRPs = N prisms (implementation units) over the technical PRD
- Greenfield: 4 interview dimensions over the system idea
  (PRRS precursor — elicits the data source instead of refracting it)

---

## What is ACE and why do I need it?

**Agentic Context Engineering** is LLC's cross-session continuity protocol. Without it, each AI session starts from scratch (model amnesia).

- **Append-only:** session files are never rewritten — only deltas are appended
- **`<context_seed>`:** at the end of each session, the AI compresses state into 4 fields (~300 tokens)
- **Savings:** ~1,500 tokens/session vs ~22,000 for full history (93% reduction — calculated, not empirical)
- **Technology:** Python (scripts), Markdown + XML tags + YAML front matter

> **Note on metrics:** Token reduction, cost, and time estimates in this FAQ are
> **calculations based on API pricing and typical context sizes**, not empirical results
> from case studies. LLC is at v1.5.0 — benchmarks with real projects are underway.
> Contributions with empirical data are welcome.

### What is the exact context_seed schema?

The `<context_seed>` is a text block with **4 mandatory fields**, separated by newlines. This is the formal schema — the contract every AI client must implement to be compatible with LLC:

```
state: [completed actions, changed files, decisions made]
pending: [incomplete tasks, planned next steps]
blockers: [active blockers — technical, dependencies, questions]
next_action: [recommended next step — specific, actionable]
```

**Format rules:**

| Rule | Detail |
|------|--------|
| Field names | Exact: `state`, `pending`, `blockers`, `next_action` (case-sensitive, English) |
| Separator | `:` (colon + space) after each field name |
| Line break | `\n` between fields |
| Encoding | UTF-8, no Markdown or XML markers in field values |
| Max size | ~300 tokens (approximately 1200 characters) |
| Empty fields | Allowed (e.g., `blockers: none` or `blockers:`) |

**Real example:**

```
state: Step 5 completed. ARCHITECTURE.md generated with NestJS + PostgreSQL stack. ADRs documented for JWT auth and multi-tenancy. C4 Level 2 diagram created.
pending: Awaiting Gate 6 approval. Step 6 (Tasks) is next.
blockers: Uncertain which ORM to use — Prisma vs TypeORM. Awaiting tech lead decision.
next_action: Run llc-step-6.md after Gate 6 approved. If Prisma chosen, use schema.prisma.
```

**Where the schema is documented:** In addition to this section, the full schema is in `AGENTS_TEMPLATE.en.md` §Handoff Protocol and in the `initialize_session.py` / `finalize_session.py` scripts.

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

### Does LLC work for non-JavaScript/TypeScript stacks?

Yes. LLC is **tool-agnostic by design** — skills are Markdown files, ACE scripts are Python, gates are human processes. No pipeline component depends on Node.js or npm.

**Where JS/TS appears (and equivalents for other stacks):**

| LLC Component | JS/TS Example | Python Equivalent | Go Equivalent | Rust Equivalent |
|--------------|--------------|-------------------|---------------|-----------------|
| Mock data layer (Step 8) | MSW + `mocks/handlers/*.ts` | `responses` + `mocks/handlers/*.py` | `httptest` + `mocks/handlers/*.go` | `mockall` + `mocks/handlers/*.rs` |
| Dependency audit (Step 11) | `npm audit` | `pip-audit` | `govulncheck` | `cargo audit` |
| Screenshots (User Guide) | Playwright | Playwright (works with Python) | Chromedp | Chromedp |
| Steering files | `CLAUDE.md` / `AGENTS.md` | Same — pure Markdown | Same | Same |

**The docs use JS/TS as examples because it's the most common stack**, but all concepts are translatable. The only real dependency is Python 3.10+ (for ACE scripts). Everything else is Markdown, Git, and processes.

### Why does the reference implementation use Python?

The LLC **methodology** (Markdown skills, gates, versioned artifacts) is tool-agnostic — works with any terminal AI client. The **reference implementation** (ACE scripts, Thin Harness, code-health, impact-analyzer) uses Python 3.10+ because:

- Python is the most widely available language in development environments (pre-installed on Linux/macOS, easy on Windows)
- ACE scripts need `subprocess`, `json`, `pathlib`, `hashlib` — all in stdlib
- The only external dependency is `click` (CLI framework, `pip install click`)

Alternative implementations in other languages (Node.js, Go, Rust) are welcome — as long as they follow the same contracts (4-field context_seed, gates.json, atomic cache writes). LLC is an open specification, not a Python product.

---

## What does each Python script do?

| Script | When it runs | Function |
|--------|-------------|----------|
| `initialize_session.py` | Start of every session | Creates session file, loads `context_seed` |
| `finalize_session.py` | End of every session | Generates `context_seed`, promotes learnings, updates TASKS.md |
| `promote-learning-points.py` | Auto in finalize | Promotes learnings to `memory/` |
| `validate-tags.py` | Pre-commit hook / standalone | Validates XML tags, context_seed schema, index.json + **session coverage** (`--coverage`: a commit with code requires a recorded ACE session) |
| `impact-analyzer.py` | Before refactoring | Propagates impact via dependency graph |
| `code-health.py` | Each wave / QA checkpoint | Monitors Moved Code, Copy/Paste, Legacy Touch |
| `pre-commit.sh` | Git pre-commit | Orchestrates session coverage + ACE validation + impact analysis |

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

### What exactly happens when a gate is rejected?

The gate rejection process follows 4 stages:

**1. Decision recording:** `<gate_result decision="rejected" reviewer="...">` is appended to the session's ACE file. The rejection reason is logged as `<blocker resolved="...">` for traceability.

**2. Downstream artifact rollback:** `impact-analyzer.py` detects which artifacts depend on the rejected one and flags them as potentially stale. Example: rejecting Gate 2 (7 specs) → `impact-analyzer.py` reports that PRDs, PRPs, planning, architecture, and design system need review.

```bash
python .ace/scripts/impact-analyzer.py --files "docs/business/specs/glossario.md" --json --skills
```

**3. Correction and re-execution:** The user fixes the artifact and re-runs the step. Skills are idempotent — they overwrite the previous artifact. The new ACE session receives a `<context_seed>` with `pending: gate N rejected — re-executing step N`.

**4. Worktree (if applicable):** If the step used a git worktree, the harness automatically discards the worktree on `session_end` (no merge). The next execution creates a fresh worktree.

**What does NOT happen:** The ACE history of the rejected session is **never deleted** — it's append-only. The failure history is preserved for audit.

---

## What's the difference between dependency-graph.yaml and dependency-graph.mmd?

| File | Function | Read by | Maintained by |
|------|----------|---------|---------------|
| `dependency-graph.yaml` | Actual structure — used by `impact-analyzer.py` | Python scripts | **Source of truth** — manually maintained as methodology artifact |
| `dependency-graph.mmd` | Topological Mermaid visualization — visual understanding | Humans and LLMs | **Derived from .yaml** — generated from the YAML, not independently maintained |

> **Rule:** The `.yaml` is the source of truth. The `.mmd` should be regenerated from the `.yaml`
> whenever the dependency graph is updated. Do not edit `.mmd` manually —
> edit the `.yaml` and update `.mmd` as a derivative. This prevents desynchronization.

---

## Next steps after the pipeline?

1. Mocked MVP running → validate with stakeholders
2. MVP CHECKPOINT approved → implement real integrations
3. Integrations working → deploy to staging
4. Acceptance tests passing → deploy to production
5. Monitor code health and iterate

---

## 📖 User Guide

### What is the user guide in LLC?

It's documentation aimed at the **end user** of the application, automatically generated by the LLC pipeline. Unlike README and DEPLOYMENT (which are for developers), the user guide teaches **how to use** the system: how to navigate, register, generate reports, etc.

The guide consists of:

- **Skeleton** (`docs/user-guide/USER_GUIDE.md`): generated by the `llc-user-guide` skill (Step 10.5), containing page index, per-profile guide, and conventions.
- **Content pages** (`docs/user-guide/[module]/*.md`): generated by PRPs during execution (Step 11). Each PRP declares which manual pages it produces in the `user_docs` section.

### Why is the user guide important in agentic development?

AI agents produce code, but end users need to understand how to use the system. The user guide closes the loop: the same AI that implements a feature also documents how to use it. This ensures documentation is always in sync with code — if code changes, re-running the PRP updates the manual.

### The guide was generated without screenshots. How do I add real screens?

LLC generates the guide with screenshots if Playwright is installed in the environment. Otherwise, it uses Mermaid diagrams as a fallback. To add real screenshots:

1. Install Playwright: `npm install -D @playwright/test && npx playwright install`
2. Start the application development server
3. Navigate to `docs/user-guide/[module]/img/`
4. Replace diagrams with real screenshots, or re-run the PRP capture script

### Can I use Puppeteer or Selenium instead of Playwright?

Yes. LLC's screenshot script automatically detects `playwright`, `puppeteer`, or `selenium-webdriver` in `package.json`. Any of the three works. Install your preferred one and re-run the PRP.

### How do I keep the guide up to date after changes?

Each executed PRP regenerates the manual pages declared in `user_docs`. If an existing feature changed (e.g., new field in a form), re-run the corresponding PRP. The impact analyzer (`llc-impact-analyzer`) reports which manual pages are affected by each code change.

### Do I need a separate website for the guide?

No. The Markdown files in `docs/user-guide/` render natively on GitHub, GitLab, and any Markdown previewer. If you want a site with search and theming, tools like MkDocs or VitePress can convert the `.md` files into a static site with a single command (`mkdocs build`), without changing the content.

---

## 📖 Token Compression

### Does LLC use any token compression strategy?

Yes, across **5 complementary layers**. The goal is to maximize the amount of useful information that fits in the LLM context window, keeping the AI always in the peak quality zone (0-30% fill):

| Layer | Mechanism | Reduction |
|-------|-----------|:---------:|
| **1. ACE `<context_seed>`** | Compresses session state into 4 fields (~300 tokens) instead of reloading full history (~22,000 tokens) | **93%** |
| **2. Self-contained PRPs** | Each implementation agent receives only the PRP (~50-80 lines), not the entire project (~25+ artifacts, ~5000+ lines) | **95%+** |
| **3. Compressed Index in AGENTS.md** | `|`-delimited format: 16 artifacts in ~400 tokens with routing keywords. The agent decides which files to load on demand (lazy loading) | **23% vs traditional table** |
| **4. Impact Analyzer** | `impact-analyzer.py` tells exactly which artifacts to read before each change — eliminates unnecessary reading | **On demand** |
| **5. Markdown via Docling** | PDF/DOCX/HTML converted to pure Markdown (Step 0.1) — reduces structural noise from heavy tags (XML, HTML) | **60-80% vs binary formats** |

**Design principle:** descriptions are for routing, not full reading. The agent uses the compressed index to decide which files to load — and only loads them when the task actually requires it.

### Is LLC compatible with prompt caching?

Yes. LLC's design maximizes **cache hits** by construction, even without being explicitly designed for it:

| Cache layer | LLC Mechanism | Effect |
|-------------|---------------|--------|
| **1. Static prefix** | `<!-- @include AGENTS.md -->` loads rules, zones, TDD, and protocol at the top of every session. LLC skills have fixed structure (YAML → prereqs → prompt → rules). The prefix is identical across sessions | Guaranteed cache hit on prefix |
| **2. Dynamic isolation** | Dynamic content (user messages, tool outputs, error logs) is appended at the end. The agent receives only the current PRP, not the full history | Cache not invalidated between tasks |
| **3. Short sessions** | PRPs of 2-8 days ensure atomic sessions. ACE `<context_seed>` (~300 tokens) replaces reloading history (~22K tokens) | Fresh cache per session |
| **4. Consistent ordering** | Fixed Document Hierarchy in AGENTS.md, compressed index in stable format, immutable skill structure across runs | Zero cache miss from reordering |
| **5. Lazy loading** | Compressed index + impact analyzer — the agent only loads files on demand, keeping the prompt lean | Fewer tokens = less cache pressure |

**Practical rule:** keep static content (AGENTS.md, tool schemas, project rules) at the top of every prompt. Append dynamic content (messages, tool outputs, errors) at the end. This maximizes prefix cache hits.

---

## 🔀 Git Worktree

### What is Git Worktree and how does LLC use it?

Git Worktree allows creating **multiple working directories** linked to different branches, all sharing the same `.git/` repository. Instead of running `git checkout` and overwriting files in the same directory, each branch gets its own physical directory.

```
/project/              ← branch: main       (main worktree)
/project-prp-001/      ← branch: prp-001/wave-1
/project-prp-002/      ← branch: prp-002/wave-1
```

**How LLC uses it:**

| When | Behavior |
|------|----------|
| **Step 11 (Execution)** | `initialize_session.py` automatically creates a worktree when `--prp` is provided or `step >= 11` |
| **Parallel PRPs** | Each PRP gets its own physical directory — agents never collide on files |
| **Merge/discard** | `finalize_session.py`: gate `approved` → `git merge --no-ff <branch>` into master, then remove the worktree and delete the branch; gate `rejected` → discard without merge (`git worktree remove --force` + `git branch -D`) |
| **Conflicts** | Not auto-resolved. If two PRPs modify the same file, the second merge fails and the operator resolves manually; well-designed PRPs minimize file overlap (see Pipeline Design) |
| **Branch naming** | `prp-{id}/wave-{n}` — consistent, predictable, traceable |

**Benefits for agentic development:**

| Benefit | How it works |
|----------|-------------|
| **Real parallelism** | 3 agents implement 3 PRPs simultaneously, each in its own directory, without cloning the repo |
| **Isolated builds** | `node_modules/`, `dist/`, `.env` independent per worktree — different dependency versions without conflict |
| **No stashing** | No need to hide uncommitted changes to review another branch — just `cd` to another directory |
| **Unified history** | `git log`, `git branch -a`, `git diff` between branches work from any worktree |
| **Auto cleanup** | Orphan worktrees are removed by `cleanup_orphan_worktrees()` at the start of each session |

**To disable isolation:** use `--no-worktree` with `initialize_session.py`. Useful for specification sessions (Steps 0-10) where parallelism is not needed.

---

## 🔧 Thin Harness

### What is the LLC Thin Harness?

The **Thin Harness** is the orchestration layer connecting skills (Markdown), ACE scripts (Python), and the AI client. It's a ~390-line Python CLI that automates the lifecycle of each pipeline step.

**Main commands:**

```bash
llc run --step 5                     # Execute a complete step
llc pipeline --from 0                # Full pipeline (stops at gates)
llc session start --step 5           # Start manual session
llc session end --approve            # End manual session
llc status                           # Pipeline progress
```

**Benefits over manual mode:**

| Dimension | Without harness | With harness |
|-----------|:---------------:|:------------:|
| Manual actions per full pipeline | ~88 | ~15 (gates only) |
| Risk of skipping a step | High (manual) | Zero (orchestrated) |
| Risk of forgetting context_seed | High | Zero (automatic) |
| Consistency between sessions | Manual (copy/paste JSON) | Automatic |
| Learning curve | Must read 3 docs | 1 command |
| Worktree for parallel PRPs | Must remember `--worktree` | Automatic (step >= 11) |
| Worktree merge/discard | Manual | Automatic (by gate) |
| Learning points promoted | Manual (separate script) | Automatic (finalize) |
| New developer onboarding | ~30 min reading guides | `llc pipeline --from 0` |

**The harness does NOT replace ACE scripts** — it invokes them via subprocess. ACE scripts remain independent and manually invocable.

**Why "thin"?** The harness is ~390 lines by design. It does NOT implement tool-calling (client), does NOT define security rules (AGENTS.md), does NOT teach the model (skills). Its 5 responsibilities are strict:

| # | Responsibility | How |
|---|---------------|-----|
| 1 | ACE session | init/finalize, context_seed, worktree |
| 2 | Skill loading | Progressive disclosure — loads the Document Index (~400 tokens), not full AGENTS.md |
| 3 | Agent invocation | CLI client detection, 10min timeout, automatic context_seed extraction |
| 4 | Gate validation | External checklist (`gates.json`) |
| 5 | Pipeline orchestration | Step iteration, gate pauses |

**What the harness does NOT do (and why):**

| Responsibility | Who handles it | Why |
|---------------|---------------|-----|
| Prompt caching | AI client | Client manages prefix caching natively |
| Parallel sub-agents | Git worktrees + client | Worktrees isolate; client launches agents |
| Specific tools | ACE scripts | `impact-analyzer.py`, `code-health.py` are fat code |
| Live repository context | AGENTS.md + CLAUDE.md | Harness loads only the compressed index |

### How do I guarantee sessions are recorded in `.ace`, regardless of which AI client I use?

The `llc run --step N` flow (init → skill → agent → gate → finalize) is already tool-agnostic at
**execution**: the harness detects `claude`/`opencode`/`codex`/`cursor` on the PATH or prints the
prompt for manual mode. The fragile point isn't execution — it's **enforcement**: guaranteeing the
agent goes through the flow instead of coding "directly". Coding outside the cycle leaves
`.ace/index.json` with `sessions: []`: the work happened, but with no history proving incremental
delivery.

Recording only happens through the session lifecycle: `initialize_session.py` appends the entry
(`in_progress`) and `finalize_session.py` completes it (`completed`). Completing tasks or generating
scaffolding **does not** touch the index — `<task_completed>` goes to `TASKS.md`, not to `index.json`.

The guarantee is layered (defense in depth):

| Layer | Mechanism | Tool-agnostic? |
|-------|-----------|:---:|
| **Contract** | `AGENTS.md`/`CLAUDE.md` state "all work becomes a session" | ✅ (advisory) |
| **Procedure** | the step's skill, auto-loaded by `llc run` | ✅ (advisory) |
| **Guarantee** | `pre-commit.sh` + `validate-tags.py --coverage`: a commit with code but no session is **rejected** by git | ✅ (deterministic) |
| **Per-client UX** | a client hook (e.g. Claude Code `PreToolUse`) blocks edits with no open session | ❌ (per-client) |

The layer that actually guarantees it is the **git pre-commit hook** — git runs it no matter which
agent made the commit. Install it: `cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit` (or
`pre-commit install`). Per-client hook snippets in `docs/templates/hooks/`.

> **Can it be bypassed?** Yes — `git commit --no-verify` (pre-commit) or disabling the client hook.
> No mechanism is 100%; layered, they shift the failure mode from "the agent forgot" to "someone had
> to actively bypass it". See
> [`llc-pipeline-design.en.md` §8.7](llc-pipeline-design.en.md#87-guaranteed-session-registration-enforcement).

---

## ⚡ Early Commitment + Deterministic Replay

### Does LLC use Early Commitment and Deterministic Replay?

Yes. Starting from version 1.5.0, the Thin Harness includes two modules that reduce repetitive task costs by up to 99%:

**Early Commitment:** Before execution, `llc_classify.py` classifies the task into 4 types (crud_endpoint, ui_component, validation_rule, test_write). This collapses the agent's search space and eliminates dead-end paths.

**Deterministic Replay:** After the first human-gate-approved execution, the execution path (tool calls, generated code, commands) is recorded in `.ace/cache/{type}.json`. Future tasks of the same classification replay the script deterministically, with near-zero token cost.

| Metric | Target |
|--------|:------:|
| Hit rate (tasks with replay) | >60% |
| Success rate (replays without rollback) | >90% |
| Token reduction per repeated task | ~99% |
| Rollback on partial failure | Instant `git checkout` |

**View metrics:** `python .ace/scripts/replay_stats.py`
