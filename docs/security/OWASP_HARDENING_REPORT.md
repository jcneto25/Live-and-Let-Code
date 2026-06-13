---
name: owasp-hardening-report
description: Relatório de hardening OWASP Top 10:2021 do SGI. Gerado pela skill llc-step-11-owasp-security após implementação dos PRPs.
version: 1.0.0
tags: [security, owasp, hardening, report, llc-pipeline]
---

# Relatório de Hardening — OWASP Top 10:2021

| Campo | Valor |
|---|---|
| **Data da verificação** | 2026-06-13 |
| **Auditor** | llc-step-11-owasp-security skill |
| **Referência** | OWASP Top 10:2021 |
| **Decisão** | **APROVADO** (sem código para verificar) |

---

## 1. Sumário

| Categoria | Status | Críticos | Altos | Médios |
|-----------|--------|----------|-------|--------|
| A01 — Broken Access Control | ⚪ N/A | 0 | 0 | 0 |
| A02 — Cryptographic Failures | ⚪ N/A | 0 | 0 | 0 |
| A03 — Injection | ⚪ N/A | 0 | 0 | 0 |
| A04 — Insecure Design | ⚪ N/A | 0 | 0 | 0 |
| A05 — Security Misconfiguration | ⚪ N/A | 0 | 0 | 0 |
| A06 — Vulnerable Components | ⚪ N/A | 0 | 0 | 0 |
| A07 — Auth Failures | ⚪ N/A | 0 | 0 | 0 |
| A08 — Integrity Failures | ⚪ N/A | 0 | 0 | 0 |
| A09 — Logging Failures | ⚪ N/A | 0 | 0 | 0 |
| A10 — SSRF | ⚪ N/A | 0 | 0 | 0 |

### Recomendação

O projeto SGI está na fase de especificação e planejamento (Steps 0–9 do pipeline LLC). Não há código de aplicação implementado para verificar. O hardening OWASP Top 10:2021 deve ser executado após a implementação dos PRPs, quando houver código fonte (controllers, middlewares, rotas, configurações) para inspecionar. O gate está APROVADO por ausência de código. Consulte `docs/planning/TASKS.md` para o status das tarefas de implementação.

---

## 2. A01:2021 — Broken Access Control

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | Middleware de auth em todas as rotas | ⚪ | — | — |
| 2 | Verificação RBAC/ABAC coerente com `perfis_permissoes.md` | ⚪ | — | — |
| 3 | Ownership check (usuário não acessa recursos de outros) | ⚪ | — | — |
| 4 | Validação de perfil no backend para ações privilegiadas | ⚪ | — | — |
| 5 | Sem escalonamento de privilégio via parâmetros | ⚪ | — | — |
| 6 | CORS com origens explícitas | ⚪ | — | — |

---

## 3. A02:2021 — Cryptographic Failures

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | Senhas hasheadas com bcrypt/argon2 | ⚪ | — | — |
| 2 | TLS 1.2+ para dados em trânsito | ⚪ | — | — |
| 3 | Dados sensíveis criptografados em repouso | ⚪ | — | — |
| 4 | JWT com algoritmo seguro (RS256/ES256) | ⚪ | — | — |
| 5 | Secrets não hardcoded no código | ⚪ | — | — |
| 6 | Dados sensíveis não logados em texto plano | ⚪ | — | — |

---

## 4. A03:2021 — Injection

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | SQL parametrizado (bind/ORM) | ⚪ | — | — |
| 2 | Sem shell command injection | ⚪ | — | — |
| 3 | Validação de input em todas as APIs | ⚪ | — | — |
| 4 | Output HTML escapado (sem XSS) | ⚪ | — | — |
| 5 | Headers HTTP sanitizados | ⚪ | — | — |
| 6 | LDAP/XML/XPath parametrizados (se aplicável) | ⚪ | — | — |

---

## 5. A04:2021 — Insecure Design

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | Análise de riscos documentada | ✅ | `docs/business/specs/analise_riscos.md` | Manter atualizada |
| 2 | Rate limiting em endpoints sensíveis | ⚪ | — | — |
| 3 | Política de complexidade de senha implementada | ⚪ | — | — |
| 4 | Lockout após N tentativas de login | ⚪ | — | — |
| 5 | Token de reset de senha com expiração e uso único | ⚪ | — | — |
| 6 | Workflows críticos com validações de estado | ⚪ | — | — |

---

## 6. A05:2021 — Security Misconfiguration

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | Headers HTTP de segurança (CSP, HSTS, X-Frame, X-Content-Type) | ⚪ | — | — |
| 2 | Stack traces não expostos em produção | ⚪ | — | — |
| 3 | Debug mode desabilitado em produção | ⚪ | — | — |
| 4 | Serviços/portas desnecessários desabilitados | ⚪ | — | — |
| 5 | Permissões de arquivos com menor privilégio | ⚪ | — | — |
| 6 | Configurações padrão de frameworks revisadas | ⚪ | — | — |

---

## 7. A06:2021 — Vulnerable and Outdated Components

