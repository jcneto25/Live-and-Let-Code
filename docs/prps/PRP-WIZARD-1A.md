# PRP: [WIZARD-1A] — LLC Wizard TUI — Fase 1A MVP (data + kanban + runner + app + CLI)

> **ID:** PRP-WIZARD-1A | **Fase:** Fase 1 — Observabilidade | **Onda:** 1
> **Owner:** jcneto25 | **Reviewer:** jcneto25
> **Estimativa:** ~15 dias-homem | **Status:** ⏳ Pending
> **Prioridade:** Crítico
> **Complexidade:** Alta
> **Criado em:** 2026-08-05 | **Última atualização:** 2026-08-05 | **Versão:** v1.0
> **ADR de origem:** ADR-0002 (aceito em 2026-08-04)

---

## 1. Contexto e Objetivo

### 1.1 ADR de Origem

| Campo | Valor |
|-------|-------|
| ID | ADR-0002 |
| Decisão | Construir LLC Wizard — TUI interativa com Textual (Python 3.10+) |
| Arquivo | `docs/architecture/ADR-0002-llc-wizard-tui-hitl-kanban.md` |

### 1.2 Por que este PRP existe?

O LLC opera exclusivamente via CLI (`llc.py`). O operador não tem visibilidade consolidada do progresso do pipeline: estado inferido via `.ace/index.json`, gates apresentados de forma textual minimalista, sem indicador de "onde estou" ou "o que está bloqueado". Este PRP entrega o MVP do Wizard — a camada de dados, modelo Kanban, runner assíncrono, UI básica e integração CLI — que resolve a dor de observabilidade mais imediata sem tocar no harness existente.

### 1.3 O que é entregue

- [ ] `llc_wizard/data.py` — camada de acesso read-only ao estado do pipeline
- [ ] `llc_wizard/kanban.py` — modelo de dados Kanban (sem UI) com SLA e is_stale
- [ ] `llc_wizard/runner.py` — execução não-bloqueante via `asyncio.to_thread`
- [ ] `llc_wizard/app.py` + widgets básicos — TUI funcional com sidebar, gate checklist
- [ ] `llc wizard` subcomando no `llc.py` com graceful degradation se Textual ausente
- [ ] Suite de testes TDD com cobertura ≥ 85% em `data.py` e `kanban.py`

### 1.4 O que NÃO está no escopo

- ❌ HITL completo (`decisions.py`, `commands.py`, `RealtimePromptCollector`) → PRP-WIZARD-1B
- ❌ Artifact Review, Scope Confirmation, rerun automático → PRP-WIZARD-1C
- ❌ Kanban UI board completo (toggle K, SLA visual, WIP) → PRP-WIZARD-1.1
- ❌ Drag & drop no backlog, `--export-flow-metrics` → PRP-WIZARD-1.2
- ❌ Swimlanes por wave, integração Herdr → PRP-WIZARD-2.0
- ❌ Refatoração `KanbanBoardBuilder` para projetar do `GraphEngine` → PRP-GRAPH-1A

---

## 2. Requisitos Funcionais

> **Nota de protocolo:** colunas `Teste(s)` e `Arquivo(s) impl` são lidas por `prp_verify.py` (Step 11.2).

