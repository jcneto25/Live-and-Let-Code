# Execution Guide — Live and Let Code (LLC)

**Version:** 1.0.0  
**Audience:** Developers, Product Owners, Tech Leads  
**Prerequisite:** Read [`llc-pipeline-design.md`](llc-pipeline-design.md) (methodology overview)

> 🚧 **This guide is being translated from Portuguese.**  
> For the complete guide, see [`LLC_GUIDE.md`](LLC_GUIDE.md) (PT-BR).
>
> Para o guia completo, veja [`LLC_GUIDE.md`](LLC_GUIDE.md).

---

## Quick Start

### What you need

- A terminal AI client (Claude Code, opencode, Codex, Cursor CLI, etc.)
- Git installed and configured
- A software project to be developed
- Business domain documents (manuals, meeting minutes, regulations, transcripts, operational guides)

### Initial Setup

```bash
git clone https://github.com/jcneto25/Live-and-Let-Code.git your-project
cd your-project
```

### LLM Operation Mode

| Stages | Recommended Mode | Reason |
|--------|-----------------|--------|
| **Steps 0–10** (spec & planning) | **Thinking / Reasoning** | Multi-step analysis, cross-artifact consistency |
| **Post-validation fixes** | **Thinking / Reasoning** | Full context understanding required |
| **Step 11 — Execution** (dev & tests) | **Regular / Default** | Faster iteration, code validated by automated tests |
| **Subflow F1–F4** (prototyping) | **Thinking / Reasoning** | Design judgment, Design System consistency |
| **Subflow F5–F6** (code & validation) | **Regular / Default** | Follows approved specs |

### Pipeline in 1 Minute

```
Step 0:     Load docs → docs/business/ingestion/
Step 0.5:   AI → Vision + Module Specs  👤 Gate 1
Step 1:     AI → 7 Specs                👤 Gate 2
Step 2:     AI → PRDs                   👤 Gate 3
Step 3:     AI → PRPs                   👤 Gate 4
Step 4:     AI → Planning               👤 Gate 5
Step 5:     AI → Architecture           👤 Gate 6
Step 6:     AI → Tasks                  👤 Gate 7
Step 7:     AI → Design System          👤 Gate 8
Step 8:     AI → Setup + Mock Data      👤 Gate 9
Step 9:     AI → Testing Docs           👤 Gate 10
Step 10:    AI → README + DEPLOYMENT    👤 Gate 11
Step 11:    Execution (with prototyping subflow for UI modules)
```

### Running a Step

```
Execute the skill docs/skills/llc-step-0-5.md
```

**Golden rule:** No step advances without the previous gate approved.

---

Full step-by-step instructions in [`LLC_GUIDE.md`](LLC_GUIDE.md) (PT-BR). English version coming soon.
