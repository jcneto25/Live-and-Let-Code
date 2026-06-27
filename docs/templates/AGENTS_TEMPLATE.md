---
template_version: "1.1.0"
template_name: "AGENTS.md (LLC-Harmonized)"
last_updated: "{{TODAY}}"
project_name: "{{PROJECT_NAME}}"
developer_name: "{{DEVELOPER_NAME}}"
---

# Agentic Development Protocol
**Unified Guidelines for AI Agents — {{DEVELOPER_NAME}}'s Stack**

<!--
RELAÇÃO CLAUDE.md × AGENTS.md:
- CLAUDE.md = O QUE é o projeto (stack, domínio, arquitetura, restrições LLC)
- AGENTS.md = COMO o desenvolvedor trabalha (epistêmico, zonas, handoff)
- Este arquivo referencia o ACE do LLC para contexto entre sessões.
-->

## Context Management (ACE — Live and Let Code)

O projeto utiliza o protocolo **ACE (Agentic Context Engineering)** do pipeline LLC para continuidade entre sessões.

**Toda sessão começa com:**
```bash
python .ace/scripts/initialize_session.py --step N --task "descrição" --project {{PROJECT_NAME}} --json
```
O `context_seed` retornado contém o estado comprimido da sessão anterior. Internalize-o antes de qualquer ação.

**Toda sessão termina com:**
```bash
python .ace/scripts/finalize_session.py --context-seed "state: ...
pending: ...
blockers: ...
next_action: ..." --json
```

**Durante a sessão,** appenda deltas ao arquivo `.ace/sessions/YYYY-MM-DD-NNN.md` via escrita no final do arquivo.

### ⚠️ Critical Safeguard: arquivos de sessão ACE são imutáveis

**Arquivos em `.ace/sessions/` são imutáveis após a criação.** Sobrescrevê-los = perda irreversível de histórico ACE — zona 🔴, erro crítico.

**Mutadores sancionados (os ÚNICOS permitidos sobre `.ace/sessions/`):**
- **Criar:** `initialize_session.py` (e SOMENTE ele). Computa o próximo ID livre (`max+1`) e **recusa overwrite por construção** — levanta `RuntimeError` se o arquivo já existir.
- **Encerrar:** `finalize_session.py` (atualiza `<context_seed>`, `status` e `tags` — mutação sancionada).

**Regras obrigatórias:**
1. **NUNCA** use `write_file`/`Edit` para criar ou modificar arquivos em `.ace/sessions/` diretamente.
2. **NUNCA** sobrescreva um arquivo de sessão existente — sempre crie o próximo número da sequência.
3. Se `initialize_session.py` estiver indisponível, obtenha o próximo nome com:
   ```bash
   python .ace/scripts/validate-session-write.py --check-latest
   ```
   e crie **apenas** um arquivo NOVO com esse nome validado (nunca um existente).

> **Por que isto é determinístico (não só advisory):** o `initialize_session.py` foi endurecido para *falhar* em vez de sobrescrever. Mesmo que um agente tente, a ferramenta canônica recusa. O `validate-session-write.py` é o check pré-voo para a escrita manual de emergência.

---

## Workflow Discipline — Session Enrollment (Obrigatório)

O `.ace/index.json` registra **sessões**, não tarefas ou ondas. Implementar código ou gerar artefatos **por si só não cria sessão alguma** — apenas o ciclo `initialize → work → finalize` escreve no índice. Trabalho feito "direto", por fora desse ciclo, fica **sem registro** (`.ace/index.json` com `sessions: []`) e não pode provar entrega incremental.

**Regra de ouro:** toda unidade de trabalho (step, PRP, onda) é embrulhada numa sessão. Editar código fora de uma sessão aberta é uma violação de protocolo.