| ID | Requisito | Critérios de Aceitação (Gherkin) | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------------------|------------|--------|----------|-----------------|
| RF-W1A.1 | `StepStatus` enum com 7 estados | **Dado** o enum `StepStatus`, **Quando** iterado, **Então** contém exatamente `{pending, in_progress, gate_pending, completed, failed, skipped, excluded}` | Must | ⏳ | `tests/test_data.py` | `llc_wizard/data.py` |
| RF-W1A.2 | `StepInfo` é imutável (frozen dataclass) | **Dado** uma instância de `StepInfo`, **Quando** tentativa de mutação, **Então** lança `FrozenInstanceError` | Must | ⏳ | `tests/test_data.py` | `llc_wizard/data.py` |
| RF-W1A.3 | `PipelineStatus.progress_percent` conta só steps `in_pipeline` | **Dado** 2 steps completed + 1 pending + 1 excluded, **Quando** `progress_percent`, **Então** retorna ~66.6% | Must | ⏳ | `tests/test_data.py` | `llc_wizard/data.py` |
| RF-W1A.4 | `PipelineDataReader` tolera `index.json` ausente | **Dado** `.ace/index.json` deletado, **Quando** `get_status()`, **Então** todos os steps retornam `pending` sem exceção | Must | ⏳ | `tests/test_data.py` | `llc_wizard/data.py` |
| RF-W1A.5 | `PipelineDataReader` parseia gates do `gates.json` | **Dado** `gate-1` em `gates.json` com 2 itens, **Quando** `get_gate_for_step("1")`, **Então** `GateInfo` com 2 `GateItem` e `all_required_met=False` | Must | ⏳ | `tests/test_data.py` | `llc_wizard/data.py` |
| RF-W1A.6 | `KanbanCard.is_stale` respeita SLA configurável | **Dado** card em `AWAITING_HUMAN` há 31 min e SLA=30, **Quando** `is_stale(30)`, **Então** retorna `True` | Must | ⏳ | `tests/test_kanban.py` | `llc_wizard/kanban.py` |
| RF-W1A.7 | `KanbanBoardBuilder.build()` mapeia steps para colunas corretas | **Dado** steps com status variados, **Quando** `build()`, **Então** cada step aparece na coluna correspondente ao seu status | Must | ⏳ | `tests/test_kanban.py` | `llc_wizard/kanban.py` |
| RF-W1A.8 | `AWAITING_HUMAN` ordenado por tempo de espera (mais antigo no topo) | **Dado** 2 HITL pendentes com timestamps distintos, **Quando** `build()`, **Então** mais antigo é o primeiro na lista | Must | ⏳ | `tests/test_kanban.py` | `llc_wizard/kanban.py` |
| RF-W1A.9 | `HarnessRunner.run_step()` emite `OutputEvent` antes de `CompletionEvent` | **Dado** runner com harness mockado, **Quando** `run_step()` consumido via async-for, **Então** `OutputEvent` precede `CompletionEvent` final | Must | ⏳ | `tests/test_runner.py` | `llc_wizard/runner.py` |
| RF-W1A.10 | `FallbackRunner` gera prompt copia-cola | **Dado** `FallbackRunner`, **Quando** `run_step()`, **Então** emite `OutputEvent` com "copie" ou "cole" no texto | Must | ⏳ | `tests/test_runner.py` | `llc_wizard/runner.py` |
| RF-W1A.11 | `select_runner()` usa `HarnessRunner` se agente detectado | **Dado** `shutil.which` retorna path para `claude`, **Quando** `select_runner()`, **Então** retorna `HarnessRunner` | Must | ⏳ | `tests/test_runner.py` | `llc_wizard/runner.py` |
| RF-W1A.12 | `WizardApp` monta layout com sidebar, context e output panels | **Dado** `WizardApp(project_root)`, **Quando** `run_test()`, **Então** `#sidebar`, `#context-panel` e `#output-panel` existem no DOM | Must | ⏳ | `tests/test_app.py` | `llc_wizard/app.py` |
| RF-W1A.13 | `llc wizard --help` registrado e mostra flags `--from` e `--auto-approve` | **Dado** CLI, **Quando** `llc wizard --help`, **Então** exit code 0 e flags presentes | Must | ⏳ | `tests/test_app.py` | `.ace/scripts/llc.py` |
| RF-W1A.14 | `llc wizard` sem Textual exibe mensagem de instalação | **Dado** `textual` não instalado, **Quando** `llc wizard`, **Então** output contém "pip install textual" | Must | ⏳ | `tests/test_app.py` | `.ace/scripts/llc.py` |
| RF-W1A.15 | Wizard não escreve frontmatter diretamente em `.ace/sessions/` | **Dado** todo código `llc_wizard/`, **Quando** análise AST, **Então** nenhum `open(..., "w")` aponta para `sessions/` | Must | ⏳ | `tests/test_app.py` | `llc_wizard/decisions.py` |

---

## 3. Requisitos Não-Funcionais

