



Com base na extensa documentação de auditoria e planos de remediação fornecidos, fiz um levantamento detalhado dos erros recorrentes por tema. O objetivo agora é responder à sua pergunta central: **Como configurar o "harness" (o ecossistema de prompts, skills, scripts e ferramentas ao redor do LLM) para evitar que esses erros ocorram em iterações futuras.**

Abaixo, apresento a análise dividida por tema, listando os erros e como o harness pode ser usado para preveni-los.

---

### 1. Segurança (Security)
**Erros Encontrados:**
- Segredos hardcoded (JWT, chaves de API).
- Validação de premium apenas no client-side (bypass fácil).
- Criptografia fraca (XOR fallback, IV estático, chave compartilhada).
- Ausência de `user_id` (modelo de dados sem ownership).
- Exposição de PII em logs e backups descriptografados.
- Ausência de SSL Pinning e middlewares de auth no backend.

**Como o Harness previne:**
- **Skill ("Secure-by-Design"):** Criar uma skill no LLM que seja acionada sempre que o contexto envolver backend, autenticação ou banco de dados. Essa skill deve forçar o LLM a:
  - Usar variáveis de ambiente para qualquer segredo.
  - Adicionar `user_id` automaticamente em qualquer modelagem de tabela de domínio.
  - Usar `expo-secure-store` para tokens no mobile.
  - Falhar fechado (fail-closed) em vez de falhar aberto (ex: se o backend cair, não concede premium).
- **Scripts/Ferramentas (CI):** Integrar ferramentas como `gitleaks`, `eslint-plugin-security` e `npm audit` no pipeline. O LLM pode ser instruído a rodar esses scripts e corrigir os alertas antes de sugerir um PR.
- **Prompt Constraint:** Incluir na system prompt: *"Nunca use AsyncStorage para dados sensíveis. Sempre aplique parâmetros `?` em queries SQL. Esconda PII nos logs via sanitização."*

### 2. Arquitetura (Architecture)
**Erros Encontrados:**
- Abuso do padrão Singleton (acoplamento alto, testes paralelos inviáveis).
- Vazamento de SQL cru nas camadas de Serviço (violação da regra de dependência).
- Métodos "pass-through" rasos.
- Ausência de ADRs (Architecture Decision Records).
- Falta de fitness functions para evitar regressão arquitetural.

**Como o Harness previne:**
- **Skill ("Clean Architecture Enforcer"):** Uma skill que revisa o código gerado exigindo:
  - Repository Pattern: SQL só vive em `repositories/*`, services não importam SQLite.
  - Injeção de Dependência: Substituir `getInstance()` por interfaces injetadas via Context (React) ou Construtores.
- **Ferramentas (Architecture Fitness):** Usar o `dependency-cruiser`. O LLM deve ser instruído a executar `npm run arch:check` e só entregar o código se o comando passar 0 violações.
- **Prompt Constraint:** Exigir que o LLM documente qualquer decisão estrutural grande gerando um arquivo markdown em `docs/adr/` usando o template Nygard.

### 3. Clean Code
**Erros Encontrados:**
- Funções monolíticas (100-200 linhas) violando SRP.
- Violação de CQS (Commands mutando estado e retornando valores simultaneamente).
- Retornos de `null` espalhados (necessidade de null-checks em todo lugar).
- Code smells: Magic numbers, Data Clumps (ex: `technicianName`, `technicianPhone` sempre juntos).
- Tipagem fraca (`any`).

**Como o Harness previne:**
- **Prompt Constraint:** Adicionar regras estritas de geração de código:
  - *"Toda função deve ter no máximo 30 linhas. Se passar, extraia métodos privados."*
  - *"Substitua `return null` por Objetos de Caso Especial (ex: `NotFoundSentinel`)."*
  - *"Nunca use `any`. Use `unknown` e aplique Type Guards."*
  - *"Extraia constantes mágicas para um arquivo de configuração."*
- **Skill ("Refactoring Assistant"):** Sempre que o LLM for requisitado a alterar uma função grande, ele deve primeiro propor um plano de extração (ex: extrair `validateInput`, `encryptPii`, `buildSetClause`).

### 4. Testes e TDD
**Erros Encontrados:**
- Desenvolvimento Test-After (escrever código e testar depois).
- Testes vazios (`expect(true).toBe(true)`) ou `it()` blocks sem implementação.
- Mocks frágeis baseados em roteamento de string SQL.
- Flakiness por uso excessivo de `setTimeout` mágicos.
- Ausência de testes no pre-commit.

**Como o Harness previne:**
- **Skill ("TDD Master"):** Forçar o fluxo Red-Green-Refactor. O LLM só deve gerar o código de produção *após* gerar o teste que falha. A skill deve banir a geração de `setTimeout` em testes, forçando o uso de `waitFor` ou `await Promise.all`.
- **Skill ("Mock Builder"):** Padronizar a criação de mocks. Proibir o LLM de criar mocks que verificam `sql.includes('...')`. Ele deve criar interfaces mockadas que simulam o comportamento do banco (ex: o `createValidatingMockDb`).
- **Ferramentas (Hooks):** Configurar Husky para rodar `jest` no pre-commit. Instruir o LLM que o código só está "pronto" se os testes que ele mesmo escreveu passarem localmente.

### 5. DevOps e CI/CD
**Erros Encontrados:**
- Confiança apenas em hooks locais (sem CI na nuvem).
- Ausência de observabilidade (sem Sentry/Crashlytics).
- Sem OTA (expo-updates) para hotfixes.
- Falta de scanning de dependências (Dependabot).

**Como o Harness previne:**
- **Skill ("DevOps Bootstrap"):** Quando o LLM iniciar um projeto, ele deve scaffoldar automaticamente o `.github/workflows/ci.yml` com os steps de lint, test, build e arch:check.
- **Prompt Constraint:** O LLM deve ser instruído a sempre adicionar telemetry hooks (`Sentry.addBreadcrumb`) quando criar blocos `try/catch` no código de produção.

### 6. UI/UX
**Erros Encontrados:**
- Anti-padrão "Roach Motel" (fácil de entrar no paywall, difícil de sair).
- Confirmshaming no onboarding.
- Falta de abstração de formulários (código duplicado em 8 telas).
- Alertas de erro genéricos sem botão de "Tentar novamente".
- Hardcoding de strings em português no código (burlando i18n).

**Como o Harness previne:**
- **Skill ("UX Anti-Pattern Checker"):** Uma skill que atua como um revisor de design. Ao gerar uma tela de paywall ou alerta, ela verifica se há rotas de fuga claras e se a linguagem não é punitiva.
- **Skill ("Form Abstraction Generator"):** O LLM deve ser proibido de criar estado de formulário (`useState` para cada campo) diretamente na Screen. Ele deve ser forçado a criar um hook `useForm` customizado.
- **Prompt Constraint:** *"Toda string exibida na UI deve ser uma chave i18n. Todo Alert.alert de erro deve incluir uma ação de 'Retry' ou 'Support'."*
- **Ferramentas:** Usar um script customizado (ex: grep por acentos/português em arquivos `.tsx`) rodando no pre-commit para barrar strings hardcoded. O LLM deve rodar esse script para validar seu output.

---

### Resumo Prático de Implementação do Harness

Para implementar isso nas próximas iterações, você deve estruturar seu arquivo de configuração de sistema (ex: `CLAUDE.md`, `.cursorrules`, ou system prompt do seu agente) da seguinte forma:
 Vou analisar os relatórios e mapear, por tema, os padrões de falhas recorrentes e como um **harness preventivo** (prompts, skills, scripts, gates) poderia eliminá-los em ciclos futuros.

---

## 🔍 Análise dos Padrões de Falha

Após revisar os 20+ relatórios, identifiquei **6 categorias de falhas sistêmicas** que se repetem independentemente do domínio (segurança, arquitetura, código, testes). Abaixo, o diagnóstico por tema e o harness correspondente.

---

## 1. 🛡️ Segurança (Security)

### Erros Recorrentes Encontrados
| Falha | Ocorrência | Relatório |
|-------|-----------|-----------|
| Chave de criptografia hardcoded | `smartfix-pii-key-v1` no source | `SECURITY_AUDIT.md` C1, C2, C3 |
| Fallback para criptografia fraca (XOR) | `piiEncryption.ts` | `SECURITY_AUDIT.md` C2 |
| IV estático em AES-CBC | `new Uint8Array(16)` | `SECURITY_AUDIT.md` C6 |
| Tokens em AsyncStorage (fallback inseguro) | `authService.ts` | `SECURITY_AUDIT.md` C5, F-011 |
| JWT secret hardcoded no backend | `smartfix-dev-secret` | `SECURITY_AUDIT.md` F-007 |
| Dados PII em logs sem sanitização | `logger.ts` | `SECURITY_AUDIT.md` F-014 |
| Constantes interpoladas em SQL | `userSettingsService.ts` | `SECURITY_AUDIT.md` F-010 |
| Secrets bundled no APK (AdMob, RevenueCat) | `app.config.ts` | `SECURITY_AUDIT.md` F-013 |
| WebView sem restrição de navegação | `YouTubePlayer.tsx` | `SECURITY_AUDIT.md` F-020 |
| Compra falha silenciosamente concede premium | `purchasesService.ts` | `SECURITY_AUDIT.md` F-002 |

### Harness Preventivo

#### A. **Security Skill / System Prompt**
Criar uma skill injetada em todo ciclo de geração de código:
```
[SECURITY_HARNESS]
Antes de gerar qualquer código que envolva:
- Criptografia (encrypt/decrypt/hash)
- Autenticação (token, JWT, OAuth)
- Storage local (SQLite, AsyncStorage, SecureStore)
- Network (fetch, WebView, cert pinning)
- Monetização/IAP (RevenueCat, AdMob)
- PII (nome, email, telefone, endereço, CPF)

Execute mentalmente este checklist:
1. NUNCA hardcode keys/secrets. Derive de keystore (SecureStore/Keychain) ou env.
2. NUNCA use fallback criptográfico fraco (XOR, MD5, DES). Fail-closed.
3. NUNCA reuse IV. Use crypto.getRandomValues() por operação.
4. NUNCA armazene tokens em AsyncStorage. SecureStore apenas.
5. NUNCA interpole valores em SQL. Use parameterized queries (?).
6. NUNCA logue PII cru. Use sanitizeForLogging().
7. NUNCA permita fallback que conceda privilégios (premium, admin).
8. SEMPRE valide origin em WebView (strict hostname match).
9. SEMPRE use AES-256-GCM (não CBC) para dados sensíveis.
10. SEMPRE valide JWT secret no startup (exit se default/missing).
```

#### B. **Pre-commit Hook: Secret Scanning**
```bash
# .husky/pre-commit ou CI
npx gitleaks detect --source . --verbose
npx detect-secrets scan --all-files
# Falha o commit se encontrar padrão de secret/key/password
```

#### C. **ESLint Plugin: Security Rules**
```javascript
// eslint.config.js
import security from 'eslint-plugin-security';
export default [
  security.configs.recommended,
  {
    rules: {
      'security/detect-object-injection': 'off', // false positives
      'security/detect-unsafe-regex': 'error',
      'security/detect-non-literal-regexp': 'error',
      'security/detect-eval-with-expression': 'error',
      'security/detect-possible-timing-attacks': 'warn',
      'no-secrets/no-secrets': ['error', { tolerance: 4.5 }]
    }
  }
];
```

#### D. **Template de Código Seguro (PII + Crypto)**
Criar snippets que o LLM deve usar:
```typescript
// TEMPLATE: piiEncryption.ts
// REGRA: Key NUNCA pode ser string literal no código
const getUserEncryptionKey = async (userId: string): Promise<CryptoKey> => {
  const stored = await SecureStore.getItemAsync(`pii_key_${userId}`);
  if (!stored) throw new SecurityError('Encryption key not found');
  // Derive key from stored material...
};

// TEMPLATE: SQL queries
// REGRA: NUNCA use template literal para valores SQL
const sql = `UPDATE table SET col = ? WHERE id = ?`; // ✅
const sql = `UPDATE table SET col = ${value}`;       // ❌ BLOCKED
```

---

## 2. 🏗️ Arquitetura & Clean Architecture

### Erros Recorrentes Encontrados
| Falha | Ocorrência | Relatório |
|-------|-----------|-----------|
| Singletons com estado compartilhado entre testes | 27 singletons | `CLEAN_CODE_REPORT.md` §5.3, `singleton-migration-guide.md` |
| SQL em services (violação de camadas) | `maintenanceService.ts` JOIN | `ARCHITECTURE_AUDIT_V2.md` §1.1 |
| Business logic em screens (UI) | `HomeScreen` chama múltiplos services | `Architecture_Audit_v3.md` §2.1 |
| Pass-through methods (shallow) | 13 métodos em 3 services | `PHASE_8_PLAN.md` 8.1 |
| Sem ADRs (decisões não documentadas) | Zero ADRs inicialmente | `ARCHITECTURE_AUDIT.md` Issue 5 |
| Sem fitness functions arquiteturais | Sem `dependency-cruiser` inicial | `ARCHITECTURE_AUDIT_V2.md` §4.3 |
| Test infrastructure visível em produção | `isTestInstance()`, `getTestId()` | `PHASE_10_PLAN.md` 10.A |
| Sem Use Case / Application Layer | Screens orquestram services | `Architecture_Improvement_Plan.md` 1.1 |

### Harness Preventivo

#### A. **Architecture Guard Prompt (System Instruction)**
```
[ARCHITECTURE_HARNESS]
Para toda nova feature ou refatoração, aplique:

1. LAYERS: UI → UseCase → Service → Repository → DB
   - Screen NUNCA importa Repository ou Database diretamente
   - Service NUNCA contém SQL string (apenas Repository)
   - UseCase orquestra múltiplos services para screens

2. DEPENDENCY RULE:
   - Services dependem de abstrações (interfaces *Api)
   - Screens usam hooks useService() do ServiceContext
   - NUNCA importe singleton concreto em screen/component

3. SCREAMING ARCHITECTURE:
   - Arquivos devem estar em src/features/{domain}/ (não src/services/, src/screens/)
   - Nome do diretório deve refletir domínio (properties/, maintenance/)

4. DEPTH (Ousterhout):
   - Método > 40 linhas → extrair sub-métodos
   - Método com flag argument (isRefresh) → split em 2 métodos
   - Pass-through (delega sem lógica) → remova, aponte direto

5. ADR: Se a decisão afeta >3 arquivos ou muda boundary, crie ADR.

VALIDAÇÃO: Rode `npm run arch:check` antes de considerar pronto.
```

#### B. **Dependency Cruiser como Gate (Fitness Function)**
```javascript
// .dependency-cruiser.js
module.exports = {
  forbidden: [
    {
      name: 'no-database-in-ui',
      severity: 'error',
      from: { path: 'src/(screens|components)/' },
      to: { path: 'src/services/database' }
    },
    {
      name: 'sql-only-in-repositories',
      severity: 'error',
      from: { path: 'src/services/', pathNot: 'src/services/repositories/' },
      to: { path: 'src/services/database' } // indireto, mas captura imports
    },
    {
      name: 'no-ui-in-services',
      severity: 'error',
      from: { path: 'src/services/' },
      to: { path: 'src/(screens|components)/' }
    },
    {
      name: 'use-cases-no-react-native',
      severity: 'error',
      from: { path: 'src/use-cases/' },
      to: { path: 'react-native' }
    }
  ]
};
```

#### C. **Template de Service (evita singleton hardcoded)**
```typescript
// TEMPLATE: newService.ts
// REGRA: Todo service novo segue este padrão
export interface NewServiceApi {
  operation(): Promise<Result>;
}

export class NewService implements NewServiceApi {
  private static instance: NewService;
  
  private constructor(
    private executor: DatabaseExecutor = databaseExecutor,
    private deps: { notificationService: NotificationServiceApi } = { notificationService }
  ) {}
  
  static getInstance(): NewService { /* ... */ }
  static createTestInstance(testId: string, executor?: DatabaseExecutor): NewService { /* ... */ }
  static resetInstance(): void { /* ... */ }
  
  // Test methods NUNCA são públicos na interface *Api
  // Colocar em interface separada Testable se necessário
}
```

