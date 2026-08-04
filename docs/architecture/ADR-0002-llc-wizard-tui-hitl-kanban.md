A ferramenta de extração está temporariamente indisponível, mas já consolidei todas as informações necessárias das análises anteriores e das convenções do repositório (formato do `ADR_TEMPLATE.md`: contexto → decisão → consequências → alternativas → compliance, com arquivos em `docs/architecture/adr/ADR-*.md`). Vou gerar o ADR-0002 oficial seguindo essas convenções e incorporando suas 5 decisões confirmadas.

---

# ADR-0002: LLC Wizard — TUI Orquestradora com HITL e Kanban Board

**Arquivo:** `docs/architecture/adr/ADR-0002-llc-wizard-tui-hitl-kanban.md`

```yaml
---
adr: "0002"
title: "LLC Wizard — TUI Orquestradora com HITL e Kanban Board"
status: accepted
date: 2026-08-04
deciders:
  - jcneto25
  - claude
supersedes: null
related:
  - ADR-0001
  - "issue #22"
tags: [tui, textual, hitl, kanban, wizard, orchestrator]
compliance:
  fitness_functions: [arch, clean-code]
  gates: [5, 5a, 11.2]
---
```

---

## 1. Contexto

### 1.1 Situação Atual

O Live and Let Code (LLC) opera exclusivamente via CLI (`llc.py`) e agentes de IA em terminal. O usuário não possui visibilidade consolidada do progresso do pipeline: cada step é executado de forma isolada, o estado atual é inferido indiretamente via `.ace/index.json`, e a apresentação dos gates é textual e minimalista (`[A]provar / [R]ejeitar`). Não há indicador visual de "onde estou", "quanto falta", "o que está bloqueado" ou "o que já foi feito".

Adicionalmente, três lacunas arquiteturais foram identificadas durante a especificação:

1. **Ausência de orquestração visual** — o pipeline é operado "às cegas" via terminal puro.
2. **HITL sub-especificado** — a spec inicial tratou o Wizard como *read-only*, mas o pipeline possui múltiplos pontos de interação humana durante execução (gates, perguntas de clarificação, revisão de artefatos, confirmação de escopo, waivers), não apenas ao final dos steps.
3. **Ausência de visão de fluxo** — não há representação do trabalho em andamento, bloqueado e concluído que permita identificar gargalos e medir throughput — requisito fundamental para a evolução do LLC rumo a uma *fábrica agentica de software*.

### 1.2 Forças em Jogo

| Força | Direção |
|---|---|
| **Tool-agnostic** | O Wizard não pode acoplar a um cliente de IA específico |
| **Integridade ACE** | `initialize_session.py`/`finalize_session.py` são os únicos escritores sancionados de sessões |
| **Human-in-control** | IA propõe, humano dispõe; todo HITL deve ser auditável |
| **Zero mudança no harness** | O Wizard é consumidor, não modificador do `llc_harness` |
| **Preparação para fábrica** | A camada de dados deve antecipar paralelismo (Fase 2/Herdr) sem retrabalho |
| **Escassez de espaço em terminal** | UIs ricas devem respeitar larguras de 80–120 colunas |

### 1.3 Escopo

Este ADR cobre a **Fase 1** da evolução do LLC: o Wizard TUI com suporte completo a HITL e um painel Kanban de fluxo. Não cobre multi-projeto, workflow engine (Temporal), ou execução paralela via Herdr (Fases 2 e 3, tratadas em ADRs futuros).

---

## 2. Decisão

Construir o **LLC Wizard** — uma TUI interativa com o framework **Textual** (Python 3.10+, async) que serve como orquestrador visual do pipeline LLC. O Wizard espelha o `llc.py` CLI e adiciona três capacidades: (a) navegação visual de steps com gates interativos; (b) recebimento estruturado de feedback humano (HITL) durante e ao final dos steps; e (c) um painel Kanban para visualização do fluxo de trabalho.

### 2.1 Princípios de Design (não negociáveis)

| # | Princípio |
|---|---|
| **P1** | Read-only sobre **estado do pipeline**; write-via-API para **decisões humanas auditáveis** |
| **P2** | Integridade ACE preservada — sessões escritas apenas pelos scripts sancionados |
| **P3** | Feature parity com o CLI — tudo que `llc.py` faz, o Wizard faz |
| **P4** | Graceful degradation — sem Textual ou sem cliente de IA, cai para fallback copia-cola |
| **P5** | Single-project scope — 1 instância = 1 projeto = 1 pipeline |
| **P6** | Single source of truth — toda visão (sidebar, Kanban) deriva do mesmo `PipelineDataReader` |

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
                           │ KanbanBoardBuilder
┌──────────────────────────┴─────────────────────────────────┐
│ DADOS (data.py + kanban.py) — read-only                      │
│   PipelineDataReader · KanbanCard · KanbanBoardBuilder        │
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
└── llc_wizard/                     # NOVO pacote
    ├── __init__.py
    ├── app.py                      # WizardApp (Textual App)
    ├── data.py                     # PipelineDataReader (read-only)
    ├── kanban.py                   # KanbanCard + KanbanBoardBuilder
    ├── decisions.py                # UserDecisionWriter + PromptCollector
    ├── commands.py                 # HITLCommand pattern
    ├── runner.py                   # HarnessRunner + FallbackRunner
    ├── widgets/
    │   ├── step_list.py
    │   ├── gate_checklist.py
    │   ├── progress_bar.py
    │   ├── output_log.py
    │   ├── prompt_widgets.py       # input HITL em tempo real
    │   ├── decision_modal.py       # waiver / feedback
    │   └── kanban_board.py         # board + coluna + card
    ├── screens/
    │   ├── gate_decision.py
    │   ├── failure_recovery.py
    │   └── help_screen.py
    ├── styles/wizard.tcss          # Textual CSS
    └── tests/
        ├── test_data.py
        ├── test_kanban.py
        ├── test_decisions.py
        ├── test_commands.py
        ├── test_runner.py
        └── test_app.py
