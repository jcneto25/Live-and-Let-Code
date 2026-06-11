# Live and Let Code (LLC) — Pipeline Design Specification

**Versão:** 1.0.0  
**Data:** 04 de Junho de 2026  
**Status:** Design Aprovado  
**Projeto:** Live and Let Code (LLC) — Metodologia de Desenvolvimento Agentico Autônomo  
**Autor:** Equipe LLC  

---

## 1. Visão Geral

### 1.1 O que é LLC

Live and Let Code (LLC) é uma metodologia de desenvolvimento de software agentico que estrutura o ciclo completo de construção de sistemas — da ingestão de conhecimento de negócio ao deploy em produção — em etapas discretas, cada uma com entradas, saídas, templates e gates de validação humana bem definidos.

### 1.2 Princípios Fundamentais

1. **Documentação como código:** Todo artefato é um arquivo versionável (.md, .json, .yaml). Nada vive apenas em ferramentas externas.
2. **Humano no controle:** Nenhuma etapa avança sem validação humana explícita. A IA propõe, o humano dispõe.
3. **Tool-agnóstico:** A metodologia define o processo, não as ferramentas. Claude Code, opencode, Codex ou qualquer cliente de IA terminal pode executar os skills.
4. **Rastreabilidade total:** Cada artefato referencia sua origem. Da visão estratégica ao PRP, do PRP à tarefa, da tarefa ao commit.
5. **Paralelismo por design:** PRPs são contratos auto-contidos que permitem execução paralela em worktrees independentes.

### 1.3 Estrutura do Documento

Este documento especifica:
- A arquitetura de diretórios do LLC (§2)
- O pipeline completo com 11 etapas principais + 1 subfluxo (§3)
- O catálogo de skills (§4)
- O subfluxo de prototipagem agentica (§5)
- O sistema de gates humanos (§6)
- O inventário completo de templates (§7)
- O sistema ACE de contexto entre sessões (§8)
- O analisador de impacto e rastreabilidade (§9)

---

## 2. Arquitetura de Diretórios

### 2.1 Estrutura Completa

