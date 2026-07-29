---
name: llc-step-clean-code-deep
description: Pipeline LLC — Clean Code: Deep Clean (Ação 4 do Harness Preventivo). 8 fitness functions para erros recorrentes que os checks básicos não pegam — CQS violation, null return, data clump, flag arguments, primitive obsession, funções longas non-core, validação ausente e pass-through. Integra com fitness-functions.py --check-deep-clean.
version: 1.0.0
tags: [clean-code, deep-clean, cqs, null-safety, data-clump, llc-pipeline, code-quality]
---

# LLC Skill: Clean Code — Deep Clean

**Pipeline:** Live and Let Code (LLC)
**Fase:** Transversal — dimensão adicional do Step 5c (Clean Code Enforcement)
**Referência:** *Clean Code* (R. Martin) Cap. 3, 6, 17 · *Refactoring* (M. Fowler) — code smells · CQS (Meyer)
**Origem:** Ação 4 do Harness Preventivo LLC (§2.4)
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-clean-code-deep` ou "Execute a skill llc-step-clean-code-deep".
3. Pelo Thin Harness: `python .ace/scripts/llc.py run --step clean-code-deep --task "Aplicar Deep Clean checks"`.

Esta skill é a **7ª dimensão** do Step 5c. As 6 dimensões básicas (Functions, Classes, Naming, Errors, Smells, ReadModels) cobrem estrutura; Deep Clean cobre os **erros recorrentes de lógica** que passam pelos checks básicos.

---

## 🎯 OBJETIVO

Detectar 8 erros recorrentes que os 21 checks básicos de Clean Code não capturam. São padrões que corrompem a arquitetura silenciosamente:

- **CQS violation** — comando que também retorna dados (mistura escrita e leitura)
- **Null return** — `return null` que propaga `NullPointerException` para as camadas de cima
- **Data clump** — grupos de campos que andam juntos e deveriam ser um Value Object
- **Flag arguments** — booleano que faz o método fazer duas coisas
- **Primitive obsession** — `string`/`number` onde um tipo de domínio seria mais seguro
- **Funções longas non-core** — funções > 30 linhas fora dos módulos core
- **Validação ausente** — `create`/`update` sem validação explícita
- **Pass-through** — método que só delega, sem lógica própria (indireção inútil)

---

## 📋 REGRAS OBRIGATÓRIAS

### 1. No CQS Violation (block em core)

Command-Query Separation: um método ou **muda estado** (command, retorna `void`) ou **retorna dado** (query, sem side effect) — nunca os dois.

```typescript
// ❌ RUIM: command com side effect QUE TAMBÉM retorna dados
async createPedido(dto: CreatePedidoDto): Promise<Pedido> {
    const pedido = await this.repo.create(dto);
    this.eventEmitter.emit('pedido.criado', new PedidoCriadoEvent(pedido)); // side effect
    return pedido; // ... e retorna dado
}

// ✅ BOM: command retorna void ou só o identificador
async createPedido(dto: CreatePedidoDto): Promise<PedidoId> {
    const id = await this.repo.create(dto);
    this.eventEmitter.emit('pedido.criado', new PedidoCriadoEvent(id));
    return id; // identificador para navegação, não a entidade completa
}
```

**Heurística do check:** método `create*/update*/delete*` com return type ≠ `void`/`Id` **e** chamada a `eventEmitter.emit()` ou `notificationService.*`.

### 2. No Null Return (block em core)

Services e repositories não devem retornar `null` — usar `Optional<T>`, `Result<T, E>` ou lançar exceção descritiva.

```typescript
// ❌ RUIM: null propaga para o caller, que esquece de checar
async findUser(id: string): Promise<User | null> {
    return this.repo.findUnique(id); // pode retornar null
}

// ✅ BOM: Result explícito, obriga o caller a tratar
async findUser(id: string): Promise<Result<User, UserNotFoundError>> {
    const user = await this.repo.findUnique(id);
    return user ? ok(user) : err(new UserNotFoundError(id));
}
```

### 3. No Data Clump (warn)

3+ campos que aparecem **juntos** em 5+ assinaturas de função são um Value Object escondido.

```typescript
// ❌ RUIM: {rua, numero, cidade, cep} repetidos em toda assinatura
function criarEntrega(rua: string, numero: string, cidade: string, cep: string, ...) {}
function validarEndereco(rua: string, numero: string, cidade: string, cep: string) {}
function formatarEndereco(rua: string, numero: string, cidade: string, cep: string) {}

// ✅ BOM: Value Object Endereco
class Endereco {
  constructor(readonly rua: string, readonly numero: string,
              readonly cidade: string, readonly cep: string) {}
}
function criarEntrega(endereco: Endereco, ...) {}
```

**Config:** `min_fields: 3`, `min_occurrences: 5` (ajustável em `.ace/arch-config.yaml`).

### 4. No Flag Arguments (block em core)

Parâmetro booleano em método público = o método faz duas coisas. Divida em dois métodos.

```typescript
// ❌ RUIM: flag decide o comportamento
async salvar(pedido: Pedido, notificar: boolean): Promise<void> {
    await this.repo.save(pedido);
    if (notificar) await this.notificar(pedido);
}

// ✅ BOM: dois métodos com nomes que revelam a intenção
async salvar(pedido: Pedido): Promise<void>
async salvarENotificar(pedido: Pedido): Promise<void>
```

### 5. No Primitive Obsession (warn)

Campo semanticamente rico (email, CPF, dinheiro, IDs) não deve ser `string`/`number` cru.

```typescript
// ❌ RUIM: string aceita qualquer coisa
function enviarEmail(destinatario: string) {} // "não-é-email" compila

