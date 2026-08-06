# PRP: [EVALS-F1] — Instrumentação de Tokens e Custo por Sessão ACE

> **ID:** PRP-EVALS-F1 | **Trilha:** Evals | **Onda:** 1
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ⏳ Pending
> **Prioridade:** Alto | **ADR de origem:** ADR-0005 §2.5, §2.1 P1

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Sem capturar tokens e custo por step, nenhuma análise de eficiência é possível. Este PRP é a camada de fundação do Eval Harness: instrumenta cada sessão ACE com métricas de custo, capturadas via fallback em 3 níveis (log nativo → parsing → estimativa), e persiste o bloco `<eval_metrics>` append-only na sessão.

### 1.2 O que é entregue

- [ ] `llc_evals/instrument.py` — captura em 3 níveis com `source` registrado
- [ ] Tag `<eval_metrics>` append-only no arquivo de sessão ACE (sem tocar frontmatter)
- [ ] `llc_evals/evaluators/efficiency_meter.py` — calcula `TokenCost` e `EfficiencyScore`
- [ ] Estrutura de diretórios `.ace/evals/` (baselines/, results/, golden/)
- [ ] Integração com `finalize_session.py` — **o append de `<eval_metrics>` é executado pelo finalize** (escritor único preservado — GOV-003/R8); `instrument.py` apenas calcula o bloco e o entrega, nunca escreve no arquivo da sessão

### 1.3 O que NÃO está no escopo

- ❌ `QualityScore` e `CodeEvaluator` → PRP-EVALS-F2
- ❌ LLM-as-judge → PRP-EVALS-F3
- ❌ Baselines e regressão → PRP-EVALS-F4

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-EF1.1 | Captura tokens via nível 1 (log nativo `.claude/`) | **Dado** log claude existente, **Quando** `instrument()`, **Então** `source="level_1"` e tokens precisos | Must | ⏳ | `tests/test_instrument.py` | `llc_evals/instrument.py` |
| RF-EF1.2 | Fallback para nível 2 (parsing de saída estruturada) | **Dado** log ausente mas output com usage block, **Quando** `instrument()`, **Então** `source="level_2"` | Must | ⏳ | `tests/test_instrument.py` | `llc_evals/instrument.py` |
| RF-EF1.3 | Fallback para nível 3 (estimativa tiktoken) | **Dado** nem log nem usage block, **Quando** `instrument()`, **Então** `source="level_3"` com estimativa | Must | ⏳ | `tests/test_instrument.py` | `llc_evals/instrument.py` |
| RF-EF1.4 | `<eval_metrics>` persiste append-only na sessão ACE — **escrita por `finalize_session.py`** (escritor único), nunca por `instrument.py` diretamente | **Dado** sessão aberta, **Quando** `finalize_session.py`, **Então** bloco XML adicionado sem modificar frontmatter **e** AST de `instrument.py` sem `open(..., "a")`/`write` em `sessions/` | Must | ⏳ | `tests/test_instrument.py` | `llc_evals/instrument.py` |
| RF-EF1.5 | `EfficiencyScore = QualityScore / log10(TokenCost)` calculado corretamente | **Dado** `QualityScore=86, TokenCost=15500`, **Quando** `efficiency_score()`, **Então** `≈18.9` | Must | ⏳ | `tests/test_efficiency_meter.py` | `llc_evals/evaluators/efficiency_meter.py` |
| RF-EF1.6 | Dados nível 3 marcados com tag `precision: estimated` | **Dado** instrumentação nível 3, **Quando** resultado, **Então** campo `precision: "estimated"` presente | Must | ⏳ | `tests/test_instrument.py` | `llc_evals/instrument.py` |

---

## 3. Formato `<eval_metrics>`

```xml
<eval_metrics timestamp="2026-08-05T10:00:00">
  step: "5"
  tokens_in: 12000
  tokens_out: 3500
  total_tokens: 15500
  cost_usd: 0.08
  duration_s: 45
  retries: 0
  source: "level_1"
</eval_metrics>
```

---

## 4. Estrutura de Arquivos

```
.ace/scripts/llc_evals/
├── __init__.py
├── instrument.py
└── evaluators/
    └── efficiency_meter.py
.ace/evals/
├── baselines/
├── results/
└── golden/
```

---

## 5. Dependências

### Bloqueado por
- PRP-ACE-TAGS ✅ (taxonomia `<eval_metrics>` reconhecida pelo `validate-tags.py` — GOV-003/R1)
- PRP-GOV-T3 (`tiktoken` N1 registrado na governança de dependências — fallback nível 3)

> **Correção (GOV-003/R6):** a dependência original em PRP-WIZARD-1A era artificial —
> sessões ACE já existem e são criadas pelo pipeline hoje, sem o Wizard. A integração
> real com o Wizard é a **exibição** de scores no Kanban (PRP-WIZARD-1.1), que já
> depende deste PRP — direção correta da seta. Este PRP pode rodar **em paralelo**
> ao WIZARD-1A.

### Desbloqueia
- PRP-EVALS-F2 (CodeEvaluator)
- PRP-WIZARD-1.1 (exibe scores no card Kanban)

---

## 6. Definition of Done

- [ ] Todos os 6 RF com testes verdes
- [ ] Captura funcional em pelo menos nível 3 (tiktoken como fallback universal)
- [ ] `<eval_metrics>` não toca frontmatter da sessão ACE
- [ ] `.ace/evals/` estrutura criada
- [ ] Dados nível 3 identificados como `precision: estimated`
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
