# PRP: [EVALS-F5] — Dashboard Pareto (Custo × Qualidade) + Ranking de Ineficiência

> **ID:** PRP-EVALS-F5 | **Trilha:** Evals | **Onda:** 3
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** ⏳ Pending
> **Prioridade:** Baixo | **ADR de origem:** ADR-0005 §2.10 (Reporting)

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com F1–F4, o sistema coleta dados e detecta regressões. Mas "qual step é o maior gargalo de custo?" ainda não tem resposta visual. Este PRP entrega o relatório Pareto: ranking de steps por `EfficiencyScore` e `ReworkWaste`, integrado ao `code-health.py` existente.

### 1.2 O que é entregue

- [ ] `llc_evals/report.py` — relatório Markdown/JSON com Pareto por step
- [ ] Ranking: steps ordenados por `EfficiencyScore` (menor = pior custo-benefício)
- [ ] Ranking: steps ordenados por `ReworkWaste` (maior = mais tokens em retries)
- [ ] Integração com `code-health.py`: seção Eval adicionada ao relatório existente
- [ ] `llc eval --report` CLI subcommand

### 1.3 O que NÃO está no escopo

- ❌ Dashboard visual TUI (escopo do Wizard v1.2+)
- ❌ Integração com plataformas externas

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|----------------------|------------|--------|----------|-----------------|
| RF-EF5.1 | Ranking por `EfficiencyScore` correto | **Dado** 5 steps com scores distintos, **Quando** `rank_by_efficiency()`, **Então** ordenados do menor para o maior score | Must | ⏳ | `tests/test_report.py` | `llc_evals/report.py` |
| RF-EF5.2 | Ranking por `ReworkWaste` correto | **Dado** steps com retries, **Quando** `rank_by_rework_waste()`, **Então** ordenados do maior para o menor desperdício | Must | ⏳ | `tests/test_report.py` | `llc_evals/report.py` |
| RF-EF5.3 | `llc eval --report` gera arquivo `.ace/evals/results/report-{date}.md` | **Quando** `llc eval --report`, **Então** arquivo Markdown criado | Must | ⏳ | `tests/test_report.py` | `.ace/scripts/llc.py` |
| RF-EF5.4 | `code-health.py` inclui seção Eval quando dados disponíveis | **Dado** `code-health.py` executado com dados de eval, **Quando** relatório gerado, **Então** seção "Eval Summary" presente | Should | ⏳ | `tests/test_report.py` | `.ace/scripts/code_health/` |

---

## 3. Formato do Relatório

```markdown
# Eval Report — 2026-08-05

## Pareto: Eficiência por Step (pior → melhor)
| Step | QualityScore | TokenCost | EfficiencyScore | Fase |
|------|-------------|-----------|-----------------|------|
| 11   | 78          | 48000     | 14.1            | warmup |
| 5    | 86          | 15500     | 20.1            | stable |

## Pareto: Desperdício de Rework (maior → menor)
| Step | ReworkWaste% | Retries |
|------|-------------|---------|
| 3    | 34%         | 2       |
```

---

## 4. Dependências

### Bloqueado por
- PRP-EVALS-F4

### Desbloqueia
- Análise de gargalos disponível para o operador

---

## 5. Definition of Done

- [ ] Rankings por `EfficiencyScore` e `ReworkWaste` corretos e testados
- [ ] `llc eval --report` gera Markdown válido
- [ ] `code-health.py` inclui seção eval
- [ ] Relatório indica qual fase de baseline cada step está (`collecting/warmup/stable`)
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
