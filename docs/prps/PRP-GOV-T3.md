# PRP: [GOV-T3] — Fitness Function `dependency-governance` (TDD)

> **ID:** PRP-GOV-T3 | **Trilha:** Governança | **Onda:** 0
> **Owner:** jcneto25 | **Estimativa:** 1 dia | **Status:** ✅ Done (2026-08-05)
> **Prioridade:** Crítico | **ADR de origem:** ADR-0006 §5.1 + §6 Task T3

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O ADR-0006 define uma política, mas política sem enforcement automático é advisory. A fitness function `dependency-governance` é o mecanismo que torna a política vinculante: qualquer PR que adiciona uma dependência não registrada é bloqueado automaticamente pelo pre-commit. Sem ela, T1 e T2 são documentação; com ela, são contratos executáveis.

### 1.2 O que é entregue

- [ ] Check `dependency-governance` em `fitness-functions.py` (TDD — RED→GREEN→REFACTOR)
- [ ] 5 verificações implementadas conforme ADR-0006 §5.1
- [ ] Teste de regressão: falha intencionalmente quando dependência sem registro é detectada

### 1.3 O que NÃO está no escopo

- ❌ Modificar a lógica de outros checks existentes
- ❌ Integrar ao pre-commit hook (já existe; o check novo é chamado pelo hook existente)

---

## 2. Requisitos Funcionais (TDD)

| ID | Requisito | RED esperado | GREEN | Status |
|----|-----------|-------------|-------|--------|
| RF-GOV3.1 | Detecta import não registrado em `dependencies.yaml` | `AssertionError` / check retorna CRITICAL | Check passa após registro | ⏳ |
| RF-GOV3.2 | Detecta dependência sem versão pinada (`latest` ou sem pin) | Check retorna CRITICAL | Passa com versão pinada | ⏳ |
| RF-GOV3.3 | Detecta dependência sem licença registrada | Check retorna CRITICAL | Passa com licença preenchida | ⏳ |
| RF-GOV3.4 | Detecta revisão expirada (`last_reviewed` + 90d < hoje) | Check retorna WARN | Passa com `last_reviewed` atual | ⏳ |
| RF-GOV3.5 | Detecta dependência N2/N3 importada diretamente em `.ace/scripts/` (caminho crítico) | Check retorna CRITICAL | Passa quando N2 está apenas em skills/ | ⏳ |

---

## 3. Implementação (esqueleto TDD)

### 🔴 RED — testes primeiro

```python
# .ace/scripts/tests/test_fitness_dependency_governance.py
import pytest
from pathlib import Path
from fitness_functions.checks_governance import check_dependency_governance

def test_unregistered_import_returns_critical(tmp_path):
    """Dependência importada mas ausente do yaml → CRITICAL."""
    (tmp_path / "test_mod.py").write_text("import unregistered_lib\n")
    (tmp_path / "dependencies.yaml").write_text(
        "version: 1\ndependencies: []\n"
    )
    results = check_dependency_governance(tmp_path)
    assert any(r.severity == "CRITICAL" for r in results)

def test_dependency_without_pin_returns_critical(tmp_path):
    """Dependência com `version: latest` → CRITICAL."""
    ...

def test_expired_review_returns_warn(tmp_path):
    """Revisão expirada (> 90d) → WARN."""
    ...

def test_n2_in_scripts_returns_critical(tmp_path):
    """Import N2 em .ace/scripts/ (não em skills/) → CRITICAL."""
    ...

def test_clean_yaml_passes(tmp_path):
    """Yaml completo e atualizado → nenhum CRITICAL."""
    ...
```

### 🟢 GREEN — implementação mínima

```python
# .ace/scripts/fitness_functions/checks_governance.py
from pathlib import Path
from datetime import datetime, timedelta
import yaml, ast, sys

def check_dependency_governance(root: Path) -> list:
    results = []
    yaml_path = root / ".ace" / "config" / "dependencies.yaml"
    if not yaml_path.exists():
        results.append(Result("CRITICAL", "dependencies.yaml não encontrado"))
        return results

    config = yaml.safe_load(yaml_path.read_text())
    registered = {d["name"] for d in config.get("dependencies", [])}
    # ... 5 verificações conforme RF-GOV3.1–3.5
    return results
```

---

## 4. Dependências

### 4.1 Bloqueado por
- PRP-GOV-T2 (yaml completo e auditado)

### 4.2 Desbloqueia
- Todas as trilhas — a política está operacional

---

## 5. Definition of Done

- [x] `fitness-functions.py --check-governance` passa sem erros no repositório atual ✅ (2026-08-05)
- [x] Teste de regressão RED: adicionar import não registrado → check retorna CRITICAL ✅ (verificado com `unregistered_lib_xyz`)
- [x] Todos os 5 RFs com testes verdes ✅ (15 testes em `test_fitness_dependency_governance.py`)
- [x] `fitness-functions.py --all --strict` continua passando ✅ (40/41 — único alerta é `module_coverage` pré-existente, sem arquivo de cobertura)
- [x] Sessão ACE registrada ✅ (2026-08-05-011)

> **Nota de implementação (2026-08-05):** a flag real é `--check-governance` (o CLI do
> fitness-functions usa flags específicas por check — não há `--check <nome>` genérico).
> Escopo da varredura: `.ace/scripts/**/*.py` exceto `test_*.py` (governança de produção;
> `pytest` registrado como dev em GOV-T2). Núcleo testável em
> `checks_governance._check_dependency_governance(root)`.
