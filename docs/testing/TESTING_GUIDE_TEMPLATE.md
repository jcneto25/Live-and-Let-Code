# Comprehensive Testing Guide — Guia de Testes Completo

> **Versão:** {X.Y} | **Data:** {YYYY-MM-DD} | **Status:** {Draft / Approved / Archived}
> **Projeto:** {Nome do Projeto} | **Autor:** {Tech Lead / QA Lead}
> **Revisores:** {Senior Dev, DevOps, UX Lead} | **Referências:** `{Development Plan}`, `{PRP-XXX}`, `{Architecture Definition}`

---

## 📋 Checklist Pré-Preenchimento

Este guia é a **fonte da verdade** para todas as práticas de teste do projeto. Antes de usá-lo:
- [ ] Stack de testes definida (Jest, Vitest, Playwright, Detox, etc.)
- [ ] CI/CD configurado para rodar testes automaticamente
- [ ] Banco de dados de teste configurado (Docker/Testcontainers)
- [ ] Mock Service Worker (MSW) instalado para frontend/mobile
- [ ] jest-axe instalado para acessibilidade
- [ ] Time treinado no ciclo Red-Green-Refactor
- [ ] Template de testes revisado e disponível em `docs/testing/templates/`

---

## 1. Visão Geral e Filosofia

### 1.1 Propósito
Este guia define **como** testamos no projeto — desde a filosofia até o código. Ele serve para:
- **Padronizar** práticas de teste entre todos os devs (backend, frontend, mobile)
- **Eliminar ambiguidade** sobre quando mockar vs. usar banco real
- **Acelerar** desenvolvimento com TDD estruturado e templates
- **Garantir qualidade** com acessibilidade, performance e regressão

> **Exemplo (NeuroHub):** *"Guia de testes para 3 apps (API NestJS, Web React, Mobile RN) com TDD formalizado, MSW para network mocking, jest-axe para a11y, e Prisma 7 com banco de testes Docker."*

### 1.2 Princípios Fundamentais

| Princípio | Definição | Aplicação |
|-----------|-----------|-----------|
| **TDD Obrigatório** | Testes antes do código, sempre | Nenhum PRP sem test strategy preenchida |
| **Red-Green-Refactor** | Ciclo formal: teste falha → código mínimo → refatora | Documentado em cada template |
| **Mock com Propósito** | Mockar é decisão, não default | Árvore de decisão na seção 5 |
| **Acessibilidade é Testável** | axe-core em todo componente UI | jest-axe no setup de testes |
| **Testes como Documentação** | Testes descrevem comportamento esperado | Gherkin nos nomes de teste |
| **CI é Gate** | Nada mergeia sem testes passando | Pipeline bloqueia PR se falhar |

### 1.3 Pirâmide de Testes

```
        /\
       /  \
      / E2E \      ← Poucos, lentos, caros (Playwright, Detox, Maestro)
     /─────────\
    / Integration \  ← Médios (Supertest, MSW + React Testing Library)
   /────────────────\
  /     Unit Tests     \ ← Muitos, rápidos, baratos (Jest, Vitest)
 /────────────────────────\
```

| Nível | Quantidade | Velocidade | Custo | Ferramentas | Cobertura alvo |
|-------|-----------|------------|-------|-------------|----------------|
| **Unit** | 70% | < 100ms cada | Baixo | Jest, Vitest | 80% linhas |
| **Integration** | 20% | < 1s cada | Médio | Supertest, MSW, RTL | APIs principais |
| **E2E** | 10% | < 30s cada | Alto | Playwright, Detox | Fluxos críticos |

---

## 2. TDD com Red-Green-Refactor

### 2.1 O Ciclo

```
┌─────────────────────────────────────────────────────────────┐
│                    TDD com Assistente IA                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. DEV SOLICITA FEATURE                                     │
│     "Adicionar endpoint de criação de usuário"               │
│            │                                                 │
│            ▼                                                 │
│  2. IA GERA TESTE (RED)                                      │
│     ✅ users.service.spec.ts → falha (esperado)            │
│            │                                                 │
│            ▼                                                 │
│  3. DEV REVISA TESTE                                       │
│     - Comportamento está correto?                           │
│     - Edge cases cobertos?                                  │
│     - Factories/mocks adequados?                            │
│            │                                                 │
│            ▼                                                 │
│  4. IA GERA IMPLEMENTAÇÃO (GREEN)                          │
│     ✅ users.service.ts → código mínimo para passar        │
│            │                                                 │
│            ▼                                                 │
│  5. IA SUGERE REFATORAÇÃO                                  │
│     ✅ Extrair validação → validateUserDto()             │
│            │                                                 │
│            ▼                                                 │
│  6. DEV APROVA REFATORAÇÃO                                 │
│     ✅ Testes continuam verdes                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Prompts para IA (Templates)

#### Prompt para Teste de Service (Backend)

```markdown
Seguindo TDD, crie um teste para {UsersService.findAll()}:

1. Escreva {users.service.spec.ts} com describe 'findAll'
2. Casos de teste:
   - Retorna todos os usuários da organização
   - Filtra por role quando parâmetro fornecido
   - Retorna array vazio quando não há usuários
   - Lança erro quando banco está indisponível
3. Use {getTestPrisma()} helper para DB real
4. Limpe dados no beforeEach
5. Use factories: {createUser(), createOrganization()}

