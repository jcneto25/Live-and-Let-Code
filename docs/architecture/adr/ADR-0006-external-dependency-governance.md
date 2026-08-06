# ADR-0006: Governança de Dependências Externas

**Arquivo:** `docs/architecture/adr/ADR-0006-external-dependency-governance.md`

```yaml
---
adr: "0006"
title: "Governança de Dependências Externas"
status: accepted
date: 2026-08-05
last_updated: 2026-08-05
deciders:
  - jcneto25
supersedes: null
related:
  - ADR-0002   # Wizard usa textual (Nível 1)
  - ADR-0004   # Graph é Python puro (Nível 0)
  - ADR-0005   # Evals usa tiktoken opcional (Nível 1)
referenced_by:
  - ADR-0002
  - ADR-0004
  - ADR-0005
tags: [governance, dependencies, licensing, sbom, bus-factor, risk-management, graceful-degradation]
compliance:
  fitness_functions: [dependency-governance]
  gates: [dependency-admission]
implementation_status:
  T1_dependencies_yaml: pending
  T2_retro_classify: pending
  T3_fitness_function: pending
  T4_amend_adrs: partial   # ADR-0002 já referencia; ADR-0004/0005 pendentes
  T5_review_date: pending
---
```

> **Motivação imediata:** este ADR nasce da reavaliação crítica do roadmap de fábrica agentica, que expôs que dependências externas (ex.: Herdr) estavam sendo adotadas sem análise formal de licença, bus factor e degradação. O caso Herdr é emblemático: pré-1.0 (v0.8.0), bus factor 1, e **licença alterada recentemente**. Sem governança, cada ADR que integra uma ferramenta externa reintroduz análise de risco ad-hoc e inconsistente.

---

## 1. Contexto

### 1.1 Situação Atual

O LLC evolui para incorporar capacidades que podem exigir dependências externas: UI rica (Textual), visibilidade multi-agente (possivelmente Herdr), instrumentação de tokens (possivelmente tiktoken). Até agora, cada decisão de dependência foi tomada **caso a caso, sem política formal**, gerando três riscos concretos já observados:

1. **Risco de licença:** a filosofia do LLC é MIT + tool-agnostic. Uma dependência com copyleft forte (GPL/AGPL) pode impor obrigações incompatíveis com a distribuição MIT. O caso Herdr demonstrou que **licenças mudam** — era necessário verificar a licença no momento exato da integração.
2. **Risco de bus factor:** uma dependência mantida por uma única pessoa pode ser descontinuada ou quebrar API sem aviso, comprometendo funcionalidades do LLC que dela dependam.
3. **Risco de acoplamento:** uma dependência no caminho crítico do harness transforma uma falha externa em falha do LLC.

### 1.2 O Princípio-Guia (herdado da proposta de evolução)

> *"Nenhuma ferramenta externa entra na camada de Fat Code (`.ace/scripts/`) ou no Thin Harness sem que sua ausência degrade graciosamente. O LLC continua funcionando via CLI puro (`llc run --step N`) mesmo se toda ferramenta de UI/runtime for removida."*

Este ADR formaliza esse princípio em política aplicável e verificável.

### 1.3 Forças em Jogo

| Força | Direção |
|---|---|
| **Filosofia MIT + tool-agnostic** | Dependências devem ser compatíveis e removíveis |
| **Terminal-first, single-user** | Evitar plataformas/serviços pesados |
| **Evolução necessária** | Algumas capacidades exigem dependências externas |
| **Previsibilidade** | Licenças, APIs e mantenedores mudam ao longo do tempo |
| **Baixa burocracia** | O processo não pode inviabilizar adoção de ferramentas úteis |

### 1.4 Escopo

Este ADR define a **política de governança** aplicável a toda dependência externa do LLC — bibliotecas, ferramentas binárias, ou serviços. Não avalia dependências específicas (isso é feito nos ADRs que as introduzem), mas estabelece **os critérios que qualquer dependência deve satisfazer**.

> **Aviso:** esta política orienta decisões técnicas, mas **não substitui consulta jurídica formal** em casos de dúvida sobre licenciamento.

---

## 2. Decisão

