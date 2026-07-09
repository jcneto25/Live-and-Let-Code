---
name: llc-step-clean-code-errors
description: Pipeline LLC — Clean Code: Error Handling (Cap. 7 Clean Code). Regras para exceptions com contexto, sem try/catch vazio, Result<T,E> para regras de negócio, error boundaries. Integra com fitness functions.
version: 1.0.0
tags: [clean-code, error-handling, exceptions, result-pattern, llc-pipeline, code-quality]
---

# LLC Skill: Clean Code — Error Handling

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Transversal — aplica-se em Steps 9, 11a, 11b  
**Referência:** *Clean Code* (R. Martin) — Capítulo 7, *Domain-Driven Design* — Domain Errors  
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-clean-code-errors` ou "Execute a skill llc-step-clean-code-errors".
3. Pelo Thin Harness: `python .ace/scripts/llc.py run --step clean-code-errors --task "Aplicar regras de Clean Code para error handling"`.

---

## 🎯 OBJETIVO

Garantir tratamento de erros **limpo, consistente e informativo**:
- **Exceptions com contexto** — mensagens descritivas, nunca vazias
- **Result<T, E> para regras de negócio** — nunca throw para fluxo esperado
- **Sem try/catch vazio** — sempre logar ou transformar
- **Domain Errors tipados** — classes de erro por agregado
- **Error boundaries centralizados** — Global Exception Filter

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. Exceptions Sempre com Contexto

```typescript
// ❌ RUIM: mensagem vazia
if (!auditoria) throw new NotFoundException('');
if (!usuario) throw new NotFoundException('');

// ✅ BOM: contexto completo para debugging
if (!auditoria) throw new NotFoundException(`Auditoria ${auditoriaId} não encontrada`);
if (!usuario) throw new NotFoundException(`Usuario ${usuarioId} não encontrado para auditoria ${auditoriaId}`);
```

### 2. Result<T, E> para Regras de Negócio

**NUNCA use `throw` para fluxos de negócio esperados** (validações, transições de estado, regras).

```typescript
// ❌ RUIM: throw para regra de negócio
async iniciarExecucao(id: string) {
    const auditoria = await this.repo.find(id);
    if (auditoria.status !== 'ABERTA')
        throw new BadRequestException('Auditoria deve estar ABERTA para iniciar');
    auditoria.status = 'EM_EXECUCAO';
    return this.repo.save(auditoria);
}

// ✅ BOM: Result<T, E> — fluxo explícito, tipado, testável
async iniciarExecucao(id: string): Promise<Result<Auditoria, TransicaoInvalidaError>> {
    const auditoria = await this.repo.find(id);
    if (!auditoria) return err(new AuditoriaNaoEncontradaError(id));
    
    const resultado = auditoria.iniciarExecucao(); // domain method returns Result
    if (isErr(resultado)) return err(resultado.error);
    
    const salva = await this.repo.save(resultado.value);
    return ok(salva);
}

// Caller:
const resultado = await useCase.iniciarExecucao(id);
if (isErr(resultado)) {
    // Trata erro tipado
    switch (resultado.error.constructor) {
        case AuditoriaNaoEncontradaError: return notFound();
        case TransicaoInvalidaError: return badRequest(resultado.error.message);
    }
}
return ok(resultado.value);
```

### 3. Domain Errors: Classes Tipadas por Agregado

```typescript
// domain/errors/auditoria-nao-encontrada.error.ts
export class AuditoriaNaoEncontradaError extends DomainError {
    constructor(public readonly auditoriaId: string) {
        super(`Auditoria ${auditoriaId} não encontrada`, 'AUDITORIA_NAO_ENCONTRADA');
    }
}

// domain/errors/transicao-status-invalida.error.ts
export class TransicaoStatusInvalidaError extends DomainError {
    constructor(
        public readonly statusAtual: StatusAuditoria,
        public readonly statusTentado: StatusAuditoria,
    ) {
        super(
            `Transição inválida: ${statusAtual} → ${statusTentado}. ` +
            `Transições válidas: ${TRANSICOES_VALIDAS[statusAtual]?.join(', ') || 'nenhuma'}`,
            'TRANSICAO_STATUS_INVALIDA'
        );
    }
}

// domain/errors/domain-error.base.ts
export abstract class DomainError extends Error {
    abstract readonly code: string;
    
    constructor(message: string, public readonly code: string) {
        super(message);
        this.name = this.constructor.name;
        Error.captureStackTrace(this, this.constructor);
    }
}
```

### 4. Sem try/catch Vazio

```typescript
// ❌ RUIM: engole erro silenciosamente
try {
    await this.externalApi.call();
} catch (e) {
    // vazio!
}

// ❌ RUIM: só loga e continua
try {
    await this.notificacaoService.enviar(...);
} catch (e) {
    console.log(e); // perde stack trace, não re-throw
}

