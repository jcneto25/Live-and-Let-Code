# PRP: [WIZARD-1C] — Artifact Review + Scope Confirmation + Rerun

> **ID:** PRP-WIZARD-1C | **Trilha:** Wizard | **Onda:** 1
> **Owner:** jcneto25 | **Estimativa:** 2 semanas | **Status:** ✅ Done (2026-08-06)
> **Prioridade:** Médio | **ADR de origem:** ADR-0002 §2.4

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com PRP-WIZARD-1B, o Wizard suporta perguntas e waivers durante execução. Este PRP adiciona as duas categorias HITL restantes mais complexas: Artifact Review (humano revisa artefato gerado e pode rejeitar com feedback) e Scope Confirmation (humano confirma ou restringe escopo antes do step iniciar). Ambas fecham o ciclo HITL completo descrito no ADR-0002 §2.4.

### 1.2 O que é entregue

- [x] `ReviewArtifactCommand` — apresenta artefato no painel, aguarda aprovação/rejeição com feedback
- [x] `ConfirmScopeCommand` — apresenta escopo proposto, bloqueia início até confirmação
- [x] Rerun automático — quando gate rejeitado, Wizard oferece re-execução do step sem sair da TUI
- [x] `FailureRecoveryScreen` completa (iniciada no 1A como stub)

### 1.3 O que NÃO está no escopo

- ❌ Kanban UI → PRP-WIZARD-1.1
- ❌ Integração com `EfficiencyScore` do Eval Harness no painel de review → PRP-WIZARD-1.1

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação (Gherkin) | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|--------------------------------|------------|--------|----------|-----------------|
| RF-W1C.1 | Artifact Review apresenta conteúdo do artefato no painel | **Dado** `ReviewArtifactCommand`, **Quando** executado, **Então** conteúdo do artefato visível no output panel | Must | ✅ | `test_app.py` | `llc_wizard/app.py` |
| RF-W1C.2 | Rejeição com feedback persiste `<user_response type="artifact_review">` | **Dado** review rejeitada com feedback, **Quando** `execute()`, **Então** tag XML com `approved="false"` e itens de feedback | Must | ✅ | `test_decisions.py`, `test_commands.py` | `llc_wizard/decisions.py` |
| RF-W1C.3 | Scope Confirmation bloqueia início do step | **Dado** `ConfirmScopeCommand` pendente, **Quando** step tenta iniciar, **Então** step aguarda confirmação | Must | ✅ | `test_app.py` | `llc_wizard/app.py` |
| RF-W1C.4 | Rerun automático após rejeição de gate | **Dado** gate rejeitado na `FailureRecoveryScreen`, **Quando** usuário seleciona "re-executar", **Então** step reinicia sem sair da TUI | Must | ✅ | `test_app.py` | `llc_wizard/screens/failure_recovery.py` |
| RF-W1C.5 | `FailureRecoveryScreen` oferece opções: re-executar, pular, encerrar | **Dado** tela de recovery aberta, **Quando** renderizada, **Então** 3 opções visíveis com atalhos de teclado | Must | ✅ | `test_app.py` | `llc_wizard/screens/failure_recovery.py` |

---

## 3. Dependências

### Bloqueado por
- PRP-WIZARD-1B

### Desbloqueia
- Wizard HITL completo (feature parity com CLI puro)

---

## 4. Definition of Done

- [x] Todos os 5 RF com testes verdes (incluindo FTDD para cada estado visual)
- [x] `ReviewArtifactCommand` e `ConfirmScopeCommand` implementados
- [x] Rerun automático funcional sem perda de estado ACE
- [x] `fitness-functions.py --all --strict` verde
- [x] Sessão ACE registrada

---

## 5. Execução (2026-08-06)

### O que foi entregue

| Componente | Conteúdo |
|-----------|----------|
| `screens/failure_recovery.py` (novo) | `FailureRecoveryScreen` real — 3 opções `[r] re-executar / [s] pular / [q] encerrar` via `action_for(key)` (RF-W1C.4/5); o 1A tinha apenas o nome no `_screen_stack` |
| `decisions.py` | `ArtifactReview.approved: bool` + `feedback: list[str]`; `submit_artifact_review` grava `approved="true|false"` + `<feedback>` itens (RF-W1C.2) — append-only preservado |
| `commands.py` | `ReviewArtifactCommand.validate()` — rejeição exige ≥1 feedback (auditabilidade, ADR-0002 §2.4) |
| `app.py` | `show_artifact_review()` no `#output-panel` (RF-W1C.1); `set_pending_scope`/`confirm_scope`/`can_start_step` (RF-W1C.3); `reject_gate` cria a tela real; `rerun_step()` desempilha recovery e re-executa (RF-W1C.4) |
| 8 novos testes | 2 decisions + 2 commands + 4 app (FTDD por estado) |

### Verificação
- llc_wizard suite **72 passed** · cobertura **TOTAL 97%** (screens 100%, decisions 100%)
- Full suite **488 passed** · fitness **`--all --strict` 41/41**
- Guarda AGENTS.md (sessões imutáveis) mantida: `test_wizard_does_not_write_to_sessions_dir` verde com o novo módulo `screens/`

### Compatibilidade 1A
`reject_gate()` continua empilhando `"FailureRecoveryScreen"` no `_screen_stack` (contrato do SPEC 6.1 do 1A) — agora junto ao objeto real em `_recovery_screens[step_id]`. Zero quebra nos testes do 1A.
