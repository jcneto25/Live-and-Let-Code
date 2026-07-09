---
name: llc-step-5b-api-design
description: LLC Pipeline Step 5b — API Design Enforcement based on ADD-R process (Higginbotham). Validates REST semantics, naming consistency, pagination, OpenAPI spec, HATEOAS, versioning, security schemes. Runs automated fitness functions (--check-api-design).
version: 1.0.0
tags: [api-design, rest, add-r, openapi, pagination, hateoas, versioning, security, llc-pipeline]
---

# LLC Skill: Step 5b — API Design Enforcement

**Pipeline:** Live and Let Code (LLC)
**Phase:** Architecture (sub-step of Step 5 — after Step 5a Architecture Patterns)
**Depends on:** Step 5a (Architecture Patterns validated)
**Executes before:** Step 6 (Tasks) and Step 8 (Setup + Mock)
**Maintainer:** LLC Team

## 🛠️ How to Use This Skill

1. Place this file in `.claude/skills/` or the project's `docs/skills/` folder.
2. Invoke in chat using: `@llc-step-5b` or "Execute skill llc-step-5b-api-design".
3. Via Thin Harness (recommended): `python .ace/scripts/llc.py run --step 5b --task "Enforce API Design ADD-R"`.

## 📋 Prerequisites

- [ ] `docs/architecture/ARCHITECTURE.md` — architectural overview (Step 5)
- [ ] `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` — architectural patterns (Step 5a)
- [ ] `docs/business/specs/requisitos_nao_funcionais.md` — API NFRs (latency, versioning, etc.)
- [ ] `docs/planning/PLAN.md` — core modules and waves (for enforcement block)
- [ ] `docs/templates/CONTROLLER_TEMPLATE.ts` — base controller template
- [ ] `.ace/arch-config.yaml` — fitness function configuration (core modules, thresholds)

---

## 🔄 Delta Mode — Smart Skip Check

**If `docs/planning/DELTA_REPORT.md` exists and is approved (Gate Δ.0):**

1. Read section §5.2 (Steps to Skip) of DELTA_REPORT.md.
2. If **Step 5b** is listed as "skip":
   - Generate skip note in `docs/delta/skip-notes/step-5b.md`:
     ```markdown
     # Skip Note: Step 5b — API Design Enforcement
     **Decision:** Step skipped — API design unchanged since last execution.
     **Gate:** ✅ Auto-approved (reusing previous approval from {date})
     ```
   - **STOP** and report: "Step 5b skipped via Smart Skip. Existing API design reused. Gate auto-approved."
3. If **Step 5b** is listed as "execute": update `docs/api/openapi.yaml`, controllers, and `.ace/arch-config.yaml` only in changed sections, preserving decision history.
4. If DELTA_REPORT.md doesn't exist: proceed normally.

---

## 🎯 EXECUTION PROMPT

You are executing the skill `llc-step-5b-api-design` of the LLC pipeline. Your goal is to **enforce API design** following the ADD-R process (Align, Define, Design, Refine) by James Higginbotham ("Principles of Web API Design") and modern REST conventions. The rules defined here are **binding** and will be verified by automated fitness functions (`fitness-functions.py --check-api-design`).

### 1. Read Inputs (Align)

- `docs/architecture/ARCHITECTURE.md` — modules, responsibilities, C4 context diagram
- `docs/business/specs/requisitos_funcionais.md` — use cases that become endpoints
- `docs/business/specs/perfis_permissoes.md` — RBAC/ABAC for security schemes
- `docs/planning/PLAN.md` — identify core modules (wave 1) with `block` enforcement
- `docs/templates/CONTROLLER_TEMPLATE.ts` — base controller template to customize
- `.ace/arch-config.yaml` — active API design rules (see "Fitness Functions" section)

### 2. Execute ADD-R (Define → Design → Refine)

#### 2.1 Align — Validate Domain-API Alignment

For each module identified in Step 0.5 + Step 5a:
- [ ] Resources are domain nouns (not verbs)
- [ ] Aggregate roots have their own endpoints; sub-resources are nested
- [ ] Operations map to use cases from Step 5a
- [ ] Domain status codes (e.g., `EM_EXECUCAO`, `CONCLUIDA`) kept in Portuguese if domain requires

#### 2.2 Define — Define Contracts per Resource

For each resource (e.g., `auditorias`, `achados`, `planos`):
| Item | Decision |
|------|----------|
| Base path | `api/v1/{resource}` (kebab-case, versioned) |
| Sub-resources | `/:id/{sub-resource}` (e.g., `/auditorias/:id/achados`) |
| Collection | `GET /api/v1/resources?page=1&limit=20&search=...` |
| Single item | `GET /api/v1/resources/:id` |
| Creation | `POST /api/v1/resources` |
| Full replacement | `PUT /api/v1/resources/:id` (idempotent) |
| Partial update | `PATCH /api/v1/resources/:id` |
| Deletion | `DELETE /api/v1/resources/:id` (204 No Content) |
| Status transitions | **NOT** `POST /:id/conclude` — use `PATCH /:id { status: "CONCLUDED", reason?: string }` |

