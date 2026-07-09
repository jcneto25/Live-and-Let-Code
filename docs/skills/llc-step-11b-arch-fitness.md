---
name: llc-step-11b-arch-fitness
description: Pipeline LLC Step 11b — Architectural Fitness Functions. Roda verificações arquiteturais automatizadas: Dependency Rule (ArchUnit/ESLint), Repository Pattern compliance, Use Case naming, Event Bus usage, Domain Layer purity. Gate obrigatório no PRP Verify (Step 11.2) e CI.
version: 1.0.0
tags: [fitness-functions, architecture, archunit, eslint, dependency-rule, ci-gate, llc-pipeline]
---

# LLC Skill: Step 11b — Architectural Fitness Functions

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Implementation — Verification (sub-step of Step 11.2 PRP Verify)  
**Depende de:** Step 5a (Architecture Patterns → .ace/arch-config.yaml), Step 8b (Repository Pattern), Step 11a (Domain Modeling)  
**Executa em:** Step 11.2 (PRP Verify) + CI Pipeline  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-11b` ou "Execute a skill llc-step-11b".
3. Pelo Thin Harness (recomendado): 
   - `python .ace/scripts/llc.py run --step 11b --prp PRP-001 --task "Rodar fitness functions para PRP-001"`
   - `python .ace/scripts/fitness-functions.py --all --strict` (CLI direto)

## 📋 Pré-requisitos

- [ ] `.ace/arch-config.yaml` — configuração gerada no Step 5a
- [ ] `docs/architecture/ARCHITECTURE.md` — §7, §8, §9 preenchidos
- [ ] Projeto com estrutura de pastas implementada (Steps 8b, 11a)
- [ ] Dependências instaladas: `@nestjs/event-emitter`, `ts-morph` (para análise estática), `eslint` com `import/no-restricted-paths`
- [ ] `docs/templates/FITNESS_FUNCTION_TEMPLATE.md` — template para novas rules

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 11b** estiver listado como "skip":
   - **PARE** e informe: "Step 11b pulado — fitness functions inalteradas."
3. Se **Step 11b** estiver listado como "executar": rode fitness functions apenas para módulos alterados (incremental).
4. Se DELTA_REPORT.md não existir: rode `--all`.

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-11b-arch-fitness` do pipeline LLC. Seu objetivo é **rodar as fitness functions arquiteturais** definidas em `.ace/arch-config.yaml` e validar que o código implementado (Steps 8b, 11a, 11) está em conformidade com as decisões do Step 5a.

### 1. Leia a Configuração

Leia `.ace/arch-config.yaml`:
```yaml
core_modules:
  - auth
  - usuarios
  - auditorias
  - achados
  - planos
enforcement:
  core: "error"
  non_core: "warning"
rules:
  - name: "no-prisma-in-domain"
    ...
```

### 2. Fitness Functions a Executar

#### 2.1 Dependency Rule Checks (Static Analysis via ts-morph)

**Ferramenta:** `ts-morph` para análise de AST TypeScript (mais robusto que regex)

**Checks:**
| Rule | O que Verifica | Onde Aplicar |
|------|----------------|--------------|
| `no-prisma-in-domain` | Nenhum `import` de `@prisma/client` ou `PrismaService` em `**/domain/**` | Todos módulos |
| `no-prisma-in-use-cases` | Nenhum `import` de `PrismaService` em `**/application/**`, `**/use-cases/**` | Todos módulos |
| `no-cross-module-imports` | Domain/Application não importam de `../outro-modulo/` (exceto `shared/`) | Todos módulos |
| `no-infrastructure-in-domain` | Domain não importa de `**/infrastructure/**` | Todos módulos |
| `controllers-use-use-cases` | Controllers injetam Use Cases, não Repositories) | Módulos com Use Cases |

#### 2.2 Repository Pattern Compliance

