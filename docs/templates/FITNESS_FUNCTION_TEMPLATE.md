# FITNESS_FUNCTION_TEMPLATE.md

Template para definição de Fitness Functions Arquiteturais (Architectural Fitness Functions).
**Versão:** 1.0 | **Gerado por:** llc-step-5a-architecture-patterns | **Usado em:** Step 11b (llc-step-11b-arch-fitness)

---

## Visão Geral

Fitness Functions são **testes arquiteturais automatizados** que verificam se o código implementado está em conformidade com as decisões arquiteturais documentadas nos ADRs e no `ARCHITECTURE.md`.

Baseado em: **Ingeno - Software Architect's Handbook, Ch. 16** — "Architectural Fitness Functions"

---

## Estrutura do Arquivo de Configuração

O arquivo principal é `.ace/arch-config.yaml` (gerado no Step 5a). Este template define como adicionar/estender rules.

```yaml
# .ace/arch-config.yaml
version: "1.0"
generated_by: "llc-step-5a"
last_updated: "2025-01-15T10:00:00Z"

core_modules:
  - auth
  - usuarios
  - auditorias
  - achados
  - planos

enforcement:
  core: "error"      # Bloqueia CI / PRP approval
  non_core: "warning" # Apenas avisa

rules:
  # --- Dependency Rule (Clean Architecture) ---
  - name: "no-prisma-in-domain"
    type: "import_pattern"
    pattern: "(@prisma/client|PrismaService)"
    forbidden_in:
      - "**/domain/**"
    message: "Domain layer não pode importar Prisma client ou PrismaService"
    severity: "error"
    adr: "ADR-0008"

  - name: "no-prisma-in-use-cases"
    type: "import_pattern"
    pattern: "PrismaService"
    forbidden_in:
      - "**/application/**"
      - "**/use-cases/**"
    message: "Use Cases não podem injetar PrismaService diretamente"
    severity: "error"
    adr: "ADR-0008"

  - name: "no-infrastructure-in-domain"
    type: "import_pattern"
    pattern: "from ['\"].*infrastructure"
    forbidden_in:
      - "**/domain/**"
    message: "Domain não pode importar de infrastructure"
    severity: "error"
    adr: "ADR-0008"

  - name: "no-cross-module-imports-domain"
    type: "import_pattern"
    pattern: "from ['\"]\\.\\./[^/]+/"
    forbidden_in:
      - "**/domain/**"
    allowed_except:
      - "**/shared/**"
      - "**/domain/**"
      - "**/application/**"
      - "**/dto/**"
    message: "Domain não pode importar de módulos irmãos (exceto shared)"
    severity: "error"
    adr: "ADR-0008"

  - name: "no-cross-module-imports-application"
    type: "import_pattern"
    pattern: "from ['\"]\\.\\./[^/]+/"
    forbidden_in:
      - "**/application/**"
    allowed_except:
      - "**/shared/**"
      - "**/domain/**"
      - "**/application/**"
      - "**/dto/**"
    message: "Application não pode importar de módulos irmãos (exceto shared)"
    severity: "error"
    adr: "ADR-0008"

  # --- Repository Pattern Compliance ---
  - name: "repository-interface-exists"
    type: "file_exists"
    path: "**/domain/repositories/I*Repository.ts"
    message: "Cada aggregate root deve ter interface de repository em domain/repositories/"
    severity: "error"
    adr: "ADR-0008"

  - name: "repository-impl-exists"
    type: "file_exists"
    path: "**/infrastructure/repositories/Prisma*Repository.ts"
    message: "Cada interface deve ter implementação Prisma em infrastructure/repositories/"
    severity: "error"
    adr: "ADR-0008"

  - name: "repository-binding-in-module"
    type: "pattern_in_file"
    pattern: "provide: I.*Repository"
    required_in:
      - "**/*.module.ts"
    message: "Module deve ter binding DI: { provide: I{Nome}Repository, useClass: Prisma{Nome}Repository }"
    severity: "error"
    adr: "ADR-0008"

  - name: "service-injects-interface"
    type: "import_pattern"
    pattern: "@Inject\\(I.*Repository\\)"
    required_in:
      - "**/*.service.ts"
      - "**/use-cases/*.ts"
    forbidden_in:
      - "**/*.service.ts"  # negated check via separate rule
    message: "Services/Use Cases devem injetar interface do repository"
    severity: "error"
    adr: "ADR-0008"

  - name: "mapper-exists"
    type: "file_exists"
    path: "**/infrastructure/mappers/*.mapper.ts"
    message: "Cada aggregate root deve ter Mapper em infrastructure/mappers/"
    severity: "error"
    adr: "ADR-0008"

  # --- Use Case Compliance ---
  - name: "use-case-naming"
    type: "naming"
    pattern: "UseCase\\.ts$"
    required_in:
      - "**/application/use-cases/**"
    message: "Use Cases devem terminar com sufixo UseCase (arquivo: .use-case.ts)"
    severity: "error"
    adr: "ADR-0010"

  - name: "use-case-injects-ports-only"
    type: "import_pattern"
    pattern: "(PrismaService|@nestjs/common.*Controller|@nestjs/common.*Injectable.*Service)"
    forbidden_in:
      - "**/application/use-cases/**"
    message: "Use Cases não podem injetar PrismaService, Controllers ou Services de infraestrutura"
    severity: "error"
    adr: "ADR-0010"

  - name: "use-case-returns-result-or-promise"
    type: "class_structure"
    check: "execute_method_signature"
    required_in:
      - "**/application/use-cases/**/*.use-case.ts"
    message: "Use Case deve ter método execute(input) retornando Promise<Output>"
    severity: "error"
    adr: "ADR-0010"

  - name: "use-case-emits-events"
    type: "pattern_in_file"
    pattern: "eventEmitter\\.emit\\("
    required_in:
      - "**/application/use-cases/**/*.use-case.ts"
    # Note: nem todo use case emite events, mas os que mutam estado devem
    message: "Use Cases que mutam estado devem emitir domain events via eventEmitter.emit()"
    severity: "warning"
    adr: "ADR-0011"

  # --- Domain Layer Purity ---
  - name: "entity-no-framework"
    type: "class_structure"
    check: "no_decorators"
    forbidden_in:
      - "**/domain/entities/**/*.entity.ts"
    message: "Entities não podem ter decorators (@Entity, @Injectable, @Module, etc.)"
    severity: "error"
    adr: "ADR-0009"

  - name: "entity-no-prisma"
    type: "import_pattern"
    pattern: "(@prisma/client|Prisma\\.)"
    forbidden_in:
      - "**/domain/**"
    message: "Domain layer não pode importar tipos Prisma"
    severity: "error"
    adr: "ADR-0009"

  - name: "vo-immutable"
    type: "class_structure"
    check: "readonly_properties"
    required_in:
      - "**/domain/value-objects/**/*.vo.ts"
    message: "Value Objects devem ter propriedades readonly"
    severity: "error"
    adr: "ADR-0009"

  - name: "vo-factory-validation"
    type: "class_structure"
    check: "static_criar_method"
    required_in:
      - "**/domain/value-objects/**/*.vo.ts"
    message: "Value Objects devem ter método static criar() retornando Result"
    severity: "error"
    adr: "ADR-0009"

  - name: "domain-event-structure"
    type: "class_structure"
    check: "extends_domain_event"
    required_in:
      - "**/domain/events/**/*.event.ts"
    message: "Domain Events devem extender DomainEvent base com aggregateId, occurredAt, eventId"
    severity: "error"
    adr: "ADR-0009"

  - name: "domain-error-typed"
    type: "class_structure"
    check: "extends_domain_error"
    required_in:
      - "**/domain/errors/**/*.error.ts"
    message: "Domain Errors devem extender DomainError base com code único"
    severity: "error"
    adr: "ADR-0009"

  # --- Event Bus Compliance ---
  - name: "event-emitter-configured"
    type: "file_content"
    path: "src/app.module.ts"
    pattern: "EventEmitterModule\\.forRoot\\(\\)"
    message: "EventEmitterModule deve ser registrado no AppModule"
    severity: "error"
    adr: "ADR-0011"

  - name: "handlers-use-onevent"
    type: "class_structure"
    check: "on_event_decorator"
    required_in:
      - "**/handlers/**/*.handler.ts"
    message: "Event handlers devem usar decorator @OnEvent('event.name')"
    severity: "error"
    adr: "ADR-0011"

  - name: "modules-dont-import-each-other"
    type: "import_pattern"
    pattern: "from ['\"]\\.\\./[^/]+/"
    forbidden_in:
      - "**/*.module.ts"
    allowed_except:
      - "**/shared/**"
      - "**/prisma/**"
      - "**/common/**"
    message: "Modules não devem importar outros modules de negócio (use eventos)"
    severity: "error"
    adr: "ADR-0011"

event_bus:
  library: "@nestjs/event-emitter"
  base_event_class: "src/shared/domain/domain-event.ts"
  modules_with_handlers:
    - notificacoes
    - auditorias
    - achados
```