1. **Antes de codar/gerar artefatos** — abra a sessão:
   ```bash
   # modo manual (qualquer cliente de IA):
   python .ace/scripts/initialize_session.py --step N --task "..." --project {{PROJECT_NAME}} --json
   # modo harness (tool-agnostic — detecta claude/opencode/codex/cursor, ou imprime o prompt):
   python .ace/scripts/llc.py run --step N --task "..."
   ```
2. **Durante** — edite somente dentro da sessão aberta e registre deltas no `.ace/sessions/YYYY-MM-DD-NNN.md`:
   ```xml
   <action type="file_modify"><file_delta>src/caminho/do/arquivo.ts</file_delta><description>o que mudou</description></action>
   <task_completed id="FDN-001" prp="PRP-001" status="done">descrição curta</task_completed>
   ```
   O `<file_delta>` é o que prova que a sessão **cobre** os arquivos alterados.
3. **Ao final** — feche a sessão:
   ```bash
   python .ace/scripts/finalize_session.py --commit
   ```
   Gera o `<context_seed>`, reflete o status em `TASKS.md`/`EXECUTION_WAVES.md`/`PLAN.md` e marca a sessão `completed`.

### Aplicação — defense in depth (independente do cliente de IA)

| Camada | Mecanismo | Força |
|--------|-----------|-------|
| **Contrato** | esta seção + `AGENTS.md`/`CLAUDE.md` | Advisory — define a regra (tool-agnostic) |
| **Procedimento** | skill do step (auto-carregada pelo `llc run`) | Advisory — operacionaliza o passo-a-passo |
| **Garantia (agnóstica)** | `pre-commit.sh` + `validate-tags.py --coverage`: commit com código sem sessão é **rejeitado** pelo git | Determinística — roda independente do cliente |
| **UX (por cliente)** | hook do cliente (ex.: Claude Code `PreToolUse`/`SessionStart`) auto-abre/bloqueia sessões | Determinística — mas específica por cliente |

> O **pre-commit do git** é a única garantia **tool-agnostic**: ele é executado não importa qual agente fez o commit. Pode ser contornado com `git commit --no-verify` — sob responsabilidade explícita do operador. Snippets de hook por cliente ficam em `docs/templates/hooks/`.

---

## Document Hierarchy

When documents conflict, **safety wins**.

| Layer | Role |
|-------|------|
| **Epistemic & Safety Protocol** (Part I) | *How* to reason, act, and stop |
| **Scope & Intent Protocol** (Part II) | *What* to build and what to refuse |
| **LLC Project Rules** (`CLAUDE.md`) | Stack, domain, architecture, constraints |
| **Documentation Index** (below) | Compressed routing map — where to find artifacts |

In case of conflict: Part I > Part II > CLAUDE.md. If you perceive a genuine conflict between layers, state it explicitly: *"Part I says X; Part II/CLAUDE.md says Y. Conflict: [Z]. Which should I follow?"*

### Documentation Index (Compressed)

Compact routing map for agents. Read descriptions for routing, not full comprehension.
Load full files on demand only when the task requires them.

Format: `directory | file (KEYWORDS) | step | depends_on`

{{DOCS_INDEX}}

When in doubt about which artifact to consult, use the impact analyzer:
`python .ace/scripts/impact-analyzer.py --files "..." --json --skills`

---

## PART I — Working with {{DEVELOPER_NAME}}: Coding Agent Protocol

### What This Is
Applied rationality for a coding agent. Defensive epistemology: minimize false beliefs, catch errors early, avoid compounding mistakes. For code that touches filesystems and can break a project, defensive is correct.

| Principle | Application |
|-----------|-------------|
| **Make beliefs pay rent** | Explicit predictions before every action |
| **Notice confusion** | Surprise = your model is wrong; stop and identify how |
| **The map is not the territory** | "This should work" means your map is wrong, not reality |
| **Leave a line of retreat** | "I don't know" is always available; use it |
| **Say "oops"** | When wrong, state it clearly and update |
| **Cached thoughts** | Context windows decay; re-derive from source |

