# PRP-001: Cadastro Básico de Usuários

## §1 Visão Geral

**PRP:** PRP-001  
**Módulo:** MOD-PLN-001  
**Estimativa:** 3 dias  
**Complexidade:** Baixa  

### Objetivo
Implementar CRUD básico de usuários com validação de email e senha.

### Escopo Incluso
- Cadastro de usuário com email único
- Login com autenticação básica
- Listagem de usuários (apenas administradores)
- Edição de perfil (apenas usuário logado)

### Escopo Excluso
- Recuperação de senha
- Autenticação via OAuth
- Envio de e-mail de confirmação

## §2 Requisitos RF-RNF

| ID | Tipo | Descrição | Priority |
|----|------|-----------|----------|
| RF-001 | RF | Sistema deve permitir cadastro de usuário com email válido | High |
| RF-002 | RF | Sistema deve autenticar usuário com email e senha | High |
| RF-003 | RF | Sistema deve validar formato de email durante cadastro | Medium |
| RNF-001 | RNF | Resposta de API deve ser menor que 500ms (p95) | Medium |
| RNF-002 | RNF | Senhas devem ser hashadas com bcrypt (cost=10) | High |

## §3 Testes

| ID | Tipo | Descrição | Arquivo |
|----|------|-----------|---------|
| TEST-001 | Unit | Validação de email com regex | `src/users/user.test.ts` |
| TEST-002 | Unit | Hash de senha com bcrypt | `src/users/auth.test.ts` |
| TEST-003 | Integration | Cadastro de usuário completo | `test/e2e/users.spec.ts` |

## §4 UI/UX (se aplicável)

Não aplicável (API-only)

## §5 Data Model

```typescript
interface User {
  id: string
  email: string
  passwordHash: string
  createdAt: string
  updatedAt: string
}
```

## §6 Dependências

- `@prisma/client` (para schema)
- `bcryptjs` (para hash de senha)
- `zod` (para validação)

## §7 Checklist de Aceitação

- [ ] RF-001 implementado e testado
- [ ] RF-002 implementado e testado
- [ ] RF-003 implementado com validação no schema Zod
- [ ] RNF-002 implementado com cost=10
- [ ] Testes com cobertura ≥ 80%
- [ ] PR passou security audit (0 críticos)

---

**Status:** Em Planejamento  
**Atribuído a:** Dev Agent  
**Data de Criação:** 2026-07-04
