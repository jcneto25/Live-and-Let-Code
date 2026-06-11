# Compressed Documentation Index — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a compressed documentation index to `AGENTS.md` as a 4th layer in the Document Hierarchy table, enabling agents to route to LLC artifacts with minimal token cost.

**Architecture:** Two-file change. `AGENTS_TEMPLATE.md` gains a new row in Document Hierarchy + a `### Documentation Index` section with placeholder `{{DOCS_INDEX}}`. `llc-step-10.md` gains a sub-section instructing the AI to fill the placeholder with 16-line compressed index during generation.

**Tech Stack:** Markdown, YAML frontmatter.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `docs/templates/AGENTS_TEMPLATE.md` | MODIFY | Add Documentation Index row + compressed index section |
| `docs/skills/llc-step-10.md` | MODIFY | Add index filling instructions to execution prompt |

---

### Task 1: Add Documentation Index to AGENTS_TEMPLATE.md

**Files:**
- Modify: `docs/templates/AGENTS_TEMPLATE.md`

- [ ] **Step 1: Add new row to Document Hierarchy table**

Insert after the `CLAUDE.md` row (line 49):

```markdown
| **Documentation Index** (below) | Compressed routing map — where to find artifacts |
```

- [ ] **Step 2: Add Documentation Index section after the Document Hierarchy table**

Insert after the conflict note (after line 51) and before `## PART I`:

```markdown

### Documentation Index (Compressed)

Compact routing map for agents. Read descriptions for routing, not full comprehension.
Load full files on demand only when the task requires them.

Format: `directory | file (KEYWORDS) | step | depends_on`

{{DOCS_INDEX}}

When in doubt about which artifact to consult, use the impact analyzer:
`python .ace/scripts/impact-analyzer.py --files "..." --json --skills`

```

- [ ] **Step 3: Commit**

```bash
git add docs/templates/AGENTS_TEMPLATE.md
git commit -m "feat: add compressed Documentation Index to AGENTS_TEMPLATE.md"
```

---

### Task 2: Add index filling instructions to llc-step-10.md

**Files:**
- Modify: `docs/skills/llc-step-10.md`

- [ ] **Step 1: Add index filling sub-section after CLAUDE.md/AGENTS.md generation (section 4)**

Insert after the AGENTS.md description block (after the line about "Salve na **raiz do projeto**: `AGENTS.md`."), before the current section 5 (Validacao Cruzada):

```markdown

### 5. Preencha o Documentation Index no AGENTS.md

No `AGENTS.md` gerado, localize o placeholder `{{DOCS_INDEX}}` e substitua pelo indice
comprimido de todos os artefatos LLC existentes no projeto.

#### Regras de preenchimento

1. **Formato fixo por linha:** `directory | file (KEYWORDS) | step | depends_on`
2. **KEYWORDS:** 3-5 palavras-chave em ingles, uppercase, que o agente encontrara
   em suas tarefas. Ex: `(STACK, C4, ADRS, SEGURANCA)` para ARCHITECTURE.md.
3. **step:** O step LLC que gerou o artefato. Ex: `Step 5`.
4. **depends_on:** Artefatos que este depende (nomes curtos, separados por virgula).
   Ex: `prd_tecnico, rnf`. Se nao depende de nenhum, use `-`.
5. **So inclua artefatos que EXISTEM.** Se um spec nao foi gerado, nao o liste.
6. **PRPs usam wildcard:** `PRP-*.md` — nao liste PRPs individuais.
7. **Ordem:** Agrupe por diretorio, mesma ordem do pipeline (Step 0 → Step 10.5).
8. **Diretorio:** Use caminho relativo a raiz do projeto. Ex: `docs/business/specs/`.

#### Template de saida (preencha apenas as linhas cujos artefatos existem)

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

```

- [ ] **Step 2: Renumber existing sections 5 and 6**

The old section "5. Validacao Cruzada" becomes "6. Validacao Cruzada". Update its heading:

```markdown
### 6. Validacao Cruzada
```

- [ ] **Step 3: Update the saida esperada section to include documentation index check**

After item 4 in the saida esperada (around line 302), add item 5:

```markdown
5. **Documentation Index:** O indice comprimido foi preenchido no AGENTS.md?
   Todas as keywords cobrem os dominios do projeto? Algum artefato existente ficou de fora?
```

And renumber the existing item 5 to 6:

```markdown
6. **Consistencia:** Todos os comandos do README funcionam com os scripts do projeto?
```

- [ ] **Step 4: Commit**

```bash
git add docs/skills/llc-step-10.md
git commit -m "feat: add compressed Documentation Index filling to llc-step-10"
```
