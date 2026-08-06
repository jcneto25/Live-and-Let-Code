# PRP: [GOV-T1] — Criar `.ace/config/dependencies.yaml` (SBOM inicial)

> **ID:** PRP-GOV-T1 | **Trilha:** Governança | **Onda:** 0
> **Owner:** jcneto25 | **Estimativa:** 0,5 dia | **Status:** ✅ Done (2026-08-05)
> **Prioridade:** Crítico — bloqueia todas as trilhas
> **ADR de origem:** ADR-0006 §6 Task T1

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O ADR-0006 (Governança de Dependências) foi aceito, mas a política só tem dentes quando o registro central existe. Sem o `dependencies.yaml`, a fitness function `dependency-governance` (PRP-GOV-T3) não pode ser implementada, e qualquer nova dependência continua sendo adotada sem critério formal. Este PRP cria o artefato fundacional da governança.

### 1.2 O que é entregue

- [ ] `.ace/config/dependencies.yaml` criado com estrutura SBOM-like
- [ ] `click`, `pyyaml`, `textual`, `tiktoken` classificados com todos os campos obrigatórios
- [ ] `textual` com fallback documentado e `last_reviewed` preenchido
- [ ] Template do arquivo usável para futuras adições

### 1.3 O que NÃO está no escopo

- ❌ Retro-classificar imports não listados no `requirements.txt` → PRP-GOV-T2
- ❌ Implementar a fitness function → PRP-GOV-T3

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação | Prioridade | Status |
|----|-----------|----------------------|------------|--------|
| RF-GOV1.1 | `dependencies.yaml` criado em `.ace/config/` | Arquivo existe e é YAML válido | Must | ⏳ |
| RF-GOV1.2 | `textual` registrado como N1 com fallback | `level: 1`, `license: MIT`, `fallback` preenchido | Must | ⏳ |
| RF-GOV1.3 | `click` e `pyyaml` registrados como N1 | `level: 1`, licenças corretas | Must | ⏳ |
| RF-GOV1.4 | `tiktoken` registrado como N1 opcional | `level: 1`, `experimental: false`, fallback = "estimativa por contagem" | Must | ⏳ |
| RF-GOV1.5 | Todos os campos obrigatórios preenchidos | checklist de admissão §2.3 do ADR-0006 satisfeito por entrada | Must | ⏳ |
| RF-GOV1.6 | `review_interval_days: 90` definido | Revisão trimestral configurada | Must | ⏳ |

---

## 3. Artefato Entregue

```yaml
# .ace/config/dependencies.yaml
version: 1
updated_at: "2026-08-05"
review_interval_days: 90

dependencies:
  - name: click
    version: ">=8.0,<9.0"
    level: 1
    license: BSD-3-Clause
    bus_factor: community
    purpose: "CLI framework do llc.py e llc_wizard"
    critical_path: true
    fallback: "N/A — click é o backbone do CLI; remover exigiria reescrever o CLI"
    last_reviewed: "2026-08-05"
    next_review: "2026-11-05"

  - name: pyyaml
    version: ">=6.0,<7.0"
    level: 1
    license: MIT
    bus_factor: community
    purpose: "Leitura de dependency-graph.yaml e gates.json"
    critical_path: false
    fallback: "json stdlib para configs simples; yaml apenas para artefatos declarativos"
    last_reviewed: "2026-08-05"
    next_review: "2026-11-05"

  - name: textual
    version: ">=0.80.0,<1.0"
    level: 1
    license: MIT
    bus_factor: community
    purpose: "TUI do Wizard (ADR-0002)"
    critical_path: false
    fallback: "CLI puro llc run/pipeline — Wizard não carrega mas harness funciona"
    degradation_test: "test_select_runner_falls_back_when_no_agent (PRP-WIZARD-1A Task 3.4)"
    last_reviewed: "2026-08-05"
    next_review: "2026-11-05"
    notes: "0.x — API instável; pin rigoroso obrigatório"

  - name: tiktoken
    version: ">=0.7.0,<1.0"
    level: 1
    license: MIT
    bus_factor: community
    purpose: "Fallback nível 3 para estimativa de tokens (ADR-0005 §2.5)"
    critical_path: false
    optional: true
    fallback: "Estimativa por contagem de palavras × fator heurístico (nível 3 degradado)"
    last_reviewed: "2026-08-05"
    next_review: "2026-11-05"
```

---

## 4. Dependências

### 4.1 Bloqueado por
- ADR-0006 aceito ✅

### 4.2 Desbloqueia
- PRP-GOV-T2 (retro-classificação)
- PRP-GOV-T3 (fitness function — lê este arquivo)

---

## 5. Definition of Done

- [ ] `.ace/config/dependencies.yaml` existe e é YAML válido (`python -c "import yaml; yaml.safe_load(open('.ace/config/dependencies.yaml'))"`)
- [ ] 4 dependências registradas com todos os campos obrigatórios (nível, licença, bus_factor, fallback, last_reviewed)
- [ ] `textual` tem `degradation_test` apontando para o teste do PRP-WIZARD-1A
- [ ] Sessão ACE registrada para esta task
