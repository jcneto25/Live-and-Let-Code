# PRP: [HERDR-SKILL] — Skill `llc-wave-observability.md` + Feature Detection

> **ID:** PRP-HERDR-SKILL | **Trilha:** Herdr / Visibilidade Multi-Agente | **Onda:** 4
> **Owner:** jcneto25 | **Estimativa:** 2 semanas | **Status:** 🔒 Condicional
> **Prioridade:** Condicional | **ADR de origem:** `factory-evolution.md` §4; ADR-0006 §8.2

---

## ⚠️ Gate de Entrada (não iniciar sem evidência)

**Este PRP só deve ser iniciado quando:**
- ≥ 4 semanas de uso da Fase 1 (Wizard MVP)
- Sessões ACE documentam dor específica: múltiplos PRPs de uma wave executados em terminais separados sem coordenação visual
- ADR-0006 checklist de admissão preenchido para a ferramenta escolhida (licença, bus factor, fallback)

Sem essa evidência, este PRP é a Fase 2 condicional que pode não ser necessária.

---

## 1. Contexto e Objetivo

### 1.1 Por que este PRP existe?

O paralelismo via worktrees já existe. O gap é visibilidade: quando 3 PRPs rodam simultaneamente em worktrees, o operador não tem uma lente consolidada sobre o que cada pane está fazendo. Esta skill adiciona visualização sobre o paralelismo existente — não cria novo paralelismo.

**A ferramenta externa é uma lente, não um orquestrador.**

### 1.2 O que é entregue

- [ ] `docs/skills/llc-wave-observability.md` — skill opcional de visualização
- [ ] Feature detection: skill verifica se a ferramenta está instalada antes de qualquer uso
- [ ] Fallback documentado e testado: sem a ferramenta, workflow continua via CLI puro
- [ ] Socket API tolerante a falha (timeout + fallback se API não responde)
- [ ] Gate humano permanece em `finalize_session.py` — nunca delegado à ferramenta externa

### 1.3 O que NÃO está no escopo

- ❌ A ferramenta externa em si (usuário instala separadamente)
- ❌ Gates humanos delegados à ferramenta
- ❌ Modificar o harness existente

---

## 2. Requisitos Funcionais

| ID | Requisito | Critério de Aceitação | Prioridade | Status |
|----|-----------|----------------------|------------|--------|
| RF-HS.1 | Feature detection antes de qualquer uso | **Dado** ferramenta não instalada, **Quando** skill executada, **Então** degradação graciosa com mensagem de instalação | Must | ⏳ |
| RF-HS.2 | Socket API com timeout e fallback | **Dado** ferramenta instalada mas API não responde, **Quando** timeout N segundos, **Então** degrada para visualização passiva | Must | ⏳ |
| RF-HS.3 | Gate humano permanece em `finalize_session.py` | **Dado** skill ativa, **Quando** gate pendente, **Então** `<gate_result>` escrito exclusivamente por `finalize_session.py` | Must | ⏳ |
| RF-HS.4 | `llc run` sem ferramenta = comportamento idêntico ao atual | **Dado** ferramenta removida, **Quando** `llc run --step N`, **Então** pipeline funciona sem diferença | Must | ⏳ |

---

## 3. Pré-condições (ADR-0006)

Antes de criar este PRP, o checklist de admissão deve estar preenchido para a ferramenta escolhida:

```
☑ Nível de acoplamento determinado (N2 — ferramenta externa, não distribuída)
☑ Licença verificada na fonte oficial
☑ Licença compatível com N2
☑ Bus factor documentado
☑ Versão pinada em dependencies.yaml
☑ Degradação graciosa definida E testada (RF-HS.1, RF-HS.4)
☑ Fallback documentado
☑ Registrada em dependencies.yaml
☑ Data de revisão definida
☑ Se bus_factor=1 → marcada como experimental
```

---

## 4. Dependências

### Bloqueado por
- PRP-GRAPH-2A (`parallel_frontier()` como fonte de dados para visualização)
- Gate de entrada: evidência em sessões ACE + ADR-0006 checklist preenchido

### Desbloqueia
- Visibilidade consolidada de PRPs paralelos

---

## 5. Definition of Done

- [ ] Todos os 4 RF com testes verdes
- [ ] Feature detection funcional (RF-HS.1)
- [ ] `llc run` sem ferramenta = comportamento idêntico (RF-HS.4 — regressão zero)
- [ ] ADR-0006 checklist preenchido e registrado na sessão ACE
- [ ] `fitness-functions.py --all --strict` verde
- [ ] Evidência do gate de entrada documentada na sessão ACE que inicia o PRP
