# Política de Segurança — SGI

## 1. Propósito

Este documento define a política de segurança do **Sistema de Gestão de Investigações (SGI)**, projeto conduzido sob a metodologia **Live and Let Code (LLC)**. A política abrange o ciclo de vida de desenvolvimento, a operação da plataforma e o tratamento de vulnerabilidades reportadas.

## 2. Versões Suportadas

| Versão | Status | Correções de Segurança |
|--------|--------|------------------------|
| 1.0.x (branch principal) | Em desenvolvimento ativo | ✅ Todas as vulnerabilidades |
| < 1.0 (branches de feature) | Preview | Apenas vulnerabilidades críticas |

## 3. Ciclo de Segurança LLC

O pipeline LLC integra verificações de segurança nos seguintes pontos:

| Step | Ferramenta | Escopo | Gate |
|------|-----------|-------|------|
| **Step 11-Security** | npm audit / pip-audit | SCA — Dependências | Bloqueia em CVSS ≥ 9.0 |
| **Step 11-Security** | Semgrep | SAST — Código estático | Bloqueia em ERROR |
| **Step 11-Security** | Gitleaks | Secrets — Credenciais expostas | Bloqueia em secrets reais |
| **Step 12-Null-Safety** | Validação manual/IA | Nulabilidade nos PRPs | Bloqueia campos sem especificação |
| **Step 1** | RBAC/ABAC via `perfis_permissoes.md` | Controle de acesso | Bloqueia segregação conflitante |
| **Step 5** | Definição em `ARCHITECTURE.md` | Arquitetura de segurança | Bloqueia gaps de segurança |

### 3.1 Relatórios de Segurança

Os relatórios consolidados de auditoria de segurança são armazenados em:

```
docs/security/
├── SECURITY_AUDIT_REPORT.md        # SCA + SAST + Secrets (Step 11)
├── NULL_SAFETY_REPORT.md           # Validação de nulabilidade (Step 12)
├── SECURITY_AUDIT_REPORT_TEMPLATE.md   # Template SCA/SAST/Secrets
└── NULL_SAFETY_REPORT_TEMPLATE.md      # Template Null Safety
```

Dados brutos dos scans são armazenados em `.ace/security/` (não versionados).

## 4. Reportando Vulnerabilidades

### 4.1 Canal de Reporte

Se você descobrir uma vulnerabilidade de segurança no SGI, **NÃO** abra uma issue pública. Utilize o canal confidencial:

- **GitHub Security Advisories:** [Reportar via GitHub](https://github.com/jcneto25/Live-and-Let-Code/security/advisories/new) — canal recomendado
- **Email:** `seguranca@{{ORGANIZACAO}}.jus.br` — para reportes confidenciais que não possam usar GitHub
- **Chave PGP:** A ser publicada no site institucional da {{ORGANIZACAO}} (em implantação)
- **Mantenedor do Projeto:** Equipe LLC — contato via `docs/skills/llc-step-11-security.md`

### 4.2 Informações Necessárias

Ao reportar uma vulnerabilidade, inclua sempre que possível:

1. **Descrição detalhada** da vulnerabilidade e seu impacto potencial
2. **Passos para reprodução** (proof of concept, payloads, configuração)
3. **Versão afetada** do sistema ou componente
4. **CVSS estimado** (se souber calcular)
5. **Sugestão de mitigação** (se tiver)
6. **Seu contato** para acompanhamento (email, GitHub, etc.)

### 4.3 Tempo de Resposta

| Severidade | Triagem Inicial | Correção | Divulgação |
|------------|-----------------|----------|------------|
| 🔴 Crítica (CVSS ≥ 9.0) | 24h | 72h | Após correção + 7 dias |
| 🟡 Alta (CVSS 7.0–8.9) | 48h | 7 dias | Após correção + 14 dias |
| 🟢 Média (CVSS 4.0–6.9) | 5 dias úteis | 30 dias | Próximo release notes |
| ⚪ Baixa (CVSS < 4.0) | 10 dias úteis | Próximo milestone | Release notes |

### 4.4 Processo de Tratamento

1. **Recepção e Triagem** — A vulnerabilidade é recebida, registrada e classificada por severidade.
2. **Validação** — A equipe reproduz e confirma a vulnerabilidade.
3. **Correção** — A correção é desenvolvida em branch privada.
4. **Teste** — A correção é validada com testes de regressão e segurança.
5. **Release** — A correção é mergeada e publicada.
6. **Divulgação** — Um advisory é publicado com crédito ao reportador (se autorizado).

## 5. Práticas de Desenvolvimento Seguro

### 5.1 Código

- **Revisão obrigatória** de PRs por pelo menos 1 revisor antes de merge.
- **Análise estática** automatizada via Semgrep no Step 11.
- **Secrets scanning** via Gitleaks no Step 11 e em pre-commit hooks.
- **Proibição de segredos hardcoded** — usar variáveis de ambiente ou secret manager.
- **Dependências** atualizadas com `npm audit fix` / `pip-audit --fix` antes de cada release.

### 5.2 Dados

- **Classificação da informação** conforme `perfis_permissoes.md` (PÚBLICO, INTERNO, RESTRITO, SIGILOSO).
- **Criptografia em trânsito** via TLS 1.3 como padrão mínimo.
- **Criptografia em repouso** para dados sensíveis (campos definidos em `perfis_permissoes.md` §8.3).
- **Sanitização de inputs** em todas as APIs (proteção contra XSS, SQL Injection, Command Injection).
- **Validação de nulabilidade** conforme `NULL_SAFETY_REPORT.md` (prevenção de NPE).

### 5.3 Autenticação e Autorização

- Modelo **RBAC + ABAC** conforme `docs/business/specs/perfis_permissoes.md`.
- **Segregação de funções (SoD)** — regras de incompatibilidade definidas em §6 do documento de perfis.
- **MFA** para perfis críticos.
- **JWT** com expiração configurável e refresh token rotation.
- **Logs de auditoria** imutáveis para todos os eventos de autenticação e autorização.

### 5.4 Infraestrutura

- **Contêineres** com imagens base atualizadas e scanning de vulnerabilidades.
- **Configuração como código** — infraestrutura versionada e auditável.
- **Segredos de infra** gerenciados via secret manager (nunca em código ou `.env` commitado).

## 6. Política de Divulgação

### 6.1 Advisories

Vulnerabilidades corrigidas são documentadas em advisories no GitHub, contendo:

- Descrição da vulnerabilidade (CWE, CVSS)
- Versões afetadas
- Correção aplicada
- Workarounds (se houver)
- Crédito ao reportador (se autorizado)

### 6.2 Embargo

Durante o período de correção, a vulnerabilidade é mantida sob embargo. O reportador é mantido informado do progresso. Após a correção e publicação, a divulgação pública ocorre conforme os prazos da tabela §4.3.

## 7. Reconhecimento

Agradecemos a contribuição de pesquisadores e profissionais de segurança que reportam vulnerabilidades de forma responsável. Reportadores que seguirem esta política receberão:

- Crédito no advisory (se autorizado)
- Inclusão na página de agradecimentos do projeto (se autorizado)

## 8. Contato

- **Segurança:** `seguranca@{{ORGANIZACAO}}.jus.br` ou via [GitHub Security Advisories](https://github.com/jcneto25/Live-and-Let-Code/security/advisories/new)
- **Mantenedor do Projeto:** Equipe LLC
- **Pipeline de Segurança:** `docs/skills/llc-step-11-security.md`
- **Documentação de Segurança:** `docs/security/`
- **Política de Segurança (este documento):** `SECURITY.md`
- **Tarefas de Segurança:** `docs/planning/TASKS.md` §4
- **Auditoria Inicial:** Executada em 2026-06-12 — `docs/security/SECURITY_AUDIT_REPORT.md`
