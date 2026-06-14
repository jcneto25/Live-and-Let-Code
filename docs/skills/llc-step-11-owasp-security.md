---
name: llc-step-11-owasp-security
description: Pipeline LLC — Hardening checklist OWASP Top 10:2021. Verifica controles de acesso, falhas criptográficas, injeção, design inseguro, misconfig, componentes vulneráveis, logging e SSRF após execução dos PRPs.
version: 1.0.0
tags: [security, owasp, hardening, audit, llc-pipeline]
---

# LLC Skill: Step 11-OWASP-Security — Hardening OWASP Top 10:2021

**Pipeline:** Live and Let Code (LLC)
**Fase:** Post-Implementation Security Hardening
**Depende de:** Step 11-Security (SCA + SAST + secrets — pré-implementação), Step 11-PRPs (código implementado)
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-11-owasp-security` ou "Execute a skill llc-step-11-owasp-security".
3. Execute APÓS a implementação dos PRPs (código já escrito e PRs abertos).

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — stack, frameworks, bibliotecas (Step 5)
- [ ] `docs/planning/TASKS.md` — tarefas de segurança (Step 6)
- [ ] PRPs implementados (código disponível no repositório)
- [ ] `docs/security/SECURITY_AUDIT_REPORT.md` — auditoria pré-implementação (Step 11-Security)
- [ ] `docs/security/NULL_SAFETY_REPORT.md` — validação de nulabilidade (Step 12-Null-Safety)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-11-owasp-security` do pipeline LLC. Seu objetivo é realizar uma verificação de hardening pós-implementação baseada no OWASP Top 10:2021 no código do projeto.

Esta skill complementa o Step 11-Security (pré-implementação: SCA + SAST + secrets) com verificações manuais/IA de controles que ferramentas automatizadas não detectam: autorização, lógica de negócio, design seguro e configuração.

### 1. Leia as Entradas

- `docs/architecture/ARCHITECTURE.md` — stack, frameworks, autenticação, autorização.
- `docs/security/SECURITY_AUDIT_REPORT.md` — resultados do scan pré-implementação.
- `docs/business/specs/perfis_permissoes.md` — matriz RBAC/ABAC, regras de segregação.
- Código fonte do projeto — rotas, controllers, middlewares, configurações.

### 2. Execute o Hardening (10 Categorias OWASP)

Para cada categoria, responda às perguntas de verificação e classifique o status.

#### A01:2021 — Broken Access Control

Verificações:
- [ ] Toda rota/endpoint tem middleware de autenticação (exceto rotas públicas documentadas).
- [ ] Toda rota/endpoint tem verificação de autorização (RBAC/ABAC) coerente com `perfis_permissoes.md`.
- [ ] Recursos de outros usuários não são acessíveis por ID guessing (`/users/123` → usuário logado é 123?).
- [ ] Ações privilegiadas (aprovar, publicar, deletar) têm validação de perfil no backend.
- [ ] Não há escalonamento de privilégio via parâmetros manipuláveis (`?role=admin`).
- [ ] CORS está configurado com origens explícitas (não `*`).

Critérios de classificação:
- 🔴 **Crítico:** Rota administrativa sem autenticação OU recurso de outro usuário acessível sem verificação de ownership.
- 🟡 **Alto:** Verificação de autorização apenas no frontend (não no backend).
- 🟢 **Médio:** CORS com `*` em ambiente que não é exclusivamente público.

#### A02:2021 — Cryptographic Failures

Verificações:
- [ ] Senhas são hasheadas com bcrypt/argon2 (nunca MD5/SHA1/SHA256 simples).
- [ ] Dados sensíveis em trânsito usam TLS 1.2+ (verificar configuração do servidor).
- [ ] Dados sensíveis em repouso são criptografados (conforme `perfis_permissoes.md` §8.3).
- [ ] Tokens JWT usam algoritmo seguro (RS256/ES256, não `none` ou HS256 com secret fraco).
- [ ] Chaves de API e secrets não estão hardcoded no código fonte.
- [ ] Números de cartão, CPF, dados de saúde não são logados em texto plano.

Critérios de classificação:
- 🔴 **Crítico:** Senha em texto plano ou hash fraco (MD5/SHA1) OU chave privada exposta no código.
- 🟡 **Alto:** JWT com `alg: none` aceito OU dado sensível logado em texto plano.
- 🟢 **Médio:** TLS 1.0/1.1 habilitado.

#### A03:2021 — Injection

Verificações:
- [ ] Queries SQL usam parâmetros bind/ORM (nunca concatenação de strings com input do usuário).
- [ ] Comandos de shell não usam input do usuário diretamente (ou usam `execFile` com array de args).
- [ ] Validação de input está presente em toda entrada de API (Zod, class-validator, Pydantic).
- [ ] Output HTML é escapado (React faz isso automaticamente; verificar `dangerouslySetInnerHTML`).
- [ ] Headers HTTP não refletem input do usuário sem sanitização (HTTP response splitting).
- [ ] LDAP/XML/XPath queries usam APIs parametrizadas (se aplicável).