```

### 2.4 Decisão HITL — Write-via-API

O Wizard recebe feedback humano através de **6 categorias de decisão**, todas tipadas, validadas e auditáveis:

| Tipo | Quando | Comando | Artefato |
|---|---|---|---|
| Gate Approval/Rejection | Fim do step | `ApproveGateCommand` / `RejectGateCommand` | `<gate_result>` |
| Question Answer | Durante execução | `AnswerQuestionCommand` | `<user_response type="question">` |
| Artifact Review | Durante step | `ReviewArtifactCommand` | `<user_response type="artifact_review">` |
| Scope Confirmation | Antes do step | `ConfirmScopeCommand` | `<user_response type="scope">` |
| Waiver | Gate com ressalva | `WaiveGateCommand` | `<gate_result waiver="true">` |
| Multi-option Choice | Durante step | `AnswerQuestionCommand` (options) | `<user_response type="question">` |

**Mecanismo de persistência:** toda decisão é serializada como tag XML **append-only** no arquivo de sessão (`.ace/sessions/{sid}.md`), preservando histórico imutável e rastreabilidade total. O frontmatter permanece escrito exclusivamente pelos scripts sancionados.

**Contratos principais:**

```python
# decisions.py — write-only API
class UserDecisionWriter:
    async def submit_gate_decision(self, d: GateDecision) -> None: ...
    async def submit_question_answer(self, a: QuestionAnswer) -> None: ...
    async def submit_artifact_review(self, r: ArtifactReview) -> None: ...
    async def submit_scope_confirmation(self, s: ScopeConfirmation) -> None: ...

# decisions.py — coleta em tempo real
class RealtimePromptCollector:
    async def request_input(self, prompt: PromptRequest) -> str: ...
    def submit_response(self, prompt_id: str, response: str) -> None: ...

# commands.py — pattern Command com validação
class HITLCommand(ABC):
    def validate(self) -> bool: ...
    async def execute(self, writer: UserDecisionWriter) -> None: ...
