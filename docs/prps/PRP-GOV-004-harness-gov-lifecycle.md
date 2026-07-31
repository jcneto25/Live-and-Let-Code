# PRP: [GOV.4] — Harness Integration para GOV Lifecycle

> **ID:** PRP-GOV-004 | **Fase:** Evolução da Metodologia | **Onda:** 2
> **Owner:** Equipe LLC | **Reviewer:** Equipe LLC
> **Estimativa:** 3 dias | **Status:** ✅ Complete
> **Prioridade:** Médio | **Complexidade:** Média
> **Criado em:** 2026-07-30 | **Última atualização:** 2026-07-30 | **Versão:** v1.0

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Atualmente o GOV é um artefato manual — o agente cria o arquivo Markdown durante o step 11.4. Para que o ciclo de vida do GOV seja sustentável em alta velocidade, o harness precisa oferecer:

1. Criação assistida de GOVs a partir de blockers e learning points
2. Injeção de contexto de GOVs abertos nas sessões (para que agentes saibam de falhas estruturais pendentes na área que estão alterando)
3. Transição automática de status (addressed → closed após N PRPs sem reincidência)

### 1.2 O que é entregue?

- [ ] `initialize_session.py` atualizado para injetar GOVs abertos relacionados aos arquivos-alvo da sessão
- [ ] Script `python .ace/scripts/gov-tools.py` com comandos:
  - `gov-tools.py list --status open` — lista GOVs por status
  - `gov-tools.py impact --files "src/X"` — mostra GOVs relacionados aos arquivos
  - `gov-tools.py check-recurrence` — varre sessões recentes para detectar reincidência de GOVs addressed
- [ ] Atualização do step 11.4 skill para usar `gov-tools.py`
- [ ] Integração com ACE: `<gov_reference id="GOV-001" status="addressed">` como tag parseável no contexto seed

### 1.3 O que NÃO está no escopo

- ❌ Transição automática de addressed → closed (exige decisão humana) → futuros PRPs
- ❌ Alertas proativos de reincidência → futuros PRPs
- ❌ Dashboard de governança → futuros PRPs

---

## 2. Requisitos Funcionais

| ID | Requisito | Critérios de Aceitação | Prioridade | Status | Arquivo(s) impl |
|----|-----------|------------------------|------------|--------|-----------------|
| RF-GOV-004.1 | GOVs abertos injetados no contexto da sessão | **Dado** sessão iniciada, **Quando** `initialize_session.py` executa, **Então** contexto inclui `<govs>` com GOVs abertos | Must | ✅ | `.ace/scripts/initialize_session.py` |
| RF-GOV-004.2 | Script gov-tools.py lista GOVs por status | **Dado** comando `gov-tools.py list --status open`, **Então** exibe tabela com ID, título, data de abertura | Must | ✅ | `.ace/scripts/gov-tools.py` |
| RF-GOV-004.3 | gov-tools.py mostra GOVs relacionados a arquivos | **Dado** comando `gov-tools.py impact --files "src/auth"`, **Então** exibe GOVs cuja área afetada inclui `src/auth` | Should | ✅ | `.ace/scripts/gov-tools.py` |
| RF-GOV-004.4 | gov-tools.py detecta reincidência | **Dado** comando `gov-tools.py check-recurrence`, **Então** varre sessões ACE em busca de blockers que correspondam a padrões de GOVs addressed | Should | ✅ | `.ace/scripts/gov-tools.py` |

---

## 14. Definition of Done

- [x] `initialize_session.py` injeta GOVs abertos no contexto
- [x] `python .ace/scripts/gov-tools.py` implementado com 3 comandos
- [x] Step 11.4 skill atualizado para usar `gov-tools.py`
- [x] Testes manuais: `gov-tools.py list`, `gov-tools.py impact`, `gov-tools.py check-recurrence` funcionam
