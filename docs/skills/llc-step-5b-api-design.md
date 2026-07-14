---
name: llc-step-5b-api-design
description: Pipeline LLC Step 5b — API Design Enforcement baseado no processo ADD-R (Higginbotham). Valida REST semantics, naming consistency, pagination, OpenAPI spec, HATEOAS, versioning, security schemes. Executa fitness functions automatizadas (--check-api-design).
version: 1.0.0
tags: [api-design, rest, add-r, openapi, pagination, hateoas, versioning, security, llc-pipeline]
---

# LLC Skill: Step 5b — API Design Enforcement

**Pipeline:** Live and Let Code (LLC)
**Fase:** Architecture (sub-step of Step 5 — after Step 5a Architecture Patterns)
**Depende de:** Step 5a (Architecture Patterns validados)
**Executa antes de:** Step 6 (Tasks) e Step 8 (Setup + Mock)
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-5b` ou "Execute a skill llc-step-5b-api-design".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 5b --task "Enforcar API Design ADD-R"`.

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — overview arquitetural (Step 5)
- [ ] `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` — padrões arquiteturais (Step 5a)
- [ ] `docs/business/specs/requisitos_nao_funcionais.md` — RNFs de API (latência, versioning, etc.)
- [ ] `docs/planning/PLAN.md` — módulos core e ondas (para enforcement block)
- [ ] `docs/templates/CONTROLLER_TEMPLATE.ts` — template base para controllers
- [ ] `.ace/arch-config.yaml` — configuração de fitness functions (módulos core, thresholds)

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 5b** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-5b.md`:
     ```markdown
     # Skip Note: Step 5b — API Design Enforcement
     **Decisão:** Step pulado — design de API inalterado desde última execução.
     **Gate:** ✅ Auto-aprovado (reaproveitando aprovação anterior de {data})
     ```
   - **PARE** e informe: "Step 5b pulado via Smart Skip. Design de API existente reaproveitado. Gate auto-aprovado."
3. Se **Step 5b** estiver listado como "executar": atualize `docs/api/openapi.yaml`, controllers e `.ace/arch-config.yaml` apenas nas seções alteradas, mantendo histórico de decisões.
4. Se DELTA_REPORT.md não existir: prossiga normalmente.

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-5b-api-design` do pipeline LLC. Seu objetivo é **enforcar o design de API** seguindo o processo ADD-R (Align, Define, Design, Refine) de James Higginbotham ("Principles of Web API Design") e as convenções REST modernas. As regras definidas aqui são **vinculantes** e serão verificadas por fitness functions automatizadas (`fitness-functions.py --check-api-design`).

### 1. Leia as Entradas (Align)

- `docs/architecture/ARCHITECTURE.md` — módulos, responsabilidades, C4 context diagram
- `docs/business/specs/requisitos_funcionais.md` — casos de uso que viram endpoints
- `docs/business/specs/perfis_permissoes.md` — RBAC/ABAC para security schemes
- `docs/planning/PLAN.md` — identifique módulos core (wave 1) que terão enforcement `block`
- `docs/templates/CONTROLLER_TEMPLATE.ts` — template base de controller a customizar
- `.ace/arch-config.yaml` — regras de API design ativas (ver seção "Fitness Functions")

### 2. Execute ADD-R (Define → Design → Refine)

#### 2.1 Align — Valide alinhamento domínio-API

Para cada módulo identificado no Step 0.5 + Step 5a:
- [ ] Recursos (resources) são substantivos de domínio (não verbos)
- [ ] Agregados raiz têm endpoints próprios; sub-recursos são nested
- [ ] Operações mapeiam para casos de uso (use cases) do Step 5a
- [ ] Status codes de domínio (ex: `EM_EXECUCAO`, `CONCLUIDA`) mantidos em português se domínio assim exigir

#### 2.2 Define — Defina contratos por recurso

Para cada recurso (ex: `auditorias`, `achados`, `planos`):
| Item | Decisão |
|------|---------|
| Base path | `api/v1/{recurso}` (kebab-case, versionado) |
| Sub-recursos | `/:id/{sub-recurso}` (ex: `/auditorias/:id/achados`) |
| Coleção | `GET /api/v1/recursos?page=1&limit=20&search=...` |
| Item único | `GET /api/v1/recursos/:id` |
| Criação | `POST /api/v1/recursos` |
| Substituição total | `PUT /api/v1/recursos/:id` (idempotente) |
| Atualização parcial | `PATCH /api/v1/recursos/:id` |
| Exclusão | `DELETE /api/v1/recursos/:id` (204 No Content) |
| Transições de status | **NÃO** `POST /:id/concluir` — usar `PATCH /:id { status: "CONCLUIDA", motivo?: string }` |