```
project-root/
├── CLAUDE.md                                   # [OUTPUT] Steering file — regras do projeto (Step 10)
├── AGENTS.md                                   # [OUTPUT] Steering file — protocolo do desenvolvedor (Step 10)
├── README.md                                   # Portal de entrada (Step 10)
│
├── docs/
│   ├── DEPLOYMENT.md                           # Estratégia de deploy (Step 10)
│   │
  │   ├── business/                               # Hub de negócio
  │   │   ├── ingestion/                          # [INPUT] Docs brutos do usuário
  │   │   │   └── converted/                      # [OUTPUT] Markdown convertido (Step 0.1)
  │   │   ├── specs/                              # [OUTPUT] 8 specs + visão + módulos
  │   │   └── Template_Especificacao_Modulo.md    # Template de módulo
│   │
│   ├── prd/                                    # PRDs (templates + gerados)
│   │   ├── template_prd_executivo_institucional.md
│   │   ├── template_prd_tecnico_institucional.md
│   │   ├── executive_PRD.md                    # [OUTPUT]
│   │   └── PRD_tecnico_institucional.md        # [OUTPUT]
│   │
│   ├── prps/                                   # PRPs (template + gerados)
│   │   ├── PRP_TEMPLATE.md
│   │   ├── PRP-001-[nome].md                   # [OUTPUT]
│   │   └── PRP-002-[nome].md                   # [OUTPUT]
│   │
│   ├── planning/                               # Planejamento (templates + gerados)
│   │   ├── PLAN_TEMPLATE.md
│   │   ├── TASKS_TEMPLATE.md
│   │   ├── EXECUTION_WAVES_TEMPLATE.md
│   │   ├── DEPENDENCY_MATRIX_TEMPLATE.md
│   │   ├── DEPENDENCY_MATRIX.md                # [OUTPUT]
│   │   ├── PLAN.md                             # [OUTPUT]
│   │   ├── EXECUTION_WAVES.md                  # [OUTPUT]
│   │   └── TASKS.md                            # [OUTPUT]
│   │
│   ├── architecture/                           # Arquitetura (template + gerado)
│   │   ├── ARCHITECTURE_TEMPLATE.md
│   │   └── ARCHITECTURE.md                     # [OUTPUT]
│   │
│   ├── design/                                 # Design System (master + gerado)
│   │   ├── Design_System_Master.md
│   │   └── DESIGN_SYSTEM.md                    # [OUTPUT]
│   │
│   ├── user-guide/                               # [NOVO] Manual do usuario (Step 10.5)
│   │   ├── USER_GUIDE.md                         # Esqueleto: indice, navegacao
│   │   ├── index.md                              # Pagina inicial
│   │   ├── visao-geral.md                        # Visao geral do sistema
│   │   ├── perfis/
│   │   │   └── index.md                          # Guia por perfil de usuario
│   │   ├── [modulo]/
│   │   │   ├── [pagina].md                       # Pagina de manual (PRP, Step 11)
│   │   │   └── img/
│   │   │       └── [screenshot].png              # Screenshot (opcional, Step 11)
│   │
│   ├── testing/                                # Testes (templates + gerados)
│   │   ├── TESTING_GUIDE_TEMPLATE.md
│   │   ├── COVERAGE_BASELINE_TEMPLATE.md
│   │   ├── COVERAGE_PROGRESS_TEMPLATE.md
│   │   ├── TESTING_GUIDE.md                    # [OUTPUT]
│   │   ├── COVERAGE_BASELINE.md                # [OUTPUT]
│   │   └── COVERAGE_PROGRESS.md                # [OUTPUT]
│   │
│   ├── specs/                                  # Template de especificação
│   │   └── SPEC_TEMPLATE.md
│   │
  │   ├── skills/                                 # Skills LLC (tool-agnostic)
  │   │   ├── llc-user-guide.md                    # [NOVO] Skill de manual do usuario
│   │   └── ...
  │   │
  │   ├── templates/                              # Templates de arquivos de steering
  │   │   ├── CLAUDE_TEMPLATE.md                  # Template para CLAUDE.md (projeto)
  │   │   └── AGENTS_TEMPLATE.md                  # Template para AGENTS.md (desenvolvedor)
  │   │
│   ├── superpowers/                             # Meta-documentação
│   │   └── specs/                               # Design specs
│   │
│   ├── template_visao_estrategica_e_negocio.md  # Template de visão (Step 0.5)
│   ├── guia_preenchimento_template_visao_estrategica_negocio.md
│   ├── Template_Glossario.md
│   ├── Template_Requisitos_Nao_Funcionais.md
│   ├── template_requisitos_funcionais.md
│   ├── template_business_rules.md
│   ├── Template_WORKFLOWS_E_BPMN.md
│   ├── Template_Perfis_Permissoes.md
│   └── Template_Catalogo_Integracoes.md
│
├── .ace/                                         # ACE — Histórico de sessões + Infra
│   ├── dependency-graph.yaml                     # Grafo de dependências (rastreabilidade)
│   ├── index.json                                # Índice de sessões
│   ├── sessions/                                 # Sessões append-only
│   │   └── YYYY-MM-DD-NNN.md
│   ├── memory/                                   # Conhecimento cross-sessão
│   │   ├── learning_points.md
│   │   └── architecture.md
│   ├── scripts/                                  # Scripts ACE
│   │   ├── initialize_session.py
│   │   ├── finalize_session.py
│   │   ├── promote-learning-points.py
│   │   ├── validate-tags.py
│   │   ├── impact-analyzer.py
│   │   └── pre-commit.sh
│   └── templates/
│       └── session.template.md
│
├── .pre-commit-config.yaml                       # Validação ACE + impacto no commit
│
├── mocks/                                       # Camada de dados mockados (Step 8)
│   ├── data/
│   │   ├── users.json
│   │   └── [entidade].json
│   ├── handlers/
│   │   ├── auth.ts
│   │   └── [modulo].ts
│   ├── browser.ts
│   ├── server.ts
│   └── README.md
│
├── src/                                         # Código fonte (Step 11 + subfluxo)
│   ├── app/
│   ├── components/
│   └── tokens/
```

### 2.2 Convenções de Nomenclatura