Estabelecer uma política de governança de dependências externas baseada em **classificação por nível de acoplamento**, **critérios obrigatórios de admissão**, **registro central (SBOM-like)**, e **revisão periódica**. Nenhuma dependência é integrada sem satisfazer os critérios do seu nível.

### 2.1 Princípios (não negociáveis)

| # | Princípio |
|---|---|
| **P1** | **Degradação graciosa obrigatória** — o LLC via CLI puro funciona sem qualquer dependência externa |
| **P2** | **Licença verificada na fonte** — nunca assumida; verificada no momento da integração |
| **P3** | **Nenhum `latest`** — toda dependência tem versão pinada |
| **P4** | **Bus factor conhecido e registrado** — dependências de mantenedor único são experimentais |
| **P5** | **Registro único** — toda dependência vive em `.ace/config/dependencies.yaml` |
| **P6** | **Revisão contínua** — licenças, versões e mantenedores mudam; revisão periódica obrigatória |
| **P7** | **Caminho crítico livre** — nenhuma dependência externa no caminho crítico do harness |

### 2.2 Classificação por Nível de Acoplamento

Toda dependência é classificada em um de quatro níveis, que determinam o rigor das salvaguardas:

| Nível | Descrição | Exemplo | Rigor |
|---|---|---|---|
| **N0** | Python stdlib, sem dependência externa | `json`, `asyncio` | Nenhum |
| **N1** | Biblioteca Python importada e distribuída | `textual`, `click`, `pyyaml` | Licença permissiva obrigatória |
| **N2** | Ferramenta externa invocada (binário/socket), **não distribuída** | `herdr`, `git` | Salvaguardas completas + fallback |
| **N3** | Serviço/plataforma externa (SaaS, servidor) | Temporal, SaaS de eval | **Bloqueado no caminho crítico**; apenas opcional |

**Regra de localização:**
- **Fat Code (`.ace/scripts/`):** apenas **N0** e **N1**.
- **Skills e UI/runtime:** **N2** permitido, com feature detection e fallback.
- **N3:** nunca no caminho crítico; apenas como integração opcional e removível.

### 2.3 Critérios Obrigatórios de Admissão (Gate de Admissão)

Nenhuma dependência **N1 ou superior** é integrada sem passar por este checklist:

```
☐ 1. Nível de acoplamento determinado (N0–N3)
☐ 2. Licença identificada na fonte oficial (não assumida)
☐ 3. Licença compatível com o nível (ver §2.4)
☐ 4. Bus factor documentado
☐ 5. Versão pinada (nunca latest)
☐ 6. Degradação graciosa definida E testada
☐ 7. Fallback documentado
☐ 8. Registrada em dependencies.yaml
☐ 9. Data de próxima revisão definida
☐ 10. Se bus_factor=1 ou pré-1.0 → marcada como experimental
```

### 2.4 Política de Licenciamento

A compatibilidade de licença depende do **nível de acoplamento** (distribuição vs. invocação):

| Categoria | Licenças | N1 (distribuída) | N2 (invocada) |
|---|---|---|---|
| **Permissivas** | MIT, Apache-2.0, BSD-2/3, ISC, Unlicense | ✅ Permitida | ✅ Permitida |
| **Copyleft fraco** | LGPL, MPL-2.0, EPL | ⚠️ Avaliar caso a caso | ✅ Geralmente OK |
| **Copyleft forte** | GPL-2/3, AGPL-3.0 | ❌ Bloqueada | ⚠️ Tolerável* |
| **Proprietária/restritiva** | — | ❌ Bloqueada | ❌ Bloqueada |

> \* **Nuança jurídica crítica:** uma dependência **AGPL/GPL pode ser usada como N2** (ferramenta externa que o usuário instala separadamente e o LLC apenas invoca), porque o LLC **não a distribui nem a linka**. Mas **não pode ser N1** (biblioteca importada e distribuída com o LLC). Essa distinção é central — foi exatamente o risco levantado no caso Herdr antes do seu relicenciamento para Apache-2.0.

**Regra de verificação contínua (P6):** licenças **mudam**. A licença registrada em `dependencies.yaml` deve ser **re-verificada em cada revisão periódica**, e qualquer mudança de licença dispara **reavaliação imediata** (ver §2.7).