Mostre o arquivo de teste primeiro. Aprovarei antes de você escrever o service.
```

#### Prompt para Teste de Componente (Web)

```markdown
Seguindo TDD, crie um teste para {UserList} component:

1. Escreva {UserList.test.tsx}
2. Use MSW para mockar GET {/api/users}
3. Casos de teste:
   - Mostra loading state inicialmente
   - Exibe usuários quando carregado
   - Mostra mensagem de erro em falha
   - Passa em verificação de acessibilidade (axe)
4. Use Testing Library queries ({getByRole, queryByText})
5. Teste keyboard navigation

Mostre o arquivo de teste primeiro.
```

#### Prompt para Teste de Hook

```markdown
Seguindo TDD, crie um teste para {useUsers} hook:

1. Escreva {useUsers.test.tsx}
2. Use {renderHook} de @testing-library/react
3. MSW mock para GET {/api/users}
4. Casos de teste:
   - Fetches users on mount
   - Refetch quando {refetch()} chamado
   - Trata erros gracefully
   - Mostra loading state

Mostre o teste primeiro, depois a implementação.
```

### 2.3 Red Flags de IA (Quando Interromper)

| IA Diz | Problema | Resposta Correta |
|--------|----------|------------------|
| "Testes não são necessários para isso" | Viola TDD | "Escreva testes primeiro, é nosso padrão" |
| "Vou criar teste e código juntos" | Bypassa revisão | "Mostre o teste primeiro, aprovo antes do código" |
| "Isso é muito simples para testar" | Mindset errado | "Mesmo código simples precisa de proteção contra regressão" |
| "Vou adicionar algumas features extras" | Scope creep | "Fique no que o teste especifica" |
| "Vou mockar o banco localmente no teste" | Padrão errado | "Use {getTestPrisma()} helper ao invés de mock manual" |

---

## 3. Setup por Aplicação

### 3.1 Backend API (`apps/api/`)

#### Stack

| Ferramenta | Versão | Uso | Config |
|------------|--------|-----|--------|
| Jest | latest | Unit + Integration | `jest.config.ts` |
| jest-mock-extended | latest | Mock de services | `mockDeep<T>()` |
| Supertest | latest | E2E HTTP | `request(app)` |
| Prisma 7 | latest | ORM + Test DB | `prisma.config.ts` |
| Docker Compose | — | Banco de testes | `docker-compose.test.yml` |

#### Estrutura de Testes

```
apps/api/
├── src/
│   ├── {modulo}/
│   │   ├── {modulo}.service.ts
│   │   ├── {modulo}.service.spec.ts      ← Unit (mock Prisma)
│   │   ├── {modulo}.controller.ts
│   │   ├── {modulo}.controller.spec.ts   ← Unit (mock Service)
│   │   └── dto/
│   ├── test-helpers/
│   │   ├── factories/
│   │   │   ├── user.factory.ts
│   │   │   ├── patient.factory.ts
│   │   │   └── organization.factory.ts
│   │   ├── mocks/
│   │   │   ├── auth.mock.ts              ← MockJwtAuthGuard
│   │   │   └── prisma.mock.ts            ← MockPrismaClient
│   │   └── setup/
│   │       └── test-prisma.ts            ← getTestPrisma(), setupTestDatabase()
│   └── prisma/
│       ├── schema.prisma
│       └── seed.test.ts                  ← Dados de teste
├── test/
│   └── {modulo}.e2e-spec.ts              ← E2E (Supertest + Test DB)
├── docker-compose.test.yml               ← PostgreSQL teste
├── jest.config.ts
├── jest.setup.ts                         ← Mock global de auth guards
└── package.json
```

#### Configuração Prisma 7 para Testes

```typescript
// src/test-helpers/setup/test-prisma.ts
import 'dotenv/config';
import { PrismaClient } from '@prisma/client';
import { PrismaPg } from '@prisma/adapter-pg';

/**
 * Prisma 7 — Setup de banco de testes
 *
 * Usa Docker Compose test database na porta 5433
 * Fallback para DATABASE_URL se não setado
 */
const getTestConnectionString = () => {
  return process.env.DATABASE_URL || 'postgresql://test:test@localhost:5433/{projeto}_test';
};

export const getTestPrisma = () => {
  const adapter = new PrismaPg({
    connectionString: getTestConnectionString(),
  });
  return new PrismaClient({ adapter });
};

/**
 * Limpa todas as tabelas (exceto _prisma_migrations)
 * em uma única query, bypassando FK constraints
 */
export async function setupTestDatabase() {
  const prisma = getTestPrisma();
  await prisma.$connect();

  const tables = await prisma.$queryRawUnsafe<{ string_agg: string }[]>(`
    SELECT string_agg(quote_ident(tablename), ', ')
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename != '_prisma_migrations';
  `);

  if (tables[0]?.string_agg) {
    await prisma.$executeRawUnsafe(`TRUNCATE TABLE ${tables[0].string_agg} CASCADE;`);
  }

  return prisma;
}

export async function teardownTestDatabase(prisma: PrismaClient) {
  await prisma.$disconnect();
}
```

#### Mock de Auth Guards (Global)

```typescript
// src/test-helpers/mocks/auth.mock.ts
import { ExecutionContext } from '@nestjs/common';

/**
 * Mock JWT Auth Guard para testes
 * Bypassa autenticação e injeta usuário mock
 */
