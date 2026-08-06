# PRP: [ACE-TAGS] — Taxonomia de tags ACE reconhecida pelo validate-tags.py

> **ID:** PRP-ACE-TAGS | **Trilha:** Governança | **Onda:** 0
> **Owner:** jcneto25 | **Estimativa:** 2 dias | **Status:** ✅ Done (2026-08-05)
> **Prioridade:** Crítico — bloqueia WIZARD-1B e EVALS-F1
> **Origem:** GOV-003 / R1 (conflito C1 — formatos XML propostos × validador determinístico)

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

A auditoria GOV-003 (conflito C1) verificou que os formatos de serialização propostos nos
ADRs aceitos eram **incompatíveis com o `validate-tags.py`** — o mecanismo determinístico
que valida sessões ACE e roda no pre-commit:

- `<gate_result approved="true" waiver="true">` (ADR-0002 §7.2 original) violava
  `REQUIRED_ATTRS["gate_result"] = ["step", "decision"]`;
- `<user_response>` (ADR-0002 HITL), `<eval_metrics>` (ADR-0005) e `<task_completed>`
  (AGENTS.md) não constavam de `BALANCED_TAGS` — eram silenciosamente ignorados
  (sem verificação de balanceamento, atributos ou valores).

Sem este PRP, WIZARD-1B e EVALS-F1 gerariam sessões que falhariam na validação ou
passariam sem nenhuma verificação estrutural.

### 1.2 O que foi entregue

- [x] `validate-tags.py`: `BALANCED_TAGS` += `user_response`, `question`, `answer`,
      `waiver_note`, `eval_metrics`, `task_completed`
- [x] `REQUIRED_ATTRS` += `user_response: [type]`, `task_completed: [id, status]`
- [x] `VALID_VALUES` += `gate_result.waiver: [true, false]` (atributo **opcional**),
      `user_response.type: [question, artifact_review, scope]`,
      `task_completed.status: [done, partial]`
- [x] Helper `_tag_opens()`: ignora **menções em prosa** (tag sem atributos, sem
      fechamento na mesma linha e com texto após a tag) — sessões ACE são imutáveis
      e continham menções históricas legítimas (ex.: 2026-07-31-001 linha 57)
- [x] ADR-0002 §7.2/§2.4: formato `<gate_result>` alinhado ao schema
      (`step` + `decision` obrigatórios, `waiver` opcional) com nota de emenda
- [x] `llc-pipeline-design.md` §8.4: taxonomia ampliada com as 4 novas tags
      (+ filhos) e schema completo de `gate_result`
- [x] Suite de testes TDD: `.ace/scripts/test_validate_tags.py` (14 testes)

### 1.3 Formato canônico pós-R1

```xml
<user_response type="question" question_id="q-123" timestamp="...">
  <question>...</question>
  <answer>...</answer>
</user_response>

<eval_metrics timestamp="...">
  step: "5"
  tokens_in: 12000
  total_tokens: 15500
  source: "level_1"
</eval_metrics>

<task_completed id="FDN-001" prp="PRP-001" status="done">descrição</task_completed>

<gate_result step="5" decision="approved" waiver="true" timestamp="...">
  <waiver_note>justificativa com mínimo de 10 caracteres</waiver_note>
</gate_result>
```

---

## 2. Requisitos Funcionais (executados via TDD)

| ID | Requisito | RED | GREEN | Teste |
|----|-----------|-----|-------|-------|
| RF-AT.1 | `<user_response>` balanceado + `type` obrigatório + valores válidos | 3 falhas | ✅ | `TestUserResponse` (4 testes) |
| RF-AT.2 | `<eval_metrics>` balanceado | 1 falha | ✅ | `TestEvalMetrics` (2 testes) |
| RF-AT.3 | `<task_completed>` com `id`/`status` obrigatórios + valores válidos | 2 falhas | ✅ | `TestTaskCompleted` (3 testes) |
| RF-AT.4 | `<gate_result ... waiver="true">` aceito; `waiver="sim"` rejeitado; formato antigo sem `step`/`decision` continua inválido | 1 falha | ✅ | `TestGateResultWaiver` (3 testes) |
| RF-AT.5 | Menção em prosa sem atributos ignorada (sessões imutáveis); tag real sem atributos continua flagrada | 1 falha | ✅ | `TestProseMentions` (2 testes) |

**Ciclo TDD registrado:** RED `7 failed, 5 passed` → GREEN `12 passed` →
RED prosa `1 failed` → GREEN final **`14 passed`**.

---

## 3. Verificação de Regressão

| Checagem | Resultado |
|----------|-----------|
| Sessões reais (`.ace/sessions/*.md`) após mudança | **0 erros de tags** (17 erros pré-existentes de `<dependencies>` — baseline não relacionado) |
| Suite completa `.ace/scripts/` | 215 passed, 7 failed — falhas **pré-existentes** (`test_observability.py` × 6, `test_llc_wave.py` × 1), confirmadas no código original via stash |
| Compatibilidade retroativa | Sessões existentes continuam válidas (mudança puramente aditiva + tolerância a prosa) |
| HTML comments com exemplos de tag (`<!-- <task_completed ...> -->`) | Passam (atributos presentes, balanceados) |

## 4. Incidente Operacional (documentado)

Durante a execução da suite completa, foram detectadas 3 sessões órfãs
(`2026-08-05-004/005/006`, padrão GOV-002: `project: ""` + `task_context: "Step 0.5"`
literal) criadas pelo caminho `llm_fallback` do `llc.py` durante o `pytest`.
**3ª reincidência documentada do GOV-002** — removidas conforme seu controle
(Decisão item 1) e registrada no GOV-002. Reforça o R7 do GOV-003 (fix arquitetural
do `llm_fallback`) como bloqueio de PRP-WIZARD-1A.

## 5. Dependências

### Bloqueado por
- GOV-003 (auditoria que originou R1) ✅

### Desbloqueia
- PRP-WIZARD-1B (HITL — serializa `<user_response>` e `<gate_result waiver>`)
- PRP-EVALS-F1 (serializa `<eval_metrics>`)

## 6. Definition of Done

- [x] `validate-tags.py` reconhece as 4 novas tags (+ filhos) com balanceamento, atributos e valores
- [x] Formato `<gate_result>` único (step/decision + waiver opcional) em validador, ADR-0002 e pipeline-design §8.4
- [x] 14 testes verdes; zero falsos positivos nas sessões históricas
- [x] Taxonomia §8.4 do pipeline-design atualizada
- [x] Sessão ACE registrada (2026-08-05-003)