| Camada | Prefixo | Exemplo |
|--------|---------|---------|
| Metodologia LLC | `LLC_` | `docs/testing/LLC_TESTING_GUIDE.md` |
| Templates de usuário | `template_` ou `Template_` | `docs/template_visao_estrategica_e_negocio.md` |
| Artefatos gerados | nome descritivo | `docs/business/specs/glossario.md` |
| Módulos | `MOD-[SIGLA]-[NNN]_[nome]` | `MOD-PLN-001_planejamento_anual.md` |
| PRPs | `PRP-[NNN]-[nome]` | `PRP-001-cadastros_basicos.md` |
| Skills | `llc-step-[N]` ou `llc-subflow-[nome]` | `llc-step-0-5.md` |

---

## 3. Pipeline

### 3.1 Diagrama de Fluxo

```mermaid
graph TD
    START{Documentação prévia?}
    START -->|Sim| S0[Step 0: User loads raw docs]
    START -->|Não| GF[Step 0-Greenfield: Entrevista estruturada]
    GF --> S01
    S0 --> S01[Step 0.1: Docling → Markdown]
    S01 --> S05[Step 0.5: AI → Vision + Module Specs]
    S05 --> G1{👤 Gate 1}
    G1 -->|approved| S1[Step 1: AI → 7 Specs]
    S1 --> G2{👤 Gate 2}
    G2 -->|approved| S2[Step 2: AI → PRDs]
    S2 --> G3{👤 Gate 3}
    G3 -->|approved| S3[Step 3: AI → PRPs]
    S3 --> G4{👤 Gate 4}
    G4 -->|approved| S4[Step 4: AI → Planning]
    S4 --> G5{👤 Gate 5}
    G5 -->|approved| S5[Step 5: AI → Architecture]
    S5 --> G6{👤 Gate 6}
    G6 -->|approved| S6[Step 6: AI → Tasks]
    S6 --> G7{👤 Gate 7}
    G7 -->|approved| S7[Step 7: AI → Design System]
    S7 --> G8{👤 Gate 8}
    G8 -->|approved| S8[Step 8: AI → Setup + Mock Data]
    S8 --> G9{👤 Gate 9}
    G9 -->|approved| S9[Step 9: AI → Testing Docs]
    S9 --> G10{👤 Gate 10}
    G10 -->|approved| S10[Step 10: AI → Project Docs]
    S10 --> G11{👤 Gate 11}
    G11 -->|approved| S105[Step 10.5: User Guide Skeleton]
    S105 --> G115{👤 Gate 11.5}
    G115 -->|approved| S11[Step 11: LLC Execution]
    S11 --> BACK[PRPs sem UI → agente direto]
    S11 --> UI[PRPs com UI → Subfluxo F1-F6]
    UI --> F4[F4: Hi-Fi]
    F4 --> CV{🔴 CHECKPOINT VISUAL}
    CV -->|approved| F5[F5: Código]
    F5 --> F6[F6: Validação]
    BACK --> QA[Checkpoints QA]
    F6 --> QA
    QA --> DEPLOY[Deploy]
```

### 3.2 Tabela de Etapas

