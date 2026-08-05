# ADR-0002: LLC Wizard — TUI Orquestradora com HITL e Kanban Board

```yaml
---
adr: "0002"
title: "LLC Wizard — TUI Orquestradora com HITL e Kanban Board"
status: accepted
date: 2026-08-04
last_updated: 2026-08-05
deciders:
  - jcneto25
supersedes: null
related:
  - ADR-0001
  - ADR-0004   # Graph Engineering — KanbanBoardBuilder será refatorado para projetar do GraphEngine
  - ADR-0006   # Governança de Dependências — textual (N1), registrado em dependencies.yaml
  - "issue #22"
tags: [tui, textual, hitl, kanban, wizard, orchestrator]
compliance:
  fitness_functions: [arch, clean-code]
  gates: [5, 5a, 11.2]
implementation:
  prp: "docs/prps/PRP-WIZARD-1A.md"
---
```

---

## 1. Contexto

### 1.1 Situação Atual

O Live and Let Code (LLC) opera exclusivamente via CLI (`llc.py`) e agentes de IA em terminal. O usuário não possui visibilidade consolidada do progresso do pipeline: cada step é executado de forma isolada, o estado atual é inferido indiretamente via `.ace/index.json`, e a apresentação dos gates é textual e minimalista (`[A]provar / [R]ejeitar`). Não há indicador visual de "onde estou", "quanto falta", "o que está bloqueado" ou "o que já foi feito".

Três lacunas arquiteturais foram identificadas:

1. **Ausência de orquestração visual** — o pipeline é operado "às cegas" via terminal puro.
2. **HITL sub-especificado** — o pipeline possui múltiplos pontos de interação humana durante execução (gates, perguntas de clarificação, revisão de artefatos, confirmação de escopo, waivers), não apenas ao final dos steps.
3. **Ausência de visão de fluxo** — não há representação do trabalho em andamento, bloqueado e concluído para identificar gargalos e medir throughput.

### 1.2 Forças em Jogo

| Força | Direção |
|---|---|
| **Tool-agnostic** | O Wizard não pode acoplar a um cliente de IA específico |
| **Integridade ACE** | `initialize_session.py`/`finalize_session.py` são os únicos escritores sancionados |
| **Human-in-control** | IA propõe, humano dispõe; todo HITL deve ser auditável |
| **Zero mudança no harness** | O Wizard é consumidor, não modificador do `llc_harness` |
| **Preparação para fábrica** | Camada de dados deve antecipar paralelismo (Fase 2) sem retrabalho |
| **Escassez de espaço em terminal** | UIs ricas devem respeitar larguras de 80–120 colunas |

### 1.3 Escopo

Este ADR cobre a **Fase 1** do Wizard: TUI com HITL e painel Kanban. Não cobre multi-projeto, workflow engine (Temporal), ou execução paralela via Herdr (tratados em ADRs futuros).

---

## 2. Decisão

Construir o **LLC Wizard** — uma TUI interativa com **Textual** (Python 3.10+, async) que serve como orquestrador visual do pipeline LLC. Adiciona três capacidades ao `llc.py`: (a) navegação visual de steps com gates interativos; (b) HITL estruturado durante e ao final dos steps; (c) painel Kanban para visualização do fluxo.

### 2.1 Princípios de Design (não negociáveis)

| # | Princípio |
|---|---|
| **P1** | Read-only sobre **estado do pipeline**; write-via-API para **decisões humanas auditáveis** |
| **P2** | Integridade ACE preservada — sessões escritas apenas pelos scripts sancionados |
| **P3** | Feature parity com o CLI — tudo que `llc.py` faz, o Wizard faz |
| **P4** | Graceful degradation — sem Textual ou sem cliente de IA, cai para fallback copia-cola |
| **P5** | Single-project scope — 1 instância = 1 projeto = 1 pipeline |
| **P6** | Single source of truth — toda visão deriva do mesmo `PipelineDataSource` |
| **P7** | Interface `PipelineDataSource` estável — `KanbanBoardBuilder` recebe o Protocol, não a implementação concreta, preparando a migração para `GraphEngine` (ADR-0004) sem retrabalho |

### 2.2 Arquitetura em Camadas

