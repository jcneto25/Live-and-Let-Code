# PRP: [EVALS-F2] — CodeEvaluator (Agregação de Testes + Fitness + Coverage)

> **ID:** PRP-EVALS-F2 | **Trilha:** Evals | **Onda:** 1
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ✅ Done (2026-08-06)
> **Prioridade:** Alto | **ADR de origem:** ADR-0005 §2.6, §2.8

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Steps de código já possuem mecanismos de avaliação dispersos: testes, fitness functions, coverage, consistency-check. Nenhum agrega em um score único comparável entre execuções. O `CodeEvaluator` unifica esses mecanismos em `CodeQuality` — sem recriar nada, apenas agregando o que já existe.

### 1.2 O que é entregue

- [x] `llc_evals/evaluators/code_evaluator.py`
- [x] Fórmula: `CodeQuality = w1·pass_rate + w2·fitness_score + w3·coverage + w4·consistency`
- [x] Pesos configuráveis via `.ace/config/gates.json → evals.code_weights`
- [x] Roteamento automático para steps de código (categoria `code` e `test`)
- [x] `llc_evals/aggregate.py` com score por step + armazenamento em `.ace/evals/results/`

### 1.3 O que NÃO está no escopo

- ❌ LLM-as-judge → PRP-EVALS-F3
- ❌ Baselines e regressão → PRP-EVALS-F4

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-EF2.1 | `CodeQuality` calculado corretamente com pesos padrão | **Dado** `pass_rate=0.9, fitness=38/40, coverage=0.87, consistency=true`, **Quando** `code_evaluator.evaluate()`, **Então** score ∈ [0,100] correto (91.9) | Must | ✅ | `tests/test_code_evaluator.py` | `llc_evals/evaluators/code_evaluator.py` |
| RF-EF2.2 | Pesos configuráveis via `gates.json` | **Dado** pesos customizados, **Quando** evaluator instanciado, **Então** usa pesos do config | Should | ✅ | `tests/test_code_evaluator.py` | `llc_evals/evaluators/code_evaluator.py` |
| RF-EF2.3 | `aggregate.py` persiste resultado em `.ace/evals/results/` | **Dado** avaliação concluída, **Quando** `save_result()`, **Então** arquivo YAML criado | Must | ✅ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF2.4 | Determinismo — mesma entrada gera mesmo score | **Dado** inputs fixos, **Quando** `evaluate()` chamado N vezes, **Então** score idêntico | Must | ✅ | `tests/test_code_evaluator.py` | `llc_evals/evaluators/code_evaluator.py` |
| RF-EF2.5 | `FirstPassRate` e `ReworkWaste` calculados | **Dado** histórico de retries da sessão, **Quando** `aggregate()`, **Então** métricas corretas | Must | ✅ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |

---

## 3. Fórmula e Pesos Padrão

```python
# Pesos padrão (configuráveis em gates.json → evals.code_weights)
DEFAULT_WEIGHTS = {
    "pass_rate":    0.40,  # pytest pass rate
    "fitness":      0.30,  # fitness-functions.py score (checks passed / total)
    "coverage":     0.20,  # pytest --cov coverage %
    "consistency":  0.10,  # consistency-check.py pass/fail
}

CodeQuality = sum(w * score for w, score in zip(weights, scores)) * 100
```

---

## 4. Dependências

### Bloqueado por
- PRP-EVALS-F1

### Desbloqueia
- PRP-EVALS-F3 (DocJudge)
- PRP-WIZARD-1.1 (exibe `CodeQuality` no card Kanban)

---

## 5. Definition of Done

- [x] Todos os 5 RF com testes verdes
- [x] Determinismo confirmado (mesmo input → mesmo output)
- [x] Pesos configuráveis funcionam
- [x] Resultado salvo em `.ace/evals/results/step-{id}-{date}.yaml`
- [x] `fitness-functions.py --all --strict` verde
- [x] Sessão ACE registrada

> **Nota de execução (2026-08-06):** implementado em sessão 2026-08-06-013
> (step 10.8). 14 testes novos (25 no total da trilha evals); cobertura
> `code_evaluator.py` 94%, `aggregate.py` 100%, `instrument.py` 90% (TOTAL 95%);
> fitness 41/41; suite geral 370 passed. Roteamento code/test para steps
> `11`, `9`, `10.8`, `10.9` (ADR-0005 §2.6).