---

## 3. 🧹 Clean Code & SOLID

### Erros Recorrentes Encontrados
| Falha | Ocorrência | Relatório |
|-------|-----------|-----------|
| Funções gigantes (>200 linhas) | `updateRoomItem` (203), `ItemFormScreen` (1040) | `CLEAN_CODE_REPORT.md` §2.1 |
| CQS violations (comando retorna valor + side effects) | `createRoomItem` cria + agenda notificação | `CLEAN_CODE_REPORT.md` §2.4 |
| Duplicação massiva (SQL SET builder) | 265 linhas duplicadas em 4 services | `CLEAN_CODE_REPORT.md` §6.1 |
| Data Clump (5 campos de técnico) | 7+ locais | `CLEAN_CODE_REPORT.md` §6.2 |
| `return null` em 84 locais | Services `getById` | `CLEAN_CODE_REPORT.md` §4.2 |
| Magic numbers (`1000*60*60*24`, `7` dias) | 6x, 9x | `CLEAN_CODE_REPORT.md` §3.5 |
| Nomenclatura inconsistente (`getIs…`, `I` prefix) | 6 services | `CLEAN_CODE_REPORT.md` §1.2, §3.1 |
| Flag arguments (`isRefresh`) | 2 screens | `CLEAN_CODE_REPORT.md` §2.2 |
| Comentários que repetem código | JSDoc redundante | `CLEAN_CODE_REPORT.md` §3.2 |

### Harness Preventivo

#### A. **Clean Code Guard Prompt**
```
[CLEAN_CODE_HARNESS]
Antes de finalizar qualquer arquivo, execute:

1. TAMANHO: Nenhuma função > 40 linhas. Nenhum componente > 150 linhas.
   - Se passar: extrair sub-funções com nomes descritivos (Beck: Composed Method)

2. CQS: Comandos (create/update/delete) retornam void OU entidade, NUNCA ambos + side effects.
   - Side effects (notificações, badges) devem ser eventos ou chamadas explícitas separadas

3. DRY: Se você copiou/colidou >3 linhas, extraia para helper/constant.
   - Magic numbers → constantes nomeadas (MILLISECONDS_IN_DAY, NOTIFICATION_DEFAULT_DAYS)

4. NULL: Evite `return null`. Use Special Case Object (NotFoundSentinel) ou Optional.

5. NOMES:
   - Booleanos: `isPremium`, `hasPermission` (não `getIsPremium`)
   - Interfaces: `ServiceApi` (não `IService`)
   - Throwing validators: `assertValidXxx` (não `validateXxx` se throw)
   - Um conceito = uma palavra: `find` OU `get`, não ambos

6. PARÂMETROS: Máximo 3 params. Se mais, use object parameter.
   - NUNCA flag argument booleano. Split em 2 métodos.

7. DATA CLUMP: Se 3+ campos viajam juntos, crie Value Object (TechnicianContact).

8. COMENTÁRIOS: Se o comentário explica "o quê", delete e renomeie a função.
   - Comentários devem explicar "porquê" (decisões de design), não "o quê".
```

#### B. **Refactoring Automation Script**
```bash
# scripts/code-quality-gate.sh
#!/bin/bash
echo "=== Clean Code Gates ==="

# 1. Funções > 50 linhas
npx jscodeshift -t scripts/transforms/large-function-detector.ts src/

# 2. Magic numbers (exceto 0, 1, -1, 2)
grep -rn "1000 \* 60 \* 60 \* 24\|7\|30\|0.8" src/services/ src/utils/ | grep -v "const " && echo "FAIL: Magic numbers found" && exit 1

# 3. return null em services
grep -n "return null" src/services/*.ts | grep -v "test" | grep -v "// " && echo "FAIL: return null in services" && exit 1

# 4. Flag arguments
grep -n "isTest\|isRefresh\|isUpdate" src/services/*.ts src/screens/*.tsx | grep "boolean" && echo "WARN: Flag arguments detected"

echo "PASS"
```

#### C. **SonarQube / CodeClimate Rules**
Configurar thresholds quebrando build:
- Cognitive Complexity > 15 → erro
- Duplicated Lines > 3% → erro
- Function Length > 50 → erro
- Parameter Count > 4 → erro

---

## 4. 🧪 Testes & TDD

### Erros Recorrentes Encontrados
| Falha | Ocorrência | Relatório |
|-------|-----------|-----------|
| Test-After (TAD), não TDD | 0 commits test-first | `TDD_AUDIT.md` §1.1 |
| 51 hard-coded delays (`setTimeout`) | Flaky tests | `TDD_AUDIT.md` §6.1 |
| Mock routing por SQL string | 8 instâncias | `TDD_AUDIT.md` §5.2 |
| `expect(true).toBe(true)` | 8 placeholders | `TDD_CLEAN_CODE_AUDIT_REPORT.md` |
| Empty `it()` blocks | Integration tests | `TDD_CLEAN_CODE_AUDIT_REPORT.md` |
| Testes não rodam no pre-commit | Só lint/build | `TDD_AUDIT.md` §8 |
| Coverage thresholds baixos (20-30%) | Sem significado | `TDD_AUDIT.md` §7 |
| Concurrency tests quebrando | 28 falhas | `CONCURRENCY_BUG_FIX_PLAN.md` |
| Mock executor compartilhado | Isolamento quebrado | `CONCURRENCY_TEST_REFACTORING.md` |
| E2E quebrado (Detox não instalado) | Pipeline E2E inexistente | `DEVOPS_ASSESSMENT_REPORT.md` |

### Harness Preventivo

#### A. **TDD Discipline Prompt**
```
[TDD_HARNESS]
Para cada nova feature ou bug fix:

FASE VERMELHA (Red):
1. Escreva o teste ANTES do código de produção
2. O teste deve falhar (verifique rodando `npm test -- <file>`)
3. Commit: "test(red): <descrição do comportamento esperado>"

FASE VERDE (Green):
4. Escreva o mínimo de código para passar o teste
5. Não refatore ainda. Commit: "feat(green): <implementação mínima>"

FASE AZUL (Refactor):
6. Limpe duplicação, renomeie, extraia
7. Garanta que todos os testes passam
8. Commit: "refactor: <o que melhorou>"

REGRAS DE OURO:
- Nenhum código de produção sem teste que o justifique
- Nenhum teste sem assertion real (nunca `expect(true).toBe(true)`)
- Nunca use `setTimeout` em testes. Use `waitFor`, `act`, event-driven
- Mock por comportamento, não por implementação (não route por SQL string)
- Coverage threshold mínimo: 70% branches, 80% lines (globais)
```

#### B. **Pre-commit Hook: Test Gate**
```bash
# .husky/pre-commit
#!/bin/bash
echo "Running quality gates..."

# 1. Lint staged
npx lint-staged

# 2. Type check
npx tsc --noEmit

# 3. Architecture check
npx depcruise src --config .dependency-cruiser.js

# 4. UNIT TESTS (fast feedback)
npx jest --selectProjects unit --passWithNoTests --silent

# 5. Coverage check (fails if below threshold)
npx jest --coverage --collectCoverageFrom="src/**/*.{ts,tsx}" --coverageThreshold='{"global":{"branches":70,"functions":80,"lines":80,"statements":80}}'

echo "All gates passed ✅"
```

#### C. **Test Template (evita placeholders)**
```typescript
// TEMPLATE: <service>.test.ts
// ANTI-PATTERN PROIBIDO: it('should...', async () => {}); // empty
// ANTI-PATTERN PROIBIDO: expect(true).toBe(true);

describe('FeatureDomain', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    ServiceName.resetInstance();
  });

  describe('methodName', () => {
    it('should return expected result when given valid input', async () => {
      // GIVEN
      const input = { /* valid data */ };
      // WHEN
      const result = await service.methodName(input);
      // THEN
      expect(result).toEqual(expected);
    });

    it('should throw ServiceError when given invalid input', async () => {
      await expect(service.methodName(invalid)).rejects.toBeInstanceOf(ServiceError);
    });

    it('should handle edge case (empty, null, boundary)', async () => {
      // ...
    });
  });
});
```

#### D. **Flaky Test Detector Script**
```bash
# scripts/flaky-test-detector.sh
# Roda o suite 5x e detecta inconsistências
for i in {1..5}; do
  npx jest --no-cache 2>&1 | tee test-run-$i.log
done

# Compara resultados
if ! cmp -s test-run-1.log test-run-2.log; then
  echo "FLAKY TESTS DETECTED"
  exit 1
fi
```

---

## 5. ⚙️ DevOps & CI/CD

### Erros Recorrentes Encontrados
| Falha | Ocorrência | Relatório |
|-------|-----------|-----------|
| Sem GitHub Actions CI | Apenas pre-commit local | `DEVOPS_ASSESSMENT_REPORT.md` |
| Sem crash reporting (Sentry) | Erros de produção invisíveis | `DEVOPS_ASSESSMENT_REPORT.md` |
| Sem OTA updates (`expo-updates`) | Hotfix requer store review | `DEVOPS_ASSESSMENT_REPORT.md` |
| Sem `npm audit` / Dependabot | Vulnerabilidades não detectadas | `DEVOPS_ASSESSMENT_REPORT.md` |
| E2E pipeline quebrada | Detox não instalado | `DEVOPS_ASSESSMENT_REPORT.md` |
| Sem feature flags | Sem kill-switch | `DEVOPS_REMEDIATION_PLAN.md` D3.1 |
| Sem observabilidade (golden signals) | Latency, errors, traffic invisíveis | `DEVOPS_ASSESSMENT_REPORT.md` |
| Versionamento remoto (EAS), não no Git | Sem rastreabilidade | `DEVOPS_ASSESSMENT_REPORT.md` |

### Harness Preventivo

#### A. **DevOps Checklist Prompt**
```
[DEVOPS_HARNESS]
Antes de marcar qualquer task como "Done":

CI/CD:
□ `.github/workflows/ci.yml` existe e roda: lint, build, test, coverage, arch-check
□ `npm audit --audit-level=high` passa no CI
□ Dependabot configurado para weekly updates
□ Pre-commit roda: lint + type-check + unit tests

Deploy:
□ `expo-updates` instalado e configurado (OTA)
□ EAS profile `staging` existe (TestFlight/Internal Testing)
□ Feature flag system existe (mínimo: src/config/features.ts)
□ Crash reporting (Sentry) integrado e testado

Observability:
□ Logs estruturados com PII sanitization
□ Sentry breadcrumbs para errors
□ Dashboard de health check (/health no backend)
□ Alertas configurados (5xx, uptime, RTDN failures)

Security:
□ Secrets em EAS Secrets / SecureStore (nunca no repo)
□ SBOM gerado no release (`npm run sbom`)
□ SSL pinning hashes configurados para produção
```

#### B. **GitHub Actions Template**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: 'npm' }
      
      - run: npm ci
      - run: npm run lint
      - run: npm run build
      - run: npm run test:unit -- --passWithNoTests
      - run: npm run test:integration -- --passWithNoTests
      - run: npm run test:coverage
      - run: npm run arch:check
      - run: npm audit --audit-level=high
      
      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const coverage = require('./coverage/coverage-summary.json');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              body: `📊 Coverage: ${coverage.total.lines.pct}% lines, ${coverage.total.branches.pct}% branches`
            });
```

---

## 6. 📋 Meta-Harness: Orquestração do LLM

O problema mais profundo observado nos relatórios é que **o LLM gerou código funcional mas sem as guardas de qualidade**. O harness final deve ser um **orquestrador de prompts/skills** que o LLM consulta obrigatoriamente.

### A. **Master Prompt (injetado no início de toda sessão)**
```
Você é um engenheiro sênior seguindo rigorosamente:

1. [SECURITY_HARNESS] - Todo código criptográfico/autenticação/PII
2. [ARCHITECTURE_HARNESS] - Todo novo service/screen/repository  
3. [CLEAN_CODE_HARNESS] - Todo método/classe/componente
4. [TDD_HARNESS] - Todo novo comportamento (Red-Green-Refactor)
5. [DEVOPS_HARNESS] - Todo deploy/infra/config

REGRA DE OURO: Se um arquivo NÃO passar nos gates abaixo, ele NÃO está pronto:
- `npm run lint` limpo
- `npm run build` limpo (tsc --noEmit)
- `npm run arch:check` limpo (0 violations)
- `npm test` passando (sem skips, sem `expect(true).toBe(true)`)
- Coverage não regrediu

Você NUNCA deve:
- Hardcode secrets, keys, ou passwords
- Usar `return null` em services sem justificativa documentada
- Criar funções > 40 linhas
- Deixar SQL em services (apenas repositories)
- Escrever testes vazios ou placeholders
- Adicionar side effects em comandos sem eventos explícitos
```

### B. **Skill Files (documentação técnica do projeto)**
Criar no repo:
- `.llm/skills/security.md` — Checklist OWASP + patterns seguros
- `.llm/skills/architecture.md` — Regras de camadas, DIP, ADR template
- `.llm/skills/clean-code.md` — Heurísticas de tamanho, nome, CQS, DRY
- `.llm/skills/testing.md` — TDD cycle, mock patterns, flaky prevention
- `.llm/skills/devops.md` — CI/CD gates, deploy checklist, observability

### C. **Self-Validation Script**
```bash
# scripts/llm-validation.sh
# Roda após o LLM "terminar" uma task
echo "🔍 LLM Output Validation"

# 1. Nenhum secret hardcoded
if grep -rn "smartfix-pii-key\|smartfix-dev-secret\|sk-.*[0-9]" src/; then
  echo "❌ HARDCODED SECRET DETECTED"; exit 1
fi

