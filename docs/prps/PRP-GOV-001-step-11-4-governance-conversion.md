# PRP: [GOV.1] — Step 11.4: Governance Conversion

> **ID:** PRP-GOV-001 | **Fase:** Evolução da Metodologia | **Onda:** 1
> **Owner:** Equipe LLC | **Reviewer:** Equipe LLC
> **Estimativa:** Concluído | **Status:** ✅ Complete
> **Prioridade:** Crítico | **Complexidade:** Média
> **Criado em:** 2026-07-30 | **Última atualização:** 2026-07-30 | **Versão:** v1.0

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O artigo "Cheap Code, Costly Judgment" identifica que o LLC é forte em governança ex-ante, mas precisa institucionalizar a governança ex-post: o loop de converter falhas estruturais descobertas durante a execução agentica em mecanismos duráveis de governança. Este PRP cria o step 11.4 Governance Conversion como o momento formal do pipeline para revisar, classificar e tratar falhas estruturais.

### 1.2 O que é entregue?

- [x] Skill `docs/skills/llc-step-11-4-governance-conversion.md` — instrução completa para o agente executar o step
- [x] Step 11.4 adicionado ao `llc-pipeline-design.md` (diagrama mermaid + tabela de etapas)
- [x] Skill listada no catálogo de skills do pipeline
- [x] Gate 👤 11.4 adicionado à tabela de gates

### 1.3 O que NÃO está no escopo

- ❌ Scripts de automação do GOV lifecycle → PRP-GOV-004
- ❌ Métricas de governança → PRP-GOV-003

---

## 2. Requisitos Funcionais

| ID | Requisito | Critérios de Aceitação | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|------------------------|------------|--------|----------|-----------------|
| RF-GOV-001.1 | Agente deve ter skill para executar step 11.4 | Skill existe em `docs/skills/` com seções: classificação de falhas, registro GOV, instalação de mecanismo | Must | ✅ | — | `docs/skills/llc-step-11-4-governance-conversion.md` |
| RF-GOV-001.2 | Pipeline deve incluir step 11.4 | Diagrama mermaid mostra step 11.4 após 11.3; tabela de etapas lista step; catálogo de skills listado | Must | ✅ | — | `llc-pipeline-design.md` |
| RF-GOV-001.3 | Gate humano deve validar o step | Gate 👤 11.4 listado na tabela de gates com checklist | Must | ✅ | — | `llc-pipeline-design.md` |

---

## 14. Definition of Done (DoD)

- [x] Skill criada e revisada
- [x] Pipeline design atualizado (diagrama + tabela + skills + gates)
- [x] CONTEXT.md atualizado com termos do dominio

---

## 15. Execution Log

| Data | Status Anterior | Status Novo | Responsável | Motivo |
|------|-----------------|-------------|-------------|--------|
| 2026-07-30 | — | ✅ Complete | Agente + Equipe LLC | Sessão de grilling + domain modeling |

## Referências

- `docs/article-parallel-llc.md` § Prioridade 1
- `docs/skills/llc-step-11-4-governance-conversion.md`
- `CONTEXT.md` § Governance Conversion
- `docs/governance/GOV-TEMPLATE.md`
