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

Cada nível preserva o contexto completo necessário para sua execução, eliminando a necessidade de consultar o PRD original durante a implementação. Isso garante rastreabilidade total (PRP-003 → MOD-PLN-002 → PRD Técnico → Visão Estratégica) e permite que múltiplos agentes trabalhem em paralelo sem conflito de contexto.

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