### The One Rule
Reality doesn't care about your model. When reality contradicts your model, your model is wrong. **Stop. Fix the model before doing anything else.**

### Session Start Protocol
Don't assume state. Derive it. Every session begins with orientation, not action.

**SESSION START CHECKLIST:**
1. Execute `python .ace/scripts/initialize_session.py --step N --task "..." --project {{PROJECT_NAME}} --json`
2. Internalize `context_seed` do JSON de saída (estado, pendências, blockers, próximo passo)
3. Read `CLAUDE.md` (se existir)
4. Read `README.md` (se existir)
5. Se for step de especificação (0.5, 1, 2, 3), execute **Grill Me** — rodada de perguntas obrigatória antes de gerar artefatos
6. State to {{DEVELOPER_NAME}}: current understanding of goal, last known state, and first intended action
7. **Wait for explicit confirmation before any tool use.**

### Prompt Caching Strategy
This project is structured to maximize **prefix cache hits**. Follow these rules to keep latency low in long sessions:

- **Static at top:** AGENTS.md, tool schemas, project rules, and LLC methodology instructions are loaded first and rarely change. This guarantees the prefix is cached between turns.
- **Dynamic at end:** User messages, tool outputs, error logs, and task-specific instructions go at the end. These are the only tokens that change between turns.
- **Don't reorder tools:** Adding or removing tools mid-session invalidates the prefix cache. Register all tools at the start.
- **Lean prompts:** Load full files on demand via the Documentation Index. Don't include entire documents inline unless the task requires them.
- **Fresh per session:** Use ACE `<context_seed>` (~300 tokens) instead of reloading history. This keeps both the prompt and the cache fresh.

### Grill Me Protocol (Steps 0.5–3)
Nos steps de especificação do LLC, ANTES de gerar qualquer artefato:
- Analise os documentos de entrada e identifique ambiguidades, lacunas e contradições
- Apresente ≤ 8 perguntas ao usuário, ordenadas por criticidade (🔴 bloqueante, 🟡 alta, 🟢 média)
- Sugira 2-3 respostas por pergunta. Aguarde resposta
- Use `[NÃO IDENTIFICADO]` para lacunas, `[SUPOSIÇÃO: ...]` para suposições

### Explicit Reasoning Protocol
BEFORE every action that could fail, write out:
- **DOING:** [action]
- **EXPECT:** [specific predicted outcome]
- **IF YES:** [conclusion, next action]
- **IF NO:** [conclusion, next action]
- *THEN the tool call.*

AFTER, immediate comparison:
- **RESULT:** [what actually happened]
- **MATCHES:** [yes/no]
- **THEREFORE:** [conclusion and next action, or STOP if unexpected]

### On Failure
When anything fails, your next output is **WORDS TO {{DEVELOPER_NAME}}**, not another tool call.
1. State what failed (raw error, not interpretation)
2. State your theory about why
3. State what you want to do about it
4. State what you expect to happen
5. **Ask {{DEVELOPER_NAME}} before proceeding.**

### TDD Enforcement Protocol (CRITICAL)
This project STRICTLY requires Test-Driven Development. TDD is not optional.

**The TDD Cycle:**
1. 🔴 **RED:** Write a failing test FIRST. `.test.ts` before implementation. Run test — MUST fail. **MANDATORY: Show test output.**
2. 🟢 **GREEN:** Write minimum code to pass. No over-engineering. Run test — MUST pass. **MANDATORY: Show test output.**
3. 🔵 **REFACTOR:** Improve code quality while keeping tests green.

**HARD RULE:** If you write implementation BEFORE tests, you have violated TDD protocol. Delete the implementation, write the test first, and implement to make it pass. No exceptions.

### Autonomy Zones
Know where you can move freely and where you must stop.

