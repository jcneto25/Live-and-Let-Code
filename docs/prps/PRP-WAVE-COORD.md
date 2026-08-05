# PRP: [WAVE-COORD] — `wave_coordinator.py` (Sugestão Reativa, Estritamente Sugestivo)

> **ID:** PRP-WAVE-COORD | **Trilha:** Wave Coordinator | **Onda:** 4
> **Owner:** jcneto25 | **Estimativa:** 1 semana | **Status:** 🔒 Condicional
> **Prioridade:** Condicional | **ADR de origem:** `factory-evolution.md` §5

---

## ⚠️ Gate de Entrada (não iniciar sem evidência)

**Este PRP só deve ser iniciado quando:**
- ≥ 3 sessões ACE documentam retrabalho causado por `DEPENDENCY_MATRIX.md` estático
- O retrabalho é especificamente: PRP iniciado mas bloqueado por dep que mudou mid-wave

Sem essa evidência registrada, este PRP é otimização prematura.

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O `DEPENDENCY_MATRIX.md` é gerado uma vez no Step 4 e é estático. Quando dependências mudam no meio de uma wave (PRP Amendment, Smart Skip em cascata), o operador não tem visibilidade de quais PRPs foram desbloqueados. O `wave_coordinator.py` resolve isso com polling simples — **nunca executa, apenas sugere**.

### 1.2 O que é entregue

- [ ] `.ace/scripts/wave_coordinator.py` — polling de `index.json` + sugestão textual
- [ ] Lê `parallel_frontier()` do `GraphEngine` para identificar PRPs recém-desbloqueados
- [ ] Escreve sugestão em `docs/planning/EXECUTION_WAVES.md §próxima ação`
- [ ] Nunca invoca `llc run`, `initialize_session`, worktree ou qualquer agente

### 1.3 O que NÃO está no escopo (CRÍTICO)

- ❌ Invocar execução de qualquer tipo
- ❌ Modificar `.ace/index.json` ou sessões ACE
- ❌ Aprovar gates automaticamente
- ❌ Criar worktrees

---

## 2. Requisitos Funcionais (todos com teste de contrato)

| ID | Requisito | Como testar | Prioridade | Status |
|----|-----------|-------------|------------|--------|
| RF-WC.1 | Nunca invoca execução | Mock de `llc run`, `initialize_session`, `subprocess` → asserta zero chamadas | Must | ⏳ |
| RF-WC.2 | Única saída é sugestão textual em `EXECUTION_WAVES.md §próxima ação` | Asserta nenhum outro arquivo modificado | Must | ⏳ |
| RF-WC.3 | Não muta `.ace/index.json` nem sessões | Snapshot antes/depois → idêntico | Must | ⏳ |
| RF-WC.4 | Degrada graciosamente se `DEPENDENCY_MATRIX.md` ausente | Loga e sai sem crash | Must | ⏳ |
| RF-WC.5 | Decisão de iniciar PRP permanece humana | Revisão: ausência de auto-aprovação no código | Must | ⏳ |

---

## 3. Comportamento Esperado

```
[wave_coordinator] PRP-042 desbloqueado (deps: PRP-038 ✅, PRP-040 ✅)
[wave_coordinator] Sugestão adicionada em EXECUTION_WAVES.md §próxima ação
[wave_coordinator] → Aguardando decisão humana para iniciar PRP-042
```

---

## 4. Dependências

### Bloqueado por
- PRP-GRAPH-2A (`parallel_frontier()`)
- Gate de entrada: evidência em sessões ACE

### Desbloqueia
- Coordenação reativa sem infraestrutura pesada

---

## 5. Definition of Done

- [ ] Todos os 5 contratos com testes verdes
- [ ] Zero chamadas a funções de execução (RF-WC.1 — crítico)
- [ ] Única escrita em `EXECUTION_WAVES.md` (RF-WC.2)
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Evidência do gate de entrada documentada na sessão ACE que inicia o PRP
