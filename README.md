![Live and Let Code](LLC.png)

# Live and Let Code (LLC)

**Agentic Autonomous Development Methodology** | **Metodologia de Desenvolvimento Agentico Autônomo**

---

### 🇧🇷 Português

Live and Let Code (LLC) é uma metodologia open-source que estrutura o ciclo completo de construção de software — da ingestão de conhecimento de negócio ao deploy em produção — em **24 etapas pipeline + 2 de análise de mudança (Δ)** com **26 gates de validação humana** em cada fase. **27+ skills tool-agnostic** executáveis por qualquer cliente de IA terminal.

📘 **[Guia de Execução (PT-BR)](LLC_GUIDE.md)** — passo a passo completo  
📄 **[Especificação do Pipeline](llc-pipeline-design.md)** — design document

---

### 🇺🇸 English

Live and Let Code (LLC) is an open-source methodology that structures the complete software development lifecycle — from business knowledge ingestion to production deployment — into **24 pipeline + 2 change analysis (Δ) steps** with **26 human validation gates** at every phase. **27+ tool-agnostic skills** executable by any terminal AI client.

📘 **[Execution Guide (EN-US)](LLC_GUIDE.en.md)** — full step-by-step guide  
📄 **[Pipeline Specification](llc-pipeline-design.en.md)** — design document

---

### Princípios | Principles

| 🇧🇷 | 🇺🇸 |
|-----|-----|
| Documentação como código — todo artefato é versionável | Documentation as code — every artifact is versionable |
| Humano no controle — IA propõe, humano dispõe | Human in control — AI proposes, human decides |
| Tool-agnostic — qualquer cliente de IA terminal. A metodologia (skills, gates, artefatos) é independente de ferramenta; a implementação de referência usa Python 3.10+ | Tool-agnostic — any terminal AI client. The methodology (skills, gates, artifacts) is tool-independent; the reference implementation uses Python 3.10+ |
| Rastreabilidade total — da visão ao commit | Full traceability — from vision to commit |
| Paralelismo por design — PRPs auto-contidos | Parallelism by design — self-contained PRPs |

### 🚀 Quick Start (Thin Harness)

```bash
pip install click
python .ace/scripts/llc.py pipeline --from 0
```

**New: Test Coverage Gate**

```bash
# Verify test coverage before execution (Gate 10-COVERAGE)
python .ace/scripts/llc.py gate run --gate test-coverage

# Run pre-wave check (build + boot + health + coverage)
bash .ace/scripts/pre-wave-check.sh
```

**New: Architecture Fitness Functions (41 checks)**

```bash
# Verify compliance — 41 checks: architecture (6), clean code (16),
# deep clean (8), governance (1), security (5), UX (5)
python .ace/scripts/fitness-functions.py --all

# Strict mode (exit 1 on violations) for CI/CD
python .ace/scripts/fitness-functions.py --all --strict

# Include in code health report
python .ace/scripts/code-health.py --since "30 days ago" --fitness
```

**New: LLM Self-Validation (post-generation)**

```bash
# 8 checks on AI-generated code (5 blocking + 3 warnings)
# Run by the agent before reporting a task as done;
# the ace-llm-validation hook repeats the barrier at commit
bash .ace/scripts/llm-validation.sh
```

**New: ADRs in separate files**

```bash
# Step 5 generates ARCHITECTURE.md + individual ADR files
python .ace/scripts/llc.py run --step 5 --task "Arquitetura do sistema"
# ADRs available at: docs/architecture/adr/ADR-*.md
```

**New in v2.0.0: Wizard TUI (graph source) + Evals reports**

```bash
# Wizard TUI — Kanban fed by the pipeline graph (default source)
python .ace/scripts/llc.py wizard
#   - critical path steps marked 🔺 · next step suggested ➤ in BACKLOG
#   - swimlanes per wave (▾/▸) when EXECUTION_WAVES.md exists
#   - fallback: --source index (read-only PipelineDataReader)
python .ace/scripts/llc.py wizard --source index

# Evals — cost×quality Pareto dashboard + real bottleneck report
python .ace/scripts/llc.py eval --report      # Pareto dashboard (RF-EF5.3)
python .ace/scripts/llc.py eval flow-report   # critical_path × flow-metrics → bottlenecks
```

### Pipeline

```
Greenfield:
Ingestion → Conversion (Docling) ─👤─→ Vision + Modules ─👤─→ 2.5 Casos de Uso ─👤─→ 7 Specs ─👤─→ PRDs ─👤─→ PRPs
─👤─→ Planning ─👤─→ Architecture ─👤─→ Tasks ─👤─→ Design System ─👤─→ Setup + Mock
─👤─→ Testing ─👤─→ Project Docs ─👤─→ User Guide ─👤─→ Security Gates ─👤─→ Execution

Change (Delta):
New Documents ─👤─→ Δ.0 Impact Analysis ─👤─→ Δ.1 Grill Me ─👤─→ Smart Skip Pipeline
(cada step condicional decide: executar diff ou skip com reaproveitamento)
```

> 🔒 **Security in 3 layers:** Secure-by-Design (Step 5d, design-time prevention) → SCA/SAST/secrets audit (10.6, pre-code detection) → OWASP hardening + null-safety (11.1, post-code verification). Plus **Test Coverage Gate (10.8)**. See the [Execution Guide](LLC_GUIDE.en.md).
>
> 🔒 **Segurança em 3 camadas:** Secure-by-Design (Step 5d, prevenção no design) → auditoria SCA/SAST/secrets (10.6, detecção pré-código) → hardening OWASP + null-safety (11.1, verificação pós-código). Mais **Test Coverage Gate (10.8)**. Veja o [Guia de Execução](LLC_GUIDE.md).
>
> 🔄 **Fluxo Delta:** Para mudanças em sistemas existentes, o LLC oferece 2 steps de análise de impacto (Δ.0 + Δ.1) + Smart Skip que pula steps inalterados. Consulte o [FAQ](FAQ.md#-fluxo-delta-mudanças-em-sistemas-existentes).

---

**[GitHub](https://github.com/jcneto25/Live-and-Let-Code)** | **MIT License**
