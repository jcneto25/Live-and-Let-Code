# Live and Let Code (LLC)

Metodologia de desenvolvimento agentico que estrutura o ciclo completo de construcao de software — da ingestao de conhecimento de negocio ao deploy — em etapas discretas com gates de validacao humana. Projeto da Equipe LLC.

## Pipeline

**Step**:
Unidade atomica do pipeline LLC. Cada step tem entradas (artefatos), saidas (novos artefatos gerados), uma skill Markdown que instrui o agente, e um gate de validacao humana.
_Avoid_: Etapa, fase, estagio

**Gate**:
Checkpoint de validacao humana ao final de cada step. O agente propoe, o humano revisa uma checklist e aprova ou rejeita. 26 gates no total.
_Avoid_: Aprovacao, checkpoint, revisao

**PRP (Project Requirement Proposal)**:
Contrato auto-contido de trabalho que substitui user stories tradicionais. Cada PRP tem DoD, specs, estimativa e pode ser executado em worktree paralela.
_Avoid_: User story, ticket, task, feature

**Execution Wave**:
Grupo de PRPs sem dependencias mutuas, executaveis em paralelo via git worktrees.
_Avoid_: Sprint, iteracao, release

**Smart Skip**:
Motor de analise delta que determina quais steps precisam ser re-executados e quais podem ser pulados com uma nota, reutilizando artefatos anteriores.
_Avoid_: Skip, cache hit, incremental

**Grill Me**:
Protocolo de Q&A estruturado (maximo 8 perguntas) que o agente executa antes de gerar artefatos nas etapas de especificacao (steps 0.5-3). Identifica ambiguidades por ordem de criticidade.
_Avoid_: Interview, discovery, requirements gathering

## Contexto entre Sessoes

**ACE (Agentic Context Engineering)**:
Protocolo de continuidade entre sessoes de IA. Comprime o estado da sessao anterior em um `<context_seed>` (~300 tokens, 93% de compressao) e injeta na sessao seguinte. Gerido por `initialize_session.py` / `finalize_session.py`.
_Avoid_: Context window, memory, handoff

**Context Seed**:
Bloco de 4 campos (`state`, `pending`, `blockers`, `next_action`) que resume o estado de uma sessao ACE concluida. E a interface canonica de handoff entre agentes.
_Avoid_: Summary, handoff, resume

**Session**:
Unidade de trabalho registrada em `.ace/sessions/YYYY-MM-DD-NNN.md`. Cada sessao e imutavel apos criacao e contem deltas de arquivos, tags `<task_completed>`, e `<gate_result>`.
_Avoid_: Log, entry, record

## Arquitetura

**Thin Harness**:
CLI Python (`llc.py`, ~390 linhas) que orquestra o ciclo de vida de cada step: init session -> load skill -> invoke agent -> gate check -> finalize session. "Thin" por design: nao implementa tool-calling, apenas conecta as pecas existentes.
_Avoid_: Orchestrator, engine, runner

**Fitness Functions**:
Checagens automatizadas de conformidade arquitetural (21+ regras): DIP, isolamento de dominio, dependencias circulares, cobertura de interfaces, tamanho de use cases. Executadas via `fitness-functions.py`.
_Avoid_: Linter rules, quality gates, architecture tests

**Autonomy Zones**:
Sistema de 3 zonas que controla o que agentes podem modificar sem aprovacao humana: verde (seguro, ex.: `/tmp/`, testes), amarelo (cautela, ex.: `src/`, `lib/`), vermelho (escalar, ex.: schemas, `.env`, auth, artifacts LLC).
_Avoid_: Permissions, access levels, sandbox

**DIP (Dependency Inversion Principle)**:
Regra arquitetural obrigatoria: services dependem de interfaces (`IUserRepository`), nunca de implementacoes concretas (`PrismaService`). Verificado por fitness functions.
_Avoid_: DI, IoC, injection

## Wizard (TUI)

**Wizard**:
Interface TUI (Terminal UI) construida com Textual que serve como orquestrador visual do pipeline LLC. Espelha o `llc.py` CLI com layout de 3 paineis (sidebar de steps, contexto, output/gate) e checklists interativas nos gates.
_Avoid_: GUI, web interface, dashboard, frontend

**Wizard Step**:
Representacao visual de um step do pipeline na TUI Wizard. Exibe status (concluido, em andamento, pendente, gate pendente, falhou), contexto (skill, artefatos de entrada) e output do agente.

**Gate Checklist**:
Renderizacao interativa do gate na TUI Wizard. Cada item da checklist do `.ace/config/gates.json` vira um checkbox. O usuario marca cada item e decide "Aprovar" ou "Rejeitar". Suporta modo bypass (`--auto-approve`).

**Session Handoff**:
Mecanismo pelo qual a TUI Wizard transiciona entre o ciclo ACE (init/finalize) e o agente de IA: a TUI chama `llc.py` como subprocess (modo harness wrapper) ou, como fallback, exibe o prompt formatado para copia-cola no cliente de IA do usuario.
