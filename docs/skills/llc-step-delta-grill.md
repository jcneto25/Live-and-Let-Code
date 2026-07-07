---
name: llc-step-delta-grill
description: Step Δ.1 — Grill Me de Mudança: IA faz até 8 perguntas focadas no delta entre versões para resolver ambiguidades antes de gerar artefatos de alteração.
version: 1.0.0
tags: [delta, change, grill-me, specification, llc-pipeline]
---

# LLC Skill: Step Δ.1 — Grill Me de Mudança

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Change Management — Ambiguity Resolution  
**Pré-requisito:** Step Δ.0 concluído e `docs/planning/DELTA_REPORT.md` aprovado (Gate Δ.0).  
**Quando usar:** Após o DELTA_REPORT.md estar aprovado, ANTES de gerar qualquer artefato de alteração (addendum de visão, specs diff, PRPs de alteração).  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `docs/skills/` do projeto (já está lá).
2. Invoque no chat: `@llc-step-delta-grill` ou "Execute a skill llc-step-delta-grill".
3. **IMPORTANTE:** Ative o modo thinking/extended reasoning da sua LLM — perguntas de alta qualidade reduzem retrabalho nos gates seguintes.

## 📋 Pré-requisitos (Verificação Automática)

- [ ] `docs/planning/DELTA_REPORT.md` existe e foi aprovado (Gate Δ.0)
- [ ] Novos documentos em `docs/business/ingestion/converted/` disponíveis
- [ ] Artefatos da versão atual disponíveis (visão, specs, PRDs, PRPs, architecture, design_system)

*Se o DELTA_REPORT.md não existir, PARE e execute `@llc-step-delta-impact` primeiro.*

---

## 🎯 PROMPT DE EXECUÇÃO

Você está operando no modo de execução da skill `llc-step-delta-grill` do pipeline Live and Let Code (LLC). Seu objetivo é conduzir uma rodada de questionamento focada no **delta** entre a versão atual do sistema e os novos documentos de mudança.

**Diferente do Grill Me tradicional (Steps 0.5-3), que pergunta sobre o sistema como um TODO, este Grill Me é focado no delta — o que MUDA entre a versão atual e a proposta.**

### 1. Prepare a Análise

Antes de formular as perguntas, leia:

1. **DELTA_REPORT.md** — o relatório de impacto aprovado (entenda a classificação major/minor e o escopo)
2. **Novos documentos** em `docs/business/ingestion/converted/` — as mudanças propostas
3. **Artefatos da versão atual** — o que existe hoje:
   - `docs/business/specs/perfis_permissoes.md` (perfis atuais)
   - `docs/business/specs/catalogo_integracoes.md` (integrações atuais)
   - `docs/prps/` (PRPs existentes — entenda contratos de API atuais)
   - `docs/architecture/ARCHITECTURE.md` (stack e decisões atuais)
   - `docs/design/DESIGN_SYSTEM.md` (design atual)

### 2. Formule as Perguntas (Máximo 8)

Identifique ambiguidades, lacunas e contradições entre a versão atual e os novos documentos nas seguintes dimensões. Apresente ao usuário uma lista numerada de perguntas (máximo 8), ordenadas por criticidade:

#### Dimensão 1: Funcionalidades Existentes (sempre perguntar)

- 🔴 **Quais funcionalidades existentes são alteradas?** (não apenas as novas)
  - Ex: "O novo documento menciona 'fluxo de aprovação simplificado'. O fluxo atual tem 3 etapas. Quais etapas são removidas/alteradas?"
- 🟡 **Funcionalidades existentes que não são mencionadas nos novos docs devem permanecer como estão?**
  - Ex: "O relatório de impacto não menciona o módulo de relatórios. Ele permanece inalterado?"

#### Dimensão 2: Perfis e Permissões (perguntar se DELTA_REPORT apontar impacto)

- 🔴 **Perfis de usuário mudam?** (novo perfil, perfil removido, permissões alteradas)
  - Ex: "O novo documento menciona um 'auditor externo'. É um novo perfil? Quais permissões ele tem que os perfis existentes não têm?"
- 🟡 **Regras de acesso existentes são afetadas?**
  - Ex: "Atualmente, apenas ADMIN pode excluir. O novo fluxo permite que OPERADOR exclua registros? É uma mudança intencional?"

#### Dimensão 3: Contratos de API (perguntar se DELTA_REPORT apontar impacto em PRPs existentes)

- 🔴 **Contratos de API existentes mudam? Há breaking changes?**
  - Ex: "O PRP-003 define `GET /api/usuarios` retornando `{id, nome, email}`. O novo documento menciona 'dados completos do usuário'. Isso significa que o contrato muda? Campos obrigatórios novos?"
- 🟡 **Versionamento de API precisa ser introduzido?**
  - Ex: "Se há breaking changes, precisamos versionar a API (`/v1/`, `/v2/`) ou podemos migrar todos os consumidores de uma vez?"