---

## Tipos de Rule Suportados

| Tipo | Descrição | Parâmetros Principais |
|------|-----------|----------------------|
| `import_pattern` | Verifica imports via regex | `pattern`, `forbidden_in`, `allowed_except`, `required_in` |
| `file_exists` | Verifica existência de arquivo | `path` (glob) |
| `pattern_in_file` | Verifica padrão em arquivo(s) | `pattern`, `required_in`, `forbidden_in` |
| `naming` | Verifica convenção de nomes | `pattern`, `required_in` |
| `class_structure` | Verifica estrutura de classe (AST) | `check`, `required_in`, `forbidden_in` |
| `file_content` | Verifica conteúdo de arquivo específico | `path`, `pattern` |

### Class Structure Checks Disponíveis

| Check | O que Verifica |
|-------|----------------|
| `no_decorators` | Classe não tem decorators |
| `readonly_properties` | Todas as propriedades são `readonly` |
| `static_criar_method` | Tem método static `criar()` retornando `Result` |
| `extends_domain_event` | Extende `DomainEvent` base |
| `extends_domain_error` | Extende `DomainError` base |
| `execute_method_signature` | Tem método `execute(input)` com signature correta |
| `on_event_decorator` | Tem decorator `@OnEvent()` |

---

## Como Adicionar Nova Fitness Function