export const MockJwtAuthGuard = {
  canActivate: (context: ExecutionContext) => {
    const req = context.switchToHttp().getRequest();
    req.user = mockCurrentUser();
    return true;
  },
};

/**
 * Mock Roles Guard para testes
 * Bypassa verificação de roles (sempre permite)
 */
export const MockRolesGuard = {
  canActivate: () => true,
};

/**
 * Cria usuário mock para testes
 */
export const mockCurrentUser = (overrides = {}) => ({
  id: 'test-user-id',
  email: 'test@test.com',
  name: 'Test User',
  role: 'ADMIN',
  organizationId: 'test-org-id',
  ...overrides,
});
```

```typescript
// jest.setup.ts — Mock global de guards
import { MockJwtAuthGuard, MockRolesGuard } from './src/test-helpers/mocks/auth.mock';

jest.mock('../src/auth/guards/jwt-auth.guard', () => ({
  JwtAuthGuard: jest.fn(() => ({
    canActivate: jest.fn(() => true),
  })),
}));

jest.mock('../src/auth/guards/roles.guard', () => ({
  RolesGuard: jest.fn(() => ({
    canActivate: jest.fn(() => true),
  })),
}));
```

#### Docker Compose para Testes

```yaml
# docker-compose.test.yml
services:
  postgres_test:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: {projeto}_test
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test"]
      interval: 5s
      timeout: 5s
      retries: 5
```

```bash
# Setup do banco de testes
docker-compose -f docker-compose.test.yml up -d
DATABASE_URL="postgresql://test:test@localhost:5433/{projeto}_test" npm test
```

---

### 3.2 Frontend Web (`apps/web/`)

#### Stack

| Ferramenta | Versão | Uso | Config |
|------------|--------|-----|--------|
| Vitest | latest | Unit + Integration | `vitest.config.ts` |
| React Testing Library | latest | Component + Hook tests | `@testing-library/react` |
| MSW | latest | Network mocking | `src/mocks/` |
| jest-axe | latest | Acessibilidade | `vitest-setup.ts` |
| jsdom | latest | DOM environment | `environment: 'jsdom'` |

#### Estrutura de Testes

```
apps/web/
├── src/
│   ├── mocks/
│   │   ├── server.ts              ← MSW server setup
│   │   └── handlers.ts            ← Handlers centralizados
│   ├── components/
│   │   ├── {Component}/
│   │   │   ├── {Component}.tsx
│   │   │   └── {Component}.test.tsx
│   ├── hooks/
│   │   ├── use{Domain}.ts
│   │   └── use{Domain}.test.ts
│   └── test-helpers/
│       ├── render.tsx             ← Render com providers
│       └── fixtures/              ← Dados mock
├── vitest.config.ts
├── vitest-setup.ts                ← MSW + jest-axe setup
└── package.json
```

#### Configuração Vitest + MSW + jest-axe

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./vitest-setup.ts'],
    deps: {
      moduleDirectories: ['node_modules', '../packages/ui/node_modules'],
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: {
        statements: 80,
        branches: 70,
        functions: 80,
        lines: 80,
      },
    },
  },
});
```

```typescript
// vitest-setup.ts
import { beforeAll, afterEach, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';
import { server } from './src/mocks/server';
import { toHaveNoViolations } from 'jest-axe';

// Estende Vitest expect com jest-axe
expect.extend({ toHaveNoViolations });

// MSW setup
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  server.resetHandlers();
  cleanup();
});
afterAll(() => server.close());
```

#### MSW Handlers Centralizados

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';
import { mockUser, mockPatient, mockGoal } from '../test-helpers/fixtures';

export const handlers = [
  // Auth
  http.post('/api/auth/login', () => {
    return HttpResponse.json({ token: 'mock-token', user: mockUser });
  }),

  // Users
  http.get('/api/users', () => {
    return HttpResponse.json({ users: [mockUser] });
  }),
  http.post('/api/users', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: crypto.randomUUID(), ...body }, { status: 201 });
  }),

  // Patients
  http.get('/api/patients', () => {
    return HttpResponse.json({ patients: [mockPatient] });
  }),

  // Goals/PEI
  http.get('/api/goals', () => {
    return HttpResponse.json({ goals: [mockGoal] });
  }),

  // Error example
  http.get('/api/users/error', () => {
    return HttpResponse.json({ error: 'Server Error' }, { status: 500 });
  }),
];
```

```typescript
// src/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

---

### 3.3 Mobile (`apps/mobile/`)

#### Stack

| Ferramenta | Versão | Uso | Config |
|------------|--------|-----|--------|
| Jest | latest | Unit + Integration | `jest.config.js` |
| React Native Testing Library | latest | Component tests | `@testing-library/react-native` |
| MSW | latest | Network mocking | `src/mocks/` |
| NativeWind | latest | Estilização | — |

#### Estrutura de Testes

```
apps/mobile/
├── src/
│   ├── mocks/
│   │   ├── server.ts              ← MSW server (native)
│   │   └── handlers.ts            ← Shared ou mobile-specific
│   ├── screens/
│   │   ├── {Screen}.tsx
│   │   └── {Screen}.test.tsx
│   ├── database/
│   │   ├── schema.ts
│   │   └── __tests__/
│   │       └── schema.test.ts
│   └── test-helpers/
│       ├── mocks/
│       │   └── database.mock.ts   ← Mock WatermelonDB
│       └── fixtures/
├── jest.config.js
└── package.json
```

---

## 4. Templates de Teste

