# Exemplo de Consistency Config — Comentado

## Estrutura Básica

```yaml
# Mapeamento de PRP → arquivos de serviço implementados
prp_services:
  PRP-001:
    - src/auth/auth.service.ts
    - src/usuarios/usuarios.service.ts
  PRP-002:
    - src/perfis/perfis.service.ts

# Padrões para ignorar tarefas (UI, testes, etc.)
skip_task_patterns:
  - "Tela"
  - "Componente"
  - "Testes"

# Padrões de stub por linguagem
stub_patterns:
  any:
    - "TODO"
    - "NotImplemented"
  typescript:
    - "return Promise.resolve([])"
  python:
    - "raise NotImplementedError"
```

## Explicação dos Campos

### prp_services
Mapeia cada PRP para os arquivos de serviço que devem ser implementados:
- O `consistency-check.py` lê o TASKS.md para encontrar tarefas marcadas como ✅
- Para cada PRP com tarefas concluídas, verifica se os arquivos listados são stubs
- Se o arquivo não existir ou for detectado como stub → **divergência**

### skip_task_patterns
Regex patterns para ignorar tarefas que não exigem implementação de serviço:
- "Tela" — tarefas de frontend UI
- "Componente" — componentes React/Vue/etc.
- "Testes" — testes automatizados
- "E2E" — testes end-to-end
- "Seed" — seeds de banco de dados
- "Docs" — documentação

### stub_patterns
Patterns específicos por linguagem para detectar stubs:

| Linguagem | Exemplo de Stub |
|-----------|-----------------|
| TypeScript | `return Promise.resolve([])` |
| Python | `raise NotImplementedError` |
| Go | `return nil, nil` |
| Rust | `todo!()` |

Patterns disponíveis:
- `any`: aplicados a todas as linguagens
- `typescript`, `python`, `go`, `rust`, etc.: específicos por linguagem

### custom_patterns
Patterns adicionais específicos do projeto (regex globais).

## Gerar Configuração Automaticamente

```bash
# Executar este comando após completar o Step 5 (Arquitetura)
python .ace/scripts/consistency-check.py --update-config
```

Isso extrai o mapeamento da seção 6.5 do `ARCHITECTURE.md` e gera o arquivo `.ace/consistency-config.yaml`.

## Validação

```bash
# Verificar consistência (visual)
python .ace/scripts/consistency-check.py

# Verificar consistência (JSON)
python .ace/scripts/consistency-check.py --json

# Bloquear se houver divergências (CI/CD)
python .ace/scripts/consistency-check.py --strict
```

## Exemplo de Saída

```
============================================================
📋 VERIFICAÇÃO DE CONSISTÊNCIA — TASKS.md vs Código
============================================================
PRPs com tarefas concluídas analisados: 3
Services implementados: 4
Services stub: 1
Divergências: 1

❌ DIVERGÊNCIAS ENCONTRADAS:

  [PRP-001] src/auth/auth.service.ts
         Tarefa marcada T-001 como ✅ mas código é stub

============================================================
```

## Troubleshooting

### "Nenhum mapeamento encontrado"

1. Execute `llc run --step 5 --task "Arquitetura"`
2. Preencha a seção 6.5 do `ARCHITECTURE.md` com o mapeamento
3. Execute `python .ace/scripts/consistency-check.py --update-config`

### Falso positivo

Adicione o padrão no `skip_task_patterns` ou ajuste o `stub_patterns`:
```yaml
skip_task_patterns:
  - "Meu Padrão Personalizado"
```
