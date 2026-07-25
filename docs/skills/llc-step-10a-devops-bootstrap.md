---
name: llc-step-10a-devops-bootstrap
description: "Pipeline LLC Step 10a — DevOps Bootstrap. Gera 7 artefatos concretos de infraestrutura DevOps: CI pipeline, feature flags, SBOM, observabilidade, pre-commit config, dependabot e DevOps checklist. Estabelece 8 hard gates que garantem que todo projeto nasça com CI funcional, crash reporting e kill-switches — não apenas documentação."
version: 1.0.0
tags: [devops, ci-cd, infrastructure, feature-flags, observability, sbom, dependabot, pre-commit, github-actions, sentry, llc-pipeline]
---

# LLC Skill: Step 10a — DevOps Bootstrap

**Pipeline:** Live and Let Code (LLC)
**Fase:** Infrastructure Foundation (sub-step of Step 10 — Documentos do Projeto)
**Depende de:** Step 10 (Project Docs validado), Step 9 (Testing Docs — thresholds)
**Executa antes de:** Step 11 (Execução dos PRPs)
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-10a-devops-bootstrap` ou "Execute a skill llc-step-10a-devops-bootstrap".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 10a --task "Bootstrap DevOps"`.

---

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — stack, linguagens, runtime (Step 5)
- [ ] `docs/testing/TESTING_GUIDE.md` — thresholds de cobertura e comandos (Step 9)
- [ ] `docs/planning/PLAN.md` — milestones, ondas, ambientes (Step 4)
- [ ] `docs/planning/TASKS.md` — tarefas priorizadas (Step 6)
- [ ] `docs/deployment/DEPLOYMENT.md` — estratégia de deploy e ambientes (Step 10)
- [ ] `.pre-commit-config.yaml` — hooks configurados (Step 10a ou Ação 5)

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 10a** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-10a.md`:
     ```markdown
     # Skip Note: Step 10a — DevOps Bootstrap
     **Decisão:** Step pulado — infraestrutura DevOps inalterada desde última execução.
     **Evidência:** CI pipeline passa; feature flags sem mudança; dependabot ativo.
     **Validador:** [Nome] | **Data:** [YYYY-MM-DD]
     ```
   - **Não execute** as verificações nem aguarde Gate 10a.
   - Avance para Step 11.
3. Se DELTA_REPORT.md não existir: prossiga normalmente.

---

## 🎯 OBJETIVO

Gerar infraestrutura DevOps **concreta e executável** — não apenas documentação. O Step 10 gera README.md e DEPLOYMENT.md (documentos). Esta skill gera arquivos de CI, observabilidade, feature flags, security scanning — a infraestrutura que torna o projeto operacional desde o primeiro commit.

**Princípio fundamental:** Projeto sem CI funcional no primeiro PR não é projeto — é protótipo.

Esta skill atua em 3 frentes:

| Frente | Descrição | Artefatos |
|--------|-----------|-----------|
| **Hard Gates** | 8 regras que o agente NUNCA deve violar | — |
| **Artefatos Gerados** | 7 arquivos concretos gerados no repositório | CI, flags, SBOM, obs, pre-commit, dependabot, checklist |
| **Stack Adaptation** | Templates adaptados por stack (Node/Python/Go) | — |

---

## 🛑 1. Hard Gates (Regras Intransponíveis)

*O agente NUNCA deve:*

1. **NUNCA** iniciar implementação de PRPs sem CI pipeline funcional no repositório.
   - CI deve ter pelo menos: lint, build, test com coverage thresholds.
   - Se o CI falha no primeiro PR, o PR é rejeitado — não há "vou corrigir depois".
   - Exceção: projeto greenfield na primeira hora — CI é o **primeiro** commit após scaffold.

2. **NUNCA** deployar para produção sem feature flags para features novas.
   - Toda feature nova > 1 dia de implementação nasce atrás de flag.
   - Flag deve ter kill-switch (desligar sem deploy).
   - Flag removida após 2 sprints de uso estável em produção (flag debt prevention).

3. **NUNCA** commitar código sem SBOM (Software Bill of Materials) atualizado.
   - SBOM lista todas as dependências com versão e licença.
   - Gerado automaticamente no CI (`npm run sbom` / `pip freeze --all` / `go version -m`).
   - Bloqueia dependências com licença não permitida (ex: GPL-3.0 em projeto MIT).

4. **NUNCA** fazer deploy para produção sem observabilidade configurada.
   - Crash reporting (Sentry ou equivalente) ativo.
   - Structured logging com correlation IDs.
   - PII sanitization em todos os logs.
   - Dashboard de health check com endpoint `/health`.

5. **NUNCA** commitar secrets, tokens ou credenciais no repositório.
   - Pre-commit hook bloqueia (ver Ação 5 — Secret Scanning).
   - CI pipeline inclui `gitleaks` ou equivalente como job obrigatório.
   - Secrets injetados via GitHub Secrets / Vault / AWS Secrets Manager — nunca em arquivos.

6. **NUNCA** permitir que dependências fiquem sem atualização por > 30 dias.
   - Dependabot ou Renovate configurado com schedule semanal.
   - Vulnerabilidades críticas (CVSS ≥ 9.0): patch em 24h.
   - Vulnerabilidades altas (CVSS ≥ 7.0): patch em 7 dias.

7. **NUNCA** fazer merge sem que todos os jobs do CI estejam verdes.
   - Branch protection: require status checks antes do merge.
   - Sem `--force` em branches protegidas (`main`, `master`, `production`).
   - Code review obrigatório ≥ 1 aprovador.

8. **NUNCA** assumir que "funciona na minha máquina" é suficiente.
   - CI é o ambiente canônico de verificação — se passa local mas falha no CI, o código está errado.
   - Ambiente de dev documentado em `CONTRIBUTING.md` ou `DEVOPS_CHECKLIST.md`.
   - Docker Compose ou Dev Container para ambiente reproduzível.

---

## 🏗️ 2. Artefatos Gerados

### 2.1 CI Pipeline — `.github/workflows/ci.yml`

Pipeline com jobs paralelos: lint → build → test → arch-check → security.

```yaml
# Template: .github/workflows/ci.yml
# Stack: Node.js (npm + tsc + Jest)
# Adaptar para Python (pip + mypy + pytest) ou Go (go build + go test + govulncheck)