### 4.1 Backend — Service Test

```typescript
// {modulo}.service.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { {Modulo}Service } from './{modulo}.service';
import { getTestPrisma, setupTestDatabase, teardownTestDatabase } from '../test-helpers/setup/test-prisma';
import { createOrganization, createUser } from '../test-helpers/factories';

describe('{Modulo}Service', () => {
  let service: {Modulo}Service;
  let prisma: ReturnType<typeof getTestPrisma>;

  beforeAll(async () => {
    prisma = await setupTestDatabase();
    const module: TestingModule = await Test.createTestingModule({
      providers: [{Modulo}Service, { provide: 'PrismaService', useValue: prisma }],
    }).compile();
    service = module.get<{Modulo}Service>({Modulo}Service);
  });

  afterEach(async () => {
    // Clean specific tables or use setupTestDatabase cleanup
  });

  afterAll(async () => {
    await teardownTestDatabase(prisma);
  });

  describe('create', () => {
    it('should create {entidade} with valid data', async () => {
      // Arrange
      const org = await createOrganization(prisma);
      const data = { name: 'Test', organizationId: org.id };

      // Act
      const result = await service.create(data);

      // Assert
      expect(result).toHaveProperty('id');
      expect(result.name).toBe('Test');
      expect(result.organizationId).toBe(org.id);
    });

    it('should throw when name is missing', async () => {
      // Arrange
      const data = { name: '' };

      // Act & Assert
      await expect(service.create(data)).rejects.toThrow('Name is required');
    });

    it('should throw when duplicate {campo único}', async () => {
      // Arrange
      const org = await createOrganization(prisma);
      const existing = await service.create({ name: 'Duplicate', organizationId: org.id });

      // Act & Assert
      await expect(service.create({ name: 'Duplicate', organizationId: org.id }))
        .rejects.toThrow('already exists');
    });
  });

  describe('findAll', () => {
    it('should return all {entidades} for organization', async () => {
      // Arrange
      const org = await createOrganization(prisma);
      await service.create({ name: 'A', organizationId: org.id });
      await service.create({ name: 'B', organizationId: org.id });

      // Act
      const result = await service.findAll({ organizationId: org.id });

      // Assert
      expect(result).toHaveLength(2);
      expect(result[0].organizationId).toBe(org.id);
    });

    it('should return empty array when no {entidades}', async () => {
      // Arrange
      const org = await createOrganization(prisma);

      // Act
      const result = await service.findAll({ organizationId: org.id });

      // Assert
      expect(result).toEqual([]);
    });
  });

  describe('update', () => {
    it('should update {entidade} and return updated', async () => {
      // Arrange
      const org = await createOrganization(prisma);
      const created = await service.create({ name: 'Old', organizationId: org.id });

      // Act
      const result = await service.update(created.id, { name: 'New' });

      // Assert
      expect(result.name).toBe('New');
    });
  });

  describe('delete', () => {
    it('should remove {entidade} and return success', async () => {
      // Arrange
      const org = await createOrganization(prisma);
      const created = await service.create({ name: 'ToDelete', organizationId: org.id });

      // Act
      await service.remove(created.id);

      // Assert
      const found = await service.findOne(created.id);
      expect(found).toBeNull();
    });
  });
});
```

### 4.2 Backend — Controller Test (com mock de Service)

```typescript
// {modulo}.controller.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { {Modulo}Controller } from './{modulo}.controller';
import { {Modulo}Service } from './{modulo}.service';
import { mockDeep } from 'jest-mock-extended';

describe('{Modulo}Controller', () => {
  let controller: {Modulo}Controller;
  const mockService = mockDeep<{Modulo}Service>();

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [{Modulo}Controller],
      providers: [{ provide: {Modulo}Service, useValue: mockService }],
    }).compile();
    controller = module.get<{Modulo}Controller>({Modulo}Controller);
  });

  describe('POST /{modulo}', () => {
    it('should return 201 with created {entidade}', async () => {
      // Arrange
      const dto = { name: 'Test' };
      mockService.create.mockResolvedValue({ id: '1', ...dto });

      // Act
      const result = await controller.create(dto);

      // Assert
      expect(result).toEqual({ id: '1', name: 'Test' });
      expect(mockService.create).toHaveBeenCalledWith(dto);
    });

    it('should return 400 for invalid email', async () => {
      // Arrange
      const dto = { email: 'invalid' };
      mockService.create.mockRejectedValue(new BadRequestException('Invalid email'));

      // Act & Assert
      await expect(controller.create(dto)).rejects.toThrow(BadRequestException);
    });

    it('should return 409 for duplicate', async () => {
      // Arrange
      const dto = { name: 'Duplicate' };
      mockService.create.mockRejectedValue(new ConflictException('Already exists'));

      // Act & Assert
      await expect(controller.create(dto)).rejects.toThrow(ConflictException);
    });
  });

  describe('GET /{modulo}', () => {
    it('should require ADMIN role', async () => {
      // Arrange
      mockService.findAll.mockResolvedValue([]);

      // Act
      const result = await controller.findAll();

      // Assert
      expect(result).toEqual([]);
    });
  });
});
```

### 4.3 Web — Component Test (com MSW + jest-axe)

