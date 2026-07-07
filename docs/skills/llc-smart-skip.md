---
name: llc-smart-skip
description: Mecanismo transversal de Smart Skip para o fluxo delta. Cada skill condicional verifica no DELTA_REPORT.md se deve executar ou pular, reutilizando artefatos existentes quando possível.
version: 1.0.0
tags: [delta, smart-skip, transverse, llc-pipeline]
---

# LLC Skill: Smart Skip — Lógica de Skip Condicional no Fluxo Delta

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Transversal — Change Management  
**Quando usar:** Automático — embutido nos steps condicionais (0.5, 1, 2, 5, 7, 8, 9, 10.5) quando DELTA_REPORT.md está presente.  
**Mantenedor:** Equipe LLC

---

## O Problema

Em uma iteração de mudança (delta), nem todos os steps precisam ser reexecutados. Reescrever a arquitetura do zero quando nada mudou no stack é desperdício de tokens e tempo. No entanto, pular um step sem registro quebra a rastreabilidade do pipeline.

## A Solução

Cada step condicional incorpora uma verificação padronizada no início da execução. Se o DELTA_REPORT.md classificar o step como "skip", a skill produz um **Skip Note** — artefato leve que documenta a decisão e substitui o artefato completo.

---

## Protocolo de Smart Skip

### 1. Verificação

Ao ser invocada, a skill verifica:

```python
# Pseudocódigo da verificação
if os.path.exists("docs/planning/DELTA_REPORT.md"):
    report = read_delta_report()
    if step_id in report.skip_steps:
        return generate_skip_note(step_id, report.skip_steps[step_id].justification)
    elif step_id in report.execute_steps:
        return execute_normally()
```

### 2. Skip Note

Quando um step é pulado, a skill gera um arquivo de skip note em vez do artefato completo:

**Local:** `docs/delta/skip-notes/{step_id}.md`

**Conteúdo:**

```markdown
# Skip Note: Step {N} — {Nome do Step}

**Iteração:** v{Atual} → v{Nova}
**Data:** {YYYY-MM-DD}
**Decisão:** Step pulado conforme DELTA_REPORT.md §5.2

## Justificativa
{O motivo exato pelo qual este step não precisa ser reexecutado,
extraído do DELTA_REPORT.md}

## Artefatos Reaproveitados
- {artefato existente} — v{versão} (gate aprovado em {data})
- {artefato existente} — v{versão} (gate aprovado em {data})

## Gate
**Gate {N}:** ✅ Auto-aprovado via Smart Skip (reaproveitando artefatos da versão anterior)
**Referência:** Aprovação original em {data} por {revisor}
```

### 3. Gate Handling

| Situação | Comportamento |
|----------|--------------|
| **Skip com DELTA_REPORT.md** | Gate **auto-aprovado** com referência à aprovação anterior |
| **Skip sem DELTA_REPORT.md** | **Não aplicável** — Smart Skip só opera em modo delta |
| **Executar (na lista do DELTA_REPORT)** | Gate normal — validação humana obrigatória |
| **DELTA_REPORT.md não encontrado** | Modo padrão — gate normal |

### 4. Steps Condicionais e Suas Regras de Skip

| Step | Condição para Skip | O que é reaproveitado |
|------|-------------------|----------------------|
| **0.5** (Visão + Módulos) | DELTA_REPORT.md não lista alteração na visão ou módulos | `visao_estrategica_e_negocio.md` + `MOD-*.md` existentes |
| **1** (7 Especificações) | Nenhum spec (glossário, RF, RNF, RN, BPMN, perfis, integrações) é afetado | 7 specs existentes |
| **2** (PRDs) | Step 1 não foi executado (e DELTA_REPORT não lista PRDs como afetados) | `executive_PRD.md` + `PRD_tecnico_institucional.md` existentes |
| **5** (Arquitetura) | DELTA_REPORT.md não lista `architecture` como afetado | `ARCHITECTURE.md` existente |
| **7** (Design System) | DELTA_REPORT.md não lista `design_system` como afetado | `DESIGN_SYSTEM.md` existente |
| **8** (Setup + Mock) | Modelo de dados não mudou (schema/migrations inalterados) | `mocks/` existentes + projeto inicializado |
| **9** (Testing Docs) | Estratégia de testes inalterada (stack e ferramentas mantidas) | `TESTING_GUIDE.md`, `COVERAGE_BASELINE.md`, `COVERAGE_PROGRESS.md` existentes |
| **10.5** (User Guide) | UI inalterada (DELTA_REPORT.md não lista UI como afetada) | `docs/user-guide/` existente |

---

## ⚠️ Regras Críticas

1. **Skip não é esquecimento.** O skip note é um artefato versionado em git — a decisão de pular é tão rastreável quanto a decisão de executar.

2. **Auto-aprovação só com referência.** O gate auto-aprovado sempre referencia a aprovação original da versão anterior. Sem aprovação anterior, o gate é pendente e exige validação humana.

3. **Revisão de consistência.** Após todos os steps, o Step 11.2 (PRP Verify) deve verificar se os artefatos reaproveitados ainda são consistentes com os artefatos alterados. Se houver drift, o erro de skip deve ser corrigido.

4. **Threshold de correção.** Se durante a execução de um step subsequente for descoberto que um step pulado deveria ter sido executado, **interrompa e reexecute o step** antes de prosseguir. Registre como `<learning_point priority="high">` para ajustar o DELTA_REPORT.md.

---

## 📤 Saída Esperada

- **Se skip:** `docs/delta/skip-notes/{step_id}.md` com justificativa e referência de gate
- **Se executar:** Artefato normal do step + gate humano
