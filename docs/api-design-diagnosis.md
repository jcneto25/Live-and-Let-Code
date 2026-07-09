# Diagnóstico de API Design — CONFORMITAS 3.0

**Baseado em**: *Principles of Web API Design* (James Higginbotham — ADD-R)
**Data**: 2026-07-08 | **Escopo**: Controllers em `api/src/`

---

## Sumário

| Dimensão | Avaliação | 
|----------|-----------|
| ADD-R Process (Align/Define/Design/Refine) | ⚠️ Design executado, Align/Define implícito |
| Resource Design | 🟡 Misto — boa parte, mas várias inconsistências |
| REST Conventions | 🔴 Inconsistências entre módulos |
| Developer Experience | 🟢 Swagger configurado, OpenAPI presente |
| Security | 🟢 Rate limiting, JWT, RBAC |
| Consistency | 🔴 PORTUGUÊS/INGLÊS, kebab-case/snake-case/camelCase |
| Pagination | 🟡 Só 1/26 controllers implementa |

---

## RESULTADOS POR CATEGORIA

### 1. Naming & URL Conventions — 🔴 10 violações

| # | Violação | Exemplo | Impacto |
|---|----------|---------|---------|
| 1 | **Português na maioria, inglês em alguns** | `GET /auditorias` vs `GET /auth/profile` | Inconsistência confunde consumidores |
| 2 | **kebab-case vs snake_case em query params** | `?arquivo_path` (snake) vs `?auditoriaId` (camel) | Documentação ambígua |
| 3 | **Plural inconsistente** | `solicitacoes-consultoria` (plural+singular) vs `auditorias` (plural) | Quebra previsibilidade |
| 4 | **Verbete no path em vez de recurso** | `POST /planos/:id/submeter`, `POST /planos/:id/criar-revisao` | Misto de RPC com REST (Higginbotham ch03) |
| 5 | **Mistura de inglês e português nos status** | `PENDENTE`, `APROVADO`, `EM_EXECUCAO` vs `BACKLOG`, `TODO` | Consistente internamente, mas sem tradução na API |
| 6 | **Sem padronização PT-BR → EN** | `criar-evidencia.dto.ts` vs `create-auditoria.dto.ts` | Nomes de arquivo mistos |
| 7 | **Query params sem tipo consistente** | `GET /auditorias?status=ABERTA` (string) vs `GET /logs?page=1&limit=50` (number) | ok, mas sem padrão de envelope |
| 8 | **`@Patch` vs `@Put` inconsistente** | 14x `@Patch`, 7x `@Put` para updates parciais | Violação REST: PUT deve ser idempotente total, PATCH para parcial |

### 2. Resource Modeling — 🟡 5 violações

| # | Violação | Exemplo |
|---|----------|---------|
| 9 | **Apenas 1 nested resource** | `auditorias/:auditoriaId/achados` existe, mas `planos/:id/itens` e `auditorias/:id/evidencias` estão em controller único |
| 10 | **Resources duplicados** | `GET /planos/:id` e `GET planos/:id` no mesmo controller com paths diferentes |
| 11 | **Ações como endpoints** | `POST .../concluir`, `POST .../suspender`, `POST .../iniciar` — Higginbotham recomenda `PATCH ... { status: "CONCLUIDA" }` |
| 12 | **Prefixos de módulo como pasta** | `qualidade/avaliacoes`, `qualidade/nao-conformidades`, `qualidade/indicadores` — sub-recursos sem controller separado |
| 13 | **Sem HATEOAS ou links** | Nenhum endpoint retorna links para recursos relacionados |

### 3. HTTP Semantics — 🟡 4 violações

| # | Violação | Exemplo |
|---|----------|---------|
| 14 | **PUT para update parcial** | `PUT /config/:chave`, `PUT /avaliacoes/:id`, `PUT /determinacoes-externas/:id` — deveria ser PATCH |
| 15 | **Sem @HttpCode na maioria** | Apenas 1 endpoint usa `@HttpCode(200)` ou `@HttpCode(HttpStatus.NO_CONTENT)` |
| 16 | **Sem @ApiResponse para erros** | Nenhum endpoint documenta 401, 403, 404 ou 422 com `@ApiResponse` |
| 17 | **Status code genérico** | `NotFoundException` retorna 404, `BadRequestException` retorna 400 — ok, mas sem padronização de body |

### 4. Pagination — 🟡 2 violações

| # | Violação | Exemplo |
|---|----------|---------|
| 18 | **Só logs-sistema implementa paginação** | `GET /logs?page=1&limit=50` — os outros 25 controllers listam sem limite |
| 19 | **Sem envelope de paginação** | Não há padrão `{ data, total, page, limit, totalPages }` nos endpoints que deveriam ter |

### 5. Error Handling — 🟢 ok

| Item | Status |
|------|--------|
| GlobalExceptionFilter | ✅ Configurado |
| ValidationPipe com whitelist | ✅ `whitelist: true, forbidNonWhitelisted: true` |
| Status 422 para validação | ✅ `errorHttpStatusCode: 422` |
| Logging de erros | ✅ Logger presente |

### 6. Versioning & OpenAPI — 🟢 ok

| Item | Status |
|------|--------|
| Version prefix | ✅ `api/v1` global |
| Version in config | ✅ `setVersion('0.1.0')` |
| Bearer auth | ✅ `.addBearerAuth()` |
| Tags | ✅ `addTag()` por módulo |
| Swagger UI | ✅ `GET /swagger` |

### 7. Security — 🟢 ok

| Item | Status |
|------|--------|
| Rate limiting global | ✅ 60 req/min |
| Login throttle | ✅ 10 req/min |
| JWT + Bearer | ✅ |
| RBAC via @Roles | ✅ |
| Helmet | ✅ |

---

## Prioridade de Correção

| Prioridade | Itens | Esforço |
|-----------|-------|---------|
| 🔴 **Alta** | 8 (PATCH vs PUT), 11 (ações como endpoints), 18 (pagination) | Médio |
| 🟡 **Média** | 1 (pt/en), 2 (query case), 4 (RPC no path), 9 (nesting), 15 (HttpCode), 16 (@ApiResponse) | Médio |
| 🟢 **Baixa** | 3 (plural), 5 (status i18n), 6 (file naming), 13 (HATEOAS), 19 (pagination envelope) | Alto |
