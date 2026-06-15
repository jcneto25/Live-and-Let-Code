# User Guide Documentation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add user-facing documentation generation (`llc-user-guide` skill) to the LLC pipeline, enabling incremental user manual creation via PRP `user_docs` sections.

**Architecture:** New skill `llc-user-guide` runs within Step 10, generating a Markdown skeleton at `docs/user-guide/`. Each PRP declares its documentation pages in a new `user_docs` section. Visual assets follow a cascade: Playwright screenshots → Mermaid diagrams → text descriptions. No external tools or build steps required.

**Tech Stack:** Markdown, YAML frontmatter, Mermaid (diagrams), optional Playwright/Puppeteer/Selenium for screenshots.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `docs/USER_GUIDE_TEMPLATE.md` | CREATE | Structure template for the user guide skeleton |
| `docs/skills/llc-user-guide.md` | CREATE | Skill that generates the skeleton from PRPs + specs |
| `docs/prps/PRP_TEMPLATE.md` | MODIFY | Add `user_docs` section between section 12 (DoD) and footer |
| `docs/skills/llc-step-10.md` | MODIFY | Add `llc-user-guide` invocation after gate 11 |
| `llc-pipeline-design.md` | MODIFY | Document new skill, gate 11.5, updated directory structure, extended skill catalog |
| `LLC_GUIDE.md` | MODIFY | Add Step 10.5 and Gate 11.5 to step-by-step guide |
| `FAQ.md` | MODIFY | Add user guide FAQ section |
| `FAQ.en.md` | MODIFY | Add user guide FAQ section (English) |

---

### Task 1: Create USER_GUIDE_TEMPLATE.md

**Files:**
- Create: `docs/USER_GUIDE_TEMPLATE.md`

- [ ] **Step 1: Write the template**

```markdown
# USER_GUIDE.md — Manual do Usuario

**Versao:** 1.0.0
**Projeto:** [{NOME DO SISTEMA}]
**Ultima atualizacao:** {YYYY-MM-DD}

---

## 1. Bem-vindo

Bem-vindo ao manual do usuario do **{NOME DO SISTEMA}**. Este guia foi criado para ajudar voce a utilizar todas as funcionalidades do sistema.

### 1.1 O que e o {NOME DO SISTEMA}?

{Descricao de 1 paragrafo sobre o sistema, extraida da visao estrategica.}

### 1.2 Quem usa este sistema?

| Perfil | Descricao | Principais funcionalidades |
|--------|-----------|---------------------------|
{Preencher com perfis de `perfis_permissoes.md`}

### 1.3 Como navegar neste manual

- **Por perfil:** Acesse a secao [Guias por Perfil](#3-guias-por-perfil) para encontrar conteudo relevante ao seu papel.
- **Por modulo:** Use o indice na secao [Modulos](#4-modulos) para navegar pelas funcionalidades do sistema.
- **Busca:** Use a busca do GitHub/GitLab (`Ctrl+K` ou `/`) para encontrar termos especificos.

---

## 2. Visao Geral do Sistema

{Derivado de `visao_estrategica_e_negocio.md`. Descrever o proposito, principais modulos e fluxos gerais do sistema em linguagem de usuario final.}

### 2.1 Principais Fluxos

| Fluxo | Descricao | Modulos envolvidos |
|-------|-----------|-------------------|
{Preencher com fluxos de `workflows_bpmn.md`}

### 2.2 Glossario

| Termo | Significado |
|-------|-------------|
{Preencher com termos relevantes ao usuario de `glossario.md`}

---

## 3. Guias por Perfil

{Cada perfil de `perfis_permissoes.md` vira uma secao listando paginas relevantes.}

### 3.1 {Nome do Perfil}

**Descricao:** {Descricao do perfil extraida de `perfis_permissoes.md`}

**Paginas relevantes:**
- {Link para pagina} — {descricao curta}
- ...

---

## 4. Modulos

{Indice de todas as paginas declaradas nos PRPs, agrupadas por modulo.}

### 4.1 {Nome do Modulo}

- [{Titulo da pagina}]({caminho}) — {descricao curta}
- ...

---

## 5. Convencoes

Este manual segue as seguintes convencoes:

- **Botoes** sao indicados em **negrito** (ex: clique em **Salvar**).
- **Menus** usam o sinal `>` para indicar navegacao (ex: **Administracao > Usuarios > Cadastro**).
- **Campos** sao indicados em `codigo` (ex: preencha o campo `E-mail`).
- **Alertas** usam blockquotes com emoji:
  - ⚠️ Atencao: informacao importante
  - 💡 Dica: sugestao util
  - 🔒 Restrito: funcionalidade limitada por perfil

---

## 6. Suporte

{Informacoes de contato, links para FAQ, repositorio.}

---

> **Nota:** Este esqueleto e gerado automaticamente pela skill `llc-user-guide` (Step 10.5)
> e preenchido incrementalmente pelos PRPs durante a execucao (Step 11).
> Para adicionar novas paginas, declare a secao `user_docs` no PRP correspondente.
```

