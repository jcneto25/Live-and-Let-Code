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

## Governance Conversion

**Governance Conversion**:
Processo de converter padrões de falha agentica observados em governança durável e explícita. Ciclo: execução → falha estrutural → conversão em governança → propagação para próximas execuções. Substep formal 11.4 do pipeline LLC.
_Avoid_: Learnings, lessons learned, improvement process

**Defeito Local**:
Erro ou defeito isolado e pontual que não indica necessariamente uma lacuna sistêmica no ambiente de engenharia.
_Avoid_: Bug, incident

**Falha Estrutural**:
Falha interpretada como evidência de abstração, salvaguarda ou modelo fraco/ausente no ambiente de engenharia. Representa uma classe recorrente de erro impossível de prever totalmente de forma ex-ante.
_Avoid_: Bug recorrente, systemic issue, recurring error

**Resposta Arquitetural**:
Tipo de resposta a uma falha estrutural que elimina a classe de falha por construção (ex.: modelo tipado, componente catalog, seam canônico). Após instalada, a falha não pode mais ser expressa pelo agente.
_Avoid_: Fix arquitetural, structural fix

**Resposta de Controle**:
Tipo de resposta a uma falha estrutural que detecta a falha após ocorrer (ex.: lint, fitness function, teste, gate). Não elimina a possibilidade, mas barra ou sinaliza a falha antes que chegue a produção.
_Avoid_: Check, validation, guard

**Controle Probabilístico**:
Mecanismo de governança que orienta o comportamento do agente sem garantia determinística. Ex.: skills, prompts, brief templates, steering files. Útil quando a classe de falha tem baixo impacto, não é formalizável, ou o custo de automatizar supera o benefício.
_Avoid_: Soft control, guideline, suggestion

**Controle Determinístico**:
Mecanismo de governança que falha ou bloqueia de forma determinística se violado. Ex.: hooks, lints, types, fitness functions, merge/deploy gates. Meta preferencial para respostas a falhas estruturais de alto impacto.
_Avoid_: Hard control, hard gate, enforcement

**GOV (Governance Artifact)**:
Artefato imortal em `docs/governance/GOV-NNN-<slug>.md` que registra uma falha estrutural e o mecanismo instalado em resposta. Ciclo de vida: **open** (identificada, sem mecanismo) → **addressed** (mecanismo instalado, monitorando) → **closed** (sem reincidência por 3 PRPs). Pode reabrir se a mesma classe de falha reaparecer.
_Avoid_: Incident report, post-mortem, failure log

**Autoridade de Conversão**:
Regra de quem pode promover uma falha estrutural em novo mecanismo de governança. Qualquer operador pode registrar um GOV (open); a promoção para guardrail/lint/fitness function/skill novo exige validação humana em gate. A instalação do mecanismo é zona 🔴.
_Avoid_: Approval, ownership, governance authority

**Documento de Análise (article-parallel-llc.md)**:
Documento `docs/article-parallel-llc.md` que faz o paralelo entre o artigo "Cheap Code, Costly Judgment" (Davis et al.) e o workflow LLC. Identifica convergências, lacunas e 7 prioridades de evolução da metodologia, sendo a principal a institucionalização do loop de Governance Conversion.

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
