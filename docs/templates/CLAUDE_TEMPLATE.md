---
template_version: "1.0.0"
template_name: "CLAUDE.md (LLC-Ready)"
last_updated: "{{TODAY}}"
project_name: "{{PROJECT_NAME}}"
project_type: "{{PROJECT_TYPE}}"
primary_language: "{{PRIMARY_LANGUAGE}}"
framework: "{{FRAMEWORK}}"
---

<!-- @include AGENTS.md -->

# {{PROJECT_NAME}}

> **Propósito:** {{ONE_LINE_DESCRIPTION}}

<!--
GUIA DE PREENCHIMENTO (LLC):
- Este arquivo é gerado pelo Step 10 do pipeline LLC e mantido pelo Step 4 a cada onda.
- Substitua todos os {{PLACEHOLDERS}}.
- Remova seções [OPCIONAL] se não se aplicarem.
- Atualize SEMPRE que arquitetura ou regras de domínio mudarem significativamente.
- O @include AGENTS.md na linha acima carrega regras compartilhadas entre agentes (se existir).
-->

## 📋 Project Overview

**{{PROJECT_NAME}}** é {{PROJECT_DESCRIPTION}}.

**Stack Principal:**
- **Frontend:** {{FRONTEND_STACK}}
- **Backend:** {{BACKEND_STACK}}
- **Mobile:** {{MOBILE_STACK}} [OPCIONAL]
- **Database:** {{DATABASE}}
- **ORM/Query Builder:** {{ORM}}
- **Infraestrutura:** {{INFRA}}

**Estrutura do Repositório:**
```text
{{REPO_STRUCTURE}}
```

## 🧠 Key Domain Concepts

### {{CONCEPT_1_NAME}}
{{CONCEPT_1_DESCRIPTION}}

### {{CONCEPT_2_NAME}}
{{CONCEPT_2_DESCRIPTION}}

### {{CONCEPT_3_NAME}}
{{CONCEPT_3_DESCRIPTION}}

## 🚀 Common Commands

```bash
{{ROOT_COMMANDS}}
```

### {{APP_1_NAME}} (`{{APP_1_PATH}}`)
```bash
cd {{APP_1_PATH}}
{{APP_1_COMMANDS}}
```

### {{APP_2_NAME}} (`{{APP_2_PATH}}`) [OPCIONAL]
```bash
cd {{APP_2_PATH}}
{{APP_2_COMMANDS}}
```

## 🔍 Code Search & Navigation

### Estratégia de Busca

**Opção A: Grafo de Código (Recomendado para projetos >1000 arquivos)**
- Claude Code: `semantic_search_nodes_tool`, `query_graph_tool`, `get_impact_radius_tool`
- Aider: tree-sitter indexing automático
- Cursor: codebase indexing nativo
- **Regra:** Consulte o grafo antes de escanear diretórios.

**Opção B: Repo Map (Para projetos médios)**
Consulte `.repo-map.md` ou equivalente antes de explorar.

**Opção C: Busca Direta (Fallback)**
Use `grep`/`find` apenas quando o grafo não cobrir o necessário.

## 🏗️ Architecture

### Visão Geral
```mermaid
{{ARCHITECTURE_DIAGRAM}}
```

### {{APP_1_NAME}} Architecture
**Framework:** {{APP_1_FRAMEWORK}}
**Padrão:** {{APP_1_PATTERN}}

**Estrutura:**
```text
{{APP_1_STRUCTURE}}
```

**Padrões Importantes:**
{{APP_1_PATTERNS}}

## 💾 Database Schema

**ORM:** {{ORM}}
**Total de Entidades:** {{ENTITY_COUNT}}

### Entidades Core
{{CORE_ENTITIES}}

### Relacionamentos Importantes
{{KEY_RELATIONSHIPS}}

### Padrões de Database
{{DATABASE_PATTERNS}}

## 🛠️ Development Notes

### Environment Variables
**Arquivo:** `{{ENV_FILE_PATH}}`
```bash
{{ENV_VARS_EXAMPLE}}
```

### Seed Data [OPCIONAL]
```bash
{{SEED_COMMANDS}}
```

### Test-Driven Development (TDD)
Este projeto segue TDD:
1. Escreva o teste PRIMEIRO.
2. Rode e veja falhar (red).
3. Implemente código mínimo para passar (green).
4. Refatore se necessário (refactor).

