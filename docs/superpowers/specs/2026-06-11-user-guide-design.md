# User Guide — Design Specification

**Versao:** 1.0.0
**Data:** 11 de Junho de 2026
**Status:** Design Aprovado
**Projeto:** Live and Let Code (LLC) — Nova funcionalidade de documentacao de usuario
**Autor:** Equipe LLC

---

## 1. Visao Geral

### 1.1 Problema

O pipeline LLC atual (v1.2.0) gera documentacao exclusivamente voltada para desenvolvedores e stakeholders tecnicos — README, DEPLOYMENT, CLAUDE.md, AGENTS.md. Nao existe uma etapa de criacao e manutencao de documentacao voltada para o **usuario final** da aplicacao (manual de uso, wiki).

### 1.2 Solucao

Nova skill `llc-user-guide` integrada ao pipeline que gera um manual do usuario como arquivos Markdown versionados em `docs/user-guide/`. O manual cresce **incrementalmente**: o esqueleto e gerado no Step 10 (Project Docs) e cada PRP alimenta suas paginas durante a execucao (Step 11).

### 1.3 Decisoes de Design

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| Ferramenta de wiki | Markdown puro | Tool-agnostic, zero build, zero dependencias, renderiza nativamente no GitHub/GitLab |
| Momento do esqueleto | Step 10 (Project Docs) | Agrupa documentacao do projeto em um unico passo |
| Crescimento | Incremental via PRP | Cada feature entrega sua propria documentacao — alinhado ao principio de PRPs auto-contidos |
| Capturas visuais | Cascata: Playwright → Mermaid → texto | Tool-agnostic, zero configuracao, sempre entrega o artefato |
| Gate | 👤 11.5 — pos-esqueleto | Validacao humana da estrutura antes da execucao |

---

## 2. Arquitetura de Artefatos

### 2.1 Artefatos Novos

| Artefato | Local | Tipo | Gerado por |
|----------|-------|------|------------|
| `llc-user-guide.md` | `docs/skills/` | Skill | Manual (criado uma vez) |
| `USER_GUIDE_TEMPLATE.md` | `docs/` | Template | Manual (criado uma vez) |
| `USER_GUIDE.md` | `docs/user-guide/` | Esqueleto | Skill `llc-user-guide` (Step 10) |
| `index.md` | `docs/user-guide/` | Pagina inicial | Skill `llc-user-guide` (Step 10) |
| `visao-geral.md` | `docs/user-guide/` | Visao geral | Skill `llc-user-guide` (Step 10) |
| `perfis/index.md` | `docs/user-guide/perfis/` | Guia por perfil | Skill `llc-user-guide` (Step 10) |
| `[modulo]/*.md` | `docs/user-guide/[modulo]/` | Paginas de manual | PRPs (Step 11) |
| `[modulo]/img/*.png` | `docs/user-guide/[modulo]/img/` | Screenshots | Script Playwright (Step 11, opcional) |

### 2.2 Artefatos Modificados

| Artefato | Local | Modificacao |
|----------|-------|-------------|
| `PRP_TEMPLATE.md` | `docs/prps/` | Nova secao `user_docs` |
| `llc-step-10.md` | `docs/skills/` | Invoca `llc-user-guide` apos gate 11 |
| `llc-pipeline-design.md` | Raiz | Documenta nova skill, gate 11.5 e artefatos |
| `LLC_GUIDE.md` | Raiz | Passo a passo atualizado com `llc-user-guide` |
| `FAQ.md` | Raiz | Nova secao de FAQ sobre manual do usuario |
| `FAQ.en.md` | Raiz | Nova secao de FAQ sobre manual do usuario (EN) |

### 2.3 Estrutura de Diretorios Atualizada