| # | Nome | Entrada | Saída | Template(s) | Gate |
|---|------|---------|-------|-------------|------|
| 0 | Ingestão | Documentos do usuário | `business/ingestion/` | — | — |
| 0-GF | Greenfield (alternativo) | Entrevista com usuário | `ingestion/converted/` (.md de entrevista) | — | — |
| 0.1 | Conversão | `ingestion/` | `ingestion/converted/` | — | — |
| 0.5 | Visão + Módulos | `ingestion/converted/` | Visão + MOD-*.md | `template_visao_estrategica_e_negocio.md`, `Template_Especificacao_Modulo.md`, guia de preenchimento | 👤 1 |
| 1 | 7 Especificações | Visão + Módulos | Glossário, RF, RNF, RN, BPMN, Perfis, Integrações | 7 templates em `docs/` | 👤 2 |
| 2 | PRDs | 7 specs + Visão | `executive_PRD.md`, `PRD_tecnico_institucional.md` | `template_prd_executivo_institucional.md`, `template_prd_tecnico_institucional.md` | 👤 3 |
| 3 | PRPs | PRDs + Specs + Módulos | `PRP-*.md` (N arquivos) | `PRP_TEMPLATE.md` | 👤 4 |
| 4 | Planejamento | PRPs | `DEPENDENCY_MATRIX.md`, `PLAN.md`, `EXECUTION_WAVES.md` | `DEPENDENCY_MATRIX_TEMPLATE.md`, `PLAN_TEMPLATE.md`, `EXECUTION_WAVES_TEMPLATE.md` | 👤 5 |
| 5 | Arquitetura | PRDs + RNF + Integrações + Planejamento | `ARCHITECTURE.md` | `ARCHITECTURE_TEMPLATE.md` | 👤 6 |
| 6 | Tarefas | PRPs + Arquitetura + Planejamento | `TASKS.md` | `TASKS_TEMPLATE.md` | 👤 7 |
| 7 | Design System | Arquitetura + Visão + Perfis | `DESIGN_SYSTEM.md` | `Design_System_Master.md` | 👤 8 |
| 8 | Setup + Mock | Arquitetura + Tarefas + Design System | `mocks/` + projeto inicializado | — | 👤 9 |
| 9 | Testing Docs | Arquitetura + PRPs + Tarefas | `TESTING_GUIDE.md`, `COVERAGE_BASELINE.md`, `COVERAGE_PROGRESS.md` | `TESTING_GUIDE_TEMPLATE.md`, `COVERAGE_BASELINE_TEMPLATE.md`, `COVERAGE_PROGRESS_TEMPLATE.md` | 👤 10 |
| 10 | Project Docs | Arquitetura + Planejamento + Design System + Testing | `README.md`, `DEPLOYMENT.md`, `CLAUDE.md`, `AGENTS.md` | `CLAUDE_TEMPLATE.md`, `AGENTS_TEMPLATE.md` | 👤 11 |
| 10.5 | User Guide | PRPs + Perfis + Workflows + Glossario | `USER_GUIDE.md`, `index.md`, `visao-geral.md`, `perfis/index.md` | `USER_GUIDE_TEMPLATE.md` | 👤 11.5 |
| 11 | Execucao | Todos os artefatos anteriores | Codigo fonte + paginas de manual (`docs/user-guide/[modulo]/*.md`) | — | Checkpoints QA |

---

## 4. Catálogo de Skills

### 4.1 Formato

Cada skill é um arquivo Markdown com YAML frontmatter, armazenado em `docs/skills/`. O formato é tool-agnostic: qualquer cliente de IA terminal pode ler e executar.

**Estrutura de um skill:**
```yaml
---
name: llc-step-N
description: Descrição curta
version: 1.0.0
tags: [categoria, llc-pipeline]
---
```

**Seções obrigatórias em cada skill:**
1. Metadados (YAML frontmatter)
2. Como usar (3 modos: referência, pipe, cópia)
3. Pré-requisitos (checklist com paths)
4. Prompt de execução (instruções para a IA)
5. Regras críticas (anti-alucinação, idempotência, consistência)
6. Saída esperada (o que apresentar ao parar)

### 4.2 Lista de Skills

| Skill | Passo | Descrição |
|-------|-------|-----------|
| `llc-step-0-greenfield` | 0-GF | Fluxo alternativo greenfield: entrevista estruturada para projetos sem documentação prévia |
| `llc-step-0-1` | 0.1 | Conversão de documentos raw para Markdown via Docling |
| `llc-step-0-5` | 0.5 | Gera Visão Estratégica + Especificação de Módulos a partir de documentos de ingestão |
| `llc-step-1` | 1 | Gera 7 documentos de especificação (Glossário, RF, RNF, RN, BPMN, Perfis, Integrações) |
| `llc-step-2` | 2 | Gera PRD Executivo e PRD Técnico Institucional |
| `llc-step-3` | 3 | Gera PRPs (Project Requirement Proposals) — contratos auto-contidos |
| `llc-step-4` | 4 | Gera Matriz de Dependências, Plano e Ondas de Execução |
| `llc-step-5` | 5 | Gera documento de Arquitetura (Stack, C4, ADRs, CI/CD) |
| `llc-step-6` | 6 | Gera TASKS.md com tarefas concretas, agentes e estimativas |
| `llc-step-7` | 7 | Gera Design System completo (tokens, componentes, padrões) |
| `llc-step-8` | 8 | Setup do projeto + Camada de dados mockados (JSON + MSW handlers) |
| `llc-step-9` | 9 | Gera documentação de testes (Guia, Baseline, Progresso) |
| `llc-step-10` | 10 | Gera README.md e DEPLOYMENT.md |
| `llc-user-guide` | 10.5 | Gera esqueleto do manual do usuario a partir dos PRPs, perfis e workflows |
| `llc-subflow-prototyping` | Subfluxo | Prototipagem agentica em 6 fases para PRPs com UI |
| `llc-ace-context` | Transversal | Protocolo ACE de contexto entre sessões — append-only, anti-amnésia |
| `llc-code-health` | 11 | Monitora saúde estrutural (Moved Code, Copy/Paste, Legacy Touch) |
| `llc-impact-analyzer` | Transversal | Analisa impacto de alterações via git diff + grafo de dependências |