- [ ] **Step 2: Commit**

```bash
git add docs/USER_GUIDE_TEMPLATE.md
git commit -m "docs: add USER_GUIDE_TEMPLATE.md for user guide skeleton structure"
```

---

### Task 2: Create llc-user-guide skill

**Files:**
- Create: `docs/skills/llc-user-guide.md`

- [ ] **Step 1: Write the skill file**

```markdown
---
name: llc-user-guide
description: Pipeline LLC Step 10.5: Gera o esqueleto do manual do usuario a partir dos PRPs, perfis e workflows. O manual e preenchido incrementalmente pelos PRPs durante a execucao (Step 11).
version: 1.0.0
tags: [documentacao, user-guide, manual-usuario, llc-pipeline]
---

# LLC Skill: Step 10.5 — Manual do Usuario

**Pipeline:** Live and Let Code (LLC)
**Fase:** Project Documentation
**Depende de:** Step 10 (Project Docs — gate 11 aprovado), Steps 0.5-3 (PRPs, Perfis, Workflows, Glossario)
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-user-guide` ou "Execute a skill llc-user-guide".

## 📋 Pre-requisitos

- [ ] `docs/prps/PRP-*.md` — todos os PRPs (para extrair paginas declaradas em `user_docs`)
- [ ] `docs/business/specs/perfis_permissoes.md` — perfis de usuario (Step 1)
- [ ] `docs/business/specs/workflows_bpmn.md` — fluxos do sistema (Step 1)
- [ ] `docs/business/specs/glossario.md` — glossario de termos (Step 1)
- [ ] `docs/business/specs/visao_estrategica_e_negocio.md` — visao do sistema (Step 0.5)
- [ ] `docs/USER_GUIDE_TEMPLATE.md` — template do esqueleto
- [ ] Gate 11 (Step 10) aprovado

---

## 🎯 PROMPT DE EXECUCAO

Voce esta executando a skill `llc-user-guide` do pipeline LLC. Seu objetivo e gerar o **esqueleto do manual do usuario** em `docs/user-guide/`, que sera preenchido incrementalmente durante a execucao dos PRPs (Step 11).

### 1. Leia as Entradas

- `docs/prps/PRP-*.md` — leia a secao `user_docs` de cada PRP. Extraia a tabela `Paginas` (arquivo, titulo, perfil).
- `docs/business/specs/perfis_permissoes.md` — lista de perfis com descricao.
- `docs/business/specs/workflows_bpmn.md` — fluxos principais do sistema.
- `docs/business/specs/glossario.md` — termos e definicoes para o usuario.
- `docs/business/specs/visao_estrategica_e_negocio.md` — visao geral e objetivo do sistema.
- `docs/USER_GUIDE_TEMPLATE.md` — template de estrutura.

### 2. Gere o Esqueleto

Preencha o template `USER_GUIDE_TEMPLATE.md` e salve os seguintes arquivos:

| # | Arquivo | Conteudo |
|---|---------|----------|
| 1 | `docs/user-guide/USER_GUIDE.md` | Esqueleto completo: indice de paginas, mapa de navegacao, guia por perfil, convencoes, suporte |
| 2 | `docs/user-guide/index.md` | Pagina inicial: o que e o sistema, para quem e, como navegar |
| 3 | `docs/user-guide/visao-geral.md` | Visao geral do sistema em linguagem de usuario final |
| 4 | `docs/user-guide/perfis/index.md` | Guia indexado por perfil com links para paginas relevantes |