```

### 2.5 Decisão Kanban Board

O Wizard inclui um painel Kanban como **segunda lente** sobre o estado do pipeline, acessível via **toggle `K`** (tela exclusiva, não painel permanente).

**Colunas e mapeamento de estados:**

| Coluna | StepStatus | WIP Limit |
|---|---|---|
| `BACKLOG` | `pending` | ∞ |
| `RUNNING` | `in_progress` | 1 (MVP) |
| `AWAITING_HUMAN` | `gate_pending` + HITL pendente | ∞ (SLA) |
| `REWORK` | `failed` | 2 |
| `DONE` | `completed` | ∞ |
| `SKIPPED` | `skipped` | ∞ (**colapsada por padrão**) |

**Card types:** `WORK` (steps/PRPs/tasks) e `DECISION` (solicitações HITL). A coluna `AWAITING_HUMAN` agrega ambos os gates pendentes e pedidos HITL, ordenados por **tempo de espera** (mais antigo no topo), transformando o humano em um worker com fila e SLA.

**Regras de movimento:**
- Movimento de cards é **state-driven** (dirigido por mudança de estado), não drag-livre.
- **Única exceção:** reordenação de prioridade **dentro de `BACKLOG`** via drag & drop.
- Tentativa de mover card para outra coluna exibe notificação explicativa.

**SLA humano:** cards em `AWAITING_HUMAN` há mais de **30 minutos** (valor **configurável** via `.ace/config/gates.json` → `wizard.hitl_sla_minutes`) recebem destaque visual (borda vermelha, classe `card-stale`).

**Derivação:** o board é construído pelo `KanbanBoardBuilder` a partir do mesmo `PipelineDataReader` (single source of truth), garantindo consistência entre sidebar e Kanban.

### 2.6 Decisões Confirmadas (Registro Explícito)

As seguintes decisões de design foram confirmadas pelo decisor e são vinculantes para a implementação:

| # | Decisão | Valor Confirmado |
|---|---|---|
| D1 | Coluna `SKIPPED` | **Colapsada por padrão** (expandível sob demanda) |
| D2 | SLA humano para card stale | **30 minutos**, valor **configurável** |
| D3 | Posição do Kanban | **Tela exclusiva via toggle `K`** (não painel permanente) |
| D4 | Swimlanes por wave | **Adiadas para v2.0**, junto com integração Herdr |
| D5 | Export de métricas de fluxo | **`--export-flow-metrics` incluído na v1.2** |

### 2.7 Layout da TUI

**Modo Pipeline (padrão):**

```
┌────────────────────────────────────────────────────────┐
│ Header: Barra de Progresso · Step Atual · Modo [K]     │
├──────────────┬─────────────────────────────────────────┤
│ Sidebar      │ Painel de Contexto                      │
│ (Steps)      │ (skill, artefatos, inputs)              │
│  ✅ 0.5      ├─────────────────────────────────────────┤
│  ✅ 1        │ Painel de Output / Gate                 │
│  🔄 3        │ (log do agente, gate checklist,         │
│  ⏳ 4        │  prompt HITL)                           │
├──────────────┴─────────────────────────────────────────┤
│ Footer: [A]provar [R]ejeitar [K]anban [B]ypass [Q]uit  │
└────────────────────────────────────────────────────────┘
```

**Modo Kanban (toggle `K`):**

```
┌──────────────────────────────────────────────────────────────┐
│ Header: WIP total · Block Time · Stale count · [K] voltar    │
├────────┬────────┬──────────────┬────────┬────────┬──────────┤
│BACKLOG │RUNNING │AWAITING HUMAN│ REWORK │  DONE  │ SKIPPED ▸│
│ ⏳ 4    │ 🔄 3   │ ⚠️ Gate 2.5  │ ❌ 5   │ ✅ 0.5 │ (colap.) │
│ ⏳ 5    │        │ ❓ Qual BD?  │        │ ✅ 1   │          │
│ ⏳ 5a   │        │ 📄 Review ADR│        │ ✅ 2   │          │
├────────┴────────┴──────────────┴────────┴────────┴──────────┤
│ Footer: [←→] colunas · [↑↓] cards · [Enter] abrir · [Q]uit  │
└──────────────────────────────────────────────────────────────┘
```

### 2.8 Navegação por Teclado

| Tecla | Ação (Pipeline) | Ação (Kanban) |
|---|---|---|
| `↑`/`↓` | Navegar steps | Navegar cards na coluna |
| `←`/`→` | — | Navegar entre colunas |
| `Enter` | Selecionar step / confirmar | Abrir ação do card |
| `A` | Aprovar gate | — |
| `R` | Rejeitar gate | — |
| `K` | Alternar para Kanban | Alternar para Pipeline |
| `B` | Toggle bypass | Toggle bypass |
| `Space` | Marcar checkbox | Marcar card (batch futuro) |
| `Q`/`Ctrl+C` | Sair | Sair |

---

## 3. Consequências

### 3.1 Positivas

- **Visibilidade consolidada:** usuário enxerga progresso, bloqueios e histórico em tempo real.
- **HITL estruturado e auditável:** toda decisão humana é tipada, validada e persistida como tag append-only.
- **Identificação de gargalos:** a coluna `AWAITING_HUMAN` + SLA expõe o tempo de resposta humana como métrica de fluxo.
- **Preparação para fábrica:** o `KanbanBoardBuilder` e o modelo `KanbanCard` antecipam paralelismo (Fase 2/Herdr) sem retrabalho.
- **Baixo risco:** harness existente intocado; Wizard é camada consumidora com fallback robusto.
- **Tool-agnostic preservado:** Wizard não acopla a cliente de IA específico.

### 3.2 Negativas / Custos

- **Nova dependência:** `textual` adicionado a `requirements.txt` (mitigado por lazy-loading e fallback).
- **Complexidade de UI:** Textual em versão 0.x pode ter breaking changes (mitigado por pin de versão e testes de integração).
- **Espaço de terminal:** Kanban com 6 colunas exige largura ≥ 120 cols para conforto (mitigado por scroll horizontal e colapso de `SKIPPED`).
- **Superfície de teste ampliada:** novos módulos `decisions.py`, `commands.py`, `kanban.py` exigem cobertura ≥ 85%.

### 3.3 Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Breaking changes do Textual | Pin `textual>=0.80.0,<1.0`; testes headless via `pilot` |
| `step_run` bloqueante | `asyncio.to_thread` + queue assíncrona de streaming |
| Cliente de IA sem stdout capturável | `FallbackRunner` sempre disponível |
| `input()` bloqueante em gates | Wizard substitui `gate_check()` por UI própria; mantém `session_end()` |
| Dessincronização sidebar ↔ Kanban | Single source of truth (`PipelineDataReader`) |
| Crash da TUI perde estado | Estado persistido em `.ace/`; restart recupera via `index.json` |
| Drag & drop quebra semântica | Movimento state-driven; drag restrito ao `BACKLOG` |

---

## 4. Alternativas Consideradas

| Alternativa | Descrição | Motivo da Rejeição |
|---|---|---|
| **GUI Web/Browser** | Dashboard web com WebSocket | Rejeitada no ADR-0001; viola princípio terminal-first e zero-servidor |
| **Apenas CLI melhorado** | Enriquecer saída textual do `llc.py` | Insuficiente para HITL rico e Kanban; não resolve visibilidade consolidada |
| **Adotar Herdr imediatamente (Fase 2)** | Usar multiplexer externo como orquestrador | Herdr é agnóstico ao LLC (não conhece steps/gates); prematuro antes da fundação de dados do Wizard |
| **Workflow engine (Temporal)** | Orquestrar steps como workflows duráveis | Complexidade operacional alta; apropriado para Fase 3, não para Fase 1 |
| **Kanban com drag-livre** | Permitir mover cards livremente entre colunas | Quebra semântica state-driven do pipeline; rejeitado em favor de movimento por estado |
| **Kanban como painel permanente** | Board sempre visível abaixo do pipeline | Consome espaço de terminal; toggle `K` preserva espaço no modo Pipeline |
| **Swimlanes por wave no MVP** | Agrupar cards por wave desde o início | Prematuro sem paralelismo real; adiado para v2.0 com Herdr |

---

## 5. Compliance

### 5.1 Fitness Functions (Gate 5c / 11.3)

O código do Wizard deve passar nas verificações de `fitness-functions.py`:

- **Architecture:** separação em camadas (data/decisions/runner/app); `data.py` não importa de `app.py` (DIP).
- **Clean Code:** funções < 50 linhas, nomeação consistente, sem god-classes.
- **Deep Clean:** CQS respeitado (`PipelineDataReader` query-only; `UserDecisionWriter` command-only); sem flags booleanas em assinaturas públicas.
- **Security:** nenhum segredo em código; input do usuário sanitizado antes de serializar em XML.

### 5.2 Gates Aplicáveis

| Gate | Aplicação |
|---|---|
| Gate 5 | Arquitetura do Wizard documentada neste ADR |
| Gate 5a | Padrões: Command (HITL), Builder (Kanban), Protocol (Runner) |
| Gate 9a (TDD) | Todo módulo novo segue RED → GREEN → REFACTOR |
| Gate 10.8 | Cobertura de testes ≥ 85% em `data.py`, `kanban.py`, `decisions.py`, `runner.py` |
| Gate 11.2 | `prp-verify` e `consistency-check` passam antes do merge |

### 5.3 TDD / FTDD Obrigatórios

Testes FTDD para cada estado visual (Pipeline e Kanban):

**Pipeline:** tela inicial, step em execução, gate pendente, gate aprovado, gate rejeitado, bypass, smart skip, fallback, pipeline concluído, navegação por teclado.

**Kanban:** board inicial, card em RUNNING, gate HITL em AWAITING_HUMAN, pergunta HITL, SLA estourado (`card-stale`), rejeição → REWORK, aprovação → DONE, smart skip → SKIPPED colapsado, WIP limit atingido, drag no backlog vs. drag bloqueado, toggle `K` preserva seleção.

**HITL:** resposta a pergunta durante step, revisão de artefato com feedback, waiver exige nota mínima, confirmação de escopo bloqueia início, múltiplos prompts preservam ordem, agente continua após resposta.

---

## 6. Roadmap de Entrega

| Fase | Entrega | Estimativa |
|---|---|---|
| **1A (MVP)** | `data.py` + `runner.py` + `app.py` + sidebar + gates + `kanban.py` (modelo) | 4 semanas |
| **1B** | HITL completo: `decisions.py` + `commands.py` + `RealtimePromptCollector` | +2 semanas |
| **1C** | Artifact Review + Scope Confirmation + rerun automático | +2 semanas |
| **v1.1** | Kanban UI (board + toggle `K` + SLA + WIP) | +2 semanas |
| **v1.2** | Drag & drop no backlog + `--export-flow-metrics` + temas | +1 semana |
| **v2.0** | Swimlanes por wave + cards de PRPs paralelos (integração Herdr) | Fase 2 |

**Critério de conclusão do MVP (1A):** `llc wizard --from 0` executa o pipeline completo com gates interativos, fallback funcional, todos os testes verdes.

---

## 7. Métricas de Sucesso

| Categoria | Métrica | Meta |
|---|---|---|
| Técnica | Cobertura de testes | ≥ 85% |
| Técnica | Startup da TUI | < 2s |
| Técnica | Crash-free sessions | ≥ 99% |
| Fluxo | Cycle Time (BACKLOG → DONE) | baseline medido na v1.2 |
| Fluxo | Block Time (AWAITING_HUMAN) | baseline medido na v1.2 |
| Fluxo | Stale Rate (SLA estourado) | < 20% |
| Adoção | Uso do Fallback | < 20% |
| Valor | Tempo médio de pipeline | −15% vs. CLI puro |
| Valor | Gates rejeitados | −10% |

---

## 8. Anexos

### 8.1 Modelo de Dados Kanban (contrato)

```python
class KanbanColumn(str, Enum):
    BACKLOG; RUNNING; AWAITING_HUMAN; REWORK; DONE; SKIPPED

