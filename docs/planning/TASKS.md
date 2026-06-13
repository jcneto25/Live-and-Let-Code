---
name: tasks-backlog
description: Backlog operacional do SGI — todas as tarefas organizadas por PRP, fase e onda. Fonte da verdade para status de desenvolvimento.
version: 1.0.0
tags: [tasks, backlog, planning, llc-pipeline, sgi]
---

# Tasks — Backlog de Desenvolvimento

> **Versão:** 1.0 | **Última atualização:** 2026-06-13 | **Status:** Em execução (fase de planejamento)
> **Projeto:** Sistema de Gestão de Investigações (SGI) | **Metodologia:** PRP-Based Development + Dependency Matrix
> **Autor:** Equipe LLC | **Referências:** `docs/planning/PLAN.md`, `docs/planning/DEPENDENCY_MATRIX.md`, `docs/planning/EXECUTION_WAVES.md`

---

## 📋 Checklist Pré-Preenchimento

- [ ] Development Plan aprovado com fases e PRPs definidos
- [ ] Dependency Matrix validada (ondas e dependências)
- [ ] Capacidade do time definida (quantos devs, quantas tarefas paralelas)
- [ ] Definition of Done (DoD) acordada com o time
- [x] Template de PRP revisado e disponível (`docs/prps/PRP_TEMPLATE.md`)

---

## 1. Visão Geral do Backlog

### 1.1 Propósito
Este documento é o **backlog operacional** do SGI. Ele organiza todas as tarefas por PRP, fase e onda, servindo como:
- **Ponto de entrada** para devs saberem o que trabalhar
- **Fonte da verdade** para status de cada PRP
- **Relatório** para stakeholders de progresso
- **Histórico** para auditoria e retrospectivas

### 1.2 Resumo Executivo

| Métrica | Valor | Tendência | Observação |
|---------|-------|-----------|------------|
| **Total PRPs** | 0 | — | PRPs ainda não criados (Step 3 pendente) |
| **Completos** | 0 | — | — |
| **Em andamento** | 0 | — | — |
| **Planejados** | 0 | — | Serão definidos no Step 3 |
| **Bloqueados** | 0 | — | — |
| **Progresso geral** | 0% | — | Fase de especificação em andamento |
| **Ondas completas** | 0 | — | — |
| **Onda atual** | — | — | Pré-PRPs |
| **Velocity média** | N/A | — | A ser medida após primeiros PRPs |
| **Cobertura de testes** | N/A | — | Target: 80% |
| **Débito técnico** | 0 | — | — |

---

## 2. Legenda e Convenções

### 2.1 Status de PRP

| Símbolo | Status | Definição | Quem altera | Quando alterar |
|---------|--------|-----------|-------------|----------------|
| ✅ | Complete | DoD 100% atendido, mergeado na branch principal, deploy staging OK | Tech Lead | Após validação final |
| 🔄 | In Progress | Dev iniciou, código em desenvolvimento, PR pode estar aberto | Dev Owner | Quando começar a codar |
| ⏳ | Planned | Especificado no PRP, priorizado, mas não iniciado | PM | Quando priorizado |
| 🛑 | Blocked | Impedimento técnico ou de negócio ativo | Tech Lead | Quando impedimento identificado |
| ❌ | Cancelled | Removido do escopo, documentar razão | PM | Quando escopo muda |
| ⏸️ | Paused | Suspensão temporária, documentar razão | Tech Lead | Quando necessário pausar |

### 2.2 Status de Tarefa (dentro do PRP)

| Símbolo | Status | Definição |
|---------|--------|-----------|
| [x] | Done | Tarefa concluída |
| [ ] | Todo | Tarefa pendente |
| [~] | In Progress | Tarefa em execução |
| [-] | N/A | Não aplicável a este PRP |
| [?] | Blocked | Bloqueada por dependência externa |

### 2.3 Prioridade

| Nível | Definição | Impacto no release |
|-------|-----------|-------------------|
| **Crítico** | Sem isso, o release não sai | Bloqueante |
| **Alto** | Importante para MVP, mas release pode sair sem | Patch posterior aceitável |
| **Médio** | Desejável, se houver tempo | Backlog próximo |
| **Baixo** | Nice to have, reconhecidamente fora do escopo desta versão | vNext |