```
project-root/
├── docs/
│   ├── user-guide/                              # [NOVO] Manual do usuario
│   │   ├── USER_GUIDE.md                        # Esqueleto: indice, navegacao
│   │   ├── index.md                             # Pagina inicial
│   │   ├── visao-geral.md                       # Visao geral do sistema
│   │   ├── perfis/
│   │   │   └── index.md                         # Guia por perfil de usuario
│   │   ├── admin/
│   │   │   ├── cadastro-usuarios.md             # Pagina de manual (PRP)
│   │   │   └── img/
│   │   │       ├── listagem.png                 # Screenshot (opcional)
│   │   │       └── formulario.png               # Screenshot (opcional)
│   │   └── operador/
│   │       └── ...
│   │
│   ├── USER_GUIDE_TEMPLATE.md                   # [NOVO] Template do esqueleto
│   │
│   ├── skills/
│   │   ├── llc-user-guide.md                    # [NOVO] Skill de documentacao
│   │   └── ...
│   │
│   └── prps/
│       └── PRP_TEMPLATE.md                      # [MODIFICADO] + secao user_docs
```

---

## 3. Pipeline Atualizado

### 3.1 Fluxo

```
Step 8 ──👤9──→ Step 9 ──👤10──→ Step 10 ──👤11──→ llc-user-guide ──👤11.5──→ Step 11
```

### 3.2 Tabela de Etapas (Atualizada)

| # | Nome | Entrada | Saida | Template(s) | Gate |
|---|------|---------|-------|-------------|------|
| 10 | Project Docs | Arquitetura + Planejamento + Design System + Testing | `README.md`, `DEPLOYMENT.md`, `CLAUDE.md`, `AGENTS.md` | `CLAUDE_TEMPLATE.md`, `AGENTS_TEMPLATE.md` | 👤 11 |
| 10.5 | User Guide | PRPs + Perfis + Workflows + Glossario | `USER_GUIDE.md`, `index.md`, `visao-geral.md`, `perfis/index.md` | `USER_GUIDE_TEMPLATE.md` | 👤 11.5 |
| 11 | Execucao | Todos os artefatos anteriores | Codigo fonte + paginas de manual | — | Checkpoints QA |

### 3.3 Novo Gate — 👤 11.5

| Gate | Apos Step | O que e validado |
|------|-----------|-----------------|
| 👤 11.5 | 10.5 (User Guide) | A estrutura cobre todos os modulos? Os perfis tem paginas relevantes? O indice e navegavel? A linguagem e adequada ao usuario final? |

---

## 4. Skill `llc-user-guide`

### 4.1 Metadados

```yaml
---
name: llc-user-guide
description: Gera o esqueleto do manual do usuario a partir dos PRPs, perfis e workflows
version: 1.0.0
tags: [documentacao, llc-pipeline, user-guide]
---
```

### 4.2 Entrada

- `docs/prps/PRP-*.md` — todos os PRPs (le a secao `user_docs` de cada um)
- `docs/business/specs/perfis_permissoes.md` — para guia por perfil
- `docs/business/specs/workflows_bpmn.md` — para entender fluxos do sistema
- `docs/business/specs/glossario.md` — para glossario voltado ao usuario
- `docs/USER_GUIDE_TEMPLATE.md` — template de estrutura

### 4.3 Saida

| Arquivo | Conteudo |
|---------|----------|
| `docs/user-guide/USER_GUIDE.md` | Esqueleto completo: indice de todas as paginas declaradas nos PRPs, mapa de navegacao, guia por perfil, convencoes de escrita |
| `docs/user-guide/index.md` | Pagina inicial: o que e o sistema, para quem e, como navegar no manual |
| `docs/user-guide/visao-geral.md` | Visao geral do sistema em linguagem de usuario final (derivada de `visao_estrategica_e_negocio.md`) |
| `docs/user-guide/perfis/index.md` | Guia indexado por perfil (Administrador, Operador, etc.) com links para paginas relevantes |

### 4.4 Regras

1. So gera paginas que estao declaradas na secao `user_docs` de cada PRP.
2. Nao inventa paginas — se um modulo nao tem PRP com `user_docs`, nao entra no indice.
3. A linguagem e voltada ao **usuario final**, nao ao desenvolvedor.
4. O esqueleto e reexecutavel — se novos PRPs forem adicionados, reexecutar o skill atualiza o indice.
5. Nao sobrescreve paginas ja geradas por PRPs durante a execucao.

