---
name: llc-step-5
description: Pipeline LLC Passo 5: Gera documento de Arquitetura (ARCHITECTURE.md) com stack, C4, ADRs, segurança e CI/CD.
version: 1.0.0
tags: [architecture, stack, llc-pipeline]
---

# LLC Skill: Step 5 — Arquitetura

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Architecture  
**Depende de:** Step 4 (Planejamento validado)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-5` ou "Execute a skill llc-step-5".

## 📋 Pré-requisitos

- [ ] PRDs, specs e PRPs validados (Steps 1-3)
- [ ] `docs/planning/PLAN.md` (validado no Step 4)
- [ ] `docs/architecture/ARCHITECTURE_TEMPLATE.md`
- [ ] `docs/business/specs/requisitos_nao_funcionais.md`
- [ ] `docs/business/specs/catalogo_integracoes.md`
- [ ] `docs/business/specs/perfis_permissoes.md`

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-5` do pipeline LLC. Seu objetivo é definir a arquitetura completa do sistema, incluindo stack tecnológico, diagramas C4, ADRs, segurança e estratégia de deploy.

### 1. Leia as Entradas
- Leia `docs/architecture/ARCHITECTURE_TEMPLATE.md` — estrutura a seguir.
- Leia `docs/prd/PRD_tecnico_institucional.md` — requisitos técnicos.
- Leia `docs/business/specs/requisitos_nao_funcionais.md` — performance, segurança, disponibilidade.
- Leia `docs/business/specs/catalogo_integracoes.md` — sistemas externos.
- Leia `docs/business/specs/perfis_permissoes.md` — modelo de autorização.
- Leia `docs/planning/PLAN.md` — ondas e milestones.

### 2. Defina o Stack Tecnológico
- **Frontend Web:** Framework, linguagem, UI library, state management, bundler, testing.
- **Mobile (se aplicável):** Framework, estratégia offline-first.
- **Backend:** Runtime, framework, ORM, cache, filas.
- **Banco de Dados:** SGBD, estratégia de migração, backups.
- **Infraestrutura:** Cloud/on-premise, containers, orquestração, CI/CD.
- Para cada tecnologia: versão, justificativa, alternativas consideradas e por que foram descartadas.

### 3. Diagramas C4
- **Level 1 (Contexto):** Sistema e seus atores/ sistemas externos.
- **Level 2 (Containers):** Aplicações, bancos, filas, storage.
- **Level 3 (Componentes):** Exemplo de um fluxo principal.

### 4. Architecture Decision Records (ADRs)
- Registre as decisões arquiteturais-chave no formato ADR.
- Mínimo de 5 ADRs cobrindo: stack frontend, stack backend, banco de dados, estratégia de autenticação, estratégia de integração.

### 5. Segurança e Compliance
- Medidas por camada (rede, aplicação, dados).
- Estratégia de autenticação e autorização (derivada de Perfis e Permissões).
- Criptografia (trânsito e repouso).
- Conformidade regulatória (LGPD, normas institucionais).

### 6. Estratégia de Deploy e CI/CD
- Ambientes (dev, staging, prod).
- Pipeline CI/CD (build, test, deploy).
- Estratégia de rollback.
- Monitoramento e observabilidade.

### 7. Salve
- Salve o documento completo em: `docs/architecture/ARCHITECTURE.md`.

---

## ⚠️ REGRAS CRÍTICAS

1. **Decisões justificadas:** Toda escolha tecnológica deve ter justificativa e alternativas descartadas.
2. **RNFs endereçados:** Cada requisito não-funcional deve ser coberto por uma decisão arquitetural.
3. **Realista:** Stack deve ser compatível com o ambiente institucional (restrições de infraestrutura, orçamento).
4. **Diagramas:** Use Mermaid para todos os diagramas — são versionáveis e geráveis por IA.
5. **Idempotência:** Verifique existência do arquivo de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar o documento, **PARE** e apresente:

1. **Stack Summary:** Tabela resumo das tecnologias escolhidas.
2. **ADRs:** Lista dos ADRs gerados com títulos.
3. **Diagramas:** Confirmação dos diagramas C4 gerados.
4. **RNF Coverage:** Cada RNF dos specs foi endereçado?
5. **Riscos Arquiteturais:** Tabela de riscos identificados.
6. **Próximos Passos:** Perguntas para validação humana (foco em trade-offs e viabilidade).

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