# 2. Nenhum return null em service novo
if grep -n "return null" src/services/*.ts | grep -v "test" | grep -v "repository"; then
  echo "⚠️  return null in services - justify or use NotFoundSentinel"
fi

# 3. Nenhuma função > 50 linhas
npx jscodeshift -t scripts/transforms/count-lines.ts src/

# 4. Nenhum SQL fora de repositories
if grep -rn "INSERT INTO\|UPDATE.*SET\|DELETE FROM" src/services/*.ts | grep -v "repositories/"; then
  echo "❌ SQL OUTSIDE REPOSITORY"; exit 1
fi

# 5. Todos os testes têm assertions reais
if grep -rn "expect(true).toBe(true)\|it('.*',.*async.*=>.*{.*}\s*)" src/__tests__/; then
  echo "❌ PLACEHOLDER TESTS DETECTED"; exit 1
fi

echo "✅ LLM output passed validation"
```

---

## 📊 Resumo: Matriz de Prevenção

| Tema | Erro Típico | Harness Principal | Automação |
|------|-------------|-------------------|-----------|
| **Segurança** | Hardcoded keys, fallback inseguro | Security Skill + Secret scanning | `gitleaks`, `eslint-plugin-security`, `npm audit` |
| **Arquitetura** | SQL em service, DIP violation | Architecture Guard Prompt | `dependency-cruiser`, `arch:check` |
| **Clean Code** | Função 200 linhas, magic numbers | Clean Code Heuristics | SonarQube, custom script |
| **TDD/Testes** | Test-after, flaky delays, placeholders | TDD Discipline Prompt | Pre-commit test gate, flaky detector |
| **DevOps** | Sem CI, sem OTA, sem observability | DevOps Checklist | GitHub Actions, Sentry, `expo-updates` |
| **Meta** | LLM gera sem guardas | Master Prompt + Self-Validation | `scripts/llm-validation.sh` |

---

## 🎯 Recomendação Final

Para que estes erros **nunca mais se repitam**, implemente este pipeline:

1. **Início do projeto**: Injetar o **Master Prompt** + **5 Skills** no contexto do LLM
2. **Durante desenvolvimento**: LLM gera código → roda **Self-Validation Script** localmente
3. **Pre-commit**: Hook executa lint + type-check + **unit tests** + arch-check
4. **Pull Request**: CI executa suite completa + **coverage gate** + **security audit**
5. **Deploy**: Checklist DevOps (OTA, Sentry, feature flags, SSL pinning)

A raiz de quase todos os problemas nos relatórios é a **ausência de feedback automático no momento da geração**. O harness transforma "escrever código" em "escrever código que passa em gates verificáveis automaticamente" — e isso é o que impede a regressão.

*******************

1. **Regras Invioláveis (Hard Constraints):** Cole as restrições diretas (ex: "NUNCA use `any`", "NUNCA retorne `null`", "SQL apenas em repositories").
2. **Checklist de Geração:** Force o LLM a passar por um checklist antes de exibir o código final:
   - [ ] O código passa no `tsc --noEmit` e `eslint`?
   - [ ] Os testes foram escritos antes da implementação?
   - [ ] Os segredos estão em variáveis de ambiente?
   - [ ] As strings estão internacionalizadas?
3. **Uso de Ferramentas (Tool Calling):** Dê ao LLM acesso ao terminal para rodar `npm test`, `npm run arch:check` e `git lint`. O agente deve iterar no código até que essas ferramentas retornam sucesso.

Ao transformar os achados dos relatórios em *regras de validação automatizadas* e *restrições de prompt*, você fecha o cerco para o LLM, garantindo que ele não tenha espaço para repetir esses desvios arquiteturais ou de qualidade.


****************
Qwen 

Excelente iniciativa. Analisar os relatórios de auditoria para retroalimentar o "harness" (o conjunto de prompts, skills, ferramentas e processos que guiam a IA) é o passo mais maduro no desenvolvimento assistido por LLMs. 

Os relatórios mostram um padrão claro: **LLMs são excelentes em gerar a "feliz caminho" (happy path) de funcionalidades isoladas, mas são cegos para requisitos não-funcionais, empatia de UX, limites de arquitetura e segurança em repouso/trânsito.**

Abaixo, apresento um diagnóstico dos **5 Pontos Cegos do LLM** baseados nos seus relatórios e, em seguida, **como configurar o seu Harness** para blindar as próximas iterações e projetos contra esses erros.

---

### 1. O Diagnóstico: Por que o LLM cometeu esses erros?

| Domínio | O Erro Recorrente (Baseado nos Relatórios) | A Causa Raiz no LLM |
| :--- | :--- | :--- |
| **Segurança** | PII em texto puro, fallback para XOR/AsyncStorage, bypass de premium no client, falta de `user_id`. | O LLM prioriza a *funcionalidade imediata* (fazer o app rodar) em detrimento da *defesa em profundidade*. Ele assume um ambiente de confiança (localhost). |
| **Arquitetura / Clean Code** | Telas de 1000+ linhas (`ItemFormScreen`), violação de SRP, métodos "pass-through", acoplamento de Singletons. | O LLM não tem "consciência espacial" de arquivos. Se você pede "uma tela de formulário", ele gera tudo em um único bloco de código monolítico. |
| **UX / UI** | *Confirmshaming* no onboarding, *Roach Motel* no paywall, falta de recuperação de erros, ausência de personas. | O LLM implementa **requisitos técnicos**, não **jornadas de usuário**. Ele não sente a frustração do usuário ao ver um alerta genérico de erro. |
| **Testes (TDD)** | Test-After (TAD), blocos vazios (`expect(true).toBe(true)`), mocks frágeis com `setTimeout`. | O LLM é uma máquina de completude. Se pede "teste para cobrir X", ele escreve o teste para *passar*, não para *desenhar* o código. |
| **DevOps** | Ausência de CI/CD, sem crash reporting, sem OTA, sem varredura de secrets. | O LLM foca no `src/`. O ciclo de vida operacional (build, deploy, observabilidade) é ignorado a menos que seja explicitamente exigido. |

---

### 2. Como Evitar: A Evolução do Harness

Para que esses erros não se repitam, você deve transformar as lições dos relatórios em **barreiras automatizadas (Guardrails)** e **Skills de Contexto**.

#### A. Segurança & Privacidade (Foco: OWASP & Defesa em Profundidade)
*O problema: O LLM criou criptografia "teatral" (chave hardcoded, fallback XOR).*
* **Skill de Contexto (`SECURITY_FIRST.md`):** Crie uma skill que o LLM deve consultar antes de criar qualquer modelo de dados ou serviço de rede. Ela deve conter um checklist: *Os dados são PII? Onde a chave será armazenada (Keystore/SecureStore)? Há fallback para plaintext? (A resposta deve ser sempre: falhar fechado / fail-closed).*
* **Ferramenta (SAST no Pre-commit):** Integre o `eslint-plugin-security` e o `gitleaks` (ou `trufflehog`) no hook de pre-commit. O LLM não deve conseguir commitar se houver regex de chave hardcoded ou fallback inseguro.
* **Prompt Pattern (Threat Modeling):** Antes de pedir para o LLM codar uma feature de pagamento ou backup, use o prompt: *"Atue como um Auditor de Segurança. Liste as 3 maiores ameaças (OWASP) para esta feature e me diga como a arquitetura deve mitigá-las antes de escrevermos o código."*

#### B. Arquitetura & Clean Code (Foco: Limites e SOLID)
*O problema: Telas monolíticas e serviços "Deus" (God Classes).*
* **Skill de Arquitetura (`ARCHITECTURE_BOUNDARIES.md`):** Documente as regras de dependência (ex: UI nunca fala com DB, Services não conhecem SQLite). 
* **Ferramenta (Dependency Cruiser):** O relatório já menciona o `dependency-cruiser`. **Regra de Ouro:** O LLM só pode considerar uma task "concluída" se o script `npm run arch:check` passar. Isso força o LLM a refatorar e extrair hooks/use-cases em vez de acoplar a tela ao serviço.
* **Prompt Pattern (Composed Method):** Ao pedir telas complexas, use a instrução: *"Não escreva a tela inteira. Primeiro, extraia a lógica de estado para um hook `useForm`. Depois, crie os sub-componentes de UI. Por fim, monte a tela. Limite de 50 linhas por função."*
* **Regra de Code Review por IA:** Antes de abrir o PR, rode um script que chama a API do LLM com o prompt: *"Aplique a heurística de Martin (Clean Code) e Ousterhout (Profundidade de Módulo) neste diff. Aponte funções com mais de 20 linhas ou violações de CQS."*

#### C. UX / UI (Foco: Empatia e Heurísticas de Nielsen)
*O problema: O LLM criou anti-padrões de dark pattern (confirmshaming) e ignorou a recuperação de erros.*
* **Skill de UX (`UX_PERSONAS_AND_HEURISTICS.md`):** Alimente o LLM com as Personas (Maria, Carlos, Ana) e as 10 Heurísticas de Nielsen. 
* **Prompt Pattern (Journey Mapping):** Nunca peça "Crie a tela de Paywall". Peça: *"Mapeie a jornada do usuário quando ele atinge o limite gratuito. Qual a emoção dele? Desenhe a UI aplicando a heurística de Nielsen #3 (Controle e Liberdade do Usuário) para evitar o anti-padrão Roach Motel."*
* **Ferramenta (UX Linter / Accessibility Test):** O relatório aponta falta de testes de acessibilidade e strings hardcoded. Crie um script de teste que falha se encontrar `Alert.alert` sem botão de "Retry" ou "Suporte", ou se encontrar strings em português fora dos arquivos de `locales/`.

#### D. Testes & TDD (Foco: Test-First e F.I.R.S.T.)
*O problema: O LLM escreveu testes para cobrir métricas, não para validar comportamento.*
* **Skill de TDD (`TDD_RED_GREEN_REFACTOR.md`):** Instrução explícita no system prompt: *"Você opera em modo TDD estrito. Você NÃO escreverá código de produção até que eu aprove o teste falhando (Red). Você NÃO escreverá mais código do que o necessário para passar (Green)."*
* **Ferramenta (Coverage Gate com Mutação):** Thresholds de cobertura enganam o LLM. Use ferramentas de **Mutation Testing** (como Stryker). Se o LLM escrever `expect(true).toBe(true)`, o mutation testing vai matar o teste e o CI vai falhar.
* **Prompt Pattern (Triangulação):** *"Escreva testes para esta função de validação usando a técnica de Triangulação do Kent Beck: forneça pelo menos 3 exemplos de borda (edge cases) antes de implementar a função."*

#### E. DevOps & Observabilidade (Foco: Shift-Left e Automação)
*O problema: O app é construído, mas não há pipeline, nem crash reporting.*
* **Skill de DevOps (`DEVOPS_CHECKLIST.md`):** Toda vez que uma nova feature crítica for criada, o LLM deve atualizar o `CLAUDE.md` ou `AGENTS.md` com os requisitos de deploy (ex: "Esta feature exige OTA update? Precisa de feature flag?").
* **Ferramenta (CI/CD como Gate):** O GitHub Actions deve rodar `npm audit`, `tsc --noEmit`, `jest --coverage` e `depcruise`. O LLM deve ser instruído a ler os logs do CI para corrigir os próprios erros antes de chamar o desenvolvedor humano.

---

### 3. O Fluxo de Trabalho (Workflow) Sugerido para o Futuro

Para institucionalizar essas melhorias, sugiro a seguinte estrutura de **Agentes/Fases** no seu prompt inicial ou no `AGENTS.md` do projeto:

```markdown
# AGENTS.md - Regras de Operação do LLM

## 1. O Ciclo de Vida da Feature (Obrigatório)
Toda nova feature deve seguir esta ordem. Não pule etapas.
1. **UX & Threat Modeling:** Definir Persona, Heurística de Nielsen aplicada e matriz de ameaças (OWASP).
2. **Test-First (Red):** Escrever os testes de integração e unidade (incluindo edge cases e mocks realistas).
3. **Implementação (Green):** Escrever o código mínimo para passar. Respeitar os limites do `dependency-cruiser`.
4. **Refatoração (Refactor):** Extrair hooks, aplicar Clean Code (Ousterhout/Beck), remover duplicações.
5. **DevOps:** Atualizar CI, adicionar métricas de observabilidade (analytics/UX events).

## 2. Barreiras Intransponíveis (Hard Gates)
- **NUNCA** armazenar tokens ou PII em AsyncStorage. Use `expo-secure-store`.
- **NUNCA** criar fallbacks de criptografia para texto puro ou XOR. Falhe fechado (throw error).
- **NUNCA** escrever queries SQL com interpolação de string. Apenas parâmetros (`?`).
- **NUNCA** criar telas com mais de 150 linhas. Extraia para `useForm` e sub-componentes.
- **NUNCA** criar `Alert.alert` de erro sem opções de Retry ou Suporte.

## 3. Ferramentas de Validação (O LLM deve rodar antes de terminar)
Antes de reportar conclusão, o LLM deve executar e aprovar:
- `npm run arch:check` (Dependency Cruiser)
- `npm run test:coverage` (Jest)
- `npm run lint` (ESLint + Security)
```

### Resumo da Estratégia
O segredo não é pedir para o LLM "ser mais seguro" ou "escrever código mais limpo". O segredo é **mudar o ambiente em que ele opera**. 
1. **Skills** dão a ele o conhecimento das heurísticas (Nielsen, OWASP, SOLID).
2. **Prompts** forçam a ordem correta das coisas (TDD, Threat Modeling).
3. **Tools/Scripts** (dependency-cruiser, SAST, Mutation Testing) atuam como o "professor rigoroso" que não deixa o LLM entregar trabalho pela metade ou com atalhos perigosos.

Se você adicionar essas regras ao seu `AGENTS.md` e configurar os hooks de CI, na próxima iteração os relatórios de auditoria mostrarão uma evolução drástica, pois o LLM será "forçado" a respeitar os limites da engenharia de software moderna.

***********************************


Com base na análise profunda dos seus relatórios de auditoria (que identificaram e resolveram falhas críticas como criptografia "teatral", fallback para texto puro, falta de modelo de propriedade e validação de entitlements apenas no cliente), criei o arquivo **`SECURITY_FIRST.md`**.

Este documento foi desenhado para ser usado como uma **Skill de Contexto**, **Regra de Agente** (ex: `.cursor/rules/`, `AGENTS.md`, `CLAUDE.md`) ou **Checklist de Shift-Left**. Ele atua como uma "barreira intransponível" para impedir que o LLM (ou desenvolvedores) reintroduzam vulnerabilidades conhecidas.

---

# 🛡️ SECURITY_FIRST.md - Regras Intransponíveis de Segurança e Privacidade

**Propósito:** Este documento define os padrões de segurança e privacidade obrigatórios para o projeto. Qualquer código gerado, refatorado ou revisado que viole estas regras deve ser **imediatamente rejeitado**. A segurança não é um "feature", é um requisito não-funcional base.

**Metodologia:** Defesa em Profundidade (Gupta) & Fail-Closed (OWASP).

---

## 🛑 1. Hard Gates (Regras Intransponíveis)
*O LLM/Desenvolvedor NUNCA deve:*

1. **NUNCA** armazenar tokens de autenticação, chaves de criptografia ou PII em `AsyncStorage`. Use **exclusivamente** `expo-secure-store` (ou Keychain/Keystore).
2. **NUNCA** criar fallbacks de criptografia para texto puro, XOR ou cifras fracas (ex: AES-CBC com IV estático). **Se a criptografia falhar, o sistema deve falhar fechado (throw error).**
3. **NUNCA** escrever queries SQL com interpolação de string (`${var}`). Use apenas parâmetros (`?`).
4. **NUNCA** confiar no cliente para validação de Premium/Entitlements. O backend é a única fonte da verdade.
5. **NUNCA** logar PII (emails, telefones, CPF, endereços) ou stack traces completos em ambientes de produção.
6. **NUNCA** versionar arquivos `.env` com secrets reais. Use `.env.example` para documentação e EAS Secrets / Variáveis de Ambiente do CI para produção.
7. **NUNCA** criar tabelas de entidades sem uma coluna de propriedade (`user_id` / `owner_id`).

---

## 📋 2. Checklist de Implementação por Domínio

### 🔐 2.1. Criptografia e Dados em Repouso (PII)
- [ ] **Algoritmo:** Usar apenas **AES-256-GCM** (criptografia autenticada). Nunca AES-CBC.
- [ ] **Chaves:** Chaves devem ser derivadas por usuário e armazenadas no Keystore do dispositivo (`pii_key_{userId}`). Nunca hardcodar chaves no código-fonte.
- [ ] **IVs:** O IV (Initialization Vector) deve ser gerado aleatoriamente (`crypto.getRandomValues()`) para *cada* operação de criptografia.
- [ ] **Fronteira de Criptografia:** A criptografia/descriptografia de PII deve ocorrer na **Service Layer**, nunca na Repository/Database Layer. O banco de dados lida apenas com strings cifradas (ex: `ENC2:...`).
- [ ] **Backups:** Arquivos de backup devem ser criptografados com chave per-user antes de tocar o sistema de arquivos.
- [ ] **Fotos:** Se contiverem dados sensíveis, devem ser criptografadas em repouso ou armazenadas em diretórios protegidos pelo OS.

### 🗄️ 2.2. Armazenamento Seguro (Storage)
- [ ] **Wrapper Obrigatório:** Criar e usar um `secureStorage.ts` que encapsule `expo-secure-store`.
- [ ] **Fail-Closed:** Se o `SecureStore` não estiver disponível (ex: Expo Go), o app deve **lançar um erro** ou bloquear o login. **Nunca** fazer fallback silencioso para `AsyncStorage`.
- [ ] **Cache:** O `CacheService` nunca deve ser usado para dados sensíveis. Adicionar guardas de tipo ou documentação explícita.

### 🛡️ 2.3. Controle de Acesso, Autorização e Ownership
- [ ] **Modelo de Propriedade:** Todas as queries de leitura/escrita devem filtrar por `user_id`. O `user_id` deve ser obtido de forma segura (ex: `ownershipGuard.getUserId()`).
- [ ] **Entitlements (Premium):**
  - O app deve chamar o backend (`/me/entitlements`).
  - Implementar cache local com TTL curto (ex: 5 minutos) para resiliência offline.
  - **Regra de Ouro:** Se offline e o cache expirou, o padrão deve ser **Free Tier** (nunca assumir Premium por dados locais stale).
- [ ] **Limites (Freemium):** A verificação de limites (ex: `canAddRoom()`) deve ocorrer no Service e ser refletida na UI (ex: `LimitationBanner`), nunca bloqueando o app com modais sem saída (evitar *Roach Motel*).

### 🛑 2.4. Validação de Input e Anti-Injeção
- [ ] **Validação na Fronteira:** Usar validadores estritos (ex: `assertValidTextInput`, Zod) em todos os métodos `create()` e `update()` da Service Layer.
- [ ] **SQL Dinâmico:** Se for necessário construir cláusulas `SET` dinâmicas, usar **Allowlists** de colunas (`allowedColumns.includes(col)`).
- [ ] **Path Traversal:** Sanitizar nomes de arquivos e validar caminhos base (`isPathSafe()`) ao restaurar backups ou fotos. Rejeitar `../`, null bytes e URLs encodadas.
- [ ] **CSV Injection:** Escapar células que comecem com `=`, `+`, `-`, `@` ao gerar relatórios CSV.

### 🌐 2.5. Rede e Comunicação
- [ ] **SSL Pinning:** Implementar pinning de certificado para a API backend. Os hashes SHA-256 devem ser injetados via variáveis de ambiente no build (`SSL_PIN_HASHES`), nunca no código.
- [ ] **Backend (CORS & Headers):** Usar `helmet`. CORS deve restringir origens (ex: `smartfix://`). **Nunca** permitir `file://` ou `*`.
- [ ] **Rate Limiting:** Endpoints de autenticação (`/auth/google`) devem ter rate limiting (ex: 10 req/min/IP).

### 🔑 2.6. Autenticação e Sessão
- [ ] **Tokens:** Usar Access Tokens de curta duração (15min) + Refresh Tokens (30d) com rotação.
- [ ] **Validação de ID Token:** Validar `exp`, `aud` e `iss` de tokens OAuth (ex: Google) no cliente antes de enviar ao backend.
- [ ] **Webhooks:** Webhooks de pagamento (ex: Google Play RTDN) devem verificar assinatura ou shared secret (`X-Webhook-Secret`).

### 📝 2.7. Logs, Erros e Observabilidade
- [ ] **Sanitização de Logs:** O `Logger` deve aplicar regex para mascarar PII (emails, telefones, CPF, CNPJ, Cartões) antes de escrever.
- [ ] **Mensagens de Erro:** A UI deve receber apenas mensagens genéricas e seguras (`ServiceError.userMessage`). Detalhes técnicos (SQL, paths) devem ir apenas para logs internos/sentry.
- [ ] **Debug em Produção:** Logs de nível `debug` devem ser removidos ou desativados via `__DEV__` em builds de produção.

---

## 🧠 3. Prompt Patterns para o LLM (Threat Modeling)

Antes de implementar qualquer feature que envolva dados sensíveis, rede ou permissões, o LLM deve executar o seguinte raciocínio (Chain of Thought):

```markdown
### 🛡️ Threat Modeling Check (Obrigatório antes de codar)
1. **Quais dados são PII ou sensíveis?** (Ex: endereço, telefone, token).
2. **Onde eles serão armazenados?** (Ex: SQLite, SecureStore, Backend).
3. **Como serão protegidos em repouso?** (Ex: AES-256-GCM, chave per-user).
4. **Como serão protegidos em trânsito?** (Ex: HTTPS, SSL Pinning).
5. **Quem tem acesso?** (Ex: A query está filtrada por `user_id`?).
6. **O que acontece se falhar?** (Ex: Se o SecureStore falhar, eu faço fallback para texto puro? NÃO. Eu lanço um erro).
```

---

## 🏗️ 4. Padrões de Implementação (Snippets de Referência)

### 4.1. Wrapper de Armazenamento Seguro (Fail-Closed)
```typescript
// src/utils/secureStorage.ts
import * as SecureStore from 'expo-secure-store';

export const secureStorage = {
  async getItem(key: string): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(key);
    } catch (error) {
      // NUNCA fallback para AsyncStorage
      throw new Error(`SecureStore read failed for ${key}`); 
    }
  },
  async setItem(key: string, value: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(key, value);
    } catch (error) {
      throw new Error(`SecureStore write failed for ${key}`);
    }
  }
};
```

### 4.2. Sanitização de Logs
```typescript
// src/utils/logger.ts
const PII_REGEX = /(\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b|\b\d{3}\.\d{3}\.\d{3-\d{2}|[0-9]{11}|[0-9]{14}\b)/g;

function sanitizeForLogging(data: any): string {
  const str = typeof data === 'string' ? data : JSON.stringify(data);
  return str.replace(PII_REGEX, '[REDACTED]');
}
```

### 4.3. Validação de Entitlements (Offline-First com Fail-Safe)
```typescript
// src/services/subscriptionService.ts
async function checkPremiumStatus(userId: string): Promise<boolean> {
  try {
    const backendStatus = await api.get('/me/entitlements');
    await cacheEntitlement(backendStatus); // TTL 5 min
    return backendStatus.isPremium;
  } catch (error) {
    // Fallback: Se offline, usa cache. Se cache expirado, DEFAULT PARA FREE.
    const cached = await getCachedEntitlement();
    if (cached && !isExpired(cached)) return cached.isPremium;
    
    return false; // FAIL-SAFE: Nunca assume premium por dados locais stale
  }
}
```

---

## 🚦 5. Fitness Functions (Automação no CI/CD)
Para garantir que estas regras não sejam violadas no futuro, o pipeline de CI deve executar:
1. **SAST:** `eslint-plugin-security` e `gitleaks` (ou `trufflehog`) no pre-commit.
2. **Dependency Cruiser:** Regras para impedir que a UI acesse diretamente o banco de dados ou módulos de criptografia.
3. **Secret Scanning:** Bloquear commits que contenham padrões de chaves privadas ou tokens.
4. **Audit:** `npm audit --audit-level=high` no CI.

---

### 💡 Como usar este arquivo no seu Harness:
1. **No `AGENTS.md` ou `CLAUDE.md`:** Adicione a linha: *"Antes de escrever código para Services, Database ou Auth, consulte e obedeça estritamente as regras em `docs/SECURITY_FIRST.md`."*
2. **Como System Prompt:** Se você usa ferramentas como Cursor ou Copilot Workspace, adicione este arquivo como uma `@Rule` ou `@Docs` globais.
3. **Code Review por IA:** Peça para o LLM: *"Revise este diff usando o checklist do SECURITY_FIRST.md. Aponte qualquer violação de Hard Gate."*

******************************

Com base na análise profunda dos relatórios de auditoria de arquitetura (Clean Architecture, Ousterhout, Richards-Ford, Stemmler) e clean code (Martin, Beck, Fowler, Seemann, Hock), criei o arquivo **`ARCHITECTURE_BOUNDARIES.md`**. 

Este documento atua como uma **Skill de Contexto** e **Barreira Intransponível** para impedir que o LLM reintroduza "God Classes", violações da Dependency Rule, duplicação de código, métodos pass-through e anti-padrões de design.

---

# 🏛️ ARCHITECTURE_BOUNDARIES.md - Regras Intransponíveis de Arquitetura e Clean Code

**Propósito:** Este documento define os padrões de arquitetura, design e clean code obrigatórios para o projeto. Qualquer código gerado, refatorado ou revisado que viole estas regras deve ser **imediatamente rejeitado**. 
**Metodologia:** Clean Architecture (Martin) · A Philosophy of Software Design (Ousterhout) · SOLID (Stemmler) · Refactoring (Fowler) · Implementation Patterns (Beck).

---

## 🛑 1. Hard Gates (Regras Intransponíveis)
*O LLM/Desenvolvedor NUNCA deve:*

1. **NUNCA** escrever `raw SQL` (ex: `INSERT INTO`, `SELECT * FROM`) fora da camada de **Repositories**.
2. **NUNCA** importar singletons concretos (ex: `import { propertyService }`) em **Screens, Contexts ou Hooks**. Usar exclusivamente o hook de injeção (ex: `useServices()`).
3. **NUNCA** criar funções/métodos com mais de **30-40 linhas**. Aplicar o padrão *Composed Method* (Beck).
4. **NUNCA** criar componentes de tela (Screens) com mais de **150 linhas**. Extrair lógica para hooks (ex: `useForm`, `useHomeScreenData`) e sub-componentes.
5. **NUNCA** retornar `null` para entidades não encontradas. Usar **Special Case / Null Object Pattern** (ex: `NotFoundSentinel`).
6. **NUNCA** violar CQS (Command-Query Separation). Um método `createX()` ou `updateX()` **não deve** ter efeitos colaterais ocultos (ex: agendar notificações, atualizar badges). Usar Domain Events ou Orquestradores.
7. **NUNCA** duplicar lógica de construção de SQL (`SET clause = ?`), loops de criptografia/descriptografia PII, ou formatação de datas (`toISOString().split('T')[0]`). Extrair para utilitários compartilhados.
8. **NUNCA** usar `switch` ou `if/else` em cascata para lógica de negócio extensível (ex: formatos de relatório, tipos de integração). Usar **Strategy Pattern / Registry Map**.
9. **NUNCA** expor nomes de tabelas, colunas ou dependências de framework (`expo-*`, `react-native-*`) na camada de Domínio/Serviços.
10. **NUNCA** criar *Pass-Through Methods* (métodos que apenas repassam chamadas para outra classe sem adicionar valor).

---

## 📋 2. Checklist de Implementação por Domínio

### 🧅 2.1. Camadas e Dependency Rule (Martin / Stemmler)
A arquitetura deve seguir rigorosamente o fluxo de dependência:
`UI (Screens/Components) → Use Cases / Hooks → Services (Application) → Repositories → Database`

- [ ] **UI Layer:** Contém apenas lógica de apresentação, roteamento e chamadas a Use Cases/Hooks. Zero SQL. Zero acesso direto a repositórios.
- [ ] **Use Cases / Hooks:** Orquestram múltiplos serviços para atender a uma jornada de usuário (ex: `GetHomeScreenDataUseCase`). Retornam DTOs prontos para a UI (ex: `StatDisplay[]`), não entidades cruas do banco.
- [ ] **Service Layer:** Contém regras de negócio puras. Não conhece SQLite, não conhece `expo-file-system`. Depende de interfaces de Repositórios.
- [ ] **Repository Layer:** Encapsula **TODO** o SQL. Mapeia linhas do banco para Entidades de Domínio.
- [ ] **Database Layer:** Conexão, migrações e pragmas. Isolada do resto do sistema.

### 🧼 2.2. Clean Code & Funções (Ousterhout / Beck / Martin)
- [ ] **Composed Method:** Funções públicas devem ler como uma história de alto nível, delegando passos para funções privadas de mesmo nível de abstração.
- [ ] **Data Clumps:** Se 3 ou mais campos aparecem juntos frequentemente (ex: `technicianName`, `phone`, `email`, `company`, `address`), extrair para um **Value Object** (ex: `TechnicianContact`).
- [ ] **Magic Numbers:** Números como `1000 * 60 * 60 * 24` ou `7` (dias de notificação) devem ser constantes nomeadas (`MILLISECONDS_IN_DAY`, `NOTIFICATION_DEFAULT_DAYS`).
- [ ] **Primitive Obsession:** Usar tipos de domínio corretos. Ex: `notificationsEnabled: boolean` (não `number`), `photos: Photo[]` (não `string` JSON).
- [ ] **Flag Arguments:** Evitar booleanos em parâmetros (ex: `loadData(isRefresh)`). Dividir em dois métodos: `loadData()` e `refreshData()`.

### 🏗️ 2.3. SOLID & Design Patterns (Stemmler / Fowler)
- [ ] **SRP (Single Responsibility):** Se o nome da classe tem "and" (ex: `ItemAndPhotoService`), ou se ela faz CRUD + Agendamento + Validação, ela deve ser dividida.
- [ ] **OCP (Open/Closed):** Para adicionar um novo formato de relatório ou tipo de calendário, o código existente **não deve ser modificado**. Usar `Map<Type, Handler>` ou Registros.
- [ ] **DIP (Dependency Inversion):** Contextos e Hooks devem receber dependências via props/Context API, nunca importar o arquivo do singleton diretamente.
- [ ] **Domain Events:** Para comunicação entre bounded contexts (ex: quando um Item é criado, notificar o serviço de Notificações), usar um `EventBus` em vez de acoplamento direto.

### 🏷️ 2.4. Nomenclatura e Contratos (Silén / Martin)
- [ ] **Validadores:** 
  - `assertValid*()` → Lança exceção se inválido.
  - `isValid*()` → Retorna `boolean`.
  - `validate*()` → Retorna `ValidationResult { isValid, errors }`.
- [ ] **Queries vs Commands:** 
  - `get*` / `find*` → Retornam dados (Queries).
  - `create*` / `update*` / `delete*` → Mutam estado (Commands).
- [ ] **Consistência:** Escolher UM verbo por conceito. (Ex: sempre `find*` para repositórios, sempre `get*` para serviços).

---

## 🧠 3. Prompt Patterns para o LLM (Architecture Threat Modeling)

Antes de implementar qualquer feature nova ou refatoração, o LLM deve executar o seguinte raciocínio (Chain of Thought):

```markdown
### 🏛️ Architecture & Clean Code Check (Obrigatório antes de codar)
1. **Qual camada está sendo alterada?** (UI, Use Case, Service, Repository). A dependência aponta para dentro?
2. **Qual o tamanho do método?** (Se > 30 linhas, como posso decompor em Composed Methods?).
3. **Há efeitos colaterais ocultos?** (Se é um Command, ele deve retornar void ou a entidade. Não deve agendar notificações silenciosamente).
4. **Há duplicação?** (Estou construindo SQL SET clause? Estou criptografando PII campo a campo? -> Extrair para utilitário).
5. **Qual o contrato de erro?** (Se a entidade não existir, retornarei um Special Case ou lançarei exceção? NUNCA `return null`).
6. **A UI está orquestrando lógica?** (Se a Screen chama 3 serviços diferentes e monta a resposta, extrair para um Use Case).
```

---

## 🏗️ 4. Padrões de Implementação (Snippets de Referência)

### 4.1. Special Case Pattern (Substituindo `return null`)
```typescript
// ❌ ERRADO (Obriga o caller a fazer null-check)
async getById(id: number): Promise<Property | null> { ... }

// ✅ CORRETO (Special Case / Sentinel)
const NOT_FOUND_PROPERTY: Property = { id: -1, name: 'Not Found', /* ... */ };