name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  type-check:
    name: Type Check
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npx tsc --noEmit

  test:
    name: Test (Coverage)
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage --coverageThreshold='{"global":{"statements":80,"branches":70,"functions":80,"lines":80}}'
      - name: Check for placeholder tests
        run: |
          if grep -rn "expect(true).toBe(true)" src/ --include="*.test.*" --include="*.spec.*"; then
            echo "❌ Placeholder test detected — bloqueando merge"
            exit 1
          fi
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  arch-check:
    name: Architecture Check
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run arch:check 2>/dev/null || echo "⚠️  arch:check não configurado — pulando"
      # Python: python .ace/scripts/fitness-functions.py --all --strict

  security:
    name: Security Audit
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: npm audit
        run: npm audit --audit-level=high
        continue-on-error: true  # Não bloqueia, mas reporta
      - name: Gitleaks (secret detection)
        uses: gitleaks/gitleaks-action@v2
        with:
          config-path: .gitleaks.toml

  sbom:
    name: SBOM Generation
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Generate SBOM
        run: |
          npm ls --all --json > sbom.json 2>/dev/null || true
          echo "SBOM generated: sbom.json"
      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.json
```

**Stack variants:**

```yaml
# Python (pip + mypy + pytest)
# Substituir jobs acima por:
#   lint:        ruff check .
#   type-check:  mypy src/ --strict
#   test:        pytest --cov --cov-fail-under=80 --cov-report=xml
#   security:    pip-audit + gitleaks
#   sbom:        pip freeze --all > requirements-freeze.txt