#### 2.3 Design — Gere artefatos

**A. OpenAPI Spec (`docs/api/openapi.yaml`)**
```yaml
openapi: 3.0.3
info:
  title: {Projeto} API
  version: 1.0.0
servers:
  - url: https://api.{dominio}.com/api/v1
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    # DTOs de request/response por recurso
    CreateAuditoriaDto: ...
    AuditoriaReadModel: ...
    PaginatedResponse: ...
paths:
  /auditorias:
    get:
      summary: Listar auditorias
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
        - $ref: '#/components/parameters/SearchParam'
      responses:
        '200': { description: OK, content: { application/json: { schema: { $ref: '#/components/schemas/PaginatedAuditoriaResponse' } } } }
        '401': { $ref: '#/components/responses/Unauthorized' }
        '403': { $ref: '#/components/responses/Forbidden' }
        '422': { $ref: '#/components/responses/ValidationError' }
      security:
        - BearerAuth: []
    post:
      summary: Criar auditoria
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CreateAuditoriaDto' }
      responses:
        '201': { description: Created, content: { application/json: { schema: { $ref: '#/components/schemas/AuditoriaReadModel' } } } }
        '401': { $ref: '#/components/responses/Unauthorized' }
        '403': { $ref: '#/components/responses/Forbidden' }
        '422': { $ref: '#/components/responses/ValidationError' }
      security:
        - BearerAuth: []
  /auditorias/{id}:
    get:
      summary: Obter auditoria por ID
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '200': { description: OK, content: { application/json: { schema: { allOf: [{ $ref: '#/components/schemas/AuditoriaReadModel' }, { type: object, properties: { _links: { type: object } } }] } } } }
        '401': { $ref: '#/components/responses/Unauthorized' }
        '403': { $ref: '#/components/responses/Forbidden' }
        '404': { $ref: '#/components/responses/NotFound' }
      security:
        - BearerAuth: []
    patch:
      summary: Atualizar auditoria (parcial ou status)
      parameters:
        - $ref: '#/components/parameters/IdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/UpdateAuditoriaDto' }
      responses:
        '200': { description: OK, content: { application/json: { schema: { $ref: '#/components/schemas/AuditoriaReadModel' } } } }
        '401': { $ref: '#/components/responses/Unauthorized' }
        '403': { $ref: '#/components/responses/Forbidden' }
        '404': { $ref: '#/components/responses/NotFound' }
        '422': { $ref: '#/components/responses/ValidationError' }
      security:
        - BearerAuth: []
    delete:
      summary: Excluir auditoria
      parameters:
        - $ref: '#/components/parameters/IdParam'
      responses:
        '204': { description: No Content }
        '401': { $ref: '#/components/responses/Unauthorized' }
        '403': { $ref: '#/components/responses/Forbidden' }
        '404': { $ref: '#/components/responses/NotFound' }
      security:
        - BearerAuth: []
  /auditorias/{id}/achados:
    get:
      summary: Listar achados de uma auditoria
      parameters:
        - $ref: '#/components/parameters/IdParam'
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/LimitParam'
      responses:
        '200': { description: OK, content: { application/json: { schema: { $ref: '#/components/schemas/PaginatedAchadoResponse' } } } }
        '401': { $ref: '#/components/responses/Unauthorized' }
        '403': { $ref: '#/components/responses/Forbidden' }
        '404': { $ref: '#/components/responses/NotFound' }
        '422': { $ref: '#/components/responses/ValidationError' }
      security:
        - BearerAuth: []
```

**B. Controllers NestJS (atualize/genere por módulo)**
Use `docs/templates/CONTROLLER_TEMPLATE.ts` como base. Para cada módulo:
- Aplique `@Controller('api/v1/{recurso}')`
- Adicione `@HttpCode` explícito em **todos** endpoints
- Adicione `@ApiResponse` para 401, 403, 404, 422
- Use `@Query('page') page = 1, @Query('limit') limit = 20` (camelCase)
- Retorne envelope de paginação: `{ data, total, page, limit, totalPages, _links }`
- Inclua `_links` (HATEOAS) em respostas de item único