async getById(id: number): Promise<Property> {
  const row = await this.repository.findById(id);
  return row ? mapRowToProperty(row) : NOT_FOUND_PROPERTY;
}

// Caller fica limpo:
const property = await propertyService.getById(id);
if (property.id === -1) return showError();
```

### 4.2. Composed Method (Evitando funções de 200+ linhas)
```typescript
// ❌ ERRADO (Mistura validação, criptografia, SQL e efeitos colaterais)
async updateRoomItem(id: number, updates: UpdateRoomItem): Promise<RoomItem> {
  // 150 linhas de ifs, encryptPii, buildSetClause, execute, scheduleNotification...
}

// ✅ CORRETO (Facade delegando para passos de mesmo nível)
async updateRoomItem(id: number, updates: UpdateRoomItem): Promise<RoomItem> {
  const validatedId = assertValidId(id, 'id');
  const encryptedUpdates = await this.encryptPiiFields(updates);
  const { setClause, values } = SetClauseBuilder.forItemUpdate(encryptedUpdates);
  
  const updatedItem = await this.executeItemUpdate(validatedId, setClause, values);
  
  // Efeito colateral explícito e orquestrado (ou via Domain Event)
  await this.maintenanceOrchestrator.syncNotificationsAfterMutation(validatedId);
  
  return updatedItem;
}
```

### 4.3. Use Case Pattern (Tirando lógica da UI)
```typescript
// ❌ ERRADO (Screen orquestrando serviços e montando DTOs)
const HomeScreen = () => {
  const { propertyService, itemService } = useServices();
  const [stats, setStats] = useState();
  
  useEffect(() => {
    const count = await propertyService.count();
    const items = await itemService.getItemsForMaintenance();
    setStats({ total: count, urgent: items.filter(i => i.overdue).length });
  }, []);
}