---

## 5. Extensao do PRP Template

### 5.1 Nova Secao: `user_docs`

Adicionada apos a secao de testes no `PRP_TEMPLATE.md`.

```markdown
## 📖 user_docs

> Preenchimento obrigatorio se o PRP envolver interface de usuario ou fluxo
> visivel ao usuario final. Deixar vazio para PRPs puramente internos (infra, CI/CD).

### Paginas

| Arquivo | Titulo | Perfil |
|---------|--------|--------|
| `modulo/pagina.md` | Titulo Amigavel | Nome do Perfil |

### `modulo/pagina.md`

#### Topicos
- [ ] Topico 1 — o que o usuario aprende
- [ ] Topico 2 — passo a passo
- [ ] ...

#### Capturas de Tela (se aplicavel)
- [ ] 📸 Tela: [nome da tela] — [oque o usuario ve]
- [ ] 📸 Tela: [nome da tela] — [oque o usuario ve]
```

### 5.2 Regras

1. **PRP sem UI** (backend, infra, CI/CD): `user_docs` vazio. Nada e gerado.
2. **PRP com UI**: `user_docs` preenchido. Cada arquivo em `Paginas` vira um `.md` em `docs/user-guide/`.
3. **Topicos**: servem como guia para a IA — ela so escreve sobre features que foram implementadas e validadas.
4. **Capturas de Tela (📸)**: disparam o script de screenshot se Playwright/Puppeteer/Selenium estiver disponivel. Caso contrario, geram diagrama Mermaid do fluxo da tela.
5. **Perfil**: campo obrigatorio. Vincula a pagina ao guia por perfil (`perfis/index.md`).
6. **Idempotencia**: reexecutar o PRP regenera as paginas — o conteudo reflete o estado atual do codigo.

---

## 6. Cascata Visual

### 6.1 Estrategia

Deteccao automatica em tempo de execucao (Step 11), sem arquivo de configuracao:

```
PRP tem user_docs com 📸 ?
  ├── NAO → pagina so com texto
  └── SIM → playwright disponivel? (npx playwright --version)
               ├── SIM → screenshots PNG em img/
               └── NAO → mermaid disponivel? (sempre — e texto puro)
                            ├── SIM → diagrama de fluxo de tela inline no .md
                            └── NAO → descricao textual estruturada
```

### 6.2 Deteccao de Ferramenta

A skill verifica em ordem:

1. `npx playwright --version` — se retornar versao, usa Playwright
2. `npx puppeteer --version` — se retornar versao, usa Puppeteer
3. `npx selenium-webdriver --version` — se retornar versao, usa Selenium
4. Nenhum disponivel — fallback para Mermaid

A verificacao usa `package.json` do projeto (instalado no Step 8). Para stacks nao-Node.js (Python, Go, Rust), a deteccao retorna fallback Mermaid automaticamente. O usuario pode instalar Playwright globalmente e usar o caminho absoluto se desejar screenshots em stacks alternativas.

### 6.3 Exemplo: Pagina com Screenshot (Playwright disponivel)

```markdown
# Cadastro de Usuarios

## Como acessar
Acesse **Administracao > Usuarios > Cadastro**.

## Listagem de Usuarios

![Listagem de usuarios](img/listagem.png)

A tabela exibe: nome, e-mail, perfil, status e data de criacao.
Ao clicar no nome de um usuario, voce acessa a tela de edicao.
```

### 6.4 Exemplo: Pagina com Mermaid (fallback)

```markdown
# Cadastro de Usuarios

## Tela de Listagem

```mermaid
flowchart LR
    A[Barra Superior: Admin > Usuarios] --> B[Campo de Busca]
    B --> C[Tabela: Nome | Email | Perfil | Status | Acoes]
    C --> D[Botao: + Novo Usuario]
    C --> E[Botao: Importar CSV]
    D --> F[Modal: Formulario de Cadastro]
    F --> G[Campos: Nome, Email, Perfil, Senha]
    G --> H[Botao: Salvar]
