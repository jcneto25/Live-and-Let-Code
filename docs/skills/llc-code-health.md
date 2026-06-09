---
name: llc-code-health
description: Monitora saúde estrutural do código — Moved Code, Copy/Paste, Legacy Touch. Previne degradação por agentes paralelos.
version: 1.0.0
tags: [code-health, metrics, refactoring, llc-pipeline]
---

# LLC Skill: Code Health (Saúde Estrutural)

Monitora métricas estruturais do código via git history para detectar degradação causada por agentes trabalhando em PRPs paralelos.

## Quando usar

- Checkpoint QA do Step 11 (obrigatório)
- Após cada onda de execução (Wave)
- Manualmente: `@llc-code-health`

## Métricas Monitoradas

| Métrica | Threshold | Severidade |
|---------|-----------|------------|
| **% Moved Code** | < 10% do total de alterações | 🔴 Crítico — perda estrutural de manutenibilidade |
| **Copy/Paste vs Moved** | Cópias > Movimentações | 🟡 Alto — duplicação superando reuso (viola DRY) |
| **% Legacy Code Touch** | < 20% das alterações em código > 30 dias | 🟡 Alto — código antigo sem refatoração |

## Uso

```
Execute a skill docs/skills/llc-code-health.md
```

Ou via script:

```
python .ace/scripts/code-health.py --since "30 days ago" --json
```

Com `--strict` para uso em CI/gates (exit code 1 se thresholds violados):

```
python .ace/scripts/code-health.py --since "90 days ago" --strict --json
```

## Ações Corretivas

Quando alertas são disparados:

1. **🔴 Moved Code < 10%:** Agendar onda de refatoração cross-PRP. Identificar blocos duplicados e consolidar em módulo compartilhado.
2. **🟡 Copy/Paste > Moved:** Revisar PRPs recentes — agentes estão duplicando em vez de abstrair. Verificar se falta um módulo compartilhado no planejamento.
3. **🟡 Legacy Touch < 20%:** Garantir que PRPs incluam tarefas de `file_modify` em código existente, não apenas `file_create`.