class CardType(str, Enum):
    WORK; DECISION

@dataclass(frozen=True)
class KanbanCard:
    id: str
    title: str
    card_type: CardType
    column: KanbanColumn
    step_id: Optional[str]
    session_id: Optional[str]
    entered_column_at: datetime
    agent: Optional[str]
    meta: dict

    @property
    def time_in_column(self) -> timedelta: ...

    @property
    def is_stale(self) -> bool:
        sla = load_config().get("wizard", {}).get("hitl_sla_minutes", 30)
        return (self.column == KanbanColumn.AWAITING_HUMAN
                and self.time_in_column > timedelta(minutes=sla))
```

### 8.2 Formato de Serialização HITL (XML append-only)

```xml
<user_response type="question" question_id="q-123" timestamp="2026-08-04T14:32:10">
  <question>Qual o tipo de banco de dados preferido?</question>
  <answer>Postgres</answer>
</user_response>

<user_response type="artifact_review" approved="false" timestamp="2026-08-04T14:45:22">
  <feedback>
    <item>ADR não menciona estratégia de backup</item>
  </feedback>
</user_response>

<gate_result approved="true" waiver="true" timestamp="2026-08-04T15:10:05">
  <waiver_note>Performance aceitável porque...</waiver_note>
</gate_result>
```

### 8.3 Configuração do Wizard (`.ace/config/gates.json`)

```json
{
  "wizard": {
    "hitl_sla_minutes": 30,
    "kanban": {
      "skipped_collapsed_by_default": true,
      "wip_limits": { "running": 1, "rework": 2 }
    },
    "export": {
      "flow_metrics": true
    }
  }
}
```

---

## 9. Registro de Aprovação

| Decisor | Papel | Data |
|---|---|---|
| jcneto25 | Owner / Arquiteto | 2026-08-04 |
| claude | Co-autor da especificação | 2026-08-04 |

**Status:** `accepted`
**Próximo ADR previsto:** ADR-0003 — Integração Herdr para execução paralela de PRPs (Fase 2).

---

# 🔨 Fase 1A (MVP) — Quebra em Tasks TDD Granulares

**Referência normativa:** ADR-0002 · Issue LLC Wizard · `AGENTS.md` (TDD Enforcement Protocol)

**Protocolo obrigatório por task:** 🔴 RED (teste falha, mostrar saída) → 🟢 GREEN (código mínimo passa, mostrar saída) → 🔵 REFACTOR (manter verde).

---

## 0. Mapa de Dependências e Ordenação

```
WP0 Setup ─────────────────────────────────────────────────┐
                                                            │
WP1 data.py ──────────┐                                     │
   (foundation)       │                                     │
                      ├──► WP2 kanban.py (modelo)           │
                      │         (deriva de data.py)         │
                      │                                     │
                      └──► WP3 runner.py                    │
                                (usa data.py + llc_harness) │
                                                            │
WP1 + WP3 ─────────────► WP4 widgets + app.py               │
                                (consome data + runner)     │
                                                            │