---

## 5. Subfluxo de Prototipagem Agentica

### 5.1 Posição no Pipeline

O subfluxo de prototipagem é invocado **dentro do Step 11 (Execução)** para cada PRP ou módulo que envolva interfaces de usuário. PRPs sem UI (backend, infraestrutura) seguem implementação direta.

### 5.2 Fases

| Fase | Nome | Artefatos | Duração |
|------|------|-----------|---------|
| F1 | Discovery & Estratégia | `personas_[MOD-ID].md`, `journey_[MOD-ID].mmd` | 1-2 dias |
| F2 | Tokens Semânticos | `tokens.json`, `tokens.css`, config do stack, `accessibility_report_[MOD-ID].md` | 1 dia |
| F3 | Wireframes Lo-Fi | Wireframes (`.excalidraw` ou `.md`), `heuristic_eval_[MOD-ID].md` | 2-3 dias |
| F4 | Protótipo Hi-Fi | Protótipo visual (Pencil ou descritivo) | 3-5 dias |
| 🔴 | **CHECKPOINT VISUAL** | Aprovação humana obrigatória do protótipo hi-fi | — |
| F5 | Geração de Código | `src/components/ui/*.tsx`, `src/app/[modulo]/*.tsx`, stories | 2-4 dias |
| F6 | Validação & Iteração | `usability_report_[MOD-ID].md`, `a11y_report_[MOD-ID].json`, TASKS.md/PRPs atualizados | 2-3 dias |

### 5.3 Âncoras LLC

Cada fase do subfluxo é ancorada nos artefatos LLC já validados:

- **F1:** Deriva personas de `perfis_permissoes.md`, journeys de `workflows_bpmn.md`
- **F2:** Implementa tokens do `DESIGN_SYSTEM.md` — não os redefine
- **F3-F4:** Seguem estrutura de layout e padrões do Design System §3 e §5
- **F5:** Consome handlers de `mocks/` (Step 8), usa stack da `ARCHITECTURE.md` (Step 5)
- **F6:** Retroalimenta `TASKS.md` e PRPs com achados de validação

### 5.4 Tool-Agnosticismo

MCP servers (Excalidraw, Pencil) são recomendados mas não obrigatórios. Fallback: descrições em markdown com especificações visuais precisas.

---

## 6. Sistema de Gates Humanos

### 6.1 Gates por Etapa

| Gate | Após Step | O que é validado |
|------|-----------|-----------------|
| 👤 1 | 0.5 | Visão estratégica cobre o escopo? Módulos estão corretamente identificados? |
| 👤 2 | 1 | 7 specs estão completos? Glossário é consistente? Perfis e integrações batem com a visão? |
| 👤 3 | 2 | PRD executivo comunica valor? PRD técnico cobre todos os requisitos? |
| 👤 4 | 3 | PRPs têm granularidade correta? Dependências entre PRPs fazem sentido? |
| 👤 5 | 4 | Ondas estão bem agrupadas? Caminho crítico é realista? |
| 👤 6 | 5 | Stack é viável? ADRs são justificados? RNFs estão endereçados? |
| 👤 7 | 6 | Tarefas são acionáveis? Agentes estão corretamente atribuídos? |
| 👤 8 | 7 | Design System reflete a identidade do projeto? Todos os componentes têm estados definidos? |
| 👤 9 | 8 | Projeto roda? Dados mock são realistas? Handlers cobrem o núcleo? |
| 👤 10 | 9 | Estratégia de testes é adequada ao stack? Thresholds são realistas? |
| 👤 11 | 10 | README permite onboarding em ≤ 10 min? DEPLOYMENT cobre rollback e monitoramento? |
| 👤 11.5 | 10.5 | A estrutura cobre todos os modulos? Os perfis tem paginas relevantes? O indice e navegavel? A linguagem e adequada ao usuario final? |
| 🔴 | Subfluxo F4 | Protótipo hi-fi corresponde ao wireframe aprovado? Design System foi aplicado corretamente? |
| Checkpoints | 11 (Execução) | QA score ≥ 7.0? Cobertura ≥ thresholds? Security audit aprovado? |