### 1. Identifique a Decisão Arquitetural (ADR)
Toda fitness function deve rastrear para um ADR.

### 2. Escolha o Tipo de Rule
Use a tabela acima para escolher o tipo mais apropriado.

### 3. Adicione ao `.ace/arch-config.yaml`

```yaml
rules:
  - name: "minha-nova-rule"
    type: "import_pattern"  # ou outro tipo
    pattern: "minha-regex"
    forbidden_in:
      - "**/caminho/proibido/**"
    allowed_except:
      - "**/excecao/**"
    message: "Mensagem clara explicando a violação"
    severity: "error"  # ou "warning"
    adr: "ADR-XXX"
```

### 4. Teste Localmente

```bash
# Rodar para módulo específico
python .ace/scripts/fitness-functions.py --module auditorias --strict

# Rodar todas
python .ace/scripts/fitness-functions.py --all --strict
```

### 5. Atualize este Template
Adicione a nova rule na seção correspondente acima.

---

## Integração com ESLint (import/no-restricted-paths)

Além das fitness functions TypeScript, configure ESLint para catch rápido no IDE:

```javascript
// api/.eslintrc.js
module.exports = {
  rules: {
    'import/no-restricted-paths': ['error', {
      zones: [
        // Domain não pode importar infraestrutura
        {
          target: '**/domain/**',
          from: ['**/infrastructure/**', '**/prisma/**', '@prisma/client'],
          message: 'Domain layer cannot import infrastructure or Prisma'
        },
        // Application não pode importar infraestrutura ou presentation
        {
          target: '**/application/**',
          from: ['**/infrastructure/**', '**/presentation/**', '**/controllers/**', 'PrismaService'],
          message: 'Application layer cannot import infrastructure, presentation, or PrismaService'
        },
        // Controllers devem usar Use Cases, não Repositories
        {
          target: '**/*.controller.ts',
          from: ['**/repositories/**', '**/infrastructure/repositories/**'],
          message: 'Controllers must use Use Cases, not Repositories directly'
        },
        // Use Cases não injetam PrismaService
        {
          target: '**/application/use-cases/**',
          from: ['PrismaService'],
          message: 'Use Cases cannot inject PrismaService'
        },
        // Módulos de negócio não importam uns aos outros
        {
          target: ['**/domain/**', '**/application/**'],
          from: ['../*/**'],
          except: ['**/shared/**', '**/domain/**', '**/application/**', '**/dto/**'],
          message: 'Domain/Application cannot import from sibling modules'
        }
      ]
    }]
  }
};
```

