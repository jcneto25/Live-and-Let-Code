---
name: llc-impact-analyzer
description: Analisa impacto de alterações via git diff e reporta quais artefatos LLC precisam ser revisados em cascata, com sugestão de skills a re-executar.
version: 1.0.0
tags: [impact, traceability, consistency, llc-pipeline]
---

# LLC Skill: Impact Analyzer

Detecta alterações no projeto e propaga o impacto através do grafo de dependências entre artefatos LLC, reportando exatamente quais documentos precisam ser revisados e em qual ordem.

## Quando usar

- Após alterar qualquer artefato LLC (visão, specs, PRDs, PRPs, arquitetura, design system...)
- Antes de commits que envolvam mudanças na documentação
- Como parte do pre-commit hook (automático)
- Para responder: "mudei X, o que mais preciso atualizar?"

## Como funciona

```
git diff --name-only → cruza com .ace/dependency-graph.yaml → propaga impacto em cascata
```

O grafo de dependências mapeia cada artefato LLC: o que o originou (`depends_on`) e o que ele impacta quando alterado (`triggers_update`). A propagação é recursiva até os artefatos terminais.

## Uso

### Análise de arquivos não commitados

```
python .ace/scripts/impact-analyzer.py --json
```

### Análise de arquivos staged

```
python .ace/scripts/impact-analyzer.py --staged --json
```

### Análise de arquivos específicos

```
python .ace/scripts/impact-analyzer.py --files "docs/business/specs/glossario.md,docs/prd/executive_PRD.md" --json
```

### Com sugestão de skills

```
python .ace/scripts/impact-analyzer.py --staged --json --skills
```

A saída JSON inclui `suggested_skills` com os skills LLC que devem ser re-executados, em ordem.

## Integração com Pre-Commit Hook

Adicione ao `.ace/scripts/pre-commit.sh`:

```bash
# Análise de impacto (informativo — não bloqueia)
echo ""
echo "📊 Analisando impacto nos artefatos LLC..."
python .ace/scripts/impact-analyzer.py --staged --json 2>/dev/null || true
```

## Exemplo de Saída

```json
{
  "changed_files": ["docs/business/specs/perfis_permissoes.md"],
  "directly_affected": [
    {"file": "docs/business/specs/perfis_permissoes.md", "artifact_id": "perfis_permissoes", "artifact_path": "docs/business/specs/perfis_permissoes.md"}
  ],
  "cascade_impact": [
    {"id": "prd_tecnico", "path": "docs/prd/PRD_tecnico_institucional.md", "triggered_by": "perfis_permissoes", "depth": 2},
    {"id": "design_system", "path": "docs/design/DESIGN_SYSTEM.md", "triggered_by": "perfis_permissoes", "depth": 2},
    {"id": "deployment", "path": "docs/DEPLOYMENT.md", "triggered_by": "perfis_permissoes", "depth": 2},
    {"id": "prps", "path_pattern": "docs/prps/PRP-*.md", "triggered_by": "prd_tecnico", "depth": 3},
    {"id": "architecture", "path": "docs/architecture/ARCHITECTURE.md", "triggered_by": "prd_tecnico", "depth": 3}
  ],
  "total_artifacts_to_review": 6,
  "suggested_skills": ["llc-step-2", "llc-step-3", "llc-step-5", "llc-step-7", "llc-step-10"]
}
```

Interpretação: alterar `perfis_permissoes.md` impacta 6 artefatos em cascata. Re-execute os skills na ordem sugerida.

## Manutenção do Grafo

O grafo é atualizado automaticamente pelo Step 4 (`llc-step-4`). Se novos artefatos forem adicionados ao pipeline, o skill DEVE atualizar `.ace/dependency-graph.yaml` ao gerar `DEPENDENCY_MATRIX.md`.
