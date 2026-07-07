![Live and Let Code](LLC.png)

# Live and Let Code (LLC)

**Agentic Autonomous Development Methodology** | **Metodologia de Desenvolvimento Agentico Autônomo**

---

### 🇧🇷 Português

Live and Let Code (LLC) é uma metodologia open-source que estrutura o ciclo completo de construção de software — da ingestão de conhecimento de negócio ao deploy em produção — em **14 etapas principais + 5 auxiliares + 2 de análise de mudança (Δ)** com **gates de validação humana** em cada fase. **23 skills tool-agnostic** executáveis por qualquer cliente de IA terminal.

📘 **[Guia de Execução (PT-BR)](LLC_GUIDE.md)** — passo a passo completo  
📄 **[Especificação do Pipeline](llc-pipeline-design.md)** — design document

---

### 🇺🇸 English

Live and Let Code (LLC) is an open-source methodology that structures the complete software development lifecycle — from business knowledge ingestion to production deployment — into **14 main + 5 auxiliary + 2 change analysis (Δ) steps** with **human validation gates** at every phase. **23 tool-agnostic skills** executable by any terminal AI client.

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

### Pipeline

```
Greenfield:
Ingestion → Conversion (Docling) ─👤─→ Vision + Modules ─👤─→ 7 Specs ─👤─→ PRDs ─👤─→ PRPs
─👤─→ Planning ─👤─→ Architecture ─👤─→ Tasks ─👤─→ Design System ─👤─→ Setup + Mock
─👤─→ Testing ─👤─→ Project Docs ─👤─→ User Guide ─👤─→ Security Gates ─👤─→ Execution

Change (Delta):
New Documents ─👤─→ Δ.0 Impact Analysis ─👤─→ Δ.1 Grill Me ─👤─→ Smart Skip Pipeline
(cada step condicional decide: executar diff ou skip com reaproveitamento)
```

> 🔒 **Security gates** wrap every execution wave — SCA/SAST/secrets audit (pre-code), OWASP hardening + null-safety (post-code), **Test Coverage Gate (10.8)**. See the [Execution Guide](LLC_GUIDE.en.md).
>
> 🔒 **Gates de segurança** envolvem cada onda de execução — auditoria SCA/SAST/secrets (pré-código), hardening OWASP + null-safety (pós-código), **Test Coverage Gate (10.8)**. Veja o [Guia de Execução](LLC_GUIDE.md).
>
> 🔄 **Fluxo Delta:** Para mudanças em sistemas existentes, o LLC oferece 2 steps de análise de impacto (Δ.0 + Δ.1) + Smart Skip que pula steps inalterados. Consulte o [FAQ](FAQ.md#-fluxo-delta-mudanças-em-sistemas-existentes).

---

**[GitHub](https://github.com/jcneto25/Live-and-Let-Code)** | **MIT License**
