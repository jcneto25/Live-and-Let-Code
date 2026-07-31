# PRP: [GOV.3] — Métricas de Governança

> **ID:** PRP-GOV-003 | **Fase:** Evolução da Metodologia | **Onda:** 1
> **Owner:** Equipe LLC | **Reviewer:** Equipe LLC
> **Estimativa:** 2 dias | **Status:** ✅ Complete
> **Prioridade:** Alto | **Complexidade:** Média
> **Criado em:** 2026-07-30 | **Última atualização:** 2026-07-30 | **Versão:** v1.0

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O artigo sugere que o indicador correto não é volume de código nem número de tarefas, mas capacidade de transformar atividade agentica em progresso duravel. Sem métricas de governança, não é possível medir se o loop de Governance Conversion está funcionando — se falhas estruturais estão sendo convertidas em mecanismos duráveis com velocidade e eficácia.

Este PRP implementa duas métricas: `failure_to_control_lead_time` (velocidade do loop) e `structural_failure_recurrence_rate` (eficácia do loop).

### 1.2 O que é entregue?

- [ ] Script `python .ace/scripts/governance-metrics.py` que calcula as métricas a partir dos GOVs em `docs/governance/` e das sessões ACE
- [ ] Métrica `failure_to_control_lead_time`: tempo médio (dias) entre abertura do GOV e transição para addressed
- [ ] Métrica `structural_failure_recurrence_rate`: % de GOVs que reabrem após closed sobre total de GOVs closed
- [ ] Seção no relatório do step 11.4 com as métricas
- [ ] Integração opcional com `replay_stats.py` para dashboard unificado

### 1.3 O que NÃO está no escopo

- ❌ Métricas avançadas (governed_throughput, guardrail_coverage_by_module) → futuros PRPs
- ❌ Dashboard visual → futuros PRPs
- ❌ Alertas automáticos por reincidência → futuros PRPs

---

## 2. Requisitos Funcionais

| ID | Requisito | Critérios de Aceitação | Prioridade | Status | Arquivo(s) impl |
|----|-----------|------------------------|------------|--------|-----------------|
| RF-GOV-003.1 | Script calcula `failure_to_control_lead_time` | **Dado** GOVs em `docs/governance/`, **Quando** executa script, **Então** exibe média de dias entre `Data de abertura` e transição para addressed | Must | ✅ | `.ace/scripts/governance-metrics.py` |
| RF-GOV-003.2 | Script calcula `structural_failure_recurrence_rate` | **Dado** GOVs em `docs/governance/`, **Quando** executa script, **Então** exibe % de GOVs que reabriram após closed sobre total de GOVs closed | Must | ✅ | `.ace/scripts/governance-metrics.py` |
| RF-GOV-003.3 | Relatório do step 11.4 inclui métricas | Skill do step 11.4 possui seção que invoca script e exibe resultados no relatório de governança | Should | ✅ | `docs/skills/llc-step-11-4-governance-conversion.md` |

---

## 14. Definition of Done

- [x] Script criado em `.ace/scripts/governance-metrics.py`
- [x] `failure_to_control_lead_time` implementado e testado com GOVs de exemplo
- [x] `structural_failure_recurrence_rate` implementado e testado com GOVs de exemplo
- [x] Skill step 11.4 atualizado para invocar script e exibir métricas
- [x] `python .ace/scripts/governance-metrics.py` roda sem erros