#### Dimensão 4: Integrações (perguntar se DELTA_REPORT apontar impacto)

- 🟡 **Integrações existentes são afetadas?**
  - Ex: "O sistema atualmente integra com o Sistema X via webhook. O novo documento não menciona essa integração. Ela continua existindo?"
- 🟢 **Novas integrações são necessárias?**
  - Ex: "O novo documento menciona 'validação na base da Receita Federal'. É uma nova integração a ser construída?"

#### Dimensão 5: Modelo de Dados (perguntar se DELTA_REPORT apontar mudança)

- 🔴 **O modelo de dados existente muda? Migrações necessárias?**
  - Ex: "O PRP-007 define o campo `status` como `enum('ativo','inativo')`. O novo documento menciona 'status: pendente, ativo, suspenso, cancelado'. Confirma que o enum se expande?"
- 🟡 **Dados existentes precisam ser migrados?**
  - Ex: "Registros com `status='inativo'` devem ser mapeados para qual novo valor?"

#### Dimensão 6: Regras de Negócio (sempre perguntar)

- 🟡 **Regras de negócio existentes são alteradas?**
  - Ex: "A regra atual diz 'pedidos acima de R$ 10.000 requerem aprovação do gestor'. O novo documento diz 'acima de R$ 5.000'. Confirma a alteração?"

#### Dimensão 7: UI e Experiência (perguntar se UI for impactada)

- 🟢 **A UI existente é impactada?**
  - Ex: "O novo fluxo de aprovação adiciona uma etapa. Isso significa que a tela de aprovação atual precisa ser modificada?"

#### Dimensão 8: Requisitos Não-Funcionais (perguntar se DELTA_REPORT apontar mudança)

- 🟢 **Requisitos não-funcionais mudam?**
  - Ex: "O novo documento menciona 'tempo de resposta máximo de 2 segundos'. O RNF atual especifica 5 segundos. Confirma a redução?"

### 3. Regras de Condução

1. **NÃO faça todas as 8 perguntas de uma vez.** Priorize as 🔴 bloqueantes primeiro, depois 🟡 alta, depois 🟢 média. Cada rodada: 2-4 perguntas no máximo.

2. **Sugira 2-3 respostas possíveis** baseadas no contexto disponível para cada pergunta. Ex:
   > "O novo documento menciona 'auditor externo' — isso pode ser:
   > a) Um novo perfil com permissões de leitura em todos os módulos
   > b) Um perfil existente (CONSULTA) renomeado
   > c) Algo diferente — por favor, descreva"

3. **O usuário pode responder seletivamente** ou dizer **"prossiga com o que tem"** a qualquer momento. Neste caso, registre a ambiguidade como `[NÃO RESPONDIDO — validar com stakeholder]` nos artefatos gerados posteriormente.

4. **Se a resposta do usuário revelar que a classificação major/minor do DELTA_REPORT.md está errada**, registre a correção e recomende a reexecução do Step Δ.0:
   > "Sua resposta indica que a arquitetura é afetada, mas o DELTA_REPORT.md classificou como MINOR. Recomendo reexecutar o Step Δ.0 com esta informação."

5. **Registre cada pergunta e resposta** em um arquivo de sessão — o conteúdo alimentará os steps seguintes (0.5 addendum, specs diff, PRPs alterados).

---

## ⚠️ REGRAS CRÍTICAS

1. **Foco no delta, não no todo.** Não pergunte sobre funcionalidades que não mudaram. O Grill Me tradicional já cobriu a visão completa do sistema na primeira iteração.

2. **Apoie-se no DELTA_REPORT.md.** Cada pergunta deve ser justificável pelo relatório de impacto. Se o relatório não identificou uma ambiguidade que você enxergou, mencione isso.

3. **Perguntas de alta qualidade > quantidade.** 3 perguntas excelentes valem mais que 8 perguntas genéricas. Adapte ao domínio.

4. **Não presuma que o usuário lembra de todos os detalhes da versão atual.** Contextualize: "Atualmente, o PRP-003 define X. O novo documento diz Y. Pode confirmar a mudança?"

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após todas as rodadas de perguntas, **PARE** e apresente:

1. **Resumo das respostas:** Tabela com pergunta, resposta do usuário e impacto nos artefatos.
2. **Ambiguidades residuais:** O que ficou como `[NÃO RESPONDIDO]` e que precisará de validação posterior.
3. **Correções no DELTA_REPORT.md:** Se as respostas revelarem algo que muda a classificação ou o plano.
4. **Próximo passo recomendado:**
   - Se MAJOR: "Execute `@llc-step-0-5` para gerar addendum à visão estratégica (modo diff)."
   - Se MINOR: "Execute `@llc-step-3` para gerar PRPs de alteração (PRP-A-*)."

**NÃO gere artefatos de alteração neste step.** O Grill Me de Mudança é apenas para resolver ambiguidades — a geração vem nos steps seguintes.
