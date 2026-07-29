---
template_version: "1.0.0"
template_name: "MASTER_PROMPT_TEMPLATE.md"
last_updated: "{{TODAY}}"
generated_by: "llc-step-10 (Documentos do Projeto)"
ref: "Harness Preventivo LLC §2.7 — Ação 7 (Master Prompt Template)"
---

# Master Prompt — Cross-Cutting Harness (LLC)

**Propósito:** Consolidar as regras cross-cutting (segurança, arquitetura, clean code, TDD, DevOps) em 5 harness blocks que são injetados em **TODA sessão** de geração de código — em vez de depender do carregamento seletivo de cada skill.

**Como usar (Step 10):**
1. Preencha os placeholders `{{...}}` com os valores do projeto (stack, comandos).
2. Copie o bloco entre `<!-- MASTER_PROMPT:BEGIN -->` e `<!-- MASTER_PROMPT:END -->` para dentro do `AGENTS.md` gerado (placeholder `{{MASTER_PROMPT}}`).
3. Os blocks são **resumos executáveis** — o detalhe completo vive nas skills de origem (5d, 5a, 5c, 9a, 10a). Não carregue as skills inteiras em toda sessão; carregue este consolidado.

**Placeholders:**

| Placeholder | Descrição | Exemplo (Node) |
|-------------|-----------|----------------|
| `{{STACK}}` | Stack principal do projeto | `Node.js + NestJS + Prisma` |
| `{{LINT_CMD}}` | Comando de lint | `npm run lint` |
| `{{BUILD_CMD}}` | Comando de build/typecheck | `npm run build` (tsc --noEmit) |
| `{{ARCH_CHECK_CMD}}` | Verificação arquitetural | `python .ace/scripts/fitness-functions.py --all --strict` |
| `{{TEST_CMD}}` | Test runner | `npm test` |
| `{{COVERAGE_CMD}}` | Cobertura de testes | `npm test -- --coverage` |

---

<!-- MASTER_PROMPT:BEGIN -->

## Master Prompt — Regras Cross-Cutting ({{STACK}})

Estas regras se aplicam a **todo código gerado nesta sessão**, independente da task. Elas consolidam os hard gates das skills 5d (Secure-by-Design), 5a (Architecture Patterns), 5c (Clean Code), 9a (TDD Discipline) e 10a (DevOps Bootstrap).

### [SECURITY_HARNESS]

1. **Secrets:** NUNCA hardcode keys/secrets/tokens/passwords — derivar de env vars, secrets manager ou SecureStore/Keychain. (`--check-security: no-hardcoded-secrets`)
2. **SQL:** NUNCA interpolar valores em SQL (template literals/concat) — usar parâmetros `?`. (`--check-security: no-sql-injection`)
3. **PII:** NUNCA logar PII cru — usar `sanitizeForLogging()` antes de qualquer log/crash report.
4. **Auth:** NUNCA validar auth/entitlements apenas no client — o backend é a fonte de verdade. (`--check-security: no-client-only-auth`)
5. **Crypto:** NUNCA usar criptografia fraca (XOR, MD5, SHA1 para senhas, DES, AES-CBC) nem fallback fail-open — AES-256-GCM, IV único por operação, falhar fechado.

### [ARCHITECTURE_HARNESS]

1. **Layers:** Respeitar a Dependency Rule — `domain/` não importa nada de infraestrutura (Prisma, TypeORM, HTTP). (`--check-domain`)
2. **DI:** Depender de **interfaces** (DIP), nunca de implementações concretas de infra em services/use cases. (`--check-deps`)
3. **Screaming Architecture:** Package by component — a estrutura grita o domínio (`src/{modulo}/domain|application|infrastructure`), não o framework.
4. **Depth:** Módulos profundos — interface pequena, implementação encapsulada; sem métodos pass-through que só delegam. (`--check-deep-clean: no-pass-through`)
5. **ADR:** Decisão arquitetural nova (tabela, dependência, endpoint público, auth) exige ADR + escalação humana — o agente não é o arquiteto.

### [CLEAN_CODE_HARNESS]