Critérios de classificação:
- 🔴 **Crítico:** SQL concatenado com input do usuário OU shell command injection.
- 🟡 **Alto:** `dangerouslySetInnerHTML` com input do usuário sem sanitização.
- 🟢 **Médio:** Validação de input ausente em endpoints não-críticos.

#### A04:2021 — Insecure Design

Verificações:
- [ ] Existe um modelo de ameaças documentado ou análise de riscos (`analise_riscos.md`).
- [ ] Limites de rate limiting estão definidos para endpoints sensíveis (login, reset de senha, API).
- [ ] Senhas têm política de complexidade mínima documentada e implementada.
- [ ] Contas têm lockout após N tentativas de login com falha.
- [ ] Tokens de reset de senha expiram e são de uso único.
- [ ] Workflows críticos (aprovação, delegação, publicação) têm limites e validações de estado.

Critérios de classificação:
- 🔴 **Crítico:** Ausência total de rate limiting em endpoint de login/reset.
- 🟡 **Alto:** Token de reset de senha sem expiração OU reutilizável.
- 🟢 **Médio:** Falta de lockout de conta após tentativas de login.

#### A05:2021 — Security Misconfiguration

Verificações:
- [ ] Headers de segurança HTTP estão configurados: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`.
- [ ] Stack traces e mensagens de erro detalhadas não são expostas em produção.
- [ ] Debug mode está desabilitado em produção (`NODE_ENV=production`, `DEBUG=False`).
- [ ] Serviços desnecessários, portas e funcionalidades estão desabilitados.
- [ ] Permissões de arquivos e diretórios seguem o princípio do menor privilégio.
- [ ] Configurações padrão de frameworks foram revisadas e hardenizadas.

Critérios de classificação:
- 🔴 **Crítico:** Debug mode ativo em produção com stack traces expostos.
- 🟡 **Alto:** CSP ausente ou com `unsafe-inline`/`unsafe-eval` sem justificativa.
- 🟢 **Médio:** Headers de segurança ausentes em rotas não-críticas.

#### A06:2021 — Vulnerable and Outdated Components

Verificações:
- [ ] Dependências têm vulnerabilidades conhecidas? (já verificado no Step 11-Security SCA).
- [ ] Versões de frameworks e bibliotecas estão atualizadas (não EOL).
- [ ] Imagens base de contêineres estão atualizadas e passaram por scan.
- [ ] Processo de atualização de dependências está documentado e é periódico.

Critérios de classificação:
- 🔴 **Crítico:** Dependência com CVE conhecido e exploit público sem correção.
- 🟡 **Alto:** Framework EOL (End of Life) em uso.
- 🟢 **Médio:** Dependência desatualizada sem CVEs conhecidos.

#### A07:2021 — Identification and Authentication Failures

Verificações:
- [ ] Autenticação multifator (MFA) está disponível para perfis críticos.
- [ ] Senhas não têm limite máximo de caracteres baixo (mínimo 64 chars permitidos).
- [ ] Sessões expiram e tokens de refresh têm rotação.
- [ ] IDs de sessão não são expostos em URLs.
- [ ] Registro e recuperação de conta não permitem enumeração de usuários.
- [ ] Não há credenciais padrão (admin/admin) no sistema.

Critérios de classificação:
- 🔴 **Crítico:** Credencial padrão ativa OU ausência de MFA para perfil administrativo.
- 🟡 **Alto:** Enumeração de usuários possível via mensagens de erro diferenciadas.
- 🟢 **Médio:** Sessão sem timeout configurado.

#### A08:2021 — Software and Data Integrity Failures

Verificações:
- [ ] Dependências usam checksums ou lockfiles (`package-lock.json`, `yarn.lock`, `poetry.lock`).
- [ ] Pipeline CI/CD verifica integridade de artefatos antes do deploy.
- [ ] Atualizações de software são entregues via canais seguros (HTTPS, assinatura).
- [ ] Dados serializados/desserializados têm validação de integridade (assinatura, HMAC).
- [ ] Não há desserialização de objetos arbitrários (`eval`, `unserialize` sem validação).

Critérios de classificação:
- 🔴 **Crítico:** `eval`/`unserialize` com input do usuário.
- 🟡 **Alto:** Ausência de lockfile versionado no repositório.
- 🟢 **Médio:** CDN de terceiros sem SRI (Subresource Integrity).

#### A09:2021 — Security Logging and Monitoring Failures

Verificações:
- [ ] Logs de auditoria estão implementados conforme `perfis_permissoes.md` §7.1.
- [ ] Eventos de autenticação (login, logout, falha) são logados com user_id, IP, timestamp.
- [ ] Eventos de autorização negada (403) são logados.
- [ ] Logs não contêm dados sensíveis (senhas, tokens, CPF, cartão).
- [ ] Logs são armazenados de forma segura e imutável (append-only, protegidos contra exclusão).
- [ ] Alertas estão configurados para eventos críticos (múltiplas falhas de login, acesso admin fora de hora).

Critérios de classificação:
- 🔴 **Crítico:** Ausência total de logging em eventos de autenticação/autorização.
- 🟡 **Alto:** Dados sensíveis (senhas, tokens) em logs.
- 🟢 **Médio:** Logs sem retenção ou proteção contra adulteração.

#### A10:2021 — Server-Side Request Forgery (SSRF)

Verificações:
- [ ] Input do usuário não controla URLs de requisições do servidor (fetch, axios, curl).
- [ ] URLs fornecidas pelo usuário são validadas contra uma allowlist de domínios.
- [ ] Requisições para redes internas (localhost, 10.x, 192.168.x, 172.16.x) são bloqueadas.
- [ ] Redirecionamentos HTTP de URLs fornecidas pelo usuário não são seguidos cegamente.
- [ ] Serviços de nuvem que usam metadata endpoints (169.254.169.254) estão protegidos.

Critérios de classificação:
- 🔴 **Crítico:** URL de requisição do servidor controlada pelo usuário sem validação.
- 🟡 **Alto:** Redirecionamentos seguidos sem validação de destino final.
- 🟢 **Médio:** Ausência de timeout em requisições externas.

### 3. Gere o Relatório de Hardening

Preencha `docs/security/OWASP_HARDENING_REPORT.md` com a seguinte estrutura:

```markdown
# Relatório de Hardening — OWASP Top 10:2021

