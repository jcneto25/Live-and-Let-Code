# Compressed Documentation Index — Design Specification

**Versao:** 1.0.0
**Data:** 11 de Junho de 2026
**Status:** Design Aprovado
**Projeto:** Live and Let Code (LLC) — Indice comprimido de documentacao no AGENTS.md
**Autor:** Equipe LLC

---

## 1. Visao Geral

### 1.1 Problema

O `CLAUDE.md` gerado pelo Step 10 contem uma tabela de "References" com ~13 linhas (~520 tokens) que lista artefatos LLC com nomes, locais e steps. Essa tabela e **legivel para humanos**, mas **ineficiente como indice de roteamento para agentes** — ocupa muitos tokens, nao tem palavras-chave para busca semantica e nao informa dependencias entre artefatos.

O `AGENTS.md` nao possui nenhuma secao de documentacao — ele e focado exclusivamente no protocolo de desenvolvimento (zonas, TDD, handoff). O agente precisa adivinhar onde encontrar informacao ou ler o README inteiro.

### 1.2 Solucao

Adicionar um **indice comprimido de documentacao** no `AGENTS.md` como 4a camada na tabela **Document Hierarchy**. O indice usa formato compacto delimitado por `|` com palavras-chave para roteamento, step de origem e dependencias. O `CLAUDE.md` herda o indice automaticamente via `<!-- @include AGENTS.md -->`.

### 1.3 Decisoes de Design

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| Localizacao | AGENTS.md, Document Hierarchy | Tool-agnostic: AGENTS.md e carregado por todos os clientes. A Document Hierarchy e a secao onde o agente aprende as camadas de verdade |
| Formato da linha | `diretorio \| arquivo (KEYWORDS) \| step \| depends_on` | Maximo de informacao no minimo de tokens |
| Artefatos cobertos | 16 essenciais | Cobre especificacao, arquitetura, testes, deploy e manual — o necessario para roteamento |
| Relacao com tabela existente | Mantida no CLAUDE.md | Legibilidade humana preservada; agente usa o indice comprimido |
| Preenchimento | Step 10 preenche placeholder `{{DOCS_INDEX}}` | Automatizado, sem scripts extras |

---

## 2. Modificacoes no `AGENTS_TEMPLATE.md`

### 2.1 Nova linha na Document Hierarchy

```markdown
| **Documentation Index** (below) | Compressed routing map — where to find artifacts |
```

### 2.2 Nova secao apos a tabela

```markdown
### Documentation Index (Compressed)

Compact routing map for agents. Read descriptions for routing, not full comprehension.
Load full files on demand only when the task requires them.

Format: `directory | file (KEYWORDS) | step | depends_on`

{{DOCS_INDEX}}

When in doubt about which artifact to consult, use the impact analyzer:
`python .ace/scripts/impact-analyzer.py --files "..." --json --skills`
```

### 2.3 Catalogo do Indice Comprimido

16 linhas preenchidas pelo Step 10 quando os artefatos existirem:

```
docs/business/specs/ | visao_estrategica_e_negocio.md (VISAO, ESCOPO, ATORES, OBJETIVOS) | Step 0.5 | ingestion
docs/business/specs/ | glossario.md (TERMOS, SIGLAS, DEFINICOES, VOCABULARIO) | Step 1 | visao
docs/business/specs/ | requisitos_funcionais.md (FEATURES, COMPORTAMENTO, GHERKIN) | Step 1 | visao, glossario
docs/business/specs/ | requisitos_nao_funcionais.md (PERFORMANCE, SEGURANCA, RESTRICOES) | Step 1 | visao
docs/business/specs/ | regras_negocio.md (REGRAS, VALIDACOES, CONDICOES) | Step 1 | visao, glossario
docs/business/specs/ | workflows_bpmn.md (FLUXOS, PROCESSOS, DIAGRAMAS) | Step 1 | modulos
docs/business/specs/ | perfis_permissoes.md (PERFIS, ROLES, ACESSOS, RBAC) | Step 1 | visao
docs/business/specs/ | catalogo_integracoes.md (APIS, SERVICOS, EXTERNOS) | Step 1 | visao
docs/prd/ | executive_PRD.md (RESUMO, STAKEHOLDERS, VALOR) | Step 2 | visao, glossario
docs/prd/ | PRD_tecnico_institucional.md (STACK, REQUISITOS, API, DB) | Step 2 | specs
docs/prps/ | PRP-*.md (CONTRATO, IMPLEMENTACAO, GHERKIN, TESTES) | Step 3 | prd_tecnico
docs/architecture/ | ARCHITECTURE.md (STACK, C4, ADRS, CI/CD, SEGURANCA) | Step 5 | prd_tecnico, rnf
docs/design/ | DESIGN_SYSTEM.md (TOKENS, COMPONENTES, PADROES, A11Y) | Step 7 | arquitetura, perfis
docs/testing/ | TESTING_GUIDE.md (TDD, MOCKS, TEMPLATES, THRESHOLDS) | Step 9 | arquitetura, prps
docs/ | DEPLOYMENT.md (AMBIENTES, PIPELINE, ROLLBACK, VARIAVEIS) | Step 10 | arquitetura
docs/user-guide/ | USER_GUIDE.md (MANUAL, USUARIO, TUTORIAIS, NAVEGACAO) | Step 10.5 | prps, perfis
```

### 2.4 Estimativa de Tokens

| Indice | Linhas | Tokens/linha | Total |
|--------|--------|-------------|-------|
| Tabela atual (CLAUDE.md References) | 13 | ~40 | ~520 |
| Indice comprimido (AGENTS.md) | 16 | ~25 | ~400 |

O indice comprimido cobre **mais artefatos** (16 vs 13) com **menos tokens** (~400 vs ~520). Reducao de ~23% com cobertura 23% maior.

---

## 3. Modificacoes no `llc-step-10.md`

### 3.1 Nova subsecao no prompt de execucao

Adicionada apos a secao de geracao de CLAUDE.md + AGENTS.md:

```markdown
### 6. Preencha o Documentation Index no AGENTS.md

No `AGENTS.md` gerado, preencha o placeholder `{{DOCS_INDEX}}` com o indice
comprimido de todos os artefatos LLC existentes no projeto.

#### Regras de preenchimento

1. **Formato fixo por linha:** `directory | file (KEYWORDS) | step | depends_on`
2. **KEYWORDS:** 3-5 palavras-chave em ingles, uppercase, que o agente encontrara
   em suas tarefas. Ex: `(STACK, C4, ADRS, SEGURANCA)` para ARCHITECTURE.md.
3. **step:** O step LLC que gerou o artefato. Ex: `Step 5`.
4. **depends_on:** Artefatos que este depende (nomes curtos, separados por virgula).
   Ex: `prd_tecnico, rnf`.
5. **So inclua artefatos que EXISTEM.** Se um spec nao foi gerado, nao o liste.
6. **PRPs usam wildcard:** `PRP-*.md` — nao liste PRPs individuais.
7. **Ordem:** Agrupe por diretorio, mesma ordem do pipeline (Step 0 → Step 10.5).
```

### 3.2 Atualizacao na saida esperada

Adicionar item 5:

```markdown
5. **Documentation Index:** O indice comprimido foi preenchido no AGENTS.md?
   Todas as keywords cobrem os dominios do projeto?
```

---

## 4. Impacto nos Artefatos

| Artefato | Impacto |
|----------|---------|
| `docs/templates/AGENTS_TEMPLATE.md` | Nova linha na Document Hierarchy + nova secao `### Documentation Index` com placeholder `{{DOCS_INDEX}}` |
| `docs/skills/llc-step-10.md` | Nova subsecao de preenchimento do indice + atualizacao da saida esperada |
| `CLAUDE_TEMPLATE.md` | Nenhuma alteracao — herda o indice via `<!-- @include AGENTS.md -->` |

---

## 5. Controle de Versao

| Versao | Data | Autor | Alteracoes |
|--------|------|-------|------------|
| 1.0.0 | 11/06/2026 | Equipe LLC | Versao inicial do design de indice comprimido de documentacao |