---

## 3. Tarefas de Fundação (Pipeline LLC)

> **Fase:** Pre-PRPs | **Onda:** 0 — Fundação
> **Objetivo:** Estabelecer os artefatos base do pipeline antes da criação dos PRPs.

### 3.1 Especificação e Planejamento

| ID | Tarefa | Skill | Status | Prioridade | Dependências | Output |
|----|--------|-------|--------|------------|--------------|--------|
| FDN-001 | Visão Estratégica e Negócio | llc-step-0-5 | ⏳ | Crítico | Documentos de ingestão | `docs/business/specs/visao_estrategica_e_negocio.md` |
| FDN-002 | Guia de Preenchimento da Visão | llc-step-0-5 | ✅ | Crítico | — | `docs/business/specs/guia_preenchimento_visao_estrategica.md` |
| FDN-003 | Análise de Riscos | llc-step-0-5 | ✅ | Alto | FDN-001 | `docs/business/specs/analise_riscos.md` |
| FDN-004 | 7 Especificações (Glossário, RF, RNF, RN, BPMN, Perfis, Integrações) | llc-step-1 | ⏳ | Crítico | FDN-001 | `docs/business/specs/*.md` |
| FDN-005 | Perfis e Permissões (RBAC/ABAC) | llc-step-1 | ✅ | Crítico | FDN-001 | `docs/business/specs/perfis_permissoes.md` |
| FDN-006 | PRD Executivo | llc-step-2 | ⏳ | Crítico | FDN-004, FDN-005 | `docs/prd/executive_PRD.md` |
| FDN-007 | PRD Técnico Institucional | llc-step-2 | ⏳ | Crítico | FDN-004, FDN-005 | `docs/prd/PRD_tecnico_institucional.md` |
| FDN-008 | PRPs (Product Requirements Pages) | llc-step-3 | ⏳ | Crítico | FDN-006, FDN-007 | `docs/prps/PRP-*.md` |
| FDN-009 | Plano de Desenvolvimento | llc-step-4 | ⏳ | Crítico | FDN-008 | `docs/planning/PLAN.md` |
| FDN-010 | Matriz de Dependências | llc-step-4 | ⏳ | Crítico | FDN-008 | `docs/planning/DEPENDENCY_MATRIX.md` |
| FDN-011 | Ondas de Execução | llc-step-4 | ⏳ | Crítico | FDN-010 | `docs/planning/EXECUTION_WAVES.md` |
| FDN-012 | Arquitetura (ADD) | llc-step-5 | ⏳ | Crítico | FDN-004, FDN-007 | `docs/architecture/ARCHITECTURE.md` |
| FDN-013 | Tasks (este documento) | llc-step-6 | ✅ | Crítico | FDN-001 a FDN-012 | `docs/planning/TASKS.md` |

### 3.2 Design e Testes

| ID | Tarefa | Skill | Status | Prioridade | Dependências | Output |
|----|--------|-------|--------|------------|--------------|--------|
| DSG-001 | Design System | llc-step-7 | ⏳ | Alto | FDN-005 | `docs/design/DESIGN_SYSTEM.md` |
| DSG-002 | Mock Data | llc-step-8 | ⏳ | Alto | FDN-005, FDN-012 | `mocks/data/*.json` |
| DSG-003 | Guia de Testes | llc-step-9 | ⏳ | Alto | FDN-012 | `docs/testing/TESTING_GUIDE.md` |
| DSG-004 | Cobertura Baseline | llc-step-9 | ⏳ | Médio | DSG-003 | `docs/testing/COVERAGE_BASELINE.md` |

---

## 4. Tarefas de Segurança (Security Gates)

> **Fase:** Pre-Implementation Validation
> **Objetivo:** Auditoria de segurança e validação de null safety antes da execução dos PRPs.
> **Gate:** Bloqueia implementação se vulnerabilidades críticas (CVSS ≥ 9.0) ou secrets reais forem encontrados.

