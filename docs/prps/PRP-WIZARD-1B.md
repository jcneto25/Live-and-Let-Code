# PRP: [WIZARD-1B] — LLC Wizard HITL Completo

> **ID:** PRP-WIZARD-1B | **Trilha:** Wizard | **Onda:** 1
> **Owner:** jcneto25 | **Estimativa:** 2 semanas | **Status:** ✅ Done (2026-08-06)
> **Prioridade:** Alto | **ADR de origem:** ADR-0002 §2.4

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O PRP-WIZARD-1A entrega o MVP do Wizard com gates básicos (aprovar/rejeitar). Mas o pipeline LLC possui múltiplos pontos de interação humana durante execução além de gates: perguntas de clarificação, revisão de artefatos, confirmação de escopo e waivers. Sem esses mecanismos, o Wizard não pode substituir o fluxo CLI completo — o operador ainda precisaria sair do Wizard para responder prompts do agente.

### 1.2 O que é entregue

- [x] `decisions.py` — `UserDecisionWriter` e `RealtimePromptCollector`
- [x] `commands.py` — pattern Command para todas as 6 categorias HITL
- [x] Widgets HITL em tempo real (`prompt_widgets.py`, `decision_modal.py`)
- [x] Integração no `WizardApp` — roteamento de prompts durante execução do step
- [x] Serialização XML append-only para todas as categorias

### 1.3 O que NÃO está no escopo

- ❌ Artifact Review e Scope Confirmation → PRP-WIZARD-1C
- ❌ Kanban UI completo → PRP-WIZARD-1.1

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação (Gherkin) | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|--------------------------------|------------|--------|----------|-----------------|
| RF-W1B.1 | `AnswerQuestionCommand` persiste resposta como `<user_response type="question">` | **Dado** prompt do agente, **Quando** usuário responde, **Então** tag XML append-only no session file | Must | ✅ | `test_decisions.py` | `llc_wizard/decisions.py` |
| RF-W1B.2 | `WaiveGateCommand` exige nota mínima de 10 chars | **Dado** waiver sem nota, **Quando** `validate()`, **Então** retorna `False` | Must | ✅ | `test_commands.py` | `llc_wizard/commands.py` |
| RF-W1B.3 | `RealtimePromptCollector` bloqueia agente até resposta | **Dado** prompt pendente, **Quando** agente tenta continuar, **Então** aguarda resposta via `asyncio.Event` | Must | ✅ | `test_decisions.py` | `llc_wizard/decisions.py` |
| RF-W1B.4 | Múltiplos prompts preservam ordem FIFO | **Dado** 3 prompts em sequência, **Quando** respondidos, **Então** ordem preservada | Must | ✅ | `test_decisions.py` | `llc_wizard/decisions.py` |
| RF-W1B.5 | Agente continua após resposta recebida | **Dado** prompt respondido, **Quando** `submit_response()`, **Então** event liberado e step prossegue | Must | ✅ | `test_decisions.py` | `llc_wizard/decisions.py` |
| RF-W1B.6 | `DecisionModal` renderiza prompt e aceita resposta | **Dado** modal aberto com prompt, **Quando** usuário digita e confirma, **Então** resposta enviada ao `PromptCollector` | Must | ✅ | `test_app.py` | `llc_wizard/widgets/decision_modal.py` |

---

## 3. Contratos de Implementação

```python
# decisions.py
class UserDecisionWriter:
    async def submit_gate_decision(self, d: GateDecision) -> None: ...
    async def submit_question_answer(self, a: QuestionAnswer) -> None: ...
    async def submit_artifact_review(self, r: ArtifactReview) -> None: ...
    async def submit_scope_confirmation(self, s: ScopeConfirmation) -> None: ...

class RealtimePromptCollector:
    async def request_input(self, prompt: PromptRequest) -> str: ...
    def submit_response(self, prompt_id: str, response: str) -> None: ...

# commands.py
class HITLCommand(ABC):
    def validate(self) -> bool: ...
    async def execute(self, writer: UserDecisionWriter) -> None: ...

# Comandos concretos:
# ApproveGateCommand, RejectGateCommand, WaiveGateCommand
# AnswerQuestionCommand, ReviewArtifactCommand, ConfirmScopeCommand
```

---

## 4. Serialização XML (append-only)

```xml
<user_response type="question" question_id="q-{id}" timestamp="{iso}">
  <question>{text}</question>
  <answer>{response}</answer>
</user_response>

<gate_result step="{step}" decision="approved" waiver="true" timestamp="{iso}">
  <waiver_note>{note_min_10_chars}</waiver_note>
</gate_result>

<!-- Emenda GOV-003/R1 (PRP-ACE-TAGS): step + decision obrigatórios (schema
     validate-tags.py); waiver é atributo opcional. Formato anterior
     (approved="/waiver=" sem step/decision) é rejeitado pelo validador. -->

```

---

## 5. Dependências

### Bloqueado por
- PRP-WIZARD-1A ✅

### Desbloqueia
- PRP-WIZARD-1C

---

## 6. Definition of Done

- [x] Todos os 6 RF implementados com testes verdes
- [x] `UserDecisionWriter` usa apenas append — nenhum `open(..., "w")` em sessions/
- [x] `WaiveGateCommand.validate()` rejeita notas < 10 chars
- [x] Múltiplos prompts simultâneos tratados corretamente (sem deadlock)
- [x] `fitness-functions.py --all --strict` verde
- [x] Sessão ACE registrada

> **Nota de fechamento (2026-08-06):** `prp_verify` reporta 0 CRITICAL, 1 WARN
> (`coverage_not_generated` — formato Istanbul `coverage-final.json` vs fonte real
> `pytest-cov`; mesmo padrão de DD-W1A-02). Cobertura e fitness validados: 61 testes
> verdes, fitness 41/41. Sessão ACE `2026-08-06-004` finalizada com `<gate_result>`.