```typescript
// {Component}.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { axe } from 'jest-axe';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import { {Component} } from './{Component}';
import { mockUser } from '../test-helpers/fixtures';

describe('{Component}', () => {
  // Setup
  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  describe('happy path', () => {
    it('renders with data from API', async () => {
      // Arrange
      server.use(
        http.get('/api/users', () => HttpResponse.json({ users: [mockUser] }))
      );

      // Act
      render(<{Component} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(mockUser.name)).toBeInTheDocument();
      });
    });

    it('handles user interaction', async () => {
      // Arrange
      const onSubmit = jest.fn();
      render(<{Component} onSubmit={onSubmit} />);

      // Act
      fireEvent.click(screen.getByRole('button', { name: /submit/i }));

      // Assert
      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalled();
      });
    });
  });

  describe('loading state', () => {
    it('shows skeleton while loading', () => {
      // Arrange
      server.use(
        http.get('/api/users', async () => {
          await new Promise(r => setTimeout(r, 1000));
          return HttpResponse.json({ users: [] });
        })
      );

      // Act
      render(<{Component} />);

      // Assert
      expect(screen.getByRole('status')).toBeInTheDocument(); // Skeleton
    });
  });

  describe('error state', () => {
    it('shows error message on API failure', async () => {
      // Arrange
      server.use(
        http.get('/api/users', () => HttpResponse.json(null, { status: 500 }))
      );

      // Act
      render(<{Component} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });

  describe('empty state', () => {
    it('shows empty message when no data', async () => {
      // Arrange
      server.use(http.get('/api/users', () => HttpResponse.json({ users: [] })));

      // Act
      render(<{Component} />);

      // Assert
      await waitFor(() => {
        expect(screen.getByText(/no users/i)).toBeInTheDocument();
      });
    });
  });

  describe('accessibility', () => {
    it('has no axe violations', async () => {
      // Arrange
      server.use(http.get('/api/users', () => HttpResponse.json({ users: [mockUser] })));
      const { container } = render(<{Component} />);

      // Act & Assert
      await waitFor(() => screen.getByText(mockUser.name));
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it('supports keyboard navigation', () => {
      // Arrange
      render(<{Component} />);
      const button = screen.getByRole('button', { name: /add user/i });

      // Act
      button.focus();
      fireEvent.keyDown(button, { key: 'Tab' });

      // Assert
      expect(document.activeElement).toBe(screen.getByRole('searchbox'));
    });

    it('announces dynamic changes to screen readers', async () => {
      // Arrange
      render(<{Component} />);

      // Assert
      expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite');
    });
  });
});
```

### 4.4 Web — Hook Test

```typescript
// use{Domain}.test.ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { server } from '../mocks/server';
import { http, HttpResponse } from 'msw';
import { use{Domain} } from './use{Domain}';

describe('use{Domain}', () => {
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  it('fetches data on mount', async () => {
    // Arrange
    server.use(http.get('/api/{endpoint}', () => HttpResponse.json({ data: 'mock' })));

    // Act
    const { result } = renderHook(() => use{Domain}());

    // Assert
    await waitFor(() => {
      expect(result.current.data).toEqual('mock');
    });
  });

  it('refetches when refetch() called', async () => {
    // Arrange
    let callCount = 0;
    server.use(
      http.get('/api/{endpoint}', () => {
        callCount++;
        return HttpResponse.json({ data: `call-${callCount}` });
      })
    );
    const { result } = renderHook(() => use{Domain}());
    await waitFor(() => expect(result.current.data).toBeDefined());

    // Act
    act(() => { result.current.refetch(); });

    // Assert
    await waitFor(() => {
      expect(result.current.data).toEqual('call-2');
    });
  });

  it('handles errors gracefully', async () => {
    // Arrange
    server.use(http.get('/api/{endpoint}', () => HttpResponse.json(null, { status: 500 })));

    // Act
    const { result } = renderHook(() => use{Domain}());

    // Assert
    await waitFor(() => {
      expect(result.current.error).toBeDefined();
      expect(result.current.isError).toBe(true);
    });
  });

  it('shows loading state', () => {
    // Arrange
    server.use(http.get('/api/{endpoint}', () => HttpResponse.json({ data: 'mock' })));

    // Act
    const { result } = renderHook(() => use{Domain}());

    // Assert
    expect(result.current.isLoading).toBe(true);
  });
});
```

### 4.5 Mobile — Component Test

```typescript
// {Screen}.test.tsx
import { render, screen, fireEvent } from '@testing-library/react-native';
import { {Screen} } from './{Screen}';

describe('{Screen}', () => {
  it('renders patient name and age', () => {
    // Arrange
    const patient = { name: 'João', age: 8 };

    // Act
    render(<{Screen} patient={patient} />);

    // Assert
    expect(screen.getByText('João')).toBeTruthy();
    expect(screen.getByText('8 anos')).toBeTruthy();
  });

  it('shows last session date', () => {
    // Arrange
    const patient = { lastSession: '2026-06-01' };

    // Act
    render(<{Screen} patient={patient} />);

    // Assert
    expect(screen.getByText('Última sessão: 01/06/2026')).toBeTruthy();
  });

  it('handles loading state', () => {
    // Act
    render(<{Screen} isLoading />);

    // Assert
    expect(screen.getByAccessibilityHint('Carregando')).toBeTruthy();
  });

  it('has accessible labels for icon-only buttons', () => {
    // Act
    render(<{Screen} />);

    // Assert
    expect(screen.getByLabelText('Editar paciente')).toBeTruthy();
  });
});
```

### 4.6 Mobile — Offline Sync Test

