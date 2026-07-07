---
name: llc-step-delta-impact
description: Step Δ.0 — Analisa o delta entre a versão atual do sistema e novos documentos de mudança, gerando DELTA_REPORT.md com classificação major/minor, artefatos afetados e plano de execução adaptado.
version: 1.0.0
tags: [delta, change, impact-analysis, llc-pipeline]
---

# LLC Skill: Step Δ.0 — Delta Impact Analysis

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Change Management — Impact Analysis  
**Quando usar:** Quando novos documentos de mudança chegam e o sistema já passou pelo pipeline completo ao menos uma vez.  
**Pré-requisito:** Sistema em versão N (com `docs/`, `src/`, `.ace/dependency-graph.yaml` existentes).  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `docs/skills/` do projeto (já está lá).
2. Invoque no chat: `@llc-step-delta-impact` ou "Execute a skill llc-step-delta-impact".
3. **IMPORTANTE:** Ative o modo thinking/extended reasoning da sua LLM — a análise de impacto cruzado exige raciocínio multi-step.

## 📋 Pré-requisitos (Verificação Automática)

Antes de iniciar, verifique se os seguintes itens existem:
- [ ] Diretório `docs/business/ingestion/` com **novos** documentos de mudança (PDF, DOCX, MD, etc.)
- [ ] `docs/business/ingestion/converted/` com versão convertida dos novos documentos (ou execute Step 0.1 primeiro)
- [ ] `.ace/dependency-graph.yaml` existente (mapeamento dos artefatos da versão atual)
- [ ] `.ace/scripts/impact-analyzer.py` existente
- [ ] Repositório git com histórico (para `git diff` entre versões)
- [ ] Step 0.1 já executado (conversão Docling) — se não, execute `@llc-step-0-1` primeiro

*Se algum item faltar, PARE e liste os arquivos ausentes para o usuário.*

---

## 🎯 PROMPT DE EXECUÇÃO

Você está operando no modo de execução da skill `llc-step-delta-impact` do pipeline Live and Let Code (LLC). Seu objetivo é analisar o **delta** entre a versão atual do sistema (artefatos existentes em `docs/`) e os novos documentos de mudança em `docs/business/ingestion/converted/`, gerando um relatório de impacto que orientará os passos seguintes.

**Contexto:** O sistema já passou pelo pipeline LLC completo ao menos uma vez. Agora novos documentos chegaram propondo mudanças. Não é greenfield — é evolução.

### 1. Leia e Compreenda

1. Leia TODOS os novos documentos em `docs/business/ingestion/converted/` (Markdown puro).
2. Leia os artefatos existentes da versão atual do sistema:
   - `docs/business/specs/visao_estrategica_e_negocio.md` (visão atual)
   - `docs/business/specs/` (7 specs atuais)
   - `docs/prd/PRD_tecnico_institucional.md` (PRD técnico atual)
   - `docs/prps/` (PRPs existentes)
   - `docs/architecture/ARCHITECTURE.md` (arquitetura atual)
   - `docs/design/DESIGN_SYSTEM.md` (design system atual)
   - `docs/planning/DEPENDENCY_MATRIX.md` (matriz de dependências atual)
   - `docs/planning/TASKS.md` (tarefas atuais)

3. Execute o analisador de impacto automático:

   ```
   python .ace/scripts/impact-analyzer.py --json --skills --classify
   ```

   O `--classify` classifica automaticamente a mudança como MAJOR ou MINOR baseado em thresholds (arquitetura, design system, perfis, migrations, 3+ PRPs).
   O `--skills` sugere skills a re-executar.

   Se o `impact-analyzer.py` reportar arquivos de código-fonte não mapeados no YAML (`unmatched_source`), analise manualmente o diretório `src/` para identificar módulos potencialmente afetados.

### 2. Gere o DELTA_REPORT.md

