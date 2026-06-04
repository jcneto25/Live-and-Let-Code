![Live and Let Code](LLC.png)

# Live and Let Code (LLC)

**Metodologia de Desenvolvimento Agentico Autônomo**

Live and Let Code (LLC) é uma metodologia open-source que estrutura o ciclo completo de construção de software — da ingestão de conhecimento de negócio ao deploy em produção — em etapas discretas, cada uma com entradas, saídas, templates e gates de validação humana bem definidos.

## Princípios

- **Documentação como código:** Todo artefato é um arquivo versionável. Nada vive apenas em ferramentas externas.
- **Humano no controle:** Nenhuma etapa avança sem validação humana explícita. A IA propõe, o humano dispõe.
- **Tool-agnóstico:** A metodologia define o processo, não as ferramentas. Qualquer cliente de IA terminal pode executar os skills.
- **Rastreabilidade total:** Da visão estratégica ao PRP, do PRP à tarefa, da tarefa ao commit.
- **Paralelismo por design:** PRPs são contratos auto-contidos que permitem execução paralela.

## Pipeline

```
Ingestion → Vision + Modules → 7 Specs → PRDs → PRPs → Planning → Architecture
→ Tasks → Design System → Setup + Mock → Testing Docs → Project Docs → Execution
```

**11 etapas principais + 1 subfluxo de prototipagem agentica, 11 human gates, 1 checkpoint visual.**

## Estrutura

```
docs/
├── business/       # Hub de negócio (ingestion + specs)
├── prd/            # Product Requirements (templates + gerados)
├── prps/           # Project Requirement Proposals
├── planning/       # Matriz, Plano, Ondas, Tarefas
├── architecture/   # Stack, C4, ADRs, CI/CD
├── design/         # Design System
├── testing/        # Guia, Baseline, Progresso
├── skills/         # Skills LLC tool-agnostic
└── specs/          # Template de especificação
```

## Skills

12 skills tool-agnostic em `docs/skills/`. Cada skill é um arquivo Markdown com YAML frontmatter — execute com qualquer cliente de IA terminal:

| Skill | Passo | Descrição |
|-------|-------|-----------|
| `llc-step-0-5` | 0.5 | Visão Estratégica + Módulos |
| `llc-step-1` | 1 | 7 Especificações |
| `llc-step-2` | 2 | PRDs (Executivo + Técnico) |
| `llc-step-3` | 3 | PRPs |
| `llc-step-4` | 4 | Planejamento (Matrix + Plan + Waves) |
| `llc-step-5` | 5 | Arquitetura |
| `llc-step-6` | 6 | Tarefas |
| `llc-step-7` | 7 | Design System |
| `llc-step-8` | 8 | Setup + Mock Data |
| `llc-step-9` | 9 | Documentação de Testes |
| `llc-step-10` | 10 | README + DEPLOYMENT |
| `llc-subflow-prototyping` | Subfluxo | Prototipagem Agentica (F1-F6) |

## Documentação

A especificação completa está em [`docs/superpowers/specs/2026-06-04-llc-pipeline-design.md`](docs/llc-pipeline-design.md).

## Licença

MIT