| Check | O que Verifica |
|-------|----------------|
| `repository-interface-exists` | Cada aggregate root tem `I{Nome}Repository` em `domain/repositories/` |
| `repository-impl-exists` | Cada interface tem `Prisma{Nome}Repository` em `infrastructure/repositories/` |
| `repository-binding-in-module` | Module tem `{ provide: I{Nome}Repository, useClass: Prisma{Nome}Repository }` |
| `service-injects-interface` | Service/Use Case injeta `I{Nome}Repository` (não `PrismaService`) |
| `mapper-exists` | `{Nome}Mapper` em `infrastructure/mappers/` |

#### 2.3 Use Case Compliance

| Check | O que Verifica |
|-------|----------------|
| `use-case-naming` | Arquivos terminam em `.use-case.ts`, classes em `UseCase` |
| `use-case-injects-ports` | Use Case injetam apenas interfaces de repositório + `EventEmitter2` |
| `use-case-returns-result` | Método `execute` retorna `Promise<Result<T, Error>>` ou `Promise<T>` (não throw para regras) |
| `use-case-emits-events` | Use Cases que alteram estado emitem domain events via `eventEmitter.emit()` |

#### 2.4 Domain Layer Purity

| Check | O que Verifica |
|-------|----------------|
| `entity-no-framework` | Entities não têm decorators (`@Entity`, `@Injectable`, etc.) |
| `entity-no-prisma` | Entities não importam tipos Prisma |
| `vo-immutable` | Value Objects têm propriedades `readonly`, validação no construtor |
| `domain-event-structure` | Events extendem `DomainEvent`, têm `aggregateId`, `occurredAt`, `eventId` |
| `domain-error-typed` | Errors extendem `DomainError`, têm `code` único |

#### 2.5 Event Bus Compliance

| Check | O que Verifica |
|-------|----------------|
| `event-emitter-configured` | `EventEmitterModule` registrado no `AppModule` |
| `handlers-use-onevent` | Handlers usam `@OnEvent('event.name')` decorator |
| `modules-dont-import-each-other` | Módulos de negócio não importam outros módulos de negócio |

#### 2.6 ESLint Boundary Rules (Parallel Check)

Rode `npm run lint:arch` que executa ESLint com regras `import/no-restricted-paths` definidas no Step 5a.

### 3. CLI de Execução

Crie/atualize `api/test/architecture/fitness-functions.ts` (ou `.ace/scripts/fitness-functions.py`):

