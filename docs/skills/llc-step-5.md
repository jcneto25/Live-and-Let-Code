---
name: llc-step-5
version: 1.2.0
---

# LLC Skill: Step 5 — Arquitetura

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Architecture  
**Depende de:** Step 4 (Planejamento validado)  
**Sub-steps:** Step 5a (Architecture Patterns - **obrigatório**), Step 5b (API Design Enforcement - **obrigatório**), Step 5c (Clean Code Enforcement - **obrigatório**), Step 5d (Secure-by-Design - **obrigatório**)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-5` ou "Execute a skill llc-step-5".

## 📋 Pré-requisitos

- [ ] PRDs, specs e PRPs validados (Steps 1-3)
- [ ] `docs/planning/PLAN.md` (validado no Step 4)
- [ ] `docs/architecture/ARCHITECTURE_TEMPLATE.md` (template expandido v1.2+)
- [ ] `docs/architecture/ADR_TEMPLATE.md` (template de ADR individual)
- [ ] `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` (template de padrões — **Step 5a**)
- [ ] `docs/business/specs/requisitos_nao_funcionais.md`
- [ ] `docs/business/specs/catalogo_integracoes.md`
- [ ] `docs/business/specs/perfis_permissoes.md`

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 5** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-5.md`:
     ```markdown
     # Skip Note: Step 5 — Arquitetura
     **Decisão:** Step pulado — stack, ADRs e decisões arquiteturais inalterados.
     **Gate 6:** ✅ Auto-aprovado (reaproveitando aprovação anterior de {data})
     ```
   - **PARE** e informe: "Step 5 pulado via Smart Skip. ARCHITECTURE.md existente reaproveitado. Gate 6 auto-aprovado."
3. Se **Step 5** estiver listado como "executar": gere ARCHITECTURE.md v2, incluindo chancela de ADRs alterados e seção "O que mudou desde v1".
4. Se DELTA_REPORT.md não existir: prossiga normalmente.

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
- **Cada ADR é um arquivo separado** em `docs/architecture/adr/ADR-{NNN}-{nome}.md`.
- Use o template `docs/architecture/ADR_TEMPLATE.md`.
- Gere o índice de ADRs na §8 do ARCHITECTURE.md (tabela com links para cada arquivo).
- Mínimo de 5 ADRs cobrindo: stack frontend, stack backend, banco de dados, estratégia de autenticação, comunicação entre módulos.

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

### 7. Camada de Domínio e Ports & Adapters
- Defina a estrutura de diretórios intra-módulo: `domain/`, `application/`, `infrastructure/`
- Documente as regras da Dependency Rule: domínio não importa infra
- Inclua exemplo de Repository Pattern com interface (`I{nome}Repository`) e implementação concreta
- Inclua exemplo de Use Case com `execute(dto)`

### 8. Comunicação entre Módulos
- Defina o barramento de eventos: EventEmitter2 para monólito modular, RabbitMQ/Redis para microserviços
- Documente a matriz de eventos por módulo (publisher → subscriber)

### 9. Fitness Functions
- Gere `.ace/arch-config.yaml` com `core_modules` e thresholds
- Liste os módulos core (auth, usuarios, etc.) — estes terão enforcement block
- Documente como executar as fitness functions antes do merge:
  ```
  python .ace/scripts/fitness-functions.py --all --strict
  ```

### 10. Sub-Steps Obrigatórios: 5a, 5b, 5c, 5d

**Após concluir o Step 5, você DEVE executar quatro sub-steps obrigatórios antes de prosseguir para o Step 6:**

#### Step 5a — Architecture Patterns (`llc-step-5a-architecture-patterns`)

- Usa o template `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md`
- Define: Clean Architecture layers, Repository Pattern, Domain Layer puro, Use Cases, Event Bus
- Gera/atualiza: `ARCHITECTURE.md` §7, §8, §9 + `.ace/arch-config.yaml` + ADRs 008–011
- **Gate 6a** — obrigatório antes do Step 5b

> ⚠️ **Não prossiga para o Step 5b sem completar o Step 5a.** Os padrões definidos no 5a são vinculantes e verificados por fitness functions automatizadas.