Use o template em `docs/templates/DELTA_REPORT_TEMPLATE.md` (se existir) ou produza um relatório seguindo a estrutura abaixo. Salve em `docs/planning/DELTA_REPORT.md`.

#### 2.1 Metadados da Iteração

Registre a versão atual do sistema e a identificação da iteração proposta.

#### 2.2 Classificação Automática (Major vs Minor)

Use a classificação automática do `impact-analyzer.py --classify` como ponto de partida,
mas complemente com raciocínio humano para casos de fronteira.

**Thresholds automáticos (embutidos no --classify):**
- 🔴 Afeta **arquitetura** (stack, ADRs, diagramas C4) → Step 5 precisa reexecutar
- 🔴 Afeta **Design System** (tokens, novos componentes, temas) → Step 7 precisa reexecutar
- 🔴 Afeta **perfis/permissoes** (novo perfil, alteração de regras de acesso) → Step 6 + 7 impactados
- 🔴 **Migrations/schema** alterados (prisma, migrations) → modelo de dados muda
- 🔴 **Configuração de infraestrutura** alterada (Docker, CI/CD, nginx)
- 🔴 Afeta **3+ PRPs existentes** → mudança generalizada

**Classifica como MINOR se apenas código/documentação for afetado:**
- 🟢 1-2 PRPs (código apenas, sem breaking changes)
- 🟢 Novos RFs sem alterar requisitos existentes
- 🟢 Hotfix (bug em produção, escopo cirúrgico)
- 🟢 Cosmética (UI/tradução/documentação)

**Thresholds que exigem julgamento humano (não automatizados):**
- 🔴 **Breaking changes** em contratos de API existentes (análise semântica necessária)
- 🔴 Afeta **requisitos não-funcionais** (performance, segurança, compliance)
- 🟡 Afeta **modelo de dados** indiretamente (sem migration automática)

> **Se o `--classify` reportar MAJOR, confirme os motivos. Se reportar MINOR mas
> você identificar um dos thresholds não-automatizados acima, sobrescreva para MAJOR.**

#### 2.3 Inventário de Artefatos

Para cada artefato LLC da versão atual, determine:

| Status | Significado |
|--------|-------------|
| **unchanged** | Artefato não é afetado — pode ser reaproveitado sem revisão |
| **to_review** | Artefato é afetado direta ou indiretamente — precisa ser revisado/atualizado |
| **re_execute** | Artefato precisa ser regerado do zero pela skill correspondente |

Use três listas separadas:
- `artifacts_unchanged` — podem pular o gate
- `artifacts_to_review` — precisam de revisão humana
- `artifacts_to_re_execute` — precisam ser regerados

#### 2.4 PRPs Afetados

Para cada PRP existente, determine:
- **PRP-XXX:** Não afetado (mantido como está)
- **PRP-XXX:** Afetado — requer PRP de alteração (PRP-A-*)
- **PRP-XXX:** Deprecado (removido na nova versão)

Liste os PRPs que precisam de alteração e, para cada um, descreva brevemente o que muda.

#### 2.5 Novos PRPs Necessários

Liste os PRPs totalmente novos (PRP-N-*) que precisam ser criados para cobrir as novas funcionalidades.

#### 2.6 Plano de Execução Sugerido

Com base na classificação major/minor e no inventário de artefatos, sugira:

- **execute_steps:** Lista de steps que precisam ser executados nesta iteração
- **skip_steps:** Lista de steps que podem ser pulados (com justificativa). Cada entrada deve conter: `step_id`, `reason` (justificativa do skip), `artifacts_reused` (quais artefatos da versão anterior são reaproveitados)
- **estimated_effort:** Estimativa de esforço total (dias)
- **suggested_waves:** Sugestão de ondas de execução (se aplicável)

> **Os steps listados em `skip_steps` são automaticamente detectados pelas skills condicionais
> via Smart Skip. Consulte `docs/skills/llc-smart-skip.md` para o protocolo detalhado.**

