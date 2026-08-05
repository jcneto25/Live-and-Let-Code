---
name: llc-step-11-4-governance-conversion
description: Pipeline LLC — Governance Conversion. Revisa falhas estruturais da wave, classifica falhas como locais ou estruturais, registra GOVs, e promove mecanismos de governança (lints, fitness functions, skills, ADRs).
version: 1.0.0
tags: [governance, conversion, structural-failure, gov, llc-pipeline]
---

# LLC Skill: Step 11.4 — Governance Conversion

**Pipeline:** Live and Let Code (LLC)
**Fase:** Pós-Implementação / Pré-Deploy
**Depende de:** Step 11.3 (Arch Fitness) aprovado
**Mantenedor:** Equipe LLC

## Como usar esta Skill

1. Coloque este arquivo em `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-11-4-governance-conversion` ou "Execute a skill llc-step-11-4-governance-conversion".
3. Execute APÓS o Step 11.3 (Arch Fitness) e ANTES do deploy.

> **Nota:** Esta skill descreve a cerimônia de revisão do step 11.4. GOVs individuais podem ser abertos durante toda a execução (qualquer operador pode registrar uma falha estrutural). O step 11.4 é o momento de revisar, classificar e promover GOVs abertos.

## Pré-requisitos

- [ ] Step 11.3 (Arch Fitness) aprovado — Gate 11-ARCH verde
- [ ] Lista de PRPs concluídos na wave atual
- [ ] Sessões ACE da wave atual acessíveis em `.ace/sessions/`
- [ ] Diretório `docs/governance/` existe (com `GOV-TEMPLATE.md`)
- [ ] `python .ace/scripts/impact-analyzer.py` disponível
- [ ] `python .ace/scripts/gov-tools.py` disponível (comandos: list, impact, check-recurrence)
- [ ] `python .ace/scripts/governance-metrics.py` disponível (métricas: failure_to_control_lead_time, structural_failure_recurrence_rate)

---

## PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-11-4-governance-conversion` do pipeline LLC. Seu objetivo é revisar falhas estruturais ocorridas durante a wave, classificá-las, registrar artefatos GOV, e instalar mecanismos de governança para prevenir reincidência.

### 1. Levante as Falhas da Wave

- Obtenha a lista de PRPs concluídos na wave atual.
- Para cada PRP, examine as sessões ACE em `.ace/sessions/` em busca de:
  - `<blocker>` tags — impedimentos que ocorreram
  - `<action type="test_run">` com falha — testes que quebraram
  - `<gate_result decision="rejected">` — gates que foram rejeitados
  - `<learning_point priority="high">` — aprendizados consolidados
- Analise o diff da wave: `git log --oneline <base>..HEAD`
- Execute detecção de reincidência:
  ```bash
  python .ace/scripts/gov-tools.py check-recurrence
  ```
  GOVs addressed que reaparecem como blockers em sessões recentes são candidatos a revisão.

### 2. Classifique Cada Falha

Para cada incidente identificado, classifique como **Defeito Local** ou **Falha Estrutural**:

| Critério | Defeito Local | Falha Estrutural |
|----------|--------------|-------------------|
| Ocorrência | Isolada, um arquivo | Recorrente, múltiplos contextos |
| Causa | Erro de implementação | Abstração/controle ausente ou fraco |
| Prevenção | Ajuste pontual no prompt | Requer novo mecanismo de governança |
| Reincidência | Improvável | Provável se não tratada |

Se **Defeito Local**: registre como nota no PRP §11, sem GOV. Se **Falha Estrutural**: prossiga.

### 3. Registre o GOV

Antes de registrar, verifique GOVs existentes para evitar duplicatas:
```bash
python .ace/scripts/gov-tools.py list
python .ace/scripts/gov-tools.py list --status open
```

Para cada falha estrutural não registrada, crie um arquivo `docs/governance/GOV-NNN-<slug>.md`:

```bash
# Descubra o próximo número GOV
ls docs/governance/GOV-*.md 2>/dev/null | wc -l
# (incremente +1 para o novo GOV)
```

Use o template `docs/governance/GOV-TEMPLATE.md` como base.
Preencha todos os campos. Status inicial: **open**.

```xml
<action type="file_create">
  <file_delta>docs/governance/GOV-001-<slug>.md</file_delta>
  <description>Registro de falha estrutural: <classe></description>
</action>
```

### 4. Decida o Mecanismo de Resposta

Para cada GOV, decida o tipo de resposta:

| Resposta | Descrição | Exemplo | Exige ADR? |
|----------|-----------|---------|-----------|
| **Arquitetural** | Elimina a falha por construção | Modelo tipado, seam canônico, component catalog | Sim, se difícil de reverter |
| **Controle Probabilístico** | Orienta o agente sem garantia determinística | Skill update, novo padrão de briefing, template | Não |
| **Controle Determinístico** | Falha/bloqueia deterministicamente se violado | Lint, fitness function, pre-commit hook, gate | Sim, se alterar arquitetura |
| **Misto** | Combina arquitetura + controle | Modelo tipado + lint de violação | Sim |

**Critério de escolha:**
- Impacto **Alto** → meta é determinístico (ou misto)
- Impacto **Médio** → determinístico se viável, senão probabilístico
- Impacto **Baixo** → probabilístico é suficiente

