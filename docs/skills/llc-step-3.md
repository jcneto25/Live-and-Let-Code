---
name: llc-step-3
description: Pipeline LLC Passo 3: Gera PRPs (Project Requirement Proposals) a partir dos PRDs e Especificações validadas.
version: 1.0.0
tags: [prp, planning, llc-pipeline]
---

# LLC Skill: Step 3 — Project Requirement Proposals (PRPs)

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Decomposition  
**Depende de:** Step 2 (PRDs validados)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-3` ou "Execute a skill llc-step-3".

## 📋 Pré-requisitos

- [ ] `docs/prd/executive_PRD.md` e `docs/prd/PRD_tecnico_institucional.md` (validados no Step 2)
- [ ] 7 specs em `docs/business/specs/` (base de referência)
- [ ] `docs/prps/PRP_TEMPLATE.md`
- [ ] `docs/business/specs/MOD-*.md` (módulos validados)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-3` do pipeline LLC. Seu objetivo é decompor o sistema em contratos auto-contidos de implementação chamados PRPs (Project Requirement Proposals).

### O que é um PRP
Um PRP é um contrato completo para uma unidade de trabalho implementável. Ele contém: contexto, requisitos (Gherkin), API contracts, componentes, mudanças de banco, estratégia de testes, riscos e Definition of Done. Cada PRP deve ser auto-contido o suficiente para um agente de desenvolvimento executá-lo sem ambiguidade.

### 1. Leia as Entradas
- Leia os PRDs em `docs/prd/`.
- Leia os specs e módulos em `docs/business/specs/`.
- Leia `docs/prps/PRP_TEMPLATE.md` — estrutura que cada PRP deve seguir.

### 2. Decomponha em PRPs
- Analise specs, módulos e PRDs para identificar unidades de trabalho independentes.
- Cada módulo (MOD-XXX-NNN) tipicamente gera 1 a 5 PRPs, dependendo da complexidade.
- Use a nomenclatura: `PRP-[NNN]-[nome_descritivo].md`
  - NNN: número sequencial com 3 dígitos (001, 002, ...)
  - nome_descritivo: minúsculas com underscores
- Agrupe PRPs relacionados por módulo de origem.
- Salve cada PRP em: `docs/prps/PRP-001-[nome].md`, `docs/prps/PRP-002-[nome].md`, ...

### 3. Preencha Cada PRP
- **Contexto e Objetivo:** O que este PRP entrega e por quê.
- **Requisitos Funcionais:** Formato Gherkin (Given/When/Then) para cada cenário.
- **Requisitos Não Funcionais:** Performance, segurança, acessibilidade aplicáveis.
- **API Contracts:** Endpoints, payloads, autenticação, rate limits.
- **Componentes:** Props, estados (loading, empty, error, success), referência ao Design System.
- **Database Changes:** Tabelas, campos, índices, migrações.
- **Test Strategy:** Testes unitários, integração e E2E esperados.
- **Dependências:** Quais PRPs devem ser concluídos antes deste.
- **Riscos e Mitigações:** O que pode dar errado e como mitigar.
- **Definition of Done:** Checklist de aceitação.

### 4. Análise de Dependências
- Identifique dependências entre PRPs (A bloqueia B, B depende de C).
- Anote no campo `Dependências` de cada PRP: quais PRPs são pré-requisitos.
- Anote no campo `Bloqueia`: quais PRPs dependem deste.

---

## ⚠️ REGRAS CRÍTICAS

1. **Auto-contido:** Um agente deve conseguir implementar o PRP lendo apenas este arquivo + templates referenciados.
2. **Granularidade:** Cada PRP deve ter entre 2 e 8 dias de esforço estimado. Se for maior, quebre em PRPs menores.
3. **Gherkin Obrigatório:** Todo requisito funcional deve ter pelo menos um cenário Gherkin.
4. **Rastreabilidade:** Cada PRP deve referenciar o(s) módulo(s) e spec(s) de origem.
5. **Idempotência:** Verifique existência dos arquivos de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os PRPs, **PARE** e apresente:

1. **Resumo:** Quantos PRPs gerados, organizados por módulo.
2. **Grafo de Dependências:** Diagrama Mermaid ou tabela mostrando relações entre PRPs.
3. **Estimativa Total:** Soma das estimativas de todos os PRPs em dias.
4. **PRPs sem dependências:** Quais podem começar imediatamente (execução paralela).
5. **Lacunas:** Algum módulo ou requisito dos PRDs não foi coberto por PRPs?
6. **Próximos Passos:** Perguntas para validação humana sobre granularidade, dependências e escopo.

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