### 3. Construa o Indice de Modulos

Na secao 4 (Modulos) do `USER_GUIDE.md`, liste todas as paginas declaradas nos PRPs, agrupadas por modulo:

- Agrupe paginas por diretorio (ex: `admin/`, `operador/`).
- Para cada pagina, inclua: titulo, caminho relativo, descricao curta, perfil alvo.
- Se um modulo nao tem nenhum PRP com `user_docs`, nao aparece no indice.

### 4. Construa os Guias por Perfil

Na secao 3 (Guias por Perfil) do `USER_GUIDE.md`:

- Para cada perfil em `perfis_permissoes.md`, crie uma subsecao com descricao do perfil.
- Liste as paginas relevantes para aquele perfil (extraido da coluna `Perfil` da secao `user_docs` de cada PRP).
- Se um perfil nao tem paginas associadas, indique "Nenhuma pagina especifica — este perfil utiliza funcionalidades compartilhadas."

### 5. Crie a Pagina Inicial (index.md)

`docs/user-guide/index.md` deve conter:

- Titulo e descricao do sistema (1 paragrafo).
- Links rapidos: "Sou Administrador", "Sou Operador", etc.
- Link para `USER_GUIDE.md` (indice completo).
- Link para `visao-geral.md`.
- Instrucoes de busca no GitHub/GitLab.

### 6. Crie a Visao Geral (visao-geral.md)

`docs/user-guide/visao-geral.md` deve conter:

- Proposito do sistema (derivado da visao estrategica).
- Principais modulos e o que cada um faz.
- Fluxos principais (derivados dos workflows).
- Glossario de termos relevantes ao usuario.

### 7. CREATE DIRECTORIES

Crie os diretorios necessarios:

```bash
mkdir -p docs/user-guide/perfis
```

Os diretorios `docs/user-guide/admin/`, `docs/user-guide/operador/`, etc. serao criados pelos PRPs conforme necessario — nao precisam ser criados agora.

---

## ⚠️ REGRAS CRITICAS

1. **Linguagem de usuario final:** Todo o conteudo deve ser escrito para quem vai USAR o sistema, nao para quem vai desenvolve-lo. Evite jargoes tecnicos.
2. **Nao invente paginas:** So liste paginas que estao declaradas na secao `user_docs` de PRPs existentes. Se um modulo nao tem PRP com `user_docs`, nao aparece no indice.
3. **Nao sobrescreva conteudo de PRPs:** Este skill gera APENAS o esqueleto e paginas de navegacao. As paginas de conteudo (`[modulo]/*.md`) sao geradas pelos PRPs no Step 11.
4. **Reexecutavel:** Se novos PRPs forem adicionados, reexecutar este skill atualiza o indice e os guias por perfil sem perder paginas ja geradas por PRPs.
5. **Idempotencia:** Verifique existencia dos arquivos antes de sobrescrever. Pergunte ao usuario antes de substituir.
6. **Perfis obrigatorios:** Todo link de pagina no indice deve incluir o perfil alvo (extraido da coluna `Perfil` do `user_docs`).

---

## 📤 SAIDA ESPERADA E FINALIZACAO

Apos gerar os 4 arquivos, **PARE** e apresente:

1. **USER_GUIDE.md:** Secoes geradas, numero de paginas no indice, perfis cobertos.
2. **index.md:** Links rapidos e estrutura de navegacao.
3. **visao-geral.md:** Modulos listados, fluxos documentados.
4. **perfis/index.md:** Perfis com paginas associadas. Algum perfil ficou sem pagina?
5. **Modulos nao cobertos:** Algum PRP com UI nao declarou `user_docs`? Liste-os.
6. **Gate 11.5:** "A estrutura cobre todos os modulos? Os perfis tem paginas relevantes? A linguagem e adequada ao usuario final?"

**Este e o ultimo passo antes da Execucao (Step 11).**
```

- [ ] **Step 2: Commit**

```bash
git add docs/skills/llc-user-guide.md
git commit -m "feat: add llc-user-guide skill for user manual skeleton generation"
```

---

### Task 3: Extend PRP_TEMPLATE.md with user_docs section

**Files:**
- Modify: `docs/prps/PRP_TEMPLATE.md` — insert new section between line 331 (end of section 12 DoD) and line 334 (footer note)

- [ ] **Step 1: Insert the user_docs section**

Insert after line 333 (after `---` that closes section 12, before the footer note):

```markdown
---