```
┌────────────────────────────────────────────────────────────┐
│ APRESENTAÇÃO (Textual)                                       │
│   Sidebar(steps) · ContextPanel · OutputLog · GateChecklist  │
│   PromptCollector · KanbanBoard · DecisionModal               │
└──────────────────────────┬─────────────────────────────────┘
                           │ Signals / Events
┌──────────────────────────┴─────────────────────────────────┐
│ CONTROLE (app.py)                                            │
│   WizardApp: roteia eventos, aplica regras de negócio,       │
│   alterna visão Pipeline ↔ Kanban (toggle K)                 │
└──────────────────────────┬─────────────────────────────────┘
                           │ Commands (HITL)
┌──────────────────────────┴─────────────────────────────────┐
│ DECISÕES (decisions.py + commands.py)                        │
│   UserDecisionWriter · RealtimePromptCollector · QuestionRouter│
│   ApproveGate / AnswerQuestion / ArtifactReview / Waive cmds  │
└──────────────────────────┬─────────────────────────────────┘
                           │ KanbanBoardBuilder(PipelineDataSource)
┌──────────────────────────┴─────────────────────────────────┐
│ DADOS (data.py + kanban.py) — read-only                      │
│   PipelineDataSource (Protocol) · PipelineDataReader         │
│   KanbanCard · KanbanBoardBuilder                            │
└──────────────────────────┬─────────────────────────────────┘
                           │ asyncio.to_thread
┌──────────────────────────┴─────────────────────────────────┐
│ EXECUÇÃO (runner.py)                                         │
│   HarnessRunner (wrapper llc_harness) · FallbackRunner        │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────┐
│ LLC EXISTENTE (intocado)                                     │
│   llc_harness · llc_steps · initialize/finalize_session       │
│   .ace/sessions/*.md (append-only) · .ace/index.json          │
└────────────────────────────────────────────────────────────┘
```

### 2.3 Estrutura de Arquivos

```
.ace/scripts/
├── llc.py                          # novo subcomando: `llc wizard`
└── llc_wizard/
    ├── __init__.py
    ├── app.py                      # WizardApp (Textual App)
    ├── data.py                     # PipelineDataReader + PipelineDataSource Protocol
    ├── kanban.py                   # KanbanCard + KanbanBoardBuilder
    ├── decisions.py                # UserDecisionWriter + PromptCollector
    ├── commands.py                 # HITLCommand pattern
    ├── runner.py                   # HarnessRunner + FallbackRunner
    ├── widgets/
    │   ├── step_list.py
    │   ├── gate_checklist.py
    │   ├── progress_bar.py
    │   ├── output_log.py
    │   ├── prompt_widgets.py
    │   ├── decision_modal.py
    │   └── kanban_board.py
    ├── screens/
    │   ├── gate_decision.py
    │   ├── failure_recovery.py
    │   └── help_screen.py
    ├── styles/wizard.tcss
    └── tests/
        ├── test_data.py
        ├── test_kanban.py
        ├── test_decisions.py
        ├── test_commands.py
        ├── test_runner.py
        └── test_app.py
```

### 2.4 Decisão HITL — Write-via-API

6 categorias de decisão, todas tipadas, validadas e auditáveis:

| Tipo | Quando | Comando | Artefato |
|---|---|---|---|
| Gate Approval/Rejection | Fim do step | `ApproveGateCommand` / `RejectGateCommand` | `<gate_result>` |
| Question Answer | Durante execução | `AnswerQuestionCommand` | `<user_response type="question">` |
| Artifact Review | Durante step | `ReviewArtifactCommand` | `<user_response type="artifact_review">` |
| Scope Confirmation | Antes do step | `ConfirmScopeCommand` | `<user_response type="scope">` |
| Waiver | Gate com ressalva | `WaiveGateCommand` | `<gate_result waiver="true">` |
| Multi-option Choice | Durante step | `AnswerQuestionCommand` (options) | `<user_response type="question">` |

Toda decisão é serializada como tag XML **append-only** no arquivo de sessão (`.ace/sessions/{sid}.md`). O frontmatter permanece escrito exclusivamente pelos scripts sancionados.

### 2.5 Decisão Kanban Board

Painel Kanban acessível via **toggle `K`** (tela exclusiva, não painel permanente).

**Colunas e WIP:**

| Coluna | Status mapeado | WIP Limit |
|---|---|---|
| `BACKLOG` | `pending` | ∞ |
| `RUNNING` | `in_progress` | 1 no nível N1 (steps); múltiplos cards permitidos no nível N2 (PRPs em worktrees) |
| `AWAITING_HUMAN` | `gate_pending` + HITL pendente | ∞ (SLA) |
| `REWORK` | `failed` | 2 |
| `DONE` | `completed` | ∞ |
| `SKIPPED` | `skipped` | ∞ (colapsada por padrão) |

> **Nota sobre WIP=1:** o limite aplica ao nível N1 (pipeline macro). Múltiplos cards `RUNNING` são exibidos quando há PRPs paralelos em worktrees (nível N2). O paralelismo via worktrees já existe no LLC (ADR-0004 §1.1); bloquear a visualização seria uma regressão.

**Regras de movimento:** state-driven. Única exceção: reordenação dentro de `BACKLOG` via drag & drop.

