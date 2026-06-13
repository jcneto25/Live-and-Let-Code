---
name: owasp-spec-delta
description: Delta entre a especificacao original, o plano de implementacao e o que foi efetivamente entregue para o hardening OWASP no pipeline LLC.
version: 1.0.0
tags: [spec-delta, owasp, security, llc-pipeline, traceability]
---

# Specification Delta — OWASP Hardening (Junho 2026)

**Spec de referencia:** `docs/superpowers/specs/2026-06-12-llc-security-step-design.md` (281 linhas)
**Plano de implementacao:** `docs/superpowers/plans/2026-06-13-owasp-hardening.md` (391 linhas)
**Entregue:** 9 arquivos (2.171 linhas totais)

---

## 1. Visao Geral das Divergencias

| Aspecto | Spec Original | Plano | Entregue | Divergencia |
|---------|--------------|-------|----------|-------------|
| **Skill OWASP** | Nao existia | Modificar `llc-step-11-security.md` (adicionar Stages 4-7) | Skill dedicada `llc-step-11-owasp-security.md` | **Arquitetural** |
| **Null safety OWASP** | Nao existia | Modificar `llc-step-12-null-safety.md` (adicionar Stages 4-5) | Nao modificado; OWASP consolidado no skill proprio | **Escopo** |
| **Modelo mental** | 1 skill de seguranca | 2 skills estendidas inline | 3 skills especializadas (pre-code automated + design + post-code manual) | **Arquitetural** |
| **Relatorio OWASP** | Nao especificado | Nao especificado | `OWASP_HARDENING_REPORT.md` dedicado | **Aditivo** |
| **FAQ** | Nao existia | Tabela "OWASP Top 10 coverage" | 2 Q&As detalhados + exemplos reais | **Escopo expandido** |
| **Tarefas (TASKS.md)** | Nao existia | Nao especificado | SEC-004 + sub-tarefas + gate checklist | **Aditivo** |
| **Politica (SECURITY.md)** | Nao existia | Nao especificado | Sec.3 pipeline + Sec.3.2 hardening + Sec.5.1 praticas | **Aditivo** |

---

## 2. Divergencia Principal: Skill Dedicado vs. Estender Skills Existentes

### O que o plano dizia (Tasks 1 e 2)

O plano propunha **modificar** dois skills existentes:
- `llc-step-11-security.md`: adicionar Stages 4-7 (SSRF, Security Headers, Password Policy, Logging)
- `llc-step-12-null-safety.md`: adicionar Stages 4-5 (Payload Limits A06, Input Schema A08)

### O que foi entregue

Criado um **terceiro skill dedicado**: `llc-step-11-owasp-security.md` (263 linhas) com:
- 10 categorias OWASP completas (nao apenas 4+2)
- 60+ verificacoes manuais/IA
- Classificacao 🔴/🟡/🟢 por categoria
- Relatorio proprio (`OWASP_HARDENING_REPORT.md`)

### Por que a divergencia

| Criterio | Abordagem do Plano (extender skills) | Abordagem Entregue (skill dedicado) |
|----------|--------------------------------------|-------------------------------------|
| **Momento de execucao** | Stages 1-7 no mesmo skill (mistura pre-code com post-code) | Pre-code (Step 11-Security) + Post-code (Step 11-OWASP) — separacao clara |
| **Ferramentas vs. raciocinio** | Semgrep para tudo (inclusive headers, password policy, logging) | Semgrep para pattern matching (Step 11-Security); inspecao manual/IA para raciocinio (Step 11-OWASP) |
| **Single Responsibility** | 7 stages em 1 skill (~400+ linhas) | 3 stages no Step 11-Security (133 linhas) + 10 categorias no Step 11-OWASP (263 linhas) |
| **Reusabilidade** | Skill acoplado a ferramentas especificas (semgrep rules, zxcvbn) | Skill tool-agnostic — as verificacoes sao perguntas, nao comandos |
| **Cobertura OWASP** | 4 categorias adicionadas (A01 SSRF, A02 Headers, A07 Passwords, A09 Logging) | 10 categorias completas (todas as A01-A10) |

### Decisao arquitetural

A separacao em 3 skills segue o principio de **Single Responsibility**:

```
Step 11-Security (pre-code)     Step 12-Null-Safety (pre-code)     Step 11-OWASP (post-code)
├─ SCA (npm audit)              ├─ Nulabilidade nos PRPs            ├─ A01 Access Control
├─ SAST (Semgrep)               ├─ Fallbacks documentados           ├─ A02 Cryptography
└─ Secrets (Gitleaks)           └─ Consistencia entre PRPs          ├─ A03 Injection
                                                                     ├─ A04 Insecure Design
                                                                     ├─ A05 Misconfiguration
                                                                     ├─ A06 Vulnerable Components
                                                                     ├─ A07 Auth Failures
                                                                     ├─ A08 Integrity Failures
                                                                     ├─ A09 Logging Failures
                                                                     └─ A10 SSRF
```

O plano original teria misturado verificacoes automatizadas (Semgrep) com verificacoes manuais no mesmo skill, violando o principio de que um skill deve ter um unico proposito claro.

---

## 3. Divergencias Especificas por Artefato

### 3.1 `llc-step-11-security.md`

| Item do Plano | Status | Notas |
|---------------|--------|-------|
| Stage 4: SSRF (A01) | ❌ Nao implementado | Movido para `llc-step-11-owasp-security.md` A10 |
| Stage 5: Security Headers (A02) | ❌ Nao implementado | Movido para `llc-step-11-owasp-security.md` A05 |
| Stage 6: Password Policy (A07) | ❌ Nao implementado | Movido para `llc-step-11-owasp-security.md` A07 |
| Stage 7: Logging (A09) | ❌ Nao implementado | Movido para `llc-step-11-owasp-security.md` A09 |
| Report template update | ❌ Nao implementado | Substituido por `OWASP_HARDENING_REPORT.md` dedicado |
| Prerequisites (express-rate-limit, zxcvbn) | ❌ Nao implementado | Ferramentas especificas substituidas por perguntas de verificacao tool-agnostic |

### 3.2 `llc-step-12-null-safety.md`

| Item do Plano | Status | Notas |
|---------------|--------|-------|
| Stage 4: Payload Limits (A06) | ❌ Nao implementado | Escopo diferente — null safety verifica nulabilidade de campos, nao limites de API |
| Stage 5: Input Schema (A08) | ❌ Nao implementado | Escopo diferente — null safety verifica contratos de dados, nao validacao de schema |
| Report structure update | ❌ Nao implementado | Report mantido focado em nulabilidade |

**Justificativa:** Adicionar payload limits e input schema validation ao skill de null safety violaria seu proposito. Null safety verifica se campos sao `nullable` ou `required` — nao se endpoints tem rate limiting ou sanitizacao HTML. Essas verificacoes pertencem ao hardening OWASP pos-implementacao.

### 3.3 FAQ

| Item do Plano | Status | Notas |
|---------------|--------|-------|
| "Does LLC cover OWASP Top 10?" (PT-BR) | ✅ Parcialmente entregue | Substituido por 2 Q&As mais detalhados |
| "Does LLC cover OWASP Top 10?" (EN-US) | ✅ Parcialmente entregue | Substituido por 2 Q&As mais detalhados |
| Tabela de cobertura OWASP (10 linhas) | ❌ Nao entregue como tabela | Cobertura distribuida nos Q&As de hardening e pipeline |

**Entregue em vez disso:**
- "Como o LLC implementa hardening OWASP Top 10?" — tabela de 10 categorias com verificacoes detalhadas
- "Como funciona o pipeline de auditoria de seguranca?" — fluxo completo com 3 skills e diagrama ASCII
- Ambos com exemplos reais de execucao (Junho 2026)

---

## 4. Artefatos Adicionais (Nao Especificados no Plano)