WP4 ───────────────────► WP5 integração CLI `llc wizard`    │
```

**Regra de ouro:** nenhuma task GREEN pode ser declarada sem a saída do teste exibida. Nenhum módulo importa de camada superior (DIP): `data.py` não conhece `app.py`; `kanban.py` conhece apenas `data.py`.

**Estimativa total da Fase 1A:** ~4 semanas (20 tasks, ~13 dias-homem de código + testes).

---

## 📦 WP0 — Setup do Pacote (Pré-TDD)

### Task 0.1 — Estrutura do pacote + dependências + config pytest

**Objetivo:** Criar `.ace/scripts/llc_wizard/`, `requirements.txt`, e config de teste. Não há TDD aqui (é infraestrutura), mas é pré-requisito.

**Ações:**
```
.ace/scripts/llc_wizard/
├── __init__.py
├── tests/
│   ├── __init__.py
│   └── conftest.py        # fixtures compartilhadas
requirements.txt           # raiz do repo
pytest.ini                 # ou pyproject section
```

`requirements.txt`:
```txt
click>=8.0
pyyaml>=6.0
textual>=0.80.0,<1.0
```

`conftest.py` (fixture base reutilizada por todos os WPs):
```python
# .ace/scripts/llc_wizard/tests/conftest.py
import pytest
import json
from pathlib import Path


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Cria uma estrutura .ace/ mínima e isolada para testes."""
    ace = tmp_path / ".ace"
    (ace / "config").mkdir(parents=True)
    (ace / "sessions").mkdir(parents=True)

    # index.json vazio
    (ace / "index.json").write_text(json.dumps({"sessions": []}), encoding="utf-8")

    # gates.json mínimo
    (ace / "config" / "gates.json").write_text(json.dumps({}), encoding="utf-8")
    return tmp_path


@pytest.fixture
def make_index():
    """Factory para popular .ace/index.json com sessões."""
    def _make(root: Path, sessions: list[dict]):
        (root / ".ace" / "index.json").write_text(
            json.dumps({"sessions": sessions}), encoding="utf-8"
        )
    return _make


@pytest.fixture
def make_gates():
    """Factory para popular .ace/config/gates.json."""
    def _make(root: Path, gates: dict):
        (root / ".ace" / "config" / "gates.json").write_text(
            json.dumps(gates), encoding="utf-8"
        )
    return _make
```

**Definition of Done:** `pytest .ace/scripts/llc_wizard/tests/ -v` roda e reporta `no tests ran` sem erro de import.

**Esforço:** 0,5 dia · **Depende de:** nada.

---

## 📦 WP1 — `data.py` (Camada de Acesso a Dados, read-only)

> **Alvo de cobertura:** ≥ 85%. Todos os dataclasses são `frozen=True` (imutabilidade para UI reativa).

### Task 1.1 — `StepStatus` enum e `StepInfo` dataclass

**🔴 RED — escreva o teste primeiro:**
```python
# tests/test_data.py
from llc_wizard.data import StepStatus, StepInfo


def test_step_status_has_all_seven_states():
    assert {s.value for s in StepStatus} == {
        "pending", "in_progress", "gate_pending",
        "completed", "failed", "skipped", "excluded",
    }


def test_step_info_is_frozen():
    step = StepInfo(
        id="5", name="Arquitetura", status=StepStatus.PENDING,
        in_pipeline=True, depends_on=["4"], current_session_id=None,
        artifacts_output=["docs/architecture/ARCHITECTURE.md"],
    )
    import dataclasses, pytest
    with pytest.raises(dataclasses.FrozenInstanceError):
        step.status = StepStatus.COMPLETED  # type: ignore[misc]
```
**Saída esperada (RED):** `ModuleNotFoundError: No module named 'llc_wizard.data'` ou `ImportError`.

**🟢 GREEN — implementação mínima:**
```python
# llc_wizard/data.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class StepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    GATE_PENDING = "gate_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_IN_PIPELINE = "excluded"


@dataclass(frozen=True)
class StepInfo:
    id: str
    name: str
    status: StepStatus
    in_pipeline: bool
    depends_on: list[str]
    current_session_id: Optional[str]
    artifacts_output: list[str]
```

**🔵 REFACTOR:** adicionar docstrings; garantir `from __future__ import annotations` se necessário.

**DoD:** 2 testes verdes. **Esforço:** 0,5 dia.

---

### Task 1.2 — `GateItem` e `GateInfo` dataclasses

**🔴 RED:**
```python
from llc_wizard.data import GateItem, GateInfo


def test_gate_item_defaults_to_unchecked():
    item = GateItem(id="g1", description="7 Especificações completas", required=True)
    assert item.checked is False
    assert item.required is True


def test_gate_info_aggregates_required_met():
    items = [
        GateItem(id="a", description="x", required=True, checked=True),
        GateItem(id="b", description="y", required=True, checked=False),
    ]
    gate = GateInfo(step_id="1", items=items)
    assert gate.all_required_met is False

    all_checked = [
        GateItem(id="a", description="x", required=True, checked=True),
        GateItem(id="b", description="y", required=True, checked=True),
    ]
    assert GateInfo(step_id="1", items=all_checked).all_required_met is True
```

**🟢 GREEN:** `GateItem` com `checked: bool = False`; `GateInfo` com `all_required_met` como `@property` que retorna `all(i.checked for i in self.items if i.required)`.

> ⚠️ **Nota de design:** como o dataclass é frozen, `all_required_met` deve ser **property calculada**, não campo armazenado (evita dessincronização).

**DoD:** 2 testes verdes. **Esforço:** 0,5 dia.

---

### Task 1.3 — `PipelineStatus` com propriedades computadas

**🔴 RED:**
```python
from llc_wizard.data import PipelineStatus, StepInfo, StepStatus


def _step(id, status, in_pipeline=True):
    return StepInfo(id=id, name=id, status=status, in_pipeline=in_pipeline,
                    depends_on=[], current_session_id=None, artifacts_output=[])


def test_progress_percent_counts_only_pipeline_steps():
    steps = [
        _step("0.5", StepStatus.COMPLETED),
        _step("1", StepStatus.COMPLETED),
        _step("2", StepStatus.PENDING),
        _step("11.2", StepStatus.COMPLETED, in_pipeline=False),  # excluído
    ]
    status = PipelineStatus(steps=steps, current_step_id="2")
    # denominador = 3 (steps in_pipeline); numerador = 2
    assert abs(status.progress_percent - 66.66) < 0.1


def test_progress_zero_when_no_pipeline_steps():
    status = PipelineStatus(steps=[], current_step_id=None)
    assert status.progress_percent == 0.0


def test_completed_steps_filters_by_status_and_pipeline():
    steps = [
        _step("0.5", StepStatus.COMPLETED),
        _step("1", StepStatus.FAILED),
        _step("x", StepStatus.COMPLETED, in_pipeline=False),
    ]
    status = PipelineStatus(steps=steps, current_step_id=None)
    assert [s.id for s in status.completed_steps] == ["0.5"]
```

**🟢 GREEN:** implementar `PipelineStatus` (não-frozen, mutável para `bypass_mode`) com `@property in_pipeline_steps`, `completed_steps`, `progress_percent`.

**DoD:** 3 testes verdes. **Esforço:** 0,5 dia.

---

### Task 1.4 — `PipelineDataReader.get_status()` deriva status do `index.json`

**🔴 RED:**
```python
from llc_wizard.data import PipelineDataReader, StepStatus


def test_get_status_marks_in_progress_from_open_session(project_root, make_index, monkeypatch):
    make_index(project_root, [
        {"session_id": "2026-08-04-001", "step": "5", "status": "in_progress"},
        {"session_id": "2026-08-04-002", "step": "0.5", "status": "completed"},
    ])
    reader = PipelineDataReader(project_root)
    monkeypatch.setattr(reader, "_get_registry", lambda: _fake_registry())

    status = reader.get_status()
    by_id = {s.id: s for s in status.steps}
    assert by_id["5"].status == StepStatus.IN_PROGRESS
    assert by_id["0.5"].status == StepStatus.COMPLETED


def test_get_status_tolerates_missing_index(project_root, monkeypatch):
    (project_root / ".ace" / "index.json").unlink()
    reader = PipelineDataReader(project_root)
    monkeypatch.setattr(reader, "_get_registry", lambda: _fake_registry())
    status = reader.get_status()
    assert all(s.status == StepStatus.PENDING for s in status.steps)


def _fake_registry():
    # stub mínimo do registry de llc_steps
    class _S:
        def __init__(self, id, name, in_pipeline=True, deps=None):
            self.id, self.name, self.in_pipeline = id, name, in_pipeline
            self.depends_on, self.artifacts = deps or [], []
    return {
        "0.5": _S("0.5", "Visão"), "5": _S("5", "Arquitetura"),
        "11.2": _S("11.2", "PRP Verify", in_pipeline=False),
    }
```

**🟢 GREEN:** implementar `PipelineDataReader.__init__`, `get_status()`, `_load_index()` (tolerante a arquivo ausente/JSON inválido → retorna `{"sessions": []}`), `_derive_status()`, `_get_registry()` (import dinâmico de `llc_steps`).

**🔵 REFACTOR:** extrair `_safe_load_json(path, default)` para reuso.

**DoD:** 3 testes verdes; cobre os ramos "arquivo ausente" e "sessão aberta". **Esforço:** 1 dia.

---

### Task 1.5 — `PipelineDataReader.get_gate_for_step()` parseia `gates.json`

**🔴 RED:**
```python
def test_get_gate_returns_items_from_gates_json(project_root, make_gates):
    make_gates(project_root, {
        "gate-1": {"items": [
            {"description": "7 Especificações completas", "required": True},
            {"description": "Glossário alinhado", "required": False},
        ]}
    })
    reader = PipelineDataReader(project_root)
    gate = reader.get_gate_for_step("1")
    assert gate.step_id == "1"
    assert len(gate.items) == 2
    assert gate.items[0].required is True
    assert gate.items[1].required is False
    assert gate.all_required_met is False


def test_get_gate_returns_none_when_absent(project_root):
    reader = PipelineDataReader(project_root)
    assert reader.get_gate_for_step("99") is None
```

**🟢 GREEN:** implementar `get_gate_for_step()` lendo `gate-{step_id}` do config; retorna `None` se ausente.

**DoD:** 2 testes verdes. **Esforço:** 0,5 dia.

---

### Task 1.6 — `get_status_since()` e `get_pending_hitl()` (contratos para o Kanban)

> **Por que agora:** o `KanbanBoardBuilder` (WP2) precisa de `entered_column_at` (SLA) e da fila HITL. Entregar na 1A evita retrabalho na Fase 2/Herdr.

**🔴 RED:**
```python
from datetime import datetime, timedelta


def test_get_status_since_returns_timestamp_from_session(project_root, make_index):
    ts = "2026-08-04T10:00:00"
    make_index(project_root, [
        {"session_id": "s1", "step": "5", "status": "in_progress", "updated_at": ts},
    ])
    reader = PipelineDataReader(project_root)
    since = reader.get_status_since("5")
    assert isinstance(since, datetime)


def test_get_status_since_falls_back_to_now_when_unknown(project_root):
    reader = PipelineDataReader(project_root)
    since = reader.get_status_since("missing")
    assert (datetime.now() - since) < timedelta(seconds=5)


def test_get_pending_hitl_returns_gate_pending_sessions(project_root, make_index):
    make_index(project_root, [
        {"session_id": "s1", "step": "2.5", "status": "gate_pending",
         "updated_at": "2026-08-04T09:00:00", "hitl_kind": "gate"},
    ])
    reader = PipelineDataReader(project_root)
    pending = reader.get_pending_hitl()
    assert len(pending) == 1
    assert pending[0].step_id == "2.5"
    assert pending[0].kind == "gate"
```

**🟢 GREEN:** implementar os dois métodos; definir dataclass `PendingHITL(id, step_id, session_id, kind, summary, created_at)`.

**DoD:** 3 testes verdes. **Esforço:** 1 dia.

---

## 📦 WP2 — `kanban.py` (Modelo de Dados, sem UI)

> **Alvo de cobertura:** ≥ 85%. Deriva do `PipelineDataReader` (single source of truth).

### Task 2.1 — `KanbanColumn` e `CardType` enums

**🔴 RED:**
```python
from llc_wizard.kanban import KanbanColumn, CardType


def test_kanban_has_six_columns():
    assert {c.value for c in KanbanColumn} == {
        "backlog", "running", "awaiting_human", "rework", "done", "skipped",
    }


def test_card_types():
    assert {t.value for t in CardType} == {"work", "decision"}
```

**🟢 GREEN:** enums simples. **DoD:** 2 testes verdes. **Esforço:** 0,25 dia.

---

### Task 2.2 — `KanbanCard` com `time_in_column` e `is_stale`

**🔴 RED:**
```python
from datetime import datetime, timedelta
from llc_wizard.kanban import KanbanCard, KanbanColumn, CardType


def _card(column, entered_at):
    return KanbanCard(
        id="hitl-1", title="Gate 2.5", card_type=CardType.DECISION,
        column=column, step_id="2.5", session_id="s1",
        entered_column_at=entered_at, agent=None, meta={},
    )


def test_is_stale_true_when_awaiting_human_over_sla():
    old = datetime.now() - timedelta(minutes=31)
    assert _card(KanbanColumn.AWAITING_HUMAN, old).is_stale(sla_minutes=30) is True


def test_is_stale_false_when_under_sla():
    recent = datetime.now() - timedelta(minutes=10)
    assert _card(KanbanColumn.AWAITING_HUMAN, recent).is_stale(sla_minutes=30) is False


def test_is_stale_false_for_non_awaiting_columns():
    old = datetime.now() - timedelta(hours=2)
    assert _card(KanbanColumn.RUNNING, old).is_stale(sla_minutes=30) is False


def test_time_in_column_is_non_negative():
    card = _card(KanbanColumn.BACKLOG, datetime.now())
    assert card.time_in_column >= timedelta(0)
```

> ⚠️ **Decisão D2 vinculante:** SLA é **injetado** (`sla_minutes=30` default), lido de `wizard.hitl_sla_minutes` em `gates.json`. Injetar via parâmetro facilita teste e configuração.

**🟢 GREEN:** implementar `KanbanCard` (frozen) com `is_stale(sla_minutes: int = 30)`.

**DoD:** 4 testes verdes. **Esforço:** 0,5 dia.

---

### Task 2.3 — `KanbanBoardBuilder.build()` mapeia steps → colunas

**🔴 RED:**
```python
from llc_wizard.kanban import KanbanBoardBuilder, KanbanColumn, CardType
from llc_wizard.data import StepStatus


def test_build_places_steps_in_correct_columns(project_root, monkeypatch):
    reader = _reader_with_steps([
        ("0.5", StepStatus.COMPLETED),
        ("1", StepStatus.IN_PROGRESS),
        ("2", StepStatus.PENDING),
        ("3", StepStatus.FAILED),
        ("10.5", StepStatus.SKIPPED),
    ])
    board = KanbanBoardBuilder(reader).build()
    assert _ids(board[KanbanColumn.DONE]) == ["step-0.5"]
    assert _ids(board[KanbanColumn.RUNNING]) == ["step-1"]
    assert _ids(board[KanbanColumn.BACKLOG]) == ["step-2"]
    assert _ids(board[KanbanColumn.REWORK]) == ["step-3"]
    assert _ids(board[KanbanColumn.SKIPPED]) == ["step-10.5"]


def test_build_includes_hitl_cards_sorted_by_age(project_root):
    reader = _reader_with_hitl([
        ("hitl-b", "2026-08-04T10:00:00"),   # mais recente
        ("hitl-a", "2026-08-04T08:00:00"),   # mais antigo
    ])
    board = KanbanBoardBuilder(reader).build()
    awaiting = board[KanbanColumn.AWAITING_HUMAN]
    decision_ids = [c.id for c in awaiting if c.card_type == CardType.DECISION]
    assert decision_ids == ["hitl-a", "hitl-b"]  # mais antigo primeiro (SLA)
```

**🟢 GREEN:** implementar `build()` iterando `reader.get_status().steps` + `reader.get_pending_hitl()`, mapeando via dict `STEP_TO_COLUMN`, ordenando `AWAITING_HUMAN` por `entered_column_at`.

**🔵 REFACTOR:** extrair `STEP_TO_COLUMN` como constante de módulo.

**DoD:** 2 testes verdes (6 asserções de coluna + ordenação SLA). **Esforço:** 1 dia.

---

## 📦 WP3 — `runner.py` (Execução, não-bloqueante)

> **Alvo de cobertura:** ≥ 80% (runner tem I/O; usa mocks). Regra crítica: **nunca bloquear** o event loop da UI.

### Task 3.1 — Tipos de evento (`OutputEvent`, `CompletionEvent`)

**🔴 RED:**
```python
from llc_wizard.runner import OutputEvent, CompletionEvent


def test_output_event_carries_line_and_source():
    e = OutputEvent(line="Gerando arquitetura...", source="agent")
    assert e.line == "Gerando arquitetura..."
    assert e.source == "agent"


def test_completion_event_carries_gate():
    e = CompletionEvent(success=True, session_id="s1", gate_data=None)
    assert e.success is True
```

**🟢 GREEN:** dataclasses simples. **DoD:** 2 testes verdes. **Esforço:** 0,25 dia.

---

### Task 3.2 — `HarnessRunner.run_step()` invoca `llc_harness` em thread

**🔴 RED:** (mock do `llc_harness` para não depender do harness real)
```python
import pytest
from llc_wizard.runner import HarnessRunner, OutputEvent, CompletionEvent


@pytest.mark.asyncio
async def test_run_step_emits_output_then_completion(project_root, monkeypatch):
    runner = HarnessRunner(project_root)

    events = []
    async for ev in runner.run_step("5", "Arquitetura"):
        events.append(ev)

    types = [type(e).__name__ for e in events]
    assert "OutputEvent" in types
    assert types[-1] == "CompletionEvent"
    assert events[-1].success is True
```
> Use `monkeypatch` para stubar `step_run` do `llc_harness` retornando um objeto com `.success=True, .session_id="s1", .gate=None`.

**🟢 GREEN:** implementar `run_step()` usando `asyncio.get_event_loop().run_in_executor` + `asyncio.Queue` + sentinela `None` (conforme ADR-0002). Captura stdout via `redirect_stdout`.

**🔵 REFACTOR:** isolar `_blocking_call()` para legibilidade.

**DoD:** 1 teste verde (ordem de eventos garantida). **Esforço:** 1,5 dia.

---

### Task 3.3 — `FallbackRunner` gera prompt copia-cola

**🔴 RED:**
```python
@pytest.mark.asyncio
async def test_fallback_runner_yields_prompt_with_instructions(project_root, monkeypatch):
    from llc_wizard.runner import FallbackRunner
    monkeypatch.setattr("builtins.input", lambda *a: "")  # simula Enter
    runner = FallbackRunner(project_root)
    events = [ev async for ev in runner.run_step("5", "Arquitetura")]
    prompt = next(e for e in events if isinstance(e, OutputEvent))
    assert "copie" in prompt.line.lower() or "cole" in prompt.line.lower()
```

**🟢 GREEN:** implementar `FallbackRunner.run_step()` montando `context_seed` + skill e aguardando `input()` via executor.

**DoD:** 1 teste verde. **Esforço:** 0,5 dia.

---

### Task 3.4 — Seleção automática de runner (detecção de cliente de IA)

**🔴 RED:**
```python
def test_select_runner_uses_harness_when_agent_available(project_root, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/claude")
    from llc_wizard.runner import select_runner, HarnessRunner
    runner = select_runner(project_root)
    assert isinstance(runner, HarnessRunner)


def test_select_runner_falls_back_when_no_agent(project_root, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    from llc_wizard.runner import select_runner, FallbackRunner
    runner = select_runner(project_root)
    assert isinstance(runner, FallbackRunner)
```

**🟢 GREEN:** implementar `select_runner()` verificando `which()` para `["claude","opencode","codex","cursor"]`.

**DoD:** 2 testes verdes. **Esforço:** 0,5 dia.

---

## 📦 WP4 — Widgets + `app.py` (UI)

> **Testes via `textual.App.run_test()` + `pilot` (headless).** Regra FTDD: 1 teste por estado visual.

### Task 4.1 — `WizardApp` skeleton renderiza layout base

**🔴 RED:**
```python
from llc_wizard.app import WizardApp


async def test_app_mounts_header_sidebar_output(project_root):
    app = WizardApp(project_root)
    async with app.run_test() as pilot:
        assert app.query_one("#sidebar") is not None
        assert app.query_one("#output-panel") is not None
        assert app.query_one("#context-panel") is not None
```

**🟢 GREEN:** implementar `compose()` com `Header`, `Horizontal(StepList, Vertical(context, output))`, `Footer`.

**DoD:** 1 teste verde. **Esforço:** 1 dia.

---

### Task 4.2 — `StepList` renderiza ícones por status

**🔴 RED:**
```python
async def test_sidebar_shows_pending_icons_initially(project_root):
    app = WizardApp(project_root)
    async with app.run_test():
        sidebar = app.query_one("#sidebar")
        assert sidebar.all_pending()  # helper exposto para teste
        assert "⏳" in sidebar.render_text()
```

**🟢 GREEN:** implementar `StepList.update(PipelineStatus)` mapeando `StepStatus → ícone` (`⏳🔄⚠️✅❌⏭️○`).

**DoD:** 1 teste verde. **Esforço:** 1 dia.

---

### Task 4.3 — Barra de progresso reflete `progress_percent`

**🔴 RED:**
```python
async def test_progress_bar_shows_zero_initially(project_root):
    app = WizardApp(project_root)
    async with app.run_test():
        assert "0.0%" in app.sub_title or "0/22" in app.sub_title
```

**🟢 GREEN:** bindar `sub_title` ao `progress_percent` do `PipelineStatus`.

**DoD:** 1 teste verde. **Esforço:** 0,5 dia.

---

### Task 4.4 — `GateChecklist` renderiza itens e valida obrigatórios

**🔴 RED:**
```python
from llc_wizard.widgets.gate_checklist import GateChecklist


async def test_checklist_blocks_approve_when_required_unchecked():
    gate = _gate_with_required_unchecked()
    widget = GateChecklist(gate)
    async with widget.run_test() as pilot:
        assert widget.all_required_checked() is False


async def test_checklist_allows_approve_when_all_required_checked():
    gate = _gate_all_required_checked()
    widget = GateChecklist(gate)
    async with widget.run_test() as pilot:
        pilot.press("space")  # marca item
        assert widget.all_required_checked() is True
```

**🟢 GREEN:** implementar `GateChecklist` com checkboxes; `all_required_checked()`; bloqueio de aprovação se item obrigatório desmarcado.

**DoD:** 2 testes verdes. **Esforço:** 1,5 dia.

---

### Task 4.5 — Fluxo aprovar gate avança; rejeitar abre recovery

**🔴 RED:**
```python
async def test_approve_gate_calls_session_end_and_advances(project_root, monkeypatch):
    called = {}
    monkeypatch.setattr("llc_harness.session_end",
                        lambda sid, status, extra: called.update(status=status))
    app = WizardApp(project_root)
    async with app.run_test() as pilot:
        # simula gate pendente e pressiona 'A'
        pilot.press("a")
        await pilot.pause()
    assert called.get("status") == "approved"


async def test_reject_gate_opens_recovery_screen(project_root):
    app = WizardApp(project_root)
    async with app.run_test() as pilot:
        pilot.press("r")
        await pilot.pause()
        assert app.screen.__class__.__name__ == "FailureRecoveryScreen"
```

**🟢 GREEN:** implementar `action_approve_gate()` (valida checklist → `session_end` → refresh) e `action_reject_gate()` (push `FailureRecoveryScreen`).

**DoD:** 2 testes verdes. **Esforço:** 1,5 dia.

---

## 📦 WP5 — Integração CLI `llc wizard`

### Task 5.1 — Subcomando `wizard` com flags

**🔴 RED:**
```python
from click.testing import CliRunner
from llc import cli  # entry point do llc.py


def test_wizard_command_registered():
    runner = CliRunner()
    result = runner.invoke(cli, ["wizard", "--help"])
    assert result.exit_code == 0
    assert "--from" in result.output or "--from-step" in result.output
    assert "--auto-approve" in result.output


def test_wizard_friendly_message_when_textual_missing(monkeypatch):
    import builtins
    real_import = builtins.__import__
    def fake_import(name, *a, **k):
        if name == "textual":
            raise ImportError("No module named 'textual'")
        return real_import(name, *a, **k)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    runner = CliRunner()
    result = runner.invoke(cli, ["wizard"])
    assert "pip install textual" in result.output
```

**🟢 GREEN:** adicionar subcomando `wizard` no `llc.py` (lazy-import de `llc_wizard.app`); tratar `ImportError` com mensagem amigável.

**DoD:** 2 testes verdes; `llc run`/`llc pipeline`/`llc gate` permanecem intactos. **Esforço:** 1 dia.

---

### Task 5.2 — Sessão ACE obrigatória (disciplina de protocolo)

**🔴 RED:** (teste de contrato, não de UI)
```python
def test_wizard_requires_session_enrollment(project_root):
    """O Wizard não pode escrever em .ace/sessions fora do ciclo init→finalize."""
    # Assert: nenhum módulo de llc_wizard escreve frontmatter diretamente.
    import ast, pathlib
    src = (pathlib.Path(__file__).parent.parent).glob("*.py")
    for f in src:
        tree = ast.parse(f.read_text())
        # heurística: nenhuma chamada direta a open(..., "w") em sessions/
        assert "sessions" not in _find_direct_session_writes(tree), f"{f} viola ACE"
```

**🟢 GREEN:** garantir que `UserDecisionWriter` usa apenas append (`"a"`) de tags e `session_end()`; nenhum `open(..., "w")` em `.ace/sessions/`.

**DoD:** 1 teste de contrato verde. **Esforço:** 0,5 dia.

---

## 📋 Resumo — Backlog Ordenado da Fase 1A

| # | Task | WP | Esforço | Depende de |
|---|---|---|---|---|
| 0.1 | Setup pacote + conftest | WP0 | 0,5d | — |
| 1.1 | StepStatus + StepInfo | WP1 | 0,5d | 0.1 |
| 1.2 | GateItem + GateInfo | WP1 | 0,5d | 1.1 |
| 1.3 | PipelineStatus | WP1 | 0,5d | 1.1 |
| 1.4 | get_status() | WP1 | 1,0d | 1.1–1.3 |
| 1.5 | get_gate_for_step() | WP1 | 0,5d | 1.2 |
| 1.6 | get_status_since() + get_pending_hitl() | WP1 | 1,0d | 1.4 |
| 2.1 | KanbanColumn + CardType | WP2 | 0,25d | 1.1 |
| 2.2 | KanbanCard + is_stale | WP2 | 0,5d | 2.1 |
| 2.3 | KanbanBoardBuilder.build() | WP2 | 1,0d | 1.6, 2.2 |
| 3.1 | Eventos do runner | WP3 | 0,25d | 0.1 |
| 3.2 | HarnessRunner.run_step() | WP3 | 1,5d | 3.1, 1.4 |
| 3.3 | FallbackRunner | WP3 | 0,5d | 3.1 |
| 3.4 | select_runner() | WP3 | 0,5d | 3.2, 3.3 |
| 4.1 | WizardApp skeleton | WP4 | 1,0d | 1.4, 3.4 |
| 4.2 | StepList ícones | WP4 | 1,0d | 4.1 |
| 4.3 | Barra de progresso | WP4 | 0,5d | 4.1 |
| 4.4 | GateChecklist | WP4 | 1,5d | 1.5, 4.1 |
| 4.5 | Aprovar/Rejeitar gate | WP4 | 1,5d | 4.4 |
| 5.1 | Subcomando `llc wizard` | WP5 | 1,0d | 4.1 |
| 5.2 | Contrato sessão ACE | WP5 | 0,5d | 5.1 |

**Total:** 21 tasks · **~15 dias-homem** de código/teste · margem para atingir as 4 semanas do MVP com integrações e correções.

---

## ✅ Gate de Saída da Fase 1A (antes de avançar à 1B)

- [ ] Todas as 21 tasks com ciclos RED→GREEN→REFACTOR documentados (saída de teste exibida em cada um).
- [ ] `pytest .ace/scripts/llc_wizard/tests/ -v --cov=llc_wizard` → cobertura ≥ 85% (`data.py`, `kanban.py`), ≥ 80% (`runner.py`).
- [ ] `llc wizard --from 0` executa pipeline com gates interativas; fallback funcional.
- [ ] `fitness-functions.py --all --strict` verde (DIP entre camadas, CQS, sem flags em assinaturas públicas).
- [ ] Nenhuma alteração em `llc_harness`/`llc_steps`/`llc_delta`/`llc_wave`.
- [ ] Frontmatter de sessões escrito apenas pelos scripts sancionados (Task 5.2 verde).
- [ ] Sessão ACE registrada para o trabalho da Fase 1A.

---