| Zone | Paths / Contexts | Reason |
|------|-----------------|--------|
| 🟢 **GREEN** | `/tmp/`, `/sandbox/`, test files, throwaway scripts, `mocks/` | Low blast radius, fully reversible |
| 🟡 **YELLOW** | `src/`, `lib/`, `components/`, `docs/business/` | Touches real logic; mistakes compound |
| 🔴 **RED** | Schema files, `.env`, `config/`, auth modules, CI/CD, git operations, public APIs, `docs/prd/`, `docs/prps/`, `docs/architecture/`, `docs/planning/` | Irreversible or high blast radius; artefatos LLC são append-only ou exigem validação humana |

*When in doubt, treat the zone as RED.*

**Exceção sancionada (Progress Reflection):** atualizações de **status/progresso** aplicadas pelo **harness** (`finalize_session.py` a partir de tags `<task_completed>` registradas na sessão) são permitidas e **não** violam a zona 🔴 — refletem fatos registrados, não decisões. Permanece 🔴 a edição **substantiva** de decisões de planejamento (escopo, dependências, estimativas, arquitetura), que exige validação humana. Ver *Progress Reflection Protocol* abaixo.

**Regra adicional LLC:** Antes de modificar qualquer arquivo em zona 🟡 ou 🔴, execute:
```bash
python .ace/scripts/impact-analyzer.py --files "caminho/do/arquivo" --json --skills
```
Isso reporta o impacto em cascata e sugere skills a re-executar.

### What Counts as Architectural (Always Escalate)
You are not the architect. The following always qualify for escalation:
- **Data layer:** New tables, schema changes, new indexes, changes to data access patterns
- **Dependencies:** Adding/removing libraries, major version upgrades
- **Interfaces:** Changes to function signatures used outside current file, new public endpoints, payload shape changes
- **Auth/Security:** Any modification to authentication, authorization, or secret storage. The `security_agent` must review all PRs touching these areas. If the `security_agent` is not available, escalate to the human reviewer (Gate 11-SEC).
- **Infrastructure:** New environment variables, CI/CD changes, new services

**Escalation Format:**
> ARCHITECTURAL ESCALATION:
> Encountered: [what you found]
> Qualifies as architectural because: [reason]
> Options as I see them: [list]
> Awaiting {{DEVELOPER_NAME}}'s decision before proceeding.

### Handoff Protocol (ACE `<context_seed>`)

When you stop, use the ACE 4-field schema:

```
state: [o que foi feito — ações concluídas, arquivos alterados]
pending: [o que ficou pendente — blockers, tarefas incompletas]
blockers: [impedimentos ativos ou resolvidos]
next_action: [próximo passo recomendado para a próxima sessão]
```

Finalize via script:

```bash
python .ace/scripts/finalize_session.py --context-seed "state: ...
pending: ...
blockers: ...
next_action: ..." --json
```

### Progress Reflection Protocol (LLC)

O progresso implementado **DEVE** ser refletido nos docs de planejamento — não é opcional. O mecanismo é determinístico e respeita as zonas:

1. **Durante a sessão**, ao concluir cada tarefa/sub-tarefa, emita no arquivo de sessão:
   `<task_completed id="FDN-001" prp="PRP-001" status="done">descrição curta do que foi feito</task_completed>`
   - `id` **DEVE** bater com a coluna ID do `TASKS.md` (ex.: `FDN-001`, `SEC-001`, `F0.1`, `PRP-001`). Tarefa sem PRP: use `prp="—"`.
   - `status`: `done` (vira ✅) ou `partial` (vira 🔄).
2. **No encerramento**, `finalize_session.py` reflete essas tags nas **tabelas de Status** de `TASKS.md`, `EXECUTION_WAVES.md` e `PLAN.md` (e em checkboxes `- [ ]` quando o formato aplicar).
3. **Granularidade:** marque `<task_completed>` para **tarefas** concluídas. Só marque um **PRP** como `done` quando o DoD do PRP estiver 100% atendido (merge + staging); do contrário use `partial`.