**SLA humano:** cards em `AWAITING_HUMAN` há mais de **30 minutos** (configurável via `wizard.hitl_sla_minutes` em `gates.json`) recebem borda vermelha (`card-stale`).

### 2.6 Decisões Confirmadas

| # | Decisão | Valor |
|---|---|---|
| D1 | Coluna `SKIPPED` | Colapsada por padrão (expandível) |
| D2 | SLA humano para card stale | 30 minutos, configurável |
| D3 | Posição do Kanban | Tela exclusiva via toggle `K` |
| D4 | Swimlanes por wave | Adiadas para v2.0 (integração Herdr) |
| D5 | Export de métricas de fluxo | `--export-flow-metrics` incluído na v1.2 |
| D6 | Interface de dados | `KanbanBoardBuilder` recebe `PipelineDataSource` Protocol, nunca `PipelineDataReader` diretamente |

### 2.7 Layout da TUI

**Modo Pipeline:**
```
┌────────────────────────────────────────────────────────┐
│ Header: Barra de Progresso · Step Atual · Modo [K]     │
├──────────────┬─────────────────────────────────────────┤
│ Sidebar      │ Painel de Contexto                      │
│  ✅ 0.5      ├─────────────────────────────────────────┤
│  ✅ 1        │ Painel de Output / Gate / Prompt HITL   │
│  🔄 3        │                                         │
│  ⏳ 4        │                                         │
├──────────────┴─────────────────────────────────────────┤
│ Footer: [A]provar [R]ejeitar [K]anban [B]ypass [Q]uit  │
└────────────────────────────────────────────────────────┘
```

**Modo Kanban (toggle K):**
```
┌──────────────────────────────────────────────────────────────┐
│ Header: WIP total · Block Time · Stale count · [K] voltar    │
├────────┬────────┬──────────────┬────────┬────────┬──────────┤
│BACKLOG │RUNNING │AWAITING HUMAN│ REWORK │  DONE  │ SKIPPED ▸│
├────────┴────────┴──────────────┴────────┴────────┴──────────┤
│ Footer: [←→] colunas · [↑↓] cards · [Enter] abrir · [Q]uit  │
└──────────────────────────────────────────────────────────────┘
```

### 2.8 Navegação por Teclado

| Tecla | Modo Pipeline | Modo Kanban |
|---|---|---|
| `↑`/`↓` | Navegar steps | Navegar cards na coluna |
| `←`/`→` | — | Navegar entre colunas |
| `Enter` | Selecionar step / confirmar | Abrir ação do card |
| `A` | Aprovar gate | — |
| `R` | Rejeitar gate | — |
| `K` | Alternar para Kanban | Alternar para Pipeline |
| `B` | Toggle bypass | Toggle bypass |
| `Space` | Marcar checkbox | Marcar card |
| `Q`/`Ctrl+C` | Sair | Sair |

---

## 3. Consequências

### 3.1 Positivas

- Visibilidade consolidada do pipeline em tempo real.
- HITL tipado, validado e auditável via tags append-only.
- Coluna `AWAITING_HUMAN` + SLA expõe tempo de resposta humana como métrica de fluxo.
- `PipelineDataSource` Protocol prepara a migração para `GraphEngine` (ADR-0004) sem retrabalho no Kanban.
- Harness existente intocado; degradação graciosa sem Textual.

### 3.2 Negativas / Custos

- Nova dependência `textual` (N1, MIT, registrada em `dependencies.yaml` conforme ADR-0006).
- Textual 0.x pode ter breaking changes — mitigado por pin de versão.
- Kanban com 6 colunas exige terminal ≥ 120 cols — mitigado por scroll e colapso de `SKIPPED`.

### 3.3 Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Breaking changes do Textual | Pin `textual>=0.80.0,<1.0`; testes headless via `pilot` |
| `step_run` bloqueante | `asyncio.to_thread` + queue assíncrona |
| Cliente de IA sem stdout capturável | `FallbackRunner` sempre disponível |
| Dessincronização sidebar ↔ Kanban | Single source of truth via `PipelineDataSource` |
| Crash da TUI perde estado | Estado persistido em `.ace/`; restart recupera via `index.json` |
| `KanbanBoardBuilder` precisa retrabalho na Fase 3 | Resolvido por D6: recebe Protocol, não implementação |

---

## 4. Alternativas Consideradas

| Alternativa | Motivo da Rejeição |
|---|---|
| GUI Web/Browser | Viola terminal-first e zero-servidor (ADR-0001) |
| Apenas CLI melhorado | Insuficiente para HITL rico e Kanban |
| Herdr imediatamente | Agnóstico ao LLC; prematuro antes da fundação de dados |
| Workflow engine (Temporal) | Complexidade operacional; Fase 3, não Fase 1 |
| Kanban drag-livre | Quebra semântica state-driven |
| Kanban painel permanente | Consome espaço de terminal |

