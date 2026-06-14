# Security Policy — SGI

## 1. Purpose

This document defines the security policy for the **Investigation Management System (SGI)**, a project conducted under the **Live and Let Code (LLC)** methodology. The policy covers the development lifecycle, platform operations, and reported vulnerability handling.

## 2. Supported Versions

| Version | Status | Security Fixes |
|---------|--------|----------------|
| 1.0.x (main branch) | Under active development | ✅ All vulnerabilities |
| < 1.0 (feature branches) | Preview | Critical vulnerabilities only |

## 3. LLC Security Cycle

The LLC pipeline integrates security checks at the following points:

| Step | Tool | Scope | Gate |
|------|------|-------|------|
| **Step 11-Security** | npm audit / pip-audit | SCA — Dependencies | Blocks on CVSS ≥ 9.0 |
| **Step 11-Security** | Semgrep | SAST — Static code | Blocks on ERROR |
| **Step 11-Security** | Gitleaks | Secrets — Exposed credentials | Blocks on real secrets |
| **Step 12-Null-Safety** | Manual/AI validation | Nullability in PRPs | Blocks on unspecified fields |
| **Step 1** | RBAC/ABAC via `perfis_permissoes.md` | Access control | Blocks on conflicting segregation |
| **Step 5** | Definition in `ARCHITECTURE.md` | Security architecture | Blocks on security gaps |
| **Step 11-OWASP** | Manual/AI verification | OWASP Top 10:2021 hardening | Blocks on 1+ 🔴 check |

### 3.1 Security Reports

Consolidated security audit reports are stored at:

```
docs/security/
├── SECURITY_AUDIT_REPORT.md            # SCA + SAST + Secrets (Step 11)
├── NULL_SAFETY_REPORT.md               # Nullability validation (Step 12)
├── OWASP_HARDENING_REPORT.md           # OWASP Top 10 hardening (Step 11-OWASP)
├── SECURITY_AUDIT_REPORT_TEMPLATE.md   # SCA/SAST/Secrets template
└── NULL_SAFETY_REPORT_TEMPLATE.md      # Null Safety template
```

Raw scan outputs are stored in `.ace/security/` (not versioned).

### 3.2 Post-Implementation Hardening (OWASP Top 10:2021)

After PRP implementation (code written and PRs open), Step 11-OWASP performs hardening checks based on OWASP Top 10:2021. This verification complements automated tools (SCA + SAST + secrets) with manual/AI inspections of controls that tools cannot detect.

**Verified categories (10):**

| ID | Category | Verification Focus |
|----|----------|-------------------|
| A01 | Broken Access Control | Auth middleware on all routes, RBAC/ABAC, ownership check |
| A02 | Cryptographic Failures | Password hashing (bcrypt/argon2), TLS, secure JWT, no hardcoded secrets |
| A03 | Injection | Parameterized SQL, shell injection, input validation, XSS |
| A04 | Insecure Design | Rate limiting, lockout, secure password reset, risk analysis |
| A05 | Security Misconfiguration | HTTP headers (CSP, HSTS), debug disabled, stack traces |
| A06 | Vulnerable Components | Updated dependencies, no CVEs with public exploits |
| A07 | Auth Failures | MFA for critical profiles, secure sessions, no user enumeration |
| A08 | Integrity Failures | Versioned lockfiles, secure CI/CD, no insecure deserialization |
| A09 | Logging Failures | Audit logs, no sensitive data in logs, immutable logs |
| A10 | SSRF | URL validation, internal network blocking, no blind redirects |

**Skill:** `docs/skills/llc-step-11-owasp-security.md`
**Report:** `docs/security/OWASP_HARDENING_REPORT.md`
**Gate:** Blocks release on 1+ 🔴 (critical) check. 🟡 (high) must generate a ticket.

## 4. Reporting Vulnerabilities

### 4.1 Reporting Channel

If you discover a security vulnerability in SGI, do **NOT** open a public issue. Use the confidential channel:

- **GitHub Security Advisories:** [Report via GitHub](https://github.com/jcneto25/Live-and-Let-Code/security/advisories/new) — recommended channel
- **Email:** `seguranca@{{ORGANIZATION}}.jus.br` — for confidential reports that cannot use GitHub
- **PGP Key:** To be published on {{ORGANIZATION}}'s institutional website (in deployment)
- **Project Maintainer:** LLC Team — contact via `docs/skills/llc-step-11-security.md`

### 4.2 Required Information

When reporting a vulnerability, include whenever possible:

1. **Detailed description** of the vulnerability and its potential impact
2. **Steps to reproduce** (proof of concept, payloads, configuration)
3. **Affected version** of the system or component
4. **Estimated CVSS** (if you can calculate it)
5. **Suggested mitigation** (if available)
6. **Your contact** for follow-up (email, GitHub, etc.)

### 4.3 Response Time

| Severity | Initial Triage | Fix | Disclosure |
|----------|---------------|-----|------------|
| 🔴 Critical (CVSS ≥ 9.0) | 24h | 72h | After fix + 7 days |
| 🟡 High (CVSS 7.0–8.9) | 48h | 7 days | After fix + 14 days |
| 🟢 Medium (CVSS 4.0–6.9) | 5 business days | 30 days | Next release notes |
| ⚪ Low (CVSS < 4.0) | 10 business days | Next milestone | Release notes |

### 4.4 Handling Process

1. **Reception and Triage** — The vulnerability is received, recorded, and classified by severity.
2. **Validation** — The team reproduces and confirms the vulnerability.
3. **Fix** — The fix is developed on a private branch.
4. **Test** — The fix is validated with regression and security tests.
5. **Release** — The fix is merged and published.
6. **Disclosure** — An advisory is published with credit to the reporter (if authorized).

## 5. Secure Development Practices

### 5.1 Code

- **Mandatory review** of PRs by at least 1 reviewer before merge.
- **Automated static analysis** via Semgrep in Step 11.
- **Secrets scanning** via Gitleaks in Step 11 and pre-commit hooks.
- **OWASP Top 10 hardening** post-implementation via `llc-step-11-owasp-security` — manual checks of access control, crypto, injection, design, misconfig, auth, integrity, logging, and SSRF before release.
- **Prohibition of hardcoded secrets** — use environment variables or secret manager.
- **Updated dependencies** with `npm audit fix` / `pip-audit --fix` before each release.

### 5.2 Data

- **Information classification** per `perfis_permissoes.md` (PUBLIC, INTERNAL, RESTRICTED, CLASSIFIED).
- **Encryption in transit** via TLS 1.3 as minimum standard.
- **Encryption at rest** for sensitive data (fields defined in `perfis_permissoes.md` §8.3).
- **Input sanitization** on all APIs (protection against XSS, SQL Injection, Command Injection).
- **Nullability validation** per `NULL_SAFETY_REPORT.md` (NPE prevention).

### 5.3 Authentication and Authorization

- **RBAC + ABAC** model per `docs/business/specs/perfis_permissoes.md`.
- **Segregation of duties (SoD)** — incompatibility rules defined in §6 of the profiles document.
- **MFA** for critical profiles.
- **JWT** with configurable expiration and refresh token rotation.
- **Immutable audit logs** for all authentication and authorization events.

### 5.4 Infrastructure

- **Containers** with updated base images and vulnerability scanning.
- **Configuration as code** — versioned and auditable infrastructure.
- **Infrastructure secrets** managed via secret manager (never in commited code or `.env`).

## 6. Disclosure Policy

### 6.1 Advisories

Fixed vulnerabilities are documented in GitHub advisories, containing:

- Vulnerability description (CWE, CVSS)
- Affected versions
- Applied fix
- Workarounds (if available)
- Credit to reporter (if authorized)

### 6.2 Embargo

During the fix period, the vulnerability is kept under embargo. The reporter is kept informed of progress. After the fix and publication, public disclosure occurs according to the timeframes in §4.3.

## 7. Recognition

We appreciate the contribution of researchers and security professionals who responsibly report vulnerabilities. Reporters who follow this policy will receive:

- Credit in the advisory (if authorized)
- Inclusion on the project's acknowledgments page (if authorized)

## 8. Contact

- **Security:** `seguranca@{{ORGANIZATION}}.jus.br` or via [GitHub Security Advisories](https://github.com/jcneto25/Live-and-Let-Code/security/advisories/new)
- **Project Maintainer:** LLC Team
- **Security Pipeline:** `docs/skills/llc-step-11-security.md`
- **Security Documentation:** `docs/security/`
- **Security Policy (this document):** `SECURITY.md`
- **Security Tasks:** `docs/planning/TASKS.md` §4
- **Initial Audit:** Executed on 2026-06-12 — `docs/security/SECURITY_AUDIT_REPORT.md`
