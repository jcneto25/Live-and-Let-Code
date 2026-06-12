---
name: security-audit-report-template
description: Template para relatório consolidado de auditoria de segurança (SCA + SAST + secrets) do pipeline LLC.
version: 1.0.0
tags: [security, audit, template, llc-pipeline]
---

# Relatório de Auditoria de Segurança — {{PROJECT_NAME}}

| Campo | Valor |
|---|---|
| **Data da auditoria** | {{AUDIT_DATE}} |
| **Commit / Tag** | {{GIT_REF}} |
| **Executado por** | {{AUDITOR}} |
| **Ferramentas** | npm audit / pip-audit, Semgrep, Gitleaks |
| **Decisão do Gate** | {{GATE_DECISION}} |

---

## 1. Sumário Executivo

- **Total de vulnerabilidades SCA:** {{SCA_TOTAL}} (🔴 {{SCA_CRITICAL}} críticas, 🟡 {{SCA_HIGH}} altas, 🟢 {{SCA_MEDIUM_LOW}} médias/baixas)
- **Total de findings SAST:** {{SAST_TOTAL}} (🔴 {{SAST_ERROR}} errors, 🟡 {{SAST_WARNING}} warnings, 🟢 {{SAST_INFO}} info)
- **Total de secrets detectados:** {{SECRETS_TOTAL}} (🔴 {{SECRETS_REAL}} reais, ⚪ {{SECRETS_FALSE_POSITIVE}} falsos positivos)
- **Gate Decision:** {{GATE_DECISION}}

### Recomendação

{{EXECUTIVE_RECOMMENDATION}}

---

## 2. SCA — Dependency Audit

### 2.1 Vulnerabilidades Encontradas

| # | Pacote | Versão | Vulnerabilidade | CVSS | Severidade | Fix Disponível | Recomendação |
|---|---|---|---|---|---|---|---|
| 1 | {{PKG_1}} | {{VER_1}} | {{VULN_1}} | {{CVSS_1}} | {{SEV_1}} | {{FIX_1}} | {{REC_1}} |

*(Repetir linha para cada vulnerabilidade encontrada)*

### 2.2 Dependências Sem Fix Disponível

| # | Pacote | Versão | Vulnerabilidade | CVSS | Impacto | Decisão |
|---|---|---|---|---|---|---|
| 1 | {{UNFIXED_PKG}} | {{UNFIXED_VER}} | {{UNFIXED_VULN}} | {{UNFIXED_CVSS}} | {{UNFIXED_IMPACT}} | {{UNFIXED_DECISION}} |

---

## 3. SAST — Static Code Analysis (Semgrep)

### 3.1 Findings

| # | Arquivo | Linha | Regra | Severidade | Mensagem | Recomendação |
|---|---|---|---|---|---|---|
| 1 | {{SAST_FILE_1}} | {{SAST_LINE_1}} | {{SAST_RULE_1}} | {{SAST_SEV_1}} | {{SAST_MSG_1}} | {{SAST_REC_1}} |

*(Repetir linha para cada finding)*

### 3.2 Falsos Positivos Triados

| # | Arquivo | Linha | Regra | Justificativa |
|---|---|---|---|---|
| 1 | {{SAST_FP_FILE}} | {{SAST_FP_LINE}} | {{SAST_FP_RULE}} | {{SAST_FP_JUSTIFICATION}} |

---

## 4. Secrets — Credential Scanning (Gitleaks)

### 4.1 Secrets Detectados

| # | Arquivo | Linha | Regra | Entropia | Real? | Ação |
|---|---|---|---|---|---|---|
| 1 | {{SECRET_FILE_1}} | {{SECRET_LINE_1}} | {{SECRET_RULE_1}} | {{SECRET_ENTROPY_1}} | {{SECRET_REAL_1}} | {{SECRET_ACTION_1}} |

*(Repetir linha para cada secret detectado)*

### 4.2 Falsos Positivos

| # | Arquivo | Linha | Regra | Justificativa |
|---|---|---|---|---|
| 1 | {{SECRET_FP_FILE}} | {{SECRET_FP_LINE}} | {{SECRET_FP_RULE}} | {{SECRET_FP_JUSTIFICATION}} |

---

## 5. Decisão do Security Gate

**Decisão:** {{GATE_DECISION}}

### Critérios
- [ ] 0 vulnerabilidades críticas (CVSS ≥ 9.0)
- [ ] 0 secrets reais (fora de mocks/docs/.env.example)
- [ ] Todas as ferramentas executaram com sucesso

### Bloqueios

{{BLOCKERS_LIST}}

### Ações Recomendadas

{{RECOMMENDED_ACTIONS}}

---

## 6. Log de Execução

```
{{EXECUTION_LOG}}
```

---

## 7. Assinaturas

| Papel | Nome | Data | Assinatura |
|---|---|---|---|
| Auditor | {{AUDITOR_NAME}} | {{AUDIT_DATE}} | |
| Revisor (opcional) | {{REVIEWER_NAME}} | {{REVIEW_DATE}} | |