## 13. 📖 user_docs — Documentacao de Usuario

> Preenchimento obrigatorio se o PRP envolver interface de usuario ou fluxo
> visivel ao usuario final. Deixar vazio para PRPs puramente internos (infra, CI/CD).
>
> As paginas aqui declaradas serao geradas automaticamente como arquivos Markdown
> em `docs/user-guide/[modulo]/` durante a execucao do PRP (Step 11).

### Paginas

| Arquivo | Titulo | Perfil |
|---------|--------|--------|
| `modulo/pagina.md` | Titulo Amigavel | {Nome do Perfil} |

### `modulo/pagina.md`

#### Topicos
- [ ] Topico 1 — o que o usuario aprende
- [ ] Topico 2 — passo a passo
- [ ] ...

#### Capturas de Tela (se aplicavel)
- [ ] 📸 Tela: [nome da tela] — [o que o usuario ve]
- [ ] 📸 Tela: [nome da tela] — [o que o usuario ve]

> **📸 Capturas de Tela:**
> - Se **Playwright, Puppeteer ou Selenium** estiver instalado, screenshots PNG sao geradas automaticamente em `docs/user-guide/[modulo]/img/`.
> - Caso contrario, **diagramas Mermaid** do fluxo da tela sao gerados inline no arquivo `.md`.
> - Se nenhum dos dois estiver disponivel, uma **descricao textual estruturada** e gerada.
> - Para adicionar screenshots manualmente, veja a secao de FAQ.
```

- [ ] **Step 2: Renumber the existing section 11 to account for the new section**

The existing Execution Log section (currently section 11) and Definition of Done section (currently section 12) remain as-is. The new section 13 (`user_docs`) goes after DoD. No renumbering of existing sections needed — the new section is appended to the end.

- [ ] **Step 3: Commit**

```bash
git add docs/prps/PRP_TEMPLATE.md
git commit -m "feat: add user_docs section to PRP_TEMPLATE for user manual generation"
```

---

### Task 4: Update llc-step-10.md to invoke llc-user-guide

**Files:**
- Modify: `docs/skills/llc-step-10.md`

- [ ] **Step 1: Add user guide invocation after gate 11**

At the end of the file (after line 306, which is the stop message), add a new section:

```markdown

---

### 6. Proximo Passo: Manual do Usuario

Apos a aprovacao do **Gate 11**, execute a skill `llc-user-guide` para gerar o esqueleto do manual do usuario:

```
Execute a skill docs/skills/llc-user-guide.md
```

A skill `llc-user-guide` gera a estrutura base do manual em `docs/user-guide/` com:
- Indice de paginas (extraido da secao `user_docs` de cada PRP)
- Guias por perfil de usuario
- Visao geral do sistema em linguagem de usuario final

