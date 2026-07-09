# Plano de Correção — API Design

**Baseado em**: *Principles of Web API Design* (James Higginbotham)
**Data**: 2026-07-08 | **19 violações** em 3 ondas

---

## WAVE 1 — REST Semantics (🔴 5 itens)

### 1. Normalizar `@Put` → `@Patch`

7 endpoints usam `@Put` para update parcial. PUT deve ser idempotente (substituição completa). PATCH é para modificação parcial.

| Arquivo | Linha | Mudança |
|---------|-------|---------|
| `api/src/config/config.controller.ts` | 26 | `@Put(':chave')` → `@Patch(':chave')` |
| `api/src/governanca/governanca.controller.ts` | 39 | `@Put('determinacoes-externas/:id')` → `@Patch(...)` |
| `api/src/etica/etica.controller.ts` | 69 | `@Put(...)` → `@Patch(...)` |
| `api/src/qualidade/qualidade.controller.ts` | 46, 86, 116 | 3x `@Put` → `@Patch` |
| `api/src/recomendacoes/recomendacoes.controller.ts` | 47 | `@Put(':id')` → `@Patch(':id')` |

### 2. Ações como endpoints → `PATCH { status }`

Endpoints RPC (`POST .../concluir`, `POST .../suspender`) viram `PATCH :id { status }`.

| Arquivo | Endpoint Atual | Novo |
|---------|---------------|------|
| `src/auditorias/auditorias.controller.ts` | 3x `POST .../iniciar`, `/concluir`, `/suspender` | 1x `PATCH /auditorias/:id { status, motivo? }` |
| `src/planos/planos.controller.ts` | 3x `POST .../submeter`, `/aprovar`, `/publicar` | 1x `PATCH /planos/:id { status }` |
| `src/achados/achados.controller.ts` | `POST .../enviar-manifestacao`, `/consolidar` | `PATCH /achados/:id { status }` |
| `src/consultorias/consultorias.controller.ts` | `POST .../aceitar`, `/recusar` | `PATCH ... { status }` |

### 3. Adicionar `@HttpCode` + `@ApiResponse`

Decorator compartilhado para documentar erros padronizados.

### 4. Adicionar `@ApiResponse({ status })` nos endpoints protegidos

### 5. Adicionar `@HttpCode(HttpStatus.NO_CONTENT)` em `@Delete`

---

## WAVE 2 — Pagination + Nested (🟡 4 itens)

### 6. Paginação nos endpoints de listagem

Adicionar `@Query('page') page = 1, @Query('limit') limit = 20` nos 10 endpoints prioritários.

### 7. Extrair nested resources

Criar controllers separados para evidências, papéis-trabalho, requisições em `auditorias/`.

### 8. Criar shared `PaginatedResponse<T>` interface

### 9. Aplicar envelope de paginação nos services

---

## WAVE 3 — Naming (🟢 3 itens)

### 10. Query params: `arquivo_path` → `arquivoPath`

### 11. Padronizar nomes de endpoints (kebab-case já é padrão ✅)

### 12. Domain status codes mantidos em português (intencional — domínio AUDIN)

---

## Questões Pendentes

1. Mudar ações RPC para PATCH quebra contrato com frontend — coordenar?
2. Paginar 10 endpoints de uma vez ou começar com 3 críticos?
3. Extrair nested controllers ou manter no mesmo arquivo?