### 2.5 Bus Factor e Saúde do Projeto

| Bus Factor | Tratamento |
|---|---|
| Comunidade ativa / múltiplos mantenedores | Tratamento padrão |
| **1 mantenedor principal** | Marcada **experimental**; fallback obrigatório; nunca no caminho crítico |
| Projeto **pré-1.0** (API instável) | Atenção redobrada; pin rigoroso; expectativa de adaptação |

**Regra:** dependências com `bus_factor=1` **ou** pré-1.0 devem ser marcadas `experimental: true` e acompanhadas de instrução explícita de fallback no catálogo de skills.

### 2.6 Degradação Graciosa (o requisito central)

Para toda dependência **N1+**, deve existir e ser **testado** um caminho de degradação:

- **Feature detection:** o código detecta se a dependência está presente antes de usá-la.
- **Fallback funcional:** na ausência da dependência, o LLC degrada para comportamento equivalente via CLI puro ou mecanismo alternativo.
- **Teste de remoção:** há um teste que simula a ausência da dependência e asserta que o LLC continua funcional.

Exemplo (Textual no Wizard, ADR-0002): se `textual` não está instalado, `llc wizard` exibe mensagem amigável e `llc run`/`llc pipeline` continuam funcionando.

### 2.7 Registro Central e Revisão Periódica

**Registro único:** `.ace/config/dependencies.yaml` (ver Anexo 8.1) — um SBOM simplificado com nome, versão pinada, nível, licença, bus factor, propósito, fallback, e data de revisão.

**Revisão periódica:** trimestral (configurável via `review_interval_days`). Cada revisão verifica:
- Licença mudou?
- Versão ainda suportada / há vulnerabilidades conhecidas?
- Bus factor mudou (mantenedor desistiu)?
- API quebrou em versão nova?

**Gatilhos de reavaliação imediata** (não esperam a revisão trimestral):
- Mudança de licença da dependência.
- Anúncio de descontinuação.
- Quebra de API usada pelo LLC.
- Vulnerabilidade de segurança crítica.

### 2.8 Decisões Vinculantes

| # | Decisão | Valor |
|---|---|---|
| **D1** | Classificação de acoplamento | N0–N3, determinando rigor das salvaguardas |
| **D2** | Licença para dependência distribuída (N1) | Permissiva obrigatória (MIT/Apache/BSD/ISC) |
| **D3** | Verificação de licença | Na fonte oficial, no momento da integração **e** em cada revisão |
| **D4** | Bus factor | Documentado; `=1` ou pré-1.0 ⇒ experimental + fallback obrigatório |
| **D5** | Versionamento | Pin obrigatório; nunca `latest` |
| **D6** | Degradação graciosa | Obrigatória e testada para toda dependência N1+ |
| **D7** | Registro central | `.ace/config/dependencies.yaml` único |
| **D8** | Revisão | Trimestral + gatilhos de reavaliação imediata |
| **D9** | Caminho crítico | Nenhuma dependência externa no caminho crítico do harness |
| **D10** | Localização | N0/N1 em `.ace/scripts/`; N2 em skills/UI com feature detection; N3 nunca no crítico |

---

## 3. Consequências

### 3.1 Positivas

- **Proteção contra lock-in e descontinuação:** dependências são removíveis por construção.
- **Segurança jurídica:** licenças verificadas e compatíveis com a distribuição MIT.
- **Previsibilidade:** versões pinadas e revisões periódicas evitam surpresas.
- **Transparência:** `dependencies.yaml` dá visão única de todas as dependências.
- **Resiliência:** degradação graciosa garante que falha externa ≠ falha do LLC.

### 3.2 Negativas / Custos

- **Overhead de processo:** cada nova dependência exige passar pelo checklist.
- **Possível desincentivo:** ferramentas úteis podem ser descartadas por rigor excessivo.
- **Manutenção do registro:** `dependencies.yaml` e revisões exigem disciplina contínua.

