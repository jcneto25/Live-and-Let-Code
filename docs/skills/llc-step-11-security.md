---
name: llc-step-11-security
description: Pipeline LLC — Auditoria de segurança pré-execução (SCA + SAST + secret scanning + SSRF + security headers + password policy + logging). Executa npm audit/pip-audit, Semgrep e Gitleaks antes dos agentes iniciarem os PRPs.
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
- [ ] `express-rate-limit` ou equivalente instalado (para rate limiting no login)
- [ ] `zxcvbn` ou equivalente instalado (para validação de força de senha)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-11-security` do pipeline LLC. Seu objetivo é realizar uma auditoria de segurança completa no código do projeto antes que os agentes iniciem a implementação dos PRPs.

Esta auditoria cobre 7 dimensões: dependências (SCA), código estático (SAST), credenciais expostas (secrets), SSRF, headers de segurança, política de senha e logging. Você executará ferramentas reais, lerá os outputs e gerará um relatório consolidado com recomendações.

### 1. Leia as Entradas

- `docs/architecture/ARCHITECTURE.md` — stack do projeto. Identifique se é Node.js (npm) ou Python (pip) para escolher a ferramenta SCA correta.
- `docs/planning/TASKS.md` — tarefa `SEC-001` deve estar presente.
- `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md` — estrutura do relatório a ser gerado.

### 2. Execute a Auditoria (7 Estágios)

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
