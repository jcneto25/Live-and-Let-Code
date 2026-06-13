# OWASP Top 10 Hardening — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `llc-step-11-security` and `llc-step-12-null-safety` to cover the 7 remaining OWASP Top 10 vulnerabilities not yet mitigated by LLC, achieving full coverage.

**Architecture:** Two-file change. `llc-step-11-security.md` gains 4 new audit stages (SSRF, security headers, password policy, logging). `llc-step-12-null-safety.md` gains 2 new validation stages (payload limits, input schema). No new skills or scripts — extends existing infrastructure.

**Tech Stack:** Semgrep (custom rules), Markdown, YAML frontmatter.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `docs/skills/llc-step-11-security.md` | MODIFY | Add Stages 4-7: SSRF, Security Headers, Password Policy, Logging |
| `docs/skills/llc-step-12-null-safety.md` | MODIFY | Add audit checks: payload limits (A06) + schema validation (A08) |
| `FAQ.md` | MODIFY | Add OWASP Top 10 coverage question (PT-BR) |
| `FAQ.en.md` | MODIFY | Add OWASP Top 10 coverage question (EN-US) |

---

### Task 1: Add OWASP Stages 4-7 to llc-step-11-security.md

**Files:**
- Modify: `docs/skills/llc-step-11-security.md`

- [ ] **Step 1: Add Stage 4 — SSRF Protection (A01)**

Insert after Stage 3 (Secrets scanning, before section "3. Gere o Relatorio Consolidado"):

```markdown

#### Estagio 4: SSRF — Server-Side Request Forgery (A01)

Execute Semgrep com regras customizadas de SSRF:

```bash
semgrep --config=auto --include="generic-ssrf*" --json > .ace/security/ssrf-report.json
```

Verifique manualmente os arquivos detectados para os seguintes padroes:

| Padrao de risco | Exemplo | Severidade |
|----------------|---------|-----------|
| URL de usuario usada diretamente em fetch/http | `fetch(userInput)` sem validacao | 🔴 Critico |
| URLs de metadata sem allowlist | `fetch("http://localhost:3001/" + path)` | 🔴 Critico |
| URLs construidas com input do usuario sem encode | `fetch("https://api/" + req.query.url)` | 🟡 Alto |

**Criterios de aprovacao:**
- [ ] Nenhum endpoint usa input do usuario como URL sem validacao (allowlist ou regex).
- [ ] Todas as URLs de metadata/import passam por `new URL()` + verificacao de hostname.
- [ ] URLs internas (localhost, 127.0.0.1, 10.x, 192.168.x) sao bloqueadas ou estao em allowlist explicita.

**Fix recomendado por stack:**
- Node.js: `new URL(input).hostname` + allowlist `["api.external.com"]`
- Python: `urllib.parse.urlparse(input).hostname` + allowlist
- Go: `url.Parse(input).Host` + allowlist
```

- [ ] **Step 2: Add Stage 5 — Security Headers (A02)**

```markdown

#### Estagio 5: Security Headers — Misconfiguration (A02)

Execute Semgrep com regras de headers HTTP:

```bash
semgrep --config="p/security-headers" --json > .ace/security/headers-report.json
```

**Headers obrigatorios verificados:**

| Header | Valor minimo | Severidade se ausente |
|--------|-------------|----------------------|
| `Content-Security-Policy` | `default-src 'self'` | 🔴 Critico |
| `X-Frame-Options` | `DENY` ou `SAMEORIGIN` | 🟡 Alto |
| `X-Content-Type-Options` | `nosniff` | 🟡 Alto |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | 🟢 Medio |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | 🟢 Medio |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | 🔴 Critico (prod) |

**Criterios de aprovacao:**
- [ ] CSP presente com `default-src 'self'` ou mais restritivo.
- [ ] `X-Frame-Options` e `X-Content-Type-Options` presentes.
- [ ] HSTS presente para ambientes de producao.
- [ ] Helmet ou equivalente configurado (Node.js), Django SecurityMiddleware (Python), ou middleware equivalente.

**Fix recomendado:**
- Node.js/Express: `app.use(helmet())`
- Next.js: configurar `headers()` no `next.config.js`
- Python/Django: `SECURE_HSTS_SECONDS`, `SECURE_CONTENT_TYPE_NOSNIFF`
```

- [ ] **Step 3: Add Stage 6 — Password Policy (A07)**