### 4.1 Security Audit (Step 11)

| ID | Tarefa | Descrição | Status | Prioridade | Dependências |
|----|--------|-----------|--------|------------|--------------|
| **SEC-001** | **Auditoria de Segurança (SCA + SAST + Secrets)** | Executar `llc-step-11-security`: npm audit, Semgrep, Gitleaks. Gerar `SECURITY_AUDIT_REPORT.md`. | ✅ | **Crítico** | FDN-012 (ARCHITECTURE.md), FDN-013 (TASKS.md) |
| SEC-001.1 | SCA — Dependency Audit | Executar `npm audit --json` (ou `pip-audit`). | ✅ | Crítico | Projeto inicializado com dependências |
| SEC-001.2 | SAST — Static Code Analysis | Executar `semgrep --config=auto --json`. | ✅ | Crítico | Semgrep instalado |
| SEC-001.3 | Secrets — Credential Scanning | Executar `gitleaks detect`. | ⚠ | Crítico | Gitleaks instalado (não disponível no ambiente atual) |
| SEC-001.4 | Relatório Consolidado | Preencher `docs/security/SECURITY_AUDIT_REPORT.md`. | ✅ | Crítico | SEC-001.1, SEC-001.2, SEC-001.3 |

**Resultado da Execução (2026-06-12):**
- **SCA:** N/A — projeto sem dependências de runtime (documentação apenas)
- **SAST:** Semgrep 1.166.0 — 340 regras em 147 arquivos — **0 findings**
- **Secrets:** Gitleaks não disponível — verificação manual limpa (0 secrets)
- **Gate:** **APROVADO** (com ressalva: instalar Gitleaks antes do primeiro deploy de código)

**Artefatos:**
- `.ace/security/sca-report.json`
- `.ace/security/sast-report.json`
- `.ace/security/secrets-report.json`
- `docs/security/SECURITY_AUDIT_REPORT.md`

### 4.2 Null Safety Validation (Step 12)

| ID | Tarefa | Descrição | Status | Prioridade | Dependências |
|----|--------|-----------|--------|------------|--------------|
| **SEC-002** | **Validação de Null Safety nos PRPs** | Executar `llc-step-12-null-safety`: verificar nulabilidade em todos os PRPs. Gerar `NULL_SAFETY_REPORT.md`. | ✅ | **Alto** | FDN-008 (PRPs), FDN-013 (TASKS.md) |
| SEC-002.1 | Inventário de Campos | Extrair todas as definições de dados dos PRPs. | ✅ | Alto | FDN-008 |
| SEC-002.2 | Verificação de Contratos | Validar nulabilidade explícita, fallbacks e consistência. | ✅ | Alto | SEC-002.1 |
| SEC-002.3 | Relatório de Null Safety | Preencher `docs/security/NULL_SAFETY_REPORT.md`. | ✅ | Alto | SEC-002.2 |

**Resultado da Execução (2026-06-12):**
- **PRPs encontrados:** 0 (apenas `PRP_TEMPLATE.md` existe)
- **Gate:** **APROVADO** (sem PRPs para validar)
- **Recomendação:** Re-executar após criação dos PRPs (FDN-008)

**Artefatos:**
- `docs/security/NULL_SAFETY_REPORT.md`

### 4.3 Política de Segurança

| ID | Tarefa | Descrição | Status | Prioridade | Dependências |
|----|--------|-----------|--------|------------|--------------|
| **SEC-003** | **Política de Segurança (SECURITY.md)** | Documentar política de vulnerabilidades, canais de reporte e SLAs de resposta. | ✅ | **Alto** | SEC-001 |
| SEC-003.1 | Versões Suportadas | Definir matriz de versões e correções. | ✅ | Alto | — |
| SEC-003.2 | Canal de Reporte | Documentar processo de reporte responsável. | ✅ | Alto | — |
| SEC-003.3 | SLAs de Resposta | Definir prazos por severidade (CVSS). | ✅ | Alto | — |
| SEC-003.4 | Práticas de Desenvolvimento Seguro | Documentar padrões de código, dados, auth e infra. | ✅ | Médio | FDN-012 |

