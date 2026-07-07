# Evolução Contínua com IA: Como Gerenciar Mudanças em Sistemas Existentes com o Fluxo Delta do LLC

**Autor:** Equipe LLC  
**Data:** Julho de 2026  
**Tags:** #desenvolvimento-com-ia #workflows-agenticos #brownfield #metodologia #llc

---

## O Problema: O Que Acontece Quando o Sistema Já Existe?

Grande parte da literatura sobre desenvolvimento com IA foca em *greenfield* — começar um projeto do zero com a ajuda de agentes autônomos. O problema é que a realidade do desenvolvimento de software é outra: **sistemas existentes, código legado, mudanças incrementais**.

Quando sua equipe recebe um novo documento de regulamentação, uma solicitação de nova funcionalidade ou uma alteração em regras de negócio, o sistema já está rodando em produção. Recomeçar o pipeline inteiro do zero é ineficiente. Ignorar a metodologia e "só codar" é arriscado.

Entre 2024 e 2026, testemunhamos um padrão recorrente: times que adotam workflows agenticos para greenfield colapsam quando precisam evoluir o sistema. Os motivos são sempre os mesmos:

- **Reescrita desnecessária:** o agente regenera specs, arquitetura e design system inteiros, mesmo quando nada mudou
- **Perda de rastreabilidade:** mudanças são feitas diretamente no código sem atualizar a documentação
- **Regressão silenciosa:** o agente modifica código existente sem verificar se funcionalidades estáveis continuam funcionando
- **Cegueira contextual:** o agente não sabe o que já existe, então duplica ou conflita com o código atual

Foi para resolver exatamente isso que criamos o **Fluxo Delta** do Live and Let Code (LLC).

---

## A Ideia Central: Não Reescreva — Altere

O princípio fundamental do fluxo delta é simples:

> **Preserve o que não mudou. Documente apenas o que mudou. Execute apenas o que é necessário.**

Em vez de rodar o pipeline completo de 19 steps (14 principais + 5 auxiliares), o fluxo delta executa uma **análise de impacto** inicial que determina exatamente quais steps precisam ser reexecutados e quais podem ser reaproveitados da versão anterior.

O resultado é um pipeline adaptativo que:

1. **Analisa o delta** entre o sistema atual e os novos documentos
2. **Classifica** a mudança como MAJOR ou MINOR
3. **Pula steps inalterados** (Smart Skip) com documentação da decisão
4. **Gera PRPs de alteração** (PRP-A) em vez de PRPs inteiramente novos
5. **Garante não regressão** — testes existentes continuam passando

---

## Visão Geral do Fluxo

```
Sistema em produção (v1)
    │
    ├── Novos documentos de mudança chegam
    │
    ▼
┌─────────────────────────────────────┐
│         FASE DE ANÁLISE             │
│                                     │
│  Step Δ.0 — Delta Impact Analysis   │
│  → impact-analyzer.py --classify    │
│  → DELTA_REPORT.md (major/minor)    │
│  → Gate Δ.0 (validação humana)      │
│                                     │
│  Step Δ.1 — Grill Me de Mudança     │
│  → 8 perguntas focadas no delta     │
│  → Gate Δ.1 (validação humana)      │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│      FASE DE EXECUÇÃO ADAPTATIVA    │
│                                     │
│  Para cada step do pipeline:        │
│                                     │
│  Step inalterado? → ⏭️ Skip Note    │
│                      + gate auto-   │
│                        aprovado     │
│                                     │
│  Step afetado? → ✅ Executa em      │
│                   modo diff/addendum│
│                                     │
│  Step 3 (PRPs):                     │
│  ├── PRP-A-* para alterações        │
│  └── PRP-N-* para funcionalidades   │
│      novas                          │
│                                     │
│  Step 11 (Execução):                │
│  ├── TDD para modificar/criar/      │
│  │   remover/migrar                 │
│  └── Suite completa de regressão    │
└─────────────────────────────────────┘
    │
    ▼
  Deploy v2 🚀
```

