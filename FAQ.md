# FAQ — Live and Let Code (LLC)

**Versão:** 1.2.0 — Junho 2026

---

## Conceitos Fundamentais

### O que é um workflow agentico de desenvolvimento?

É uma metodologia estruturada que utiliza agentes de IA especializados para colaborar ao longo do ciclo de vida do software — desde análise e requisitos até arquitetura, implementação e garantia de qualidade. Diferente do "vibe coding" (codificação informal por prompts), workflows agenticos definem papéis, artefatos, gates de qualidade e handoffs entre agentes. O LLC materializa isso em 13 skills, 11 human gates e um protocolo de continuidade de contexto (ACE).

### O que é "vibe coding" e por que preciso de um workflow estruturado?

Vibe coding é uma abordagem informal de codificação com IA onde os requisitos são ad hoc e o contexto se perde facilmente. Funciona para experimentos rápidos, mas gera dívida técnica, código inconsistente e falta de governança. Workflows estruturados como o LLC substituem isso por especificações formais geradas por Grill Me, agentes especializados por etapa, artefatos persistentes versionados em git e gates de qualidade com validação humana obrigatória.

### O que é "context rot" (degradação de contexto)?

É o fenômeno onde a qualidade da IA cai à medida que a janela de contexto se enche: 0-30% = qualidade de pico; 50%+ = começa a apressar e cortar cantos; 70%+ = alucinações e requisitos esquecidos. O LLC resolve isso com o protocolo **ACE** (`<context_seed>` de ~300 tokens em vez de histórico completo de ~22.000 tokens) e com **PRPs auto-contidos** — cada agente de implementação recebe apenas o PRP que precisa executar, não o projeto inteiro.

### O que é Spec-Driven Development (SDD)?

É a prática de front-loading especificações estruturadas e legíveis por máquina (visão estratégica, specs, PRDs, PRPs) para que agentes de IA possam contribuir de forma confiável à base de código. No LLC, os Steps 0-GF a 3 produzem especificações em cascata com rastreabilidade total — da visão estratégica ao PRP, cada artefato referencia sua origem. O Grill Me garante que lacunas sejam expostas antes da geração, não descobertas depois.

### O que é PRRS (Prismatic Ranked Recursive Summarization)?

É o padrão arquitetural onde uma mesma fonte de dados é analisada sob **múltiplos ângulos simultâneos** (prismas) e depois converge em camadas de granularidade crescente. No LLC: os 7 specs do Step 1 são 7 prismas sobre a documentação de ingestion; os 2 PRDs do Step 2 são 2 prismas sobre os specs (executivo vs técnico); os N PRPs do Step 3 são N prismas sobre o PRD técnico.

### O que é ACE (Agentic Context Engineering)?

É o protocolo de continuidade entre sessões do LLC. Combina Markdown (legibilidade humana), tags XML (parseabilidade por máquina) e YAML front matter (metadados). Cada sessão produz um arquivo append-only em `.ace/sessions/` que nunca é reescrito. Ao final, um `<context_seed>` de 4 campos comprime o estado da sessão em ~300 tokens. A sessão seguinte carrega apenas esse seed, não o histórico inteiro.

### O que são Human Gates?

São pontos de validação humana obrigatórios no pipeline LLC. Nenhum step avança sem aprovação explícita do usuário. O LLC tem 11 human gates + 1 checkpoint visual (subfluxo de prototipagem) + checkpoints de QA na execução. Um gate reprovado retorna o fluxo ao passo anterior com `<gate_result decision="rejected">` registrado no ACE.

### O que é Grill Me?

É o protocolo de questionamento obrigatório que a IA executa nos Steps 0.5, 1, 2 e 3 ANTES de gerar qualquer artefato. A IA analisa os documentos de entrada, identifica ambiguidades e apresenta até 8 perguntas ordenadas por criticidade (🔴 bloqueante, 🟡 alta, 🟢 média). O usuário responde seletivamente e a IA então gera os artefatos com base nas respostas. Elimina o principal ponto de falha do "vibe coding": suposições não validadas.

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