1. **Tamanho:** Funções ≤ 20 linhas efetivas (core), classes ≤ 100 — extrair antes de crescer. (`--check-functions`, `--check-classes`)
2. **CQS:** Command (create/update/delete) com side effect não retorna dados — separar command de query. (`--check-deep-clean: no-cqs-violation`)
3. **DRY:** Não duplicar lógica — na 2ª ocorrência, extrair para função/módulo compartilhado.
4. **Null:** NUNCA `return null` em services/repositories — `Result<T,E>`, `Optional<T>` ou throw descritivo. (`--check-deep-clean: no-null-return`)
5. **Nomes:** Sem nomes genéricos (`data`, `info`, `obj`, `temp`, `result`) — nomes revelam intenção de domínio. (`--check-naming`)
6. **Params:** ≤ 3 parâmetros por função; sem flag boolean em método público — dividir em dois métodos. (`--check-deep-clean: no-flag-arguments`)
7. **Data Clump:** 3+ campos que andam juntos em 5+ assinaturas viram Value Object. (`--check-deep-clean: no-data-clump`)
8. **Comentários:** Código auto-explicativo — sem comentários ruído/redundantes; comentário só para "porquê", nunca "o quê". (`--check-smells`)

### [TDD_HARNESS]

1. **RED-GREEN-REFACTOR:** Teste falhando ANTES do código de produção — mostrar o output do teste em ambas as fases. Violou? Delete a implementação e recomece pelo teste.
2. **Placeholders:** NUNCA `expect(true).toBe(true)` ou `it()` vazio — todo teste tem asserção real. (pre-commit `ace-tests`)
3. **Delays:** NUNCA `setTimeout`/`sleep` em testes — usar `waitFor()`, `findBy*`. (pre-commit `ace-tests`)
4. **Mocks:** Mockar por contrato (Test Data Builder, Constructor Injection), nunca por implementação (ex.: roteamento por SQL string).
5. **F.I.R.S.T.:** Todo teste é Fast, Independent (sem ordem), Repeatable, Self-validating, Timely.

### [DEVOPS_HARNESS]

1. **CI verde:** NUNCA mergear com CI quebrado — corrigir ou reverter, sem `skip`.
2. **Feature flags:** Feature arriscada nasce atrás de flag com kill-switch (`src/config/features.ts`).
3. **Breadcrumbs:** Toda operação crítica emite observabilidade — crash reporting + logging estruturado com PII sanitizada.
4. **Secrets:** Secrets só via env/secret manager — secret scanning no pre-commit é bloqueante (`pre-commit.sh` passo #8).
5. **Audit:** Dependências auditadas (npm audit/Dependabot) e SBOM gerado no CI — vulnerabilidade critical bloqueia.

### ✅ Gates Obrigatórios (antes de considerar código "pronto")

Nenhuma task é reportada como concluída sem TODOS os gates abaixo limpos:

```
{{LINT_CMD}}         limpo
{{BUILD_CMD}}        limpo
{{ARCH_CHECK_CMD}}   0 violações
{{TEST_CMD}}         passando (sem placeholders)
{{COVERAGE_CMD}}     coverage não regrediu
```

Se qualquer gate falhar: **PARE**, reporte o output cru ao operador e aguarde decisão (RULE 0).

<!-- MASTER_PROMPT:END -->

---

## Adaptação por Stack

Os comandos dos gates adaptam-se ao stack detectado (mesma matriz do Step 10a — DevOps Bootstrap):

| Gate | Node | Python | Go |
|------|------|--------|-----|
| Lint | `npm run lint` | `ruff check .` | `golangci-lint run` |
| Build | `npm run build` / `tsc --noEmit` | `mypy .` | `go build ./...` |
| Arch check | `fitness-functions.py --all --strict` | idem | idem |
| Test | `npm test` | `pytest -q` | `go test ./...` |
| Coverage | `npm test -- --coverage` | `pytest --cov` | `go test -cover ./...` |
| Audit | `npm audit` | `pip-audit` | `govulncheck ./...` |

## Rastreabilidade dos Blocks

| Block | Skill de origem | Enforcement automático |
|-------|----------------|------------------------|
| SECURITY_HARNESS | `llc-step-5d-secure-by-design` | `fitness-functions.py --check-security` + `pre-commit.sh` (secret scanning) |
| ARCHITECTURE_HARNESS | `llc-step-5a-architecture-patterns` | `fitness-functions.py --check-deps/--check-domain` |
| CLEAN_CODE_HARNESS | `llc-step-5c-clean-code` | `fitness-functions.py --check-functions/--check-deep-clean` |
| TDD_HARNESS | `llc-step-9a-tdd-discipline` | `pre-commit-tests.sh` (placeholders, delays, execução) |
| DEVOPS_HARNESS | `llc-step-10a-devops-bootstrap` | CI pipeline gerado (`.github/workflows/ci.yml`) |

> **Prevenção > Detecção:** estes blocks previnem na geração; as fitness functions e pre-commit hooks detectam o que passar. As duas camadas são complementares — nenhuma substitui a outra.