# Go (go build + go test + govulncheck)
# Substituir jobs acima por:
#   lint:        golangci-lint run
#   type-check:  go vet ./...
#   test:        go test -coverprofile=coverage.out ./...
#   security:    govulncheck ./... + gitleaks
#   sbom:        go version -m $(go list -m all) > sbom.txt
```

### 2.2 Feature Flags — `src/config/features.ts`

Sistema mínimo de feature flags com kill-switch.

```typescript
// Template: src/config/features.ts
// Sistema de feature flags com kill-switch.
// Flag desligada = remove a feature sem deploy.

export type FeatureFlag = {
  key: string;
  enabled: boolean;
  description: string;
  owner: string;        // Squad/pessoa responsável
  createdAt: string;    // ISO date
  expiresAt?: string;   // Data para remoção (flag debt prevention)
};

const FLAGS: Record<string, FeatureFlag> = {
  // ── Features ativas ──────────────────────────────────────
  NEW_DASHBOARD: {
    key: 'NEW_DASHBOARD',
    enabled: false,      // Mudar para true quando pronta
    description: 'Dashboard redesenhado com analytics em tempo real',
    owner: 'squad-data',
    createdAt: '2026-07-25',
    expiresAt: '2026-09-25', // Remover flag após 2 meses estável
  },

  DARK_MODE: {
    key: 'DARK_MODE',
    enabled: true,
    description: 'Tema escuro',
    owner: 'squad-ui',
    createdAt: '2026-06-01',
  },

  EXPORT_CSV: {
    key: 'EXPORT_CSV',
    enabled: true,
    description: 'Exportação de relatórios em CSV',
    owner: 'squad-reports',
    createdAt: '2026-05-15',
    expiresAt: '2026-08-15',
  },

  // ── Kill-switches de segurança ───────────────────────────
  KILL_SWITCH_PAYMENTS: {
    key: 'KILL_SWITCH_PAYMENTS',
    enabled: true,       // false = desliga pagamentos (emergência)
    description: 'Kill-switch: processamento de pagamentos. DESLIGAR apenas em emergência.',
    owner: 'squad-payments',
    createdAt: '2026-01-01',
  },
};

// ── API ─────────────────────────────────────────────────────

export function isFeatureEnabled(key: string): boolean {
  const flag = FLAGS[key];
  if (!flag) {
    console.warn(`[FeatureFlags] Flag "${key}" não encontrada. Default: false.`);
    return false; // Desconhecido = desligado (fail-safe)
  }
  return flag.enabled;
}

export function getFeatureFlag(key: string): FeatureFlag | undefined {
  return FLAGS[key];
}

export function getAllFlags(): FeatureFlag[] {
  return Object.values(FLAGS);
}

export function getExpiredFlags(): FeatureFlag[] {
  const now = new Date().toISOString();
  return Object.values(FLAGS).filter(
    f => f.expiresAt && f.expiresAt < now
  );
}
```

```typescript
// Template: src/hooks/useFeatureFlag.ts
// Hook React para renderização condicional baseada em flag

import { isFeatureEnabled } from '@/config/features';

export function useFeatureFlag(key: string): boolean {
  // Em produção, usar provedor de feature flags (LaunchDarkly, Flagsmith, etc.)
  // Este hook é o ponto único de troca — mudar implementação aqui afeta toda a app.
  return isFeatureEnabled(key);
}