| ID | Requisito | Métrica | Como verificar | Status |
|----|-----------|---------|----------------|--------|
| RNF-W1A.1 | Cobertura `data.py` e `kanban.py` | ≥ 85% | `pytest --cov=llc_wizard --cov-report=term` | ⏳ |
| RNF-W1A.2 | Cobertura `runner.py` | ≥ 80% | `pytest --cov=llc_wizard` | ⏳ |
| RNF-W1A.3 | Startup da TUI | < 2s | Medido via `time llc wizard` | ⏳ |
| RNF-W1A.4 | Crash-free sessions | ≥ 99% | Ausência de exceções não tratadas em `test_app.py` | ⏳ |
| RNF-W1A.5 | `fitness-functions.py --all --strict` verde | 0 CRITICAL | `python .ace/scripts/fitness-functions.py --all --strict` | ⏳ |
| RNF-W1A.6 | Harness existente intocado | Sem modificações | `git diff .ace/scripts/llc_harness/ .ace/scripts/llc_steps/` = vazio | ⏳ |
| RNF-W1A.7 | `runner.py` nunca bloqueia event loop | Sem `time.sleep` ou I/O síncrono fora de executor | Review de código + lint customizado | ⏳ |
| RNF-W1A.8 | `data.py` interface compatível com futura `GraphEngine` | `PipelineDataSource` Protocol definido desde o WP1 | Code review contra ADR-0004 §2.3 contrato | ⏳ |

---

## 4. Dependências

### 4.1 Bloqueado por

| Artefato | Tipo | Status | Motivo |
|----------|------|--------|--------|
| ADR-0006 | Política | ✅ Aceito | `dependencies.yaml` e `dependency-governance` check devem existir antes da implementação |
| ADR-0002 | Decisão | ✅ Aceito (limpo) | Arquitetura do Wizard definida |

### 4.2 Desbloqueia

| PRP | Nome | Motivo |
|-----|------|--------|
| PRP-WIZARD-1B | HITL completo | Depende de `data.py` e `app.py` do MVP |
| PRP-EVALS-F1 | Eval Harness F1 (Instrumentação) | Exibe métricas no Kanban — precisa do `KanbanCard` |
| PRP-GRAPH-1A | `llc_graph` model + builder | `KanbanBoardBuilder` será refatorado para projetar do `GraphEngine` |

---

## 5. API Contracts

N/A — componente de linha de comando, sem endpoints HTTP.

---

## 6. Component Spec (FTDD)

> ⚠️ Cada estado abaixo vira um caso de teste RED antes da implementação (RULE FTDD do AGENTS.md).

### 6.1 `WizardApp` — estados da tela Pipeline

| Estado | Trigger | UI esperada | Arquivo de teste |
|--------|---------|-------------|------------------|
| `initial` | App inicia sem sessão ativa | Sidebar com todos os steps `⏳`, progress `0/N`, footer com binds | `tests/test_app.py` |
| `step_running` | Step com `status=in_progress` | Sidebar mostra `🔄` no step atual, output panel exibe log streaming | `tests/test_app.py` |
| `gate_pending` | Step com `status=gate_pending` | Gate checklist visível, botões [A]provar/[R]ejeitar ativos | `tests/test_app.py` |
| `gate_approved` | Usuário pressiona `A` com todos obrigatórios marcados | Step avança para próximo, sidebar atualizada | `tests/test_app.py` |
| `gate_rejected` | Usuário pressiona `R` | `FailureRecoveryScreen` empilhada | `tests/test_app.py` |
| `fallback` | Nenhum agente detectado | Prompt copia-cola visível no output panel | `tests/test_app.py` |
| `pipeline_done` | Todos steps `completed` | Progress `N/N`, mensagem de conclusão | `tests/test_app.py` |

### 6.2 `GateChecklist` — estados

| Estado | Trigger | UI esperada | Arquivo de teste |
|--------|---------|-------------|------------------|
| `unchecked_required` | Gate com itens obrigatórios não marcados | Botão Aprovar desabilitado | `tests/test_app.py` |
| `all_required_checked` | Usuário marca todos obrigatórios | Botão Aprovar habilitado | `tests/test_app.py` |

---

## 7. Data Model

### 7.1 `StepInfo` (frozen dataclass)