// ✅ BOM: loga com contexto + re-throw ou transforma
try {
    await this.notificacaoService.enviar(...);
} catch (e) {
    this.logger.error('Falha ao enviar notificação', {
        auditoriaId,
        tipo: 'AUDITORIA_ABERTA',
        error: e.message,
        stack: e.stack,
    });
    // Decide: re-throw, retorna Result, ou ignora explicitamente
    // Se ignora, documenta POR QUE:
    // return; // Notificação é best-effort, não bloqueia abertura
}
```

### 5. Global Exception Filter (Error Boundary)

```typescript
// common/filters/global-exception.filter.ts
@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
    catch(exception: unknown, host: ArgumentsHost) {
        const ctx = host.switchToHttp();
        const response = ctx.getResponse<Response>();
        const request = ctx.getRequest<Request>();
        
        let status = HttpStatus.INTERNAL_SERVER_ERROR;
        let message = 'Erro interno do servidor';
        let code = 'INTERNAL_ERROR';
        let details: Record<string, unknown> = {};
        
        if (exception instanceof DomainError) {
            status = HttpStatus.BAD_REQUEST;
            message = exception.message;
            code = exception.code;
        } else if (exception instanceof NotFoundException) {
            status = HttpStatus.NOT_FOUND;
            message = exception.message;
            code = 'NOT_FOUND';
        } else if (exception instanceof BadRequestException) {
            status = HttpStatus.BAD_REQUEST;
            message = exception.message;
            code = 'BAD_REQUEST';
        } else if (exception instanceof UnauthorizedException) {
            status = HttpStatus.UNAUTHORIZED;
            message = exception.message;
            code = 'UNAUTHORIZED';
        } else if (exception instanceof ForbiddenException) {
            status = HttpStatus.FORBIDDEN;
            message = exception.message;
            code = 'FORBIDDEN';
        } else {
            // Log completo para erros inesperados
            this.logger.error('Erro não tratado', {
                path: request.url,
                method: request.method,
                error: exception instanceof Error ? exception.message : String(exception),
                stack: exception instanceof Error ? exception.stack : undefined,
            });
        }
        
        response.status(status).json({
            statusCode: status,
            timestamp: new Date().toISOString(),
            path: request.url,
            code,
            message,
            details,
        });
    }
}
```

### 6. Async Error Handling em Promise.allSettled

```typescript
// ❌ RUIM: acesso inseguro
const results = await Promise.allSettled(promises);
for (let i = 0; i < results.length; i++) {
    const value = results[i].value; // TypeScript error: pode ser rejected
}

// ✅ BOM: type guards corretos
const results = await Promise.allSettled(promises);
for (const result of results) {
    if (result.status === 'fulfilled') {
        const value = result.value;
        // processa value
    } else {
        this.logger.error('Promise rejeitada', { error: result.reason });
        // decide: continua, agrega erros, ou falha rápido
    }
}
```

### 7. Logging de Erros: Estruturado, com Contexto

```typescript
// ✅ BOM: structured logging
this.logger.error('Falha ao criar auditoria', {
    // Contexto de negócio
    auditoriaId: dto.itemPlanoId,
    usuarioId: criadoPorId,
    unidade: dto.unidadeAuditada,
    // Contexto técnico
    error: error.message,
    stack: error.stack,
    // Metadata
    operation: 'createAuditoria',
    timestamp: new Date().toISOString(),
});
```

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS

| Check | Descrição | Threshold | Severidade |
|-------|-----------|-----------|------------|
| `no-empty-exceptions` | Detecta `throw new XException('')` ou `throw new XException("")` | 0 ocorrências | block |
| `no-empty-catch` | Detecta `catch (e) { }` ou `catch (e) { console.log(e) }` | 0 ocorrências | block |
| `result-pattern-usage` | Verifica se regras de negócio usam `Result<T, E>` em vez de throw | - | block (core) / warn (non-core) |
| `domain-errors-exist` | Cada módulo core tem `domain/errors/*.error.ts` | ≥ 1 por agregado | warn |
| `global-filter-exists` | Projeto tem GlobalExceptionFilter registrado | 1 | block |
| `async-error-handling` | Verifica `Promise.allSettled` com type guards | - | warn |

---

## 📝 CHECKLIST DE VALIDAÇÃO HUMANA (Gate)

- [ ] Zero `NotFoundException('')`, `BadRequestException('')`, etc.?
- [ ] Regras de negócio usam `Result<T, E>` em vez de throw?
- [ ] Domain Errors tipados em `domain/errors/`?
- [ ] Sem `catch (e) { }` vazio?
- [ ] GlobalExceptionFilter existe e trata DomainError?
- [ ] `Promise.allSettled` usa type guards corretos?
- [ ] Logs de erro têm contexto estruturado?
- [ ] Fitness functions passam (`python .ace/scripts/fitness-functions.py --check-errors --strict`)?

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | `Result<T, E>` obrigatório desde o início. Domain Errors + Global Filter no setup |
| **Brownfield** | Novos use cases usam `Result<T, E>`. Legacy services: wrapper gradual. Global Filter adicionado no Step 8. |

---

## 📤 SAÍDA ESPERADA

1. **Relatório de violações**: arquivo, linha, tipo (empty exception, empty catch, throw para negócio)
2. **Domain Errors criados** por agregado
3. **GlobalExceptionFilter** implementado/validado
4. **Fitness functions** atualizadas
5. **Aguardar Gate humano**