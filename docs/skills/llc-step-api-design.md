---
name: llc-step-api-design
description: Pipeline LLC Step — API Design (ADD-R + REST + OpenAPI). Define contracts, resource modeling, REST conventions, pagination, error handling antes da implementação. Gera OpenAPI spec vinculante.
version: 1.0.0
tags: [api-design, rest, openapi, add-r, llc-pipeline, web-api]
---

# LLC Skill: API Design (ADD-R + REST)

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Architecture/Design (sub-step de Step 5a / Step 10 / Step 11a)  
**Depende de:** Step 5a (Architecture Patterns)  
**Executa antes de:** Step 11 (Execution)  
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-api-design` ou "Execute a skill llc-step-api-design".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step api-design --task "Definir API contracts"`.

---

## 📋 PRÉ-REQUISITOS

- [ ] `docs/architecture/ARCHITECTURE.md` — visão arquitetural (Step 5)
- [ ] `docs/planning/PLAN.md` — ondas e módulos core
- [ ] `docs/business/specs/requisitos_nao_funcionais.md` — RNFs (performance, segurança)
- [ ] `.ace/arch-config.yaml` — módulos core para enforcement block

---

## 🔄 MODO DELTA — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step api-design** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-api-design.md`:
     ```markdown
     # Skip Note: Step api-design — API Design
     **Decisão:** Step pulado — API contracts inalterados desde última execução.
     **Gate:** ✅ Auto-aprovado (reaproveitando aprovação anterior de {data})
     ```
   - **PARE** e informe: "Step api-design pulado via Smart Skip. API contracts existentes reaproveitados. Gate auto-aprovado."
3. Se **Step api-design** estiver listado como "executar": atualize apenas seções alteradas, mantendo histórico de decisões (ADRs).
4. Se DELTA_REPORT.md não existir: prossiga normalmente.

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-api-design` do pipeline LLC. Seu objetivo é **definir e documentar os contracts de API** que o time (e LLM) deve seguir durante toda a execução (Steps 8–11). Estes contracts são **vinculantes** e serão verificados por fitness functions automatizadas.

### 1. Leia as Entradas

- `docs/architecture/ARCHITECTURE.md` — stack, C4, ADRs
- `docs/planning/PLAN.md` — identifique módulos core (wave 1)
- `docs/business/specs/requisitos_nao_funcionais.md` — RNFs
- `docs/architecture/adr/` — ADRs existentes (especialmente API-related)

### 2. Execute o Processo ADD-R (Higginbotham)

#### 2.1 ALIGN — Alinhar Stakeholders

Documente em `docs/api/ALIGN.md`:

| Questão | Resposta |
|---------|----------|
| Consumidores da API? | (ex: Frontend React, Mobile, Integrações B2B) |
| Estilo preferido? | REST (recomendado) / GraphQL / gRPC |
| Versioning strategy? | URL path `/api/v1/` + header `Accept-Version` |
| Idioma dos recursos? | PT-BR (domínio) / EN (técnico) — documentar decisão |
| Auth padrão? | JWT Bearer + RBAC |
| Rate limiting? | 60 req/min global, 10 req/min auth |

#### 2.2 DEFINE — Definir Capabilities

Para cada **módulo core** identificado no PLAN.md, crie em `docs/api/DEFINE/{modulo}.md`:

```markdown
# {Módulo} — API Capabilities

## Recursos (Resources)
| Recurso | Path | Descrição | Aggregate Root? |
|---------|------|-----------|-----------------|
| Auditoria | `/auditorias` | Gestão de auditorias | Sim |
| Achado | `/auditorias/:auditoriaId/achados` | Achados de uma auditoria | Não (nested) |

## Operações por Recurso
| Recurso | GET (list) | GET (one) | POST | PATCH | DELETE |
|---------|------------|-----------|------|-------|--------|
| Auditoria | ✅ | ✅ | ✅ | ✅ | ✅ |
| Achado | ✅ (nested) | ✅ | ✅ | ✅ | ✅ |

