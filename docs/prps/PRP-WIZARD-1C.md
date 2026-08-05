# PRP: [WIZARD-1C] — Artifact Review + Scope Confirmation + Rerun

> **ID:** PRP-WIZARD-1C | **Trilha:** Wizard | **Onda:** 1
> **Owner:** jcneto25 | **Estimativa:** 2 semanas | **Status:** ⏳ Pending
> **Prioridade:** Médio | **ADR de origem:** ADR-0002 §2.4

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

Com PRP-WIZARD-1B, o Wizard suporta perguntas e waivers durante execução. Este PRP adiciona as duas categorias HITL restantes mais complexas: Artifact Review (humano revisa artefato gerado e pode rejeitar com feedback) e Scope Confirmation (humano confirma ou restringe escopo antes do step iniciar). Ambas fecham o ciclo HITL completo descrito no ADR-0002 §2.4.

### 1.2 O que é entregue

- [ ] `ReviewArtifactCommand` — apresenta artefato no painel, aguarda aprovação/rejeição com feedback
- [ ] `ConfirmScopeCommand` — apresenta escopo proposto, bloqueia início até confirmação
- [ ] Rerun automático — quando gate rejeitado, Wizard oferece re-execução do step sem sair da TUI
- [ ] `FailureRecoveryScreen` completa (iniciada no 1A como stub)

### 1.3 O que NÃO está no escopo

- ❌ Kanban UI → PRP-WIZARD-1.1
- ❌ Integração com `EfficiencyScore` do Eval Harness no painel de review → PRP-WIZARD-1.1

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação (Gherkin) | Prioridade | Status | Teste(s) | Arquivo(s) impl |
|----|-----------|--------------------------------|------------|--------|----------|-----------------|
| RF-W1C.1 | Artifact Review apresenta conteúdo do artefato no painel | **Dado** `ReviewArtifactCommand`, **Quando** executado, **Então** conteúdo do artefato visível no output panel | Must | ⏳ | `test_commands.py` | `llc_wizard/commands.py` |
| RF-W1C.2 | Rejeição com feedback persiste `<user_response type="artifact_review">` | **Dado** review rejeitada com feedback, **Quando** `execute()`, **Então** tag XML com `approved="false"` e itens de feedback | Must | ⏳ | `test_decisions.py` | `llc_wizard/decisions.py` |
| RF-W1C.3 | Scope Confirmation bloqueia início do step | **Dado** `ConfirmScopeCommand` pendente, **Quando** step tenta iniciar, **Então** step aguarda confirmação | Must | ⏳ | `test_commands.py` | `llc_wizard/commands.py` |
| RF-W1C.4 | Rerun automático após rejeição de gate | **Dado** gate rejeitado na `FailureRecoveryScreen`, **Quando** usuário seleciona "re-executar", **Então** step reinicia sem sair da TUI | Must | ⏳ | `test_app.py` | `llc_wizard/screens/failure_recovery.py` |
| RF-W1C.5 | `FailureRecoveryScreen` oferece opções: re-executar, pular, encerrar | **Dado** tela de recovery aberta, **Quando** renderizada, **Então** 3 opções visíveis com atalhos de teclado | Must | ⏳ | `test_app.py` | `llc_wizard/screens/failure_recovery.py` |

---

## 3. Dependências

### Bloqueado por
- PRP-WIZARD-1B

### Desbloqueia
- Wizard HITL completo (feature parity com CLI puro)

---

## 4. Definition of Done

- [ ] Todos os 5 RF com testes verdes (incluindo FTDD para cada estado visual)
- [ ] `ReviewArtifactCommand` e `ConfirmScopeCommand` implementados
- [ ] Rerun automático funcional sem perda de estado ACE
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Sessão ACE registrada