**Status:** ⚪ N/A — sem dependências de runtime

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | Dependências sem CVEs conhecidos | ✅ | `SECURITY_AUDIT_REPORT.md` §2 (SCA: N/A) | Re-verificar quando houver package.json |
| 2 | Frameworks atualizados (não EOL) | ⚪ | — | — |
| 3 | Imagens base de contêineres atualizadas | ⚪ | — | — |
| 4 | Processo de atualização de dependências documentado | ⚪ | — | — |

---

## 8. A07:2021 — Identification and Authentication Failures

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | MFA disponível para perfis críticos | ⚪ | — | — |
| 2 | Senhas sem limite máximo baixo (mín 64 chars) | ⚪ | — | — |
| 3 | Sessões com expiração e refresh token rotation | ⚪ | — | — |
| 4 | IDs de sessão não expostos em URLs | ⚪ | — | — |
| 5 | Sem enumeração de usuários | ⚪ | — | — |
| 6 | Sem credenciais padrão (admin/admin) | ⚪ | — | — |

---

## 9. A08:2021 — Software and Data Integrity Failures

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | Lockfiles versionados no repositório | ⚪ | — | — |
| 2 | CI/CD verifica integridade de artefatos | ⚪ | — | — |
| 3 | Atualizações via canais seguros (HTTPS) | ⚪ | — | — |
| 4 | Dados serializados com validação de integridade | ⚪ | — | — |
| 5 | Sem `eval`/`unserialize` com input do usuário | ⚪ | — | — |

---

## 10. A09:2021 — Security Logging and Monitoring Failures

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | Logs de auditoria conforme `perfis_permissoes.md` §7.1 | ⚪ | — | — |
| 2 | Eventos de auth logados (login, logout, falha) | ⚪ | — | — |
| 3 | Eventos de autorização negada (403) logados | ⚪ | — | — |
| 4 | Logs sem dados sensíveis (senhas, tokens, CPF) | ⚪ | — | — |
| 5 | Logs imutáveis e protegidos contra exclusão | ⚪ | — | — |
| 6 | Alertas para eventos críticos de segurança | ⚪ | — | — |

---

## 11. A10:2021 — Server-Side Request Forgery (SSRF)

**Status:** ⚪ N/A — sem código para verificar

| # | Verificação | Status | Evidência | Recomendação |
|---|-------------|--------|-----------|--------------|
| 1 | URLs de requisição do servidor não controladas pelo usuário | ⚪ | — | — |
| 2 | URLs do usuário validadas contra allowlist | ⚪ | — | — |
| 3 | Redes internas bloqueadas (localhost, 10.x, 192.168.x) | ⚪ | — | — |
| 4 | Redirecionamentos HTTP não seguidos cegamente | ⚪ | — | — |
| 5 | Metadata endpoints de nuvem protegidos (169.254.169.254) | ⚪ | — | — |

---

## 12. Decisão do Gate

**Decisão:** **APROVADO** (sem código para verificar)

### Critérios
- [x] 0 verificações 🔴 críticas
- [x] Todas as verificações 🟡 altas têm plano de correção documentado (N/A)

### Bloqueios

Nenhum. O gate está aprovado.

**Observações:**
1. **Ausência de código de aplicação:** O repositório contém apenas documentação, templates e especificações do pipeline LLC. Não há código fonte (controllers, middlewares, rotas, serviços) para inspecionar.
2. **Pré-requisitos não atendidos:** `ARCHITECTURE.md` (Step 5) e PRPs implementados são pré-requisitos para execução completa desta skill.
3. **Verificações parciais possíveis:** A04 (Insecure Design) — análise de riscos existe em `analise_riscos.md`. A06 (Vulnerable Components) — SCA executado e documentado em `SECURITY_AUDIT_REPORT.md`.

### Recomendações

1. **Executar esta skill** após a implementação dos PRPs, quando houver código fonte para inspecionar.
2. **Criar `ARCHITECTURE.md` (Step 5)** com stack de segurança (frameworks, auth, criptografia).
3. **Para cada PRP implementado,** re-executar esta skill incrementalmente (não esperar todos os PRPs).
4. **Integrar verificações OWASP ao Definition of Done** de cada PRP:
   - A01: middleware de auth em novas rotas
   - A03: validação de input em novos endpoints
   - A02: secrets em variáveis de ambiente (nunca hardcoded)
   - A09: logs de auditoria para novas ações

---

## 13. Log de Execução

```
[2026-06-13] Iniciando hardening OWASP Top 10:2021 (llc-step-11-owasp-security)
[2026-06-13] Verificando pré-requisitos...
[2026-06-13] ARCHITECTURE.md: não encontrado (será criado no Step 5)
[2026-06-13] PRPs implementados: 0 (projeto em fase de especificação)
[2026-06-13] Código fonte: apenas scripts .ace/ e templates .md
[2026-06-13] A01–A10: todas as categorias ⚪ N/A (sem código para verificar)
[2026-06-13] Exceções parciais: A04 (analise_riscos.md existe), A06 (SCA executado)
[2026-06-13] GATE: APROVADO — sem código para verificar
[2026-06-13] Hardening concluído.
```

---

## 14. Assinaturas

| Papel | Nome | Data | Assinatura |
|---|---|---|---|
| Auditor | llc-step-11-owasp-security skill (automated) | 2026-06-13 | |
| Revisor (opcional) | — | — | |
