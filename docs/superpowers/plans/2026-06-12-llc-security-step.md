# LLC Step 11-Security — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dedicated security audit step (Step 11-Security) to the LLC pipeline that runs SCA + SAST + secret scanning as the initial phase of Step 11 (Execution), before any PRP implementation begins.

**Architecture:** Creates 2 new files (skill + template), 1 directory (`.ace/security/`), and modifies 10 existing artifacts to integrate security into the pipeline. The step uses npm audit/pip-audit for dependency scanning, Semgrep for static analysis, and Gitleaks for credential detection — all open-source, zero-infrastructure tools.

**Tech Stack:** YAML frontmatter (skill), Markdown (template, guides, FAQ), Mermaid (pipeline diagram), YAML (dependency graph)

**Design Spec:** `docs/superpowers/specs/2026-06-12-llc-security-step-design.md`

---

### Task 1: Create the Security Skill

**Files:**
- Create: `docs/skills/llc-step-11-security.md`

- [ ] **Step 1: Write the skill file**

Write `docs/skills/llc-step-11-security.md` with the complete skill content:

```markdown
---
name: llc-step-11-security
description: Pipeline LLC — Auditoria de segurança pré-execução (SCA + SAST + secret scanning). Executa npm audit/pip-audit, Semgrep e Gitleaks antes dos agentes iniciarem os PRPs.
version: 1.0.0
tags: [security, audit, sast, sca, secrets, llc-pipeline]
---

# LLC Skill: Step 11-Security — Auditoria de Segurança Pré-Execução

**Pipeline:** Live and Let Code (LLC)
**Fase:** Security Gate (início do Step 11)
**Depende de:** Step 8 (Setup + dependências instaladas), Step 5 (Arquitetura — stack e ferramentas)
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-11-security` ou "Execute a skill llc-step-11-security".

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — stack e ferramentas (Step 5)
- [ ] `docs/planning/TASKS.md` — tarefas de segurança (Step 6)
- [ ] Projeto inicializado com dependências instaladas (Step 8)
- [ ] `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md` — template do relatório
- [ ] Semgrep instalado: `pip install semgrep`
- [ ] Gitleaks instalado: `brew install gitleaks` ou `go install github.com/gitleaks/gitleaks/v8@latest`

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-11-security` do pipeline LLC. Seu objetivo é realizar uma auditoria de segurança completa no código do projeto antes que os agentes iniciem a implementação dos PRPs.

Esta auditoria cobre 3 dimensões: dependências (SCA), código estático (SAST) e credenciais expostas (secrets). Você executará ferramentas reais, lerá os outputs e gerará um relatório consolidado com recomendações.

### 1. Leia as Entradas

- `docs/architecture/ARCHITECTURE.md` — stack do projeto. Identifique se é Node.js (npm) ou Python (pip) para escolher a ferramenta SCA correta.
- `docs/planning/TASKS.md` — tarefa `SEC-001` deve estar presente.
- `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md` — estrutura do relatório a ser gerado.

### 2. Execute a Auditoria (3 Estágios)

#### Estágio 1: SCA — Dependency Audit

**Se projeto Node.js:**
```bash
npm audit --json > .ace/security/sca-report.json
```

**Se projeto Python:**
```bash
pip-audit --format json > .ace/security/sca-report.json
```

**Análise:**
- Leia `.ace/security/sca-report.json`.
- Para cada vulnerability advisory, extraia: package, version, vulnerability name, CVSS score, fix version.
- Classifique por severidade:
  - 🔴 **Crítico:** CVSS ≥ 9.0
  - 🟡 **Alto:** CVSS 7.0–8.9
  - 🟢 **Médio/Baixo:** CVSS < 7.0
- Para vulnerabilidades com fix disponível, recomende: `npm audit fix` ou `pip install --upgrade <package>`.
- Para vulnerabilidades sem fix, registre na tabela "Dependências sem fix disponível" para decisão humana.

#### Estágio 2: SAST — Static Code Analysis (Semgrep)

```bash
semgrep --config=auto --json > .ace/security/sast-report.json
```

**Análise:**
- Leia `.ace/security/sast-report.json`.
- Para cada finding, extraia: file path, line number, rule ID, severity, message.
- Classifique conforme os critérios do Semgrep (ERROR = crítico, WARNING = alto, INFO = médio/baixo).
- Triagem de falsos positivos:
  - Test files (`*.test.ts`, `*.spec.ts`, `__tests__/`) com padrões intencionais.
  - Mock data (`mocks/data/`) com dados sintéticos.

#### Estágio 3: Secrets — Credential Scanning (Gitleaks)

```bash
gitleaks detect --source . --report-format json --report-path .ace/security/secrets-report.json
```

**Análise:**
- Leia `.ace/security/secrets-report.json`.
- Para cada secret detectado, extraia: file, line, rule ID, entropy.
- Triagem de falsos positivos:
  - Arquivos em `mocks/data/` com secrets de exemplo.
  - Arquivos em `docs/` com exemplos documentados.
  - Variáveis de ambiente de exemplo (`.env.example`).
- Secrets reais (entropy alta + fora de mocks/docs): 🔴 bloquear.

### 3. Gere o Relatório Consolidado

Preencha `docs/security/SECURITY_AUDIT_REPORT.md` seguindo o template `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md`.

**Regras de preenchimento:**
- Substitua `{{...}}` pelos valores reais dos scans.
- SCA: preencha a tabela §2.1 com todas as vulnerabilidades. Se houver dependências sem fix, liste em §2.2.
- SAST: preencha §3.1 com findings reais. Documente falsos positivos triados em §3.2 com justificativa.
- Secrets: preencha §4.1 com secrets detectados. Documente falsos positivos em §4.2.
- Gate Decision: `APROVADO` se 0 críticos e 0 secrets reais. `REPROVADO` caso contrário.

### 4. Regras Críticas

- **Anti-alucinação:** Sempre ler o output real das ferramentas — nunca inventar findings. Se uma ferramenta não estiver instalada, reporte como blocker.
- **Classificação CVSS:** Usar dados do advisory (npm) ou rule metadata (Semgrep). Nunca estimar severidade.
- **Falsos positivos:** Gitleaks findings em `mocks/` e `docs/` devem ser marcados como suspeitos e verificados manualmente. Explique a justificativa no relatório.
- **Idempotência:** Re-execução do step sobrescreve `.ace/security/*.json` e `docs/security/SECURITY_AUDIT_REPORT.md`. Avise antes de sobrescrever.
- **Gate bloqueante:** Se 1+ vulnerabilidade crítica ou 1+ secret real (fora de mocks/docs), o relatório deve marcar `REPROVADO`. O pipeline não avança para PRPs até correção.

### 5. Output Esperado

```
.ace/security/
├── sca-report.json       # Output bruto do npm audit / pip-audit
├── sast-report.json      # Output bruto do Semgrep
└── secrets-report.json   # Output bruto do Gitleaks

docs/security/
└── SECURITY_AUDIT_REPORT.md  # Relatório consolidado com decisão do gate
```

### 6. Ações Pós-Execução

- Se **APROVADO:** Avance para execução dos PRPs (Trilha A: sem UI, Trilha B: Subfluxo F1-F6).
- Se **REPROVADO:**
  - Para vulnerabilidades críticas com fix: execute `npm audit fix` ou equivalente, re-execute o scan.
  - Para vulnerabilidades críticas sem fix: apresente ao humano para decisão (aceitar risco, buscar alternativa, isolar componente).
  - Para secrets reais: remova o secret, verifique se foi commitado (`git log --all -- <file>`), se sim, rotacione a credencial imediatamente e considere `git filter-branch` ou BFG Repo-Cleaner.
```

- [ ] **Step 2: Commit**

```bash
git add docs/skills/llc-step-11-security.md
git commit -m "feat: add llc-step-11-security skill (SCA + SAST + secrets)

- Executes npm audit/pip-audit, Semgrep, and Gitleaks
- Classifies findings by CVSS severity
- Generates consolidated SECURITY_AUDIT_REPORT.md
- Blocks execution on critical (CVSS >= 9.0) vulnerabilities

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Create the Security Audit Report Template

**Files:**
- Create: `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md`

- [ ] **Step 1: Create directory and write template**

```bash
mkdir -p docs/security
```

Write `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md`:

```markdown
# Security Audit Report — {{NOME_DO_SISTEMA}}

**Data:** {{DATA}}
**Versão:** {{VERSAO}}
**Step LLC:** 11-Security (pré-execução)
**Executor:** security_agent

---

## 1. Sumário Executivo

| Indicador | Valor |
|-----------|-------|
| Total de findings | {{TOTAL}} |
| 🔴 Críticos (CVSS ≥ 9.0) | {{CRITICOS}} |
| 🟡 Altos (CVSS 7.0–8.9) | {{ALTOS}} |
| 🟢 Médios/Baixos | {{MEDIOS_BAIXOS}} |
| **Gate Decision** | {{APROVADO / REPROVADO}} |

---

## 2. SCA — Dependency Audit

### 2.1 Resultados

| Package | Version | Vulnerability | CVSS | Fix | Action |
|---------|---------|---------------|------|-----|--------|
| {{PACKAGE}} | {{VERSION}} | {{VULN}} | {{CVSS}} | {{FIX}} | {{ACTION}} |

### 2.2 Dependências sem fix disponível

| Package | Vulnerability | CVSS | Mitigação recomendada |
|---------|---------------|------|-----------------------|
| {{PACKAGE}} | {{VULN}} | {{CVSS}} | {{MITIGACAO}} |

---

## 3. SAST — Static Code Analysis (Semgrep)

### 3.1 Findings por Severidade

| File | Line | Rule | Severity | Message | Fix |
|------|------|------|----------|---------|-----|
| {{FILE}} | {{LINE}} | {{RULE}} | {{SEVERITY}} | {{MESSAGE}} | {{FIX}} |

### 3.2 Falsos Positivos Triados

| Finding | Motivo da exclusão |
|---------|---------------------|
| {{FINDING}} | {{MOTIVO}} |

---

## 4. Secrets — Credential Scanning (Gitleaks)

### 4.1 Secrets Detectados

| File | Line | Rule | Entropy | Verified? | Action |
|------|------|------|---------|-----------|--------|
| {{FILE}} | {{LINE}} | {{RULE}} | {{ENTROPY}} | {{YES/NO}} | {{ACTION}} |

### 4.2 Falsos Positivos

| File | Rule | Motivo |
|------|------|--------|
| {{FILE}} | {{RULE}} | Ex: dados mock em `mocks/data/` |

---

## 5. Backlog de Segurança (Médio/Baixo)

| ID | Finding | Severity | Deferido para |
|----|---------|----------|---------------|
| SEC-{{NNN}} | {{DESCRICAO}} | {{SEVERITY}} | {{MILESTONE}} |

---

## 6. Decisão do Gate 👤

- [ ] 🔴 Nenhuma vulnerabilidade crítica (CVSS ≥ 9.0) sem correção
- [ ] 🟡 Vulnerabilidades altas revisadas — decisão registrada
- [ ] 🟢 Backlog de segurança criado para achados médios/baixos
- [ ] Nenhum secret real exposto (falsos positivos documentados)

**Decisão:** {{APROVADO / REPROVADO — aguardando correções}}

**Assinatura (revisor humano):** {{NOME}}
```

- [ ] **Step 2: Commit**

```bash
git add docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md
git commit -m "feat: add SECURITY_AUDIT_REPORT_TEMPLATE.md

Template for consolidated security audit report covering
SCA, SAST, and secret scanning findings with gate checklist.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: Create .ace/security/ Output Directory

**Files:**
- Create: `.ace/security/` directory (empty, for runtime outputs)

- [ ] **Step 1: Create directory with .gitkeep**

```bash
mkdir -p .ace/security
```

Write `.ace/security/.gitkeep`:

```
# Output directory for security scan raw results.
# Generated at runtime by llc-step-11-security skill:
#   sca-report.json   — npm audit / pip-audit
#   sast-report.json  — Semgrep
#   secrets-report.json — Gitleaks
# These files are gitignored — outputs are regenerated on each audit.
```

- [ ] **Step 2: Add to .gitignore and commit**

Add to `.gitignore`:

```
# Security scan outputs (regenerated on each audit)
.ace/security/sca-report.json
.ace/security/sast-report.json
.ace/security/secrets-report.json
```

```bash
git add .ace/security/.gitkeep .gitignore
git commit -m "feat: add .ace/security/ directory for security scan outputs

Raw JSON outputs from npm audit, Semgrep, and Gitleaks.
Output files are gitignored — regenerated on each audit run.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: Update llc-pipeline-design.md

**Files:**
- Modify: `llc-pipeline-design.md`

Four changes in one file: Mermaid diagram, steps table, skills catalog, gates table.

- [ ] **Step 1: Update the Mermaid diagram (§3.1)**

Replace the Step 10.5 → Step 11 transition at lines 213–224:

Old:
```
    G115 -->|approved| S11[Step 11: LLC Execution]
    S11 --> BACK[PRPs sem UI → agente direto]
    S11 --> UI[PRPs com UI → Subfluxo F1-F6]
    UI --> F4[F4: Hi-Fi]
    F4 --> CV{🔴 CHECKPOINT VISUAL}
    CV -->|approved| F5[F5: Código]
    F5 --> F6[F6: Validação]
    BACK --> QA[Checkpoints QA]
    F6 --> QA
    QA --> DEPLOY[Deploy]
```

New:
```
    G115 -->|approved| S11SEC[Step 11-Security: SCA + SAST + Secrets]
    S11SEC --> GSEC{👤 Gate 11-SEC}
    GSEC -->|approved| S11[Step 11: LLC Execution]
    GSEC -->|rejected| S11SEC
    S11 --> BACK[PRPs sem UI → agente direto]
    S11 --> UI[PRPs com UI → Subfluxo F1-F6]
    UI --> F4[F4: Hi-Fi]
    F4 --> CV{🔴 CHECKPOINT VISUAL}
    CV -->|approved| F5[F5: Código]
    F5 --> F6[F6: Validação]
    BACK --> QA[Checkpoints QA]
    F6 --> QA
    QA --> DEPLOY[Deploy]
```

- [ ] **Step 2: Add row to steps table (§3.2)**

Insert after the Step 10.5 row (line 245) and before Step 11:

```markdown
| 11-SEC | Security Audit | Setup + Dependências instaladas (Step 8) | `.ace/security/*.json`, `docs/security/SECURITY_AUDIT_REPORT.md` | `SECURITY_AUDIT_REPORT_TEMPLATE.md` | 👤 11-SEC |
```

- [ ] **Step 3: Add skill to catalog (§4.2)**

Insert after `llc-user-guide` row (line 291):

```markdown
| `llc-step-11-security` | 11-SEC | Auditoria de segurança pré-execução: SCA (npm audit), SAST (Semgrep) e secrets (Gitleaks) |
```

- [ ] **Step 4: Add Gate 11-SEC to gates table (§6.1)**

Insert after Gate 11.5 row (line 350) and before 🔴 row:

```markdown
| 👤 11-SEC | 11-SEC | 0 vulnerabilidades críticas (CVSS ≥ 9.0)? Secrets reais zerados? Vulnerabilidades altas com decisão registrada? |
```

- [ ] **Step 5: Commit**

```bash
git add llc-pipeline-design.md
git commit -m "docs: integrate Step 11-Security into pipeline design

Add Step 11-Security to Mermaid diagram, steps table,
skills catalog, and human gates system.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: Update LLC_GUIDE.md (PT-BR)

**Files:**
- Modify: `LLC_GUIDE.md`

- [ ] **Step 1: Insert Step 11-Security section before Passo 11**

Insert before `### Passo 11: Execução` (line 409):

```markdown
### Passo 11-Security: Auditoria de Segurança 🆕

**Você faz:**

```
Execute a skill docs/skills/llc-step-11-security.md
```

**A IA faz:**
- Executa **SCA** (npm audit ou pip-audit) — varredura de vulnerabilidades em dependências
- Executa **SAST** (Semgrep) — análise estática de código
- Executa **Secret Scanning** (Gitleaks) — detecção de credenciais expostas
- Classifica achados por severidade (CVSS): 🔴 Crítico (≥ 9.0), 🟡 Alto (7.0–8.9), 🟢 Médio/Baixo (< 7.0)
- Gera `docs/security/SECURITY_AUDIT_REPORT.md` com relatório consolidado e recomendações

**Você valida:** 👤 Gate 11-SEC
- 0 vulnerabilidades críticas (CVSS ≥ 9.0)?
- Nenhum secret real exposto (falsos positivos em mocks/docs são ok)?
- Vulnerabilidades altas revisadas e decisão registrada?

**Só avance quando aprovar.**

---
```

- [ ] **Step 2: Update the approval flow diagram**

Replace the Step 11 line in the flow diagram at line 450:

Old:
```
Step 10.5 ──👤──→
```

New:
```
Step 10.5 ──👤──→ Step 11-Security ──👤──→
```

- [ ] **Step 3: Commit**

```bash
git add LLC_GUIDE.md
git commit -m "docs: add Step 11-Security to LLC execution guide (PT-BR)

Add security audit step before PRP execution with
SCA, SAST, and secret scanning tools.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: Update LLC_GUIDE.en.md (EN-US)

**Files:**
- Modify: `LLC_GUIDE.en.md`

- [ ] **Step 1: Read LLC_GUIDE.en.md to find the Step 11 section start**

The English guide mirrors the PT-BR structure. Find and insert before the Step 11 section.

- [ ] **Step 2: Insert Step 11-Security section before Step 11**

Insert the English version before the equivalent `### Step 11: Execution`:

```markdown
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
```

- [ ] **Step 3: Update the approval flow diagram (English version)**

Same change as PT-BR: add `Step 11-Security ──👤──→` in the flow diagram.

- [ ] **Step 4: Commit**

```bash
git add LLC_GUIDE.en.md
git commit -m "docs: add Step 11-Security to LLC execution guide (EN-US)

Add security audit step before PRP execution with
SCA, SAST, and secret scanning tools.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 7: Update llc-step-6.md (Add security_agent tasks)

**Files:**
- Modify: `docs/skills/llc-step-6.md`

- [ ] **Step 1: Add Security & Audit tasks to the task decomposition section**

After the "Integração e QA" task list (around line 75), add:

```markdown
**Segurança (obrigatório para todo projeto):**
- SEC-001: Executar auditoria de segurança pré-execução (security_agent)
- SEC-002: Revisar PRs que tocam auth, secrets, RBAC, criptografia (security_agent, sob demanda)
```

- [ ] **Step 2: Update agent attribution section**

In the agent metadata section (around line 78), after the table explaining agent fields, add:

```markdown
| **security_agent** | Agente de segurança | Executa auditoria pré-execução (SCA + SAST + secrets) e revisa PRs sensíveis |
```

- [ ] **Step 3: Commit**

```bash
git add docs/skills/llc-step-6.md
git commit -m "feat: add security_agent tasks to llc-step-6

Add SEC-001 (pre-execution security audit) and SEC-002
(security PR review) to task decomposition section.
Define security_agent role in agent attribution table.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8: Update TASKS_TEMPLATE.md

**Files:**
- Modify: `docs/planning/TASKS_TEMPLATE.md`

- [ ] **Step 1: Add security task template row**

After the PRP task template section, add a Security section. Find an appropriate place near the task listing structure and add:

```markdown
### Tarefas de Segurança (Obrigatórias)

Tarefas de segurança são fixas e executadas uma vez no início do Step 11, antes de qualquer PRP:

| ID | Tarefa | Agente | Paralelo? | Estimativa |
|----|--------|--------|-----------|------------|
| SEC-001 | Rodar auditoria de segurança pré-execução (SCA + SAST + secrets) | security_agent | ❌ Sequencial — antes de todos os PRPs | {X}h |
| SEC-002 | Revisar PRs de auth/security durante execução | security_agent | ✅ Paralelo — sob demanda | {X}h |
```

- [ ] **Step 2: Commit**

```bash
git add docs/planning/TASKS_TEMPLATE.md
git commit -m "feat: add security task template to TASKS_TEMPLATE.md

Add mandatory SEC-001 and SEC-002 tasks for security audit.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 9: Update AGENTS_TEMPLATE.md (Security Zone)

**Files:**
- Modify: `docs/templates/AGENTS_TEMPLATE.md`

- [ ] **Step 1: Expand the Auth/Security escalation zone**

Replace the auth line in the "What Counts as Architectural" section (line 166):

Old:
```markdown
- **Auth/Security:** Any modification to authentication, authorization, or secret storage
```

New:
```markdown
- **Auth/Security:** Any modification to authentication, authorization, or secret storage. The `security_agent` must review all PRs touching these areas. If the `security_agent` is not available, escalate to the human reviewer (Gate 11-SEC).
```

- [ ] **Step 2: Add security_agent to the Review Checklist**

In the Reviewer Guidelines section (line 234), add to the review checklist:

After the existing checklist item `- [ ] Hardcoded secrets or environment variables`, add:

```markdown
- [ ] Security audit report reviewed? Check `docs/security/SECURITY_AUDIT_REPORT.md` — zero criticals, zero real secrets
```

- [ ] **Step 3: Commit**

```bash
git add docs/templates/AGENTS_TEMPLATE.md
git commit -m "docs: expand security zone in AGENTS_TEMPLATE.md

Reference security_agent for auth/security PR review.
Add security audit report check to reviewer checklist.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 10: Update TESTING_GUIDE_TEMPLATE.md

**Files:**
- Modify: `docs/testing/TESTING_GUIDE_TEMPLATE.md`

- [ ] **Step 1: Reference .ace/security/ as complementary artifact**

At the end of the template, add a reference to security artifacts. Find the last section of the template and append:

```markdown
---

## Artefatos de Segurança Complementares

Os resultados da auditoria de segurança (Step 11-Security) complementam a documentação de testes:

- `.ace/security/sca-report.json` — vulnerabilidades em dependências (npm audit / pip-audit)
- `.ace/security/sast-report.json` — análise estática de código (Semgrep)
- `.ace/security/secrets-report.json` — credenciais expostas (Gitleaks)
- `docs/security/SECURITY_AUDIT_REPORT.md` — relatório consolidado com decisão do gate

Consulte `docs/security/SECURITY_AUDIT_REPORT.md` para verificar se há vulnerabilidades que impactam a estratégia de testes.
```

- [ ] **Step 2: Commit**

```bash
git add docs/testing/TESTING_GUIDE_TEMPLATE.md
git commit -m "docs: reference .ace/security artifacts in testing guide

Link security audit outputs as complementary testing artifacts.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 11: Update .ace/dependency-graph.yaml

**Files:**
- Modify: `.ace/dependency-graph.yaml`

- [ ] **Step 1: Add security_audit artifact entry**

Insert before the closing of the artifacts section (before the end of file, line 320):

```yaml
  # ── STEP 11-SEC (Security Audit) ──
  security_audit_report:
    path: "docs/security/SECURITY_AUDIT_REPORT.md"
    depends_on:
      - architecture
      - mock_data
    triggers_update: []

  security_scan_outputs:
    path_pattern: ".ace/security/*.json"
    depends_on:
      - architecture
      - mock_data
    triggers_update: []
```

- [ ] **Step 2: Update version metadata**

Update the version and last_updated at the top:

```yaml
version: "1.2.0"
generated_by: "llc-step-4"
last_updated: "2026-06-12"
```

- [ ] **Step 3: Commit**

```bash
git add .ace/dependency-graph.yaml
git commit -m "feat: add security_audit artifacts to dependency graph

Register SECURITY_AUDIT_REPORT.md and .ace/security/*.json
as artifacts depending on architecture and mock_data.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 12: Update FAQ.md and FAQ.en.md

**Files:**
- Modify: `FAQ.md`
- Modify: `FAQ.en.md`

- [ ] **Step 1: Add FAQ entry to FAQ.md (PT-BR)**

Insert a new entry in the "Ferramentas e Integrações" section, after the "Quais ferramentas complementam o workflow LLC?" entry (around line 446):

```markdown
### O pipeline LLC faz pentest automatizado?

Não. O **Step 11-Security** executa auditoria estática de segurança (SCA + SAST + secret scanning) com `npm audit` (ou `pip-audit`), Semgrep e Gitleaks. Essas ferramentas rodam localmente, são open-source e não exigem infraestrutura externa.

Para pentest e DAST (análise dinâmica de aplicações rodando), recomendamos integrar ferramentas complementares via CI/CD:

| Ferramenta | Tipo | GitHub |
|------------|------|--------|
| **OWASP ZAP** | DAST (dynamic scanning) | [github.com/zaproxy/zaproxy](https://github.com/zaproxy/zaproxy) |
| **Nuclei** | Vulnerability scanner | [github.com/projectdiscovery/nuclei](https://github.com/projectdiscovery/nuclei) |
| **SQLMap** | SQL injection testing | [github.com/sqlmapproject/sqlmap](https://github.com/sqlmapproject/sqlmap) |
| **Nikto** | Web server scanner | [github.com/sullo/nikto](https://github.com/sullo/nikto) |
| **Bandit** | Python SAST adicional | [github.com/PyCQA/bandit](https://github.com/PyCQA/bandit) |
| **Brakeman** | Rails SAST adicional | [github.com/presidentbeef/brakeman](https://github.com/presidentbeef/brakeman) |

Essas ferramentas podem ser adicionadas ao pipeline CI/CD definido no `docs/DEPLOYMENT.md` (gerado no Step 10). O LLC é tool-agnostic — qualquer ferramenta equivalente serve.
```

- [ ] **Step 2: Add FAQ entry to FAQ.en.md (EN-US)**

Same entry, in English, in the "Tools & Integrations" section (around line 446):

```markdown
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
```

- [ ] **Step 3: Commit**

```bash
git add FAQ.md FAQ.en.md
git commit -m "docs: add pentest/DAST FAQ entry to FAQ (PT-BR + EN-US)

Document that LLC uses static analysis (SCA+SAST+secrets) and
recommends complementary pentest/DAST tools via CI/CD.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 13: Final — Update Spec Status and Commit

**Files:**
- Modify: `docs/superpowers/specs/2026-06-12-llc-security-step-design.md`

- [ ] **Step 1: Update spec status to approved**

```bash
# Replace "Aguardando Revisão" with "Design Aprovado" in the spec header
```

Old:
```
**Status:** Aguardando Revisão
```

New:
```
**Status:** Design Aprovado
```

- [ ] **Step 2: Final commit**

```bash
git add docs/superpowers/specs/2026-06-12-llc-security-step-design.md
git commit -m "docs: mark LLC Step 11-Security design spec as approved

All design decisions validated and implementation plan created.

Co-Authored-By: Claude <noreply@anthropic.com>"
```
