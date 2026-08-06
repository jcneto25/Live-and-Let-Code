# PRP: [GOV-T2] — Retro-classificar dependências existentes em `.ace/scripts/`

> **ID:** PRP-GOV-T2 | **Trilha:** Governança | **Onda:** 0
> **Owner:** jcneto25 | **Estimativa:** 0,5 dia | **Status:** ✅ Done (2026-08-05)
> **Prioridade:** Crítico | **ADR de origem:** ADR-0006 §6 Task T2

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O `dependencies.yaml` do PRP-GOV-T1 cobre as dependências explícitas já conhecidas. Mas `.ace/scripts/` pode ter imports adicionais (diretos ou transitivos) não listados em `requirements.txt`. Sem varrer os imports reais, a fitness function `dependency-governance` pode ter falsos negativos — dependências usadas mas não registradas.

### 1.2 O que é entregue

- [ ] Inventário completo de todos os imports de terceiros em `.ace/scripts/`
- [ ] `dependencies.yaml` atualizado com quaisquer dependências ausentes encontradas
- [ ] Confirmação explícita de que nenhum import não-stdlib está sem registro

### 1.3 O que NÃO está no escopo

- ❌ Implementar a fitness function → PRP-GOV-T3
- ❌ Adicionar novas dependências não existentes

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação | Prioridade | Status |
|----|-----------|----------------------|------------|--------|
| RF-GOV2.1 | Varrer todos os imports em `.ace/scripts/**/*.py` | Script ou verificação manual identifica todos os módulos não-stdlib | Must | ⏳ |
| RF-GOV2.2 | Toda dependência não-stdlib registrada em `dependencies.yaml` | Zero imports sem entrada no yaml | Must | ⏳ |
| RF-GOV2.3 | Dependências stdlib explicitamente excluídas (N0) | Lista de módulos stdlib confirmados como N0 documentada | Should | ⏳ |

---

## 3. Método de Varredura

```bash
# Listar todos os imports de terceiros (não-stdlib) em .ace/scripts/
python -c "
import ast, sys, sysconfig
from pathlib import Path

stdlib = set(sys.stdlib_module_names)
third_party = set()

for f in Path('.ace/scripts').rglob('*.py'):
    try:
        tree = ast.parse(f.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [n.name for n in node.names] if isinstance(node, ast.Import) \
                        else ([node.module] if node.module else [])
                for name in names:
                    root = name.split('.')[0]
                    if root and root not in stdlib:
                        third_party.add(root)
    except Exception:
        pass

for m in sorted(third_party):
    print(m)
"
```

---

## 4. Dependências

### 4.1 Bloqueado por
- PRP-GOV-T1 ✅ (yaml base criado)

### 4.2 Desbloqueia
- PRP-GOV-T3

---

## 5. Definition of Done

- [ ] Varredura executada e resultado documentado na sessão ACE
- [ ] `dependencies.yaml` atualizado com quaisquer imports encontrados não cobertos pelo PRP-GOV-T1
- [ ] Confirmação explícita: "zero imports não-stdlib sem registro"
- [ ] Sessão ACE registrada com lista de módulos encontrados