---

## Mão na Massa: Exemplo Prático

Vamos supor que você tem um sistema de planejamento orçamentário em produção (v1) e recebe um novo documento: uma instrução normativa que exige um novo perfil de **auditor fiscal** e altera três regras de negócio.

### Pré-requisitos

O sistema já passou pelo pipeline LLC completo na v1. Você tem:
- Artefatos em `docs/` (visão, specs, PRDs, PRPs, arquitetura, design system)
- Código-fonte em `src/`
- Mocks em `mocks/`
- `.ace/dependency-graph.yaml` populado

### Passo 1: Coloque os novos documentos

```bash
cp instrucao_normativa_2026.pdf docs/business/ingestion/
```

### Passo 2: Converta para Markdown

```bash
python .ace/scripts/llc.py run --step 0.1
```

### Passo 3: Inicie o fluxo delta

```bash
python .ace/scripts/llc.py delta start --iteration v2
```

O Thin Harness executa automaticamente:

**Step Δ.0 — Delta Impact Analysis:**

```bash
python .ace/scripts/impact-analyzer.py --json --skills --classify
```

O analisador cruza `git diff` com o grafo de dependências, identifica que `perfis_permissoes.md` e `requisitos_funcionais.md` são afetados, classifica como **MAJOR** (afeta perfis), e gera `docs/planning/DELTA_REPORT.md`:

```
change_type: major
execute_steps: [0.5, 1, 2, 3, 4, 6, 10, 10.6, 10.7, 10.8, 11, 11.1]
skip_steps:
  - step_id: 5
    reason: Stack e ADRs mantidos
  - step_id: 7
    reason: Sem novos tokens ou componentes
  - step_id: 8
    reason: Modelo de dados inalterado
  - step_id: 9
    reason: Stack de teste inalterado
  - step_id: 10.5
    reason: Sem novas telas
```

**Gate Δ.0:** O humano valida o relatório e aprova.

**Step Δ.1 — Grill Me de Mudança:**

A IA faz perguntas focadas no delta:

> 🔴 O novo perfil "auditor fiscal" substitui ou complementa os perfis existentes?
> 🔴 As regras de negócio alteradas afetam contratos de API existentes?
> 🟡 Há breaking changes nos endpoints consumidos por integrações?

O usuário responde e a IA registra. Gate Δ.1 aprovado.

### Passo 4: Execute o pipeline adaptativo

```bash
python .ace/scripts/llc.py pipeline --delta --iteration v2
```

O que acontece em cada step:

| Step | O que ocorre | Tempo estimado |
|------|-------------|----------------|
| **0.5** (Visão) | Gera addendum: "novo perfil auditor" | 10 min |
| **1** (Specs) | Glossário +5 termos, RFs alterados, perfis expandidos | 30 min |
| **2** (PRDs) | PRDs v2 com seção "O que mudou" | 15 min |
| **3** (PRPs) | PRP-A-001 (altera PRP-003) e PRP-A-002 (altera PRP-007) | 40 min |
| **4** (Planejamento) | Matriz atualizada com PRPs-A | 10 min |
| **5** (Arquitetura) | ⏭️ PULADO — Skip note gerado | — |
| **6** (Tasks) | Tarefas de modificação + novas | 15 min |
| **7** (Design) | ⏭️ PULADO | — |
| **8** (Setup) | ⏭️ PULADO | — |
| **9** (Testing) | ⏭️ PULADO | — |
| **10** (Docs) | README, DEPLOYMENT, CLAUDE.md, AGENTS.md atualizados | 20 min |
| **10.5** (User Guide) | ⏭️ PULADO | — |
| **10.6-10.8** (Segurança) | SCA/SAST/secrets + null safety + coverage | 15 min |
| **11** (Execução) | PRP-A-001 e PRP-A-002 com TDD | 4 horas |
| **11.1** (OWASP) | Hardening pós-código | 20 min |
| **11.2** (PRP Verify) | Verificação mecânica — 0 CRITICAL | 5 min |