**Artefatos:**
- `SECURITY.md`

### 4.4 OWASP Hardening (Step 11-OWASP)

| ID | Tarefa | Descrição | Status | Prioridade | Dependências |
|----|--------|-----------|--------|------------|--------------|
| **SEC-004** | **Hardening OWASP Top 10:2021** | Executar `llc-step-11-owasp-security`: verificar 10 categorias OWASP pós-implementação dos PRPs. Gerar `OWASP_HARDENING_REPORT.md`. | ✅ | **Alto** | FDN-008 (PRPs implementados), FDN-012 (ARCHITECTURE.md), SEC-001, SEC-002 |
| SEC-004.1 | A01-A03: Access Control, Crypto, Injection | Verificar middleware de auth, hash de senhas, SQL parametrizado. | ✅ | Crítico | Código `.ace/scripts/*.py` auditado |
| SEC-004.2 | A04-A06: Design, Misconfig, Components | Verificar rate limiting, headers HTTP, dependências atualizadas. | ✅ | Alto | Código `.ace/scripts/*.py` auditado |
| SEC-004.3 | A07-A10: Auth, Integrity, Logging, SSRF | Verificar MFA, lockfiles, logs de auditoria, SSRF. | ✅ | Alto | Código `.ace/scripts/*.py` auditado |
| SEC-004.4 | Relatório de Hardening | Preencher `docs/security/OWASP_HARDENING_REPORT.md`. | ✅ | Alto | ✅ Executado: 6/10 categorias com verificações reais, 0 findings |

**Resultado da Execução (2026-06-13):**
- **Escopo:** `.ace/scripts/*.py` (9 scripts, ~85 KB), `pre-commit.sh`, `.pre-commit-config.yaml`
- **A02 (Crypto):** ✅ 0 hardcoded secrets — grep por `password|secret|token|api_key`: 0 ocorrências
- **A03 (Injection):** ✅ 28 `subprocess.run()` — todas com listas, zero `shell=True`. Zero `eval()`/`exec()`.
- **A08 (Integrity):** ✅ `yaml.safe_load()` apenas; zero `pickle`/`yaml.load()` inseguro
- **A09 (Logging):** ✅ logs estruturados via `logging` module; zero dados sensíveis expostos
- **A10 (SSRF):** ✅ zero network requests — grep por `requests|urllib|fetch|httpx`: 0 ocorrências
- **A01, A04, A05, A07:** ⚪ N/A — scripts CLI, não aplicação web
- **Gate:** **APROVADO** — 0 críticos, 0 altos, 0 médios. 6/6 categorias aplicáveis limpas.

**Artefatos:**
- `docs/skills/llc-step-11-owasp-security.md`
- `docs/security/OWASP_HARDENING_REPORT.md`

---

## 5. PRPs (Product Requirements Pages)

> **Fase:** Implementation | **Status:** ⏳ PRPs ainda não criados
> **Observação:** Esta seção será populada após a execução do Step 3 (llc-step-3). Os PRPs serão organizados por fases funcionais do SGI (ex.: F1-Autenticação, F2-Investigações, F3-Evidências, etc.).

### 5.1 Estrutura Prevista de PRPs

| Fase | Domínio Funcional | PRPs Estimados | Status |
|------|-------------------|----------------|--------|
| F0 | Fundação (Infra, CI/CD, Monorepo) | 3-5 | ⏳ |
| F1 | Autenticação e Autorização (RBAC/ABAC) | 3-4 | ⏳ |
| F2 | Gestão de Investigações (CRUD, Workflow) | 5-8 | ⏳ |
| F3 | Evidências e Documentos | 4-6 | ⏳ |
| F4 | Relatórios e Dashboards | 3-5 | ⏳ |
| F5 | Integrações e APIs | 3-4 | ⏳ |
| F6 | Administração e Auditoria | 2-3 | ⏳ |

> **Nota:** A quantidade exata de PRPs será definida no Step 3, após análise dos PRDs e especificações. Os PRPs seguirão o template `docs/prps/PRP_TEMPLATE.md`.

