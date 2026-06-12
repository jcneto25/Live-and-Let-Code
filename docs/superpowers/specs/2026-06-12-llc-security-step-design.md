# LLC Step 11-Security — Design Specification

**Versão:** 1.0.0  
**Data:** 12 de Junho de 2026  
**Status:** Aguardando Revisão  
**Projeto:** Live and Let Code (LLC) — Step de Segurança Pré-Execução  
**Autor:** Equipe LLC  

---

## 1. Problema

O pipeline Live and Let Code (LLC) não possui um passo dedicado à avaliação de brechas de segurança antes do deploy. Segurança aparece de forma pulverizada:

- **Step 5 (Arquitetura):** Seção "Segurança e Compliance" no template — define estratégia, não executa auditoria.
- **Step 6 (Tarefas):** Menciona `security_agent` como papel, mas sem protocolo definido.
- **QA Checkpoints (Step 11):** Linha única: "Security audit aprovado?" — sem skill, template, ferramentas ou critérios.

**Consequência:** Vulnerabilidades em dependências, secrets expostos e falhas de código podem chegar ao deploy sem verificação automatizada.

---

## 2. Solução

Criar o **Step 11-Security** — fase inicial do Step 11 (Execução) que executa auditoria estática de segurança antes que os agentes iniciem a implementação dos PRPs.

### 2.1 Posicionamento no Pipeline

```
Step 10.5 (User Guide) → Gate 11.5 ✓
                            │
                            ▼
              ┌─────────────────────────┐
              │ Step 11: Security Audit  │  ← NOVO
              │  ├─ SCA (npm/pip audit) │
              │  ├─ SAST (Semgrep)       │
              │  └─ Secrets (Gitleaks)   │
              └───────────┬─────────────┘
                          │
                    Gate 11-SEC 👤
                    (0 críticas?)
                          │
              ┌───── aprovado ─────┐
              ▼                    ▼
        PRPs sem UI           PRPs com UI
        (agente direto)       (Subfluxo F1-F6)
```

**Justificativa:** Rodar antes dos PRPs evita retrabalho. Se vulnerabilidade crítica existe no scaffold (Step 8), corrigir antes de N agentes escreverem código sobre base vulnerável.

### 2.2 Escopo da Auditoria

| Categoria | Ferramenta | Tipo | Output |
|-----------|-----------|------|--------|
| SCA (Dependency Audit) | `npm audit` / `pip-audit` | Análise de dependências | `.ace/security/sca-report.json` |
| SAST (Static Code) | Semgrep (`--config=auto`) | Análise estática de código | `.ace/security/sast-report.json` |
| Secret Scanning | Gitleaks | Detecção de credenciais | `.ace/security/secrets-report.json` |

**Ferramentas complementares (não executadas pelo step, documentadas na FAQ):** OWASP ZAP, Nuclei, SQLMap, Nikto, Bandit, Brakeman — para pentest e DAST, integrados via CI/CD.

### 2.3 Critérios de Classificação e Bloqueio

| Severidade | CVSS | Ação | Bloqueia Execução? |
|------------|------|------|---------------------|
| 🔴 Crítico | ≥ 9.0 | Corrigir antes de prosseguir | **Sim** |
| 🟡 Alto | 7.0–8.9 | IA recomenda, humano decide | Consultivo |
| 🟢 Médio/Baixo | < 7.0 | Registrado em backlog de segurança | Não |

---

## 3. Skill: `llc-step-11-security`

### 3.1 Frontmatter

```yaml
---
name: llc-step-11-security
description: Pipeline LLC — Auditoria de segurança pré-execução (SCA + SAST + secrets)
version: 1.0.0
tags: [security, audit, sast, sca, secrets, llc-pipeline]
---
```

### 3.2 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — stack e ferramentas (Step 5)
- [ ] `docs/planning/TASKS.md` — tarefas de segurança (Step 6)
- [ ] Projeto inicializado com dependências instaladas (Step 8)
- [ ] Semgrep instalado (`pip install semgrep`)
- [ ] Gitleaks instalado (`brew install gitleaks` ou `go install github.com/gitleaks/gitleaks/v8@latest`)
- [ ] `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md`

### 3.3 Fluxo de Execução