**C. Fitness Functions Config (`.ace/arch-config.yaml`)**
Atualize/adicionar na seção `checks`:
```yaml
checks:
  # API Design Checks (Higginbotham ADD-R)
  naming_consistency:
    enabled: true
    mode: hybrid
    block_for: core_modules
  rest_semantics_put_patch:
    enabled: true
    mode: hybrid
    block_for: core_modules
  rpc_endpoints:
    enabled: true
    mode: block
  nested_resources:
    enabled: true
    mode: warn
  duplicate_resources:
    enabled: true
    mode: hybrid
    block_for: core_modules
  http_status_codes:
    enabled: true
    mode: warn
  api_response_errors:
    enabled: true
    mode: warn
  pagination_coverage:
    enabled: true
    mode: hybrid
    block_for: core_modules
  pagination_envelope:
    enabled: true
    mode: warn
  versioning:
    enabled: true
    mode: warn
  openapi_documentation:
    enabled: true
    mode: block
  openapi_security:
    enabled: true
    mode: block
  hateoas_links:
    enabled: true
    mode: warn
```

#### 2.4 Refine — Execute validação automatizada

```bash
# Executa todos os 13 checks de API Design
python .ace/scripts/fitness-functions.py --check-api-design --verbose

# Ou checks individuais:
python .ace/scripts/fitness-functions.py --check-naming-consistency --check-rpc-endpoints --check-rest-semantics --check-pagination --check-openapi --check-hateoas --verbose
```

**Critérios de aprovação (Gate 8):**
- ✅ 0 bloqueios (`mode: block` ou `hybrid` em core_modules)
- ✅ OpenAPI spec válida em `docs/api/openapi.yaml`
- ✅ Controllers seguem template padronizado
- ✅ Endpoints RPC migrados para PATCH { status }
- ✅ Paginação em todos os endpoints de lista
- ✅ Versioning `api/v1/` em todos controllers
- ✅ BearerAuth definido e aplicado no OpenAPI

### 3. Artefatos Gerados/Atualizados

- `docs/api/openapi.yaml` — OpenAPI 3.0 spec completa
- `docs/templates/CONTROLLER_TEMPLATE.ts` — Template customizado (se houver especificidades do projeto)
- Controllers NestJS em `src/{modulo}/{modulo}.controller.ts` — atualizados
- `.ace/arch-config.yaml` — Regras de API design ativadas
- `docs/architecture/adr/ADR-012-api-design.md` — ADR documentando decisões de API Design (opcional mas recomendado)

---

## ✅ Checklist de Validação (Gate 8)

Você valida — **Gate 8 (após Step 5b)**:

- [ ] `docs/api/openapi.yaml` existe, é YAML válido e tem `paths`, `components.schemas`, `components.securitySchemes.BearerAuth`
- [ ] Todos os controllers em `src/*/*.controller.ts`:
  - [ ] `@Controller('api/v1/...')` com versioning
  - [ ] `@HttpCode` explícito em todos endpoints
  - [ ] `@ApiResponse` para 401, 403, 404, 422
  - [ ] `@Query('page')`, `@Query('limit')` camelCase
  - [ ] Retorno de lista usa envelope `{ data, total, page, limit, totalPages, _links }`
  - [ ] Resposta de item único inclui `_links` (HATEOAS)
- [ ] Zero endpoints RPC (`POST /:id/concluir`, `/suspender`, `/iniciar`, etc.) — migrados para `PATCH { status }`
- [ ] `PUT` usado **apenas** para substituição total (idempotente); `PATCH` para parcial
- [ ] Recursos aninhados modelados como paths (`/auditorias/:id/achados` não `?auditoriaId=`)
- [ ] Fitness functions `python .ace/scripts/fitness-functions.py --check-api-design --strict` passa com 0 bloqueios

**Só avance quando aprovar.**

---

## 📚 Referências

- **Principles of Web API Design** — James Higginbotham (processo ADD-R, ch. 3-6)
- **RESTful Web APIs** — Leonard Richardson & Mike Amundsen (HATEOAS, hypermedia)
- **NestJS OpenAPI (Swagger) Module** — `@nestjs/swagger` decorators
- **Fitness Functions** — Ingeno, "Software Architect's Handbook", ch. 16