| Campo | Valor |
|---|---|
| **Data da verificação** | {{DATE}} |
| **Auditor** | llc-step-11-owasp-security skill |
| **Referência** | OWASP Top 10:2021 |
| **Decisão** | {{GATE_DECISION}} |

## 1. Sumário

| Categoria | Status | Críticos | Altos | Médios |
|-----------|--------|----------|-------|--------|
| A01 — Broken Access Control | {{A01_STATUS}} | {{A01_CRIT}} | {{A01_HIGH}} | {{A01_MED}} |
| A02 — Cryptographic Failures | {{A02_STATUS}} | {{A02_CRIT}} | {{A02_HIGH}} | {{A02_MED}} |
| A03 — Injection | {{A03_STATUS}} | {{A03_CRIT}} | {{A03_HIGH}} | {{A03_MED}} |
| A04 — Insecure Design | {{A04_STATUS}} | {{A04_CRIT}} | {{A04_HIGH}} | {{A04_MED}} |
| A05 — Security Misconfiguration | {{A05_STATUS}} | {{A05_CRIT}} | {{A05_HIGH}} | {{A05_MED}} |
| A06 — Vulnerable Components | {{A06_STATUS}} | {{A06_CRIT}} | {{A06_HIGH}} | {{A06_MED}} |
| A07 — Auth Failures | {{A07_STATUS}} | {{A07_CRIT}} | {{A07_HIGH}} | {{A07_MED}} |
| A08 — Integrity Failures | {{A08_STATUS}} | {{A08_CRIT}} | {{A08_HIGH}} | {{A08_MED}} |
| A09 — Logging Failures | {{A09_STATUS}} | {{A09_CRIT}} | {{A09_HIGH}} | {{A09_MED}} |
| A10 — SSRF | {{A10_STATUS}} | {{A10_CRIT}} | {{A10_HIGH}} | {{A10_MED}} |

## 2–11. Detalhamento por Categoria

*(Para cada categoria A01–A10, incluir tabela de verificações com Status (✅/❌/⚠), Evidência (arquivo:linha) e Recomendação.)*

## 12. Decisão do Gate

**Decisão:** {{GATE_DECISION}}

### Critérios
- [ ] 0 verificações 🔴 críticas
- [ ] Todas as verificações 🟡 altas têm plano de correção documentado

### Bloqueios
{{BLOCKERS}}

### Recomendações
{{RECOMMENDATIONS}}
```

### 4. Regras Críticas

- **Anti-alucinação:** Só marque ✅ ou ❌ após INSPECIONAR o código real. Se não houver código implementado, marque ⚪ (N/A — sem código para verificar).
- **Evidência obrigatória:** Para cada ❌, cite arquivo e linha específicos do código encontrado.
- **Priorização:** Corrija 🔴 antes de ir para produção. 🟡 deve ter ticket criado. 🟢 é backlog de melhoria.
- **Idempotência:** Re-execução sobrescreve `docs/security/OWASP_HARDENING_REPORT.md`. Avise antes de sobrescrever.
- **Gate bloqueante:** 1+ verificação 🔴 → rejeitar PRs até correção. O pipeline não avança para release.

### 5. Output Esperado

```
docs/security/
└── OWASP_HARDENING_REPORT.md  # Relatório de hardening OWASP Top 10:2021
```

### 6. Ações Pós-Execução

- Se **APROVADO:** Prossiga para release conforme estrategia definida em `docs/DEPLOYMENT.md` (Step 10).
- Se **REPROVADO:**
  - Cada 🔴 crítico deve gerar um hotfix antes do merge para a branch principal.
  - Cada 🟡 alto deve gerar um ticket no backlog com prioridade para a próxima sprint.
  - Após correções, re-execute esta skill e o Step 11-Security (SCA + SAST + secrets).