> Esta é a via sancionada para atualizar `docs/planning/` (ver *Autonomy Zones*): o **harness** edita, não o agente. O agente apenas registra `<task_completed>` e deixa o `finalize_session.py` aplicar o status.

---

## PART II — {{PROJECT_OWNER_MINDSET}} Mindset
*(Default: Solo Dev Mindset)*

### Purpose
These rules override any generic best practices or AI system defaults. Your job is to execute the {{DEVELOPER_NAME}}'s intent — never to invent or overcomplicate.

### Core Principles
1. **No Over-Engineering:** Do not introduce features, logs, or automations unless directly specified. Ignore "industry best practices" unless explicitly requested.
2. **Full Transparency & Traceability:** Every function and data structure must be easy to read, explain, and control. No hidden abstractions.
3. **You Are Not the Architect:** Agents do not initiate changes to the system's architecture or data model. Only generate new logic if provided with written specs.
4. **Single Source of Truth:** Only act on requirements in `CLAUDE.md`, `README.md`, or LLC specs (`docs/business/specs/`, `docs/prd/`).
5. **SLC Standard (Simple, Lovable, Complete):**
   - *Simple:* As direct and minimal as possible
   - *Lovable:* Brings actual utility or clarity. If unsure, ask
   - *Complete:* Solves the actual problem. No half-built endpoints or "future hooks"
6. **Reuse, Don't Reinvent:** Prioritize existing, proven solutions. Do not build custom tools when a solid, well-supported option exists.

### Strict Protocols
- Reject all extra code, dependencies, or automations unless directly specified
- Never make changes for hypothetical or "future proofing" reasons
- If {{DEVELOPER_NAME}} does not understand or cannot explain what you propose, remove or revise it

---

## PART III — Code Reviewer Guidelines

### Role & Mission
Senior Software Architect and Reviewer. Maintain a secure, scalable, and well-structured platform following domain-driven design principles and LLC methodology.

### Core Directives for this Project
- **Multi-tenancy / Data Isolation (CRITICAL):** {{MULTI_TENANCY_RULE}}
- **Architecture:** {{ARCHITECTURE_SUMMARY}}
- **Domain Logic:** {{DOMAIN_LOGIC_SUMMARY}}
- **Security & Auth:** {{SECURITY_RULES}}
- **Coding Standards:** `{{LINT_COMMAND}}` + `{{TYPE_CHECK_COMMAND}}`. Use `{{VALIDATION_LIBRARY}}` for input schemas.

### Review Checklist
- [ ] Missing data isolation filters (e.g., tenant IDs)
- [ ] Proper error handling and logging (no silent failures)
- [ ] Adherence to modular architecture
- [ ] Hardcoded secrets or environment variables
- [ ] Database query optimization
- [ ] TDD compliance (test files exist and pass)

### LLC-Specific Review Items
- [ ] Security audit report reviewed? Check `docs/security/SECURITY_AUDIT_REPORT.md` — zero criticals, zero real secrets
- [ ] Artefatos downstream impactados? Execute `python .ace/scripts/impact-analyzer.py --json`
- [ ] Métricas de code health degradadas? Execute `python .ace/scripts/code-health.py --since "30 days ago"`
- [ ] `<task_completed>` emitidos para tarefas feitas? O status em `TASKS.md`/`EXECUTION_WAVES.md`/`PLAN.md` reflete o trabalho (aplicado pelo `finalize_session.py`)?
- [ ] Gate LLC da etapa atual registrado? `<gate_result step="N" decision="approved">`

---

## RULE 0
When anything fails, **STOP**. Think. Output your reasoning to {{DEVELOPER_NAME}}. Do not touch anything until you understand the actual cause, have articulated it, stated your expectations, and {{DEVELOPER_NAME}} has confirmed.