#### 2.3 Design — Generate Artifacts

**A. OpenAPI Spec (`docs/api/openapi.yaml`)**
```yaml
openapi: 3.0.3
info:
  title: {Project} API
  version: 1.0.0
servers:
  - url: https://api.{domain}.com/api/v1
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    # Request/Response DTOs per resource
    CreateAuditoriaDto: ...
    AuditoriaReadModel: ...
    PaginatedResponse: ...
paths:
  /auditorias:
    get:
      summary: List auditorias
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
      summary: Create auditoria
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
      summary: Get auditoria by ID
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
      summary: Update auditoria (partial or status)
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
      summary: Delete auditoria
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
      summary: List achados for an auditoria
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

**B. NestJS Controllers (update/generate per module)**
Use `docs/templates/CONTROLLER_TEMPLATE.ts` as base. For each module:
- Apply `@Controller('api/v1/{resource}')`
- Add explicit `@HttpCode` on **all** endpoints
- Add `@ApiResponse` for 401, 403, 404, 422
- Use `@Query('page') page = 1, @Query('limit') limit = 20` (camelCase)
- Return pagination envelope: `{ data, total, page, limit, totalPages, _links }`
- Include `_links` (HATEOAS) in single-item responses

**C. Fitness Functions Config (`.ace/arch-config.yaml`)**
Update/add in the `checks` section:
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

#### 2.4 Refine — Run Automated Validation

```bash
# Run all 13 API Design checks
python .ace/scripts/fitness-functions.py --check-api-design --verbose

# Or individual checks:
python .ace/scripts/fitness-functions.py --check-naming-consistency --check-rpc-endpoints --check-rest-semantics --check-pagination --check-openapi --check-hateoas --verbose
```

**Approval Criteria (Gate 8):**
- ✅ 0 blocks (`mode: block` or `hybrid` on core_modules)
- ✅ Valid OpenAPI spec at `docs/api/openapi.yaml`
- ✅ Controllers follow standardized template
- ✅ RPC endpoints migrated to PATCH { status }
- ✅ Pagination on all list endpoints
- ✅ Versioning `api/v1/` on all controllers
- ✅ BearerAuth defined and applied in OpenAPI

### 3. Artifacts Generated/Updated

- `docs/api/openapi.yaml` — Complete OpenAPI 3.0 spec
- `docs/templates/CONTROLLER_TEMPLATE.ts` — Customized template (if project-specific)
- NestJS Controllers in `src/{module}/{module}.controller.ts` — updated
- `.ace/arch-config.yaml` — API design rules activated
- `docs/architecture/adr/ADR-012-api-design.md` — ADR documenting API Design decisions (optional but recommended)

---

## ✅ Validation Checklist (Gate 8)

You validate — **Gate 8 (after Step 5b)**:

- [ ] `docs/api/openapi.yaml` exists, is valid YAML, and has `paths`, `components.schemas`, `components.securitySchemes.BearerAuth`
- [ ] All controllers in `src/*/*.controller.ts`:
  - [ ] `@Controller('api/v1/...')` with versioning
  - [ ] Explicit `@HttpCode` on all endpoints
  - [ ] `@ApiResponse` for 401, 403, 404, 422
  - [ ] `@Query('page')`, `@Query('limit')` camelCase
  - [ ] List response uses envelope `{ data, total, page, limit, totalPages, _links }`
  - [ ] Single-item response includes `_links` (HATEOAS)
- [ ] Zero RPC endpoints (`POST /:id/conclude`, `/suspend`, `/start`, etc.) — migrated to `PATCH { status }`
- [ ] `PUT` used **only** for full replacement (idempotent); `PATCH` for partial
- [ ] Nested resources modeled as paths (`/auditorias/:id/achados` not `?auditoriaId=`)
- [ ] Fitness functions `python .ace/scripts/fitness-functions.py --check-api-design --strict` passes with 0 blocks

**Only proceed when approved.**

---

## 📚 References

- **Principles of Web API Design** — James Higginbotham (ADD-R process, ch. 3-6)
- **RESTful Web APIs** — Leonard Richardson & Mike Amundsen (HATEOAS, hypermedia)
- **NestJS OpenAPI (Swagger) Module** — `@nestjs/swagger` decorators
- **Fitness Functions** — Ingeno, "Software Architect's Handbook", ch. 16