```typescript
// useSyncManager.test.ts
import { renderHook, act } from '@testing-library/react';
import { useSyncManager } from './useSyncManager';
import { mockDatabase } from '../test-helpers/mocks/database.mock';

describe('Offline Sync', () => {
  beforeEach(async () => {
    const db = await mockDatabase();
    await db.unsafeResetDatabase();
  });

  it('queues changes when offline', async () => {
    // Arrange — Mock NetInfo offline
    jest.mock('@react-native-community/netinfo', () => ({
      fetch: () => Promise.resolve({ isConnected: false, isInternetReachable: false }),
    }));

    const { result } = renderHook(() => useSyncManager());

    // Act
    act(() => { result.current.createPatient({ name: 'Test Patient' }); });

    // Assert
    const pendingSync = await result.current.getPendingSync();
    expect(pendingSync.length).toBe(1);
    expect(pendingSync[0].action).toBe('CREATE');
    expect(pendingSync[0].entity).toBe('patient');
  });

  it('syncs when connection restored', async () => {
    // Arrange — Simula reconexão
    const netInfoMock = jest.fn()
      .mockResolvedValueOnce({ isConnected: false })
      .mockResolvedValueOnce({ isConnected: true });

    jest.mock('@react-native-community/netinfo', () => ({
      fetch: netInfoMock,
      addEventListener: (callback) => {
        setTimeout(() => callback({ isConnected: true }), 100);
        return { remove: () => {} };
      },
    }));

    const { result } = renderHook(() => useSyncManager());
    act(() => { result.current.createPatient({ name: 'Test Patient' }); });

    // Assert
    await waitFor(() => {
      expect(result.current.syncStatus).toBe('synced');
    });
  });

  it('resolves conflicts using last-write-wins', async () => {
    // Arrange
    const localPatient = { id: '1', name: 'Local Name', updatedAt: '2026-06-03T00:00:00Z' };
    const remotePatient = { id: '1', name: 'Remote Name', updatedAt: '2026-06-02T00:00:00Z' };

    const { result } = renderHook(() => useSyncManager());

    // Act
    const resolved = await result.current.resolveConflict(localPatient, remotePatient);

    // Assert — timestamp mais recente ganha
    expect(resolved.name).toBe('Local Name');
    expect(resolved._conflictResolved).toBe(true);
  });
});
```

---

## 5. Estratégia de Mock: Quando Mockar vs. Quando Usar Real

### 5.1 Árvore de Decisão

```
┌─────────────────────────────────────────────────────────────┐
│              Árvore de Decisão: Mock vs. Real              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Testando lógica pura de negócio?                           │
│       │                                                       │
│       ├─ Sim → MOCK Prisma (jest-mock-extended)              │
│       │         ✅ Rápido, sem DB                           │
│       │         ✅ Determinístico                           │
│       │         ❌ Não testa queries reais                  │
│       │                                                       │
│       └─ Não → Testando interação com DB?                  │
│                  │                                          │
│                  ├─ Sim → DB Real (Docker/Testcontainers)  │
│                  │         ✅ Testa queries reais            │
│                  │         ✅ Pega erros de schema           │
│                  │         ❌ Mais lento, requer setup       │
│                  │                                          │
│                  └─ Não → Teste de integração (Supertest)   │
│                            ✅ Stack HTTP completa           │
│                            ❌ Mais lento, mais pesado       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Regras por Tipo de Teste

| Tipo de Teste | Mock Prisma? | Mock Service? | Mock Auth? | Banco |
|---------------|--------------|---------------|------------|-------|
| **Service Unit** | Sim (jest-mock-extended) | N/A | N/A | Nenhum |
| **Controller Unit** | N/A | Sim (mockDeep) | Sim (MockJwtAuthGuard) | Nenhum |
| **Integration (API)** | Não | Não | Não (JWT real) | Test DB (Docker) |
| **E2E (Supertest)** | Não | Não | Não (JWT real) | Test DB (Docker) |
| **Component (Web)** | N/A | N/A | N/A | N/A — MSW intercepta HTTP |
| **Hook (Web)** | N/A | N/A | N/A | N/A — MSW intercepta HTTP |
| **Component (Mobile)** | N/A | N/A | N/A | N/A — MSW ou mock local |

### 5.3 Exemplos de Mock

#### Mock de Prisma (jest-mock-extended)

```typescript
import { mockDeep } from 'jest-mock-extended';
import { PrismaClient } from '@prisma/client';

const mockPrisma = mockDeep<PrismaClient>();

// Setup
mockPrisma.user.findMany.mockResolvedValue([{ id: '1', name: 'Test' }]);
mockPrisma.user.create.mockResolvedValue({ id: '1', name: 'New' });
mockPrisma.user.update.mockResolvedValue({ id: '1', name: 'Updated' });
mockPrisma.user.delete.mockResolvedValue({ id: '1', name: 'Deleted' });

// Uso no teste
const service = new UsersService(mockPrisma);
const result = await service.findAll();
expect(result).toHaveLength(1);
```

#### Mock de Service (Controller Test)

```typescript
import { mockDeep } from 'jest-mock-extended';
const mockService = mockDeep<UsersService>();

