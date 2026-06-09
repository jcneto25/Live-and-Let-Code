# Guia de Execução — Live and Let Code (LLC)

**Versão:** 1.0.0  
**Público:** Desenvolvedores, Product Owners, Tech Leads  
**Pré-requisito:** Leitura do [`llc-pipeline-design.md`](llc-pipeline-design.md) (visão geral da metodologia)

---

## Antes de Começar

### O que você precisa

- Um cliente de IA terminal (Claude Code, opencode, Codex, Cursor CLI, etc.)
- Git instalado e configurado
- Um projeto de software a ser desenvolvido
- Documentos de domínio do negócio (manuais, atas, regulamentos, transcrições, guias operacionais)

### Estrutura Inicial

Clone o repositório LLC ou copie a estrutura de diretórios para seu projeto:

```bash
git clone https://github.com/jcneto25/Live-and-Let-Code.git seu-projeto
cd seu-projeto
```

A estrutura `docs/` contém todos os templates e skills necessários.

### Configurando as Skills para seu Cliente de IA

Os skills LLC são arquivos Markdown com YAML frontmatter. Cada cliente de IA terminal tem seu próprio diretório de skills. Copie (ou crie symlinks) dos arquivos de `docs/skills/` para o diretório apropriado:

| Cliente de IA | Diretório de Skills | Comando para configurar |
|---------------|--------------------|-------------------------|
| **Claude Code** | `.claude/skills/` | `cp docs/skills/llc-*.md .claude/skills/` |
| **opencode** | `.opencode/skills/<name>/SKILL.md` | `mkdir -p .opencode/skills/llc-step-0-1 && cp docs/skills/llc-step-0-1.md .opencode/skills/llc-step-0-1/SKILL.md` (repetir para cada skill) |
| **Codex** | `.codex/skills/` | `cp docs/skills/llc-*.md .codex/skills/` |
| **Cursor** | `.cursor/skills/` | `cp docs/skills/llc-*.md .cursor/skills/` |
| **GitHub Copilot CLI** | `.github/copilot/skills/` | `cp docs/skills/llc-*.md .github/copilot/skills/` |
| **Outros** | `.skills/` (padrão) | `cp docs/skills/llc-*.md .skills/` |

**Alternativa — sem copiar:** A maioria dos clientes aceita o caminho direto. Exemplo:

```
Execute a skill docs/skills/llc-step-0-1.md
```

**Invocação por alias:** Se o cliente suportar aliases de skill (ex: `@llc-step-0-1`), o nome no YAML frontmatter é usado automaticamente.

**Script rápido para opencode (bash):**
```bash
for f in docs/skills/llc-*.md; do
  name=$(basename "$f" .md)
  mkdir -p ".opencode/skills/$name"
  cp "$f" ".opencode/skills/$name/SKILL.md"
done
```

---

### Modo de Operação da LLM

O pipeline LLC tem dois momentos distintos que se beneficiam de modos de operação diferentes:

| Etapas | Modo Recomendado | Motivo |
|--------|------------------|--------|
| **Passos 0 a 10** (especificação e planejamento) | **Thinking / Reasoning** | Documentos exigem análise profunda, raciocínio multi-step e consistência cruzada entre artefatos. O modo thinking reduz alucinações e produz especificações mais coerentes. |
| **Ajustes pós-validação** | **Thinking / Reasoning** | Correções em documentos após um gate reprovado exigem compreensão do contexto completo e impacto das mudanças em artefatos interdependentes. |
| **Passo 11 — Execução** (desenvolvimento e testes) | **Regular / Default** | Implementação de PRPs e tarefas se beneficia de respostas mais rápidas. O código gerado é validado por testes automatizados, reduzindo o risco de alucinações. |
| **Subfluxo F1-F4** (prototipagem) | **Thinking / Reasoning** | Fases de discovery, tokens, wireframes e hi-fi exigem julgamento de design e consistência com o Design System. |
| **Subfluxo F5-F6** (código e validação) | **Regular / Default** | Geração de componentes e execução de testes seguem especificações já aprovadas. |

**Na prática:** Ative o modo thinking/extended reasoning da sua LLM para os passos 0 a 10 e para qualquer ajuste solicitado após validação. Use o modo normal para execução de código e testes.

---

## Passo a Passo

### ⚠️ Atenção: Você tem documentação prévia?

**Se SIM** (já existem manuais, atas, regulamentos) → siga para o Passo 0.

**Se NÃO** (sistema novo, sem documentação) → execute o fluxo greenfield:

```
Execute a skill docs/skills/llc-step-0-greenfield.md
```

A IA conduzirá uma entrevista estruturada em 4 dimensões (15 perguntas no total) e gerará a base documental. Depois, prossiga normalmente para o Step 0.5.

---

### Passo 0: Carregue os Documentos de Domínio

**Você faz:** Coloque todos os documentos de negócio na pasta `docs/business/ingestion/`.

Formatos aceitos: `.pdf`, `.docx`, `.pptx`, `.html`, `.txt`, imagens com texto (PNG/JPG/TIFF).

Exemplos do que colocar:
- Transcrições de reuniões com stakeholders
- Manuais de processos organizacionais
- Regulamentos e legislação aplicável
- Atas de decisões arquiteturais
- Guias operacionais da unidade demandante

---

### Passo 0.1: Conversão para Markdown (Docling) 🆕

**Você faz:** Execute o skill de conversão:

```
Execute a skill docs/skills/llc-step-0-1.md
```

**A IA faz:**
- Detecta todos os formatos em `docs/business/ingestion/` (PDF, DOCX, PPTX, HTML)
- Converte cada arquivo para Markdown usando **Docling** (ou Pandoc como fallback)
- Deposita os arquivos `.md` convertidos em `docs/business/ingestion/converted/`
- Gera `_CONVERSION_REPORT.md` com estatísticas e status de cada arquivo

**Pré-requisito único:** Python 3.10+ + `pip install docling`

**Por que Markdown?** Menos tokens, menos ruído estrutural, melhor compreensão pela IA. PDFs e DOCsX têm tags pesadas que consomem tokens desnecessários.

---

### Passo 0.5: Visão Estratégica + Módulos

**Você faz:** Execute o skill no seu cliente de IA:

```
Execute a skill docs/skills/llc-step-0-5.md
```

**A IA faz:**
- Lê todos os arquivos em `docs/business/ingestion/converted/` (Markdown puro)
- Gera `docs/business/specs/visao_estrategica_e_negocio.md` (visão do sistema)
- Gera arquivos `MOD-[SIGLA]-[NNN]_[nome].md` (um por módulo identificado)

**Você valida:** 👤 Gate 1
- A visão cobre todo o escopo do negócio?
- Os módulos estão corretamente identificados e nomeados?
- Alguma seção ficou com `[NÃO IDENTIFICADO]`? Se sim, complemente.

**Só avance quando aprovar.**

---

### Passo 1: 7 Especificações

**Você faz:**

```
Execute a skill docs/skills/llc-step-1.md
```

**A IA faz:** Gera 7 documentos em `docs/business/specs/`:
1. `glossario.md`
2. `requisitos_funcionais.md`
3. `requisitos_nao_funcionais.md`
4. `regras_negocio.md`
5. `workflows_bpmn.md`
6. `perfis_permissoes.md`
7. `catalogo_integracoes.md`

**Você valida:** 👤 Gate 2
- Termos do glossário estão consistentes entre os documentos?
- Os perfis de acesso cobrem todos os atores?
- As integrações listadas batem com a realidade?

**Só avance quando aprovar.**

---

### Passo 2: PRDs (Executivo + Técnico)

**Você faz:**

```
Execute a skill docs/skills/llc-step-2.md
```

**A IA faz:** Gera em `docs/prd/`:
- `executive_PRD.md` — para stakeholders e gestores (linguagem institucional)
- `PRD_tecnico_institucional.md` — para a equipe de desenvolvimento (linguagem técnica)

**Você valida:** 👤 Gate 3
- O PRD executivo comunica o valor do sistema claramente?
- O PRD técnico cobre todos os requisitos dos specs?
- Ambos são consistentes entre si?

**Só avance quando aprovar.**

---

### Passo 3: PRPs (Project Requirement Proposals)

**Você faz:**

```
Execute a skill docs/skills/llc-step-3.md
```

**A IA faz:** Gera arquivos `PRP-001-[nome].md`, `PRP-002-[nome].md`, etc. em `docs/prps/`. Cada PRP é um contrato auto-contido de implementação.

**Você valida:** 👤 Gate 4
- A granularidade dos PRPs está adequada (2-8 dias cada)?
- As dependências entre PRPs fazem sentido?
- Nenhum requisito do PRD ficou sem PRP?

**Só avance quando aprovar.**

---

### Passo 4: Planejamento (Matriz + Plano + Ondas)

**Você faz:**

```
Execute a skill docs/skills/llc-step-4.md
```