### 6.2 Regras de Gate

- Um gate **reprovado** retorna o fluxo ao passo anterior para correção.
- Um gate **aprovado** permite o avanço. A aprovação é registrada no artefato (ex: `Status: Aprovado` no documento).
- Nenhum passo pode ser executado sem o gate do passo anterior ter sido aprovado.

---

## 7. Templates — Inventário Completo

### 7.1 Templates do Usuário (preenchidos manualmente ou via IA)

| # | Template | Local | Preenchido por | Destino do Preenchido |
|---|----------|-------|----------------|----------------------|
| 1 | Visão Estratégica e Negócio | `docs/template_visao_estrategica_e_negocio.md` | IA (Step 0.5) | `docs/business/specs/` |
| 2 | Glossário | `docs/Template_Glossario.md` | IA (Step 1) | `docs/business/specs/` |
| 3 | Requisitos Funcionais | `docs/template_requisitos_funcionais.md` | IA (Step 1) | `docs/business/specs/` |
| 4 | Requisitos Não Funcionais | `docs/Template_Requisitos_Nao_Funcionais.md` | IA (Step 1) | `docs/business/specs/` |
| 5 | Regras de Negócio | `docs/template_business_rules.md` | IA (Step 1) | `docs/business/specs/` |
| 6 | Workflows e BPMN | `docs/Template_WORKFLOWS_E_BPMN.md` | IA (Step 1) | `docs/business/specs/` |
| 7 | Perfis e Permissões | `docs/Template_Perfis_Permissoes.md` | IA (Step 1) | `docs/business/specs/` |
| 8 | Catálogo de Integrações | `docs/Template_Catalogo_Integracoes.md` | IA (Step 1) | `docs/business/specs/` |
| 9 | Especificação de Módulo | `docs/business/Template_Especificacao_Modulo.md` | IA (Step 0.5) | `docs/business/specs/` |

### 7.2 Templates LLC (preenchidos pela IA durante o pipeline)

| # | Template | Local | Preenchido por | Destino |
|---|----------|-------|----------------|---------|
| 10 | PRD Executivo | `docs/prd/template_prd_executivo_institucional.md` | IA (Step 2) | `docs/prd/executive_PRD.md` |
| 11 | PRD Técnico | `docs/prd/template_prd_tecnico_institucional.md` | IA (Step 2) | `docs/prd/PRD_tecnico_institucional.md` |
| 12 | PRP | `docs/prps/PRP_TEMPLATE.md` | IA (Step 3) | `docs/prps/PRP-*.md` |
| 13 | Dependency Matrix | `docs/planning/DEPENDENCY_MATRIX_TEMPLATE.md` | IA (Step 4) | `docs/planning/DEPENDENCY_MATRIX.md` |
| 14 | Plan | `docs/planning/PLAN_TEMPLATE.md` | IA (Step 4) | `docs/planning/PLAN.md` |
| 15 | Execution Waves | `docs/planning/EXECUTION_WAVES_TEMPLATE.md` | IA (Step 4) | `docs/planning/EXECUTION_WAVES.md` |
| 16 | Tasks | `docs/planning/TASKS_TEMPLATE.md` | IA (Step 6) | `docs/planning/TASKS.md` |
| 17 | Architecture | `docs/architecture/ARCHITECTURE_TEMPLATE.md` | IA (Step 5) | `docs/architecture/ARCHITECTURE.md` |
| 18 | Design System | `docs/design/Design_System_Master.md` | IA (Step 7) | `docs/design/DESIGN_SYSTEM.md` |
| 19 | Testing Guide | `docs/testing/TESTING_GUIDE_TEMPLATE.md` | IA (Step 9) | `docs/testing/TESTING_GUIDE.md` |
| 20 | Coverage Baseline | `docs/testing/COVERAGE_BASELINE_TEMPLATE.md` | IA (Step 9) | `docs/testing/COVERAGE_BASELINE.md` |
| 21 | Coverage Progress | `docs/testing/COVERAGE_PROGRESS_TEMPLATE.md` | IA (Step 9) | `docs/testing/COVERAGE_PROGRESS.md` |
| 22 | User Guide | `docs/USER_GUIDE_TEMPLATE.md` | IA (Step 10.5) | `docs/user-guide/USER_GUIDE.md` |

