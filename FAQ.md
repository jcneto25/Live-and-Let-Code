# FAQ — Live and Let Code (LLC)

**Versao:** 1.5.0 — Junho 2026

---

## Conceitos Fundamentais

### O que é um workflow agentico de desenvolvimento?

É uma metodologia estruturada que utiliza agentes de IA especializados para colaborar ao longo do ciclo de vida do software — desde análise e requisitos até arquitetura, implementação e garantia de qualidade. Diferente do "vibe coding" (codificação informal por prompts), workflows agenticos definem papéis, artefatos, gates de qualidade e handoffs entre agentes. O LLC materializa isso em 21 skills, 15 human gates e um protocolo de continuidade de contexto (ACE).

### Como o LLC esta organizado arquiteturalmente?

O LLC se organiza em **5 camadas conceituais** que vao da fundacao a entrega:

| Camada | Responsabilidade | Principais mecanismos |
|--------|-----------------|----------------------|
| **1. Contexto** | Gerencia a janela de contexto, continuidade entre sessoes e compressao de tokens | ACE `<context_seed>`, Document Hierarchy, indice comprimido, prompt caching, append-only sessions |
| **2. Conhecimento** | Artefatos de dominio, especificacoes e decisoes arquiteturais | Visao estrategica, 7 specs, PRDs, PRPs, ARCHITECTURE.md (C4+ADRs), DESIGN_SYSTEM.md, USER_GUIDE.md |
| **3. Agentes** | Quem executa, como raciocina e com quais regras | AGENTS.md (protocolo epistemic, zonas, TDD, handoff), papeis por step, Grill Me, CODE-REVIEW |
| **4. Workflows** | Pipeline, gates de validacao e orquestracao | 14 steps + subfluxo, 15 human gates + checkpoint visual, execution waves, PRRS, dependency matrix |
| **5. Entrega** | Execucao paralela, qualidade estrutural e deploy | Git worktrees automaticos, code-health.py, mock data, CI/CD, DEPLOYMENT.md |

Cada camada depende da inferior: sem contexto bem gerido, o conhecimento nao cabe na janela; sem conhecimento estruturado, agentes nao tem direcao; sem agentes instruidos, workflows nao produzem qualidade; sem workflows orquestrados, a entrega nao e confiavel.

### O que é "vibe coding" e por que preciso de um workflow estruturado?

Vibe coding é uma abordagem informal de codificação com IA onde os requisitos são ad hoc e o contexto se perde facilmente. Funciona para experimentos rápidos, mas gera dívida técnica, código inconsistente e falta de governança. Workflows estruturados como o LLC substituem isso por especificações formais geradas por Grill Me, agentes especializados por etapa, artefatos persistentes versionados em git e gates de qualidade com validação humana obrigatória.

### O que é "context rot" (degradação de contexto)?

É o fenômeno onde a qualidade da IA cai à medida que a janela de contexto se enche: 0-30% = qualidade de pico; 50%+ = começa a apressar e cortar cantos; 70%+ = alucinações e requisitos esquecidos. O LLC resolve isso com o protocolo **ACE** (`<context_seed>` de ~300 tokens em vez de histórico completo de ~22.000 tokens) e com **PRPs auto-contidos** — cada agente de implementação recebe apenas o PRP que precisa executar, não o projeto inteiro.

### O que é Spec-Driven Development (SDD)?

É a prática de front-loading especificações estruturadas e legíveis por máquina (visão estratégica, specs, PRDs, PRPs) para que agentes de IA possam contribuir de forma confiável à base de código. No LLC, os Steps 0-GF a 3 produzem especificações em cascata com rastreabilidade total — da visão estratégica ao PRP, cada artefato referencia sua origem. O Grill Me garante que lacunas sejam expostas antes da geração, não descobertas depois.

### Como o LLC aperfeiçoa o Spec-Driven Development?

O SDD tradicional tem 5 críticas legítimas. O LLC foi desenhado para endereçar cada uma delas:

| Crítica ao SDD tradicional | Como o LLC resolve |
|---------------------------|-------------------|
| **1. Waterfall rígido e lento** — documentação pesada antes de qualquer código, 10x mais lento | O LLC **não é waterfall**. As 14 etapas são pipeline, não fase congelada. PRPs têm 2-8 dias e rodam em **ondas paralelas** assim que validados. O Grill Me é uma rodada curta de perguntas (~15 min), não meses de documentação. O MVP mockado (Step 8) entrega algo funcional e demonstrável em dias, não meses |
| **2. "Markdown Madness"** — milhares de linhas de documentação, 80% do tempo lendo Markdown | O ACE resolve isso: o `<context_seed>` comprime o estado em **4 campos (~300 tokens)**. Um agente de implementação recebe **apenas o PRP que vai executar** (~50-80 linhas), não o projeto inteiro. O `impact-analyzer.py` diz exatamente quais artefatos ler, eliminando leitura desnecessária |
| **3. Bugs persistentes e código insustentável** — mesmo com specs, código gerado contém erros triviais | **TDD embutido em cada PRP** + `code-health.py` + self-healing loop. A IA escreve teste → vê falhar → implementa → vê passar. Se falhar, o ciclo recomeça. O agente não entrega código sem teste passando. Métricas de Moved Code, Copy/Paste e Legacy Touch são monitoradas a cada onda |
| **4. Spec Drift** — código alterado manualmente quebra a "fonte única da verdade" | O `dependency-graph.yaml` + `impact-analyzer.py` detectam drift automaticamente: `git diff` → cruza com grafo → reporta quais artefatos estão desatualizados. **Não é manual.** O pre-commit hook alerta antes do commit. O `<gate_result>` força validação humana antes de prosseguir |
| **5. Obsolescência por modelos nativos** — frameworks externos se tornam redundantes conforme LLMs evoluem | O LLC **não é um framework externo** — é uma metodologia codificada em **skills Markdown tool-agnostic**. Se um modelo ganhar capacidade nativa de planejamento, os skills evoluem para usar essa capacidade. O LLC não compete com a LLM — ele a **orquestra** |

O resultado: o LLC mantém os benefícios do SDD (rastreabilidade, especificações formais, gates de qualidade) sem cair nas armadilhas do waterfall, da fadiga de documentação ou da obsolescência. **Especificação sim, burocracia não.**

### O que é PRRS (Prismatic Ranked Recursive Summarization)?

É o padrão arquitetural onde uma mesma fonte de dados é analisada sob **múltiplos ângulos simultâneos** (prismas) e depois converge em camadas de granularidade crescente. No LLC: os 7 specs do Step 1 são 7 prismas sobre a documentação de ingestion; os 2 PRDs do Step 2 são 2 prismas sobre os specs (executivo vs técnico); os N PRPs do Step 3 são N prismas sobre o PRD técnico.

### O que é ACE (Agentic Context Engineering)?

É o protocolo de continuidade entre sessões do LLC. Combina Markdown (legibilidade humana), tags XML (parseabilidade por máquina) e YAML front matter (metadados). Cada sessão produz um arquivo append-only em `.ace/sessions/` que nunca é reescrito. Ao final, um `<context_seed>` de 4 campos comprime o estado da sessão em ~300 tokens. A sessão seguinte carrega apenas esse seed, não o histórico inteiro.

### O que são Human Gates?

São pontos de validação humana obrigatórios no pipeline LLC. Nenhum step avança sem aprovação explícita do usuário. O LLC tem 15 human gates + 1 checkpoint visual (subfluxo de prototipagem) + checkpoints de QA na execução. Um gate reprovado retorna o fluxo ao passo anterior com `<gate_result decision="rejected">` registrado no ACE.

### O que é Grill Me?

É o protocolo de questionamento obrigatório que a IA executa nos Steps 0.5, 1, 2 e 3 ANTES de gerar qualquer artefato. A IA analisa os documentos de entrada, identifica ambiguidades e apresenta até 8 perguntas ordenadas por criticidade (🔴 bloqueante, 🟡 alta, 🟢 média). O usuário responde seletivamente e a IA então gera os artefatos com base nas respostas. Elimina o principal ponto de falha do "vibe coding": suposições não validadas.

> **Nota:** O fluxo **greenfield** (Step 0-GF, para projetos sem documentacao) usa um protocolo
> diferente: entrevista estruturada de ate **15 perguntas** em 4 dimensoes. O Grill Me (ate 8
> perguntas) e para resolver ambiguidades em documentos ja existentes — nao para gerar do zero.

### O que é um PRD? Por que há um PRD Executivo e um PRD Técnico?

PRD (Product Requirements Document) é o documento que formaliza os requisitos de um produto de software, servindo como contrato entre stakeholders e equipe de desenvolvimento. O LLC gera dois PRDs porque cada público precisa de um nível diferente de detalhe:

| PRD | Público | Conteúdo | Extensão típica |
|-----|---------|----------|-----------------|
| **Executivo** | Gestores, sponsors, stakeholders não-técnicos | Visão, objetivos de negócio, escopo macro, benefícios esperados, métricas de sucesso | ~100 linhas |
| **Técnico** | Arquitetos, desenvolvedores, QA | Stack proposto, requisitos detalhados, contratos de API, modelo de dados, integrações, restrições | ~400 linhas |

O PRD Executivo responde "por que estamos construindo isso?" e "qual o valor?". O PRD Técnico responde "como vamos construir?" e "quais são as restrições?". Ambos são gerados a partir dos mesmos 7 specs do Step 1 — é o PRRS em ação: mesma fonte, dois prismas diferentes.

### O que é um PRP?

PRP (Project Requirement Proposal) é o contrato auto-contido de implementação do LLC. Diferente de uma tarefa solta, um PRP contém TUDO que um agente de IA precisa para implementar uma unidade de trabalho sem ambiguidade:

- Contexto e objetivo da unidade
- Requisitos funcionais em formato Gherkin (Given/When/Then)
- Contratos de API (endpoints, payloads, autenticação, erros)
- Especificação de componentes (props, estados: loading, empty, error, success)
- Mudanças de banco de dados (tabelas, campos, índices, migrações)
- Estratégia de testes (unitários, integração, E2E)
- Dependências (quais PRPs bloqueiam este e quais este bloqueia)
- Riscos e mitigações
- Definition of Done (checklist de aceitação)