1. **SCA:** Executa `npm audit --json` (ou `pip-audit --format json`), extrai CVSS de cada advisory, classifica por severidade.
2. **SAST:** Executa `semgrep --config=auto --json .`, extrai findings com rule metadata, classifica por severity.
3. **Secrets:** Executa `gitleaks detect --source . --report-format json --report-path .ace/security/secrets-report.json`.
4. **Triagem:** IA analisa cada finding, identifica falsos positivos (ex: secrets de exemplo em `mocks/data/`).
5. **Relatório:** Gera `docs/security/SECURITY_AUDIT_REPORT.md` consolidado, com decisão de gate.

### 3.4 Regras Críticas

- **Anti-alucinação:** Sempre ler o output real das ferramentas — nunca inventar findings.
- **Classificação CVSS:** Usar dados do advisory (npm) ou rule metadata (Semgrep). Nunca estimar.
- **Falsos positivos:** Gitleaks findings em `mocks/` e `docs/` devem ser marcados como suspeitos e verificados manualmente.
- **Idempotência:** Re-execução do step sobrescreve `.ace/security/*.json` e `docs/security/SECURITY_AUDIT_REPORT.md`.

### 3.5 Output Esperado

- `.ace/security/sca-report.json` — resultado bruto do npm audit
- `.ace/security/sast-report.json` — resultado bruto do Semgrep
- `.ace/security/secrets-report.json` — resultado bruto do Gitleaks
- `docs/security/SECURITY_AUDIT_REPORT.md` — relatório consolidado com decisão do gate

---

## 4. Template: `SECURITY_AUDIT_REPORT_TEMPLATE.md`

**Local:** `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md`

### Estrutura

```markdown
# Security Audit Report — {{NOME_DO_SISTEMA}}

**Data:** {{DATA}}
**Versão:** {{VERSAO}}
**Step LLC:** 11-Security (pré-execução)
**Executor:** security_agent

## 1. Sumário Executivo

| Indicador | Valor |
|-----------|-------|
| Total de findings | {{TOTAL}} |
| 🔴 Críticos (CVSS ≥ 9.0) | {{CRITICOS}} |
| 🟡 Altos (CVSS 7.0–8.9) | {{ALTOS}} |
| 🟢 Médios/Baixos | {{MEDIOS_BAIXOS}} |
| **Gate Decision** | {{APROVADO / REPROVADO}} |

## 2. SCA — Dependency Audit

### 2.1 Resultados
| Package | Version | Vulnerability | CVSS | Fix | Action |
|---------|---------|---------------|------|-----|--------|

### 2.2 Dependências sem fix disponível
[Lista separada para decisão humana]

## 3. SAST — Static Code Analysis (Semgrep)

### 3.1 Findings por Severidade
| File | Line | Rule | Severity | Message | Fix |
|------|------|------|----------|---------|-----|

### 3.2 Falsos Positivos Triados
| Finding | Motivo da exclusão |

## 4. Secrets — Credential Scanning (Gitleaks)

### 4.1 Secrets Detectados
| File | Line | Rule | Entropy | Verified? | Action |

### 4.2 Falsos Positivos
[Ex: dados mock em mocks/data/]

## 5. Backlog de Segurança (Médio/Baixo)

| ID | Finding | Severity | Deferido para |

## 6. Decisão do Gate 👤

- [ ] 🔴 Nenhuma vulnerabilidade crítica (CVSS ≥ 9.0) sem correção
- [ ] 🟡 Vulnerabilidades altas revisadas — decisão registrada
- [ ] 🟢 Backlog de segurança criado para achados médios/baixos
- [ ] Nenhum secret real exposto (falsos positivos documentados)

**Decisão:** {{APROVADO / REPROVADO — aguardando correções}}

**Assinatura (revisor humano):** {{NOME}}
```

---

## 5. Gate 11-SEC

| Campo | Valor |
|-------|-------|
| **Gate ID** | 👤 11-SEC |
| **Após** | Step 11-Security (fase inicial do Step 11) |
| **Valida** | 0 vulnerabilidades críticas (CVSS ≥ 9.0); secrets reais zerados; vulnerabilidades altas com decisão registrada |
| **Reprovado** | Retorna para correção — `npm audit fix`, refactor de código afetado, remoção de secrets expostos |
| **Aprovado** | Avança para execução dos PRPs (Trilha A: sem UI, Trilha B: Subfluxo F1-F6) |

---

## 6. Protocolo `security_agent`