## Fluxos de Estado (Status Codes de Domínio)
| Recurso | Estados | Transições Válidas |
|---------|---------|-------------------|
| Auditoria | ABERTA → EM_EXECUCAO → CONCLUIDA/SUSPENSA | Documentar matriz |

## Regras de Negócio Críticas (para validação 422)
- Auditoria só pode iniciar se status = ABERTA
- Plano deve estar APROVADO para criar auditoria
```

#### 2.3 DESIGN — Design Detalhado (OpenAPI Spec)

Gere **`docs/api/openapi.yaml`** (ou `.json`) com spec completa:

```yaml
openapi: 3.0.3
info:
  title: CONFORMITAS API
  version: 1.0.0
  description: |
    API para gestão de auditorias, planos, achados.
    Status codes de domínio em PT-BR (intencional).
servers:
  - url: https://api.conformitas.local/api/v1
    description: Development
security:
  - BearerAuth: []
paths:
  /auditorias:
    get:
      summary: Listar auditorias
      operationId: listAuditorias
      tags: [Auditorias]
      security: [{ BearerAuth: [] }]
      parameters:
        - $ref: '#/components/parameters/page'
        - $ref: '#/components/parameters/limit'
        - name: status
          in: query
          schema: { type: string, enum: [ABERTA, EM_EXECUCAO, CONCLUIDA, SUSPENSA] }
      responses:
        '200':
          description: Lista paginada
          content:
            application/json:
              schema: { $ref: '#/components/schemas/PaginatedAuditoriaResponse' }
        '401': { $ref: '#/components/responses/Unauthorized' }
        '403': { $ref: '#/components/responses/Forbidden' }
    post:
      summary: Criar auditoria
      operationId: createAuditoria
      tags: [Auditorias]
      security: [{ BearerAuth: [] }]
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CreateAuditoriaRequest' }
      responses:
        '201': { description: Criada, $ref: '#/components/schemas/AuditoriaResponse' }
        '422': { $ref: '#/components/responses/ValidationError' }
  /auditorias/{id}:
    get:
      summary: Buscar auditoria por ID
      operationId: getAuditoria
      tags: [Auditorias]
      parameters:
        - $ref: '#/components/parameters/auditoriaId'
      responses:
        '200': { $ref: '#/components/schemas/AuditoriaResponse' }
        '404': { $ref: '#/components/responses/NotFound' }
    patch:
      summary: Atualizar auditoria (parcial)
      operationId: updateAuditoria
      requestBody:
        content:
          application/json:
            schema: { $ref: '#/components/schemas/UpdateAuditoriaRequest' }
      responses:
        '200': { $ref: '#/components/schemas/AuditoriaResponse' }
        '404': { $ref: '#/components/responses/NotFound' }
    delete:
      summary: Excluir auditoria
      operationId: deleteAuditoria
      responses:
        '204': { description: Excluída }
        '404': { $ref: '#/components/responses/NotFound' }
  /auditorias/{auditoriaId}/achados:
    get:
      summary: Listar achados de uma auditoria
      operationId: listAchadosByAuditoria
      parameters:
        - $ref: '#/components/parameters/auditoriaId'
        - $ref: '#/components/parameters/page'
        - $ref: '#/components/parameters/limit'
      responses:
        '200':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/PaginatedAchadoResponse' }
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  parameters:
    page:
      name: page
      in: query
      schema: { type: integer, default: 1, minimum: 1 }
    limit:
      name: limit
      in: query
      schema: { type: integer, default: 20, maximum: 100 }
    auditoriaId:
      name: auditoriaId
      in: path
      required: true
      schema: { type: string, format: uuid }
  responses:
    Unauthorized:
      description: Token inválido ou expirado
      content:
        application/json:
          schema: { $ref: '#/components/schemas/ErrorResponse' }
    Forbidden:
      description: Permissão insuficiente
      content:
        application/json:
          schema: { $ref: '#/components/schemas/ErrorResponse' }
    NotFound:
      description: Recurso não encontrado
      content:
        application/json:
          schema: { $ref: '#/components/schemas/ErrorResponse' }
    ValidationError:
      description: Erro de validação (422)
      content:
        application/json:
          schema: { $ref: '#/components/schemas/ValidationErrorResponse' }
  schemas:
    # === Envelope Padrão ===
    PaginatedResponse:
      type: object
      properties:
        data:
          type: array
          items: {}
        total:
          type: integer
        page:
          type: integer
        limit:
          type: integer
        totalPages:
          type: integer
    ErrorResponse:
      type: object
      properties:
        statusCode: { type: integer }
        timestamp: { type: string, format: date-time }
        path: { type: string }
        code: { type: string }
        message: { type: string }
        details: { type: object }
    ValidationErrorResponse:
      allOf:
        - $ref: '#/components/schemas/ErrorResponse'
        - type: object
          properties:
            details:
              type: array
              items:
                type: object
                properties:
                  field: { type: string }
                  message: { type: string }
    # === Domain Schemas ===
    AuditoriaResponse:
      type: object
      properties:
        id: { type: string, format: uuid }
        numero: { type: string }
        status: { type: string, enum: [ABERTA, EM_EXECUCAO, CONCLUIDA, SUSPENSA] }
        unidadeAuditada: { type: string }
        objetivo: { type: string }
        createdAt: { type: string, format: date-time }
        updatedAt: { type: string, format: date-time }
    CreateAuditoriaRequest:
      type: object
      required: [itemPlanoId, tipo, unidadeAuditada, objetivo]
      properties:
        itemPlanoId: { type: string, format: uuid }
        tipo: { type: string, enum: [CONFORMIDADE, DESEMPENHO, ESPECIAL] }
        unidadeAuditada: { type: string }
        objetivo: { type: string }
        escopo: { type: string }
        dataFimPrevista: { type: string, format: date }
    UpdateAuditoriaRequest:
      type: object
      properties:
        status: { type: string, enum: [ABERTA, EM_EXECUCAO, CONCLUIDA, SUSPENSA] }
        motivo: { type: string }
        # ... outros campos mutáveis
    PaginatedAuditoriaResponse:
      allOf:
        - $ref: '#/components/schemas/PaginatedResponse'
        - type: object
          properties:
            data:
              type: array
              items: { $ref: '#/components/schemas/AuditoriaResponse' }