// ✅ CORRETO (Use Case encapsula a lógica de apresentação)
class GetHomeScreenDataUseCase {
  async execute(): Promise<StatDisplay[]> {
    const count = await this.propertyRepo.count();
    const items = await this.itemRepo.getOverdue();
    return [{ label: 'Total', value: count }, { label: 'Urgent', value: items.length }];
  }
}

const HomeScreen = () => {
  const stats = useHomeScreenData(); // Hook encapsula loading, error e use case
  return <Dashboard stats={stats} />;
}
```

### 4.4. Strategy Pattern (Substituindo `switch` gigante)
```typescript
// ❌ ERRADO (OCP Violation)
function resolveConflict(type: string, duplicate: any, original: any) {
  switch(type) {
    case 'skip': return original;
    case 'rename': return { ...duplicate, name: generateName() };
    case 'timestamp': return { ...duplicate, name: `${original.name} ${Date.now()}` };
  }
}

// ✅ CORRETO (Open/Closed Principle)
const conflictResolvers: Record<ConflictResolution, ConflictHandler> = {
  skip: (dup, orig) => orig,
  rename: (dup, orig) => ({ ...dup, name: generateUniqueName(orig.name) }),
  timestamp: (dup, orig) => ({ ...dup, name: `${orig.name}_${Date.now()}` }),
};

function resolveConflict(type: ConflictResolution, duplicate: any, original: any) {
  return conflictResolvers[type](duplicate, original);
}
```

---

## 🚦 5. Fitness Functions (Automação no CI/CD e Pre-commit)
Para garantir que estas regras não sejam violadas no futuro, o pipeline deve executar:

1. **Dependency Cruiser (`npm run arch:check`):**
   - `no-database-in-ui`: UI não pode importar `database`, `repositories` ou `sqlite`.
   - `no-ui-in-services`: Services não podem importar `screens`, `components` ou `navigation`.
   - `sql-only-in-repositories`: Strings SQL (`INSERT`, `SELECT`, `UPDATE`) só podem existir na pasta `repositories/`.
   - `use-cases-no-react-native`: Use Cases não podem importar frameworks de UI.
2. **ESLint Custom Rules:**
   - Bloquear `return null` em métodos de serviço (via regex ou regra customizada).
   - Bloquear `console.log` / `console.error` (exigir `logger.info` / `logger.error`).
3. **Complexidade Ciclomática:**
   - Configurar ESLint (`complexity: ["error", { max: 10 }]`) para forçar a decomposição de métodos.
4. **Tamanho de Arquivo:**
   - Alerta se telas (`.tsx` em `screens/`) passarem de 200 linhas.

---

### 💡 Como usar este arquivo no seu Harness:
1. **No `AGENTS.md` ou `CLAUDE.md`:** Adicione a instrução: *"Antes de escrever ou refatorar código, consulte e obedeça estritamente as regras em `docs/ARCHITECTURE_BOUNDARIES.md`. Aplique o checklist de Camadas e Clean Code."*
2. **Como System Prompt / Rule:** Em ferramentas como Cursor, Copilot ou Aider, adicione este arquivo como uma `@Rule` global.
3. **Code Review por IA:** Peça para o LLM: *"Revise este diff usando o checklist do ARCHITECTURE_BOUNDARIES.md. Aponte violações de Dependency Rule, CQS, tamanho de métodos ou duplicação."*
4. **Refatoração Guiada:** Ao pedir para o LLM criar uma tela nova, use o prompt: *"Crie a tela X seguindo o padrão Use Case + Hook + Sub-componentes definido em ARCHITECTURE_BOUNDARIES.md. A tela não pode ter mais de 100 linhas."*

*******************************************


Com base na análise profunda do relatório de UX (que identificou ausência de personas, violações das 10 Heurísticas de Nielsen com score 47/100, anti-padrões como *confirmshaming* e *roach motel*, e falta de pesquisa com usuários), criei o arquivo **`UX_PERSONAS_AND_HEURISTICS.md`**.

Este documento atua como uma **Skill de Contexto** e **Barreira Intransponível** para impedir que o LLM (ou desenvolvedores) reintroduzam decisões de design auto-referenciais, anti-padrões de UX e violações de heurísticas.

---

# 🎯 UX_PERSONAS_AND_HEURISTICS.md - Regras Intransponíveis de UX e Design Centrado no Usuário

**Propósito:** Este documento define os padrões de UX, personas e heurísticas obrigatórios para o projeto. Qualquer código gerado, refatorado ou revisado que viole estas regras deve ser **imediatamente rejeitado**.
**Metodologia:** Nielsen's 10 Heuristics · Schmidt's 5 Anti-Patterns · MacDonald's Pattern/Component Distinction · Macfadyen's AI Output Principles · Lang & Howell's Research Objectives.

---

## 🛑 1. Hard Gates (Regras Intransponíveis)
*O LLM/Desenvolvedor NUNCA deve:*

1. **NUNCA** criar telas, formulários ou fluxos sem validar contra as **3 Personas** definidas (Maria, Carlos, Ana).
2. **NUNCA** implementar `Alert.alert` de erro sem oferecer **ação de recuperação** (Retry, Support, ou Contextual Help).
3. **NUNCA** criar formulários sem usar o hook `useForm()` ou o componente `FormField`.
4. **NUNCA** implementar paywalls ou limites freemium como *Roach Motel* (fácil de entrar, difícil de sair com valor).
5. **NUNCA** criar onboarding com *confirmshaming* (culpar o usuário por pular/sair).
6. **NUNCA** implementar sistemas autônomos (notificações, agendamentos) sem **controle do usuário** (snooze, desativar por item, preferências).
7. **NUNCA** criar interfaces de IA (voz) sem **progress disclosure** (mostrar estados: listening → processing → finalizing).
8. **NUNCA** implementar listas de entidades sem **busca** (a partir de 20+ itens) ou **paginação** (a partir de 100+ registros).
9. **NUNCA** criar telas com mais de **15 campos visíveis simultaneamente** sem usar abas (Essentials/Details) ou modo *Quick Add*.
10. **NUNCA** usar strings hardcoded em português fora dos arquivos de `locales/`. Toda UI deve usar `t('key')`.

---

## 👥 2. Personas Definidas (Validação Obrigatória)

### 2.1. Persona 1: Homeowner Maria
- **Perfil:** Dona de 1 propriedade, 5-10 cômodos, ~30 itens.
- **Motivação:** "Esqueço quando troquei o filtro de água pela última vez."
- **Dores:** Formulários complexos intimidam; não tem tempo para preencher 15 campos por item.
- **Necessidades:** Adição rápida, notificações simples, lembretes visuais com fotos.
- **Voz:** Usuária provável (mãos ocupadas fazendo manutenção).
- **Validação:** *"Maria precisa de gamificação? Não. Ela precisa de 'Quick Add' e notificações que funcionem sem configuração."*

### 2.2. Persona 2: Property Manager Carlos
- **Perfil:** Gerencia 5-50 propriedades, cada uma com 10+ cômodos.
- **Motivação:** "Preciso provar que a manutenção foi feita para compliance."
- **Dores:** Muitas propriedades para rastrear individualmente; relatórios manuais.
- **Necessidades:** Relatórios PDF, analytics, bulk operations, sharing com proprietários.
- **Validação:** *"Carlos precisa de exportação CSV, filtros avançados e multi-property dashboard."*

### 2.3. Persona 3: Technician Ana
- **Perfil:** Presta serviço para propriedades de terceiros.
- **Motivação:** "Preciso do histórico de manutenção para diagnosticar problemas recorrentes."
- **Dores:** Não consegue encontrar registros passados de equipamentos específicos.
- **Necessidades:** Documentação com fotos, busca em histórico de manutenção, exportação PDF.
- **Validação:** *"Ana precisa de timeline de manutenção por item, busca por técnico/equipamento e exportação de laudos."*

---

## 📋 3. Checklist de Heurísticas de Nielsen (Obrigatório por Tela)

Antes de implementar qualquer tela, valide contra as 10 Heurísticas:

### 3.1. Visibilidade do Status do Sistema (Nielsen #1)
- [ ] **Loading States:** Usar skeleton screens ou `ActivityIndicator` com texto contextual ("Carregando propriedades...").
- [ ] **Progress Indicators:** Para operações > 3s (backup, exportação), mostrar barra de progresso.
- [ ] **Sync Status:** Se offline, mostrar banner amarelo "Modo offline - alterações salvas localmente".
- [ ] **Voice States:** Mostrar estados: `idle` → `listening` (pulse) → `processing` (progress bar) → `finalizing` (check) → `done/error`.

### 3.2. Correspondência entre Sistema e Mundo Real (Nielsen #2)
- [ ] **Terminologia:** Usar "Cômodo" não "RoomEntity", "Manutenção" não "MaintenanceRecord".
- [ ] **Ícones:** Lixeira para deletar, lápis para editar, engrenagem para configurações.
- [ ] **Formatos:** Datas em `dd/mm/yyyy`, telefones em `(XX) XXXXX-XXXX`, moedas em `R$ X.XXX,XX`.
- [ ] **Metáforas:** "Filtro de Água" não "Item_001", "Cozinha" não "Room_Template_5".

### 3.3. Controle e Liberdade do Usuário (Nielsen #3)
- [ ] **Undo/Redo:** Para ações destrutivas (deletar), oferecer "Desfazer" por 5s (snackbar).
- [ ] **Saída de Emergência:** Todo modal/paywall deve ter botão "Cancelar" ou "Voltar" visível.
- [ ] **Draft Saving:** Formulários longos devem salvar rascunho automaticamente (a cada 30s ou ao mudar de aba).
- [ ] **Paywall Exit:** "Continue Free" deve retornar à tela anterior funcional (modo read-only), não travar o app.

### 3.4. Consistência e Padrões (Nielsen #4)
- [ ] **Header Actions:** Lado esquerdo = navegação (voltar), lado direito = ação primária (salvar/config).
- [ ] **Cores:** Primária `#2196F3` (azul), Erro `#F44336` (vermelho), Sucesso `#4CAF50` (verde).
- [ ] **Botões:** Primário (azul preenchido), Secundário (azul outline), Destrutivo (vermelho).
- [ ] **Formulários:** Todos devem usar `useForm()` hook e `FormField` component.

### 3.5. Prevenção de Erros (Nielsen #5)
- [ ] **Validação em Tempo Real:** Campos obrigatórios mostram asterisco vermelho ao perder foco.
- [ ] **Confirmação Destrutiva:** "Tem certeza que deseja deletar? Esta ação não pode ser desfeita."
- [ ] **Smart Defaults:** Data de compra = hoje, intervalo de manutenção = 7 dias, notificações = ativadas.
- [ ] **Duplicate Detection:** Ao criar propriedade com nome idêntico, sugerir "Casa (2)" automaticamente.

### 3.6. Reconhecimento em vez de Memorização (Nielsen #6)
- [ ] **Breadcrumbs:** Navegação profunda (Propriedade → Cômodo → Item) mostra caminho no header.
- [ ] **Recent Items:** Tela inicial mostra "Últimos 5 itens acessados".
- [ ] **Filter Chips:** Filtros ativos aparecem como chips removíveis ("Cômodo: Cozinha ✕").
- [ ] **Tooltips:** Ícones obscuros (ex: ícone de "template") mostram tooltip ao segurar.

### 3.7. Flexibilidade e Eficiência de Uso (Nielsen #7)
- [ ] **Quick Add:** Formulário de item tem aba "Essentials" (4 campos) e aba "Details" (opcional).
- [ ] **Duplicate Action:** Botão "Duplicar Item" em cards de item (copia template, intervalo, cômodo).
- [ ] **Keyboard Types:** Campo de telefone usa `keyboardType="phone-pad"`, email usa `email-address`.
- [ ] **Voice Input:** Campos de texto longo (descrição, notas) mostram ícone de microfone.

### 3.8. Estética e Design Minimalista (Nielsen #8)
- [ ] **Informação Relevante:** Não mostrar campos opcionais vazios (ex: "Garantia: Não informada").
- [ ] **Whitespace:** Espaçamento mínimo de 16px entre elementos, 24px entre seções.
- [ ] **Hierarquia Visual:** Título (18px, bold), Subtítulo (14px, regular), Corpo (12px, light).
- [ ] **Dark Mode:** Respeitar `Appearance.getColorScheme()` do sistema.

### 3.9. Ajudar Usuários a Reconhecer, Diagnosticar e Recuperar de Erros (Nielsen #9)
- [ ] **Mensagens Claras:** "Falha ao salvar" não "Error 500: Database timeout".
- [ ] **Retry Button:** Todo erro de rede mostra botão "Tentar Novamente".
- [ ] **Contextual Help:** Botão "?" no header abre painel com explicação da tela.
- [ ] **Support Contact:** Erros críticos mostram "Contatar Suporte: support@smartfix.app".

### 3.10. Ajuda e Documentação (Nielsen #10)
- [ ] **Onboarding:** 6 passos (não 5) - último passo é "Demo Workflow" mostrando app em ação.
- [ ] **FAQ:** Tela "Sobre" tem seção de perguntas frequentes (i18n).
- [ ] **Empty States:** Telas vazias mostram ilustração + "Comece adicionando sua primeira propriedade".
- [ ] **Tooltips:** Campos complexos (ex: "Intervalo de Manutenção") mostram ícone de informação.

---

## 🚫 4. Anti-Padrões a Evitar (Com Exemplos do Código)

### 4.1. Confirmshaming (Culpar o Usuário)
❌ **ERRADO:**
```typescript
// Onboarding skip alert com tom de culpa
Alert.alert(
  'Pular Tutorial?',
  'Tem certeza? Você vai perder pontos!', // Shame
  [
    { text: 'Cancelar', style: 'cancel' }, // Esconde a opção de sair
    { text: 'Pular', onPress: skipOnboarding } // Culpa o usuário
  ]
);
```

✅ **CORRETO:**
```typescript
// Bottom sheet com opções neutras e de igual prioridade
<SkipOnboardingSheet
  options={[
    { label: 'Continuar Depois', icon: 'clock', action: saveProgress },
    { label: 'Começar a Usar', icon: 'home', action: skipOnboarding },
    { label: 'Continuar Tutorial', icon: 'play', action: dismissSheet }
  ]}
/>
```

### 4.2. Roach Motel (Fácil de Entrar, Difícil de Sair)
❌ **ERRADO:**
```typescript
// Paywall bloqueia o usuário sem saída útil
Alert.alert(
  'Limite Atingido',
  'Plano gratuito permite apenas 1 propriedade',
  [
    { text: 'Cancelar', style: 'cancel' }, // Fica travado
    { text: 'Upgrade', onPress: openPaywall } // Única saída
  ]
);
```

✅ **CORRETO:**
```typescript
// Banner inline com opção de continuar em modo read-only
<LimitationBanner
  message="Plano gratuito: 1 propriedade. Você tem 1/1."
  actions={[
    { label: 'Upgrade', type: 'primary', onPress: openPaywall },
    { label: 'Dispensar', type: 'text', onPress: dismissBanner } // Volta à tela funcional
  ]}
/>
```

### 4.3. Mystery Meat Navigation (Navegação Misteriosa)
❌ **ERRADO:**
```typescript
// Header com ícone inconsistente
<Header
  title="Propriedades"
  rightComponent={<Icon name="more-vertical" />} // O que faz?
/>
```

✅ **CORRETO:**
```typescript
// Header com ação clara e acessível
<Header
  title="Propriedades"
  rightComponent={
    <IconButton
      icon="settings"
      accessibilityLabel="Configurações"
      onPress={openSettings}
    />
  }
/>
```

### 4.4. Lack of Error Recovery (Sem Recuperação de Erros)
❌ **ERRADO:**
```typescript
// Erro genérico sem ação
try {
  await propertyService.create(data);
} catch (error) {
  Alert.alert('Erro', 'Falha ao salvar propriedade'); // Sem retry, sem suporte
}
```

✅ **CORRETO:**
```typescript
// Erro com ações de recuperação
try {
  await propertyService.create(data);
} catch (error) {
  showErrorAlert({
    title: 'Falha ao Salvar',
    message: error.userMessage,
    retry: () => propertyService.create(data),
    supportContact: 'support@smartfix.app',
    contextualHelp: t('errors.network_help')
  });
}
```

