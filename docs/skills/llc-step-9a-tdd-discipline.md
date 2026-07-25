---
name: llc-step-9a-tdd-discipline
description: "Pipeline LLC Step 9a — TDD Discipline Enforcement. Estabelece 7 hard gates de disciplina TDD que o agente carrega antes de gerar qualquer código de produção. Complementa Step 11 (TDD enforcement pós-execução) com prevenção proativa: ciclo RED→GREEN→REFACTOR, estratégias de Beck, templates AAA/GIVEN-WHEN-THEN, triangulação, anti-padrões e checklist F.I.R.S.T."
version: 1.0.0
tags: [tdd, testing, red-green-refactor, tests, quality, coverage, beck, triangulation, mocks, first, llc-pipeline]
---

# LLC Skill: Step 9a — TDD Discipline Enforcement

**Pipeline:** Live and Let Code (LLC)
**Fase:** Quality Foundation (sub-step of Step 9 — Testing Docs)
**Depende de:** Step 9 (Testing Docs validado)
**Executa antes de:** Step 10 (Documentos do Projeto), Step 11 (Execução dos PRPs)
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-9a-tdd-discipline` ou "Execute a skill llc-step-9a-tdd-discipline".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 9a --task "Enforcar TDD Discipline"`.

---

## 📋 Pré-requisitos