```

#### 2.4 REFINE — Refinar com Stakeholders

- Apresente `openapi.yaml` para validação humana (Gate 5a-API / Gate 10-API)
- Colete feedback → ajuste spec → registre decisões em ADRs
- **NÃO prossiga para implementação sem Gate aprovado**

---

## 📋 REGRAS CRÍTICAS DE REST (Vinculantes)

### Resource Design (Higginbotham ch03)
| Regra | Exemplo Correto | Exemplo Incorreto |
|-------|-----------------|-------------------|
| Recursos = substantivos no plural | `/auditorias`, `/planos` | `/getAuditorias`, `/auditoria` |
| Nested para relacionamentos | `/auditorias/:id/achados` | `/achados?auditoriaId=:id` (apenas filtro) |
| Ações = PATCH no status | `PATCH /auditorias/:id { status: "CONCLUIDA" }` | `POST /auditorias/:id/concluir` |
| PUT = substituição completa (idempotente) | `PUT /config/:chave { valor: "x" }` | `PUT` para update parcial |
| PATCH = modificação parcial | `PATCH /auditorias/:id { objetivo: "novo" }` | — |

### Nomenclatura
| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Paths | kebab-case | `/solicitacoes-consultoria`, `/itens-plano` |
| Query params | camelCase | `?page=1&limit=20&auditoriaId=` |
| Path params | camelCase | `/auditorias/{auditoriaId}` |
| Request/Response body | camelCase | `{ "unidadeAuditada": "TI" }` |
| Status codes domínio | PT-BR (intencional) | `ABERTA`, `EM_EXECUCAO` |
| Enum values | UPPER_SNAKE_CASE | `CONFORMIDADE`, `DESEMPENHO` |

### HTTP Semantics
| Endpoint | @HttpCode | @ApiResponse Obrigatórios |
|----------|-----------|---------------------------|
| GET (list) | 200 | 200, 401, 403 |
| GET (one) | 200 | 200, 401, 403, 404 |
| POST | 201 | 201, 401, 403, 422 |
| PATCH | 200 | 200, 401, 403, 404, 422 |
| DELETE | 204 | 204, 401, 403, 404 |

### Pagination Contract
```typescript
// Query params obrigatórios em listagens
interface PaginationQuery {
  page?: number;    // default: 1, min: 1
  limit?: number;   // default: 20, max: 100
}