**Total estimado: ~7 horas** (contra ~40 horas do pipeline completo)

### Passo 5: Veja o skip note

Para cada step pulado, um arquivo é gerado em `docs/delta/skip-notes/`:

```markdown
# Skip Note: Step 5 — Arquitetura

**Decisao:** Step pulado conforme DELTA_REPORT.md
**Justificativa:** Stack e ADRs mantidos

**Iteracao:** v2

**Gate:** ✅ Auto-aprovado via Smart Skip
```

A rastreabilidade é mantida: qualquer pessoa no time pode entender por que a arquitetura não foi redefinida.

---

## O Que Há de Novo no PRP de Alteração (PRP-A)

Quando um PRP existente precisa ser modificado, o Step 3 gera um **PRP-A**:

```markdown
# PRP-A-001: Adição de Filtro por Unidade Orçamentária

**PRP Original:** PRP-003 — Módulo de Relatórios
**Iteracao:** v1 → v2
**Tipo:** Amendment

## Resumo do Delta
- RFs alterados: 1 (RF-003.4)
- RFs adicionados: 1 (RF-003.7)
- Contratos de API: Alterados (Breaking: Sim)
- Modelo de dados: Inalterado

## Contratos de API (Delta)
Endpoint: GET /api/relatorios
- Query param novo: ?unidade={id} (não breaking)
- Response: adiciona campo unidadeOrcamentaria (breaking)

## Arquivos
- ✏️ Modificar: src/relatorios/relatorio.service.ts
- ✏️ Modificar: src/relatorios/relatorio.controller.ts
- ✏️ Modificar: src/relatorios/relatorio.service.spec.ts
- ➕ Criar: src/relatorios/dto/filtro-unidade.dto.ts
```

Na execução, o agente segue TDD adaptado: modifica teste existente → vê falhar → implementa → vê passar. E executa a **suite completa** para garantir não regressão.

---

## Classificação Major vs Minor

### MAJOR (pipeline completo adaptado)

Dispara quando qualquer um destes ocorrer:

- Arquitetura afetada (stack, ADRs, C4)
- Design System afetado
- Perfis/permissoes alterados
- Breaking changes em API
- 3+ PRPs existentes afetados
- Migrations/schema alterados
- Configuração de infraestrutura alterada

### MINOR (pipeline leve)

Dispara quando apenas código/documentação é afetado:

- 1-2 PRPs (código apenas, sem breaking changes)
- Novos RFs sem alterar requisitos existentes
- Hotfix / escopo cirúrgico
- Cosmética (UI/tradução)

---

## Comandos Rápidos

```bash
# Iniciar fluxo delta
llc delta start --iteration v2

# Ver o plano
llc delta plan

# Executar pipeline com smart skip
llc pipeline --delta --iteration v2

# Executar step individual
llc run --step 3 --delta

# Modo CI/CD
llc pipeline --delta --iteration v2 --auto-approve
```

---

## Quando NÃO Usar

1. **Mudança de stack** (React → Vue, REST → GraphQL): use pipeline completo
2. **Primeira execução** (sistema nunca passou pelo LLC): use greenfield
3. **Refatoração completa de módulo**: use PRP-N em vez de PRPs-A

---

## Conclusão

O fluxo delta do LLC reconhece uma verdade fundamental: **sistemas vivos evoluem, não nascem prontos**.

Com cinco práticas — analisar o impacto, perguntar antes de presumir, preservar o que não mudou, documentar o delta e garantir não regressão — times podem usar agentes de IA para evoluir sistemas existentes com confiança.

---

*LLC é uma metodologia open-source sob licença MIT. Contribuições são bem-vindas.*