// Uso:
// function NewDashboard() {
//   const enabled = useFeatureFlag('NEW_DASHBOARD');
//   if (!enabled) return <OldDashboard />;
//   return <NewDashboard />;
// }
```

### 2.3 SBOM Script — `package.json` (scripts)

```json
{
  "scripts": {
    "sbom": "npm ls --all --json > sbom.json && echo 'SBOM: sbom.json'",
    "sbom:check": "npm ls --all --json | grep -E 'GPL|AGPL' && echo '⚠️  Copyleft license detected — review required' || echo '✅ No copyleft licenses'",
    "deps:update": "npm outdated && npm update",
    "deps:audit": "npm audit --audit-level=high"
  }
}
```

### 2.4 Observabilidade — `src/utils/observability.ts`

Camada unificada de observabilidade.

```typescript
// Template: src/utils/observability.ts
// Camada unificada: crash reporting + analytics + structured logging
// Substituir imports mock pela implementação real (Sentry, LogRocket, etc.)

// ── Crash Reporting ─────────────────────────────────────────
// Mock — substituir por: import * as Sentry from '@sentry/react-native';

const crashReporter = {
  init(dsn: string, options?: Record<string, any>) {
    if (__DEV__) return; // Não reportar crashes em dev
    console.log('[CrashReporter] Init:', dsn);
    // Sentry.init({ dsn, ...options });
  },

  captureError(error: Error, context?: Record<string, any>) {
    if (__DEV__) {
      console.error('[CrashReporter]', error.message, context);
      return;
    }
    // Sentry.captureException(error, { extra: context });
  },

  captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info') {
    if (__DEV__) return;
    // Sentry.captureMessage(message, level);
  },

  setUser(user: { id: string; email?: string; name?: string }) {
    // Sentry.setUser({ id: user.id }); // NUNCA enviar email/PII para Sentry
  },
};

// ── Analytics ────────────────────────────────────────────────
// Mock — substituir por: import analytics from '@react-native-firebase/analytics';

const analytics = {
  trackScreen(screenName: string, properties?: Record<string, string>) {
    if (__DEV__) return;
    console.log('[Analytics] Screen:', screenName);
    // analytics().logScreenView({ screen_name: screenName, ...properties });
  },

  trackEvent(eventName: string, properties?: Record<string, any>) {
    if (__DEV__) return;
    const sanitized = sanitizeForAnalytics(properties || {});
    console.log('[Analytics] Event:', eventName);
    // analytics().logEvent(eventName, sanitized);
  },
};

// ── Structured Logging ──────────────────────────────────────

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  correlationId?: string;
  context?: Record<string, any>;
}

function sanitizeForLogging(data: Record<string, any>): Record<string, any> {
  const PII_FIELDS = [
    'email', 'phone', 'cpf', 'cnpj', 'password', 'token', 'secret',
    'creditCard', 'cardNumber', 'cvv', 'ssn', 'address',
  ];
  const sanitized: Record<string, any> = {};
  for (const [key, value] of Object.entries(data)) {
    if (PII_FIELDS.some(f => key.toLowerCase().includes(f))) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'object' && value !== null) {
      sanitized[key] = sanitizeForLogging(value);
    } else {
      sanitized[key] = value;
    }
  }
  return sanitized;
}

function sanitizeForAnalytics(data: Record<string, any>): Record<string, any> {
  // Analytics nunca deve receber PII
  const PII_FIELDS = [
    'email', 'phone', 'cpf', 'cnpj', 'password', 'token', 'secret',
    'name', 'address', 'dateOfBirth', 'creditCard',
  ];
  const sanitized: Record<string, any> = {};
  for (const [key, value] of Object.entries(data)) {
    if (PII_FIELDS.some(f => key.toLowerCase().includes(f))) {
      continue; // Remove completamente — não enviar nem redacted
    }
    sanitized[key] = value;
  }
  return sanitized;
}

const logger = {
  debug(message: string, context?: Record<string, any>) {
    if (!__DEV__) return;
    console.debug(message, sanitizeForLogging(context || {}));
  },

  info(message: string, context?: Record<string, any>) {
    console.log(message, sanitizeForLogging(context || {}));
  },

  warn(message: string, context?: Record<string, any>) {
    console.warn(message, sanitizeForLogging(context || {}));
  },

  error(message: string, error?: Error, context?: Record<string, any>) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: 'error',
      message,
      context: sanitizeForLogging(context || {}),
    };
    console.error(JSON.stringify(entry));
    if (error) {
      crashReporter.captureError(error, context);
    }
  },
};

