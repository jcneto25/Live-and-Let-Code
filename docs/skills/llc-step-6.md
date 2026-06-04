---
name: llc-step-6
description: Pipeline LLC Passo 6: Gera TASKS.md com tarefas concretas, agentes atribuídos e estimativas para cada PRP.
version: 1.0.0
tags: [tasks, backlog, llc-pipeline]
---

# LLC Skill: Step 6 — Geração de Tarefas (TASKS.md)

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Task Breakdown  
**Depende de:** Step 5 (Arquitetura validada)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-6` ou "Execute a skill llc-step-6".

## 📋 Pré-requisitos

- [ ] PRPs em `docs/prps/` (validados no Step 3)
- [ ] `docs/planning/DEPENDENCY_MATRIX.md`, `docs/planning/EXECUTION_WAVES.md` (Step 4)
- [ ] `docs/architecture/ARCHITECTURE.md` (validado no Step 5)
- [ ] `docs/planning/TASKS_TEMPLATE.md`

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-6` do pipeline LLC. Seu objetivo é decompor cada PRP em tarefas concretas e acionáveis, prontas para execução por agentes de desenvolvimento.

### Por que a Arquitetura vem antes
A arquitetura define stack, frameworks, banco de dados e estrutura de projeto. As tarefas de scaffolding e setup inicial só podem ser escritas corretamente conhecendo essas decisões.

### 1. Leia as Entradas
- Leia `docs/planning/TASKS_TEMPLATE.md` — estrutura do documento de tarefas.
- Leia TODOS os PRPs em `docs/prps/` — base para decomposição.
- Leia `docs/architecture/ARCHITECTURE.md` — stack, padrões, estrutura de pastas.
- Leia `docs/planning/DEPENDENCY_MATRIX.md` e `docs/planning/EXECUTION_WAVES.md` — ordem e agrupamento.
- Leia `docs/design/Design_System_Master.md` — padrões de UI para tarefas de frontend.

### 2. Estruture o Documento
- Siga o template `TASKS_TEMPLATE.md`.
- Organize por fases/ondas conforme `EXECUTION_WAVES.md`.
- Dentro de cada onda, agrupe tarefas por PRP.

### 3. Decomponha Cada PRP em Tarefas
Para cada PRP, crie tarefas nos seguintes níveis:

**Setup / Scaffolding (se aplicável):**
- Inicializar estrutura de pastas do módulo
- Configurar dependências (packages, bibliotecas)
- Criar arquivos base (rotas, modelos, componentes vazios)

**Backend (se aplicável):**
- Modelagem de dados (entidades, migrações Prisma/ORM)
- Implementação de serviços (lógica de negócio)
- Implementação de controllers/rotas (API endpoints)
- Validação de entrada (schemas Zod/Yup)
- Testes unitários de serviços
- Testes de integração de controllers

**Frontend (se aplicável):**
- Criação de componentes (seguindo Design System)
- Implementação de estados (loading, empty, error, success)
- Integração com API (hooks/services)
- Testes de componente (Vitest + RTL)
- Testes de acessibilidade (jest-axe)

**Integração e QA:**
- Testes E2E para fluxos críticos
- Documentação de API (Swagger/OpenAPI)
- Revisão de segurança
- Verificação de Design System compliance

### 4. Atribua Metadados a Cada Tarefa
| Campo | Descrição |
|-------|-----------|
| **ID** | TASK-NNN (sequencial) |
| **PRP** | PRP de origem |
| **Onda** | Wave de execução |
| **Agente** | dev_agent, qa_agent, security_agent, ux_agent |
| **Paralelização** | ✅ (paralelo), ⚠️ (paralelo após setup), ❌ (sequencial) |
| **Dependências** | TASK-IDs que devem ser concluídas antes |
| **Estimativa** | Horas ou dias |
| **Prioridade** | Must / Should / Could |
| **Complexidade** | Baixa / Média / Alta |

### 5. Inclua Tarefas Transversais
- Setup inicial do repositório (monorepo, lint, type-check, CI/CD)
- Configuração de ambiente de desenvolvimento (Docker Compose)
- Scaffolding do projeto (estrutura de pastas conforme ARCHITECTURE.md)
- Documentação (README, guia de contribuição)

### 6. Salve
- Salve em: `docs/planning/TASKS.md`.

---

## ⚠️ REGRAS CRÍTICAS

1. **Tasks acionáveis:** Cada tarefa deve ser específica o suficiente para um agente executar sem ambiguidade.
2. **Cobertura total:** Todo PRP deve ter tarefas cobrindo backend, frontend, testes e documentação.
3. **Paralelismo explícito:** Marque claramente quais tarefas podem ser executadas em paralelo.
4. **Scaffolding primeiro:** Tarefas de setup e scaffolding devem vir no início da primeira onda.
5. **Idempotência:** Verifique existência do arquivo de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar o TASKS.md, **PARE** e apresente:

1. **Resumo:** Total de tarefas, distribuídas por onda e por agente.
2. **Paralelismo:** Quantas tarefas podem ser executadas em paralelo na primeira onda?
3. **Estimativa Total:** Soma das estimativas em horas/dias.
4. **Economia:** Tempo total sequencial vs. paralelo.
5. **Cobertura:** Todos os PRPs foram decompostos? Algum PRP tem menos de 3 tarefas?
6. **Próximos Passos:** Perguntas para validação humana sobre granularidade e atribuição de agentes.

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