```markdown

#### Estagio 6: Password Policy — Authentication Hardening (A07)

Execute Semgrep para detectar politicas de senha fracas:

```bash
semgrep --config=auto --include="generic-password*" --json > .ace/security/password-report.json
```

**Regras de validacao de senha:**

| Regra | Threshold minimo | Severidade se violada |
|-------|-----------------|----------------------|
| Comprimento minimo | 8 caracteres (≥ 12 recomendado) | 🔴 Critico se < 6 |
| Complexidade | Letras + numeros + especiais OU zxcvbn score ≥ 3 | 🟡 Alto se ausente |
| Mensagem de erro | Generica ("Invalid credentials") — sem enumeracao de conta | 🟡 Alto se especifica |
| Rate limiting no login | Max 5 tentativas por IP/minuto | 🔴 Critico se ausente |
| JWT secret fallback | Proibido `process.env.JWT_SECRET \|\| "default"` | 🔴 Critico |

**Criterios de aprovacao:**
- [ ] `minPasswordLength >= 8` no codigo de validacao.
- [ ] Nenhum fallback para valor default em secrets (`JWT_SECRET`, `ENCRYPTION_KEY`).
- [ ] Rate limiting configurado no endpoint de login (`express-rate-limit` ou equivalente).
- [ ] Mensagens de erro de autenticacao sao genericas (nao revelam se usuario existe).

**Fix recomendado:**
- Node.js: `express-rate-limit` + `zxcvbn` + `process.env.JWT_SECRET` sem fallback
- Python: `django-axes` + `throw ValueError` se env var ausente
```

- [ ] **Step 4: Add Stage 7 — Logging & Monitoring (A09)**

```markdown

#### Estagio 7: Logging & Monitoring — Audit Trail (A09)

Execute Semgrep para detectar ausencia de logging:

```bash
semgrep --config=auto --include="generic-logging*" --json > .ace/security/logging-report.json
```

**Endpoints que DEVEM ter logging:**

| Tipo de endpoint | Evento a loggar | Severidade se ausente |
|-----------------|----------------|----------------------|
| Login (sucesso) | `logger.info("Login: user={id}", { userId })` | 🟡 Alto |
| Login (falha) | `logger.warn("Login failed: ip={ip}", { ip })` | 🔴 Critico |
| Password change | `logger.info("Password changed: user={id}")` | 🟡 Alto |
| Role/permission change | `logger.warn("Role changed: user={id}, from={old}, to={new}")` | 🔴 Critico |
| Data export/download | `logger.info("Export: user={id}, type={format}")` | 🟢 Medio |

**Regra Semgrep customizada — empty catch blocks:**

Verifique também catch blocks vazios (A10 — ja coberto pela regra padrao `empty-catch` do Semgrep). Confirme que nenhum catch block no codigo de producao esta vazio.

**Criterios de aprovacao:**
- [ ] Endpoint de login faz `logger.warn()` em falhas de autenticacao.
- [ ] Operacoes sensiveis (role change, password reset, data export) tem log de auditoria.
- [ ] Nenhum `catch {}` vazio em codigo de producao.
- [ ] Logs incluem: timestamp, user ID (se autenticado), IP, acao, resultado.

**Fix recomendado:**
- Node.js: `pino` ou `winston` + middleware de request logging
- Python: `logging` module + `structlog`
- Go: `slog` (stdlib) ou `zap`
```

- [ ] **Step 5: Update the report template reference**

In section "3. Gere o Relatorio Consolidado", add the new stages to the report structure:

Replace:
```
- SCA: preencha a tabela 2.1 com todas as vulnerabilidades...
- SAST: preencha 3.1 com findings reais...
- Secrets: preencha 4.1 com secrets detectados...
- Gate Decision: APROVADO se 0 criticos e 0 secrets reais...
```

With:
```
- SCA: preencha a tabela 2.1 com todas as vulnerabilidades. Se houver dependencias sem fix, liste em 2.2.
- SAST: preencha 3.1 com findings reais. Documente falsos positivos triados em 3.2.
- Secrets: preencha 4.1 com secrets detectados. Documente falsos positivos em 4.2.
- SSRF: preencha 5.1 com endpoints vulneraveis a SSRF. Documente allowlists aplicadas em 5.2.
- Headers: preencha 6.1 com headers ausentes ou mal configurados.
- Password: preencha 7.1 com violacoes de politica de senha.
- Logging: preencha 8.1 com endpoints sem logging. Liste catch blocks vazios em 8.2.
- Gate Decision: APROVADO se 0 criticos, 0 secrets reais, 0 SSRF sem allowlist, headers obrigatorios presentes, politica de senha >= minima, e logging em endpoints sensiveis. REPROVADO caso contrario.
```

- [ ] **Step 6: Update prerequisites (tools)**

Add to the prerequisites list:
```markdown
- [ ] `express-rate-limit` ou equivalente instalado (para rate limiting no login)
- [ ] `zxcvbn` ou equivalente instalado (para validacao de forca de senha)
```

- [ ] **Step 7: Commit**