A validacao do esqueleto ocorre no **Gate 11.5**. Apos aprovacao, siga para o Step 11 (Execucao), onde cada PRP preenchera suas paginas de manual incrementalmente.
```

- [ ] **Step 2: Update the prerequisites section**

Add to the prerequisites list (after line 28, before `---`):

```markdown
- [ ] `docs/prps/PRP-*.md` — PRPs com secao `user_docs` preenchida (Step 3)
- [ ] `docs/business/specs/perfis_permissoes.md` — perfis de usuario (Step 1)
- [ ] `docs/business/specs/workflows_bpmn.md` — fluxos do sistema (Step 1)
- [ ] `docs/business/specs/glossario.md` — glossario (Step 1)
```

- [ ] **Step 3: Update the Documentation table in README template**

In the README.md template section (around line 121-131), add a row to the documentation table:

```markdown
| Manual do Usuario | `docs/user-guide/USER_GUIDE.md` | Guia de uso em linguagem de usuario final |
```

- [ ] **Step 4: Commit**

```bash
git add docs/skills/llc-step-10.md
git commit -m "feat: add llc-user-guide invocation to llc-step-10 skill"
```

---

### Task 5: Update llc-pipeline-design.md

**Files:**
- Modify: `llc-pipeline-design.md`

- [ ] **Step 1: Add user-guide directory to the directory structure (section 2.1)**

After the `docs/testing/` block (around line 93), add:

```
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
```

Also add to the skills directory:
```
│   │   ├── llc-user-guide.md                     # [NOVO] Skill de manual do usuario
```

- [ ] **Step 2: Update pipeline flow diagram (section 3.1)**

In the Mermaid diagram, after the Step 10 block, add:

```
S10 --> G11{👤 Gate 11}
G11 -->|approved| S105[Step 10.5: User Guide Skeleton]
S105 --> G115{👤 Gate 11.5}
G115 -->|approved| S11[Step 11: LLC Execution]
```

- [ ] **Step 3: Update stage table (section 3.2)**

Add a new row after Step 10:

```
| 10.5 | User Guide | PRPs + Perfis + Workflows + Glossario | `USER_GUIDE.md`, `index.md`, `visao-geral.md`, `perfis/index.md` | `USER_GUIDE_TEMPLATE.md` | 👤 11.5 |
```

Update the Step 11 row to include user guide pages in its output:

```
| 11 | Execucao | Todos os artefatos anteriores | Codigo fonte + paginas de manual (`docs/user-guide/[modulo]/*.md`) | — | Checkpoints QA |
```

- [ ] **Step 4: Add Gate 11.5 to gates table (section 6.1)**

Add after Gate 11:

```
| 👤 11.5 | 10.5 | A estrutura cobre todos os modulos? Os perfis tem paginas relevantes? O indice e navegavel? A linguagem e adequada ao usuario final? |
```

- [ ] **Step 5: Add skill to catalog (section 4.2)**

Add after `llc-step-10`:

```
| `llc-user-guide` | 10.5 | Gera esqueleto do manual do usuario a partir dos PRPs, perfis e workflows |
```

- [ ] **Step 6: Update the gate count**

In section 6, update "11 human gates" references to "12 human gates" where applicable. Also update the gate flow diagram in section 6.2:

After `Step 10 ──👤11──→`, add:
```
llc-user-guide ──👤11.5──→
```

- [ ] **Step 7: Add USER_GUIDE_TEMPLATE.md to templates inventory (section 7.2)**

Add a new row to the templates table:

```
| 22 | User Guide | `docs/USER_GUIDE_TEMPLATE.md` | IA (Step 10.5) | `docs/user-guide/USER_GUIDE.md` |
```

- [ ] **Step 8: Update version in header**

Change the version from `1.2.0` to `1.3.0` in the document header if applicable, and add a new row to the version control table (section 12):

```
| 1.3.0 | 11/06/2026 | Equipe LLC | Adicionado Step 10.5 (User Guide) com skill `llc-user-guide`, gate 11.5 e template USER_GUIDE_TEMPLATE.md |
```

- [ ] **Step 9: Commit**

```bash
git add llc-pipeline-design.md
git commit -m "docs: add user guide step 10.5, gate 11.5, and artifacts to pipeline design"
```

---

### Task 6: Update LLC_GUIDE.md with new step and gate

**Files:**
- Modify: `LLC_GUIDE.md`

- [ ] **Step 1: Add Step 10.5 after Step 10 section**

After the Step 10 section (after the closing `---` of Step 10, around line 395), insert:

```markdown
---

### Passo 10.5: Manual do Usuario 🆕

**Você faz:**

```
Execute a skill docs/skills/llc-user-guide.md
```

**A IA faz:**
- Le todos os PRPs e extrai as paginas declaradas na secao `user_docs`
- Gera `docs/user-guide/USER_GUIDE.md` — esqueleto completo com indice e navegacao
- Gera `docs/user-guide/index.md` — pagina inicial do manual
- Gera `docs/user-guide/visao-geral.md` — visao geral em linguagem de usuario final
- Gera `docs/user-guide/perfis/index.md` — guia indexado por perfil

**Voce valida:** 👤 Gate 11.5
- A estrutura cobre todos os modulos?
- Os perfis tem paginas relevantes?
- O indice e navegavel?
- A linguagem e adequada ao usuario final?