Um PRP típico tem 2 a 8 dias de esforço estimado. É granular o suficiente para um agente executar, mas completo o suficiente para não precisar consultar outros documentos durante a implementação.

### No que um PRP se diferencia de uma história de usuário?

| Dimensão | História de Usuário (Ágil) | PRP (LLC) |
|----------|---------------------------|-----------|
| **Formato** | "Como [perfil], quero [ação], para [benefício]" | Documento Markdown com 9 seções obrigatórias |
| **Contexto** | Depende do Product Owner e da sprint para detalhamento | Auto-contido — o agente lê apenas o PRP |
| **Requisitos** | Critérios de aceite em linguagem natural | Gherkin executável (Given/When/Then) |
| **API** | Não especificada — definida durante o desenvolvimento | Contratos de API documentados (método, endpoint, payload, erros) |
| **Componentes** | Não especificados | Props, estados e referência ao Design System |
| **Banco de dados** | Não especificado | Tabelas, campos, índices e migrações |
| **Testes** | Não especificados | Estratégia completa (unitários, integração, E2E) |
| **Dependências** | Implícitas no backlog | Explícitas: "bloqueado por PRP-002, bloqueia PRP-005" |
| **Estimativa** | Story points (relativos, subjetivos) | Dias (absolutos, calibrados com dados históricos) |
| **Validação** | Revisão humana na sprint review | DoD checklist + `<gate_result>` no ACE + testes automatizados |

A história de usuário é uma **promessa de conversa** — cabe ao time preencher as lacunas durante a sprint. O PRP é um **contrato executável** — o agente recebe, implementa e testa sem precisar perguntar nada. Um PRP equivale a uma história de usuário + especificação técnica + plano de testes + análise de riscos, tudo em um documento.

### Quais agentes são usados no LLC?

O pipeline LLC define papéis por etapa, não por pessoa. Cada papel é exercido pela IA quando o skill correspondente é executado:

| Papel | Skill LLC | Responsabilidade |
|-------|-----------|-----------------|
| **Analista de Negócio** | `llc-step-0-greenfield`, `llc-step-0-5` | Extrai conhecimento via entrevista ou documentos, gera visão estratégica e módulos |
| **Especificador** | `llc-step-1`, `llc-step-2` | Gera specs, glossário e PRDs (executivo + técnico) com Grill Me |
| **Arquiteto** | `llc-step-5` | Define stack, diagramas C4, ADRs, segurança e CI/CD |
| **Designer UX/UI** | `llc-step-7`, Subfluxo F1-F4 | Design System, wireframes, protótipos hi-fi |
| **Planejador** | `llc-step-3`, `llc-step-4` | Decompõe em PRPs, gera matriz de dependências e ondas de execução |
| **Desenvolvedor** | `llc-step-8`, Step 11, Subfluxo F5 | Setup do projeto, mock data, implementação de PRPs |
| **QA Engineer** | `llc-step-9`, `llc-code-health` | Estratégia de testes, thresholds, métricas de saúde estrutural |
| **Tech Writer** | `llc-step-10` | README, DEPLOYMENT, CLAUDE.md, AGENTS.md |
| **Orquestrador** | `llc-impact-analyzer`, `llc-ace-context` | Rastreabilidade, continuidade de contexto, análise de impacto cross-PRP |

Cada agente opera com contexto escopo restrito — recebe apenas os artefatos necessários para sua etapa, não o projeto inteiro.

### Preciso usar todos os agentes para todo projeto?

Não. Projetos pequenos (ex: single-page app, script CLI) podem condensar múltiplos papéis em menos skills. O LLC é modular — você pode pular steps que não se aplicam. O mínimo viável é: Step 0-GF (se greenfield) ou 0.5 → Step 1 → Step 6 (Tasks) → Step 11 (Execução). Projetos corporativos ou regulados se beneficiam do pipeline completo.

### Agentes substituem engenheiros humanos?

Não. Humanos definem direção, negociam escopo, supervisionam design e aprovam releases. Os agentes melhoram o retorno da atenção humana, não a substituem. O LLC formaliza isso com **human-in-the-loop** em todas as fases críticas: 15 human gates, 1 checkpoint visual e checkpoints de QA na execução. Nenhum step avança sem aprovação explícita.

### Como os agentes se comunicam entre si?

Através de **handoffs de artefatos persistentes** (visão estratégica, specs, PRDs, PRPs, arquitetura) versionados em Git, não por conversas em chat. O ACE (`<context_seed>`) comprime o estado da sessão em 4 campos para a sessão seguinte. O `dependency-graph.yaml` + `impact-analyzer.py` garantem que alterações em um artefato propaguem corretamente para os artefatos downstream. Cada agente recebe apenas o necessário para sua tarefa, otimizando o uso da janela de contexto.

---

## Fluxo de Trabalho e Fases

### Quais são as fases típicas de um workflow agentico?

Um workflow agentico completo cobre o ciclo de vida do software em 4 macro-fases, cada uma com agentes especializados e gates de validação:

| Macro-fase | Steps LLC | O que acontece |
|------------|-----------|----------------|
| **1. Descoberta e Especificação** | 0-GF a 3 | Levantamento de requisitos (ou entrevista greenfield), geração de specs, PRDs e PRPs com Grill Me |
| **2. Planejamento e Arquitetura** | 4 a 7 | Matriz de dependências, ondas de execução, arquitetura (C4 + ADRs), Design System |
| **3. Fundação e MVP** | 8 a 10 | Setup do projeto, camada mock (MSW), documentação de testes, steering files (CLAUDE.md/AGENTS.md) |
| **4. Execucao e Entrega** | 14 + Subfluxo | PRPs sem UI (agentes diretos), PRPs com UI (subfluxo F1-F6), code health, QA gates, deploy |

### O que é "Agentic Planning" e "Context-Engineered Development"?

São dois pilares complementares do LLC:

| Pilar | O que é | Como o LLC implementa |
|-------|---------|----------------------|
| **Agentic Planning** | Planejamento estruturado para maximizar paralelismo entre agentes | Steps 3-4: PRPs auto-contidos, matriz de dependências, ondas de execução com análise de caminho crítico |
| **Context-Engineered Development** | Desenvolvimento que preserva contexto entre sessões sem saturar a janela | ACE (`<context_seed>`), Grill Me (perguntas antes de gerar), PRPs como contratos isolados (agente não precisa do projeto inteiro) |

O Agentic Planning responde "o que fazer e em qual ordem". O Context-Engineered Development responde "como fazer sem perder o fio da meada entre sessões".

### Como funciona o workflow LLC passo a passo?

1. **Você carrega documentos** em `docs/business/ingestion/` (ou, se não tem docs, a IA entrevista você no fluxo greenfield)
2. **A IA converte** tudo para Markdown (Docling) e faz perguntas para preencher lacunas (Grill Me)
3. **A IA gera** visão estratégica, specs, PRDs e PRPs — cada etapa validada por você (human gates)
4. **A IA planeja** ondas de execução e define arquitetura, stack, Design System
5. **A IA configura** o projeto, cria dados mockados e documentação de testes
6. **Você aprova** e a IA implementa os PRPs em paralelo (PRPs com UI passam pelo subfluxo de prototipagem com checkpoint visual)
7. **Code health** monitora métricas estruturais; QA gates validam antes do deploy

### O que é "atomicidade agressiva" (aggressive atomicity)?

É o princípio de que cada unidade de trabalho deve ser pequena o suficiente para caber em ~50% de uma janela de contexto fresca, garantindo que o agente opere sempre na zona de qualidade de pico (0-30% de preenchimento). No LLC:

- **PRPs são dimensionados para 2-8 dias** de esforço — pequenos o suficiente para um agente concluir sem degradação de contexto
- **Ondas (waves) agrupam PRPs** de forma que o conjunto da onda não exceda a capacidade de contexto
- **PRPs independentes rodam em paralelo** (worktrees separados); PRPs dependentes aguardam a conclusão dos bloqueantes
- O `<context_seed>` de 4 campos garante que o agente retome exatamente de onde parou, sem recarregar histórico

### O que é decomposição em PRPs (equivalente a "sharding de épicos")?

É o processo de quebrar um PRD abrangente em unidades de desenvolvimento focadas e auto-contidas. No LLC, a cadeia de decomposição é:

```
PRD Técnico (~400 linhas)
    ↓ Step 0.5: decomposto em módulos (MOD-*)
Módulos (~100 linhas cada)
    ↓ Step 3: decompostos em PRPs (PRP-*)
PRPs (~50-80 linhas cada)
    ↓ Step 6: decompostos em tarefas (TASK-*)
Tarefas (checkboxes no TASKS.md)
```

Cada nível preserva o contexto completo necessário para sua execução, eliminando a necessidade de consultar o PRD original durante a implementação.

---

## Artefatos e Documentos

### Quais artefatos são produzidos no workflow LLC?

O pipeline LLC gera 25+ artefatos versionados, organizados por etapa:

| Etapa | Artefatos | Descrição |
|-------|-----------|-----------|
| 0.5 | `visao_estrategica_e_negocio.md`, `MOD-*.md` | Visão do sistema e especificação de módulos |
| 1 | 7 specs (`glossario.md`, `requisitos_funcionais.md`, `requisitos_nao_funcionais.md`, `regras_negocio.md`, `workflows_bpmn.md`, `perfis_permissoes.md`, `catalogo_integracoes.md`) | Especificações detalhadas cobrindo terminologia, funcionalidades, restrições, fluxos e integrações |
| 2 | `executive_PRD.md`, `PRD_tecnico_institucional.md` | PRD executivo (stakeholders) e técnico (desenvolvedores) |
| 3 | `PRP-*.md` | Contratos auto-contidos de implementação |
| 4 | `DEPENDENCY_MATRIX.md`, `PLAN.md`, `EXECUTION_WAVES.md` | Planejamento: matriz de dependências, plano de entregas e ondas de execução |
| 5 | `ARCHITECTURE.md` | Stack, diagramas C4, ADRs, segurança, CI/CD |
| 6 | `TASKS.md` | Tarefas concretas com agentes, estimativas e checkboxes |
| 7 | `DESIGN_SYSTEM.md` | Tokens, componentes, padrões de interface e acessibilidade |
| 8 | `mocks/` (data + handlers) | Dados mockados (JSON) + handlers MSW para MVP |
| 9 | `TESTING_GUIDE.md`, `COVERAGE_BASELINE.md`, `COVERAGE_PROGRESS.md` | Estratégia de testes, baseline e metas de cobertura |
| 10 | `README.md`, `DEPLOYMENT.md`, `CLAUDE.md`, `AGENTS.md` | Documentação do projeto, deploy e steering files |

