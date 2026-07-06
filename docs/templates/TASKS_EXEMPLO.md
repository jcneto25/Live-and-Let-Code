# TASKS_EXEMPLO.md
# Exemplo de arquivo de tarefas gerado pelo Step 6

## PRP-001: Cadastro Básico de Usuários

**Scaffolding**
- [ ] Criar estrutura de diretórios `src/users/`
- [ ] Configurar schema Prisma para `User`

**Backend**
- [ ] Implementar rota `POST /users` com validação Zod
- [ ] Implementar rota `GET /users/:id`
- [ ] Implementar hash de senha com bcrypt (cost=10)
- [ ] Adicionar unique constraint no email

**Frontend**
- [ ] Criar página `src/pages/users/create.tsx`
- [ ] Implementar validação de email no formulário
- [ ] Adicionar loading states e erros

**Testes**
- [ ] Testes unitários para validação de email (`src/users/user.test.ts`)
- [ ] Testes de integração para cadastro (`test/e2e/users.spec.ts`)
- [ ] Mockar bcrypt no test suite

**Responsável:** dev_agent  
**Estimativa:** 3 dias  
**Paralelização:** ✅

---

## PRP-002: Autenticação JWT

**Scaffolding**
- [ ] Criar diretório `src/auth/`
- [ ] Adicionar dependências `jsonwebtoken`, `bcryptjs`

**Backend**
- [ ] Implementar rota `POST /auth/login`
- [ ] Implementar rota `POST /auth/refresh`
- [ ] Adicionar middleware de autenticação
- [ ] Implementar refresh token com expires

**Testes**
- [ ] Testes de login com credenciais válidas
- [ ] Testes de token expirado
- [ ] Testes de refresh token

**Responsável:** dev_agent  
**Estimativa:** 2 dias  
**Paralelização:** ⚠️ Após PRP-001

---

## PRP-003: Gerenciamento de Perfis

**Scaffolding**
- [ ] Criar estrutura `src/profiles/`
- [ ] Adicionar tabelas no Prisma

**Backend**
- [ ] Implementar CRUD de perfis
- [ ] Adicionar validação de permissões
- [ ] Implementar associação User ↔ Profile

**Testes**
- [ ] Testes de atribuição de perfil
- [ ] Testes de revogação de permissão

**Responsável:** dev_agent  
**Estimativa:** 3 dias  
**Paralelização:** ⚠️ Após PRP-001

---

## PRP-004: Cadastro de Planos

**Scaffolding**
- [ ] Criar estrutura `src/plans/`
- [ ] Adicionar migrations do Prisma

**Backend**
- [ ] Implementar CRUD completo de planos
- [ ] Adicionar workflow de aprovação (RASCUNHO → SUBMETIDO → APROVADO)
- [ ] Implementar regras de negócio (duração máxima)

**Testes**
- [ ] Testes de workflow de aprovação
- [ ] Testes de validação de regras de negócio

**Responsável:** dev_agent  
**Estimativa:** 4 dias  
**Paralelização:** ⚠️ Após onda 1 completa

---

## PRP-005: CRUD de Auditorias

**Scaffolding**
- [ ] Criar estrutura `src/audits/`
- [ ] Adicionar schema no Prisma

**Backend**
- [ ] Implementar CRUD de auditorias
- [ ] Implementar workflow (ABERTA → EM_EXECUCAO → CONCLUIDA)
- [ ] Adicionar evidências (upload de arquivos)

**Testes**
- [ ] Testes de upload de evidências
- [ ] Testes de transição de status

**Responsável:** dev_agent  
**Estimativa:** 5 dias  
**Paralelização:** ⚠️ Após PRP-004

---

## PRP-006: Dashboard de KPIs

**Scaffolding**
- [ ] Criar diretório `src/dashboard/`
- [ ] Configurar biblioteca de gráficos (ex: Recharts)

**Frontend**
- [ ] Criar página de dashboard
- [ ] Implementar cards de KPIs (total de usuários, auditorias, etc.)
- [ ] Adicionar filtros por período

**Responsável:** dev_agent  
**Estimativa:** 4 dias  
**Paralelização:** ⚠️ Após PRP-005

---

## PRP-FDN: Foundation Tasks (Obrigatórias)

**Scaffolding**
- [ ] FDN-001: Configurar linter (ESLint) e formater (Prettier)
- [ ] FDN-002: Configurar TypeScript strict mode
- [ ] FDN-003: Configurar CI/CD básico (GitHub Actions)
- [ ] DSG-001: Configurar ambiente de desenvolvimento

**Responsável:** dev_agent  
**Estimativa:** 1 dia  
**Paralelização:** ✅ (executar antes de todos os outros PRPs)

---

## PRP-SEC: Security Gates (Obrigatórios)

**Pre-Code**
- [ ] SEC-001: Rodar SCA (npm audit/pip-audit)
- [ ] SEC-002: Rodar SAST (Semgrep)
- [ ] SEC-003: Rodar secret scanning (Gitleaks)

**Pos-Code**
- [ ] SEC-004: Hardening OWASP Top 10
- [ ] SEC-005: Revisão de null-safety em contratos de dados

**Responsável:** security_agent  
**Estimativa:** 2 dias  
**Paralelização:** ✅ (executar automaticamente após ondas)