### 3.3 Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Burocratização excessiva | Checklist enxuto (10 itens); N0 isento |
| Licença muda após admissão | Revisão periódica + gatilhos de reavaliação imediata |
| Fallback não testado apodrece | Teste de remoção obrigatório no gate de admissão |
| Dependência N2 vira crítica inadvertidamente | Fitness function valida que caminho crítico não importa N2 |
| Registro desatualizado | Fitness function checa `dependencies.yaml` vs. imports reais |

---

## 4. Alternativas Consideradas

| Alternativa | Descrição | Motivo da Rejeição |
|---|---|---|
| **Sem política (status quo)** | Decidir caso a caso | Reintroduz risco ad-hoc; inconsistente |
| **Política apenas de licença** | Verificar só licença | Ignora bus factor, degradação e versionamento |
| **Banir todas dependências externas** | Apenas stdlib | Inviabiliza capacidades legítimas (TUI, instrumentação) |
| **Adotar apenas ferramentas "maduras"** | Critério subjetivo de maturidade | "Stars" ≠ maturidade de API; não é verificável |
| **Deixar para análise jurídica no fim** | Verificar licença só antes do release | Tarde demais; acoplamento já criado |

---

## 5. Compliance

### 5.1 Fitness Function — `dependency-governance`

Um novo check em `fitness-functions.py` valida:
- Toda dependência importada em `.ace/scripts/` está registrada em `dependencies.yaml`.
- Nenhuma dependência usa `latest` (todas pinadas).
- Toda dependência tem licença registrada.
- Nenhuma dependência tem revisão expirada (`last_reviewed` + `review_interval_days` < hoje).
- Nenhuma dependência N2/N3 é importada no caminho crítico do harness.

### 5.2 Gate de Admissão de Dependência

Novo gate humano: qualquer ADR ou PR que introduz dependência **N1+** deve apresentar o checklist de admissão (§2.3) preenchido e o registro em `dependencies.yaml`.

### 5.3 Relação com Outros ADRs

| ADR | Dependência | Nível | Ação |
|---|---|---|---|
| ADR-0002 (Wizard) | `textual` | N1 | Registrar; degradação já existe (fallback CLI) |
| ADR-0004 (Graph) | Python puro | N0 | Isento |
| ADR-0005 (Evals) | `tiktoken` (opcional) | N1 | Registrar; fallback por estimativa |
| ADR-0003 (Herdr, futuro) | `herdr` | N2 | Sujeito a todas salvaguardas; experimental |

---

## 6. Plano de Adoção

> **Problema identificado na revisão:** o plano original listava passos sem tasks rastreáveis, sem responsável e sem DoD. Isso tornava a política advisory sem enforcement real. A versão abaixo transforma cada passo em uma task executável com DoD verificável.

| # | Task | DoD verificável | Bloqueia |
|---|------|----------------|---------|
| **T1** | Criar `.ace/config/dependencies.yaml` com dependências atuais (`click`, `pyyaml`, `textual`) classificadas por nível, licença e bus factor | Arquivo existe; todas as 3 dependências com campos obrigatórios preenchidos; `textual` com `fallback` documentado | T3 |
| **T2** | Retro-classificar dependências existentes ausentes do yaml (verificar `requirements.txt` e imports em `.ace/scripts/`) | Nenhuma dependência importada em `.ace/scripts/` sem entrada em `dependencies.yaml` | T3 |
| **T3** | Implementar fitness function `dependency-governance` em `fitness-functions.py` | `fitness-functions.py --check dependency-governance` passa sem erros; falha intencionalmente quando dependência sem registro é adicionada (teste de regressão) | T4 |
| **T4** | Emendar ADR-0002, ADR-0004, ADR-0005 com referência a este ADR nos pontos de dependência | Cada ADR menciona ADR-0006 no frontmatter `related` e no ponto onde a dependência é introduzida | — |
| **T5** | Definir primeira data de revisão trimestral em `dependencies.yaml` (`last_reviewed` + `review_interval_days: 90`) | Campo `review_interval_days` presente; `last_reviewed` = data de criação do arquivo | — |

**Prioridade de execução:** T1 → T2 → T3 (bloqueio em série). T4 e T5 podem rodar em paralelo após T1.

**Critério de "ADR-0006 operacional":** T1, T2 e T3 concluídos. A política só tem dentes quando `fitness-functions.py` a enforça automaticamente.