---

## Severity Matrix

| Módulo | Core? | Dependency Rule | Repository Pattern | Use Cases | Domain Purity | Event Bus |
|--------|-------|-----------------|-------------------|-----------|---------------|-----------|
| `auth` | ✅ | error | error | error | error | error |
| `usuarios` | ✅ | error | error | error | error | error |
| `auditorias` | ✅ | error | error | error | error | error |
| `achados` | ✅ | error | error | error | error | error |
| `planos` | ✅ | error | error | error | error | error |
| `notificacoes` | ❌ | warning | warning | warning | warning | error |
| `relatorios` | ❌ | warning | warning | warning | warning | warning |
| `recomendacoes` | ❌ | warning | warning | warning | warning | warning |
| `consultorias` | ❌ | warning | warning | warning | warning | warning |
| `qualidade` | ❌ | warning | warning | warning | warning | warning |
| `riscos` | ❌ | warning | warning | warning | warning | warning |
| `governanca` | ❌ | warning | warning | warning | warning | warning |
| `etica` | ❌ | warning | warning | warning | warning | warning |
| `biblioteca` | ❌ | warning | warning | warning | warning | warning |
| `integracoes` | ❌ | warning | warning | warning | warning | warning |
| `capacitacoes` | ❌ | warning | warning | warning | warning | warning |
| `dashboards` | ❌ | warning | warning | warning | warning | warning |
| `acoes-coordenadas` | ❌ | warning | warning | warning | warning | warning |
| `config` | ❌ | warning | warning | warning | warning | warning |
| `mandatos` | ❌ | warning | warning | warning | warning | warning |
| `logs-sistema` | ❌ | warning | warning | warning | warning | warning |
| `perfis` | ❌ | warning | warning | warning | warning | warning |
| `universo` | ❌ | warning | warning | warning | warning | warning |

---

## CI Integration

```yaml
# .github/workflows/arch-fitness.yml
name: Architectural Fitness Functions

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  arch-fitness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd api && npm ci
      - name: Run Fitness Functions
        run: |
          cd api
          npx ts-node test/architecture/fitness-functions.ts --all --strict
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: arch-fitness-report
          path: api/arch-fitness-report.json
```

---

## PRP Verify Integration (Step 11.2)

No `prp_verify.py` ou skill `llc-step-11-2-prp-verify.md`:

```python
def check_arch_fitness(prp_id: str, module: str) -> bool:
    """Roda fitness functions para o módulo do PRP antes de aprovar."""
    import subprocess
    
    result = subprocess.run([
        'python', '.ace/scripts/fitness-functions.py',
        '--module', module,
        '--strict'
    ], capture_output=True, text=True, cwd='api')
    
    if result.returncode != 0:
        print(f"❌ Fitness functions FALHARAM para {module} (PRP {prp_id})")
        print(result.stdout)
        print(result.stderr)
        return False
    
    print(f"✅ Fitness functions PASSARAM para {module}")
    return True

# No fluxo de verificação do PRP:
# 1. Rodar testes unitários
# 2. Rodar consistency-check
# 3. Rodar code-health
# 4. >>> RODAR FITNESS FUNCTIONS (NOVO - OBRIGATÓRIO) <<<
# 5. Se tudo passa → Gate Humano
```

---

## Greenfield vs Brownfield

| Cenário | Execução |
|---------|----------|
| **Greenfield** | `--all --strict` em todos módulos a cada PRP |
| **Brownfield** | - Módulos novos/alterados: `--module X --strict`<br>- Módulos legacy: `--module X --legacy` (severity=warning apenas)<br>- Config `arch-config.yaml` pode ter `legacy_modules` com enforcement reduzido |

### Config para Legacy Modules

```yaml
# .ace/arch-config.yaml (adição para brownfield)
legacy_modules:
  - usuarios
  - config
enforcement:
  legacy: "warning"  # Apenas warning para módulos legados
```

---

## Referências

- Ingeno, J. — *Software Architect's Handbook*, Ch. 16: Architectural Fitness Functions
- Ford, N., et al. — *Building Evolutionary Architectures*, Ch. 3: Fitness Functions
- Martin, R. — *Clean Architecture*, Ch. 22: The Dependency Rule
- Stemmler, K. — *Software Design & Architecture Handbook*, Ch. 6: Dependency Inversion