**Regras de skip por classificação:**

| Step | Major | Minor |
|------|-------|-------|
| 0.5 (Visão) | Executa (addendum) | Skip (se escopo inalterado) |
| 1 (Specs) | Executa (diff mode) | Skip (se RFs inalterados) |
| 2 (PRDs) | Executa (v2) | Skip |
| 3 (PRPs) | Executa (PRP-A + PRP-N) | Executa (PRP-A apenas) |
| 4 (Planning) | Executa | Executa |
| 5 (Architecture) | Executa (se afetado) | Skip |
| 6 (Tasks) | Executa | Executa |
| 7 (Design System) | Executa (se afetado) | Skip |
| 8 (Setup + Mock) | Executa (se schema muda) | Skip |
| 9 (Testing Docs) | Executa (se estratégia muda) | Skip |
| 10 (Project Docs) | **Sempre executa** | **Sempre executa** |
| 10.5 (User Guide) | Executa (se UI muda) | Skip |
| 10.6-10.8 (Security) | **Sempre executa** | **Sempre executa** |
| 11 (Execution) | Executa | Executa |
| 11.1 (OWASP) | **Sempre executa** | **Sempre executa** |
| 11.2 (PRP Verify) | **Sempre executa** | **Sempre executa** |

#### 2.7 Riscos e Observações

Liste riscos identificados durante a análise:
- Dependências críticas entre PRPs existentes e novos
- Potencial de regressão em funcionalidades existentes
- Breaking changes que exigem comunicação com stakeholders

---

## ⚠️ REGRAS CRÍTICAS DE EXECUÇÃO

1. **Não presuma nada sobre as mudanças.** Leia os novos documentos na íntegra antes de comparar. Use o Grill Me (Step Δ.1) para resolver ambiguidades, não este step.

2. **A classificação major/minor deve ser baseada em evidências dos documentos, não em suposição.** Se não houver informação suficiente para classificar, classifique como MAJOR (default seguro).

3. **Idempotência.** Se `docs/planning/DELTA_REPORT.md` já existir, pergunte ao usuário se deseja sobrescrever ou gerar uma nova versão com sufixo `_v2`.

4. **Rastreabilidade.** Cada item no relatório deve referenciar sua origem: trecho do novo documento, linha do artefato existente, ou output do `impact-analyzer.py`.

5. **Se o `impact-analyzer.py` falhar** (ex: repositório sem git), faça a análise manual: compare cada artefato existente com os novos documentos, seção por seção.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

1. **Arquivo gerado:** `docs/planning/DELTA_REPORT.md`
2. **Apresente** ao usuário um resumo estruturado:
   - **Classificação:** MAJOR ou MINOR (justificativa)
   - **Artefatos inalterados (skip):** N itens
   - **Artefatos a revisar:** N itens
   - **PRPs afetados:** N PRPs existentes
   - **Novos PRPs:** N PRPs necessários
   - **Steps a executar:** lista
   - **Steps a pular:** lista (com justificativa)
   - **Riscos:** principais riscos identificados

3. **Gate Δ.0 — Validação Humana Obrigatória:**

   Apresente as seguintes perguntas para o usuário validar:

   ```
   👤 GATE Δ.0 — VALIDAÇÃO DO DELTA_REPORT.md

   1. A classificação (major/minor) está correta?
   2. Os artefatos marcados como "unchanged" realmente não precisam de revisão?
   3. Os PRPs afetados estão corretamente identificados?
   4. O plano de steps proposto (executar vs pular) está adequado?
   5. Há riscos não identificados no relatório?

   Decisão: [approved / rejected / conditional]
   ```

4. **Se aprovado:** O DELTA_REPORT.md orienta os steps seguintes. Sugira a execução do Step Δ.1: `@llc-step-delta-grill`.

5. **Se rejeitado:** Corrija o relatório conforme feedback e reapresente para validação.