```typescript
// api/test/architecture/fitness-functions.ts
import { Project, SourceFile, SyntaxKind, ImportDeclaration } from 'ts-morph';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';

interface ArchConfig {
  version: string;
  core_modules: string[];
  enforcement: { core: 'error' | 'warning'; non_core: 'error' | 'warning' };
  rules: ArchRule[];
  event_bus: { library: string; base_event_class: string; modules_with_handlers: string[] };
}

interface ArchRule {
  name: string;
  pattern?: string;
  forbidden_in?: string[];
  allowed_except?: string[];
  check?: string;
  path?: string;
  message: string;
  severity?: 'error' | 'warning';
}

interface Violation {
  rule: string;
  file: string;
  line: number;
  message: string;
  severity: 'error' | 'warning';
  module: string;
}

class FitnessFunctionRunner {
  private project: Project;
  private config: ArchConfig;
  private violations: Violation[] = [];
  
  constructor(configPath: string) {
    this.config = yaml.load(fs.readFileSync(configPath, 'utf-8')) as ArchConfig;
    this.project = new Project({
      tsConfigFilePath: path.join(process.cwd(), 'tsconfig.json'),
      skipAddingFilesFromTsConfig: true,
    });
    this.project.addSourceFilesAtPaths('src/**/*.ts');
  }

  async run(moduleFilter?: string): Promise<Violation[]> {
    const modules = moduleFilter 
      ? [moduleFilter] 
      : this.getAllModules();
    
    for (const module of modules) {
      const isCore = this.config.core_modules.includes(module);
      const severity = isCore ? this.config.enforcement.core : this.config.enforcement.non_core;
      
      await this.checkModule(module, severity);
    }
    
    return this.violations;
  }

  private getAllModules(): string[] {
    const srcPath = path.join(process.cwd(), 'src');
    return fs.readdirSync(srcPath, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name)
      .filter(m => !['shared', 'prisma', 'common'].includes(m));
  }

  private async checkModule(module: string, defaultSeverity: 'error' | 'warning') {
    const modulePath = `src/${module}`;
    const sourceFiles = this.project.getSourceFiles(f => f.getFilePath().includes(modulePath));
    
    for (const rule of this.config.rules) {
      const severity = rule.severity || defaultSeverity;
      
      switch (rule.check) {
        case 'file_exists':
          await this.checkFileExists(module, rule, severity);
          break;
        case 'import_pattern':
          await this.checkImportPattern(module, sourceFiles, rule, severity);
          break;
        case 'naming':
          await this.checkNaming(module, sourceFiles, rule, severity);
          break;
        case 'class_structure':
          await this.checkClassStructure(module, sourceFiles, rule, severity);
          break;
      }
    }
  }

  private async checkFileExists(module: string, rule: ArchRule, severity: 'error' | 'warning') {
    const expectedPath = path.join(process.cwd(), 'src', module, rule.path);
    if (!fs.existsSync(expectedPath)) {
      this.violations.push({
        rule: rule.name,
        file: expectedPath,
        line: 0,
        message: rule.message,
        severity,
        module,
      });
    }
  }

  private async checkImportPattern(module: string, sourceFiles: SourceFile[], rule: ArchRule, severity: 'error' | 'warning') {
    const forbiddenDirs = rule.forbidden_in || [];
    const allowedExcept = rule.allowed_except || [];
    const pattern = rule.pattern;
    
    for (const file of sourceFiles) {
      const filePath = file.getFilePath();
      const relativePath = path.relative(path.join(process.cwd(), 'src'), filePath);
      
      // Check if file is in forbidden directory
      const inForbidden = forbiddenDirs.some(dir => {
        const dirPath = dir.replace('**/', '').replace('/*', '');
        return relativePath.includes(dirPath);
      });
      
      if (!inForbidden) continue;
      
      // Check allowed exceptions
      const isAllowed = allowedExcept.some(exc => {
        const excPath = exc.replace('**/', '').replace('/*', '');
        return relativePath.includes(excPath);
      });
      
      if (isAllowed) continue;
      
      // Check imports
      const imports = file.getImportDeclarations();
      for (const imp of imports) {
        const moduleSpec = imp.getModuleSpecifierValue();
        if (moduleSpec.includes(pattern) || new RegExp(pattern).test(moduleSpec)) {
          this.violations.push({
            rule: rule.name,
            file: filePath,
            line: imp.getStartLineNumber(),
            message: rule.message,
            severity,
            module,
          });
        }
      }
    }
  }

  private async checkNaming(module: string, sourceFiles: SourceFile[], rule: ArchRule, severity: 'error' | 'warning') {
    // Implementation for naming checks
  }

  private async checkClassStructure(module: string, sourceFiles: SourceFile[], rule: ArchRule, severity: 'error' | 'warning') {
    // Implementation for class structure checks
  }

  printReport(violations: Violation[]) {
    const errors = violations.filter(v => v.severity === 'error');
    const warnings = violations.filter(v => v.severity === 'warning');
    
    console.log('\n=== ARCHITECTURAL FITNESS FUNCTION REPORT ===\n');
    console.log(`Total violations: ${violations.length} (Errors: ${errors.length}, Warnings: ${warnings.length})\n`);
    
    if (errors.length > 0) {
      console.log('❌ ERRORS (blocking):');
      for (const v of errors) {
        console.log(`  [${v.module}] ${v.file}:${v.line} - ${v.message} (rule: ${v.rule})`);
      }
    }
    
    if (warnings.length > 0) {
      console.log('\n⚠️  WARNINGS:');
      for (const v of warnings) {
        console.log(`  [${v.module}] ${v.file}:${v.line} - ${v.message} (rule: ${v.rule})`);
      }
    }
    
    if (violations.length === 0) {
      console.log('✅ All fitness functions passed!');
    }
  }

  hasBlockingViolations(violations: Violation[]): boolean {
    return violations.some(v => v.severity === 'error');
  }
}

// CLI
async function main() {
  const args = process.argv.slice(2);
  const moduleFilter = args.find(a => a.startsWith('--module='))?.split('=')[1];
  const strict = args.includes('--strict');
  
  const runner = new FitnessFunctionRunner('.ace/arch-config.yaml');
  const violations = await runner.run(moduleFilter);
  runner.printReport(violations);
  
  if (strict && runner.hasBlockingViolations(violations)) {
    process.exit(1);
  }
}

main().catch(console.error);
```