### 6.1 Definição Formal

O `security_agent` é um papel especializado do pipeline LLC com 3 responsabilidades:

| # | Responsabilidade | Quando | Descrição |
|---|------------------|--------|-----------|
| 1 | Auditoria pré-execução | Início do Step 11 | Executa SCA + SAST + secret scanning, gera relatório consolidado, classifica findings |
| 2 | Revisão de PRs sensíveis | Durante Step 11 | Revisa PRs que tocam auth, secrets, RBAC, criptografia — zonas de escalação definidas no AGENTS_TEMPLATE.md |
| 3 | Triagem de falsos positivos | Durante auditoria | Decide se finding do Semgrep/Gitleaks é real ou falso positivo (ex: secrets em `mocks/data/`) |

### 6.2 Atribuição no TASKS.md

```markdown
| Tarefa | Agente | Paralelo? |
|--------|--------|-----------|
| SEC-001: Rodar auditoria de segurança pré-execução | security_agent | ❌ Sequencial — antes de todos os PRPs |
| SEC-002: Revisar PRs de auth/security durante execução | security_agent | ✅ Paralelo — sob demanda |
```

---

## 7. FAQ — Pentest e Ferramentas Complementares

```markdown
### O pipeline LLC faz pentest automatizado?

Não. O Step 11-Security executa auditoria estática (SCA + SAST + secret scanning)
com `npm audit`, Semgrep e Gitleaks. Para pentest e DAST (análise dinâmica),
recomendamos integrar ferramentas complementares via CI/CD:

| Ferramenta | Tipo | GitHub |
|------------|------|--------|
| **OWASP ZAP** | DAST (dynamic scanning) | github.com/zaproxy/zaproxy |
| **Nuclei** | Vulnerability scanner | github.com/projectdiscovery/nuclei |
| **SQLMap** | SQL injection testing | github.com/sqlmapproject/sqlmap |
| **Nikto** | Web server scanner | github.com/sullo/nikto |
| **Bandit** | Python SAST adicional | github.com/PyCQA/bandit |
| **Brakeman** | Rails SAST adicional | github.com/presidentbeef/brakeman |

Essas ferramentas podem ser adicionadas ao pipeline CI/CD definido no
`docs/DEPLOYMENT.md` (gerado no Step 10).
```

---

## 8. Impacto em Artefatos Existentes

| Artefato | Mudança |
|----------|---------|
| `llc-pipeline-design.md` | Adicionar Step 11-Security no diagrama Mermaid (§3.1), tabela de etapas (§3.2), catálogo de skills (§4.2), sistema de gates (§6.1) |
| `LLC_GUIDE.md` + `.en.md` | Adicionar Step 11-Security no passo a passo, antes da execução dos PRPs |
| `docs/skills/llc-step-6.md` | Adicionar `security_agent` com tarefa `SEC-001` |
| `docs/planning/TASKS_TEMPLATE.md` | Incluir linha para tarefa de auditoria de segurança |
| `docs/templates/AGENTS_TEMPLATE.md` | Expandir zona de segurança para referenciar `security_agent` |
| `docs/testing/TESTING_GUIDE_TEMPLATE.md` | Referenciar `.ace/security/` como artefato complementar |
| `.ace/dependency-graph.yaml` | Registrar: `SECURITY_AUDIT_REPORT.md` depende de `ARCHITECTURE.md` + código scaffold |
| `FAQ.md` + `FAQ.en.md` | Adicionar entrada sobre pentest complementar |

---

## 9. Arquivos a Criar (Novos)

```
docs/
├── skills/
│   └── llc-step-11-security.md              # Skill de execução
├── security/
│   ├── SECURITY_AUDIT_REPORT_TEMPLATE.md     # Template do relatório
│   └── SECURITY_AUDIT_REPORT.md             # [OUTPUT] Relatório gerado (pela IA)
.ace/
└── security/                                 # Outputs brutos das ferramentas
    ├── sca-report.json                       # [OUTPUT] npm audit / pip-audit
    ├── sast-report.json                      # [OUTPUT] Semgrep
    └── secrets-report.json                   # [OUTPUT] Gitleaks
```

---

## 10. Controle de Versão

| Versão | Data | Autor | Alterações |
|--------|------|-------|------------|
| 1.0.0 | 12/06/2026 | Equipe LLC | Design inicial do Step 11-Security |