### 5. Instale o Mecanismo

Dependendo da resposta escolhida:

- **Skill update**: edite `docs/skills/` — adicione orientação ou regra no skill relevante
- **Lint**: adicione regra em `.ace/config/arch-config.yaml` ou script de lint correspondente
- **Fitness function**: adicione teste em `fitness-functions.py` ou `.ace/config/arch-config.yaml`
- **Pre-commit hook**: atualize `.ace/scripts/pre-commit.sh`
- **ADR**: crie `docs/architecture/adr/NNNN-slug.md` (só se difícil de reverter)
- **Template update**: edite o template relevante em `docs/templates/`
- **Briefing pattern**: atualize `AGENTS.md` ou `CLAUDE.md`

Após instalar, valide:

```bash
# Se for fitness function
python .ace/scripts/fitness-functions.py --all --strict

# Se for lint
python .ace/scripts/pre-commit.sh --dry-run
```

### 6. Atualize o GOV

Transicione o GOV de **open** para **addressed**:

- Preencha o campo `Mecanismo Instalado`
- Preencha o campo `Validação Posterior` — como verificar se a reincidência foi reduzida
- Atualize `Status` para **addressed**
- Preencha `Data de instalação` com a data atual (YYYY-MM-DD) — necessário para o cálculo de `failure_to_control_lead_time`

```xml
<gate_result step="11.4" decision="addressed" reviewer="llc-step-11-4-governance-conversion">
  GOV-001: Falha estrutural <classe> convertida em <mecanismo>. Monitorando por 3 PRPs.
</gate_result>
```

### 7. Gere o Relatório de Governança

Execute as métricas automatizadas:
```bash
python .ace/scripts/governance-metrics.py
python .ace/scripts/governance-metrics.py --verbose --json
```

Use `gov-tools.py` para listar o status atual e avaliar transições:
```bash
python .ace/scripts/gov-tools.py list
python .ace/scripts/gov-tools.py list --status open
python .ace/scripts/gov-tools.py list --status addressed

# R5: addressed → closed exige 3 PRPs sem reincidência (check-recurrence)
python .ace/scripts/gov-tools.py close GOV-001-slug.md           # dry-run (elegibilidade)
python .ace/scripts/gov-tools.py close GOV-001-slug.md --confirm # aplica (decisão humana no gate)
```

Ao final, gere um resumo:

```markdown
## Relatório de Governance Conversion — Wave {N}

| GOV | Classe | Impacto | Resposta | Mecanismo | Status |
|-----|--------|---------|----------|-----------|--------|
| GOV-001 | <classe> | Alto | Arquitetural | Modelo tipado em src/X | addressed |
| GOV-002 | <classe> | Baixo | Probabilístico | Skill update llc-step-N | addressed |

**Métricas (via governance-metrics.py):**
- `failure_to_control_lead_time`: {X dias} — tempo médio entre detecção e instalação
- `structural_failure_recurrence_rate`: {X%} — % de GOVs com reincidência
- Total GOVs nesta wave: {N}
- Pendentes (open): {N}
```

---

## REGRAS CRÍTICAS

1. **GOV é imortal:** Nunca delete um arquivo GOV. Se o mecanismo for substituído, crie um novo GOV que referencie o anterior (`Supersedes: GOV-001`).

2. **Reabertura:** Se a mesma classe de falha reaparecer após GOV closed, reabra o GOV original (volta para addressed) e registre a reincidência. Se o mecanismo original se mostrou insuficiente, instale mecanismo complementar.

3. **ADR só quando necessário:** Só crie ADR se a decisão for (a) difícil de reverter, (b) surpreendente sem contexto, e (c) resultado de trade-off real. A maioria das respostas de controle não exige ADR.

4. **Não confundir GOV com PRP:** GOV registra a falha estrutural e o mecanismo. O PRP que implementa o mecanismo referencia o GOV, mas o GOV vive independentemente. Um PRP pode resolver múltiplos GOVs; um GOV pode gerar múltiplos PRPs.

5. **Autoridade de conversão:** Qualquer operador pode registrar um GOV (open). A instalação de mecanismos que alteram arquitetura, gates ou fitness functions (zona 🔴) exige validação humana em gate.

6. **Idempotência:** Re-execução desta skill é segura — GOVs já existentes não são recriados. A skill só cria GOVs para falhas ainda não registradas.

---

## SAÍDA ESPERADA

- Lista de falhas classificadas (local vs estrutural)
- GOVs criados para cada falha estrutural, status **open** → **addressed**
- Mecanismos instalados (lints, skills, fitness functions, ADRs)
- Relatório de governança da wave com métricas de `governance-metrics.py`
- `<gate_result step="11.4">` registrado na sessão
- Métricas registradas para `failure_to_control_lead_time` e `structural_failure_recurrence_rate`
- (Se aplicável) Reincidências detectadas via `gov-tools.py check-recurrence`

### Próximos Passos

- **Aprovado (GOVs addressed):** Prossiga para deploy da wave.
- **GOVs pendentes (open):** Podem ser diferidos para a próxima wave, mas devem ser registrados. Agende instalação na wave seguinte.
- **Falha estrutural sem mecanismo viável agora:** Deixe GOV como **open** e registre como blocker para a próxima iteração.