### 4.5. Autonomous Systems Without User Control (Sistemas Autônomos Sem Controle)
❌ **ERRADO:**
```typescript
// Notificações automáticas sem opção de desativar por item
useEffect(() => {
  notificationService.scheduleAllMaintenanceNotifications(); // Forçado
}, [items]);
```

✅ **CORRETO:**
```typescript
// Notificações com controle por item
<ItemFormScreen>
  <NotificationSettingsSection
    enabled={item.notificationsEnabled}
    daysAdvance={item.notificationDaysAdvance}
    onToggle={(enabled) => updateItem({ notificationsEnabled: enabled })}
    onDaysChange={(days) => updateItem({ notificationDaysAdvance: days })}
  />
</ItemFormScreen>
```

---

## 🧠 5. Prompt Patterns para o LLM (UX Validation)

Antes de implementar qualquer tela ou feature, o LLM deve executar o seguinte raciocínio (Chain of Thought):

```markdown
### 🎯 UX Validation Check (Obrigatório antes de codar)
1. **Qual persona está usando esta feature?** (Maria, Carlos ou Ana?)
2. **Qual heurística de Nielsen esta tela viola?** (Validar todas as 10)
3. **Existe anti-padrão?** (Confirmshaming, Roach Motel, Mystery Meat, etc.)
4. **O usuário tem controle?** (Undo, saída de emergência, preferências)
5. **O erro é recuperável?** (Retry, suporte, ajuda contextual)
6. **A interface é consistente?** (Cores, ícones, terminologia, padrões)
7. **Há informação desnecessária?** (Campos vazios, opções obscuras)
8. **O sistema comunica status?** (Loading, progresso, sync, offline)
```

---

## 🏗️ 6. Padrões de Implementação (Snippets de Referência)

### 6.1. Hook useForm() (Abstração de Formulários)
```typescript
// src/hooks/useForm.ts
interface UseFormConfig<T> {
  initialValues: T;
  validate: (values: T) => FormErrors<T>;
  onSubmit: (values: T) => Promise<void>;
  onSuccess?: () => void;
}

export function useForm<T>({ initialValues, validate, onSubmit, onSuccess }: UseFormConfig<T>) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<FormErrors<T>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  const setField = <K extends keyof T>(field: K, value: T[K]) => {
    setValues(prev => ({ ...prev, [field]: value }));
    setErrors(prev => ({ ...prev, [field]: undefined }));
    setIsDirty(true);
  };

  const submit = async () => {
    const validationErrors = validate(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setIsSubmitting(true);
    try {
      await onSubmit(values);
      onSuccess?.();
    } catch (error) {
      showErrorAlert({ message: error.userMessage, retry: submit });
    } finally {
      setIsSubmitting(false);
    }
  };

  return { values, errors, isSubmitting, isDirty, setField, submit };
}
```

### 6.2. Componente FormField (Campo de Formulário Consistente)
```typescript
// src/components/FormField.tsx
interface FormFieldProps {
  label: string;
  error?: string;
  required?: boolean;
  voiceEnabled?: boolean;
  children: React.ReactNode;
}

export function FormField({ label, error, required, voiceEnabled, children }: FormFieldProps) {
  return (
    <View style={styles.container}>
      <View style={styles.labelContainer}>
        <Text style={styles.label}>
          {label}
          {required && <Text style={styles.required}> *</Text>}
        </Text>
        {voiceEnabled && <VoiceIcon />}
      </View>
      {children}
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}
```

### 6.3. Função showErrorAlert() (Recuperação de Erros)
```typescript
// src/utils/errorAlert.ts
interface ErrorAlertConfig {
  title?: string;
  message: string;
  retry?: () => void | Promise<void>;
  supportContact?: string;
  contextualHelp?: string;
}

export function showErrorAlert(config: ErrorAlertConfig) {
  const buttons: AlertButton[] = [
    { text: 'Dispensar', style: 'cancel' }
  ];

  if (config.retry) {
    buttons.unshift({
      text: 'Tentar Novamente',
      onPress: config.retry,
      style: 'default'
    });
  }

  if (config.supportContact) {
    buttons.push({
      text: 'Contatar Suporte',
      onPress: () => Linking.openURL(`mailto:${config.supportContact}`)
    });
  }

  Alert.alert(
    config.title || 'Erro',
    config.message + (config.contextualHelp ? `\n\n${config.contextualHelp}` : ''),
    buttons
  );
}
```

### 6.4. Hook useVoiceStateMachine() (Progress Disclosure para IA)
```typescript
// src/hooks/useVoiceStateMachine.ts
type VoiceState = 'idle' | 'listening' | 'processing' | 'finalizing' | 'done' | 'error' | 'timeout';

export function useVoiceStateMachine() {
  const [state, setState] = useState<VoiceState>('idle');
  const [progress, setProgress] = useState(0);

  const startListening = async () => {
    setState('listening');
    // Iniciar gravação
    setTimeout(() => setState('processing'), 1000);
    setTimeout(() => setState('finalizing'), 5000);
    // ... lógica de voz
  };

  return {
    state,
    progress,
    startListening,
    isListening: state === 'listening',
    isProcessing: state === 'processing' || state === 'finalizing'
  };
}
```

---

## 🚦 7. Fitness Functions (Automação no CI/CD)
Para garantir que estas regras não sejam violadas no futuro, o pipeline deve executar:

1. **UX Linter (Custom ESLint Rules):**
   - Bloquear `Alert.alert` sem botão de retry ou suporte (via regex).
   - Bloquear strings hardcoded em português fora de `locales/` (via regex).
   - Bloquear formulários sem `useForm()` hook (via análise de AST).
2. **Accessibility Tests:**
   - `npm test -- --testPathPattern=accessibility` deve passar com 0 skipped.
   - Testes de contraste de cor (WCAG AA) para 10+ pares de cores.
3. **Persona Validation:**
   - Script que valida se novas features mencionam personas no commit message ou PR description.
4. **Anti-Pattern Detection:**
   - Script que busca por palavras-chave de anti-padrões: "Tem certeza?", "Você vai perder", "Irreversível" (sem botão de undo).

---

### 💡 Como usar este arquivo no seu Harness:
1. **No `AGENTS.md` ou `CLAUDE.md`:** Adicione a instrução: *"Antes de escrever código de UI, consulte e obedeça estritamente as regras em `docs/UX_PERSONAS_AND_HEURISTICS.md`. Valide contra as 3 Personas e as 10 Heurísticas de Nielsen."*
2. **Como System Prompt / Rule:** Em ferramentas como Cursor, Copilot ou Aider, adicione este arquivo como uma `@Rule` global.
3. **Code Review por IA:** Peça para o LLM: *"Revise este diff usando o checklist do UX_PERSONAS_AND_HEURISTICS.md. Aponte violações de heurísticas, anti-padrões ou falta de validação contra personas."*
4. **Design de Novas Features:** Ao pedir para o LLM criar uma tela nova, use o prompt: *"Crie a tela X validando contra as personas Maria, Carlos e Ana. Aplique as heurísticas de Nielsen #1, #3, #9. Evite anti-padrões confirmshaming e roach motel."*


**********************************

# 🔄 TDD_RED_GREEN_REFACTOR.md - Regras Intransponíveis de Test-Driven Development

**Propósito:** Este documento define os padrões de TDD, qualidade de testes e práticas de desenvolvimento orientado a testes obrigatórios para o projeto. Qualquer código gerado, refatorado ou revisado que viole estas regras deve ser **imediatamente rejeitado**.
**Metodologia:** Beck (TDD by Example) · Johnson (Mastering TDD) · Seemann (Code That Fits in Your Head) · Hock (Clean Code Fundamentals) · Martin (Clean Code)

---

## 🛑 1. Hard Gates (Regras Intransponíveis)

*O LLM/Desenvolvedor NUNCA deve:*

1. **NUNCA** escrever código de produção sem antes escrever um teste falhando (Red-Green-Refactor).
2. **NUNCA** criar testes com `expect(true).toBe(true)` ou blocos `it()` vazios.
3. **NUNCA** usar `setTimeout` ou delays hard-coded em testes. Usar `waitFor()`, `findBy*` ou event-driven approaches.
4. **NUNCA** criar mocks que roteiam comportamento baseado em SQL strings (ex: `if (sql.includes('maintenance_history'))`).
5. **NUNCA** escrever testes que dependem de ordem de execução ou estado compartilhado.
6. **NUNCA** criar testes com `testTimeout` maior que 5000ms sem justificativa documentada.
7. **NUNCA** pular testes (`it.skip`, `xit`, `xdescribe`) sem um comentário `TODO(#issue)` explicando o motivo.
8. **NUNCA** escrever testes que testam implementação ao invés de comportamento.
9. **NUNCA** criar testes sem estrutura AAA (Arrange-Act-Assert) ou GIVEN-WHEN-THEN.
10. **NUNCA** commitar código sem rodar `npm test` localmente (pre-commit hook obrigatório).

---

## 🔄 2. O Ciclo TDD Obrigatório (Red-Green-Refactor)

### 2.1 As Duas Regras de Beck
```markdown
Regra 1: Você NUNCA escreverá código de produção até ter um teste falhando.
Regra 2: Você NUNCA duplicará lógica sem antes extrair para um padrão compartilhado.
```

### 2.2 O Ciclo Obrigatório
Toda nova feature ou bug fix deve seguir esta ordem:

1. **RED (Teste Falhando):**
   - Escreva o teste mais simples possível que descreva o comportamento desejado
   - Execute o teste e veja-o falhar (mensagem de erro clara)
   - Commit: `test: add failing test for [feature]`

2. **GREEN (Implementação Mínima):**
   - Escreva APENAS o código necessário para fazer o teste passar
   - Não otimize, não generalize, não adicione features extras
   - Execute o teste e veja-o passar
   - Commit: `feat: implement [feature] to pass test`

3. **REFACTOR (Melhorar sem Mudar Comportamento):**
   - Remova duplicações (DRY)
   - Melhore nomes (Intention-Revealing Names)
   - Extraia métodos (Composed Method Pattern)
   - Execute TODOS os testes após cada mudança
   - Commit: `refactor: improve [feature] structure`

### 2.3 Estratégias para Chegar ao GREEN (Beck)

| Estratégia | Quando Usar | Exemplo |
|------------|-------------|---------|
| **Fake It** | Primeiro teste, retorno fixo | `return { id: 1, name: 'Test' }` |
| **Obvious Implementation** | Padrão claro e simples | Implementar lógica direta |
| **Triangulação** | Múltiplos casos de borda | 3+ exemplos com valores diferentes |

---

## 📋 3. Checklist de Implementação por Tipo de Teste

### 3.1 Testes Unitários (70% da Pirâmide)
- [ ] **Isolamento:** Mockar TODAS as dependências externas (DB, rede, filesystem)
- [ ] **Velocidade:** Cada teste deve executar em < 100ms
- [ ] **Nomenclatura:** `should [expected behavior] when [condition]`
- [ ] **Cobertura:** Focar em regras de negócio, não em getters/setters
- [ ] **Independência:** Cada teste deve ser executável isoladamente
- [ ] **AAA Pattern:**
  ```typescript
  it('should calculate overdue items', () => {
    // ARRANGE
    const items = [{ dueDate: '2024-01-01' }, { dueDate: '2025-12-31' }];
    
    // ACT
    const result = calculateOverdue(items);
    
    // ASSERT
    expect(result).toHaveLength(1);
  });
  ```

### 3.2 Testes de Integração (20% da Pirâmide)
- [ ] **Real DB Mock:** Usar `createValidatingMockDb()` ao invés de `jest.fn()`
- [ ] **Constraints:** Testar FK, UNIQUE, NOT NULL constraints
- [ ] **Cascata:** Testar deletes em cascata (Property → Room → Item)
- [ ] **Migrations:** Testar vN → vN+1 sem perda de dados
- [ ] **Cross-Service:** Testar fluxos que envolvem múltiplos serviços
- [ ] **Cleanup:** Limpar tabelas em ordem FK-safe no `beforeEach`

### 3.3 Testes E2E (10% da Pirâmide)
- [ ] **Happy Path:** Cobrir fluxo principal (Property → Room → Item → Maintenance)
- [ ] **testID Estável:** Usar `testID` ao invés de texto (i18n-safe)
- [ ] **Sem Sleep:** Usar `waitForElement()` ao invés de `setTimeout`
- [ ] **Poucos Cenários:** 5-10 testes E2E bem escolhidos > 50 testes frágeis
- [ ] **Flaky-Free:** Se um teste E2E falha 2x seguidas, investigar root cause

### 3.4 Testes de Acessibilidade
- [ ] **Roles:** Verificar `accessibilityRole` em todos elementos interativos
- [ ] **Labels:** Verificar `accessibilityLabel` em ícones e botões
- [ ] **Contraste:** Testar 10+ pares de cores para WCAG AA (4.5:1)
- [ ] **Touch Target:** Verificar tamanho mínimo de 44x44 pontos
- [ ] **Screen Reader:** Testar fluxo completo com VoiceOver/TalkBack

---

## 🚫 4. Anti-Padrões a Evitar (Com Exemplos)

### 4.1 Test-After Development (TAD)
❌ **ERRADO:**
```typescript
// Escrever toda a feature primeiro
class PropertyService {
  async create(data: PropertyData): Promise<Property> {
    // 100 linhas de implementação
  }
}

// Depois escrever teste para "cobrir"
it('should create property', async () => {
  const result = await propertyService.create({ name: 'Test' });
  expect(result).toBeDefined(); // Teste fraco, não dirige design
});
```

✅ **CORRETO:**
```typescript
// 1. RED: Escrever teste falhando primeiro
it('should create property with name', async () => {
  const result = await propertyService.create({ name: 'My Home' });
  expect(result.name).toBe('My Home');
});

// 2. GREEN: Implementar mínimo para passar
class PropertyService {
  async create(data: PropertyData): Promise<Property> {
    return { id: 1, name: data.name };
  }
}

// 3. REFACTOR: Melhorar estrutura
class PropertyService {
  async create(data: PropertyData): Promise<Property> {
    const validatedData = this.validatePropertyData(data);
    const property = await this.repository.insert(validatedData);
    return this.mapToDomain(property);
  }
}
```

### 4.2 Mocks Frágeis com SQL Routing
❌ **ERRADO:**
```typescript
mockDb.getAllAsync.mockImplementation((sql: string) => {
  if (sql.includes('maintenance_history')) {
    return [{ id: 1, item_id: 1, date: '2024-01-01' }];
  }
  if (sql.includes('room_items')) {
    return [{ id: 1, name: 'Water Filter' }];
  }
  return [];
});
```

✅ **CORRETO:**
```typescript
import { createValidatingMockDb } from '../mockSqlite';

const mockDb = createValidatingMockDb(['maintenance_history', 'room_items']);

// Mock valida SQL, constraints, e retorna dados realistas
mockDb.insert('room_items', { id: 1, name: 'Water Filter' });
mockDb.insert('maintenance_history', { id: 1, item_id: 1, date: '2024-01-01' });
```

### 4.3 Delays Hard-Coded (Flaky Tests)
❌ **ERRADO:**
```typescript
it('should load data after delay', async () => {
  const component = render(<DataLoader />);
  
  setTimeout(() => {
    expect(component.getByText('Loaded')).toBeTruthy();
  }, 100); // Delay mágico, teste frágil
});
```

✅ **CORRETO:**
```typescript
it('should load data', async () => {
  const component = render(<DataLoader />);
  
  // Aguardar elemento aparecer (event-driven)
  const loadedText = await component.findByText('Loaded');
  expect(loadedText).toBeTruthy();
  
  // Ou usar waitFor
  await waitFor(() => {
    expect(component.getByText('Loaded')).toBeTruthy();
  });
});
```

### 4.4 Placeholders e Testes Vazios
❌ **ERRADO:**
```typescript
it('should validate email', () => {
  expect(true).toBe(true); // Não testa nada
});

it('should handle integration', async () => {
  // TODO: implementar
});
```

