# PRP: [GOV.2] — GOV Template e Diretório de Governança

> **ID:** PRP-GOV-002 | **Fase:** Evolução da Metodologia | **Onda:** 1
> **Owner:** Equipe LLC | **Reviewer:** Equipe LLC
> **Estimativa:** Concluído | **Status:** ✅ Complete
> **Prioridade:** Crítico | **Complexidade:** Baixa
> **Criado em:** 2026-07-30 | **Última atualização:** 2026-07-30 | **Versão:** v1.0

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Falhas estruturais precisam de um artefato imortal para registro, rastreamento e medição de reincidência. Sem um artefato padronizado, a governança ex-post fica perdida em notas de sessão ou PRPs, sem rastreabilidade longitudinal. Este PRP cria o template GOV e o diretório `docs/governance/`.

### 1.2 O que é entregue?

- [x] Template `docs/governance/GOV-TEMPLATE.md` com campos: sintoma, contexto, classe, impacto, evidência, causa estrutural, decisão, mecanismo instalado, área afetada, validação posterior, status de reincidência
- [x] Diretório `docs/governance/` criado
- [x] Definições adicionadas ao `CONTEXT.md` (GOV, Autoridade de Conversão, Ciclo de Vida)

### 1.3 O que NÃO está no escopo

- ❌ Scripts de automação (criação automática de GOV, transição de status) → PRP-GOV-004
- ❌ Métricas de governaça → PRP-GOV-003

---

## 2. Requisitos Funcionais

| ID | Requisito | Critérios de Aceitação | Prioridade | Status | Arquivo(s) impl |
|----|-----------|------------------------|------------|--------|-----------------|
| RF-GOV-002.1 | Template GOV deve existir em `docs/governance/` | Arquivo `GOV-TEMPLATE.md` com campos definidos | Must | ✅ | `docs/governance/GOV-TEMPLATE.md` |
| RF-GOV-002.2 | Termos GOV no glossário | CONTEXT.md contém definições de GOV, Autoridade de Conversão, ciclo de vida open/addressed/closed | Must | ✅ | `CONTEXT.md` |

---

## 14. Definition of Done

- [x] Template criado com todos os campos
- [x] Diretório `docs/governance/` existe
- [x] CONTEXT.md atualizado

---

## 15. Execution Log

| Data | Status Anterior | Status Novo | Responsável | Motivo |
|------|-----------------|-------------|-------------|--------|
| 2026-07-30 | — | ✅ Complete | Agente + Equipe LLC | Sessão de grilling + domain modeling |