- [ ] `docs/testing/TESTING_GUIDE.md` — guia de testes com stack e ferramentas (Step 9)
- [ ] `docs/testing/COVERAGE_BASELINE.md` — baseline de cobertura (Step 9)
- [ ] `docs/architecture/ARCHITECTURE.md` — stack, frameworks, ferramentas (Step 5)
- [ ] `docs/planning/TASKS.md` — tarefas priorizadas com critérios de aceitação (Step 6)
- [ ] `docs/prps/PRP-*.md` — PRPs com requisitos testáveis (Step 3)

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 9a** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-9a.md`:
     ```markdown
     # Skip Note: Step 9a — TDD Discipline Enforcement
     **Decisão:** Step pulado — disciplina TDD e regras de teste inalteradas desde última execução.
     **Evidência:** Nenhum placeholder test encontrado; `npm test` passa; cobertura mantida.
     **Validador:** [Nome] | **Data:** [YYYY-MM-DD]
     ```
   - **Não execute** as verificações nem aguarde Gate 9a.
   - Avance para Step 10.
3. Se DELTA_REPORT.md não existir: prossiga normalmente.

---

## 🎯 OBJETIVO

Estabelecer disciplina TDD **antes** da geração de código, garantindo que todo código de produção nasça de um teste falhando (RED) e passe por refatoração (REFACTOR). Complementa a detecção reativa do Step 11 (TDD enforcement pós-execução).

**Princípio fundamental:** Se não há teste falhando, não há autorização para escrever código de produção.

Esta skill atua em 5 frentes:

| Frente | Descrição | Referência |
|--------|-----------|------------|
| **Hard Gates** | 7 regras intransponíveis que o agente NUNCA deve violar | Kent Beck, TDD by Example |
| **RED → GREEN → REFACTOR** | Ciclo canônico com commits por fase | Beck (2003) |
| **Estratégias de Beck** | 4 caminhos para chegar ao GREEN | Beck (2003) |
| **Anti-padrões** | 6 erros comuns de teste documentados com exemplos ❌/✅ | Meszaros (2007) |
| **Checklist F.I.R.S.T.** | Validação por teste: Fast, Independent, Repeatable, Self-validating, Timely | Clean Code (Martin, 2009) |

---

## 🛑 1. Hard Gates (Regras Intransponíveis)

*O agente NUNCA deve:*

1. **NUNCA** escrever código de produção antes do teste falhando (RED).
   - Ciclo estrito: RED (teste falha) → GREEN (código mínimo) → REFACTOR (melhoria sem quebrar).
   - Se o teste já passa sem código novo, o teste está errado ou já existe implementação.
   - Commit separado por fase: `test: RED — [nome do teste]` → `feat: GREEN — [implementação mínima]` → `refactor: [melhoria]`.

2. **NUNCA** criar testes com `expect(true).toBe(true)`, `it()` vazio, ou qualquer placeholder que passe sem validar comportamento.
   - Um teste sem asserção real é **dívida técnica ativa** — falsa sensação de cobertura.
   - Placeholders devem ser detectados pelo pre-commit hook `pre-commit-tests.sh`.
   - Exceção: `it.todo('descrição')` com ticket documentado (`TODO(#123)`).

3. **NUNCA** usar `setTimeout`/`sleep`/`wait()` arbitrário em testes para esperar condições assíncronas.
   - Backend: usar `waitFor()` (Testing Library) ou polling com timeout explícito.
   - Frontend: usar `findBy*`, `waitFor`, `waitForElementToBeRemoved`.
   - O tempo de espera deve ser determinístico — esperar por **estado**, não por **tempo**.

4. **NUNCA** mockar por implementação (ex: mock de roteamento por string SQL, mock de `useState` interno).
   - Mockar por **contrato** (interface), não por implementação (detalhe interno).
   - Exemplo ❌: `jest.spyOn(router, 'query').mockReturnValue('SELECT * FROM users')` — mock atrelado ao SQL.
   - Exemplo ✅: `jest.spyOn(userRepository, 'findAll').mockResolvedValue([mockUser])` — mock atrelado ao contrato.
   - Se o mock quebra quando a implementação muda sem mudar o contrato, o mock está errado.

5. **NUNCA** escrever testes dependentes de ordem de execução.
   - Cada teste deve poder rodar isoladamente, em qualquer ordem, em paralelo.
   - Estado compartilhado entre testes = `beforeEach`/`afterEach` para setup/teardown.
   - Se `it('teste B')` falha quando `it('teste A')` não roda antes, o design de teste está quebrado.

6. **NUNCA** usar `it.skip` sem comentário `TODO(#issue)` vinculado a um ticket real.
   - `it.skip` sem rastreabilidade é código morto que será esquecido.
   - Formato obrigatório: `it.skip('descrição' /* TODO(#123): motivo do skip */)`
   - Pre-commit hook deve contar `it.skip` sem `TODO(#\d+)` e emitir warning.

7. **NUNCA** commitar código sem `npm test` (ou equivalente da stack) passando localmente.
   - Pre-commit hook `pre-commit-tests.sh` executa `jest --findRelatedTests` nos arquivos modificados.
   - Se o teste falha, o commit é bloqueado.
   - `--no-verify` só é aceitável em branches WIP — nunca em `main`/`master`.

---

## 🔴🟢🔵 2. O Ciclo RED → GREEN → REFACTOR

O ciclo TDD canônico, com granularidade de commits e comportamentos esperados do agente.

### 2.1 Diagrama do Ciclo

```
┌──────────────────────────────────────────────┐
│                 TDD CYCLE                      │
│                                                │
│   ┌─────────┐     ┌──────────┐     ┌────────┐ │
│   │  🔴 RED  │ ──▶ │ 🟢 GREEN │ ──▶ │ 🔵 REF │ │
│   └─────────┘     └──────────┘     └────────┘ │
│        │                │               │       │
│        ▼                ▼               ▼       │
│  Escreve teste    Código mínimo    Melhora      │
│  que FALHA        que faz passar   sem quebrar  │
│                                          │       │
│                    ◀─────────────────────┘       │
│                         (loop)                   │
└──────────────────────────────────────────────┘
```

### 2.2 Fase RED — Escrever o Teste que Falha

**Objetivo:** Escrever o teste **mínimo** que captura o comportamento desejado e verifica que ele **falha** (porque a implementação não existe).

**Regras:**
- O teste deve falhar pela razão certa (ex: "function not defined", não "typo no nome").
- Use a estratégia de Beck apropriada para decidir qual teste escrever (ver §3).
- Commit message: `test: RED — <descrição do comportamento testado>`
- O teste falhando prova que o teste é capaz de detectar ausência de implementação.

**Template — AAA Pattern (Arrange, Act, Assert):**

```typescript
// ✅ Template AAA para fase RED
describe('UserService.createUser', () => {
  it('should create a user with valid input', () => {
    // Arrange — prepara o mundo
    const input = { name: 'Alice', email: 'alice@example.com' };
    const service = new UserService(mockRepository);

    // Act — executa a ação
    const result = service.createUser(input);

    // Assert — verifica o resultado
    expect(result).toMatchObject({ name: 'Alice', email: 'alice@example.com' });
    expect(result.id).toBeDefined();
    expect(mockRepository.save).toHaveBeenCalledWith(expect.objectContaining({ name: 'Alice' }));
  });
});
```

**Template — GIVEN-WHEN-THEN (BDD-style):**

```typescript
// ✅ Template GIVEN-WHEN-THEN (preferido para comportamento complexo)
describe('OrderService.checkout', () => {
  it('should apply discount for premium users', () => {
    // GIVEN a premium user with items in the cart
    const user = createPremiumUser();
    const cart = createCartWithItems(3);
    mockUserRepo.findById.mockResolvedValue(user);

    // WHEN they checkout
    const order = orderService.checkout(user.id, cart.id);

    // THEN the order has 10% discount applied
    expect(order.discount).toBe(0.10);
    expect(order.total).toBe(cart.subtotal * 0.90);
  });
});
```

### 2.3 Fase GREEN — Código Mínimo que Faz Passar

**Objetivo:** Escrever o código de produção **mínimo** que faz o teste passar. Nada mais.

**Regras:**
- Use a estratégia de Beck mais adequada (ver §3).
- Não adicione funcionalidade além do que o teste exige.
- Não refatore ainda (isso é a próxima fase).
- Commit message: `feat: GREEN — <descrição da implementação mínima>`
- Se o teste passa na primeira execução sem código novo, **o teste está errado** (não houve fase RED real).

**Exemplo — Fake It (retorno hardcoded):**

```typescript
// GREEN mínimo com Fake It
class UserService {
  createUser(input: CreateUserInput): User {
    // Mínimo absoluto para o teste passar
    return { id: 1, name: input.name, email: input.email };
  }
}
```

### 2.4 Fase REFACTOR — Melhorar sem Quebrar

**Objetivo:** Melhorar a estrutura interna do código sem alterar comportamento externo.

**Regras:**
- Os testes continuam passando (rede de segurança).
- Aplica padrões, remove duplicação, melhora nomes.
- Não adiciona funcionalidade nova — se precisa de nova funcionalidade, volte ao RED.
- Commit message: `refactor: <descrição da melhoria>`
- Se os testes quebram durante o refactor, você mudou comportamento — desfaça e refatore em passos menores.

**Checklist de Refactor:**
- [ ] Código está mais legível que antes?
- [ ] Duplicação foi removida?
- [ ] Nomes revelam intenção?
- [ ] Todos os testes ainda passam?
- [ ] Nenhum novo comportamento foi adicionado?

---

## 🧠 3. Estratégias de Beck para Chegar ao GREEN

Kent Beck descreve 4 estratégias para transformar um teste RED em GREEN. O agente deve escolher a estratégia apropriada para cada situação.

### 3.1 Fake It ("Fingir até funcionar")

**Quando usar:** Primeiro teste de uma nova funcionalidade. Comportamento simples.

**Como:** Retornar um valor hardcoded que satisfaz o teste, depois substituir por lógica real nos próximos ciclos.

```typescript
// RED: test expects greet("Alice") → "Hello, Alice!"
// GREEN com Fake It:
function greet(name: string): string {
  return "Hello, Alice!"; // Fake — funciona só para "Alice"
}

// Próximo ciclo RED: greet("Bob") → "Hello, Bob!"
// GREEN — substitui fake por implementação real:
function greet(name: string): string {
  return `Hello, ${name}!`; // Agora genérico
}
```

**Vantagem:** Rápido, mantém o ciclo curto.
**Risco:** Esquecer de substituir o fake — o próximo teste RED força a substituição.

### 3.2 Obvious Implementation ("Implementação óbvia")

**Quando usar:** A implementação é trivial e você tem alta confiança.

**Como:** Escrever a implementação correta diretamente, sem fake.

```typescript
// RED: test expects add(2, 3) → 5
// GREEN com Obvious Implementation:
function add(a: number, b: number): number {
  return a + b; // Óbvio, sem necessidade de fake
}
```

**Vantagem:** Sem etapa intermediária desnecessária.
**Risco:** Se o teste falhar no GREEN com "obvious implementation", você subestimou a complexidade — volte para Fake It.

### 3.3 Triangulação ("Triangular com exemplos")

**Quando usar:** Comportamento com múltiplos caminhos, edge cases, ou lógica não óbvia.

**Como:** Escrever 3+ testes com entradas diferentes que forçam a generalização.

```typescript
// Triangulação para função de desconto:
describe('calculateDiscount', () => {
  // Usar it.each para forçar triangulação com 3+ casos
  it.each([
    ['regular user, no items', 'regular', 0, 0],
    ['regular user, 5 items', 'regular', 5, 0],      // regular: nunca desconto
    ['premium user, 1 item', 'premium', 1, 5],         // premium: 5%
    ['premium user, 10 items', 'premium', 10, 10],     // premium + volume: 10%
    ['vip user, any items', 'vip', 1, 15],             // vip: 15%
  ])('%s → discount = %s%%', (_desc, tier, items, expectedDiscount) => {
    expect(calculateDiscount(tier, items)).toBe(expectedDiscount);
  });
});
```

**Regra de triangulação:** Mínimo de **3 casos** por comportamento não trivial. Casos devem incluir:
1. Caso base (happy path)
2. Caso de borda (edge case)
3. Caso de erro (error path)

**Vantagem:** Força a generalização correta; documenta edge cases como exemplos executáveis.
**Risco:** Over-testing de casos redundantes — foque em partições de equivalência.

### 3.4 Degenerate Test ("Teste degenerado")

**Quando usar:** Quando você precisa de um ponto de partida mínimo para começar o ciclo.

**Como:** Escrever um teste tão simples que é quase trivial — só para iniciar o ciclo RED-GREEN-REFACTOR.

```typescript
// Degenerate test para inicializar o ciclo:
it('should return an empty array when no users exist', () => {
  mockRepo.findAll.mockResolvedValue([]);
  const result = userService.listUsers();
  expect(result).toEqual([]);
});
```

**Vantagem:** Desbloqueia paralisia de análise — comece com o teste mais simples possível.
**Risco:** Pode gerar testes de baixo valor se não evoluir rapidamente para testes significativos.

### 3.5 Matriz de Decisão

| Situação | Estratégia Recomendada |
|----------|----------------------|
| Primeiro teste da feature, comportamento simples | Fake It |
| Implementação trivial, alta confiança | Obvious Implementation |
| Lógica com múltiplos caminhos ou edge cases | Triangulação |
| Paralisia de análise, não sabe por onde começar | Degenerate Test |
| Comportamento complexo com regras de negócio | Triangulação (mín. 5 casos) |

---

## 📐 4. Templates de Teste

### 4.1 AAA Pattern (Arrange, Act, Assert)

Template canônico para testes unitários. Cada seção é visualmente separada.

```typescript
// Template AAA completo
describe('FeatureName.serviceMethod', () => {
  // Setup compartilhado (antes de cada teste)
  let service: FeatureService;
  let mockRepo: jest.Mocked<Repository>;

  beforeEach(() => {
    mockRepo = {
      findById: jest.fn(),
      save: jest.fn(),
      delete: jest.fn(),
    };
    service = new FeatureService(mockRepo);
  });

  it('should describe expected behavior', () => {
    // Arrange — prepara dados, mocks e estado inicial
    const input = { /* dados do teste */ };
    mockRepo.findById.mockResolvedValue({ /* stub */ });

    // Act — executa a operação sob teste
    const result = service.method(input);

    // Assert — verifica resultado e side effects
    expect(result).toMatchObject({ /* expected */ });
    expect(mockRepo.save).toHaveBeenCalledTimes(1);
    expect(mockRepo.save).toHaveBeenCalledWith(expect.objectContaining({ /* ... */ }));
  });

  it('should handle error when dependency fails', () => {
    // Arrange — cenário de erro
    mockRepo.findById.mockRejectedValue(new Error('DB unavailable'));

    // Act + Assert combinados para exceções
    expect(() => service.method({ id: 1 })).toThrow('DB unavailable');
  });
});
```

### 4.2 GIVEN-WHEN-THEN (BDD)

Preferido para testes de integração e comportamento de negócio.

```typescript
// Template GIVEN-WHEN-THEN
describe('Checkout Flow', () => {
  it('should complete purchase and send confirmation email', () => {
    // GIVEN — contexto inicial
    const user = given.aUser({ email: 'alice@example.com', tier: 'premium' });
    const cart = given.aCart({ userId: user.id, items: 3, subtotal: 150.00 });
    given.paymentMethodIsValid(user.id);
    given.inventoryIsAvailable(cart.items);

    // WHEN — ação
    const order = when.userChecksOut(user.id, cart.id);

    // THEN — resultados esperados
    then.orderShouldBeCreated(order, {
      userId: user.id,
      total: 135.00, // 10% premium discount
      status: 'confirmed',
    });
    then.emailShouldBeSentTo(user.email, { template: 'order-confirmation' });
    then.inventoryShouldBeReserved(cart.items);
  });
});
```

---

## ❌ 6. Anti-Padrões de Teste

### 6.1 TAD — Test After Development

**Sintoma:** Código de produção escrito antes do teste. O teste é adicionado "para cumprir tabela".

```typescript
// ❌ TAD: código escrito primeiro, teste como afterthought
class DiscountCalculator {
  calculate(price: number, tier: string): number {
    // Implementação complexa já completa
    if (tier === 'premium') return price * 0.9;
    if (tier === 'vip') return price * 0.85;
    return price;
  }
}

// Teste escrito depois, tende a testar implementação, não comportamento
it('should calculate discount', () => {
  const calc = new DiscountCalculator();
  expect(calc.calculate(100, 'premium')).toBe(90); // Testa o que já foi implementado
});
```

**✅ Correção:** Inverter a ordem — escrever o teste primeiro (RED), ver falhar, depois implementar.

### 6.2 Mocks Frágeis (Implementation Mocking)

**Sintoma:** Mock atrelado a detalhes internos que quebram quando a implementação muda.

```typescript
// ❌ Mock frágil: atrelado à query SQL exata
jest.spyOn(db, 'query').mockResolvedValue({
  sql: 'SELECT id, name, email FROM users WHERE deleted_at IS NULL ORDER BY name ASC',
  rows: [{ id: 1, name: 'Alice' }],
});

// ❌ Mock frágil: atrelado à ordem de chamadas internas
expect(service.internalMethod1).toHaveBeenCalledBefore(service.internalMethod2);
```

**✅ Correção:** Mockar por contrato (interface do repositório/serviço), não por implementação.

```typescript
// ✅ Mock por contrato
mockUserRepo.findAll.mockResolvedValue([{ id: 1, name: 'Alice' }]);
expect(result).toEqual([{ id: 1, name: 'Alice' }]);
```

### 6.3 Delays Arbitrários

**Sintoma:** `setTimeout`/`sleep` para esperar condições assíncronas — torna testes lentos e instáveis (flaky).

```typescript
// ❌ Delay arbitrário
await new Promise(resolve => setTimeout(resolve, 1000));
expect(screen.getByText('Loaded')).toBeInTheDocument();

// ❌ Sleep em teste de API
await sleep(2000); // espera o webhook processar
expect(mockWebhook).toHaveBeenCalled();
```

**✅ Correção:** Usar polling determinístico que espera por estado:

```typescript
// ✅ waitFor — espera pelo estado, não por tempo
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
}, { timeout: 5000 }); // timeout é safety net, não expectation

// ✅ findBy* — query assíncrona built-in
expect(await screen.findByText('Loaded')).toBeInTheDocument();
```

### 6.4 Placeholders

**Sintoma:** Testes que passam sem validar nada — `expect(true).toBe(true)`, `it()` vazio, asserções ausentes.

```typescript
// ❌ Placeholders — passam mas não testam nada
it('should create user', () => {
  expect(true).toBe(true);
});

it('should handle edge cases'); // vazio — sem callback

it('should work', () => {
  const result = service.method();
  // sem expect — passa sempre
});
```

**✅ Correção:** Todo teste deve ter pelo menos uma asserção significativa. Se não sabe o que testar ainda, use `it.todo('descrição' /* TODO(#123) */)`.

### 6.5 Dependência de Ordem

**Sintoma:** Testes que só passam quando executados em sequência específica.

```typescript
// ❌ Dependência de ordem — teste B assume estado do teste A
let sharedUserId: number;

it('should create user', () => {
  const user = service.createUser({ name: 'Alice' });
  sharedUserId = user.id; // Estado compartilhado entre testes
  expect(user.name).toBe('Alice');
});

it('should find user by id', () => {
  // Assume que sharedUserId foi setado pelo teste anterior
  const user = service.findById(sharedUserId);
  expect(user.name).toBe('Alice');
});
```

**✅ Correção:** Cada teste configura seu próprio estado em `beforeEach`:

```typescript
let userId: number;

beforeEach(async () => {
  const user = await service.createUser({ name: 'Alice' });
  userId = user.id;
});

it('should find user by id', () => {
  const user = service.findById(userId);
  expect(user.name).toBe('Alice');
});
```

### 6.6 Testar Implementação, Não Comportamento

**Sintoma:** Teste acoplado a detalhes internos — variáveis privadas, chamadas de método interno, estado intermediário.

```typescript
// ❌ Testa implementação
it('should call validateEmail internally', () => {
  const spy = jest.spyOn(service as any, 'validateEmail');
  service.createUser({ email: 'alice@example.com' });
  expect(spy).toHaveBeenCalled(); // Acoplado a método privado
});

// ❌ Testa estado interno
expect(service['retryCount']).toBe(3);
```

**✅ Correção:** Testar outputs observáveis e side effects públicos:

```typescript
// ✅ Testa comportamento
it('should reject invalid email format', () => {
  expect(() =>
    service.createUser({ email: 'not-an-email' })
  ).toThrow('Invalid email format');
});
```

---

## 🏗️ 5. Padrões de Mock

### 5.1 Test Data Builder

Constrói objetos de teste complexos com defaults sensíveis e override seletivo.

```typescript
// Template: Test Data Builder
// Arquivo: src/test/builders/userBuilder.ts

interface UserOverrides {
  id?: number;
  name?: string;
  email?: string;
  tier?: 'free' | 'premium' | 'vip';
  createdAt?: Date;
}

export function buildUser(overrides: UserOverrides = {}): User {
  const defaults: User = {
    id: 1,
    name: 'Default User',
    email: 'default@example.com',
    tier: 'free',
    createdAt: new Date('2026-01-01'),
  };
  return { ...defaults, ...overrides };
}

// Uso nos testes:
const premiumUser = buildUser({ tier: 'premium' });
const newUser = buildUser({ id: undefined, email: 'bob@example.com' });
```

**Vantagens:**
- Testes expressam apenas o que é relevante (ex: `buildUser({ tier: 'premium' })`).
- Defaults sensíveis evitam setups verbosos.
- Mudanças no modelo (novo campo obrigatório) afetam apenas o builder, não 50 testes.

### 5.2 Constructor Injection (DI para Testabilidade)

Dependências injetadas via construtor — mockáveis sem monkey-patching.

```typescript
// ✅ Constructor Injection — testável por design
class OrderService {
  constructor(
    private readonly userRepo: UserRepository,
    private readonly orderRepo: OrderRepository,
    private readonly paymentGateway: PaymentGateway,
    private readonly emailService: EmailService,
  ) {}

  async checkout(userId: number, cartId: number): Promise<Order> {
    const user = await this.userRepo.findById(userId);
    // ...
  }
}

// No teste: mock é trivial
const service = new OrderService(
  mockUserRepo,
  mockOrderRepo,
  mockPaymentGateway,
  mockEmailService,
);
```

```typescript
// ❌ Hardcoded dependency — difícil de testar
class OrderService {
  private readonly userRepo = new PostgresUserRepository(); // Acoplado
  async checkout(userId: number, cartId: number): Promise<Order> {
    // ...
  }
}
// Teste precisa de monkey-patching ou banco real
```

---

## ✅ 7. Checklist F.I.R.S.T.

Validar **cada teste** contra os 5 princípios F.I.R.S.T. antes de considerar o ciclo completo.

| Princípio | Pergunta | ❌ Falha se... |
|-----------|----------|---------------|
| **F**ast | O teste executa em < 100ms? | Usa banco real, rede, ou `setTimeout` |
| **I**ndependent | O teste roda isolado, em qualquer ordem? | Compartilha estado com outros testes |
| **R**epeatable | O teste passa sempre com a mesma entrada? | Depende de data/hora atual, random, ou rede |
| **S**elf-validating | O teste tem asserção explícita? | Não tem `expect`/`assert`, usa `console.log` para verificar |
| **T**imely | O teste foi escrito ANTES do código de produção? | Código de produção já existia (TAD) |

### Template de Checklist por Teste

```markdown
### F.I.R.S.T. Checklist: `UserService.createUser`

- [F] Fast — < 100ms? ✅ (mock repository, sem I/O)
- [I] Independent — roda isolado? ✅ (beforeEach limpa estado)
- [R] Repeatable — determinístico? ✅ (sem Date.now(), sem Math.random())
- [S] Self-validating — tem expect? ✅ (3 asserções)
- [T] Timely — escrito antes do código? ✅ (fase RED confirmada)
```

---

## 🔗 8. Integração com o Pipeline LLC

### 8.1 Campo `tdd_phase` no `<context_seed>`

Toda sessão que executa PRPs (Step 11) deve incluir o campo `tdd_phase` no `<context_seed>`:

```xml
<context_seed>
  <state>implementando PRP-004 — UserService</state>
  <pending>Escrever teste RED para createUser</pending>
  <tdd_phase>red</tdd_phase>
  <!-- red | green | refactor -->
  <blockers>Nenhum</blockers>
  <next_action>Executar npm test para confirmar falha do RED</next_action>
</context_seed>
```

O agente **não pode** avançar para fase seguinte sem atualizar `tdd_phase` e validar a condição de saída da fase atual.

### 8.2 Integração com Steps

| Step | Integração |
|------|------------|
| **9 Testing Docs** | Skill 9a é sub-step — carregada após TESTING_GUIDE.md gerado |
| **10 AGENTS.md** | Hard gates de TDD injetados no Master Prompt |
| **11 Execução PRPs** | `tdd_phase` no `<context_seed>` de cada sessão de implementação |
| **11.2 PRP Verify** | Re-executa `npm test` e verifica placeholder detection como parte da verificação |
| **Pre-commit** | `pre-commit-tests.sh` bloqueia commits com placeholders, delays, ou testes falhando |

### 8.3 Pre-commit Hook (Test Gate)

O script `pre-commit-tests.sh` (Ação 5b do Harness Preventivo) executa estas verificações nos staged test files:

1. **Placeholder detection:** Regex para `expect(true).toBe(true)`, `it\(\)` vazio, `it\.skip\(` sem `TODO(#\d+)`.
2. **Delay detection:** Regex para `setTimeout`/`sleep`/`wait(` em arquivos de teste.
3. **Test execution:** `jest --findRelatedTests` nos arquivos modificados.

---

## 📝 9. Prompt de Execução

Você está executando a skill `llc-step-9a-tdd-discipline` do pipeline LLC. Seu objetivo é **estabelecer a disciplina TDD** que será aplicada em toda sessão subsequente de geração de código.

### 9.1 Leia as Entradas

- `docs/testing/TESTING_GUIDE.md` — stack e ferramentas de teste (Step 9)
- `docs/testing/COVERAGE_BASELINE.md` — baseline de cobertura (Step 9)
- `docs/architecture/ARCHITECTURE.md` — stack, frameworks, bibliotecas de teste (Step 5)
- `docs/prps/PRP-*.md` — PRPs com requisitos a serem testados (Step 3)

### 9.2 Execute as Verificações

1. **Valide os Hard Gates:** Confirme que o AGENTS.md referencia as 7 regras intransponíveis (§1).
2. **Verifique os Templates:** Confirme que os templates AAA e GIVEN-WHEN-THEN (§4) estão acessíveis ao agente.
3. **Configure o context_seed:** Garanta que o campo `tdd_phase` será injetado no `<context_seed>` das sessões Step 11.
4. **Verifique o Pre-commit:** Confirme que `pre-commit-tests.sh` está configurado e detecta placeholders, delays, e `it.skip` sem ticket.
5. **Estabeleça baseline TDD:** Execute `npm test` para confirmar que todos os testes existentes passam (ou documente "greenfield — 0 testes").

### 9.3 Regras Críticas

- **Stack-awareness:** Adaptar templates e comandos ao stack real do projeto (Jest/Vitest/Mocha/Playwright).
- **Idempotência:** Re-execução não deve duplicar regras no AGENTS.md ou `.ace/config/`.
- **Greenfield vs Brownfield:** Em projeto greenfield, marcar baseline como "0 testes — TDD começa no primeiro PRP". Em brownfield, documentar cobertura existente.

---

## 📤 10. Saída Esperada e Finalização

Após executar esta skill, **PARE** e apresente:

1. **Hard Gates:** As 7 regras foram injetadas no AGENTS.md ou equivalente?
2. **Templates:** Os templates AAA e GIVEN-WHEN-THEN estão acessíveis?
3. **context_seed:** O campo `tdd_phase` está configurado para sessões Step 11?
4. **Pre-commit:** `pre-commit-tests.sh` está ativo e detecta placeholders/delays?
5. **Próximos Passos:** "TDD Discipline ativo. Toda sessão Step 11 agora exige RED → GREEN → REFACTOR com commits por fase. Campo `tdd_phase` rastreia o ciclo atual."

**Gate 9a — Validação Humana:**
- [ ] As 7 hard gates são apropriadas para o stack e domínio do projeto?
- [ ] Os padrões de mock (Test Data Builder, Constructor Injection) são compatíveis com a arquitetura?
- [ ] A equipe entende o ciclo RED → GREEN → REFACTOR com commits por fase?
- [ ] O pre-commit hook `pre-commit-tests.sh` está configurado e funcional?
- [ ] Exceções documentadas (ex: projeto sem frontend → delays em teste irrelevantes)?

**NÃO prossiga para Step 10 sem Gate 9a aprovado.**

---

## 📚 11. Referências

- **Beck, K. (2003)** — *Test-Driven Development: By Example*. Addison-Wesley.
- **Meszaros, G. (2007)** — *xUnit Test Patterns: Refactoring Test Code*. Addison-Wesley.
- **Martin, R. C. (2009)** — *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall. Capítulo 9: Unit Tests, F.I.R.S.T.
- **Freeman, S. & Pryce, N. (2009)** — *Growing Object-Oriented Software, Guided by Tests*. Addison-Wesley. Mock por contrato.
- **Fowler, M. (2007)** — *Mocks Aren't Stubs*. martinfowler.com.
- **Crispin, L. & Gregory, J. (2009)** — *Agile Testing: A Practical Guide for Testers and Agile Teams*. Addison-Wesley.
