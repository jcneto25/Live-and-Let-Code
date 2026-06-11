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