✅ **CORRETO:**
```typescript
it('should validate email format', () => {
  expect(isValidEmail('test@example.com')).toBe(true);
  expect(isValidEmail('invalid')).toBe(false);
  expect(isValidEmail('')).toBe(false);
});

// Se não pode implementar agora, pular com justificativa
it.skip('should handle complex integration', async () => {
  // TODO(#123): Depends on backend API v2
});
```

### 4.5 Testes que Dependem de Ordem
❌ **ERRADO:**
```typescript
describe('PropertyService', () => {
  let createdId: number;
  
  it('should create property', async () => {
    const result = await propertyService.create({ name: 'Test' });
    createdId = result.id; // Estado compartilhado
  });
  
  it('should update property', async () => {
    await propertyService.update(createdId, { name: 'Updated' }); // Depende do teste anterior
  });
});
```

✅ **CORRETO:**
```typescript
describe('PropertyService', () => {
  beforeEach(async () => {
    await clearAllTables(); // Isolamento
  });
  
  it('should create property', async () => {
    const result = await propertyService.create({ name: 'Test' });
    expect(result.id).toBeGreaterThan(0);
  });
  
  it('should update property', async () => {
    const created = await propertyService.create({ name: 'Test' });
    await propertyService.update(created.id, { name: 'Updated' });
    
    const updated = await propertyService.getById(created.id);
    expect(updated.name).toBe('Updated');
  });
});
```

### 4.6 Falta de Triangulação
❌ **ERRADO:**
```typescript
it('should calculate next maintenance date', () => {
  const result = calculateNextMaintenanceDate(30, new Date('2024-03-15'));
  expect(result.toISOString()).toContain('2024-04-14');
});
```

✅ **CORRETO:**
```typescript
it.each([
  [30, '2024-03-15', '2024-04-14'],
  [7, '2024-03-15', '2024-03-22'],
  [90, '2024-03-15', '2024-06-13'],
  [1, '2024-03-15', '2024-03-16'],
  [365, '2024-03-15', '2025-03-15'],
])('calculateNextMaintenanceDate(%i, %s) should return %s',
  (interval, base, expected) => {
    const result = calculateNextMaintenanceDate(interval, new Date(base));
    expect(result.toISOString().split('T')[0]).toBe(expected);
  }
);
```

---

## 🧠 5. Prompt Patterns para o LLM (TDD Validation)

Antes de implementar qualquer feature ou fix, o LLM deve executar o seguinte raciocínio (Chain of Thought):

```markdown
### 🔄 TDD Validation Check (Obrigatório antes de codar)
1. **Qual comportamento estou testando?** (Descrever em uma frase)
2. **Qual o teste mais simples que falha?** (RED)
3. **Qual a implementação mínima para passar?** (GREEN)
4. **Há duplicação ou código feio?** (REFACTOR)
5. **Qual heurística F.I.R.S.T. este teste viola?**
   - Fast (< 100ms?)
   - Independent (sem estado compartilhado?)
   - Repeatable (determinístico?)
   - Self-Validating (sem `expect(true).toBe(true)`?)
   - Timely (escrito ANTES do código?)
6. **Há edge cases não cobertos?** (null, vazio, borda, erro)
7. **O teste é legível como documentação?** (GIVEN-WHEN-THEN claro?)
```

---

## 🏗️ 6. Padrões de Implementação (Snippets de Referência)

### 6.1 Hook useForm() com TDD
```typescript
// src/hooks/useForm.ts
interface UseFormConfig<T> {
  initialValues: T;
  validate: (values: T) => FormErrors<T>;
  onSubmit: (values: T) => Promise<void>;
  onSuccess?: () => void;
}

export function useForm<T>({ initialValues, validate, onSubmit, onSuccess }: UseFormConfig<T>) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<FormErrors<T>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  const setField = <K extends keyof T>(field: K, value: T[K]) => {
    setValues(prev => ({ ...prev, [field]: value }));
    setErrors(prev => ({ ...prev, [field]: undefined }));
    setIsDirty(true);
  };

  const submit = async () => {
    const validationErrors = validate(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    setIsSubmitting(true);
    try {
      await onSubmit(values);
      onSuccess?.();
    } catch (error) {
      showErrorAlert({ message: error.userMessage, retry: submit });
    } finally {
      setIsSubmitting(false);
    }
  };

  return { values, errors, isSubmitting, isDirty, setField, submit };
}

// Teste TDD
describe('useForm', () => {
  it('should validate and prevent submit when invalid', async () => {
    const validate = jest.fn().mockReturnValue({ name: 'Required' });
    const onSubmit = jest.fn();
    
    const { result } = renderHook(() => 
      useForm({ initialValues: { name: '' }, validate, onSubmit })
    );
    
    await act(async () => {
      await result.current.submit();
    });
    
    expect(validate).toHaveBeenCalled();
    expect(onSubmit).not.toHaveBeenCalled();
    expect(result.current.errors.name).toBe('Required');
  });
});
```

### 6.2 Test Data Builder (Object Mother)
```typescript
// src/__tests__/builders/propertyBuilder.ts
export function aProperty(overrides?: Partial<Property>): Property {
  return {
    id: 1,
    name: 'Default Property',
    address: '123 Test St',
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01'),
    ...overrides,
  };
}

// Uso em testes
it('should update property name', async () => {
  const property = aProperty({ id: 1, name: 'Original' });
  await propertyService.update(1, { name: 'Updated' });
  
  const result = await propertyService.getById(1);
  expect(result.name).toBe('Updated');
});
```

### 6.3 Property-Based Testing (fast-check)
```typescript
// src/__tests__/utils/validationUtils.property.test.ts
import fc from 'fast-check';

describe('assertValidTextInput (property-based)', () => {
  it('should accept any string under maxLength', () => {
    fc.assert(
      fc.property(fc.string({ maxLength: 100 }), (input) => {
        expect(() => 
          assertValidTextInput(input, { fieldName: 'test', maxLength: 100 })
        ).not.toThrow();
      })
    );
  });
  
  it('should reject strings over maxLength', () => {
    fc.assert(
      fc.property(fc.string({ minLength: 101, maxLength: 200 }), (input) => {
        expect(() => 
          assertValidTextInput(input, { fieldName: 'test', maxLength: 100 })
        ).toThrow('validation_error');
      })
    );
  });
});
```

### 6.4 Mutation Testing (Stryker)
```json
// stryker.config.json
{
  "$schema": "./node_modules/@stryker-mutator/core/schema/stryker-schema.json",
  "packageManager": "npm",
  "mutate": ["src/utils/validationUtils.ts"],
  "testRunner": "jest",
  "jest": { "project": "unit" },
  "reporters": ["progress", "html"],
  "thresholds": { "high": 80, "low": 60, "break": 50 }
}
```

---

## 🚦 7. Fitness Functions (Automação no CI/CD)

Para garantir que estas regras não sejam violadas no futuro, o pipeline deve executar:

### 7.1 Pre-commit Hooks (Husky + lint-staged)
```json
// .husky/pre-commit
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx lint-staged
npm test -- --selectProjects unit --passWithNoTests
```

```json
// lint-staged.config.js
module.exports = {
  '*.{ts,tsx}': [
    'eslint --fix',
    'prettier --write',
  ],
};
```

### 7.2 CI Pipeline Gates
```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run unit tests
        run: npm test -- --selectProjects unit --coverage
      
      - name: Check coverage thresholds
        run: |
          COVERAGE=$(npm test -- --coverage --json | jq '.total.lines.pct')
          if (( $(echo "$COVERAGE < 70" | bc -l) )); then
            echo "Coverage $COVERAGE% is below 70% threshold"
            exit 1
          fi
      
      - name: Check for placeholder tests
        run: |
          PLACEHOLDERS=$(grep -r "expect(true).toBe(true)" src/__tests__/ | wc -l)
          if [ "$PLACEHOLDERS" -gt 0 ]; then
            echo "Found $PLACEHOLDERS placeholder tests"
            exit 1
          fi
      
      - name: Check for skipped tests
        run: |
          SKIPPED=$(grep -r "it\.skip\|xit\|xdescribe" src/__tests__/ | wc -l)
          if [ "$SKIPPED" -gt 20 ]; then
            echo "Found $SKIPPED skipped tests (max 20 allowed)"
            exit 1
          fi
      
      - name: Check for hard-coded delays
        run: |
          DELAYS=$(grep -r "setTimeout" src/__tests__/ | wc -l)
          if [ "$DELAYS" -gt 0 ]; then
            echo "Found $DELAYS hard-coded delays in tests"
            exit 1
          fi
```

### 7.3 Mutation Testing no CI
```yaml
# .github/workflows/mutation.yml
jobs:
  mutation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run mutation tests
        run: npx stryker run
      
      - name: Check mutation score
        run: |
          SCORE=$(cat reports/mutation/mutation.json | jq '.metrics.mutationScore')
          if (( $(echo "$SCORE < 60" | bc -l) )); then
            echo "Mutation score $SCORE% is below 60% threshold"
            exit 1
          fi
```

### 7.4 Test Quality Dashboard
```typescript
// scripts/test-quality-report.ts
import { execSync } from 'child_process';

const report = {
  totalTests: 0,
  passedTests: 0,
  failedTests: 0,
  skippedTests: 0,
  placeholderTests: 0,
  hardcodedDelays: 0,
  coveragePercent: 0,
  mutationScore: 0,
};

// Contar placeholders
report.placeholderTests = parseInt(
  execSync('grep -r "expect(true).toBe(true)" src/__tests__/ | wc -l').toString()
);

// Contar delays
report.hardcodedDelays = parseInt(
  execSync('grep -r "setTimeout" src/__tests__/ | wc -l').toString()
);

// Gerar relatório
console.log('📊 Test Quality Report');
console.log(`Placeholders: ${report.placeholderTests}`);
console.log(`Hard-coded delays: ${report.hardcodedDelays}`);
console.log(`Coverage: ${report.coveragePercent}%`);
console.log(`Mutation Score: ${report.mutationScore}%`);
```

---

## 📊 8. Métricas de Qualidade de Testes (F.I.R.S.T.)

### 8.1 Checklist F.I.R.S.T. por Teste

| Princípio | Pergunta | Gate |
|-----------|----------|------|
| **Fast** | O teste executa em < 100ms? | ✅/❌ |
| **Independent** | O teste pode rodar isoladamente? | ✅/❌ |
| **Repeatable** | O teste é determinístico (sem flaky)? | ✅/❌ |
| **Self-Validating** | O teste tem assertions reais (não placeholders)? | ✅/❌ |
| **Timely** | O teste foi escrito ANTES do código? | ✅/❌ |

### 8.2 Thresholds de Cobertura por Camada

| Camada | Lines | Branches | Functions | Statements |
|--------|-------|----------|-----------|------------|
| **Global** | 75% | 65% | 70% | 75% |
| **Services** | 85% | 75% | 80% | 85% |
| **Utils** | 80% | 70% | 75% | 80% |
| **Repositories** | 90% | 80% | 85% | 90% |
| **Critical Paths** | 95% | 85% | 90% | 95% |

### 8.3 Pirâmide de Testes (Distribuição Ideal)

```
        /\
       /  \      E2E (10%)
      /----\     - Fluxos críticos
     /      \    - 5-10 testes bem escolhidos
    /--------\   
   /          \  Integração (20%)
  /------------\ - Cross-service flows
 /              \- Real DB mock
/----------------\
|                  | Unit (70%)
|------------------| - Regras de negócio
|                  | - Componentes isolados
--------------------
```

---

## 💡 9. Como Usar Este Arquivo no Seu Harness

### 9.1 No `AGENTS.md` ou `CLAUDE.md`
Adicione a instrução:
```markdown
## TDD & Test Quality
Antes de escrever código de produção, consulte e obedeça estritamente as regras em `docs/TDD_RED_GREEN_REFACTOR.md`.

**Obrigatório:**
1. Escrever teste falhando ANTES do código (Red-Green-Refactor)
2. Validar contra o checklist F.I.R.S.T.
3. Usar estrutura AAA ou GIVEN-WHEN-THEN
4. Evitar anti-padrões (placeholders, delays, mocks frágeis)
5. Rodar `npm test` antes de commitar
```

### 9.2 Como System Prompt / Rule
Em ferramentas como Cursor, Copilot ou Aider, adicione este arquivo como uma `@Rule` global.

### 9.3 Code Review por IA
Peça para o LLM:
```
Revise este diff usando o checklist do TDD_RED_GREEN_REFACTOR.md. Aponte:
- Violações de Red-Green-Refactor
- Anti-padrões (placeholders, delays, mocks frágeis)
- Violações de F.I.R.S.T.
- Falta de triangulação ou edge cases
- Testes que testam implementação ao invés de comportamento
```

### 9.4 Ao Pedir Novas Features
Use o prompt:
```
Implemente a feature X seguindo TDD estrito:
1. Primeiro, escreva 3 testes falhando (RED) cobrindo happy path + 2 edge cases
2. Depois, implemente o mínimo para passar (GREEN)
3. Por fim, refatore para remover duplicações (REFACTOR)
4. Valide contra o checklist F.I.R.S.T.
5. Use triangulação com 3+ exemplos
```

### 9.5 Ao Refatorar Código Existente
Use o prompt:
```
Refatore o código X seguindo TDD:
1. Primeiro, escreva testes de caracterização para o comportamento atual
2. Refatore mantendo todos os testes passando
3. Melhore a estrutura (Composed Method, DRY, nomes claros)
4. Execute mutation testing para validar qualidade dos testes
```

---

## 📈 10. Evolução da Maturidade TDD

### Nível 1: Test-After (Atual)
- Testes escritos depois do código
- Cobertura baixa (20-30%)
- Testes frágeis e lentos
- **Score: 31/50**

### Nível 2: Test-First Básico
- Testes escritos antes do código (Red-Green)
- Cobertura média (60-70%)
- Sem refatoração sistemática
- **Score: 40/50**

### Nível 3: TDD Completo
- Ciclo Red-Green-Refactor completo
- Cobertura alta (80%+)
- Triangulação e property-based testing
- Mutation testing > 60%
- **Score: 46/50**

### Nível 4: TDD Cultural
- TDD praticado por toda a equipe
- Testes como documentação viva
- Walking skeleton para novas features
- Feedback loop < 5 minutos
- **Score: 50/50**

---

## 🎯 Conclusão

Este documento estabelece as bases para uma cultura de TDD sólida no projeto SmartFix. A adoção dessas práticas não é apenas sobre escrever testes, mas sobre **pensar no design antes de implementar**, **validar comportamento ao invés de implementação**, e **manter a qualidade através de automação**.

Os anti-padrões identificados nos relatórios de auditoria (placeholders, delays, mocks frágeis, Test-After) são sintomas de uma falta de disciplina TDD. Ao seguir as regras intransponíveis e os checklists aqui definidos, o projeto evoluirá de um score de 31/50 para 50/50 em maturidade TDD.

**Lembre-se:** TDD não é sobre testes, é sobre **design**. Testes são o subproduto de um bom design dirigido por comportamento.

*******************************************************


# 🚀 DEVOPS_CHECKLIST.md - Regras Intransponíveis de DevOps e Entrega Contínua

**Propósito:** Este documento define os padrões de DevOps, CI/CD, observabilidade e deployment obrigatórios para o projeto. Qualquer código gerado, refatorado ou revisado que viole estas regras deve ser **imediatamente rejeitado**.
**Metodologia:** CALMS (Vijayakumaran) · DORA Metrics (Servile/Hattori) · Continuous Deployment (Brikman) · DevSecOps Shift-Left · Fundamentals of DevOps (Brikman)

---

## 🛑 1. Hard Gates (Regras Intransponíveis)

*O LLM/Desenvolvedor NUNCA deve:*

