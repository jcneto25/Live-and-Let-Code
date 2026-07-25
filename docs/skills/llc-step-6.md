---
name: llc-step-6
description: Pipeline LLC Passo 6: Gera TASKS.md com tarefas concretas, agentes atribuídos e estimativas para cada PRP.
version: 1.0.0
tags: [tasks, backlog, llc-pipeline]
---

# LLC Skill: Step 6 — Geração de Tarefas (TASKS.md)

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Task Breakdown  
**Depende de:** Step 5 (Arquitetura validada), Step 5d (Secure-by-Design validado)  
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

#### Regra: Cobertura de Testes por PRP

**Proporção obrigatória:** Para cada PRP, gerar tarefas de teste na proporção **1 tarefa de teste para cada 2 tarefas de implementação**.

| Tarefas de implementação (backend + frontend) | Tarefas de teste mínimas |
|:---------------------------------------------:|:------------------------:|
| 1-2 | 1 |
| 3-4 | 2 |
| 5-6 | 3 |
| 7+ | 4+ |

**Regra de mínimo absoluto:** TODO PRP com controller/service/module DEVE ter pelo menos 1 tarefa de teste unitário e, se expuser endpoint HTTP, 1 tarefa de teste de integração.

**Escopo:** As tarefas de teste devem ser distribuídas por ONDA — NÃO concentrar todas no primeiro PRP de cada onda. Se uma onda contém PRP-001, PRP-002 e PRP-003, cada um deve ter suas próprias tarefas de teste, mesmo que o primeiro já tenha cobertura.

#### Regra: Cross-Cutting Concern (CCC) de Autenticação Frontend

**Quando aplicar:** TODO PRP que incluir componentes de frontend (web ou mobile).

**Tarefas obrigatórias a incluir no TASKS.md (se ainda não existirem em PRP anterior):**
1. **AuthService** — Serviço centralizado de autenticação (login, logout, refresh, token storage)
2. **AuthGuard** — Guarda de rota autenticada (redirect para login se não autenticado)
3. **Interceptor de Refresh Token** — Interceptor que renova token expirado automaticamente e repete requisições falhas
4. **Teste unitário de cada um** — AuthService.spec, AuthGuard.spec, interceptor.spec

**Framework-agnóstico:** Angular (Guards/Interceptors), React (context + axios interceptors), Vue (router.beforeEach + axios), Svelte (stores + fetch wrapper), todas precisam destes 3 artefatos.

**Regra de acoplamento:** Identificar o PRP que primeiro declara frontend com autenticação (tipicamente o PRP de login ou layout dashboard) e alocar as 4 tarefas CCC lá. PRPs subsequentes com frontend apenas declaram dependência destas tarefas.

#### Regra: Setup de Design Tokens (Step 6 → Step 7 Handoff)

**Problema que previne:** O Step 7 (Design System) define bibliotecas de estilo (Tailwind, Bootstrap, Chakra, Material UI, etc.) mas Step 6 (Tarefas) não converte isso em tarefa de setup — então ninguém instala ou configura a biblioteca.

**Regra:** Durante a decomposição de PRPs em tarefas, verificar se `docs/architecture/ARCHITECTURE.md` declara uma estratégia CSS (framework de estilo). Se sim, incluir tarefa de instalação e configuração no setup:

| Stack CSS | Tarefa de setup necessária |
|-----------|---------------------------|
| Tailwind CSS | Instalar `tailwindcss`, `postcss`, `autoprefixer` + gerar `tailwind.config.ts` + import `globals.css` |
| Bootstrap | Instalar `bootstrap` + import SCSS + configurar tema |
| Chakra UI | Instalar `@chakra-ui/react` + `ChakraProvider` no root layout |
| Material UI | Instalar `@mui/material` + `ThemeProvider` com tokens do Design System |
| Styled Components | Instalar `styled-components` + configurar tema via `ThemeProvider` |
| Outro | Instalar pacote + configurar provider/tema conforme docs da lib |

**Localizar no TASKS.md:** A tarefa de setup de tokens deve ficar no mesmo PRP de scaffolding do frontend (tipicamente o PRP que cria o layout base ou o primeiro PRP com UI da Wave 1).

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