---

## 7. Métricas de Sucesso

| Métrica | Meta |
|---|---|
| Dependências registradas em `dependencies.yaml` | 100% |
| Dependências com `latest` | 0 |
| Dependências sem licença registrada | 0 |
| Revisões trimestrais em dia | 100% |
| Testes de degradação (remoção) por dependência N1+ | 100% |

---

## 8. Anexos

### 8.1 Template — `.ace/config/dependencies.yaml`

```yaml
version: 1
updated_at: "2026-08-05"
review_interval_days: 90

dependencies:
  - name: textual
    version: ">=0.80.0,<1.0"
    level: 1                       # biblioteca Python distribuída
    license: MIT
    bus_factor: community
    purpose: "TUI do Wizard (ADR-0002)"
    critical_path: false
    fallback: "CLI puro llc run/pipeline"
    last_reviewed: "2026-08-05"

  - name: herdr
    version: "0.8.0"               # pinada, nunca latest
    level: 2                       # ferramenta externa, não distribuída
    license: Apache-2.0
    license_note: "Relicenciado de AGPL p/ Apache-2.0 em 2026-07-22 — re-verificar"
    bus_factor: 1
    experimental: true             # bus_factor=1 E pré-1.0
    purpose: "Visibilidade multi-agente (ADR-0003, se adotado)"
    critical_path: false
    fallback: "Worktrees + CLI puro"
    last_reviewed: "2026-08-05"
```

### 8.2 Exemplo de Avaliação — Herdr (sob esta política)

| Critério | Avaliação | Resultado |
|---|---|---|
| Licença | Apache-2.0 (desde 22/jul/2026) | ✅ N2-permitida, mas registrar a mudança |
| Bus factor | 1 mantenedor principal | ⚠️ Experimental + fallback obrigatório |
| Versão | v0.8.0 (pré-1.0) | ⚠️ Pin rigoroso, expectativa de quebra |
| Nível | N2 (ferramenta externa) | ✅ Apenas em skill de visualização |
| Degradação | Wave executa via CLI puro sem Herdr | ✅ OK |
| **Veredito** | — | **Aceitável como skill experimental de visualização; inaceitável no runtime crítico** |

### 8.3 Exemplo de Avaliação — Textual (sob esta política)

| Critério | Avaliação | Resultado |
|---|---|---|
| Licença | MIT | ✅ N1-permitida |
| Bus factor | Comunidade ativa | ✅ Padrão |
| Versão | Estável, pin em requirements | ✅ OK |
| Nível | N1 (biblioteca) | ✅ Permitida |
| Degradação | Wizard não carrega; CLI funciona | ✅ OK |
| **Veredito** | — | **Aceitável** |

---

## 9. Registro de Aprovação

| Decisor | Papel | Data |
|---|---|---|
| jcneto25 | Owner / Arquiteto | 2026-08-05 |
| claude | Co-autor da especificação | 2026-08-05 |

**Status:** `accepted`
**Aplica-se a:** ADR-0002, ADR-0004, ADR-0005 (retroativo) e qualquer ADR futuro que introduza dependência externa.
**Próximo passo sugerido:** Popular `.ace/config/dependencies.yaml` com as dependências atuais e emendar os ADRs 0002/0004/0005 para referenciar este ADR.

---

Este ADR está pronto para commit em `docs/architecture/adr/ADR-0006-external-dependency-governance.md`.

Com ele, fechamos o ciclo identificado na reavaliação: os ADRs 0002/0004/0005 têm núcleo técnico saudável, e o ADR-0006 fornece a **camada de governança** que faltava para qualquer dependência externa — formalizando exatamente as salvaguardas (licença, bus factor, pinning, degradação graciosa) que a análise crítica exigiu.

Quer que eu agora:
1. ✏️ **Gere o `dependencies.yaml` populado** com as dependências atuais do LLC (click, textual, pyyaml, tiktoken) já classificados?
2. 📋 **Produza o checklist de admissão como template** (`DEPENDENCY_ADMISSION_CHECKLIST.md`) para uso em futuros ADRs?
3. 🔧 **Especifique a fitness function `dependency-governance`** em tasks TDD granulares?