---

## 5. Compliance

### 5.1 Fitness Functions

- **Architecture:** DIP — `data.py` não importa de `app.py`; `KanbanBoardBuilder` depende do Protocol.
- **Clean Code:** funções < 50 linhas; sem god-classes.
- **Deep Clean:** CQS — `PipelineDataReader` query-only; `UserDecisionWriter` command-only.
- **Security:** input sanitizado antes de serializar em XML.
- **Dependency Governance (ADR-0006):** `textual` registrada em `dependencies.yaml` como N1, MIT, com fallback testado.

### 5.2 Gates Aplicáveis

| Gate | Aplicação |
|---|---|
| Gate 5 | Arquitetura documentada neste ADR |
| Gate 5a | Padrões: Command (HITL), Builder (Kanban), Protocol (runner + data) |
| Gate 9a | TDD obrigatório — RED → GREEN → REFACTOR por módulo |
| Gate 10.8 | Cobertura ≥ 85% em `data.py`, `kanban.py`, `decisions.py`, `runner.py` |
| Gate 11.2 | `prp-verify` e `consistency-check` passam antes do merge |

---

## 6. Métricas de Sucesso

| Categoria | Métrica | Meta |
|---|---|---|
| Técnica | Cobertura de testes | ≥ 85% |
| Técnica | Startup da TUI | < 2s |
| Técnica | Crash-free sessions | ≥ 99% |
| Fluxo | Cycle Time (BACKLOG → DONE) | baseline medido na v1.2 |
| Fluxo | Stale Rate (SLA estourado) | < 20% |
| Adoção | Uso do Fallback | < 20% |
| Valor | Tempo médio de pipeline | −15% vs. CLI puro |

---

## 7. Anexos

### 7.1 `PipelineDataSource` Protocol (contrato de interface)

```python
# llc_wizard/data.py
class PipelineDataSource(Protocol):
    """Contrato estável. PipelineDataReader implementa hoje.
    GraphEngine-backed adapter implementará na Fase 3 (ADR-0004).
    KanbanBoardBuilder depende deste Protocol, nunca da implementação."""
    def get_status(self) -> PipelineStatus: ...
    def get_gate_for_step(self, step_id: str) -> Optional[GateInfo]: ...
    def get_status_since(self, step_id: str) -> datetime: ...
    def get_pending_hitl(self) -> list[PendingHITL]: ...
```

### 7.2 Formato de Serialização HITL (XML append-only)

```xml
<user_response type="question" question_id="q-123" timestamp="2026-08-04T14:32:10">
  <question>Qual o tipo de banco de dados preferido?</question>
  <answer>Postgres</answer>
</user_response>

<gate_result approved="true" waiver="true" timestamp="2026-08-04T15:10:05">
  <waiver_note>Performance aceitável porque...</waiver_note>
</gate_result>
```

### 7.3 Configuração do Wizard

```json
{
  "wizard": {
    "hitl_sla_minutes": 30,
    "kanban": {
      "skipped_collapsed_by_default": true,
      "wip_limits": { "running": 1, "rework": 2 }
    },
    "export": { "flow_metrics": true }
  }
}
```

---

## 8. Implementação

O breakdown tático de tasks TDD (WP0–WP5), fixtures, exemplos RED→GREEN→REFACTOR e backlog ordenado com estimativas estão em:

**`docs/prps/PRP-WIZARD-1A.md`**

ADRs documentam o *porquê*. PRPs documentam o *como* e *o quê* executar.

| Fase | PRP | Estimativa |
|------|-----|------------|
| 1A MVP | PRP-WIZARD-1A | 4 semanas |
| 1B HITL | PRP-WIZARD-1B | +2 semanas |
| 1C Reviews | PRP-WIZARD-1C | +2 semanas |
| v1.1 Kanban UI | PRP-WIZARD-1.1 | +2 semanas |
| v1.2 Drag+Métricas | PRP-WIZARD-1.2 | +1 semana |
| v2.0 Herdr | PRP-WIZARD-2.0 | Fase 2 |

---

## 9. Registro de Aprovação

| Decisor | Papel | Data |
|---|---|---|
| jcneto25 | Owner / Arquiteto | 2026-08-04 |

**Status:** `accepted`
**Revisado em:** 2026-08-05 — separado breakdown de tasks para PRP-WIZARD-1A; adicionado P7 e D6 (Protocol `PipelineDataSource`); corrigido WIP limit (N1 vs N2); adicionado referência ADR-0006.