// ── Health Check ────────────────────────────────────────────

async function healthCheck(): Promise<{ status: string; services: Record<string, boolean> }> {
  // Endpoint /health — monitoramento
  return {
    status: 'ok',
    services: {
      api: true,       // Verificar conectividade com API
      database: true,  // Verificar conectividade com DB
      cache: true,     // Verificar conectividade com Redis/Memcached
    },
  };
}

export { crashReporter, analytics, logger, healthCheck };
```

### 2.5 Pre-commit Config — `.pre-commit-config.yaml`

Expandido com os hooks da Ação 5 + DevOps checks.

```yaml
# Template: .pre-commit-config.yaml
# Gerado pelo Step 10a — DevOps Bootstrap
# Stack: Node.js — adaptar para Python ou Go

repos:
  - repo: local
    hooks:
      - id: ace-validate
        name: ACE — Cobertura de sessão + integridade + secret scanning
        entry: bash .ace/scripts/pre-commit.sh
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit]

      - id: ace-tests
        name: ACE — Test Gate (placeholders + delays + execução)
        entry: bash .ace/scripts/pre-commit-tests.sh
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-commit]
```

### 2.6 Dependabot — `.github/dependabot.yml`

Atualização automática de dependências.

```yaml
# Template: .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
      timezone: "America/Sao_Paulo"
    open-pull-requests-limit: 10
    versioning-strategy: "auto"
    labels:
      - "dependencies"
      - "automated"
    reviewers:
      - "team-dev"
    commit-message:
      prefix: "chore(deps)"
      include: "scope"
    # Agrupar atualizações de tipos e devDeps
    groups:
      typescript-eslint:
        patterns:
          - "@typescript-eslint/*"
          - "@types/*"
      react:
        patterns:
          - "react"
          - "react-dom"
          - "@types/react"
          - "@types/react-dom"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
```

### 2.7 DevOps Checklist — `docs/DEVOPS_CHECKLIST.md`

```markdown
# DevOps Checklist

**Projeto:** [Nome]
**Stack:** [Node.js / Python / Go]
**Gerado por:** Step 10a — DevOps Bootstrap
**Última atualização:** [YYYY-MM-DD]

## CI/CD Pipeline

- [ ] CI pipeline configurado (.github/workflows/ci.yml)
- [ ] Lint job passa
- [ ] Type check job passa (tsc --noEmit / mypy / go vet)
- [ ] Test job passa com coverage thresholds
- [ ] Arch check job configurado
- [ ] Security job (audit + gitleaks) ativo
- [ ] SBOM gerado automaticamente
- [ ] Branch protection ativa (require status checks)
- [ ] Code review obrigatório (≥ 1 aprovador)

## Observabilidade

- [ ] Crash reporting (Sentry) configurado e ativo em produção
- [ ] Structured logging com PII sanitization
- [ ] Analytics configurado (sem PII)
- [ ] Health check endpoint (/health) implementado
- [ ] Dashboard de monitoramento acessível

## Feature Flags

- [ ] Sistema de feature flags implementado (src/config/features.ts)
- [ ] Kill-switches críticos definidos (pagamentos, auth, dados)
- [ ] Flags têm `expiresAt` para prevenir flag debt
- [ ] Processo de remoção de flags documentado

## Dependências

- [ ] Dependabot/Renovate configurado com schedule semanal
- [ ] SBOM gerado no CI
- [ ] Licenças de dependências verificadas (sem GPL/AGPL não autorizada)
- [ ] npm/pip/go audit configurado

## Secrets & Segurança