Não. Humanos definem direção, negociam escopo, supervisionam design e aprovam releases. Os agentes melhoram o retorno da atenção humana, não a substituem. O LLC formaliza isso com **human-in-the-loop** em todas as fases críticas: 11 human gates, 1 checkpoint visual e checkpoints de QA na execução. Nenhum step avança sem aprovação explícita.

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
| **4. Execução e Entrega** | 11 + Subfluxo | PRPs sem UI (agentes diretos), PRPs com UI (subfluxo F1-F6), code health, QA gates, deploy |

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

- **11 human gates:** um após cada step de geração (0.5 a 10). O humano revisa o artefato e decide: `approved`, `rejected` ou `conditional`
- **1 checkpoint visual:** no subfluxo de prototipagem (F4 → F5). O protótipo hi-fi não vira código sem aprovação visual explícita
- **Checkpoints de QA:** durante a execução (Step 11): score ≥ 7.0, cobertura ≥ thresholds, security audit aprovado

Cada decisão de gate é registrada no ACE via `<gate_result step="N" decision="approved|rejected|conditional" reviewer="...">`. Um gate reprovado retorna o fluxo ao passo anterior e registra `<blocker>`.

### Como garantir que o código gerado por IA seja de qualidade?

O LLC implementa 6 camadas de garantia de qualidade:

| Camada | Mecanismo LLC |
|--------|---------------|
| **1. Especificação antes do código** | Steps 0-GF a 3 geram specs, PRDs e PRPs detalhados com Grill Me — a IA não escreve uma linha de código antes que os requisitos estejam validados |
| **2. Agentes especializados por fase** | Cada etapa tem um agente com contexto restrito: o arquiteto não implementa, o dev não define requisitos |
| **3. Quality gates em cada transição** | 11 human gates + 1 checkpoint visual + QA gates — nenhum artefato avança sem validação |
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

### O que é "human-in-the-loop"?

É o princípio de que humanos permanecem no controle em todas as decisões críticas do ciclo de desenvolvimento. Agentes de IA executam dentro de guardrails definidos por humanos — nunca os substituem. No LLC:

| Onde o humano decide | Mecanismo |
|---------------------|-----------|
| **Definir objetivos** | O humano descreve o sistema (ingestion) ou responde à entrevista greenfield |
| **Negociar escopo** | Grill Me: a IA pergunta, o humano responde. Suposições não validadas são bloqueadas |
| **Supervisionar design** | CHECKPOINT VISUAL no subfluxo F4 → F5: protótipo não vira código sem aprovação |
| **Aprovar releases** | 11 human gates + QA checkpoints: cada artefato e cada onda passam por validação explícita |
| **Registrar decisões** | `<gate_result>` no ACE fecha o loop de accountability |

Agentes melhoram o retorno da atenção humana — não a substituem. Um engenheiro que antes passava 4h escrevendo specs agora passa 30 minutos revisando e aprovando specs geradas pela IA.

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

*Valores de junho/2026. O custo real depende do número de iterações Grill Me e re-execuções de skills após gates reprovados.* Isso garante rastreabilidade total (PRP-003 → MOD-PLN-002 → PRD Técnico → Visão Estratégica) e permite que múltiplos agentes trabalhem em paralelo sem conflito de contexto.

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

| Arquivo | Função | Quem lê |
|---------|--------|---------|
| `dependency-graph.yaml` | Estrutura real — usada pelo `impact-analyzer.py` | Scripts Python |
| `dependency-graph.mmd` | Intenção documentada — visualização topológica | Humanos e LLMs |

São complementares: YAML para máquina, Mermaid para entendimento visual.

---

## Próximos passos após o pipeline?

1. MVP mockado rodando → validar com stakeholders
2. CHECKPOINT MVP aprovado → implementar integrações reais
3. Integrações funcionando → implantar em staging
4. Testes de aceite passando → implantar em produção
5. Monitorar code-health e iterar