```

A tabela exibe: nome, e-mail, perfil, status e data de criacao.
Ao clicar no nome de um usuario, voce acessa a tela de edicao.
```

### 6.5 Exemplo: Pagina com Texto (ultimo fallback)

```markdown
# Cadastro de Usuarios

## Tela de Listagem

A tela de listagem contem:
- **Barra superior:** Navegacao Admin > Usuarios
- **Campo de busca:** Filtro por nome ou e-mail
- **Tabela:** Colunas — Nome, E-mail, Perfil, Status, Acoes
- **Botao "+ Novo Usuario":** Abre modal com formulario de cadastro
- **Botao "Importar CSV":** Abre tela de importacao em lote

A tabela exibe: nome, e-mail, perfil, status e data de criacao.
Ao clicar no nome de um usuario, voce acessa a tela de edicao.
```

---

## 7. FAQ

### 7.1 Nova Secao no FAQ.md / FAQ.en.md

```markdown
### 📖 Manual do Usuario

**P: O manual foi gerado sem screenshots. Como adicionar as telas reais?**

R: O LLC gera o manual com screenshots se o Playwright estiver instalado no ambiente.
Caso contrario, usa diagramas Mermaid como fallback. Para adicionar screenshots reais:

1. Instale o Playwright: `npm install -D @playwright/test && npx playwright install`
2. Execute o servidor de desenvolvimento da aplicacao
3. Navegue ate `docs/user-guide/[modulo]/img/`
4. Substitua os diagramas por screenshots reais ou execute o script de captura do PRP novamente

**P: Posso usar Puppeteer ou Selenium em vez de Playwright?**

R: Sim. O script de screenshot do LLC detecta automaticamente `playwright`, `puppeteer`
ou `selenium-webdriver` no `package.json`. Qualquer um dos tres funciona. Instale o de
sua preferencia e re-execute o PRP.

**P: Como manter o manual atualizado apos mudancas?**

R: A cada PRP executado, as paginas de manual declaradas em `user_docs` sao
regeneradas. Se uma feature existente mudou (ex: campo novo no formulario),
re-execute o PRP correspondente. O analisador de impacto (`llc-impact-analyzer`)
reporta quais paginas de manual sao afetadas por cada alteracao de codigo.

**P: Preciso de um site separado para o manual?**

R: Nao. Os arquivos Markdown em `docs/user-guide/` sao renderizados nativamente no
GitHub, GitLab e qualquer previewer de Markdown. Se desejar um site com busca e tema,
ferramentas como MkDocs ou VitePress podem converter os `.md` em site estatico com
comando unico (`mkdocs build`), sem alterar o conteudo.
```

---

## 8. Catalogo de Skills (Atualizado)

| Skill | Passo | Descricao |
|-------|-------|-----------|
| `llc-step-10` | 10 | Gera README.md, DEPLOYMENT.md, CLAUDE.md, AGENTS.md |
| `llc-user-guide` | 10.5 | Gera esqueleto do manual do usuario a partir dos PRPs, perfis e workflows |
| `llc-step-11` | 11 | Execucao dos PRPs com geracao incremental de paginas de manual |

---

## 9. Impacto nos Artefatos Existentes

| Artefato | Impacto |
|----------|---------|
| `llc-pipeline-design.md` | Nova skill e gate na tabela de etapas, secao de diretorios atualizada |
| `LLC_GUIDE.md` | Novo passo 10.5 no guia passo a passo, novo gate 11.5 |
| `PRP_TEMPLATE.md` | Nova secao `user_docs` |
| `llc-step-10.md` | Invoca `llc-user-guide` apos gate 11 |
| `FAQ.md` / `FAQ.en.md` | Nova secao de FAQ sobre manual do usuario |
| `.ace/dependency-graph.yaml` | Novas entradas para `USER_GUIDE.md` e paginas de manual |

---

## 10. Controle de Versao

| Versao | Data | Autor | Alteracoes |
|--------|------|-------|------------|
| 1.0.0 | 11/06/2026 | Equipe LLC | Versao inicial do design de documentacao de usuario |
