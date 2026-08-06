# PRP: [EVALS-F3] — DocJudge (LLM-as-Judge + Rubrics YAML por Step)

> **ID:** PRP-EVALS-F3 | **Trilha:** Evals | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 2 semanas | **Status:** ✅ Done (2026-08-06)
> **Prioridade:** Médio | **ADR de origem:** ADR-0005 §2.7, §2.6

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Steps documentais (Visão 0.5, Specs 1, PRDs 2, PRPs 3, ADRs 5) não são avaliáveis por testes ou fitness functions. O `DocJudge` usa LLM como avaliador estruturado contra rubrics explícitos — sem subjetividade livre, com saída JSON determinística. Transforma gates humanos "às cegas" em "revisão com score prévio".

### 1.2 O que é entregue

- [x] `llc_evals/evaluators/doc_judge.py` — LLM-as-judge com rubric estruturado
- [x] Rubrics YAML por step (`rubrics/rubric-step-{N}.yaml`) para steps 0.5, 1, 2, 3, 5
- [x] Prompt padrão que instrui o judge a retornar apenas JSON
- [x] Amostragem humana: estrutura para registrar calibração judge↔humano
- [x] Roteamento automático para steps documentais e arquiteturais

### 1.3 O que NÃO está no escopo

- ❌ Baselines de regressão para DocJudge → PRP-EVALS-F4
- ❌ Integração com plataformas externas (Braintrust, LangSmith) — conforme ADR-0005 D9

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-EF3.1 | `doc_judge.evaluate()` retorna JSON com score por dimensão | **Dado** artefato + rubric, **Quando** `evaluate()` (mockado), **Então** JSON `{dimensao: {score, reason}}` | Must | ✅ | `tests/test_doc_judge.py` | `llc_evals/evaluators/doc_judge.py` |
| RF-EF3.2 | `QualityScore` agregado pelos pesos do rubric | **Dado** scores por dimensão e pesos, **Quando** `aggregate_score()`, **Então** média ponderada ∈ [0,100] | Must | ✅ | `tests/test_doc_judge.py` | `llc_evals/evaluators/doc_judge.py` |
| RF-EF3.3 | Judge roda apenas em gates/amostragem (não a cada geração) | **Dado** step em execução, **Quando** mid-execution, **Então** judge NÃO é chamado (só no gate) | Must | ✅ | `tests/test_doc_judge.py` | `llc_evals/evaluators/doc_judge.py` |
| RF-EF3.4 | Rubrics YAML existem para steps 0.5, 1, 2, 3, 5 | **Dado** `step_id`, **Quando** `load_rubric(step_id)`, **Então** rubric carregado sem KeyError | Must | ✅ | `tests/test_doc_judge.py` | `llc_evals/rubrics/` |
| RF-EF3.5 | Judge recebe artefato upstream para checar rastreabilidade | **Dado** artefato PRD + Visão upstream, **Quando** `evaluate()`, **Então** ambos incluídos no prompt | Should | ✅ | `tests/test_doc_judge.py` | `llc_evals/evaluators/doc_judge.py` |
| RF-EF3.6 | Output não-JSON do judge é tratado graciosamente | **Dado** LLM retorna texto livre, **Quando** `parse_response()`, **Então** erro registrado e score=None (não crash) | Must | ✅ | `tests/test_doc_judge.py` | `llc_evals/evaluators/doc_judge.py` |

---

## 3. Rubric Mínimo (Step 2 — PRD)

```yaml
# llc_evals/rubrics/rubric-step-2-prd.yaml
step: "2"
artifact: "PRD"
dimensions:
  - name: completude
    weight: 25
    criterion: "Todas as seções do template de PRD estão preenchidas?"
  - name: rastreabilidade
    weight: 25
    criterion: "Cada requisito traça até um módulo da Visão (Step 0.5)?"
  - name: testabilidade
    weight: 20
    criterion: "Os requisitos são verificáveis e mensuráveis?"
  - name: clareza
    weight: 15
    criterion: "Linguagem não ambígua, sem contradições internas?"
  - name: alinhamento_negocio
    weight: 15
    criterion: "Reflete os objetivos da Visão Estratégica?"
```

---

## 4. Dependências

### Bloqueado por
- PRP-EVALS-F2

### Desbloqueia
- PRP-EVALS-F4 (baselines para DocJudge)

---

## 5. Definition of Done

- [x] Todos os 6 RF com testes verdes (usando mock do LLM)
- [x] 5 rubrics YAML criados (steps 0.5, 1, 2, 3, 5)
- [x] Judge não roda fora de gates/amostragem
- [x] Saída não-JSON tratada graciosamente (sem crash)
- [x] `fitness-functions.py --all --strict` verde
- [x] Sessão ACE registrada

---

## 6. Nota de Execução (2026-08-06)

Entregue via TDD (sessão ACE `2026-08-06-015`, step 10.8 — Test Coverage Gate):

- **`llc_evals/evaluators/doc_judge.py`** — `DocJudge` (LLM-as-judge, RF-EF3.1),
  `aggregate_score()` (média ponderada pelos pesos, RF-EF3.2), `should_run()`
  (só gates/amostragem — D10, RF-EF3.3), `load_rubric()` (RF-EF3.4),
  `build_prompt()` (artefato + upstream no prompt — RF-EF3.5) e `parse_response()`
  (não-JSON gracioso, tolerante a code fences — RF-EF3.6). LLM injetado
  (tool-agnostic, D9).
- **5 rubrics YAML** em `llc_evals/rubrics/` (steps 0.5, 1, 2, 3, 5), schema do
  PRP §3 (dimensões com peso somando 100).
- **`HumanSampling`** — registra amostras judge↔humano e computa correlação de
  Pearson (meta ADR-0005 §7 ≥ 0.8).
- **15 testes novos** (suite do pacote Evals: 40 verdes). Suite completa
  **399 passed**, fitness **41/41**, DIP sem imports de `llc_wizard`/`llc_harness`.
  Cobertura do pacote **95%** (doc_judge 88%).
