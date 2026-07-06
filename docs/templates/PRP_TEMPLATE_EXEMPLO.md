# TEMPLATE_PRP_EXEMPLO.md
# Template preenchido com exemplo funcional

# PRP-001: Cadastro Básico de Usuários

## §1 Visão Geral

**PRP:** PRP-001  
**Módulo:** MOD-PLN-001  
**Estimativa:** 3 dias  
**Complexidade:** Baixa  
**Data:** 2026-07-04  
**Responsável:** dev_agent  

### Objetivo
Implementar CRUD básico de usuários com validação de email e senha, servindo como base para autenticação do sistema.

### Escopo Incluso
- Cadastro de usuário com email único e validado
- Login com autenticação JWT
- Listagem de usuários (apenas administradores)
- Edição de perfil (apenas usuário logado)
- Logout e gerenciamento de sessão

### Escopo Excluso
- Recuperação de senha (Será PRP-002)
- Autenticação via OAuth (Será PRP-003)
- Envio de e-mail de confirmação
- Duas-fatores (2FA)

---

## §2 Requisitos RF-RNF

| ID | Tipo | Descrição | Priority | Testes |
|----|------|-----------|----------|--------|
| RF-001 | RF | Sistema deve permitir cadastro de usuário com email válido | High | TEST-001, TEST-003 |
| RF-002 | RF | Sistema deve autenticar usuário com email e senha | High | TEST-002, TEST-003 |
| RF-003 | RF | Sistema deve validar formato de email durante cadastro | Medium | TEST-001 |
| RF-004 | RF | Sistema deve retornar erro 409 ao tentar cadastro com email duplicado | Medium | TEST-003 |
| RNF-001 | RNF | Resposta de API deve ser menor que 500ms (p95) | Medium | TEST-004 |
| RNF-002 | RNF | Senhas devem ser hashadas com bcrypt (cost=10) | High | TEST-001 |
| RNF-003 | RNF | Tokens JWT devem expirar em 1 hora | High | TEST-002 |

---

## §3 Data Model

```typescript
// src/users/types.ts
interface User {
  id: string              // UUID v4
  email: string           // Único, validado
  passwordHash: string    // Bcrypt hash
  name?: string           // Opcional
  role: "user" | "admin"  // Padrão: "user"
  createdAt: string       // ISO 8601
  updatedAt: string       // ISO 8601
}
```

```sql
-- prisma/schema.prisma
model User {
  id           String    @id @default(uuid())
  email        String    @unique
  passwordHash String
  name         String?
  role         Role      @default(USER)
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  
  @@map("users")
}

enum Role {
  USER
  ADMIN
}
```

---

## §4 API Endpoints

### POST /users
**Request:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "Senha123!",
  "name": "Nome do Usuário"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "email": "usuario@exemplo.com",
  "name": "Nome do Usuário",
  "role": "user",
  "createdAt": "2026-07-04T12:00:00Z"
}
```

**Response 400:** Erro de validação (email inválido, senha fraca)
**Response 409:** Email já cadastrado

---

### POST /auth/login
**Request:**
```json
{
  "email": "usuario@exemplo.com",
  "password": "Senha123!"
}
```

**Response 200:**
```json
{
  "accessToken": "jwt_token_aqui",
  "refreshToken": "refresh_token_aqui",
  "expiresIn": 3600
}
```

**Response 401:** Credenciais inválidas

---

### GET /users
**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
[
  {
    "id": "uuid",
    "email": "usuario@exemplo.com",
    "name": "Nome do Usuário",
    "role": "user"
  }
]
```

**Response 403:** Usuário não tem permissão (não é admin)

---

## §5 Testes

| ID | Tipo | Descrição | Arquivo | Coverage |
|----|------|-----------|---------|----------|
| TEST-001 | Unit | Validação de email com regex | `src/users/user.test.ts` | 100% |
| TEST-002 | Unit | Hash de senha com bcrypt | `src/users/auth.test.ts` | 100% |
| TEST-003 | Integration | Cadastro de usuário completo | `test/e2e/users.spec.ts` | 80% |
| TEST-004 | Integration | Performance de resposta | `test/perf/users.test.ts` | 100% |

---

## §6 Checklist de Aceitação

- [ ] RF-001: Cadastro com email válido implementado
- [ ] RF-002: Autenticação com email/senha implementada
- [ ] RF-003: Validação de email com regex (ex: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`)
- [ ] RF-004: Erro 409 para email duplicado
- [ ] RNF-001: Tempo de resposta < 500ms (p95)
- [ ] RNF-002: Senhas hashadas com bcrypt cost=10
- [ ] RNF-003: Tokens JWT com expiração de 1 hora
- [ ] TEST-001 a TEST-004: Todos os testes passando
- [ ] Cobertura de código ≥ 80%
- [ ] PR passou security audit (0 críticos)
- [ ] Documentation: README.md atualizado com endpoints

---

## §7 Dependências

| Biblioteca | Uso | Versão |
|------------|-----|--------|
| `@prisma/client` | Schema e queries | `^5.0.0` |
| `bcryptjs` | Hash de senha | `^2.4.3` |
| `jsonwebtoken` | JWT tokens | `^9.0.0` |
| `zod` | Validação | `^3.22.0` |
| `uuid` | IDs únicos | `^9.0.0` |

---

## §8 Checklist de Segurança

- [ ] Senhas nunca são armazenadas em plaintext
- [ ] Tokens JWT são assinados (HS256 ou RS256)
- [ ] Email é validado antes de salvar no banco
- [ ] Erros não expõem informações sensíveis (ex: "Email existe" → "Credenciais inválidas")
- [ ] Rate limiting implementado em `/auth/login`

---

**Status:** Aprovado para implementação  
**Gate:** 👤 4 (Planejamento)  
**Atribuído a:** dev_agent  
**Data de Criação:** 2026-07-04