**So avance quando aprovar.**
```

- [ ] **Step 2: Add Gate 11.5 to the approval flow**

Update the approval flow section (around line 416), adding the new gate:

```
Step 8 ──👤9──→ Step 9 ──👤10──→ Step 10 ──👤11──→
Step 10.5 ──👤11.5──→
```

- [ ] **Step 3: Update the quick reference table**

Add to the reference table (around line 489):

```
| Gerar manual do usuario | `Execute a skill docs/skills/llc-user-guide.md` |
```

- [ ] **Step 4: Commit**

```bash
git add LLC_GUIDE.md
git commit -m "docs: add Step 10.5 user guide and Gate 11.5 to LLC guide"
```

---

### Task 7: Update FAQ.md with user guide section

**Files:**
- Modify: `FAQ.md`

- [ ] **Step 1: Add new section to FAQ**

Find a good insertion point. Add after the "CLAUDE.md ou AGENTS.md? Qual usar?" section (around line 650-652) or at the end of the FAQ before the final section. Insert:

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add FAQ.md
git commit -m "docs: add user guide FAQ section (PT-BR)"
```

---

### Task 8: Update FAQ.en.md with user guide section (English)

**Files:**
- Modify: `FAQ.en.md`

- [ ] **Step 1: Add English FAQ section**

Insert the English version of the FAQ section (same position as in FAQ.md):

```markdown
---

## 📖 User Guide

### What is the user guide in LLC?

It's documentation aimed at the **end user** of the application, automatically generated by the LLC pipeline. Unlike README and DEPLOYMENT (which are for developers), the user guide teaches **how to use** the system: how to navigate, register, generate reports, etc.

The guide consists of:
- **Skeleton** (`docs/user-guide/USER_GUIDE.md`): generated by the `llc-user-guide` skill (Step 10.5), containing page index, per-profile guide, and conventions.
- **Content pages** (`docs/user-guide/[module]/*.md`): generated by PRPs during execution (Step 11). Each PRP declares which manual pages it produces in the `user_docs` section.

### Why is the user guide important in agentic development?

AI agents produce code, but end users need to understand how to use the system. The user guide closes the loop: the same AI that implements a feature also documents how to use it. This ensures documentation is always in sync with code — if code changes, re-running the PRP updates the manual.

### The guide was generated without screenshots. How do I add real screens?

LLC generates the guide with screenshots if Playwright is installed in the environment. Otherwise, it uses Mermaid diagrams as a fallback. To add real screenshots:

1. Install Playwright: `npm install -D @playwright/test && npx playwright install`
2. Start the application development server
3. Navigate to `docs/user-guide/[module]/img/`
4. Replace diagrams with real screenshots, or re-run the PRP capture script

### Can I use Puppeteer or Selenium instead of Playwright?

Yes. LLC's screenshot script automatically detects `playwright`, `puppeteer`, or `selenium-webdriver` in `package.json`. Any of the three works. Install your preferred one and re-run the PRP.

### How do I keep the guide up to date after changes?

Each executed PRP regenerates the manual pages declared in `user_docs`. If an existing feature changed (e.g., new field in a form), re-run the corresponding PRP. The impact analyzer (`llc-impact-analyzer`) reports which manual pages are affected by each code change.

### Do I need a separate website for the guide?

No. The Markdown files in `docs/user-guide/` render natively on GitHub, GitLab, and any Markdown previewer. If you want a site with search and theming, tools like MkDocs or VitePress can convert the `.md` files into a static site with a single command (`mkdocs build`), without changing the content.
```

- [ ] **Step 2: Commit**

```bash
git add FAQ.en.md
git commit -m "docs: add user guide FAQ section (EN-US)"
```

---

### Task 9: Final integration commit — update .ace/dependency-graph.yaml (if exists)

**Files:**
- Check and modify: `.ace/dependency-graph.yaml` (if the file exists)

- [ ] **Step 1: Check if dependency graph exists**

```bash
Test-Path .ace/dependency-graph.yaml
```

- [ ] **Step 2: If it exists, add user guide entries**

If the file exists and has structure, add entries for the new artifacts. If it doesn't exist or is auto-generated, skip this task.

- [ ] **Step 3: Commit**

```bash
git add .ace/dependency-graph.yaml
git commit -m "feat: add user guide artifacts to dependency graph"
```
```

[No tools used]