```bash
git add docs/skills/llc-step-11-security.md
git commit -m "feat: add OWASP stages 4-7 to security audit (SSRF, headers, passwords, logging)"
```

---

### Task 2: Extend llc-step-12-null-safety.md with A06 and A08

**Files:**
- Modify: `docs/skills/llc-step-12-null-safety.md`

- [ ] **Step 1: Add Stage 4 — Payload Limits (A06 — Insecure Design / DoS)**

Insert after Stage 3 (Classificacao e Relatorio), before section "4. Output Esperado":

```markdown

#### Estagio 4: Validacao de Limites de Payload (A06 — DoS Prevention)

Para cada PRP com API endpoint ou endpoint de import/upload, verifique:

**Regras de validacao:**

| Check | Criterio | Severidade se ausente |
|-------|---------|----------------------|
| `maxBodySize` declarado | Todo endpoint que recebe POST/PUT deve declarar limite de payload | 🔴 Critico |
| `rateLimit` declarado | Todo endpoint publico deve declarar rate limit (req/min) | 🔴 Critico |
| `maxFileSize` declarado | Todo endpoint de upload deve declarar tamanho maximo de arquivo | 🔴 Critico |
| `maxItems` declarado | Todo endpoint de import (JSON, CSV) deve declarar limite de registros | 🟡 Alto |
| `timeout` declarado | Operacoes pesadas (export, batch) devem declarar timeout | 🟡 Alto |

**Criterios de aprovacao:**
- [ ] PRPs com endpoints POST/PUT declaram `maxBodySize` (ex: `100kb` para JSON, `10mb` para upload).
- [ ] PRPs com endpoints publicos declaram `rateLimit` (ex: `60 req/min` para API publica).
- [ ] PRPs com endpoints de import declaram `maxItems` (ex: `1000 registros por lote`).
- [ ] Nenhum endpoint aceita payload ilimitado.
```

- [ ] **Step 2: Add Stage 5 — Input Schema Validation (A08 — Data Integrity)**

```markdown

#### Estagio 5: Validacao de Schema de Input (A08 — Data Integrity)

Para cada PRP com API endpoint, verifique se o input tem schema de validacao declarado:

**Regras de validacao:**

| Check | Criterio | Severidade se ausente |
|-------|---------|----------------------|
| Schema de input declarado | Todo endpoint que recebe dados (POST/PUT/PATCH) deve ter schema de validacao (Zod, Yup, Pydantic, JSON Schema) | 🔴 Critico |
| Campos obrigatorios marcados | Schema declara quais campos sao `required` vs `optional` | 🟡 Alto |
| Tipos validados | Schema valida tipos (string, number, boolean, enum, uuid) | 🟡 Alto |
| Sanitizacao declarada | Se o input vai para HTML, schema declara sanitizacao (DOMPurify, bleach) | 🔴 Critico |
| Integridade de import | Endpoints de import (JSON, CSV) verificam hash/assinatura do arquivo? | 🟡 Alto |

**Criterios de aprovacao:**
- [ ] Todo endpoint POST/PUT/PATCH tem schema de validacao declarado no PRP.
- [ ] Schemas de validacao incluem: tipo, required/optional, constraints (min, max, pattern).
- [ ] Inputs que renderizam HTML passam por sanitizacao (DOMPurify no frontend, bleach/sanitize-html no backend).
- [ ] Endpoints de import implementam verificacao de integridade (schema validation + hash check).

**Fix recomendado por stack:**
- Node.js: Zod schema + `DOMPurify.sanitize()` para HTML output
- Python: Pydantic model + `bleach.clean()` para HTML output  
- Go: `go-playground/validator` struct tags + `bluemonday` para HTML output
```

- [ ] **Step 3: Update report structure to include new stages**

In section "5. Formato do Relatorio", add to the Sumario:

```markdown
- 🚫 Endpoints sem limites de payload: {{NO_LIMIT_COUNT}}
- 🚫 Endpoints sem schema de validacao: {{NO_SCHEMA_COUNT}}
- 🚫 Inputs HTML sem sanitizacao: {{NO_SANITIZE_COUNT}}
```

And add new sections after 3.4:

```markdown

## 4. Limites de Payload (A06)

### 4.1 Endpoints sem maxBodySize Declarado (🔴 Critico)

| PRP | Endpoint | Tipo | Recomendacao |
|---|---|---|---|
| ... | ... | ... | ... |

### 4.2 Endpoints sem rateLimit Declarado (🔴 Critico)

| PRP | Endpoint | Recomendacao |
|---|---|---|---|

## 5. Schemas de Validacao (A08)

### 5.1 Endpoints sem Schema de Input (🔴 Critico)

| PRP | Endpoint | Metodo | Recomendacao (Zod/Pydantic/validator) |
|---|---|---|---|

### 5.2 Inputs HTML sem Sanitizacao (🔴 Critico)

| PRP | Componente/Endpoint | Input | Recomendacao (DOMPurify/bleach/bluemonday) |
|---|---|---|---|
```

