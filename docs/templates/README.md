# docs/templates/README.md
# Templates do Pipeline LLC

Este diretório contém templates com exemplos reais usados no pipeline LLC.

## 📁 Templates Disponíveis

| Template | Descrição | Quando Usar |
|----------|-----------|-------------|
| `PRP_TEMPLATE_EXEMPLO.md` | Exemplo completo de PRP preenchido | Guia para criar novos PRPs |
| `TASKS_EXEMPLO.md` | Exemplo de arquivo de tarefas | Referência para step 6 |
| `EXECUTION_WAVES_EXEMPLO.md` | Exemplo de ondas de execução | Referência para step 4 |
| `dependency-graph-exemplo.yaml` | Exemplo funcional do dependency graph | Referência para ACE |

## 📖 Como Usar Estes Templates

1. **PRP TEMPLATE**: Copie o formato e preencha com as especificações do seu PRP
2. **TASKS**: Use como guia para organizar tarefas por PRP
3. **EXECUTION WAVES**: Use para agrupar PRPs em ondas lógicas
4. **DEPENDENCY GRAPH**: Use como referência para configurar rastreabilidade

## 🔗 Relacionamento com o Pipeline

```
Step 0.5 → Visão Estratégica → Usa PRP TEMPLATE como base
Step 3     → PRPs             → Preenche PRP_TEMPLATE_EXEMPLO
Step 4     → Planejamento     → Gera EXECUTION_WAVES_EXEMPLO
Step 6     → Tarefas          → Gera TASKS_EXEMPLO
```

## 📝 Notas

- Todos os templates são **exemplos** e devem ser adaptados ao seu projeto
- Use o `dependency-graph-exemplo.yaml` para entender dependências entre artefatos
- A estrutura de diretórios deve seguir a convenção LLC