| Artefato | Linhas | Proposito | Por que foi necessario |
|----------|--------|-----------|----------------------|
| `llc-step-11-owasp-security.md` | 263 | Skill dedicado de hardening OWASP | Single Responsibility — separar verificacoes manuais das automatizadas |
| `OWASP_HARDENING_REPORT.md` | 247 | Relatorio de hardening com evidencias | Rastreabilidade — cada verificacao cita arquivo:linha |
| `TASKS.md` SEC-004 | 35 | Tarefa de hardening no backlog | Operacionalizacao — time sabe o que executar e quando |
| `SECURITY.md` Sec.3.2 | 20 | Documentacao do hardening na politica | Governanca — stakeholders entendem o ciclo completo |
| `Backlog.md` SEC-004 | 3 | Tarefa no backlog de produto | Alinhamento — produto e engenharia usam a mesma linguagem |
| GATE-07, GATE-08 (TASKS.md) | 2 | Gates de OWASP no checklist por onda | Operacionalizacao — gates automatizados por onda |
| FAQ exemplos reais | 4 | Evidencia de execucao nos Q&As | Confianca — usuarios veem que o skill foi testado |

---

## 5. O Que Foi Preservado do Plano Original

| Elemento | Preservado? | Onde |
|----------|------------|------|
| Cobertura OWASP Top 10 completa | ✅ Sim | `llc-step-11-owasp-security.md` (10/10 categorias) |
| Gate bloqueante para criticos | ✅ Sim | 🔴 bloqueia release em todos os 3 skills |
| Uso de Semgrep como ferramenta | ✅ Sim | Step 11-Security (SAST) — mantido como ferramenta principal |
| Relatorio versionado em `docs/security/` | ✅ Sim | 3 relatorios: SECURITY_AUDIT, NULL_SAFETY, OWASP_HARDENING |
| FAQ bilingue (PT-BR + EN-US) | ✅ Sim | Ambos atualizados com Q&As expandidos |
| Integracao com TASKS.md | ✅ Sim (expandido) | SEC-001, SEC-002, SEC-003, SEC-004 |
| YAML frontmatter em todos os artefatos | ✅ Sim | Consistente em 12 arquivos |

---

## 6. Licoes Aprendidas

1. **Skills especializados > skills monoliticos.** O plano original teria criado um `llc-step-11-security.md` de ~400 linhas com 7 stages misturando ferramentas automatizadas e verificacoes manuais. A separacao em 3 skills (pre-code automated, pre-code design, post-code manual) e mais manutenivel e testavel independentemente.

2. **Verificacoes tool-agnostic > comandos especificos.** O plano especificava comandos Semgrep exatos (`semgrep --config=p/security-headers`). O skill entregue faz perguntas ("Este endpoint verifica ownership?") que sobrevivem a mudancas de ferramentas.

3. **Especificacoes evoluem na execucao.** O plano foi escrito antes de existir codigo para auditar. Durante a execucao, ficou claro que payload limits e input schema validation pertencem ao hardening OWASP, nao ao null safety — sao dominios diferentes.

4. **Relatorios dedicados > secoes em relatorios compartilhados.** O plano propunha adicionar secoes de OWASP ao `SECURITY_AUDIT_REPORT.md`. Um relatorio dedicado (`OWASP_HARDENING_REPORT.md`) permite execucao independente e auditoria separada.

---

## 7. Rastreabilidade

| Spec → | Plano → | Entregue |
|---------|---------|----------|
| `2026-06-12-llc-security-step-design.md` §2.2 (3 stages) | Task 1 (adicionar 4 stages) | `llc-step-11-security.md` (3 stages mantidos) + `llc-step-11-owasp-security.md` (10 categorias) |
| Spec §2.3 (CVSS classification) | — | Mantido em `llc-step-11-security.md` + expandido com 🔴/🟡/🟢 OWASP |
| Spec §3 (skill frontmatter) | — | 3 skills com frontmatter consistente |
| — | Task 2 (null safety A06/A08) | Consolidado em `llc-step-11-owasp-security.md` |
| — | Task 3 (FAQ OWASP table) | Substituido por 2 Q&As expandidos + exemplos reais |

---

## 8. Conclusao

O plano original foi **arquiteturalmente refinado** durante a execucao, resultando em:

- **3 skills especializados** em vez de 2 skills estendidos
- **10/10 categorias OWASP** cobertas (vs 6/10 no plano)
- **Separacao pre-code / post-code** que permite re-execucao independente
- **7 artefatos adicionais** nao previstos no plano (relatorio dedicado, tasks, gates, politica, FAQ expandido)

O espirito do plano foi preservado (cobertura OWASP completa, gate bloqueante, relatorios versionados). A execucao melhorou a arquitetura ao aplicar Single Responsibility e separacao de dominios.
