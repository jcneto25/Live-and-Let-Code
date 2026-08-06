# PRP: [EVALS-F4] — Baselines + Detecção de Regressão (Warm-up Incluído)

> **ID:** PRP-EVALS-F4 | **Trilha:** Evals | **Onda:** 2
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ✅ Done (2026-08-06)
> **Prioridade:** Médio | **ADR de origem:** ADR-0005 §2.9 (política de warm-up D11, D12)

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com F1+F2+F3, o sistema coleta dados de qualidade e custo. Sem baselines, cada run é comparado com nada — sem detecção de regressão. Este PRP implementa a política de warm-up (N_MIN=5 antes de alertar, N_STABLE=10 para baseline confiável), separação por nível de precisão e alertas de regressão.

### 1.2 O que é entregue

- [x] `llc_evals/aggregate.py` ampliado com gestão de baselines
- [x] Arquivo de baseline por step em `.ace/evals/baselines/step-{id}.yaml`
- [x] Política de warm-up: fases `collecting → warmup → stable`
- [x] Separação de baselines por nível de precisão (level_1 vs level_3 separados)
- [x] Alertas com tag `[baseline-unstable]` na fase warmup
- [x] Reset automático ao migrar de nível 3 para nível 1

### 1.3 O que NÃO está no escopo

- ❌ Dashboard visual Pareto → PRP-EVALS-F5
- ❌ Golden datasets formais (criados manualmente conforme necessidade)

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-EF4.1 | Sem alerta de regressão se `run_count < N_MIN` | **Dado** 3 runs (N_MIN=5), **Quando** `check_regression()`, **Então** nenhum alerta emitido | Must | ✅ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.2 | Alerta `[baseline-unstable]` se `N_MIN ≤ run_count < N_STABLE` | **Dado** 7 runs (N_STABLE=10), **Quando** `check_regression()` detecta delta, **Então** alerta com tag | Must | ✅ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.3 | Alerta normal quando `run_count ≥ N_STABLE` | **Dado** 12 runs, **Quando** delta negativo, **Então** alerta sem tag | Must | ✅ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.4 | `EfficiencyScore` só compara runs do mesmo nível | **Dado** mix de level_1 e level_3, **Quando** regressão calculada, **Então** level_1 vs level_1 apenas | Must | ✅ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.5 | Baseline resetado ao migrar de level_3 para level_1 | **Dado** step com 8 runs level_3, **Quando** run level_1 chega, **Então** `run_count` resetado | Must | ✅ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |
| RF-EF4.6 | `N_MIN` e `N_STABLE` configuráveis em `gates.json` | **Dado** config customizado, **Quando** aggregate instanciado, **Então** usa valores do config | Should | ✅ | `tests/test_aggregate.py` | `llc_evals/aggregate.py` |

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

- [x] Todos os 6 RF com testes verdes
- [x] Warm-up respeitado — zero alertas em run_count < N_MIN
- [x] Separação por nível sem mistura de dados
- [x] Reset de baseline documentado e testado
- [x] `N_MIN` e `N_STABLE` configuráveis
- [x] `fitness-functions.py --all --strict` verde
- [x] Sessão ACE registrada

---

## 6. Nota de Execução (2026-08-06)

Entregue via TDD (sessão ACE `2026-08-06-017`, step 10.8 — Test Coverage Gate):

- **`llc_evals/aggregate.py`** — `BaselineManager` (persistência em
  `.ace/evals/baselines/step-{id}.yaml`, RF-EF4.1-4.5) + `load_warmup_config()`
  (RF-EF4.6). `record_run()` mantém bucket por nível de precisão com médias
  móveis de QualityScore/TokenCost/EfficiencyScore; `check_regression()`
  compara **apenas o bucket do mesmo nível** (D12).
- **Fases (D11):** `collecting` (run_count < N_MIN → zero alertas) → `warmup`
  (alerta com tag `[baseline-unstable]`) → `stable` (alerta normal, sem tag).
- **Reset (RF-EF4.5):** migração level_3 → level_1/2 reseta o baseline
  (novo `active_precision` + warm-up recomeça do zero).
- **Config (RF-EF4.6):** `evals.baseline_warmup_min/stable` adicionados ao
  `.ace/config/gates.json` (defaults D11 5/10).
- **DIP:** imports apenas stdlib + `yaml` (registrado em dependencies.yaml) +
  `efficiency_meter` intra-pacote (reuso da fórmula EfficiencyScore — sem
  duplicação). Nenhuma dependência de `llc_wizard`/`llc_harness`.
- **11 testes novos** (RF-EF4.1-4.6 + formato §3 + defaults); suite Evals 54
  verdes. Suite completa **435 passed**, fitness **41/41**, cobertura TOTAL
  **95%** (aggregate 92%).

### Revisão pós-entrega (2026-08-06) — 3 correções + 1 bug de harness

1. **🔴 `active_precision` não é mais sobrescrito por run de precisão
   inferior (D12).** Um run level_3 isolado após baseline level_1 estável
   apagava todo o histórico no próximo run level_1 (reset espúrio). Agora
   `active_precision` só é definido no 1º run/reset; runs de precisão inferior
   vão para bucket próprio ("não excluídos, mas identificados").
2. **🟡 `precision` nos buckets (PRP §3/ADR §2.9):** `level_3` →
   `"estimated"`, demais → `"exact"` — testado.
3. **🟡 Config tolerante:** `evals` não-dict (lista), valores não-numéricos,
   arquivo ausente ou JSON corrompido → defaults D11 sem crash — testado.
4. **🐛 Bug latente do harness (`finalize_session/extract.py`):** o regex
   `<action([^>]*)>` casava `<action_log>` e engolia o 1º `<action>` real
   num fantasma `[type=?]` no context_seed (mascarado nas sessões 015/016
   pelo slice `[-5:]`). Fix: word boundary `\b` — descoberto nesta sessão,
   beneficia todas as sessões futuras.

Total final: **17 testes novos**; suite Evals **60 verdes**; suite completa
**441 passed**, fitness **41/41**, cobertura TOTAL **96%** (aggregate 95%).