mockService.create.mockResolvedValue({ id: '1', name: 'Test' });
mockService.findAll.mockResolvedValue([]);
mockService.findOne.mockResolvedValue(null);
mockService.update.mockResolvedValue({ id: '1', name: 'Updated' });
mockService.remove.mockResolvedValue(undefined);
```

#### Override de MSW para um Teste

```typescript
it('handles specific error case', () => {
  // Override handler específico para este teste
  server.use(
    http.get('/api/users', () => HttpResponse.json(null, { status: 401 }))
  );

  // Testa comportamento de unauthorized
  render(<UserList />);
  // ...
});
```

---

## 6. Testes de Acessibilidade (a11y)

### 6.1 jest-axe Setup

```typescript
// vitest-setup.ts (Web)
import { toHaveNoViolations } from 'jest-axe';
expect.extend({ toHaveNoViolations });
```

### 6.2 Testes Automatizados (axe)

```typescript
import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import UserCard from './UserCard';

describe('UserCard Accessibility', () => {
  it('has no axe violations', async () => {
    const { container } = render(<UserCard user={{ name: 'Alice', email: 'alice@test.com' }} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### 6.3 Testes Manuais (além do axe)

```typescript
describe('UserList Accessibility', () => {
  it('supports keyboard navigation', () => {
    render(<UserList users={mockUsers} />);
    const addButton = screen.getByRole('button', { name: /add user/i });
    addButton.focus();

    // Tab através de elementos interativos
    fireEvent.keyDown(addButton, { key: 'Tab' });
    expect(document.activeElement).toBe(screen.getByRole('searchbox'));
  });

  it('announces dynamic changes to screen readers', () => {
    render(<UserList users={[]} />);
    // Loading announcement
    expect(screen.getByRole('status')).toHaveAttribute('aria-live', 'polite');

    // Success announcement after load
    waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent('3 users loaded');
    });
  });

  it('provides accessible labels for icon-only buttons', () => {
    render(<UserList users={mockUsers} />);
    const editButton = screen.getByRole('button', { name: /edit user/i });
    expect(editButton).toHaveAttribute('aria-label');
  });

  it('maintains focus after modal close', async () => {
    render(<UserList users={mockUsers} />);
    const triggerButton = screen.getByRole('button', { name: /create user/i });
    triggerButton.focus();

    // Abre modal
    fireEvent.click(triggerButton);
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    // Fecha modal
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    await waitFor(() => {
      expect(triggerButton).toHaveFocus();
    });
  });
});
```

### 6.4 Checklist de Acessibilidade

- [ ] Todas as imagens têm `alt` text
- [ ] Inputs de formulário têm labels associadas (`<label>` ou `aria-label`)
- [ ] Botões têm nomes acessíveis (texto ou `aria-label`)
- [ ] Contraste de cores atende WCAG AA (4.5:1)
- [ ] Navegação por teclado funciona (Tab, Enter, Escape)
- [ ] Screen reader anuncia mudanças de estado (`aria-live`)
- [ ] Atributos ARIA usados corretamente (não over-engineered)
- [ ] Indicadores de foco visíveis
- [ ] Modais têm focus trap e retornam foco ao trigger
- [ ] Mensagens de erro são anunciadas (`aria-describedby`)

---

## 7. Gerenciamento de Dados de Teste

### 7.1 Factories

```typescript
// test-helpers/factories/user.factory.ts
import { faker } from '@faker-js/faker';
import { PrismaClient } from '@prisma/client';

export async function createUser(prisma: PrismaClient, overrides = {}) {
  return prisma.user.create({
    data: {
      email: faker.internet.email(),
      name: faker.person.fullName(),
      passwordHash: faker.string.alphanumeric(60),
      role: 'THERAPIST',
      organizationId: overrides.organizationId || (await createOrganization(prisma)).id,
      ...overrides,
    },
  });
}

export async function createOrganization(prisma: PrismaClient, overrides = {}) {
  return prisma.organization.create({
    data: {
      name: faker.company.name(),
      ...overrides,
    },
  });
}
```

### 7.2 Multi-Tenancy em Testes

```typescript
describe('with test organization', () => {
  let organization: Organization;

  beforeAll(async () => {
    const prisma = getTestPrisma();
    organization = await createOrganization(prisma);
  });

  it('scopes queries by organization', async () => {
    const prisma = getTestPrisma();

    // Cria usuários em orgs diferentes
    await prisma.user.create({
      data: { email: 'user1@test.com', organization_id: organization.id },
    });
    await prisma.user.create({
      data: { email: 'user2@test.com', organization_id: 'other-org-id' },
    });

    // Query deve retornar apenas usuários da org de teste
    const users = await prisma.user.findMany({
      where: { organization_id: organization.id },
    });

    expect(users).toHaveLength(1);
    expect(users[0].email).toBe('user1@test.com');
  });
});
```

### 7.3 Limpeza de Dados

```typescript
// Clean tables em uma query (bypass FK constraints)
export async function cleanDatabase(prisma: PrismaClient) {
  const tables = await prisma.$queryRawUnsafe<{ string_agg: string }[]>(`
    SELECT string_agg(quote_ident(tablename), ', ')
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename != '_prisma_migrations';
  `);

  if (tables[0]?.string_agg) {
    await prisma.$executeRawUnsafe(`TRUNCATE TABLE ${tables[0].string_agg} CASCADE;`);
  }
}
```

---

## 8. CI/CD e Quality Gates

### 8.1 Pipeline de Testes

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: {projeto}_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type Check
        run: npm run type-check

      - name: Unit Tests
        run: npm run test:unit
        env:
          DATABASE_URL: postgresql://test:test@localhost:5433/{projeto}_test

      - name: Integration Tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://test:test@localhost:5433/{projeto}_test

      - name: E2E Tests
        run: npm run test:e2e
        env:
          DATABASE_URL: postgresql://test:test@localhost:5433/{projeto}_test

      - name: Coverage Report
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: true
```

### 8.2 Quality Gates

| Gate | Threshold | Ação se falhar |
|------|-----------|----------------|
| **Lint** | 0 erros | PR bloqueado |
| **Type Check** | 0 erros | PR bloqueado |
| **Unit Coverage** | ≥ 80% linhas | Warning (não bloqueia MVP) |
| **Unit Coverage** | ≥ 80% linhas | PR bloqueado (pós-MVP) |
| **E2E Críticos** | 100% passando | PR bloqueado |
| **Acessibilidade** | 0 violações axe críticas | PR bloqueado |
| **Vulnerabilidades** | 0 críticas | PR bloqueado |

---

## 9. Documentação e Templates

### 9.1 Estrutura de Documentação

```
docs/testing/
├── comprehensive-testing-guide.md      ← ESTE DOCUMENTO
├── test_plan.md                        ← DEPRECATED — referência apenas
├── tdd-patterns.md                     ← DEPRECATED — referência apenas
├── templates/
│   ├── api-service.spec.ts             ← Template de teste de service
│   ├── api-controller.spec.ts          ← Template de teste de controller
│   ├── react-component.test.tsx        ← Template de componente web
│   ├── react-hook.test.tsx             ← Template de hook
│   ├── rn-component.test.tsx           ← Template de componente mobile
│   └── rn-sync.test.ts               ← Template de sync offline
├── coverage-baseline.md                ← Baseline histórico
└── archive/                            ← Documentos antigos (após 2-3 meses)
    ├── test_plan.md
    └── tdd-patterns.md
```

### 9.2 Estratégia de Migração

| Fase | Ação | Prazo |
|------|------|-------|
| 1 | Criar `comprehensive-testing-guide.md` | Imediato |
| 2 | Manter docs antigos com aviso de depreciação | Imediato |
| 3 | Atualizar links em README, CLAUDE.md, etc. | 1 semana |
| 4 | Mover docs antigos para `archive/` | 2-3 meses |

---

## 10. Troubleshooting

### Problemas Comuns e Soluções

| Problema | Causa | Solução |
|----------|-------|---------|
| **Testes falham apenas no CI** | Banco de testes não disponível | Verificar `docker-compose.test.yml` e env vars |
| **MSW não intercepta requests** | Setup incompleto | Verificar `server.listen()` no `vitest-setup.ts` |
| **jest-axe falha silenciosamente** | Setup não feito | Verificar `expect.extend({ toHaveNoViolations })` |
| **Prisma 7 não conecta** | Adapter não configurado | Usar `PrismaPg` adapter com connection string |
| **Mock não funciona** | jest-mock-extended não importado | Verificar `mockDeep<T>()` e `jest.mock()` |
| **Testes lentos (> 1s cada)** | Banco real em testes unitários | Usar mock de Prisma para unit, DB real apenas integration |
| **Flaky tests** | Estado compartilhado entre testes | Usar `beforeEach` para cleanup, evitar dependências entre testes |
| **Coverage não inclui arquivo** | Configuração do provider | Verificar `coverage.provider` no vitest/jest config |

---

## 📌 Revisões do Documento

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 0.1 | {YYYY-MM-DD} | {Autor} | Rascunho inicial — TDD + MSW + jest-axe |
| 0.2 | {YYYY-MM-DD} | {Autor} | Adicionado Prisma 7 setup + Docker Compose |
| 0.3 | {YYYY-MM-DD} | {Autor} | Adicionado mobile sync testing + a11y expandida |
| 1.0 | {YYYY-MM-DD} | {Autor} | Aprovado — guia completo com todos os templates |

---

## ✅ Checklist de Aprovação do Guia

- [ ] Todos os 12 templates de teste revisados e funcionando
- [ ] Prisma 7 test configuration testada com código real
- [ ] Vitest + MSW setup completo (config + setup file + handlers)
- [ ] Auth testing patterns testadas (bypass + authenticated flows)
- [ ] MSW handlers definidos para todos os endpoints principais
- [ ] jest-axe passando em todos os componentes testados
- [ ] Hook test template criado e documentado
- [ ] Prisma testing strategy testada com exemplos reais
- [ ] Docker Compose test database configurado e funcionando
- [ ] TDD cycle documentado com Red-Green-Refactor steps
- [ ] AI prompting guidelines testadas com exemplos reais
- [ ] Mobile sync testing patterns documentadas
- [ ] Test data lifecycle management testada
- [ ] Multi-tenancy test patterns funcionando
- [ ] Accessibility testing expandida além do jest-axe
- [ ] CI/CD pipeline configurada para rodar todos os níveis de teste
- [ ] Quality gates definidos e aplicados
- [ ] Documentação migration strategy definida
- [ ] Time treinado no guia (workshop ou leitura obrigatória)

---

> **Nota:** Este guia é um documento vivo. Atualize sempre que houver mudança de stack, nova ferramenta, ou lição aprendida. A versão no repositório (`docs/testing/comprehensive-testing-guide.md`) é a fonte da verdade. Para especificação de testes de um PRP específico, consulte a seção 8 (Test Strategy) do PRP individual.
