# PRP: [EVALS-F4] — Baselines + Detecção de Regressão (Warm-up Incluído)

> **ID:** PRP-EVALS-F4 | **Trilha:** Evals | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ⏳ Pending
> **Prioridade:** Médio | **ADR de origem:** ADR-0005 §2.9 (política de warm-up D11, D12)

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com F1+F2+F3, o sistema coleta dados de qualidade e custo. Sem baselines, cada run é comparado com nada — sem detecção de regressão. Este PRP implementa a política de warm-up (N_MIN=5 antes de alertar, N_STABLE=10 para baseline confiável), separação por nível de precisão e alertas de regressão.

### 1.2 O que é entregue

- [ ] `llc_evals/aggregate.py` ampliado com gestão de baselines
- [ ] Arquivo de baseline por step em `.ace/evals/baselines/step-{id}.yaml`
- [ ] Política de warm-up: fases `collecting → warmup → stable`
- [ ] Separação de baselines por nível de precisão (level_1 vs level_3 separados)
- [ ] Alertas com tag `[baseline-unstable]` na fase warmup
- [ ] Reset automático ao migrar de nível 3 para nível 1

### 1.3 O que NÃO está no escopo

- ❌ Dashboard visual Pareto → PRP-EVALS-F5
- ❌ Golden datasets formais (criados manualmente conforme necessidade)

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-EF4.1 | Sem alerta de regressão se `run_count < N_MIN` | **Dado** 3 runs (N_MIN=5), **Quando** `check_regression()`, **Então** nenhum alerta emitido | Must | ⏳ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.2 | Alerta `[baseline-unstable]` se `N_MIN ≤ run_count < N_STABLE` | **Dado** 7 runs (N_STABLE=10), **Quando** `check_regression()` detecta delta, **Então** alerta com tag | Must | ⏳ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.3 | Alerta normal quando `run_count ≥ N_STABLE` | **Dado** 12 runs, **Quando** delta negativo, **Então** alerta sem tag | Must | ⏳ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.4 | `EfficiencyScore` só compara runs do mesmo nível | **Dado** mix de level_1 e level_3, **Quando** regressão calculada, **Então** level_1 vs level_1 apenas | Must | ⏳ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.5 | Baseline resetado ao migrar de level_3 para level_1 | **Dado** step com 8 runs level_3, **Quando** run level_1 chega, **Então** `run_count` resetado | Must | ⏳ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.6 | `N_MIN` e `N_STABLE` configuráveis em `gates.json` | **Dado** config customizado, **Quando** aggregate instanciado, **Então** usa valores do config | Should | ⏳ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |

---

## 3. Formato do Baseline

```yaml
# .ace/evals/baselines/step-5.yaml
step: "5"
run_count: 7
baseline_phase: "warmup"       # collecting | warmup | stable
warmup_config: { n_min: 5, n_stable: 10 }
by_precision_level:
  level_1:
    run_count: 3
    quality_score_avg: 84.2
    token_cost_avg: 14800
  level_3:
    run_count: 4
    quality_score_avg: 81.0
    token_cost_avg: 15200
    precision: "estimated"
```

---

## 4. Dependências

### Bloqueado por
- PRP-EVALS-F3

### Desbloqueia
- PRP-EVALS-F5

---

## 5. Definition of Done

- [ ] Todos os 6 RF com testes verdes
- [ ] Warm-up respeitado — zero alertas em run_count < N_MIN
- [ ] Separação por nível sem mistura de dados
- [ ] Reset de baseline documentado e testado
- [ ] `N_MIN` e `N_STABLE` configuráveis
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