---

## 8. ACE — Agentic Context Engineering

### 8.1 O Problema

Agentes de IA operam em sessões isoladas. Sem um mecanismo de continuidade, cada sessão começa do zero — a "amnésia do modelo". Isso é especialmente crítico no pipeline LLC, onde cada etapa depende do contexto das anteriores.

### 8.2 A Solução

O ACE é um protocolo **append-only** de gestão de contexto entre sessões. Inspirado em atualizações delta incrementais, combina **Markdown** (legibilidade humana) + **tags XML** (parseabilidade por máquina) + **YAML front matter** (metadados estruturados).

### 8.3 Funcionamento

Cada sessão LLC produz um arquivo `.ace/sessions/YYYY-MM-DD-NNN.md` que é **nunca reescrito** — apenas deltas são appenados ao final. Ao iniciar uma nova sessão, o agente carrega o `<context_seed>` da sessão anterior (~300 tokens comprimidos) em vez do histórico completo (~22.000 tokens).

### 8.4 Taxonomia de Tags

| Tag | Propósito |
|-----|-----------|
| `<action_log>` | Container de ações — append-only |
| `<action type="...">` | Ação atômica: `git_commit`, `file_create`, `file_modify`, `file_delete`, `test_run`, `tool_call` |
| `<thinking ref="...">` | Chain-of-thought que levou a uma decisão |
| `<learning_point priority="...">` | Conhecimento consolidado (`high`/`medium`/`low`) |
| `<gate_result>` | Decisão humana nos gates LLC |
| `<blocker resolved="...">` | Impedimentos da sessão |
| `<context_seed>` | Estado comprimido para a próxima sessão (schema de 4 campos) |

### 8.5 Vantagens

| Vantagem | Impacto |
|----------|---------|
| **Economia de tokens** | ~1.500 tokens/sessão vs ~22.000 do histórico completo (93% de redução) |
| **Imutabilidade** | Histórico nunca corrompido — sessões são append-only |
| **Rastreabilidade** | Cada ação, decisão e aprendizado é registrado com timestamp e origem |
| **Integração com LLC** | `<gate_result>` fecha o loop de accountability da metodologia |
| **Promoção de conhecimento** | `<learning_point priority="high">` é automaticamente promovido para `memory/learning_points.md` |

---

## 9. Rastreabilidade e Análise de Impacto

### 9.1 O Problema

O pipeline LLC produz dezenas de artefatos interdependentes. Quando um artefato é alterado (ex: um perfil de acesso muda), é difícil saber quais documentos downstream precisam ser atualizados para manter a consistência.

### 9.2 A Solução

Um **grafo de dependências declarativo** (`.ace/dependency-graph.yaml`) mapeia cada artefato LLC: o que o originou (`depends_on`) e o que ele impacta quando alterado (`triggers_update`). Um script de análise cruza `git diff` com o grafo e propaga o impacto em cascata.

### 9.3 Funcionamento

```
git diff --name-only → cruza com dependency-graph.yaml → propaga triggers_update recursivamente → reporta ordem de revisão + skills sugeridos
```

Exemplo: alterar `perfis_permissoes.md` → o analisador reporta 6 artefatos em cascata e sugere re-executar `llc-step-2`, `llc-step-3`, `llc-step-5`, `llc-step-7`, `llc-step-10`.

### 9.4 Vantagens

