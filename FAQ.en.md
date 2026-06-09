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