1. **NUNCA** commitar código sem que o pipeline de CI passe (lint, build, test, coverage, arch:check).
2. **NUNCA** fazer deploy em produção sem crash reporting configurado (Sentry/Crashlytics).
3. **NUNCA** versionar secrets no repositório. Usar exclusivamente EAS Secrets / Variáveis de Ambiente do CI.
4. **NUNCA** criar novas dependências sem verificar vulnerabilidades (`npm audit`).
5. **NUNCA** fazer deploy manual sem passar pelo pipeline automatizado (exceto emergências documentadas).
6. **NUNCA** remover testes do CI/CD para "acelerar" o pipeline.
7. **NUNCA** criar features sem feature flag ou kill-switch para produção.
8. **NUNCA** ignorar alertas de segurança (Dependabot, npm audit, SAST).
9. **NUNCA** fazer build de produção sem SBOM (Software Bill of Materials).
10. **NUNCA** deployar sem validar em staging/beta track primeiro.

---

## 📋 2. Checklist de Implementação por Domínio

### 🔁 2.1. CI/CD Pipeline (Brikman / Hattori)
- [ ] **Pipeline Automatizado:** Todo push/PR deve disparar CI no GitHub Actions.
- [ ] **Jobs Paralelos:** Lint, Build (tsc), Unit Tests, Integration Tests, Arch Check, Coverage rodando em paralelo.
- [ ] **Quality Gates:** CI deve falhar se:
  - ESLint tiver erros
  - `tsc --noEmit` falhar
  - Testes unitários/integração falharem
  - Cobertura cair abaixo dos thresholds definidos
  - `dependency-cruiser` reportar violações
  - `npm audit` encontrar vulnerabilidades high/critical
- [ ] **Cache:** `node_modules` e build artifacts devem ser cacheados no CI.
- [ ] **PR Comments:** CI deve comentar no PR com resumo de cobertura e status.
- [ ] **Branch Protection:** `master`/`main` exige CI verde + code review.

### 🚢 2.2. Deployment Strategy (Servile / Brikman)
- [ ] **OTA Updates:** `expo-updates` configurado para hotfixes sem app store review.
- [ ] **Staging Environment:** Perfil `staging` no EAS com TestFlight/Play Internal Track.
- [ ] **Feature Flags:** Sistema de feature flags para kill-switch de features em produção.
- [ ] **Versionamento:** `versionCode`/`buildNumber` auto-incrementado no CI via git tags/commits.
- [ ] **Rollback Capability:** Capacidade de reverter OTA updates em < 5 minutos.
- [ ] **Build Profiles:** `development`, `preview`, `staging`, `production` claramente separados.
- [ ] **Submit Config:** `eas submit` configurado para automação de submission (quando maduro).

### 📊 2.3. Observabilidade (Vijayakumaran - Four Golden Signals)
- [ ] **Crash Reporting:** Sentry/Bugsnag/Crashlytics integrado e validado em produção.
- [ ] **Remote Logging:** Logs de erro/warn enviados para plataforma externa (Sentry breadcrumbs).
- [ ] **Analytics Export:** Eventos de UX enviados para PostHog/Firebase/Amplitude (batch + flush).
- [ ] **Latency Tracking:** Tempo de carregamento de telas e queries críticas monitorado.
- [ ] **Error Tracking:** Taxa de erros por tela/feature trackeada e com alertas.
- [ ] **Alerting Rules:** Alertas configurados para:
  - Crash-free session rate < 99%
  - Error rate spike > 2x baseline
  - OTA update failure rate > 5%
  - Backend 5xx errors > 1%
- [ ] **Dashboards:** Dashboard de saúde do app (golden signals + business metrics).

### 🔒 2.4. DevSecOps & Security (Vijayakumaran / Brikman)
- [ ] **Dependency Scanning:** Dependabot/Snyk configurado para PRs automáticos de atualização.
- [ ] **Secrets Scanning:** `gitleaks` ou `eslint-plugin-no-secrets` no pre-commit e CI.
- [ ] **SAST:** `eslint-plugin-security` + CodeQL/Semgrep no CI.
- [ ] **SBOM:** `@cyclonedx/cyclonedx-npm` gerado em cada release e anexado ao artifact.
- [ ] **License Compliance:** Verificação de licenças de dependências (sem GPL em app proprietário).
- [ ] **SSL Pinning:** Hashes de certificado configurados via EAS Secrets em produção.
- [ ] **ProGuard/R8:** Code obfuscation habilitado em builds de produção Android.

### 🧪 2.5. Testing & Quality Gates (Brikman / Vijayakumaran)
- [ ] **Pre-commit Hooks:** Husky + lint-staged rodando lint + unit tests + tsc.
- [ ] **Coverage Thresholds:** Thresholds realistas por camada (services: 80%, utils: 70%, critical: 90%).
- [ ] **E2E Pipeline:** Detox configurado com emulador no CI (trigger por comentário `/e2e` em PR).
- [ ] **Flaky Test Detection:** Testes com `setTimeout` hard-coded são proibidos. Usar `waitFor()`.
- [ ] **Test Pyramid:** 70% unit, 20% integration, 10% E2E (monitorado no CI).
- [ ] **Mutation Testing:** Stryker configurado para validar qualidade dos testes (score > 60%).

### 🌿 2.6. Git & Versioning (Hattori)
- [ ] **Conventional Commits:** `commitlint` + husky `commit-msg` hook forçando formato.
- [ ] **Trunk-Based Development:** Branches de feature de curta duração (< 3 dias).
- [ ] **Semantic Versioning:** Version bump automatizado no CI baseado em conventional commits.
- [ ] **PR Template:** Template com checklist de arquitetura, testes, e segurança.
- [ ] **Git Bisect Ready:** Commits atômicos e bem descritos para facilitar debugging.

---

## 🧠 3. Prompt Patterns para o LLM (DevOps Validation)

Antes de implementar qualquer feature ou mudança de infraestrutura, o LLM deve executar o seguinte raciocínio (Chain of Thought):

```markdown
### 🚀 DevOps Validation Check (Obrigatório antes de codar)
1. **Esta feature precisa de feature flag?** (Se sim, criar no `features.ts`)
2. **Como será monitorada em produção?** (Crash reporting? Analytics? Logs?)
3. **Precisa de OTA update?** (Se sim, validar compatibilidade com `expo-updates`)
4. **Há novas dependências?** (Se sim, rodar `npm audit` e verificar licenças)
5. **Como será testada no CI?** (Unit? Integration? E2E?)
6. **Há secrets envolvidos?** (Se sim, usar EAS Secrets, NUNCA versionar)
7. **Precisa de migração de dados?** (Se sim, testar rollback)
8. **O pipeline de CI precisa ser atualizado?** (Novos thresholds? Novos jobs?)
```

---

## 🏗️ 4. Padrões de Implementação (Snippets de Referência)

### 4.1. CI Pipeline (GitHub Actions)
```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [master, main]
  pull_request:
    branches: [master, main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npx tsc --noEmit

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
      - name: Check coverage thresholds
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          if (( $(echo "$COVERAGE < 70" | bc -l) )); then
            echo "Coverage $COVERAGE% below 70% threshold"
            exit 1
          fi

  arch-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm run arch:check

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
      - run: npm ci
      - run: npm audit --audit-level=high
      - name: Secrets scan
        uses: gitleaks/gitleaks-action@v2
```

### 4.2. Feature Flags
```typescript
// src/config/features.ts
export const FEATURES = {
  newReportEngine: false,
  experimentalVoice: false,
  maintenanceExtracted: false,
  quickAddMode: true,
} as const;

export type FeatureFlag = keyof typeof FEATURES;

// src/hooks/useFeatureFlag.ts
export function useFeatureFlag(flag: FeatureFlag): boolean {
  // Em produção, pode buscar de remote config (EAS Update / LaunchDarkly)
  return FEATURES[flag];
}
```

### 4.3. OTA Update Integration
```json
// app.json (expo-updates config)
{
  "expo": {
    "updates": {
      "enabled": true,
      "checkAutomatically": "ON_LOAD",
      "fallbackToCacheTimeout": 0,
      "url": "https://u.expo.dev/[PROJECT_ID]"
    },
    "runtimeVersion": {
      "policy": "appVersion"
    }
  }
}
```

### 4.4. SBOM Generation
```json
// package.json scripts
{
  "scripts": {
    "sbom": "cyclonedx-npm --output-format JSON --output-file sbom.json",
    "release": "npm run sbom && eas build --profile production"
  }
}
```

### 4.5. Conventional Commits Enforcement
```javascript
// commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'docs', 'style', 'refactor',
      'perf', 'test', 'build', 'ci', 'chore', 'revert'
    ]],
    'subject-case': [2, 'always', 'lower-case'],
    'subject-max-length': [2, 'always', 100],
  },
};
```

```bash
# .husky/commit-msg
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"
npx --no -- commitlint --edit $1
```

---

## 🚦 5. Fitness Functions (Automação no CI/CD)

Para garantir que estas regras não sejam violadas no futuro, o pipeline deve executar:

### 5.1. Pre-commit Hooks (Husky + lint-staged)
```json
// lint-staged.config.js
module.exports = {
  '*.{ts,tsx}': [
    'eslint --fix',
    'prettier --write',
  ],
  '*.test.{ts,tsx}': [
    'jest --bail --findRelatedTests',
  ],
};
```

```bash
# .husky/pre-commit
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx lint-staged
npm run build
npx depcruise src --config .dependency-cruiser.js
npm test -- --selectProjects unit --passWithNoTests
```

### 5.2. CI Gates Obrigatórios
```yaml
# Checklist de gates no CI
gates:
  - name: "Lint"
    command: "npm run lint"
    blocking: true
  - name: "TypeScript Build"
    command: "npx tsc --noEmit"
    blocking: true
  - name: "Unit Tests"
    command: "npm test -- --selectProjects unit"
    blocking: true
  - name: "Integration Tests"
    command: "npm test -- --selectProjects integration"
    blocking: true
  - name: "Coverage Thresholds"
    command: "npm test -- --coverage"
    blocking: true
  - name: "Architecture Check"
    command: "npm run arch:check"
    blocking: true
  - name: "Security Audit"
    command: "npm audit --audit-level=high"
    blocking: true
  - name: "Secrets Scan"
    command: "gitleaks detect --source ."
    blocking: true
```

### 5.3. DORA Metrics Tracking
```typescript
// scripts/dora-metrics.ts
// Rodar semanalmente para trackear métricas DORA
interface DoraMetrics {
  deploymentFrequency: number; // deploys/dia
  leadTimeForChanges: number; // horas (commit → deploy)
  changeFailureRate: number; // % de deploys que causam falha
  timeToRestoreService: number; // minutos (falha → recovery)
}

// Integrar com GitHub API + Sentry API + EAS API para calcular
```

---

## 📊 6. Matriz de Maturidade DevOps

| Nível | CI/CD | Observabilidade | Deployment | Security | Score |
|-------|-------|-----------------|------------|----------|-------|
| **1 - Ad Hoc** | Manual builds | Sem crash reporting | App store only | Secrets no código | 10/50 |
| **2 - Repeatable** | CI básico (lint+test) | Crash reporting | Staging profile | npm audit no CI | 25/50 |
| **3 - Defined** | CI completo + gates | Remote logs + analytics | OTA updates | Dependabot + SAST | 35/50 |
| **4 - Managed** | Feature flags + SBOM | Dashboards + alerting | Auto-versioning | DevSecOps pipeline | 45/50 |
| **5 - Optimized** | DORA metrics tracked | Golden signals + A/B | Canary/Blue-green | Zero-trust + compliance | 50/50 |

---

## 💡 7. Como Usar Este Arquivo no Seu Harness

### 7.1. No `AGENTS.md` ou `CLAUDE.md`
Adicione a instrução:
```markdown
## DevOps & CI/CD
Antes de escrever código de infraestrutura, deployment ou observabilidade, consulte e obedeça estritamente as regras em `docs/DEVOPS_CHECKLIST.md`.

**Obrigatório:**
1. Validar contra os Hard Gates (nunca commitar secrets, sempre passar no CI)
2. Considerar feature flags para novas features
3. Garantir que crash reporting e analytics estão instrumentados
4. Verificar dependências com `npm audit`
5. Atualizar CI/CD se necessário
```

### 7.2. Como System Prompt / Rule
Em ferramentas como Cursor, Copilot ou Aider, adicione este arquivo como uma `@Rule` global.

### 7.3. Code Review por IA
Peça para o LLM:
```
Revise este diff usando o checklist do DEVOPS_CHECKLIST.md. Aponte:
- Violações de Hard Gates (secrets versionados, falta de testes)
- Falta de feature flags para features experimentais
- Ausência de instrumentação de observabilidade (crash reporting, analytics)
- Dependências não verificadas (npm audit)
- Violações de conventional commits
```

### 7.4. Ao Criar Novas Features
Use o prompt:
```
Implemente a feature X seguindo o DEVOPS_CHECKLIST.md:
1. Crie feature flag em `features.ts`
2. Instrumente analytics (trackUXEvent)
3. Adicione crash reporting (Sentry breadcrumbs)
4. Escreva testes (unit + integration)
5. Valide que não há secrets hardcoded
6. Atualize CI se necessário
```

### 7.5. Ao Configurar Infraestrutura
Use o prompt:
```
Configure [deploy/CI/observability] seguindo o DEVOPS_CHECKLIST.md:
- Valide contra os 4 pilares (CI/CD, Deployment, Observability, Security)
- Garanta que há rollback capability
- Configure alertas para golden signals
- Gere SBOM para compliance
```

---

## 🎯 8. Roadmap de Evolução DevOps

### Wave 1 - Critical (0-30 dias)
- [ ] GitHub Actions CI pipeline completo
- [ ] Sentry/Crashlytics integrado
- [ ] expo-updates configurado
- [ ] npm audit + Dependabot no CI
- [ ] E2E pipeline funcional
- [ ] Testes de repositórios e business layer

### Wave 2 - High (30-90 dias)
- [ ] SBOM generation em releases
- [ ] Staging EAS profile + TestFlight
- [ ] Analytics export (PostHog/Firebase)
- [ ] Remote log shipping
- [ ] SSL pinning enforcement
- [ ] Conventional commits enforcement
- [ ] Secrets scanning (gitleaks)

### Wave 3 - Medium (90+ dias)
- [ ] Feature flags (LaunchDarkly/custom)
- [ ] Auto-increment version no CI
- [ ] CodeQL/Semgrep SAST avançado
- [ ] Development dashboard (debug screen)
- [ ] DORA metrics tracking
- [ ] Knowledge sharing sessions

---

## 📚 9. Referências e Frameworks

| Framework | Autor | Aplicação no Projeto |
|-----------|-------|---------------------|
| **CALMS** | Vijayakumaran | Cultura, Automação, Lean, Measurement, Sharing |
| **DORA Metrics** | Servile/Hattori | Deployment Frequency, Lead Time, Change Failure, Time to Restore |
| **Continuous Deployment** | Brikman | Pipeline stages, test pyramid, zero-downtime |
| **DevSecOps** | Vijayakumaran | Shift-left security, SBOM, SAST, secrets scanning |
| **Four Golden Signals** | Google/Vijayakumaran | Latency, Traffic, Errors, Saturation |
| **GitOps** | Hattori | Trunk-based dev, conventional commits, semantic versioning |

---

## ✅ 10. Checklist de Go-Live (Pre-Production)

Antes de publicar qualquer versão em produção, valide:

- [ ] CI pipeline 100% verde (lint, build, test, coverage, arch, security)
- [ ] Crash reporting validado em staging (Sentry receiving events)
- [ ] OTA updates testados (push trivial JS change, verify on device)
- [ ] Feature flags configuradas para novas features (kill-switch ready)
- [ ] SBOM gerado e anexado ao release
- [ ] SSL pinning hashes configurados via EAS Secrets
- [ ] Backend health check respondendo (`/health`)
- [ ] Rate limiting configurado em endpoints críticos
- [ ] Alertas configurados (crash-free rate, error spike)
- [ ] Runbook de suporte criado (principais falhas e como validar)
- [ ] QA final com 3-5 usuários beta
- [ ] Privacy policy e Data Safety atualizados
- [ ] Conventional commits validados no histórico
- [ ] Version bump automatizado e testado

---

**Data de Criação:** 2026-07-24  
**Versão:** 1.0  
**Status:** ✅ ATIVO  
**Próxima Revisão:** 2026-08-24 (trimestral)