- [ ] **Step 4: Commit**

```bash
git add docs/skills/llc-step-12-null-safety.md
git commit -m "feat: add OWASP A06 and A08 checks to null-safety (payload limits, input schemas)"
```

---

### Task 3: Add OWASP FAQ question

**Files:**
- Modify: `FAQ.md`
- Modify: `FAQ.en.md`

- [ ] **Step 1: Add FAQ question (PT-BR)**

Insert after the "Git Worktree" FAQ section:

```markdown

---

## 🛡️ Seguranca no LLC

### O LLC cobre o OWASP Top 10?

Sim. O LLC implementa cobertura completa do OWASP Top 10 em **3 etapas do pipeline**:

| OWASP | Vulnerabilidade | Etapa LLC | Mecanismo |
|:-----:|----------------|-----------|-----------|
| A01 | Broken Access Control (SSRF) | Step 11-Security | Semgrep + validacao manual de allowlist de URLs |
| A02 | Security Misconfiguration | Step 11-Security | `semgrep --config=p/security-headers` + check de CSP, HSTS, X-Frame-Options |
| A03 | Supply Chain | Step 11-Security | `npm audit` / `pip-audit` com classificacao CVSS e gate bloqueante |
| A04 | Cryptographic Failures | Step 11-Security | Gitleaks (secrets) + Semgrep (JWT fallback proibido) |
| A05 | Injection (XSS) | Step 11-Security + Step 12 | Semgrep (innerHTML, dangerouslySetInnerHTML) + DOMPurify gate |
| A06 | Insecure Design (DoS) | Step 12-Null-Safety | Validacao de maxBodySize, rateLimit, maxItems nos PRPs |
| A07 | Authentication Failures | Step 11-Security | Semgrep (password length >= 8, zxcvbn) + rate limiting gate |
| A08 | Data Integrity | Step 12-Null-Safety | Validacao de schema de input (Zod/Pydantic) + sanitizacao HTML |
| A09 | Logging & Monitoring | Step 11-Security | Semgrep (logger.warn obrigatorio em login fail) + empty-catch detection |
| A10 | Exceptional Conditions | Step 11-Security | Semgrep empty-catch rule + null-safety validation |

**Gate Security (Step 11):** O pipeline nao avanca para execucao de PRPs se houver vulnerabilidades criticas, secrets expostos, SSRF sem allowlist, ou headers de seguranca ausentes.
```

- [ ] **Step 2: Add FAQ question (EN-US)**

Same content in English:

```markdown

---

## 🛡️ Security in LLC

### Does LLC cover the OWASP Top 10?

Yes. LLC implements complete coverage of the OWASP Top 10 across **3 pipeline stages**:

| OWASP | Vulnerability | LLC Stage | Mechanism |
|:-----:|--------------|-----------|-----------|
| A01 | Broken Access Control (SSRF) | Step 11-Security | Semgrep + manual URL allowlist validation |
| A02 | Security Misconfiguration | Step 11-Security | `semgrep --config=p/security-headers` + CSP, HSTS, X-Frame-Options check |
| A03 | Supply Chain | Step 11-Security | `npm audit` / `pip-audit` with CVSS classification and blocking gate |
| A04 | Cryptographic Failures | Step 11-Security | Gitleaks (secrets) + Semgrep (forbidden JWT fallback) |
| A05 | Injection (XSS) | Step 11-Security + Step 12 | Semgrep (innerHTML, dangerouslySetInnerHTML) + DOMPurify gate |
| A06 | Insecure Design (DoS) | Step 12-Null-Safety | maxBodySize, rateLimit, maxItems validation in PRPs |
| A07 | Authentication Failures | Step 11-Security | Semgrep (password length >= 8, zxcvbn) + rate limiting gate |
| A08 | Data Integrity | Step 12-Null-Safety | Input schema validation (Zod/Pydantic) + HTML sanitization |
| A09 | Logging & Monitoring | Step 11-Security | Semgrep (logger.warn required on login fail) + empty-catch detection |
| A10 | Exceptional Conditions | Step 11-Security | Semgrep empty-catch rule + null-safety validation |

**Security Gate (Step 11):** The pipeline does not advance to PRP execution if critical vulnerabilities, exposed secrets, SSRF without allowlist, or missing security headers are found.
```

- [ ] **Step 3: Commit**

```bash
git add FAQ.md FAQ.en.md
git commit -m "docs: add OWASP Top 10 coverage FAQ section (PT-BR + EN-US)"
```