| Campo | Tipo | Nulabilidade | Fallback |
|-------|------|:------------:|---------|
| `id` | `str` | NOT NULL | N/A |
| `name` | `str` | NOT NULL | N/A |
| `status` | `StepStatus` | NOT NULL | N/A |
| `in_pipeline` | `bool` | NOT NULL | N/A |
| `depends_on` | `list[str]` | NOT NULL | `[]` |
| `current_session_id` | `Optional[str]` | NULL | `None` |
| `artifacts_output` | `list[str]` | NOT NULL | `[]` |

### 7.2 `GateItem` (frozen dataclass)

| Campo | Tipo | Nulabilidade | Fallback |
|-------|------|:------------:|---------|
| `id` | `str` | NOT NULL | N/A |
| `description` | `str` | NOT NULL | N/A |
| `required` | `bool` | NOT NULL | N/A |
| `checked` | `bool` | DEFAULT `False` | — |

### 7.3 `KanbanCard` (frozen dataclass)

| Campo | Tipo | Nulabilidade | Fallback |
|-------|------|:------------:|---------|
| `id` | `str` | NOT NULL | N/A |
| `title` | `str` | NOT NULL | N/A |
| `card_type` | `CardType` | NOT NULL | N/A |
| `column` | `KanbanColumn` | NOT NULL | N/A |
| `step_id` | `Optional[str]` | NULL | `None` |
| `session_id` | `Optional[str]` | NULL | `None` |
| `entered_column_at` | `datetime` | NOT NULL | N/A |
| `agent` | `Optional[str]` | NULL | `None` |
| `meta` | `dict` | NOT NULL | `{}` |

### 7.4 `PendingHITL` (dataclass)

| Campo | Tipo | Nulabilidade | Fallback |
|-------|------|:------------:|---------|
| `id` | `str` | NOT NULL | N/A |
| `step_id` | `str` | NOT NULL | N/A |
| `session_id` | `str` | NOT NULL | N/A |
| `kind` | `str` | NOT NULL | N/A (`"gate"` \| `"question"` \| `"artifact_review"`) |
| `summary` | `Optional[str]` | NULL | `None` |
| `created_at` | `datetime` | NOT NULL | N/A |

### 7.5 `PipelineDataSource` Protocol (interface para compatibilidade futura com GraphEngine)

```python
# llc_wizard/data.py
from typing import Protocol, Optional
from datetime import datetime

class PipelineDataSource(Protocol):
    """Contrato que PipelineDataReader implementa hoje e GraphEngine-backed
    reader implementará na Fase 3 (ADR-0004). Manter este Protocol estável
    evita retrabalho na refatoração do KanbanBoardBuilder."""
    def get_status(self) -> "PipelineStatus": ...
    def get_gate_for_step(self, step_id: str) -> Optional["GateInfo"]: ...
    def get_status_since(self, step_id: str) -> datetime: ...
    def get_pending_hitl(self) -> list["PendingHITL"]: ...
```

> **Decisão de design (resolve Problema 5 da análise crítica):** o `KanbanBoardBuilder`
> recebe `PipelineDataSource`, não `PipelineDataReader` diretamente. Quando o ADR-0004
> for implementado e o `GraphEngine` existir, basta criar um adapter que implemente
> `PipelineDataSource` sobre o `GraphEngine` — sem tocar em `kanban.py` nem em `app.py`.

---

## 8. Estrutura de Arquivos

```
.ace/scripts/
├── llc.py                          # MODIFICADO: novo subcomando `llc wizard`
└── llc_wizard/                     # NOVO pacote
    ├── __init__.py
    ├── app.py                      # WizardApp (Textual App)
    ├── data.py                     # PipelineDataReader + PipelineDataSource Protocol
    ├── kanban.py                   # KanbanCard + KanbanBoardBuilder
    ├── runner.py                   # HarnessRunner + FallbackRunner + select_runner
    ├── widgets/
    │   ├── step_list.py
    │   ├── gate_checklist.py
    │   ├── progress_bar.py
    │   └── output_log.py
    ├── screens/
    │   └── failure_recovery.py
    ├── styles/wizard.tcss
    └── tests/
        ├── __init__.py
        ├── conftest.py
        ├── test_data.py
        ├── test_kanban.py
        ├── test_runner.py
        └── test_app.py
```

---

## 9. Test Strategy (TDD — RED → GREEN → REFACTOR obrigatório)

### 9.1 Mapa de Tasks TDD

**WP0 — Setup**