// Response envelope PADRÃO
interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
```

### Error Response Contract
```typescript
// Todos os erros seguem este envelope
interface ErrorResponse {
  statusCode: number;      // 400, 401, 403, 404, 422, 500
  timestamp: string;       // ISO 8601
  path: string;            // request path
  code: string;            // código de erro (ex: VALIDATION_ERROR)
  message: string;         // human-readable
  details?: Record<string, unknown>; // opcional
}
```

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS

Esta skill integra com `fitness-functions.py` através dos checks:

| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `rest-verbs/put-for-partial` | PUT não usado para update parcial | 0 | block (core) |
| `rest-verbs/rpc-endpoints` | Sem endpoints `/concluir`, `/suspender` | 0 | block |
| `rest-verbs/patch-for-status` | Status changes via PATCH body | - | block |
| `http-semantics/httpcode-decorator` | @HttpCode em todos endpoints | 100% | block |
| `http-semantics/apiresponse-errors` | @ApiResponse 401/403/404/422 | 100% | warn |
| `pagination/list-endpoints` | Listagens têm page/limit | 100% core | warn |
| `pagination/envelope-standard` | Response usa PaginatedResponse | 100% | warn |
| `naming/paths-kebabcase` | Paths em kebab-case | 100% | block |
| `naming/query-camelcase` | Query params em camelCase | 100% | warn |
| `naming/resource-nouns` | Recursos são substantivos | 100% | block |
| `openapi/spec-exists` | openapi.yaml existe e válido | 1 | block |
| `openapi/security-defined` | BearerAuth + tags | 1 | block |

---

## 📝 CHECKLIST DE VALIDAÇÃO HUMANA (Gate 5a-API / 10-API)

Antes de aprovar:

- [ ] `docs/api/ALIGN.md` preenchido com decisões de stakeholders?
- [ ] `docs/api/DEFINE/{modulo}.md` para **todos** módulos core?
- [ ] `docs/api/openapi.yaml` **completo** (todos endpoints, schemas, errors)?
- [ ] Spec valida no `swagger-codegen` / `redocly lint`?
- [ ] ADRs criados para decisões de design (ex: PT-BR status, versioning)?
- [ ] Fitness functions passam: `python .ace/scripts/fitness-functions.py --check-api-design --strict`?
- [ ] Frontend team validou contracts?

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | Aplicar a **todos endpoints** desde o primeiro commit. Spec primeiro, código depois. |
| **Brownfield** | Aplicar a **novos módulos** e **módulos alterados** (PRP-A). Legacy: marcar com `// LEGACY_API` + ADR de migração. Endpoints antigos podem manter RPC-style temporariamente. |

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os artefatos, **PARE** e apresente:

1. **Resumo dos Resources:** Tabela recurso → path → operações → nested
2. **Arquivos Gerados/Atualizados:**
   - `docs/api/ALIGN.md`
   - `docs/api/DEFINE/{modulo}.md` (um por módulo core)
   - `docs/api/openapi.yaml` (spec completa)
   - `docs/architecture/adr/ADR-XXX-api-versioning.md`
   - `docs/architecture/adr/ADR-XXX-rest-conventions.md`
   - `docs/architecture/adr/ADR-XXX-domain-status-codes.md`
2. **Módulos Core:** Lista com enforcement `block`
3. **Decisões de Naming:** PT/EN, kebab/camel, status codes
4. **Paginação:** Parâmetros, envelope, limites
5. **Próximos Passos:** Perguntas para validação humana (foco em trade-offs, breaking changes, frontend coordination)

**NÃO prossiga para Step 8/11. Aguarde validação humana (Gate 5a-API / 10-API).**