// ✅ BOM: Value Object valida na construção
class Email {
  constructor(readonly value: string) {
    if (!value.includes('@')) throw new InvalidEmailError(value);
  }
}
function enviarEmail(destinatario: Email) {}
```

### 6. Max Function Lines Deep (warn)

Funções > 30 linhas em **qualquer** módulo (o check básico `function-max-lines` só bloqueia core em 20; este pega o restante em 30).

```typescript
// ⚠️ ALERTA: 35 linhas em módulo non-core — extrair sub-funções
function processarRelatorio(dados: Dado[]) { /* 35 linhas */ }
```

**Config:** `max_lines: 30`.

### 7. No Missing Validation (block em core)

Métodos `create`/`update` em services devem chamar validação explícita (`assertValid*`, `validate*`, schema).

```typescript
// ❌ RUIM: cria sem validar
async createUsuario(dto: CreateUsuarioDto): Promise<UsuarioId> {
    return this.repo.create(dto); // dto nunca validado
}

// ✅ BOM: validação explícita antes de persistir
async createUsuario(dto: CreateUsuarioDto): Promise<UsuarioId> {
    this.assertValidUsuario(dto);
    return this.repo.create(dto);
}
```

### 8. No Pass-Through (warn)

Método que só delega para outro, sem lógica adicional, é indireção desnecessária.

```typescript
// ❌ RUIM: pass-through puro — remova e chame o repo direto
async findById(id: string): Promise<User> {
    return this.repo.findById(id); // não agrega nada
}

// ✅ BOM: o método agrega valor (mapeia, valida, decide)
async findById(id: string): Promise<UserReadModel> {
    const user = await this.repo.findById(id);
    return this.mapper.toReadModel(user); // agrega transformação
}
```

---

## 🔧 FITNESS FUNCTIONS AUTOMATIZADAS (8 Checks)

Implementados em `.ace/scripts/fitness_functions/checks_deep_clean.py`.

| Check | Descrição | Severidade Core/Non-core | Config |
|-------|-----------|--------------------------|--------|
| `no-cqs-violation` | Command retorna valor E tem side effect | block / warn | `mode: hybrid` |
| `no-null-return` | `return null` em services/repositories | block / warn | `mode: hybrid` |
| `no-data-clump` | 3+ campos juntos em 5+ assinaturas | warn / warn | `min_fields: 3`, `min_occurrences: 5` |
| `no-flag-arguments` | Parâmetro booleano em método público | block / warn | `mode: hybrid` |
| `no-primitive-obsession` | Primitivo onde tipo de domínio caberia | warn / warn | `mode: warn` |
| `max-function-lines-deep` | Funções > 30 linhas em qualquer módulo | warn / warn | `max_lines: 30` |
| `no-missing-validation` | `create`/`update` sem validação explícita | block / warn | `mode: hybrid` |
| `no-pass-through` | Método que apenas delega sem lógica | warn / warn | `mode: warn` |

> **Modo `hybrid`:** bloqueia (`block`) em módulos core (`core_modules` do `.ace/arch-config.yaml`) e apenas alerta (`warn`) nos demais.

---

## 📊 COMANDO DE EXECUÇÃO

```bash
# Executa os 8 checks de Deep Clean
python .ace/scripts/fitness-functions.py --check-deep-clean --strict

# Combinado com as demais dimensões de Clean Code
python .ace/scripts/fitness-functions.py --check-clean-code --check-deep-clean --strict
```

**Opções:**
- `--strict` — falha (exit 1) se houver qualquer violação block
- `--verbose` — detalhes por arquivo/módulo
- `--module <nome>` — filtrar módulo específico
- `--config <path>` — usar `.ace/arch-config.yaml` customizado

---

## 📝 CHECKLIST DE VALIDAÇÃO HUMANA (Gate 8.5 — dimensão Deep Clean)

- [ ] Zero commands (`create/update/delete`) retornando a entidade completa quando há side effect? (CQS)
- [ ] Zero `return null` em services/repositories? (usar `Result`/`Optional`/throw)
- [ ] Data clumps extraídos para Value Objects?
- [ ] Zero flag arguments booleanos em métodos públicos?
- [ ] Campos ricos (email, CPF, dinheiro) usam Value Objects, não primitivos?
- [ ] Zero funções > 30 linhas (mesmo em non-core)?
- [ ] Todos os `create`/`update` chamam validação explícita?
- [ ] Zero métodos pass-through puros?
- [ ] Fitness functions passam (`python .ace/scripts/fitness-functions.py --check-deep-clean --strict`)?

---

## 🌱 GREENFIELD vs BROWNFIELD

| Contexto | Aplicação |
|----------|-----------|
| **Greenfield** | Aplicar a **todo código novo** desde o primeiro commit. Baseline esperado: 0 violações. |
| **Brownfield** | Aplicar a **novos arquivos** e **arquivos modificados**. Violações `warn` em código legacy vão para dívida técnica no §11 do PRP; violações `block` em core module modificado devem ser corrigidas antes do merge. |

---

## 📤 SAÍDA ESPERADA

Ao executar esta skill, o agente deve:

1. **Verificar** o código contra os 8 checks Deep Clean
2. **Reportar** violações com localização exata, severidade e sugestão de fix
3. **Distinguir** `block` (core) de `warn` (non-core) — só `block` impede o merge
4. **Validar** via `fitness-functions.py --check-deep-clean --strict`
5. **Registrar** violações `warn` remanescentes como dívida técnica
6. **Aguardar** validação humana (Gate 8.5) antes de prosseguir

**NÃO prossiga para execução sem Gate 8.5 aprovado.**