| Task | RED esperado | GREEN | Esforço |
|------|-------------|-------|---------|
| 0.1 Setup pacote + conftest | `pytest` roda sem erro de import | `no tests ran` sem error | 0,5d |

**WP1 — `data.py`**

| Task | RED esperado | GREEN | Esforço |
|------|-------------|-------|---------|
| 1.1 `StepStatus` + `StepInfo` | `ModuleNotFoundError` | 2 testes verdes | 0,5d |
| 1.2 `GateItem` + `GateInfo` | `ImportError` | 2 testes verdes | 0,5d |
| 1.3 `PipelineStatus` | `ImportError` | 3 testes verdes | 0,5d |
| 1.4 `PipelineDataReader.get_status()` | `AttributeError` | 3 testes verdes | 1,0d |
| 1.5 `get_gate_for_step()` | `AttributeError` | 2 testes verdes | 0,5d |
| 1.6 `get_status_since()` + `get_pending_hitl()` | `AttributeError` | 3 testes verdes | 1,0d |

**WP2 — `kanban.py`**

| Task | RED esperado | GREEN | Esforço |
|------|-------------|-------|---------|
| 2.1 `KanbanColumn` + `CardType` | `ModuleNotFoundError` | 2 testes verdes | 0,25d |
| 2.2 `KanbanCard` + `is_stale` | `AttributeError` | 4 testes verdes | 0,5d |
| 2.3 `KanbanBoardBuilder.build()` | `AttributeError` | 2 testes verdes | 1,0d |

**WP3 — `runner.py`**

| Task | RED esperado | GREEN | Esforço |
|------|-------------|-------|---------|
| 3.1 `OutputEvent` + `CompletionEvent` | `ModuleNotFoundError` | 2 testes verdes | 0,25d |
| 3.2 `HarnessRunner.run_step()` | `AttributeError` | 1 teste verde | 1,5d |
| 3.3 `FallbackRunner` | `AttributeError` | 1 teste verde | 0,5d |
| 3.4 `select_runner()` | `AttributeError` | 2 testes verdes | 0,5d |

**WP4 — `app.py` + widgets (FTDD)**

| Task | RED esperado | GREEN | Esforço |
|------|-------------|-------|---------|
| 4.1 `WizardApp` skeleton | `ModuleNotFoundError` | 1 teste verde | 1,0d |
| 4.2 `StepList` ícones | `AttributeError` | 1 teste verde | 1,0d |
| 4.3 Barra de progresso | `AssertionError` | 1 teste verde | 0,5d |
| 4.4 `GateChecklist` | `ModuleNotFoundError` | 2 testes verdes | 1,5d |
| 4.5 Aprovar/Rejeitar gate | `AssertionError` | 2 testes verdes | 1,5d |

**WP5 — CLI**

| Task | RED esperado | GREEN | Esforço |
|------|-------------|-------|---------|
| 5.1 Subcomando `llc wizard` | `exit_code != 0` | 2 testes verdes | 1,0d |
| 5.2 Contrato sessão ACE | `AssertionError` | 1 teste verde | 0,5d |

**Total estimado:** ~15 dias-homem

### 9.2 conftest.py (fixtures compartilhadas)

```python
# .ace/scripts/llc_wizard/tests/conftest.py
import pytest, json
from pathlib import Path

@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    ace = tmp_path / ".ace"
    (ace / "config").mkdir(parents=True)
    (ace / "sessions").mkdir(parents=True)
    (ace / "index.json").write_text(json.dumps({"sessions": []}), encoding="utf-8")
    (ace / "config" / "gates.json").write_text(json.dumps({}), encoding="utf-8")
    return tmp_path

@pytest.fixture
def make_index():
    def _make(root: Path, sessions: list[dict]):
        (root / ".ace" / "index.json").write_text(
            json.dumps({"sessions": sessions}), encoding="utf-8")
    return _make

@pytest.fixture
def make_gates():
    def _make(root: Path, gates: dict):
        (root / ".ace" / "config" / "gates.json").write_text(
            json.dumps(gates), encoding="utf-8")
    return _make
```

---

## 10. Riscos e Mitigações