### O que é um PLAN.md?

O `PLAN.md` é o documento de planejamento de entregas gerado no Step 4. Ele contém:

- **Roadmap e milestones:** fases do projeto com datas-alvo e status
- **Estratégia de deploy:** ambientes (dev, staging, prod) e pipelines
- **Definition of Done (DoD):** 10+ critérios que cada entrega deve satisfazer
- **Master PRP List:** todos os PRPs com estimativas (planejado vs. realizado)
- **Velocity tracker:** acompanhamento de velocidade da equipe/agentes
- **Documentação de planejamento:** links para design docs e PRPs

É o documento que responde "quando ficará pronto?" e "o que já foi entregue?".

### O que é um TASKS.md?

O `TASKS.md` é o backlog de desenvolvimento gerado no Step 6. Ele decompõe cada PRP em tarefas concretas e acionáveis:

- **Tarefas por PRP:** scaffolding, backend, frontend, testes, documentação
- **Agentes atribuídos:** cada tarefa indica qual agente a executa (dev, qa, security)
- **Paralelização explícita:** ✅ (paralelo), ⚠️ (após setup), ❌ (sequencial)
- **Checkboxes:** `[ ]` pendente, `[/]` em progresso, `[x]` concluído
- **Estimativas:** em horas ou dias por tarefa

O `<task_completed>` do ACE atualiza automaticamente os checkboxes ao final de cada sessão.

### O que é um DEPENDENCY_MATRIX.md?

O `DEPENDENCY_MATRIX.md` é o grafo de dependências entre PRPs gerado no Step 4. Ele contém:

- **Inventário de PRPs:** tabela mestre com ID, fase, estimativa, complexidade, status
- **Caminho crítico:** a sequência mais longa de PRPs dependentes que determina o prazo mínimo
- **Matriz de dependências:** tabela "Pode Começar Após" → "Bloqueia" para cada PRP
- **Diagrama Mermaid:** visualização do grafo completo de dependências
- **Riscos de dependência:** análise de impacto de atrasos em PRPs críticos
- **Alocação de capacidade:** distribuição de PRPs por onda e por agente

É o artefato que o `impact-analyzer.py` consulta para propagar mudanças.

### O que é um ARCHITECTURE.md?

O `ARCHITECTURE.md` é o documento de definição arquitetural gerado no Step 5. Ele contém:

- **Stack tecnológico:** frontend, backend, banco, infraestrutura com justificativas e alternativas descartadas
- **Diagramas C4:** contexto (Level 1), containers (Level 2), componentes (Level 3) — todos em Mermaid
- **ADRs (Architecture Decision Records):** decisões arquiteturais com contexto, decisão, consequências e alternativas
- **Estratégia de segurança:** autenticação, autorização, criptografia, compliance
- **CI/CD:** pipeline, ambientes, quality gates
- **Riscos arquiteturais:** registro de riscos com probabilidade, impacto e mitigação
- **Monitoramento e observabilidade:** métricas de negócio, SLIs, SLOs, logging

### O que é um DESIGN_SYSTEM.md?

O `DESIGN_SYSTEM.md` é o documento de design system gerado no Step 7 a partir do template expandido `Design_System_Master.md`. Ele contém:

- **Design tokens:** cores (light + dark mode), tipografia, espaçamento, elevação
- **Biblioteca de componentes:** 8+ componentes com variantes, estados e props TypeScript
- **Padrões de interface:** tabelas, formulários, navegação, feedback, dashboards
- **UI consciente de permissões:** ocultar, desabilitar, read-only por perfil
- **Micro-interações:** catálogo de animações com duração e easing
- **Matriz de estados:** estados universais (default, hover, focus, disabled, loading, error) por componente
- **Acessibilidade:** WCAG 2.1 AA, contraste, touch targets, aria labels

### Como os artefatos são versionados?

Todos os artefatos LLC são documentos Markdown persistentes versionados em **Git**, tratados como entregáveis de software de primeira classe:

- **Versionamento semântico:** cada artefato tem controle de versão no front matter ou footer
- **Rastreabilidade:** o `dependency-graph.yaml` mapeia relações entre artefatos; o `impact-analyzer.py` detecta quais precisam ser atualizados quando um artefato fonte muda
- **Revisão humana:** cada artefato passa por um human gate antes de ser considerado aprovado
- **Histórico imutável:** artefatos de sessão ACE (`.ace/sessions/`) são append-only — nunca reescritos
- **PRs e code review:** artefatos podem ser revisados como código, com diff legível no git

---

## Qualidade e Gates

### O que são "quality gates" (gates de qualidade)?

São checkpoints de transição de fase que verificam se cada artefato atende aos critérios definidos antes do próximo agente começar. No LLC, os gates são formais e registrados:

- **15 human gates:** um apos cada step de geracao (0.5 a 11). O humano revisa o artefato e decide: `approved`, `rejected` ou `conditional`
- **1 checkpoint visual:** no subfluxo de prototipagem (F4 → F5). O protótipo hi-fi não vira código sem aprovação visual explícita
- **Checkpoints de QA:** durante a execução (Step 11): score ≥ 7.0, cobertura ≥ thresholds, security audit aprovado

Cada decisão de gate é registrada no ACE via `<gate_result step="N" decision="approved|rejected|conditional" reviewer="...">`. Um gate reprovado retorna o fluxo ao passo anterior e registra `<blocker>`.

### Como garantir que o código gerado por IA seja de qualidade?

O LLC implementa 6 camadas de garantia de qualidade:

| Camada | Mecanismo LLC |
|--------|---------------|
| **1. Especificação antes do código** | Steps 0-GF a 3 geram specs, PRDs e PRPs detalhados com Grill Me — a IA não escreve uma linha de código antes que os requisitos estejam validados |
| **2. Agentes especializados por fase** | Cada etapa tem um agente com contexto restrito: o arquiteto não implementa, o dev não define requisitos |
| **3. Quality gates em cada transição** | 15 human gates + 1 checkpoint visual + QA gates — nenhum artefato avança sem validação |
| **4. TDD embutido nos PRPs** | Cada PRP define estratégia de testes (unitários, integração, E2E). O `code-health.py` monitora se agentes estão seguindo TDD |
| **5. Revisão por pares (humanos e agentes)** | `<gate_result>` humano + `llc-impact-analyzer` automatizado + pre-commit hooks de validação |
| **6. Rastreabilidade de requisitos a código** | Cadeia completa: Visão → Módulo → Spec → PRD → PRP → Tarefa → Commit. O `dependency-graph.yaml` + `impact-analyzer.py` garantem que mudanças propaguem corretamente |

### Como o TDD ajuda a evitar alucinações?

O TDD fornece um **alvo objetivo** contra o qual a IA itera. Sem ele, a IA pode gerar código que "parece certo" mas não funciona. Com TDD:

1. **Âncora de realidade:** o teste que falha é uma prova concreta de que o código ainda não funciona — a IA não pode alucinar que "já está pronto"
2. **Self-healing loop:** a IA escreve o teste → roda (falha) → implementa → roda (passa). Se falhar de novo, o ciclo recomeça. A IA se auto-corrige sem intervenção humana
3. **Prevenção de overfitting:** testes escritos antes do código reduzem o viés de "implementar só para passar no teste"
4. **Mitigação de regressão:** cada PRP tem testes obrigatórios. Se um agente quebrar algo, o teste falha imediatamente — não semanas depois em produção

O LLC reforça TDD em 3 níveis: `CLAUDE.md`/`AGENTS.md` (regra de ouro do desenvolvedor), `TESTING_GUIDE.md` (thresholds de cobertura: ≥ 80% unitários, ≥ 70% integração) e `code-health.py` (monitora se agentes estão adicionando código sem testes).

### Como evitar que agentes de IA criem código duplicado?

A causa principal da duplicação é o agente não saber o que já existe no repositório — a chamada "cegueira contextual". O LLC implementa 4 camadas de defesa:

| Estratégia | Mecanismo LLC | Como previne duplicação |
|-----------|---------------|------------------------|
| **1. Mapa da base de código** | `CLAUDE.md` + `AGENTS.md` documentam onde estão componentes, utilitários e padrões. `dependency-graph.yaml` + `dependency-graph.mmd` mapeiam a topologia completa de artefatos | A IA consulta o mapa antes de criar. Sabe que `src/components/ui/Button.tsx` existe e deve ser reutilizado, não recriado |
| **2. Análise de impacto pré-execução** | `impact-analyzer.py` cruza `git diff` com o grafo de dependências. O agente executa ANTES de implementar | A IA vê exatamente quais arquivos existentes são afetados pela mudança. Não cria `UserService2.ts` se `UserService.ts` já existe |
| **3. Planejamento antes do código** | Grill Me (Steps 0.5-3) força a IA a fazer perguntas antes de gerar. AGENTS.md exige "DOING/EXPECT/IF YES/IF NO" antes de cada ação | A IA anuncia o que vai criar ANTES de criar. O humano intercepta duplicações no plano, não no código |
| **4. Refatoração forçada por métricas** | `code-health.py` monitora Copy/Paste vs Moved Code. Se copy > moved, dispara alerta e sugere onda de refatoração cross-PRP | Duplicações que escaparam das camadas 1-3 são detectadas e corrigidas em ondas de refatoração programadas |

**Regra prática no LLC:** antes de criar qualquer arquivo novo, o agente deve verificar se a funcionalidade já existe em um PRP existente, um módulo compartilhado ou um utilitário documentado no `CLAUDE.md`. O `impact-analyzer.py --files "caminho/planejado" --json` deve ser executado como verificação pré-implementação.

### Como o LLC implementa o "learning loop" (ciclo de aprendizado)?

O learning loop é o mecanismo que transforma a experiência de desenvolvimento em conhecimento persistente, evitando que erros se repitam e que decisões se percam entre sessões. O LLC implementa as 4 camadas do ecossistema de aprendizado:

| Documento de aprendizado | Equivalente LLC | Frequência | Função |
|--------------------------|-----------------|-----------|--------|
| **Diário de decisões técnicas** | `ARCHITECTURE.md` (ADRs) + ACE `<learning_point>` → `memory/learning_points.md` | Por etapa / por descoberta | Registrar o "porquê" das decisões e promover aprendizados validados para memória cross-sessão |
| **Especificação viva (spec.md)** | `docs/business/specs/` + `docs/prd/` + `docs/prps/` | Por alteração de requisito | Fonte única da verdade sobre o comportamento do sistema. Artefatos versionados em git, atualizados pelo pipeline quando requisitos mudam |
| **Arquivo de progresso** | ACE `<context_seed>` (4 campos) + `.ace/sessions/YYYY-MM-DD-NNN.md` | Por sessão | Continuidade entre sessões. O `<context_seed>` comprime o estado em ~300 tokens. O `finalize_session.py` atualiza TASKS.md automaticamente |
| **Constituição do projeto** | `CLAUDE.md` + `AGENTS.md` | Por onda / quando regras mudam | Internalizar padrões e lições aprendidas de longo prazo. Gerados pelo Step 10 e atualizados quando a arquitetura evolui |

**O ciclo completo no LLC:**

```
Sessão N
  ↓ implementa, descobre, decide
  ↓ appenda <action>, <thinking>, <learning_point>
  ↓ finalize_session.py:
  ↓   → promove <learning_point priority="high"> → memory/learning_points.md
  ↓   → gera <context_seed> com state/pending/blockers/next_action
  ↓   → atualiza TASKS.md (checkboxes [x])
  ↓
Sessão N+1
  ↓ initialize_session.py carrega context_seed (~300 tokens)
  ↓ agente sabe exatamente: o que foi feito, o que falta, blockers, próximo passo
  ↓ não repete erros da sessão anterior
```

### O que é o "problema dos 70%" e como o LLC ajuda a combatê-lo?

O "problema dos 70%" (conceito de Addy Osmani, Google Chrome DX) descreve um padrão no desenvolvimento com IA: a IA gera ~70% do código em minutos — boilerplate, CRUD, padrões conhecidos — mas os 30% restantes (arquitetura, segurança, edge cases, integração, tratamento de erros) exigem esforço desproporcional, frequentemente maior que fazer tudo do zero.

**Causas raiz:**
- A IA otimiza para o happy path e ignora edge cases sistematicamente
- Falta grounding estrutural: a IA não "enxerga" o projeto inteiro, alucina APIs
- Loop sem feedback real: erro → IA chuta solução → novo erro → degradação de contexto
- O contexto da janela do LLM se polui com tentativas falhas (lost in the middle)

**Como o LLC mitiga cada causa:**

| Causa | Mecanismo LLC |
|-------|---------------|
| IA não vê o projeto inteiro | Ferramentas de grafo de código (ver seção de ferramentas complementares abaixo) fornecem dependências, assinaturas reais e análise de impacto |
| Falta de grounding estrutural | `context_seed` comprime estado essencial entre sessões; AGENTS.md força validação contra a realidade |
| Loop sem feedback real | TDD obrigatório: RED (entendeu?) → GREEN (funciona?) → REFACTOR (não quebrou nada?) |
| Degradação de contexto | ACE append-only: cada ação é atômica e verificável; `context_seed` mantém ~300 tokens de continuidade |
| Edge cases ignorados | TDD + Grill Me + especificação antes de geração (spec-driven) |
| IA não aprende com erros | `<learning_point>` registra lições; `<skill_feedback>` captura melhorias estruturais nos skills |
| Dívida técnica invisível | 15 human gates + QA checkpoints: cada artefato passa por validação explícita antes de prosseguir |

O LLC não tenta fazer a IA chegar a 100% sozinha. Ele combina IA + humano + ferramentas estruturais (grafos, testes, gates, memória persistente) para que o conjunto entregue 100% de valor com a IA cobrindo o que ela faz bem e o humano decidindo nos 30% críticos.

### O que é "human-in-the-loop"?

É o princípio de que humanos permanecem no controle em todas as decisões críticas do ciclo de desenvolvimento. Agentes de IA executam dentro de guardrails definidos por humanos — nunca os substituem. No LLC:

| Onde o humano decide | Mecanismo |
|---------------------|-----------|
| **Definir objetivos** | O humano descreve o sistema (ingestion) ou responde à entrevista greenfield |
| **Negociar escopo** | Grill Me: a IA pergunta, o humano responde. Suposições não validadas são bloqueadas |
| **Supervisionar design** | CHECKPOINT VISUAL no subfluxo F4 → F5: protótipo não vira código sem aprovação |
| **Aprovar releases** | 15 human gates + QA checkpoints: cada artefato e cada onda passam por validação explícita |
| **Registrar decisões** | `<gate_result>` no ACE fecha o loop de accountability |

Agentes melhoram o retorno da atenção humana — não a substituem. Um engenheiro que antes passava 4h escrevendo specs agora passa 30 minutos revisando e aprovando specs geradas pela IA.

### Como o LLC implementa hardening de seguranca OWASP Top 10?

O LLC dedica o **Step 11-OWASP** (`docs/skills/llc-step-11-owasp-security.md`) exclusivamente ao hardening OWASP Top 10:2021. Diferente do Step 11-Security — que executa ferramentas automatizadas (SCA, SAST, secrets scanning) **antes** da implementacao — o Step 11-OWASP executa verificacoes manuais/IA **depois** que o codigo esta escrito, inspecionando controles que ferramentas nao detectam.

**As 10 categorias verificadas:**

| Categoria | O que e verificado |
|-----------|-------------------|
| A01 — Broken Access Control | Middleware de auth em todas as rotas, RBAC/ABAC conforme `perfis_permissoes.md`, ownership check (usuario nao acessa recursos de outros) |
| A02 — Cryptographic Failures | Senhas com bcrypt/argon2 (nunca MD5/SHA1), TLS 1.2+, JWT com algoritmo seguro, secrets nunca hardcoded |
| A03 — Injection | SQL parametrizado (nunca concatenacao), shell injection, validacao de input (Zod/Pydantic), XSS (`dangerouslySetInnerHTML`) |
| A04 — Insecure Design | Rate limiting em endpoints sensiveis, lockout de conta, token de reset seguro (expiracao + uso unico), analise de riscos documentada |
| A05 — Security Misconfiguration | Headers HTTP (CSP, HSTS, X-Frame-Options), debug mode desabilitado em producao, stack traces nao expostos |
| A06 — Vulnerable Components | Dependencias sem CVEs com exploit publico, frameworks nao EOL, imagens de container atualizadas |
| A07 — Auth Failures | MFA para perfis criticos, sessoes com expiracao, sem enumeracao de usuarios, sem credenciais padrao |
| A08 — Integrity Failures | Lockfiles versionados (`package-lock.json`), CI/CD verifica integridade, sem `eval`/`unserialize` com input do usuario |
| A09 — Logging Failures | Logs de auditoria conforme `perfis_permissoes.md` §7.1, dados sensiveis nunca em logs, logs imutaveis |
| A10 — SSRF | URLs de requisicoes do servidor nao controladas pelo usuario, allowlist de dominios, bloqueio de redes internas |

**Classificacao e gate:**

| Severidade | Significado | Acao |
|-----------|-------------|------|
| 🔴 Critico | Ex: SQL concatenado com input do usuario, rota admin sem autenticacao | **Bloqueia release** — hotfix obrigatorio |
| 🟡 Alto | Ex: `dangerouslySetInnerHTML` sem sanitizacao, JWT com `alg: none` | **Gera ticket** — correcao na proxima sprint |
| 🟢 Medio | Ex: header CSP ausente, sem lockout de conta | **Backlog de melhoria** — priorizado pelo PM |
| ⚪ N/A | Sem codigo para verificar (fase de especificacao) | **Aprovado** — re-executar apos implementacao |

**Diferenca do Step 11-Security (pre-implementacao):** O Step 11-Security encontra vulnerabilidades em dependencias (SCA), padroes de codigo inseguros (SAST) e secrets expostos — tudo automatizado. O Step 11-OWASP complementa com verificacoes que exigem raciocinio: "este endpoint verifica se o usuario logado e o dono do recurso?" ou "este reset de senha expira e e de uso unico?". Ferramentas nao respondem essas perguntas — o hardening OWASP sim.

**Relatorio:** `docs/security/OWASP_HARDENING_REPORT.md` (gerado pela skill, versionado no repo).

**Exemplo real — Auditoria dos scripts do pipeline (2026-06-13):** O hardening OWASP foi executado contra os scripts Python do proprio pipeline LLC (`.ace/scripts/*.py`, 9 arquivos, ~85 KB). Resultados: A02 ✅ 0 secrets hardcoded; A03 ✅ 28 `subprocess.run()` com listas, zero `shell=True` ou `eval()`; A08 ✅ `yaml.safe_load()` apenas; A09 ✅ logs estruturados sem dados sensiveis; A10 ✅ zero network requests. Gate: APROVADO (0 criticos).

### Como funciona o pipeline de auditoria de seguranca no LLC?

O LLC tem **3 skills de seguranca** que operam em momentos diferentes do pipeline, formando uma barreira de protecao em camadas:

| Skill | Step | Quando executa | O que verifica | Gate |
|-------|------|---------------|----------------|------|
| `llc-step-11-security` | Step 11 | **Pre-implementacao** (antes de codar) | SCA (dependencias), SAST (Semgrep), Secrets (Gitleaks) | Bloqueia em CVSS >= 9.0 ou secret real |
| `llc-step-12-null-safety` | Step 12 | **Pre-implementacao** (antes de codar) | Nulabilidade nos PRPs: campos sem `?`/`Optional`, fallbacks ausentes, inconsistencias entre PRPs | Bloqueia em campos sem especificacao de nulabilidade |
| `llc-step-11-owasp-security` | Step 11-OWASP | **Pos-implementacao** (depois de codar) | Hardening OWASP Top 10: access control, crypto, injection, design, misconfig, auth, logging, SSRF | Bloqueia em 1+ verificacao critica |

**Fluxo completo de seguranca:**