#### Step 5b — API Design Enforcement (`llc-step-5b-api-design`)

- Valida REST semantics, naming consistency, pagination, OpenAPI spec, HATEOAS, versioning
- Gera: `docs/api/openapi.yaml` + valida controllers contra template padronizado
- **Gate 6b** — obrigatório antes do Step 5c

> ⚠️ **Não prossiga para o Step 5c sem completar o Step 5b.** Os contratos de API definidos no 5b são vinculantes para a execução dos PRPs.

#### Step 5c — Clean Code Enforcement (`llc-step-5c-clean-code`)

- Consolida regras de Functions, Classes, Naming, Errors, Smells, ReadModels
- Executa 21+ fitness functions automatizadas (`--check-functions`, `--check-naming`, `--check-classes`, `--check-errors`, `--check-smells`, `--check-readmodels`)
- **Gate 8.5** — obrigatório antes do Step 5d

> ⚠️ **Não prossiga para o Step 5d sem completar o Step 5c.** As regras de Clean Code são verificadas por fitness functions em todo o pipeline de execução.

#### Step 5d — Secure-by-Design Enforcement (`llc-step-5d-secure-by-design`)

- Estabelece 10 hard gates de segurança (NUNCA hardcode secrets, NUNCA SQL com interpolação, etc.)
- Executa threat modeling check (6 perguntas obrigatórias por feature)
- Gera 4 safe code templates (piiEncryption, secureStorage, parameterizedQueries, entitlementValidation)
- Configura 5 fitness functions de segurança (`--check-security`)
- Gera: `.ace/arch-config.yaml` expandido com `security_rules`, `docs/architecture/adr/ADR-0018-secure-by-design.md`
- **Gate 5d** — obrigatório antes do Step 6

> ⚠️ **Não prossiga para o Step 6 sem completar o Step 5d.** As regras de Secure-by-Design são injetadas em toda sessão subsequente de geração de código.

### 11. Saída
- `docs/architecture/ARCHITECTURE.md` — documento principal (preencher template expandido)
- `docs/architecture/adr/ADR-0001-*.md` a `ADR-0005-*.md` — ADRs individuais (Step 5)
- `docs/architecture/adr/ADR-0008-*.md` a `ADR-0011-*.md` — ADRs de padrões (Step 5a)
- `.ace/arch-config.yaml` — configuração das fitness functions (Step 5a)
- `docs/api/openapi.yaml` — spec OpenAPI com REST semantics, paginação, versionamento (Step 5b)
- ADRs de decisões de Clean Code (Step 5c)
- `docs/architecture/adr/ADR-0018-secure-by-design.md` — 10 hard gates, threat modeling, safe code templates (Step 5d)
- `.ace/arch-config.yaml` expandido com `security_rules` (Step 5d)

---

## ⚠️ REGRAS CRÍTICAS

1. **Decisões justificadas:** Toda escolha tecnológica deve ter justificativa e alternativas descartadas.
2. **RNFs endereçados:** Cada requisito não-funcional deve ser coberto por uma decisão arquitetural.
3. **Realista:** Stack deve ser compatível com o ambiente institucional (restrições de infraestrutura, orçamento).
4. **Diagramas:** Use Mermaid para todos os diagramas — são versionáveis e geráveis por IA.
5. **Idempotência:** Verifique existência do arquivo de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os artefatos, **PARE** e apresente:

1. **Stack Summary:** Tabela resumo das tecnologias escolhidas.
2. **ADRs:** Lista dos ADRs gerados como arquivos individuais (`docs/architecture/adr/ADR-*.md`).
3. **Domain Layer:** Estrutura de domínio, use cases e interfaces definidas.
4. **Fitness Config:** `.ace/arch-config.yaml` gerado com módulos core e thresholds.
5. **Diagramas:** Confirmação dos diagramas C4 gerados.
6. **RNF Coverage:** Cada RNF dos specs foi endereçado?
7. **Riscos Arquiteturais:** Tabela de riscos identificados.
8. **Próximos Passos:** Perguntas para validação humana (foco em trade-offs e viabilidade).

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