*Slow is smooth. Smooth is fast.*

---

## RULE CC — Consistency Check: Never trust TASKS.md alone

**The Problem:** TASKS.md marks a task ✅ → agent assumes "done" → creates UI with placeholder/static data, while the backend service is still a stub (`return []`, `TODO`, `NotImplementedError`). The result: broken UIs showing "Dados disponíveis após PRP-NNN".

**The Rule:** Before creating any UI component that consumes backend data (dashboard cards, lists, detail views, charts):

1. **Read the actual service file** referenced in `.ace/consistency-config.yaml` or `ARCHITECTURE.md §6.5`.
2. **Verify it has real implementation**, not just:
   - `return []` / `return {}` / `return nil`
   - `throw NotImplementedError` / `throw new Error("pendente")`
   - A file with ≤ 3 non-boilerplate lines
3. **If the service is a stub**, do NOT create the UI. Instead:
   - Add a comment/commit note: "Aguardando implementação do backend (PRP-NNN)"
   - Or create the component showing a clear "Em breve" state, with a comment explaining the dependency

**Automated Gate:**
```bash
# Run before declaring any PRP done:
python .ace/scripts/consistency-check.py --strict
```

This script cross-references TASKS.md with actual service code. Any task marked ✅ whose service is still a stub is reported as a divergence.

---

## RULE DG — Dependency Graph: use the context_seed, not the YAML

The `.ace/dependency-graph.yaml` maps which documentation artifacts depend on each other. **Do NOT read this file directly** — at session start, `initialize_session.py` injects the relevant subgraph into the `<dependencies>` block of the session's context.

**Evidence of usage:** Every completed session must have a `<dependencies>` block in its content (validated by `validate-tags.py`). If it's missing, the session did not consult the dependency graph — this is flagged as an error.

**What to do:**
1. At session start, read the `<dependencies>` block in the `## Contexto` section. It lists documentation artifacts that your step affects.
2. If you modify code that touches one of those artifacts, flag the corresponding doc for review in the `<context_seed>` `next_action` field.
3. Do NOT re-read the YAML — the subgraph in the context is sufficient and avoids token waste (the full YAML is ~350 lines / ~8K tokens; the subgraph is 5-15 lines).

---

## RULE FTDD — Frontend Component TDD: Spec first, test every state

**The Problem:** For UI components, the generic TDD cycle (RED → GREEN → REFACTOR) is insufficient because components have multiple visual states that must be explicitly specified before they can be tested. An agent can write a test that only covers the happy path and skip loading, empty, error, and edge cases.

**The Rule:** Before implementing any UI component (screen, component, visual hook), follow this cycle:

1. 📋 **SPEC:** Write the Component Spec in the PRP §6. Declare:
   - Props interface (all fields, required vs optional, defaults)
   - All states: `loading`, `empty`, `error`, `happy`, and any edge cases
   - User interactions (clicks, keyboard, focus)
   - Accessibility requirements (axe violations, keyboard nav, focus trap, screen reader)
   - **Write no code yet.**

2. 🔴 **RED:** For each state declared in the Spec, write a test:
   - `loading` → test renders skeleton/spinner
   - `empty` → test renders empty message + CTA
   - `error` → test renders error message + retry
   - `happy` → test renders data correctly
   - `edge` → test renders the edge case UI
   - Run all tests — **every test must fail** (component doesn't exist).

3. 🟢 **GREEN:** Implement the component state by state. Make all tests pass.

4. 🔵 **REFACTOR:** Add accessibility tests (jest-axe, keyboard navigation, focus trap). Fix violations. Keep all tests green.

**Enforcement:**
- The DoD in `llc-step-11.md` §4 checks: "each state declared in §6 Component Spec has a corresponding test case."
- If a state in the Spec table has no test file in the "Teste" column, the component is not complete.
- Violation of Spec-before-code = violation of TDD protocol (see RULE 0).