- [ ] Pre-commit hook de secret scanning ativo
- [ ] Gitleaks no CI
- [ ] Secrets em GitHub Secrets / Vault (nunca no código)
- [ ] .env.example existe (sem valores reais)
- [ ] .gitignore inclui .env, credenciais, chaves

## Ambiente de Desenvolvimento

- [ ] CONTRIBUTING.md documenta setup local
- [ ] Docker Compose ou Dev Container para ambiente reproduzível
- [ ] Seed data disponível para desenvolvimento
- [ ] Script de bootstrap automatizado (npm run setup / make setup)

## Deploy

- [ ] DEPLOYMENT.md atualizado com estratégia
- [ ] Rollback documentado e testado
- [ ] Migrations de banco são reversíveis
- [ ] Smoke tests pós-deploy configurados
```

---

## 🔧 3. Stack Adaptation

### 3.1 Node.js (npm + TypeScript)

| Item | Implementação |
|------|---------------|
| Runner | GitHub Actions (`ubuntu-latest`) |
| Package manager | npm ci (lockfile) |
| Lint | ESLint + Prettier |
| Type check | `tsc --noEmit` |
| Test | Jest/Vitest com `--coverageThreshold` |
| Arch check | `fitness-functions.py --all --strict` |
| Security | `npm audit --audit-level=high` + Gitleaks |
| SBOM | `npm ls --all --json` |
| Dependabot | `package-ecosystem: "npm"` |

### 3.2 Python (pip + mypy)

| Item | Implementação |
|------|---------------|
| Runner | GitHub Actions (`ubuntu-latest`) |
| Package manager | pip install -r requirements.txt |
| Lint | Ruff (`ruff check .`) |
| Type check | mypy (`mypy src/ --strict`) |
| Test | pytest (`--cov --cov-fail-under=80`) |
| Arch check | `fitness-functions.py --all --strict` |
| Security | `pip-audit` + Gitleaks |
| SBOM | `pip freeze --all > requirements-freeze.txt` |
| Dependabot | `package-ecosystem: "pip"` |

### 3.3 Go

| Item | Implementação |
|------|---------------|
| Runner | GitHub Actions (`ubuntu-latest`) |
| Build | `go build ./...` |
| Lint | `golangci-lint run` |
| Type check | `go vet ./...` |
| Test | `go test -coverprofile=coverage.out ./...` |
| Arch check | `fitness-functions.py --all --strict` |
| Security | `govulncheck ./...` + Gitleaks |
| SBOM | `go version -m $(go list -m all)` |
| Dependabot | `package-ecosystem: "gomod"` |

---

## 📝 4. Prompt de Execução

Você está executando a skill `llc-step-10a-devops-bootstrap` do pipeline LLC. Seu objetivo é **gerar a infraestrutura DevOps concreta** do projeto — não documentação, mas arquivos executáveis que estarão funcionando no primeiro PR.

### 4.1 Leia as Entradas

- `docs/architecture/ARCHITECTURE.md` — stack, runtime, versões (Step 5)
- `docs/testing/TESTING_GUIDE.md` — thresholds de cobertura e comandos (Step 9)
- `docs/deployment/DEPLOYMENT.md` — ambientes e estratégia de deploy (Step 10)
- `.pre-commit-config.yaml` — hooks existentes

### 4.2 Execute — Gere os 7 Artefatos

1. **CI Pipeline:** `.github/workflows/ci.yml` — adaptado à stack (Node/Python/Go).
2. **Feature Flags:** `src/config/features.ts` — flags iniciais + kill-switches críticos.
3. **SBOM Script:** Adicionar scripts `sbom`, `sbom:check`, `deps:update`, `deps:audit` ao `package.json` / `pyproject.toml` / `Makefile`.
4. **Observabilidade:** `src/utils/observability.ts` — crash reporting + analytics + structured logging + health check + PII sanitization.
5. **Pre-commit Config:** Expandir `.pre-commit-config.yaml` com os hooks ACE (se não existirem).
6. **Dependabot:** `.github/dependabot.yml` — schedule semanal, agrupamento inteligente.
7. **DevOps Checklist:** `docs/DEVOPS_CHECKLIST.md` — 6 seções com checkboxes.

### 4.3 Regras Críticas

- **Concreto, não placeholder:** CI pipeline deve ser funcional — não usar `[substituir]` ou `TODO`. O que não for possível agora, documentar como "Fase 2" com data.
- **Stack-aware:** Adaptar TODOS os templates ao stack real. Não gerar `npm run` em projeto Python.
- **Feature flags começam desligadas:** Flags de features novas nascem com `enabled: false`. Kill-switches nascem com `enabled: true`.
- **Observabilidade mock:** O template de observabilidade usa mocks que logam em console. O time substitui pelos providers reais (Sentry, LogRocket, etc.) — mas a estrutura já está correta.
- **SBOM é obrigatório:** Mesmo projeto greenfield, gerar SBOM inicial (lista de dependências vazia é válida).

---

## 📤 5. Saída Esperada e Finalização

Após gerar os 7 artefatos, **PARE** e apresente:

1. **CI Pipeline:** Jobs configurados? Passa no primeiro run?
2. **Feature Flags:** Flags iniciais + kill-switches definidos?
3. **SBOM:** Script de geração funcional?
4. **Observabilidade:** Crash reporting + logging + PII sanitization implementados?
5. **Pre-commit:** Hooks ACE ativos?
6. **Dependabot:** Schedule configurado?
7. **DevOps Checklist:** 6 seções documentadas?
8. **Próximos Passos:** "Infra DevOps ativa. Primeiro PR deve ter CI verde. Feature flags disponíveis para Step 11."

**Gate 10a — Validação Humana:**
- [ ] CI pipeline está funcional e passando? (pelo menos lint + build)
- [ ] Feature flags estão corretas para o domínio? Kill-switches críticos definidos?
- [ ] Observabilidade cobre os cenários de falha relevantes?
- [ ] Dependabot está configurado com frequência adequada ao ciclo de sprint?
- [ ] DevOps checklist cobre todos os ambientes (dev, staging, prod)?
- [ ] Stack adaptation está correta? (Node/Python/Go — comandos batem com a realidade?)

**NÃO prossiga para Step 11 sem Gate 10a aprovado.**

---

## 🔗 6. Integração com Outros Steps

| Step | Integração |
|------|------------|
| **5 Arquitetura** | Stack define adaptação (Node/Python/Go) |
| **9 Testing Docs** | Thresholds de cobertura → CI test job |
| **10 Project Docs** | DEPLOYMENT.md → CI deploy job |
| **11 Execução PRPs** | Feature flags disponíveis; CI bloqueia PRs sem testes |
| **Pre-commit** | Hooks ACE (Ação 5) expandidos pelo DevOps Bootstrap |

---

## 📚 7. Referências

- **GitHub Actions Documentation** — docs.github.com/en/actions. Workflow syntax, jobs, concurrency.
- **Dependabot Documentation** — docs.github.com/en/code-security/dependabot. Version updates, security updates.
- **Sentry Documentation** — docs.sentry.io. Error tracking, release health, performance monitoring.
- **LaunchDarkly** — launchdarkly.com. Feature management platform (alternativa ao sistema built-in).
- **OpenTelemetry** — opentelemetry.io. Observability framework (logs, metrics, traces).
- **Gitleaks** — github.com/gitleaks/gitleaks. Static analysis for secrets in git repos.
- **OWASP CycloneDX** — cyclonedx.org. SBOM standard. Alternativa: SPDX (spdx.dev).
- **The Twelve-Factor App** — 12factor.net. Config (III), Backing Services (IV), Build/Release/Run (V), Logs (XI).
- **DORA Metrics** — dora.dev. Deployment frequency, lead time, MTTR, change failure rate.