```
Step 11-Security (pre-codigo)     Step 12-Null-Safety (pre-codigo)
        │                                    │
        ▼                                    ▼
   SCA + SAST + Secrets              Nulabilidade nos PRPs
        │                                    │
        ▼                                    ▼
   APROVADO ────────────────────────── APROVADO
        │                                    │
        └──────────────┬─────────────────────┘
                       ▼
              Implementacao dos PRPs
                       │
                       ▼
          Step 11-OWASP (pos-codigo)
                       │
                       ▼
              Hardening OWASP Top 10
                       │
                       ▼
          APROVADO → Release (Step 11-Release)
```

**Por que 3 skills separadas?**

1. **Ferramentas automatizadas primeiro (Step 11-Security):** Antes de escrever uma linha de codigo, o pipeline verifica se as dependencias tem CVEs, se ha secrets expostos e se o codigo existente tem padroes inseguros. Isso evita que o time construa sobre uma base vulneravel.

2. **Design seguro antes de codar (Step 12-Null-Safety):** Campos sem especificacao de nulabilidade sao a principal causa de `NullPointerException` e `Cannot read properties of null` em producao. O Step 12 valida que todo campo nos PRPs declara explicitamente se pode ser nulo e, se puder, qual o fallback. Isso previne a classe mais comum de bugs em producao antes de eles serem escritos.

3. **Raciocinio manual/IA depois do codigo (Step 11-OWASP):** Ferramentas automatizadas nao respondem perguntas como "este endpoint verifica se o usuario logado e o dono do recurso?" ou "este reset de senha e de uso unico?". O Step 11-OWASP inspeciona o codigo implementado com as 10 categorias OWASP, exigindo evidencias arquivo:linha para cada verificacao.

**Relatorios gerados:** `docs/security/SECURITY_AUDIT_REPORT.md`, `docs/security/NULL_SAFETY_REPORT.md`, `docs/security/OWASP_HARDENING_REPORT.md`.

**Tarefas:** `docs/planning/TASKS.md` §4 (SEC-001, SEC-002, SEC-003, SEC-004).

**Exemplo real — Execucao completa no projeto SGI (Junho 2026):** As 3 skills foram executadas contra o repositorio LLC. Step 11-Security: Semgrep 340 regras em 147 arquivos → 0 findings; SCA N/A (sem dependencias); Gitleaks nao disponivel → verificacao manual limpa. Gate: APROVADO. Step 12-Null-Safety: 0 PRPs encontrados (fase de especificacao) → validacao do template `PRP_TEMPLATE.md` demonstrou boas praticas (`?` para opcionais, fallbacks documentados). Gate: APROVADO. Step 11-OWASP: auditoria manual dos 9 scripts `.py` (~85 KB) → A02 0 secrets, A03 28 `subprocess.run()` seguros, A08 `yaml.safe_load()`, A09 logs limpos, A10 0 network. Gate: APROVADO. Pipeline liberado para implementacao dos PRPs.

---

## Ferramentas e Integrações

### Quais ferramentas são necessárias para utilizar o workflow LLC?

**Stack mínimo (obrigatório):**

| Ferramenta | Para que | Instalação |
|-----------|----------|------------|
| **Git** | Versionamento de todos os artefatos e código | `git --version` (pré-instalado na maioria dos sistemas) |
| **Python 3.10+** | Scripts ACE (sessões, impacto, code-health) | `python --version` |
| **Docling** | Conversão de PDF/DOCX/HTML para Markdown (Step 0.1) | `pip install docling` |
| **Um cliente de IA terminal** | Execução das skills LLC | Claude Code, opencode, Codex CLI, Cursor CLI — qualquer um |

**Stack recomendado (opcional):**

| Ferramenta | Para que | Quando usar |
|-----------|----------|-------------|
| **PyYAML** | `impact-analyzer.py` e scripts ACE | Já incluso na instalação do Docling |
| **jq** | Validação de `index.json` no pre-commit hook | `choco install jq` / `brew install jq` |
| **pre-commit** | Framework de hooks git (validação ACE automatizada) | `pip install pre-commit && pre-commit install` |
| **Excalidraw MCP** | Wireframes lo-fi no subfluxo de prototipagem (F3) | https://github.com/excalidraw/excalidraw-mcp |
| **Pencil MCP** | Protótipos hi-fi no subfluxo de prototipagem (F4) | https://docs.pencil.dev |
| **Pandoc** | Fallback de conversão se Docling indisponível | `choco install pandoc` / `brew install pandoc` |
| **MSW** | Mock Service Worker para camada de dados mockados (Step 8) | `npm install msw --save-dev` |

### Quais ferramentas complementam o workflow LLC?

Além do stack base, ferramentas externas podem potencializar o pipeline LLC atacando pontos específicos de fricção. Nenhuma é obrigatória — o LLC funciona sem elas — mas cada uma resolve um gargalo concreto do desenvolvimento com IA.

**Ferramentas complementares (todas opcionais):**

| Categoria | Ferramenta | O que resolve | Classificação |
|-----------|-----------|---------------|:---:|
| **Grafo de código** | Depwire, Graphify, Aider (tree-sitter) | Análise de dependências reais, assinaturas de funções (não alucinadas), impacto de mudanças — a IA para de "adivinhar" a estrutura do projeto | Opcional |
| **Git bisect** | `git-bisect.py` (script ACE nativo) | Automação de `git bisect run` — encontra o commit exato que introduziu uma regressão e reporta o diff | Opcional |
| **Mapa estrutural** | `code-map.py` (script ACE nativo) | Índice estrutural do codebase (árvore de arquivos, assinaturas, imports) para grounding do agente sem alucinações de API | Opcional |
| **Worktrees** | `--worktree` em `initialize_session.py` (nativo) | Isolamento de workspace por PRP/sessão via git worktree — branches paralelos sem poluir o workspace principal | Opcional |
| **Compressão de contexto** | Caveman, Headroom | Economia de 60-95% de tokens; reduz o problema de "lost in the middle" mantendo mais contexto útil na janela do LLM | Opcional |
| **Memória semântica** | agentmemory, MemPalace | Busca semântica entre sessões — complementa o ACE com recuperação por similaridade em vez de busca exata | Opcional |
| **Grill Me** | Skill LLC nativo (Steps 0.5-3) | Protocolo de perguntas obrigatórias antes de gerar artefatos — expõe lacunas e suposições não validadas | ✅ **Obrigatório** (núcleo LLC) |
| **TDD + AGENTS.md** | Protocolo LLC nativo | Zonas de autonomia, RED/GREEN/REFACTOR, handoff — força verificação antes de prosseguir | ✅ **Obrigatório** (núcleo LLC) |
| **ACE + context_seed** | Scripts `.ace/` | Continuidade entre sessões (~300 tokens), append-only delta, memória persistente de aprendizado | ✅ **Obrigatório** (núcleo LLC) |

> **Nota:** As ferramentas obrigatórias já fazem parte do LLC. As opcionais são recomendações para equipes que querem ir além na mitigação do "problema dos 70%" e na eficiência de tokens. O LLC é agnóstico a ferramentas externas — qualquer alternativa equivalente serve.

### Quais LLMs funcionam com workflows agenticos?

Qualquer LLM que suporte **tool calling** (invocação de ferramentas de terminal, leitura/escrita de arquivos) e tenha capacidade de **thinking/reasoning** para os Steps 0-10:

| LLM | Recomendação | Observações |
|-----|-------------|-------------|
| **Claude (3.5 Sonnet, 3.5 Haiku, Opus)** | ⭐⭐⭐⭐⭐ Ideal | Thinking mode nativo, excelente em análise de documentos longos, consistente em geração de specs |
| **GPT-4o, GPT-4.1** | ⭐⭐⭐⭐ Muito bom | Reasoning mode (o1/o3) cobre Steps 0-10; tool calling robusto |
| **Gemini 2.5 Pro** | ⭐⭐⭐⭐ Muito bom | Janela de contexto de 1M tokens — vantagem para ingestion de documentos extensos |
| **Qwen (2.5, 3)** | ⭐⭐⭐ Bom | Open-source, performance competitiva em code generation |
| **DeepSeek (V3, R1)** | ⭐⭐⭐ Bom | Reasoning mode (R1) para Steps 0-10; custo-benefício excelente |
| **Mistral Large** | ⭐⭐⭐ Bom | Sólido em francês e inglês; tool calling funcional |

**Regra prática:** Para Steps 0-10 (especificação e planejamento), use uma LLM com **thinking/reasoning mode**. Para Step 11 (execução), o modo regular é suficiente. O LLC é tool-agnostic — qualquer combinação de LLM + cliente de IA terminal funciona, desde que suporte leitura/escrita de arquivos e execução de comandos.

**Custo estimado por projeto completo (pipeline LLC):**

| Porte do projeto | Tokens estimados | Custo aproximado (Claude 3.5 Sonnet) |
|-----------------|-----------------|--------------------------------------|
| Pequeno (3-5 PRPs) | ~500K tokens | $1.50 - $3.00 |
| Médio (10-15 PRPs) | ~1.5M tokens | $4.50 - $9.00 |
| Grande (30+ PRPs) | ~4M tokens | $12.00 - $24.00 |

*Valores de junho/2026. O custo real depende do número de iterações Grill Me e re-execuções de skills após gates reprovados.*

### CodeAgent vs ToolCallingAgent: qual paradigma o LLC usa?

O LLC usa **ambos** os paradigmas, em fases diferentes. A escolha não está no cliente de IA — está no **design do skill**:

| Paradigma | Como funciona | Etapas por tarefa | Tokens |
|-----------|--------------|-------------------|--------|
| **ToolCallingAgent** | LLM gera JSON com tool + parâmetros. Uma tool por vez. Aguarda resultado antes da próxima | 12 etapas | ~29K tokens |
| **CodeAgent** | LLM gera + executa bloco Python. Encadeia múltiplas ações em um passo. Pode loop e condicional | 2 etapas | ~5.4K tokens |

**Uma skill bem escrita controla o paradigma — independente do cliente:**

- **Skill com pausas e gates** → a IA age uma ação por vez, aguardando validação → **ToolCallingAgent-like**
- **Skill com instruções encadeadas** → a IA executa múltiplas ações em sequência sem pausar → **CodeAgent-like**

O LLC aplica cada paradigma onde ele é mais adequado:

| Paradigma | Onde no LLC | Por que |
|-----------|------------|---------|
| **ToolCallingAgent-like** | Steps 0.5 a 10 (especificação e planejamento) | Um artefato por vez, human gate entre cada um. Grill Me força pausa para perguntas. `<gate_result>` força pausa para aprovação. Baixo risco — cada passo é pequeno e validado |
| **CodeAgent-like** | Step 11 (execução) + Subfluxo F5-F6 | Um PRP inteiro é implementado em um passo contínuo. O agente cria arquivos, escreve testes, corrige bugs, faz commit — tudo encadeado. Alto throughput — o PRP é auto-contido, dispensa consultas externas |
| **Híbrido** | Subfluxo F1-F4 (prototipagem) | F1-F3 (discovery, tokens, wireframes) são ToolCallingAgent-like com aprovação entre fases. F4 (hi-fi) tem CHECKPOINT VISUAL obrigatório. F5 (código) é CodeAgent-like |

A vantagem arquitetural: o paradigma não está preso ao cliente de IA. Um skill Markdown bem escrito produz o comportamento desejado em **qualquer agente que leia arquivos e execute comandos** — Claude Code (nativo ToolCallingAgent), opencode, Cursor, Codex CLI. O LLC não depende de um formato específico de function calling — depende de **instruções claras**.

### O que é o "scaffold" e como ele orienta a IA no LLC?

Scaffold é a estrutura inicial do projeto — o "esqueleto" que serve como base técnica sobre a qual o software será construído. Em vez de começar do zero, o projeto já nasce com convenções de pastas, padrões de código, ferramentas configuradas e exemplos funcionais que ensinam a IA **como** desenvolver naquele contexto específico.

No LLC, o scaffold opera em 3 camadas complementares:

| Camada | O que contém | Gerado por | Como orienta a IA |
|--------|-------------|-----------|-------------------|
| **Arquitetural** | Estrutura de pastas (monorepo), configuração de lint/type-check, dependências base | Step 8 (Setup) + `ARCHITECTURE.md` (Step 5) | A IA sabe exatamente onde cada arquivo vai. Não inventa estruturas — replica a existente |
| **Visual** | Design tokens (CSS/JSON), componentes base, padrões de interface | `DESIGN_SYSTEM.md` (Step 7) | A IA gera componentes que seguem o Design System. Não inventa cores, espaçamentos ou variantes |
| **Comportamental** | `CLAUDE.md` + `AGENTS.md` com regras de domínio, restrições, TDD | Step 10 | A IA sabe que deve escrever testes primeiro, filtrar por tenant ID, nunca usar `any` — as "regras da casa" estão documentadas |

**Por que funciona:** a IA aprende por exemplos. Um scaffold bem estruturado fornece modelos concretos para replicar — é mais eficaz que descrever regras abstratas em texto. Se a pasta `src/components/ui/` já tem um `Button.tsx` com variantes, estados e props TypeScript, a IA gera o `Input.tsx` seguindo o mesmo padrão — sem precisar ser instruída.

**No LLC, o scaffold é auto-gerado:** o pipeline produz a estrutura, as convenções e os exemplos como artefatos versionados. O desenvolvedor não precisa criar o scaffold manualmente — ele emerge dos Steps 5, 7, 8 e 10. Isso garante rastreabilidade total (PRP-003 → MOD-PLN-002 → PRD Técnico → Visão Estratégica) e permite que múltiplos agentes trabalhem em paralelo sem conflito de contexto.

### O pipeline LLC faz pentest automatizado?

Nao. O **Step 11-Security** executa auditoria estatica de seguranca (SCA + SAST + secret scanning) com `npm audit` (ou `pip-audit`), Semgrep e Gitleaks. Essas ferramentas rodam localmente, sao open-source e nao exigem infraestrutura externa.

Para pentest e DAST (analise dinamica de aplicacoes rodando), recomendamos integrar ferramentas complementares via CI/CD:

| Ferramenta | Tipo | GitHub |
|------------|------|--------|
| **OWASP ZAP** | DAST (dynamic scanning) | [github.com/zaproxy/zaproxy](https://github.com/zaproxy/zaproxy) |
| **Nuclei** | Vulnerability scanner | [github.com/projectdiscovery/nuclei](https://github.com/projectdiscovery/nuclei) |
| **SQLMap** | SQL injection testing | [github.com/sqlmapproject/sqlmap](https://github.com/sqlmapproject/sqlmap) |
| **Nikto** | Web server scanner | [github.com/sullo/nikto](https://github.com/sullo/nikto) |
| **Bandit** | Python SAST adicional | [github.com/PyCQA/bandit](https://github.com/PyCQA/bandit) |
| **Brakeman** | Rails SAST adicional | [github.com/presidentbeef/brakeman](https://github.com/presidentbeef/brakeman) |

Essas ferramentas podem ser adicionadas ao pipeline CI/CD definido no `docs/DEPLOYMENT.md` (gerado no Step 10). O LLC e tool-agnostic — qualquer ferramenta equivalente serve.

---

## Pipeline — Visão Geral

### Quantas etapas tem o LLC?

13 skills principais + 1 subfluxo. O pipeline vai da ingestão de conhecimento de negócio ao deploy:

| # | Etapa | Skill | Tecnologia / Ferramenta |
|---|-------|-------|-------------------------|
| 0 | Ingestão | — | PDF, DOCX, PPTX, HTML, TXT |
| 0-GF | Greenfield (alternativo) | `llc-step-0-greenfield` | LLM em modo brainstorming + thinking |
| 0.1 | Conversão | `llc-step-0-1` | **Docling** (Python 3.10+) / Pandoc |
| 0.5 | Visão + Módulos | `llc-step-0-5` | Grill Me, Templates Markdown |
| 1 | 7 Especificações | `llc-step-1` | Grill Me, **PRRS** (7 prismas de análise) |
| 2 | PRDs | `llc-step-2` | Grill Me, Templates institucionais |
| 3 | PRPs | `llc-step-3` | Grill Me, Contratos Gherkin |
| 4 | Planejamento | `llc-step-4` | **Mermaid** (grafo de dependências), YAML |
| 5 | Arquitetura | `llc-step-5` | **Mermaid** (C4), ADRs, Stack decisions |
| 6 | Tarefas | `llc-step-6` | **TASKS.md** com checkboxes |
| 7 | Design System | `llc-step-7` | Design tokens (CSS/JSON), Componentes |
| 8 | Setup + Mock | `llc-step-8` | **MSW** (Mock Service Worker), JSON |
| 9 | Testing Docs | `llc-step-9` | Jest, Vitest, Playwright, thresholds |
| 10 | Project Docs | `llc-step-10` | **CLAUDE.md**, **AGENTS.md**, README, DEPLOYMENT |
| 11 | Execução | Subfluxo F1-F6 | Excalidraw, Pencil, agentes paralelos |
| Transversal | ACE | `llc-ace-context` | **Python** (scripts), Markdown + XML, YAML |
| Transversal | Impacto | `llc-impact-analyzer` | **Python**, **PyYAML**, git diff |
| Transversal | Code Health | `llc-code-health` | **Python**, git log --numstat |

---

## E se eu não tenho documentação nenhuma?

Use o fluxo **greenfield** (`llc-step-0-greenfield`). A IA conduz uma entrevista estruturada em 4 dimensões (objetivo, atores, funcionalidades, restrições) e gera arquivos `.md` que simulam documentos reais em `ingestion/converted/`. Depois siga para o Step 0.5 normalmente.

---

## Por que converter documentos para Markdown (Step 0.1)?

| Formato | Tokens por informação útil | Ruído estrutural |
|---------|---------------------------|-----------------|
| Markdown | Baixo | Mínimo |
| JSON | Médio | Baixo-médio |
| XML | Alto | Alto |
| HTML | Muito alto | Muito alto |

Markdown é mais eficiente para tokenização LLM. A ferramenta **Docling** (IBM Research) converte PDF, DOCX, PPTX e HTML para Markdown preservando estrutura (headings, tabelas, listas).

---

## O que é Grill Me e quando usar?

É uma rodada obrigatória de perguntas que a IA faz ao usuário **ANTES** de gerar qualquer artefato nos Steps 0.5, 1, 2 e 3. A IA analisa os documentos de entrada, identifica ambiguidades, lacunas e contradições, e apresenta até 8 perguntas ordenadas por criticidade (🔴 bloqueante, 🟡 alta, 🟢 média). O usuário pode responder seletivamente ou dizer "prossiga com o que tem".

**Ative o modo thinking/extended reasoning da sua LLM para esta fase.**

### Por que o Grill Me para no Step 3?

Grill Me e um protocolo de **clarificacao de requisitos** — resolve ambiguidade sobre "o que construir". Ele para no Step 3 porque:

- **Steps 0.5-3** lidam com requisitos de negocio (escopo, atores, funcionalidades). So o usuario sabe as respostas.
- **Steps 4+** lidam com **decisoes tecnicas** derivadas dos requisitos ja validados. O AI deve decidir baseado nos RNFs e specs, nao perguntar.

Exemplo: "Qual stack usar?" (Step 5) — a resposta esta nos RNFs de performance, seguranca e escala definidos no Step 1. O AI analisa os RNFs e propoe; o humano valida no Gate 6. Perguntar ao usuario seria terceirizar uma decisao que os artefatos ja respondem.

---

## O que é PRRS (Prismatic Ranked Recursive Summarization)?

É o padrão arquitetural que o LLC usa para analisar a mesma fonte de dados sob **múltiplos ângulos simultâneos** (prismas) e depois convergir:

- Step 1: 7 specs = 7 prismas sobre `ingestion/converted/`
- Step 2: 2 PRDs = 2 prismas (executivo vs técnico) sobre os 7 specs
- Step 3: N PRPs = N prismas (unidades de implementação) sobre o PRD técnico
- Greenfield: 4 dimensões de entrevista sobre a ideia do sistema

---

## O que é ACE e por que preciso dele?

**Agentic Context Engineering** é o protocolo de continuidade entre sessões do LLC. Sem ele, cada sessão da IA começa do zero (amnésia do modelo).

- **Append-only:** arquivos de sessão nunca são reescritos — apenas deltas são appenados
- **`<context_seed>`:** ao final de cada sessão, a IA comprime o estado em 4 campos (~300 tokens)
- **Economia:** ~1.500 tokens/sessão vs ~22.000 do histórico completo
- **Tecnologia:** Python (scripts), Markdown + tags XML + YAML front matter

### Qual o schema exato do context_seed?

O `<context_seed>` e um bloco de texto com **4 campos obrigatorios**, separados por quebra de linha. Este e o schema formal — o contrato que todo cliente de IA deve implementar para ser compativel com o LLC:

```
state: [acoes concluidas, arquivos alterados, decisoes tomadas]
pending: [tarefas incompletas, proximos passos planejados]
blockers: [impedimentos ativos — tecnicos, dependencias, duvidas]
next_action: [proximo passo recomendado — especifico, acionavel]
```

**Regras de formato:**

| Regra | Detalhe |
|-------|---------|
| Nomes dos campos | Exatos: `state`, `pending`, `blockers`, `next_action` (case-sensitive, ingles) |
| Separador | `: ` (dois-pontos + espaco) apos cada nome de campo |
| Quebra de linha | `\n` entre campos |
| Encoding | UTF-8, sem marcadores Markdown ou XML no valor dos campos |
| Tamanho maximo | ~300 tokens (aproximadamente 1200 caracteres) |
| Campos vazios | Permitidos (ex: `blockers: nenhum` ou `blockers: `) |

**Exemplo real:**

```
state: Step 5 concluido. ARCHITECTURE.md gerado com stack NestJS + PostgreSQL. ADRs documentados para autenticacao JWT e multi-tenancy. Diagrama C4 nivel 2 criado.
pending: Aguardando aprovacao do Gate 6. Step 6 (Tarefas) e o proximo.
blockers: Duvida sobre qual ORM usar — Prisma vs TypeORM. Aguardando decisao do tech lead.
next_action: Executar llc-step-6.md apos Gate 6 aprovado. Se Prisma for escolhido, usar schema.prisma.
```

**Onde o schema esta documentado:** Alem desta secao, o schema completo esta no `AGENTS_TEMPLATE.md` §Handoff Protocol e nos scripts `initialize_session.py` / `finalize_session.py`.

---

## Como manter a consistência entre artefatos?

Use o **Impact Analyzer** (`llc-impact-analyzer`):

```bash
python .ace/scripts/impact-analyzer.py --files "docs/business/specs/perfis_permissoes.md" --json --skills
```

O script cruza `git diff` com o grafo de dependências (`.ace/dependency-graph.yaml`) e reporta:
- Quais artefatos downstream são impactados
- Em qual ordem revisá-los
- Quais skills re-executar

Integrado ao pre-commit hook como verificação informativa.

---

## Mermaid ou ASCII para diagramas?

**Mermaid.** ASCII é universal mas ruidoso e ineficiente para LLMs. Mermaid:
- Consome menos tokens
- É compreendido nativamente pelo tokenizador
- Pode ser gerado e atualizado pela própria IA
- Benchmarks mostram ganhos de performance em modelos open-source em problemas médios/difíceis

O LLC usa Mermaid em: fluxo do pipeline, grafo de dependências, diagramas C4, workflows BPMN.

---

## Como evitar degradação estrutural com múltiplos agentes?

Use o **Code Health** (`llc-code-health`):

```bash
python .ace/scripts/code-health.py --since "30 days ago" --strict
```

Monitora 4 métricas:

| Métrica | Threshold | Severidade |
|---------|-----------|------------|
| % Moved Code | < 10% | 🔴 Crítico |
| Copy/Paste vs Moved | copy > moved | 🟡 Alto |
| % Legacy Touch | < 20% | 🟡 Alto |

Se alertas dispararem, agende uma onda de refatoração cross-PRP.

---

## CLAUDE.md ou AGENTS.md? Qual usar?

| Arquivo | O que contém | Para quem |
|---------|-------------|-----------|
| `CLAUDE.md` | Stack, domínio, DB, arquitetura, restrições LLC | Claude Code (exclusivo) |
| `AGENTS.md` | Zonas, TDD, handoff, Grill Me, protocolo epistêmico | Cursor, Codex, Copilot CLI, opencode |

**Se sua ferramenta não suporta `CLAUDE.md`:** consolide tudo no `AGENTS.md`. O `<!-- @include AGENTS.md -->` no CLAUDE.md garante que ferramentas que suportam ambos não dupliquem regras.

Ambos são gerados automaticamente pelo Step 10 a partir dos templates em `docs/templates/`.

---

## Como funciona o TDD no LLC?

1. 🔴 **RED:** Escreva o teste primeiro. Rode — deve falhar.
2. 🟢 **GREEN:** Implemente o código mínimo para passar.
3. 🔵 **REFACTOR:** Melhore o código mantendo testes verdes.

Regras:
- Testes co-localizados com código (`.spec.ts` ao lado de `.ts`)
- Factories em `test-helpers/factories/` — nunca valores hardcoded
- Cobertura: ≥ 80% unitários, ≥ 70% integração
- O `code-health.py` monitora se agentes estão seguindo TDD ou apenas adicionando código sem teste

---

## Como configurar as skills para meu cliente de IA?

| Cliente | Diretório | Comando |
|---------|-----------|---------|
| Claude Code | `.claude/skills/` | `cp docs/skills/llc-*.md .claude/skills/` |
| opencode | `.opencode/skills/<name>/SKILL.md` | Script bash no guia |
| Codex | `.codex/skills/` | `cp docs/skills/llc-*.md .codex/skills/` |
| Cursor | `.cursor/skills/` | `cp docs/skills/llc-*.md .cursor/skills/` |
| Outros | `.skills/` | `cp docs/skills/llc-*.md .skills/` |

Alternativa: invoque pelo caminho direto — `Execute a skill docs/skills/llc-step-0-5.md`

---

## O que cada script Python faz?

| Script | Quando roda | Função |
|--------|------------|--------|
| `initialize_session.py` | Início de toda sessão | Cria arquivo de sessão, carrega `context_seed` |
| `finalize_session.py` | Fim de toda sessão | Gera `context_seed`, promove learning points, atualiza TASKS.md |
| `promote-learning-points.py` | Automático no finalize | Promove aprendizados para `memory/` |
| `validate-tags.py` | Pre-commit hook | Valida tags XML, schema do context_seed, index.json |
| `impact-analyzer.py` | Antes de refatorações | Propaga impacto via grafo de dependências |
| `code-health.py` | A cada onda / checkpoint QA | Monitora Moved Code, Copy/Paste, Legacy Touch |
| `pre-commit.sh` | Git pre-commit | Orquestra validação ACE + impacto |

---

## Por que YAML no grafo de dependências em vez de um banco de dados?

- Legível por humano e máquina
- Versionável (git diff mostra exatamente o que mudou)
- Sem dependências externas
- ~600 tokens para carregar
- Gerado e mantido pelo próprio pipeline (Step 4)

---

## Posso usar o LLC sem Claude Code?

Sim. O LLC é **tool-agnostic**. Cada skill é um arquivo Markdown que qualquer cliente de IA terminal pode ler e executar. As ferramentas específicas (Claude Code, opencode, Cursor) são recomendações, não requisitos.

---

## O que acontece se um gate humano for reprovado?

O fluxo retorna ao passo anterior para correção. A IA registra o motivo no ACE via `<gate_result decision="rejected">` e `<blocker>`. Após a correção, o gate é reavaliado. Nenhum passo avança sem aprovação explícita.

---

## Qual a diferença entre dependency-graph.yaml e dependency-graph.mmd?

| Arquivo | Função | Quem lê | Mantido por |
|---------|--------|---------|-------------|
| `dependency-graph.yaml` | Estrutura real — usada pelo `impact-analyzer.py` | Scripts Python | **Fonte da verdade** — mantido manualmente como artefato da metodologia |
| `dependency-graph.mmd` | Visualizacao topologica em Mermaid — entendimento visual | Humanos e LLMs | **Derivado do .yaml** — gerado a partir do YAML, nao mantido independentemente |

> **Regra:** O `.yaml` e a fonte da verdade. O `.mmd` deve ser regenerado a partir do `.yaml`
> sempre que o grafo de dependencias for atualizado. Nao edite o `.mmd` manualmente —
> edite o `.yaml` e atualize o `.mmd` como derivado. Isso evita dessincronizacao.

---

## Próximos passos após o pipeline?

1. MVP mockado rodando → validar com stakeholders
2. CHECKPOINT MVP aprovado → implementar integrações reais
3. Integrações funcionando → implantar em staging
4. Testes de aceite passando → implantar em produção
5. Monitorar code-health e iterar

---

## 📖 Manual do Usuario

### O que e o manual do usuario no LLC?

E a documentacao voltada para o **usuario final** da aplicacao, gerada automaticamente pelo pipeline LLC. Diferente do README e DEPLOYMENT (que sao para desenvolvedores), o manual do usuario ensina como **usar** o sistema: como navegar, como cadastrar, como gerar relatorios, etc.

O manual e composto por:
- **Esqueleto** (`docs/user-guide/USER_GUIDE.md`): gerado pela skill `llc-user-guide` (Step 10.5), contem indice de paginas, guia por perfil e convencoes.
- **Paginas de conteudo** (`docs/user-guide/[modulo]/*.md`): geradas pelos PRPs durante a execucao (Step 11). Cada PRP declara quais paginas de manual produz na secao `user_docs`.

### Por que o manual do usuario e importante no desenvolvimento agentico?

Agentes de IA produzem codigo, mas o usuario final precisa entender como usar o sistema. O manual do usuario fecha o ciclo: a mesma IA que implementa a feature tambem documenta como usa-la. Isso garante que a documentacao esteja sempre sincronizada com o codigo — se o codigo muda, reexecutar o PRP atualiza o manual.

### O manual foi gerado sem screenshots. Como adicionar as telas reais?

O LLC gera o manual com screenshots se o Playwright estiver instalado no ambiente. Caso contrario, usa diagramas Mermaid como fallback. Para adicionar screenshots reais:

1. Instale o Playwright: `npm install -D @playwright/test && npx playwright install`
2. Execute o servidor de desenvolvimento da aplicacao
3. Navegue ate `docs/user-guide/[modulo]/img/`
4. Substitua os diagramas por screenshots reais ou execute o script de captura do PRP novamente

### Posso usar Puppeteer ou Selenium em vez de Playwright?

Sim. O script de screenshot do LLC detecta automaticamente `playwright`, `puppeteer` ou `selenium-webdriver` no `package.json`. Qualquer um dos tres funciona. Instale o de sua preferencia e re-execute o PRP.

### Como manter o manual atualizado apos mudancas?

A cada PRP executado, as paginas de manual declaradas em `user_docs` sao regeneradas. Se uma feature existente mudou (ex: campo novo no formulario), re-execute o PRP correspondente. O analisador de impacto (`llc-impact-analyzer`) reporta quais paginas de manual sao afetadas por cada alteracao de codigo.

### Preciso de um site separado para o manual?

Nao. Os arquivos Markdown em `docs/user-guide/` sao renderizados nativamente no GitHub, GitLab e qualquer previewer de Markdown. Se desejar um site com busca e tema, ferramentas como MkDocs ou VitePress podem converter os `.md` em site estatico com comando unico (`mkdocs build`), sem alterar o conteudo.

---

## 📖 Compressao de Tokens

### O LLC usa alguma estrategia de compressao de tokens?

Sim, em **5 camadas** complementares. O objetivo e maximizar a quantidade de informacao util que cabe na janela de contexto da LLM, mantendo a IA sempre na zona de qualidade de pico (0-30% de preenchimento):

| Camada | Mecanismo | Reducao |
|--------|-----------|:------:|
| **1. ACE `<context_seed>`** | Comprime o estado da sessao em 4 campos (~300 tokens) em vez de recarregar o historico completo (~22.000 tokens) | **93%** |
| **2. PRPs auto-contidos** | Cada agente de implementacao recebe apenas o PRP (~50-80 linhas), nao o projeto inteiro (~25+ artefatos, ~5000+ linhas) | **95%+** |
| **3. Indice comprimido no AGENTS.md** | Formato `|`-delimitado: 16 artefatos em ~400 tokens com keywords para roteamento. O agente decide quais arquivos carregar sob demanda (lazy loading) | **23% vs tabela tradicional** |
| **4. Analisador de impacto** | `impact-analyzer.py` diz exatamente quais artefatos ler antes de cada alteracao — elimina leitura desnecessaria | **Sob demanda** |
| **5. Markdown via Docling** | PDF/DOCX/HTML convertidos para Markdown puro (Step 0.1) — reduz ruido estrutural de tags pesadas (XML, HTML) | **60-80% vs formatos binarios** |

**Principio de design:** descricoes sao para roteamento, nao para leitura integral. O agente usa o indice comprimido para decidir quais arquivos carregar — e so os carrega quando a tarefa realmente exige.

### O LLC e compativel com prompt caching?

Sim. O design do LLC maximiza **cache hits** por construcao, mesmo sem ter sido projetado explicitamente para isso:

| Camada de cache | Mecanismo LLC | Efeito |
|----------------|---------------|--------|
| **1. Prefixo estatico** | `<!-- @include AGENTS.md -->` carrega regras, zonas, TDD e protocolo no topo de toda sessao. Skills LLC tem estrutura fixa (YAML → prereqs → prompt → regras). O prefixo e identico entre sessoes | Cache hit garantido no prefixo |
| **2. Isolamento dinamico** | Conteudo dinamico (mensagens do usuario, saidas de ferramentas, logs de erro) e appenado ao final. O agente recebe apenas o PRP atual, nao o historico completo | Cache nao e invalidado entre tarefas |
| **3. Sessoes curtas** | PRPs de 2-8 dias garantem sessoes atomicas. ACE `<context_seed>` (~300 tokens) substitui recarregar historico (~22K tokens) | Cache fresco a cada sessao |
| **4. Ordem consistente** | Document Hierarchy fixa no AGENTS.md, indice comprimido em formato estavel, estrutura de skills imutavel entre execucoes | Zero cache miss por reordenacao |
| **5. Lazy loading** | Indice comprimido + analisador de impacto — o agente so carrega arquivos sob demanda, mantendo o prompt enxuto | Menos tokens = menos cache pressure |

**Regra pratica:** mantenha conteudo estatico (AGENTS.md, schemas de ferramentas, regras do projeto) no topo de cada prompt. Appenda conteudo dinamico (mensagens, saidas de ferramentas, erros) ao final. Isso maximiza prefix cache hits.

---

## 🔀 Git Worktree

### O que e Git Worktree e como o LLC o utiliza?

Git Worktree permite criar **multiplos diretorios de trabalho** vinculados a branches diferentes, todos compartilhando o mesmo repositorio `.git/`. Em vez de fazer `git checkout` e sobrescrever arquivos no mesmo diretorio, cada branch tem seu proprio diretorio fisico.

```
/projeto/              ← branch: main       (worktree principal)
/projeto-prp-001/      ← branch: prp-001/wave-1
/projeto-prp-002/      ← branch: prp-002/wave-1
```

**Como o LLC utiliza:**

| Momento | Comportamento |
|---------|--------------|
| **Step 11 (Execucao)** | `initialize_session.py` cria worktree automaticamente quando `--prp` e informado ou `step >= 11` |
| **PRPs em paralelo** | Cada PRP recebe seu proprio diretorio fisico — agentes nunca colidem em arquivos |
| **Merge/descarte** | `finalize_session.py`: gate `approved` → merge + remove worktree; gate `rejected` → descarta sem merge |
| **Branch naming** | `prp-{id}/wave-{n}` — consistente, previsivel, rastreavel |

**Vantagens para desenvolvimento agentico:**

| Vantagem | Como funciona |
|----------|---------------|
| **Paralelismo real** | 3 agentes implementam 3 PRPs simultaneamente, cada um em seu diretorio, sem clone do repositorio |
| **Build isolado** | `node_modules/`, `dist/`, `.env` independentes por worktree — versoes diferentes de dependencias sem conflito |
| **Sem stash** | Nao precisa esconder mudancas nao commitadas para revisar outro branch — `cd` para outro diretorio |
| **Historico unificado** | `git log`, `git branch -a`, `git diff` entre branches funcionam de qualquer worktree |
| **Limpeza automatica** | Worktrees orfaos sao removidos pelo `cleanup_orphan_worktrees()` no inicio de cada sessao |

**Desativar isolamento:** use `--no-worktree` no `initialize_session.py`. Util para sessoes de especificacao (Steps 0-10) onde paralelismo nao e necessario.

---

## 🔧 Thin Harness

### O que e o Thin Harness do LLC?

O **Thin Harness** e a camada de orquestracao que conecta skills (Markdown), scripts ACE (Python) e o cliente de IA. E um CLI de ~500 linhas em Python que automatiza o ciclo de vida de cada step do pipeline.

**Comandos principais:**

```bash
llc run --step 5                     # Executa um step completo
llc pipeline --from 0                # Pipeline completo (para nos gates)
llc session start --step 5           # Inicia sessao manual
llc session end --approve            # Finaliza sessao manual
llc status                           # Progresso do pipeline
```

**Beneficios em relacao ao modo manual:**

| Dimensao | Sem harness | Com harness |
|----------|:-----------:|:-----------:|
| Acoes manuais por pipeline completo | ~88 | ~15 (so gates) |
| Risco de pular um step | Alto (manual) | Zero (orquestrado) |
| Risco de esquecer context_seed | Alto | Zero (automatico) |
| Consistencia entre sessoes | Manual (copiar/colar JSON) | Automatica |
| Curva de aprendizado | Precisa ler 3 docs | 1 comando |
| Worktree para PRPs paralelos | Precisa lembrar `--worktree` | Automatico (step >= 11) |
| Merge/descarte de worktrees | Manual | Automatico (por gate) |
| Learning points promovidos | Manual (script separado) | Automatico (finalize) |
| Onboarding de novo dev | ~30 min lendo guias | `llc pipeline --from 0` |

**O harness NAO substitui os scripts ACE** — ele os invoca via subprocess. Scripts ACE permanecem independentes e invocaveis manualmente.

**Por que "thin"?** O harness tem ~350 linhas por design. Ele NAO implementa tool-calling (cliente), NAO define regras de seguranca (AGENTS.md), NAO ensina o modelo (skills Markdown). Suas 5 responsabilidades sao estritas:

| # | Responsabilidade | Como |
|---|-----------------|------|
| 1 | Sessao ACE | init/finalize, context_seed, worktree |
| 2 | Carregamento de skill | Progressive disclosure — carrega o Document Index (~400 tokens), nao o AGENTS.md inteiro |
| 3 | Invocacao do agente | Deteccao de cliente CLI, timeout 10min, extracao automatica de context_seed |
| 4 | Validacao de gate | Checklist externo (`gates.json`), timeout 60s |
| 5 | Orquestracao do pipeline | Iteracao sobre steps, parada em gates |

**O que o harness NAO faz (e por que):**

| Responsabilidade | Quem faz | Por que |
|-----------------|----------|--------|
| Prompt caching | Cliente de IA | O cliente gerencia cache de prefixo nativamente |
| Sub-agentes paralelos | Git worktrees + cliente | Worktrees isolam; cliente lanca agentes |
| Ferramentas especificas | Scripts ACE | `impact-analyzer.py`, `code-health.py` sao fat code |
| Contexto de repositorio vivo | AGENTS.md + CLAUDE.md | Harness carrega so o indice comprimido |

---

## ⚡ Early Commitment + Deterministic Replay

### O LLC usa Early Commitment e Deterministic Replay?

Sim. A partir da versao 1.5.0, o Thin Harness inclui dois modulos que reduzem o custo de tarefas repetitivas em ate 99%:

**Early Commitment:** Antes de executar, o `llc_classify.py` classifica a tarefa em 4 tipos (crud_endpoint, ui_component, validation_rule, test_write). Isso colapsa o espaco de busca do agente e elimina caminhos de beco sem saida.

**Deterministic Replay:** Apos a primeira execucao aprovada por gate humano, o caminho de execucao (tool calls, codigo gerado, comandos) e gravado em `.ace/cache/{type}.json`. Tarefas futuras da mesma classificacao reproduzem o script deterministicamente, com custo de tokens proximo de zero.

| Metrica | Alvo |
|---------|:----:|
| Taxa de hit (tarefas com replay) | >60% |
| Taxa de sucesso (replays sem rollback) | >90% |
| Reducao de tokens por tarefa repetida | ~99% |
| Rollback em falha parcial | `git checkout` instantaneo |

**Ver metricas:** `python .ace/scripts/replay_stats.py`