---

## 6. Checklist de Security Gate (por Onda)

> **Regra:** Antes de iniciar cada onda de implementação, o Security Gate deve ser re-executado.

### 6.1 Pré-Onda N

| ID | Verificação | Responsável | Onda 1 | Onda 2 | Onda 3 | Onda 4 |
|----|-------------|-------------|--------|--------|--------|--------|
| GATE-01 | `npm audit` sem críticas (CVSS < 9.0) | Tech Lead | ⏳ | ⏳ | ⏳ | ⏳ |
| GATE-02 | Semgrep sem findings ERROR | Tech Lead | ⏳ | ⏳ | ⏳ | ⏳ |
| GATE-03 | Gitleaks sem secrets reais | Tech Lead | ⏳ | ⏳ | ⏳ | ⏳ |
| GATE-04 | Null safety dos PRPs da onda validado | Tech Lead | ⏳ | ⏳ | ⏳ | ⏳ |
| GATE-05 | `SECURITY_AUDIT_REPORT.md` atualizado | Tech Lead | ⏳ | ⏳ | ⏳ | ⏳ |
| GATE-06 | `NULL_SAFETY_REPORT.md` atualizado | Tech Lead | ⏳ | ⏳ | ⏳ | ⏳ |
| GATE-07 | OWASP: sem verificações 🔴 críticas | Tech Lead | ⏳ | ⏳ | ⏳ | ⏳ |
| GATE-08 | `OWASP_HARDENING_REPORT.md` atualizado | Tech Lead | ⏳ | ⏳ | ⏳ | ⏳ |

### 6.2 Pós-Onda N (Hardening OWASP)

> **Regra:** Após cada onda de implementação, executar o hardening OWASP Top 10:2021 (`llc-step-11-owasp-security`) no código entregue.

| ID | Categoria | Foco da Onda 1 (Fundação) | Foco da Onda 2 (Core) | Foco da Onda 3+ (Completo) |
|----|-----------|---------------------------|-----------------------|----------------------------|
| OW-01 | A01 — Access Control | Middleware de auth, RBAC básico | ABAC por unidade, ownership check | Segregação completa |
| OW-02 | A02 — Cryptography | Hash de senhas, JWT seguro | Criptografia de dados sensíveis | TLS, key rotation |
| OW-03 | A03 — Injection | Validação de input em APIs | SQL parametrizado | XSS, shell injection |
| OW-04 | A04 — Insecure Design | Rate limiting em login | Lockout, reset seguro | Workflows críticos |
| OW-05 | A05 — Misconfiguration | Headers HTTP de segurança | CSP, debug desabilitado | Hardening completo |
| OW-06 | A06 — Components | Scan de dependências (SCA) | Atualização de frameworks | Container scanning |
| OW-07 | A07 — Auth Failures | MFA para admin | Sessão segura | Sem enumeração |
| OW-08 | A08 — Integrity | Lockfiles versionados | CI/CD seguro | Serialização segura |
| OW-09 | A09 — Logging | Logs de auth | Logs de autorização | Alertas de segurança |
| OW-10 | A10 — SSRF | Validação de URLs externas | Bloqueio de redes internas | Proteção completa |

---

## 7. Dívida Técnica e Decisões

| Data | Decisão / Dívida | Contexto | Impacto | Ação futura | Status |
|------|------------------|----------|---------|-------------|--------|
| 2026-06-12 | Gitleaks não disponível no ambiente | Ferramenta não instalada; verificação manual realizada | Baixo (projeto sem código de runtime) | Instalar Gitleaks antes do primeiro deploy | Pendente |
| 2026-06-12 | PRPs ainda não criados | Projeto em fase de especificação | Bloqueia validação de null safety | Executar llc-step-3 para criar PRPs | Pendente |

---

## 8. Controle de Versão

| Versão | Data | Autor | Alterações |
|--------|------|-------|------------|
| 1.0 | 2026-06-13 | Equipe LLC | Versão inicial. Tarefas de fundação, segurança (SEC-001, SEC-002, SEC-003) e estrutura de PRPs. |