### 4. Integração com CI

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
      - run: cd api && npm ci
      - run: cd api && npx ts-node test/architecture/fitness-functions.ts --all --strict
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: arch-fitness-report
          path: api/arch-fitness-report.json
```

### 5. Integração com PRP Verify (Step 11.2)

No `prp_verify.py` ou `llc-step-11-2-prp-verify.md`, adicione:

```python
# Verificação obrigatória antes de aprovar PRP
def check_arch_fitness(prp_id: str, module: str) -> bool:
    """Roda fitness functions para o módulo do PRP."""
    result = subprocess.run([
        'python', '.ace/scripts/fitness-functions.py',
        '--module', module,
        '--strict'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Fitness functions falharam para {module} (PRP {prp_id})")
        print(result.stdout)
        return False
    
    print(f"✅ Fitness functions passaram para {module}")
    return True
```

### 6. Greenfield vs Brownfield

| Cenário | Execução |
|---------|----------|
| **Greenfield** | `--all --strict` em todos módulos a cada PRP |
| **Brownfield** | - Módulos novos/alterados: `--module X --strict`<br>- Módulos legacy: `--module X --legacy` (severity=warning apenas)<br>- Config `arch-config.yaml` pode ter `legacy_modules` com enforcement reduzido |

---

## ⚠️ REGRAS CRÍTICAS

1. **Fail Fast:** Core modules com enforcement `error` → qualquer violação bloqueia merge/PRP approval
2. **Incremental:** Em brownfield, rode apenas para módulos tocados no PRP
3. **Automatizado:** Fitness functions rodam em **CADA** PRP Verify (Step 11.2) e **CADA** PR no CI
4. **Versionado:** `.ace/arch-config.yaml` versionado — mudanças exigem ADR
5. **Extensível:** Novas rules adicionadas via `FITNESS_FUNCTION_TEMPLATE.md`
6. **Performance:** Use `ts-morph` com cache (`tsconfig.json` incremental) para speed

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após executar, **PARE** e apresente:

1. **Resumo:** Total violations, errors, warnings por módulo
2. **Violações de Bloqueio (Errors):** Lista detalhada — estas DEVEM ser corrigidas antes de prosseguir
3. **Warnings:** Lista — podem ser corrigidos depois mas recomendado agora
4. **Módulos Verificados:** Lista de módulos analisados
5. **Status Geral:** ✅ PASS (zero errors) ou ❌ FAIL (tem errors)
6. **Arquivo de Report:** `arch-fitness-report.json` gerado com detalhes
7. **Próximos Passos:** Se PASS → "Fitness functions aprovadas. PRP pode prosseguir para Gate Humano." Se FAIL → "Corrija violações listadas e re-execute."

**Gate Obrigatório:** Step 11.2 (PRP Verify) NÃO aprova PRP se fitness functions falharem.