| ID | Risco | Prob. | Impacto | Mitigação |
|----|-------|-------|---------|-----------|
| RSK-W1A-01 | Breaking changes do Textual (0.x) | Média | Alto | Pin `textual>=0.80.0,<1.0`; testes headless via `pilot` |
| RSK-W1A-02 | `step_run` do harness bloqueia event loop | Alta | Alto | `asyncio.to_thread` + queue assíncrona; isolar em `_blocking_call()` |
| RSK-W1A-03 | `PipelineDataSource` Protocol diverge da interface do `GraphEngine` | Baixa | Médio | Revisar Protocol contra ADR-0004 §2.3 antes do WP3 |
| RSK-W1A-04 | `input()` bloqueante em gates legacy | Média | Médio | Wizard substitui `gate_check()` por UI própria; mantém `session_end()` |

---

## 11. Decisões Técnicas

| Data | Decisão | Alternativa | Por que esta | Quem |
|------|---------|-------------|-------------|------|
| 2026-08-05 | `KanbanBoardBuilder` recebe `PipelineDataSource` Protocol, não `PipelineDataReader` diretamente | Injetar `PipelineDataReader` diretamente | Evita retrabalho na Fase 3 quando `GraphEngine` substituir o reader | jcneto25 |
| 2026-08-05 | WIP limit `RUNNING=1` aplica ao nível N1 (pipeline macro); múltiplos cards `RUNNING` permitidos no nível N2 (PRPs em worktrees) | WIP=1 global | Paralelismo via worktrees já existe (ADR-0004 fato); bloquear a visualização seria regressão | jcneto25 |

---

## 12. Gate de Saída da Fase 1A

- [ ] Todas as 21 tasks com ciclos RED→GREEN→REFACTOR — saída de teste exibida em cada ciclo
- [ ] `pytest .ace/scripts/llc_wizard/tests/ -v --cov=llc_wizard` → ≥ 85% (`data.py`, `kanban.py`), ≥ 80% (`runner.py`)
- [ ] `llc wizard --from 0` executa pipeline com gates interativas; fallback funcional
- [ ] `fitness-functions.py --all --strict` verde (DIP, CQS, sem flags em assinaturas públicas)
- [ ] Nenhuma alteração em `llc_harness/`, `llc_steps/`, `llc_delta/`, `llc_wave/`
- [ ] Frontmatter de sessões escrito apenas pelos scripts sancionados (Task 5.2 verde)
- [ ] `PipelineDataSource` Protocol definido e `KanbanBoardBuilder` recebe a interface, não a implementação concreta
- [ ] Sessão ACE registrada para o trabalho da Fase 1A

---

## 13. Cross-Cutting Concerns

| # | CCC | Implementa? | Consome? | Tarefa |
|---|-----|:-----------:|:--------:|--------|
| 1 | AuthService | ☐ Não | ☐ Não | N/A — ferramenta local, single-user |
| 4 | Testes unitários | ✅ Sim | ☐ | WP1–WP3 test tasks |
| 5 | Testes de integração | ✅ Sim | ☐ | WP4 FTDD tasks |
| 7 | Input validation | ✅ Sim | ☐ | Task 5.2 (sanitização XML append) |
| 9 | Error handling | ✅ Sim | ☐ | `_safe_load_json`, `FallbackRunner`, graceful degradation |
| 11 | Repository Interface (DIP) | ✅ Sim | ☐ | `PipelineDataSource` Protocol (§7.5) |

---

## 14. Definition of Done

### Funcional
- [ ] Todos os RF da §2 implementados e verificados por `prp_verify.py`
- [ ] Component Spec (§6) implementado — todos os estados com testes

### Técnico
- [ ] Todos os testes da §9 verdes
- [ ] Cobertura conforme RNF-W1A.1 e RNF-W1A.2
- [ ] `fitness-functions.py --all --strict` com 0 CRITICAL
- [ ] `data.py` exporta `PipelineDataSource` Protocol (DIP preparatório para ADR-0004)
- [ ] `dependencies.yaml` atualizado com `textual` registrado (ADR-0006)

### Processo
- [ ] Sessão ACE aberta com `initialize_session.py` antes do primeiro commit de código
- [ ] `<task_completed>` emitidos para cada WP finalizado
- [ ] `finalize_session.py` executado ao final com `context_seed` atualizado