**A IA faz:** Gera em `docs/planning/`:
- `DEPENDENCY_MATRIX.md` — grafo de dependências e caminho crítico
- `PLAN.md` — roadmap, milestones, DoD
- `EXECUTION_WAVES.md` — ondas de execução com PRPs agrupados

**Você valida:** 👤 Gate 5
- As ondas estão bem agrupadas?
- O caminho crítico é realista?
- O tempo total estimado faz sentido?

**Só avance quando aprovar.**

---

### Passo 5: Arquitetura

**Você faz:**

```
Execute a skill docs/skills/llc-step-5.md
```

**A IA faz:** Gera `docs/architecture/ARCHITECTURE.md` com:
- Stack tecnológico (frontend, backend, banco, infra)
- Diagramas C4 (contexto, containers, componentes)
- ADRs (decisões arquiteturais justificadas)
- Estratégia de segurança e CI/CD

**Você valida:** 👤 Gate 6
- O stack é viável no seu ambiente?
- As decisões arquiteturais são justificadas?
- Os RNFs de performance e segurança estão endereçados?

**Só avance quando aprovar.**

---

### Passo 6: Tarefas

**Você faz:**

```
Execute a skill docs/skills/llc-step-6.md
```

**A IA faz:** Gera `docs/planning/TASKS.md` com:
- Tarefas concretas por PRP (scaffolding, backend, frontend, testes)
- Agentes atribuídos (dev_agent, qa_agent, security_agent)
- Paralelização explícita (✅ paralelo, ⚠️ após setup, ❌ sequencial)
- Estimativas em horas/dias

**Você valida:** 👤 Gate 7
- Todas as tarefas são acionáveis e sem ambiguidade?
- Os agentes estão corretamente atribuídos?
- As estimativas são realistas?

**Só avance quando aprovar.**

---

### Passo 7: Design System

**Você faz:**

```
Execute a skill docs/skills/llc-step-7.md
```

**A IA faz:** Gera `docs/design/DESIGN_SYSTEM.md` preenchendo o template `Design_System_Master.md` com:
- Design tokens (cores, tipografia, espaçamento, dark mode)
- Biblioteca de componentes (variantes, estados, props)
- Padrões de interface (tabelas, formulários, navegação, dashboards)
- Micro-interações e matriz de estados

**Você valida:** 👤 Gate 8
- A paleta de cores reflete a identidade do projeto?
- Todos os componentes têm estados definidos (loading, empty, error)?
- O Design System cobre os fluxos do sistema?

**Só avance quando aprovar.**

---

### Passo 8: Setup + Camada de Dados Mockados

**Você faz:**

```
Execute a skill docs/skills/llc-step-8.md
```

**A IA faz:**
- Inicializa o projeto com o stack definido (lint, type-check, dependências)
- Cria `mocks/data/` com JSONs realistas (usuários por perfil + entidades)
- Cria `mocks/handlers/` com CRUD completo via MSW
- Atualiza `TASKS.md` e PRPs com progresso

**Você valida:** 👤 Gate 9
- O projeto compila e roda localmente?
- Os dados mock são realistas e cobrem todos os perfis?
- Os handlers simulam erros corretamente?

**Só avance quando aprovar.**

---

### Passo 9: Documentação de Testes

**Você faz:**

```
Execute a skill docs/skills/llc-step-9.md
```

**A IA faz:** Gera em `docs/testing/`:
- `TESTING_GUIDE.md` — filosofia, pirâmide, templates de teste, estratégia de mocks
- `COVERAGE_BASELINE.md` — baseline de cobertura (ponto zero)
- `COVERAGE_PROGRESS.md` — metas por fase e tabela de progresso semanal

**Você valida:** 👤 Gate 10
- Os comandos de teste batem com o stack definido?
- Os thresholds de cobertura estão realistas (80% unitários, 70% integração)?
- Os templates de teste são reutilizáveis?

**Só avance quando aprovar.**

---

### Passo 10: Documentos do Projeto

**Você faz:**

```
Execute a skill docs/skills/llc-step-10.md
```

**A IA faz:**
- `README.md` na raiz — portal de entrada com badges, stack, como rodar, docs
- `docs/DEPLOYMENT.md` — ambientes, pipeline CI/CD, variáveis, rollback, monitoramento

**Você valida:** 👤 Gate 11
- Um dev novo consegue rodar o projeto em ≤ 10 min seguindo o README?
- O DEPLOYMENT cobre rollback e monitoramento?
- Não há secrets ou credenciais expostos?

**Só avance quando aprovar.**

---

### Passo 11: Execução

**Agora começa o desenvolvimento.** Você tem duas trilhas:

#### Trilha A: PRPs sem UI (backend, infra)

```
Execute as tarefas do TASKS.md diretamente com agentes de desenvolvimento.
Cada PRP sem UI é implementado sequencialmente ou em paralelo (conforme matriz).
```

#### Trilha B: PRPs com UI (frontend) — Subfluxo de Prototipagem

Para cada módulo ou PRP que envolva telas, execute:

```
Execute a skill docs/skills/llc-subflow-prototyping.md --module MOD-PLN-001
```

O subfluxo tem 6 fases:

| Fase | O que acontece | Você faz |
|------|---------------|----------|
| **F1** Discovery | IA gera personas e journey maps | Revisa |
| **F2** Tokens | IA gera tokens CSS/JSON do Design System | Revisa |
| **F3** Lo-Fi | IA gera wireframes de baixa fidelidade | Revisa |
| **F4** Hi-Fi | IA gera protótipo de alta fidelidade | 🔴 **CHECKPOINT VISUAL** — Aprova o visual |
| **F5** Código | IA gera componentes e páginas | Revisa |
| **F6** Validação | IA valida usabilidade, a11y, responsividade | Revisa |

---

## Fluxo de Aprovação

```
                    👤 = Gate humano obrigatório
                    🔴 = Checkpoint visual obrigatório

Step 0 ──→ Step 0.1 ──→ Step 0.5 ──👤──→ Step 1 ──👤──→ Step 2 ──👤──→ Step 3 ──👤──→
Step 4 ──👤──→ Step 5 ──👤──→ Step 6 ──👤──→ Step 7 ──👤──→
Step 8 ──👤──→ Step 9 ──👤──→ Step 10 ──👤──→

Step 11:
  ├── PRPs sem UI → agente direto
  └── PRPs com UI → F1→F2→F3→F4─🔴─→F5→F6
```

**Regra de ouro:** Nenhum passo avança sem o gate anterior aprovado.

---

## Dicas Práticas

### Se um skill falhar
- Leia o erro. A IA vai reportar o que deu errado.
- Corrija a entrada (ex: documento faltando, template incompleto).
- Re-execute o skill.

### Se um gate for reprovado
- Anote o que precisa ser ajustado.
- Peça à IA para corrigir: "O glossário está inconsistente com os requisitos funcionais. Corrija."
- Re-valide.

### Monitorando a Saúde do Código

Com múltiplos agentes atuando em paralelo, é essencial monitorar métricas estruturais:

```
python .ace/scripts/code-health.py --since "30 days ago"
```

O script analisa 4 métricas:
- **% Moved Code:** taxa de código reorganizado em módulos (alerta se < 10%)
- **Copy/Paste vs Moved:** duplicação superando reuso (alerta se copy > moved)
- **% Legacy Touch:** código antigo sendo refatorado (alerta se < 20%)

Se alertas críticos forem disparados, agende uma onda de refatoração cross-PRP.

### Se precisar recomeçar um passo
- Skills são idempotentes. A IA perguntará antes de sobrescrever arquivos existentes.
- Responda "sim, sobrescreva" ou "não, crie uma nova versão com sufixo _v2".

### Trabalhando em equipe
- O pipeline suporta múltiplos usuários. Cada gate é um ponto natural de sincronização.
- Use branches Git para isolar o trabalho de cada passo, se desejar.
- Os artefatos são arquivos Markdown — use PRs para revisão colaborativa.

---

## Referência Rápida

| Quero... | Comando |
|----------|---------|
| Iniciar o pipeline | `Execute a skill docs/skills/llc-step-0-1.md` (conversão) |
| Pular para um passo específico | `Execute a skill docs/skills/llc-step-N.md` certificando-se de que os gates anteriores foram aprovados |
| Prototipar um módulo | `Execute a skill docs/skills/llc-subflow-prototyping.md --module MOD-PLN-001` |
| Ver o design completo | Leia [`llc-pipeline-design.md`](llc-pipeline-design.md) |
| Ver a estrutura de diretórios | Leia [`llc-pipeline-design.md` §2](llc-pipeline-design.md#2-arquitetura-de-diretórios) |
| Entender um termo | Leia [`llc-pipeline-design.md` §8](llc-pipeline-design.md#8-glossário-llc) |

---

## Próximos Passos Após o Pipeline

1. O MVP mockado está rodando → valide com stakeholders
2. CHECKPOINT MVP aprovado → implemente integrações reais
3. Integrações funcionando → implante em staging
4. Testes de aceite passando → implante em produção
5. Monitore e itere