**Localização de Testes:** Co-localizados com código de produção.
**Factories:** Use factories de `test-helpers/factories/`. NUNCA use valores hardcoded.

## ⚠️ Important Constraints

{{CONSTRAINTS}}

**Restrições LLC adicionais:**
- Antes de refatorar código que afete múltiplos módulos, execute `python .ace/scripts/impact-analyzer.py --json` para verificar o impacto em artefatos downstream (PRDs, PRPs, arquitetura).
- Toda alteração em `docs/` deve ser registrada via ACE (append ao arquivo de sessão em `.ace/sessions/`).

## 🔄 CI/CD

### Workflows Principais
{{CI_WORKFLOWS}}

### Rodando CI Localmente
```bash
{{LOCAL_CI_COMMANDS}}
```

### Code Health Check
A cada onda de execução, monitore métricas estruturais:
```bash
python .ace/scripts/code-health.py --since "30 days ago" --strict
```
Se alertas críticos forem disparados (Moved Code < 10%), agende onda de refatoração.

### Detecção de Schema Drift
⚠️ O CI falhará se você modificar o schema sem migration.
```bash
cd {{APP_1_PATH}}
npx {{ORM}} migrate dev --name describe_your_changes
```

## 📚 References

Artefatos LLC gerados pelo pipeline (mantidos atualizados automaticamente):

| Artefato | Local | Atualizado por |
|----------|-------|---------------|
| Visão Estratégica | `docs/business/specs/visao_estrategica.md` | Step 0.5 |
| Requisitos Funcionais | `docs/business/specs/requisitos_funcionais.md` | Step 1 |
| PRD Técnico | `docs/prd/PRD_tecnico_institucional.md` | Step 2 |
| PRPs | `docs/prps/PRP-*.md` | Step 3 |
| Matriz de Dependências | `docs/planning/DEPENDENCY_MATRIX.md` | Step 4 |
| Arquitetura | `docs/architecture/ARCHITECTURE.md` | Step 5 |
| TASKS.md | `docs/planning/TASKS.md` | Step 6 |
| Design System | `docs/design/DESIGN_SYSTEM.md` | Step 7 |
| Guia de Testes | `docs/testing/TESTING_GUIDE.md` | Step 9 |
| DEPLOYMENT.md | `docs/DEPLOYMENT.md` | Step 10 |

## 🎯 Agent Instructions (ACE Integration)

### ✅ O que o agente DEVE fazer
1. **Consultar o Grafo:** Usar ferramentas de grafo de código antes de filesystem scanning.
2. **Seguir TDD:** Escrever testes antes da implementação.
3. **Respeitar Restrições:** Filtrar queries por tenant ID e respeitar soft delete.
4. **Usar ACE:** Iniciar sessão com `python .ace/scripts/initialize_session.py --step N --task "..." --json`. Internalizar `context_seed`. Appendar `<action>`, `<thinking>`, `<task_completed>` durante a sessão.
5. **Atualizar este Arquivo:** Se descobrir mudança arquitetural significativa, atualizar este `CLAUDE.md`.
6. **Verificar Impacto:** Antes de refatorar cross-module, rodar `python .ace/scripts/impact-analyzer.py`.

### ❌ O que o agente NUNCA DEVE fazer
1. Hard delete de entidades com soft delete.
2. Modificar logs de auditoria (append-only).
3. Usar `any` indiscriminadamente.
4. Modificar schema sem migration correspondente.
5. Reescrever arquivos `.ace/sessions/` existentes (apenas append).
6. Pular `context_seed` da sessão anterior.

### 🔄 Workflow Recomendado para Novas Features
1. Entender a tarefa e consultar grafo de código.
2. Executar `python .ace/scripts/impact-analyzer.py` para verificar impacto.
3. Escrever teste (TDD).
4. Implementar código mínimo.
5. Rodar testes localmente.
6. Registrar ação no ACE: `<action type="file_modify"><file_delta>src/...</file_delta></action>`.
7. Commit com mensagem convencional.

---

## 📝 Changelog

| Data | Versão | Mudança | Autor |
|------|--------|---------|-------|
| {{TODAY}} | 1.0.0 | Versão inicial gerada pelo pipeline LLC (Step 10) | {{AUTHOR}} |

---
**Nota:** Este arquivo é gerado e mantido pelo pipeline LLC. É consumido por agentes de IA e humanos. Atualizações significativas na arquitetura ou regras de domínio devem ser refletidas aqui e nos artefatos LLC correspondentes.