| Vantagem | Impacto |
|----------|---------|
| **Consistência garantida** | Nenhum artefato fica desatualizado por esquecimento |
| **Ordem correta** | O report mostra a ordem exata de revisão (dependências antes de dependentes) |
| **Sugestão de skills** | O agente sabe exatamente quais skills re-executar |
| **Custo zero** | O grafo é gerido e mantido pelo próprio pipeline (Step 4) |
| **Pré-commit** | Integrado ao hook de git — análise de impacto a cada commit |

---

## 10. Saúde Estrutural do Código (Code Health)

### 10.1 O Problema

Agentes de IA independentes, operando em PRPs paralelos, tendem a maximizar produtividade de curto prazo: adicionar novas linhas é mais fácil que refatorar código existente. Isso gera degradação estrutural silenciosa:

- **Queda no Moved Code:** taxa de código reorganizado em módulos cai abaixo de 10%
- **Inversão Copy/Paste vs Moved:** duplicação de código supera reuso (violação do princípio DRY)
- **Abandono de código legacy:** menos de 20% das alterações tocam código com mais de 30 dias
- **Clone em vez de abstração:** agentes duplicam blocos lógicos em vez de criar módulos compartilhados

### 10.2 A Solução

O script `code-health.py` analisa o histórico do git e monitora 4 métricas estruturais:

| Métrica | Threshold de Alerta | Severidade |
|---------|---------------------|------------|
| % Moved Code | < 10% do total de alterações | 🔴 Crítico |
| Copy/Paste vs Moved | Cópias > Movimentações | 🟡 Alto |
| % Legacy Code Touch | < 20% dos commits tocam código > 30 dias | 🟡 Alto |
| Consistência estrutural | Todos os thresholds OK | ✅ Saudável |

### 10.3 Integração

- **Checkpoint QA (Step 11):** se métricas críticas estão violadas, o gate QA bloqueia o avanço
- **Pre-commit hook:** análise informativa a cada commit
- **Execução manual:** `python .ace/scripts/code-health.py --json`

### 10.4 Ações Corretivas

Quando um alerta é disparado, o pipeline recomenda:
1. Agendar onda de refatoração cross-PRP
2. Identificar blocos duplicados e consolidar em módulo compartilhado
3. Revisar PRPs recentes que priorizaram `file_create` sobre `file_modify`

---

## 11. Glossário LLC

| Termo | Definição |
|-------|-----------|
| **PRP** (Project Requirement Proposal) | Contrato auto-contido de implementação. Contém requisitos (Gherkin), API contracts, componentes, DB changes, testes e DoD. |
| **Skill** | Arquivo Markdown tool-agnostic com prompt de execução para uma etapa do pipeline. |
| **Gate** | Ponto de validação humana obrigatório. O pipeline não avança sem aprovação explícita. |
| **Subfluxo** | Processo interno a uma etapa do pipeline. No LLC, a prototipagem agentica é um subfluxo da Execução. |
| **Ingestion** | Pasta onde o usuário deposita documentos brutos de domínio para consumo pela IA. |
| **Mock Data Layer** | Camada de dados falsos realistas (JSON + MSW handlers) que simula o backend real durante o desenvolvimento do MVP. |
| **CHECKPOINT VISUAL** | Gate específico do subfluxo de prototipagem: o protótipo hi-fi não avança para código sem aprovação visual humana. |
| **Execution Wave** | Agrupamento de PRPs executados em paralelo dentro de um intervalo de tempo (1-2 semanas). |

---

## 12. Controle de Versão

| Versão | Data | Autor | Alterações |
|--------|------|-------|------------|
| 1.3.0 | 11/06/2026 | Equipe LLC | Adicionado Step 10.5 (User Guide) com skill `llc-user-guide`, gate 11.5, template USER_GUIDE_TEMPLATE.md e secao `user_docs` no PRP |
| 1.2.0 | 10/06/2026 | Equipe LLC | Adicionado Grill Me (Steps 0.5-3), fluxo greenfield, análise de saúde estrutural (Code Health §10) |
| 1.1.0 | 10/06/2026 | Equipe LLC | Adicionado Mermaid ao fluxo do pipeline (§3.1), seções ACE (§8) e Análise de Impacto (§9), removidos archive/ e superpowers/ |
| 1.0.0 | 04/06/2026 | Equipe LLC | Versão inicial do pipeline LLC |

**Revisor:** Jaime Correia
