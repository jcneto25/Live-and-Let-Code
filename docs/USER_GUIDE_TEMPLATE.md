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
