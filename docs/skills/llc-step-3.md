---
name: llc-step-3
description: Pipeline LLC Passo 3: Gera PRPs (Project Requirement Proposals) a partir dos PRDs e Especificações validadas. Suporta modo padrão (greenfield) e modo delta (alterações em sistema existente).
version: 1.1.0
tags: [prp, planning, delta, amendment, llc-pipeline]
---

# LLC Skill: Step 3 — Project Requirement Proposals (PRPs)

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Decomposition  
**Depende de:** Step 2 (PRDs validados) ou Step Δ.1 (DELTA_REPORT.md aprovado)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-3` ou "Execute a skill llc-step-3".
3. **Modo delta:** Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado, esta skill opera em **modo delta** — gerando PRP-A (amendment) e PRP-N (new) em vez de PRPs completamente novos. O modo é detectado automaticamente pela presença do DELTA_REPORT.md.

## 📋 Pré-requisitos

### Modo Padrão (Greenfield)
- [ ] `docs/prd/executive_PRD.md` e `docs/prd/PRD_tecnico_institucional.md` (validados no Step 2)
- [ ] 7 specs em `docs/business/specs/` (base de referência)
- [ ] `docs/prps/PRP_TEMPLATE.md`
- [ ] `docs/business/specs/MOD-*.md` (módulos validados)

### Modo Delta (Alteração)
- [ ] `docs/planning/DELTA_REPORT.md` aprovado (Gate Δ.0)
- [ ] Step Δ.1 concluído (Grill Me de Mudança)
- [ ] PRPs existentes em `docs/prps/` (versão atual)
- [ ] `docs/templates/PRP_AMENDMENT_TEMPLATE.md` (template de alteração)
- [ ] `docs/prps/PRP_TEMPLATE.md` (template padrão, para PRP-N)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-3` do pipeline LLC. Seu objetivo é decompor o sistema em contratos auto-contidos de implementação chamados PRPs (Project Requirement Proposals).

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado, esta skill opera em modo delta.** Neste caso, você gerará:
- **PRP-A-\* (Amendment):** Para alterações em PRPs existentes (usa `PRP_AMENDMENT_TEMPLATE.md`)
- **PRP-N-\* (New):** Para funcionalidades totalmente novas (usa `PRP_TEMPLATE.md`)

Caso contrário, opera em modo padrão (greenfield), gerando apenas PRPs sequenciais.

## 🔍 Modo Interrogatório (Grill Me) — OBRIGATÓRIO

**ANTES de gerar qualquer PRP, execute esta fase:**

1. **Analise** os PRDs em `docs/prd/`, os specs em `docs/business/specs/` e os módulos (MOD-*.md) e identifique:
   - Ambiguidades nos requisitos que impedem decomposição precisa
   - Funcionalidades cujo escopo não está claro
   - Dependências implícitas entre módulos que não foram documentadas

2. **Apresente** ao usuário uma lista numerada de perguntas (máximo 8), ordenadas por criticidade (🔴 bloqueante, 🟡 alta, 🟢 média). Foque em questões de granularidade, escopo e dependências.

3. **Sugira** 2-3 respostas possíveis por pergunta. Aguarde a resposta do usuário.

4. O usuário pode responder seletivamente ou dizer **"prossiga com o que tem"**. Neste caso, use `[NÃO IDENTIFICADO]` no PRP e marque suposições.

5. Após as respostas, prossiga com a decomposição em PRPs.

**💡 Dica:** Ative o modo thinking/extended reasoning da sua LLM para esta fase.

### O que é um PRP
Um PRP é um contrato completo para uma unidade de trabalho implementável. Ele contém: contexto, requisitos (Gherkin), API contracts, componentes, mudanças de banco, estratégia de testes, riscos e Definition of Done. Cada PRP deve ser auto-contido o suficiente para um agente de desenvolvimento executá-lo sem ambiguidade.

### 1. Leia as Entradas
- Leia os PRDs em `docs/prd/`.
- Leia os specs e módulos em `docs/business/specs/`.
- Leia `docs/prps/PRP_TEMPLATE.md` — estrutura que cada PRP deve seguir.

### 2. Decomponha em PRPs
- Analise specs, módulos e PRDs para identificar unidades de trabalho independentes.
- Cada módulo (MOD-XXX-NNN) tipicamente gera 1 a 5 PRPs, dependendo da complexidade.
- Use a nomenclatura: `PRP-[NNN]-[nome_descritivo].md`
  - NNN: número sequencial com 3 dígitos (001, 002, ...)
  - nome_descritivo: minúsculas com underscores
- Agrupe PRPs relacionados por módulo de origem.
- Salve cada PRP em: `docs/prps/PRP-001-[nome].md`, `docs/prps/PRP-002-[nome].md`, ...

### 3. Preencha Cada PRP
- **Contexto e Objetivo:** O que este PRP entrega e por quê.
- **Requisitos Funcionais:** Formato Gherkin (Given/When/Then) para cada cenário. Preencha as colunas **Teste(s)** e **Arquivo(s) impl** com os caminhos relativos dos arquivos de teste e implementação de cada RF (obrigatório para verificação mecânica por `prp_verify.py` no Step 11.2).
- **Requisitos Não Funcionais:** Performance, segurança, acessibilidade aplicáveis.
- **API Contracts:** Endpoints, payloads, autenticação, rate limits.
- **Componentes:** Props, estados (loading, empty, error, success), referência ao Design System.
- **Database Changes:** Tabelas, campos, índices, migrações.
- **Test Strategy:** Testes unitários, integração e E2E esperados.
- **Dependências:** Quais PRPs devem ser concluídos antes deste.
- **Cross-Cutting Concerns (CCC) — §13 do template:** AuthService, AuthGuard, interceptors, testes, audit logging, input validation, etc. (ver seção obrigatória no `PRP_TEMPLATE.md`).
- **Riscos e Mitigações:** O que pode dar errado e como mitigar.
- **Definition of Done:** Checklist de aceitação.

### 4. Análise de Dependências
- Identifique dependências entre PRPs (A bloqueia B, B depende de C).
- Anote no campo `Dependências` de cada PRP: quais PRPs são pré-requisitos.
- Anote no campo `Bloqueia`: quais PRPs dependem deste.

---

## 🔄 Modo Delta — Decomposição de Alterações

**Ative este modo quando DELTA_REPORT.md existir e estiver aprovado.**

### 1. Leia as Entradas do Delta
- Leia `docs/planning/DELTA_REPORT.md` — seções §3 (PRPs afetados) e §4 (novos PRPs)
- Leia o(s) PRP(s) originais que serão alterados (PRP-YYY, PRP-ZZZ)
- Leia os novos documentos de mudança em `docs/business/ingestion/converted/`
- Leia `docs/templates/PRP_AMENDMENT_TEMPLATE.md` — estrutura para PRP-A

### 2. Gere PRP-A (Amendment) para Cada PRP Existente Afetado

Para cada PRP listado em `DELTA_REPORT.md §3.2` (PRPs com alteração):

1. **Leia o PRP original na íntegra** — você precisa entender o que existe hoje antes de documentar o que muda.
2. **Identifique o delta específico:**
   - RFs do PRP original que mudam de comportamento
   - Novos RFs que entram neste PRP
   - RFs que saem (deprecação)
   - Contratos de API: o que muda no request/response
   - Modelo de dados: campos novos, alterados ou removidos
   - Testes existentes: quais precisam ser atualizados
3. **Preencha o template PRP_AMENDMENT_TEMPLATE.md** seguindo as convenções:
   - **Nomenclatura:** `PRP-A-[NNN]-[nome_descritivo_da_alteracao].md`
     - NNN: número sequencial com 3 dígitos (001, 002, ...), independente dos PRPs existentes
     - Ex: `PRP-A-001-expansao-enum-status.md` (altera PRP-007)
   - **§1.2 — Resumo do Delta:** Seja preciso sobre o que muda em cada dimensão
   - **§2 — RF Delta:** Apenas RFs novos/alterados/removidos (RFs inalterados ficam subentendidos)
   - **§5 — API Contracts Delta:** Use diff notation (`-` antigo, `+` novo) para clareza
   - **§7 — Arquivos:** Liste explicitamente modificar/criar/remover — o agente de execução usará esta seção como roteiro
   - **§11 — DoD:** Inclui a garantia de que testes existentes não-regredidos continuam passando
4. **Salve em:** `docs/prps/PRP-A-001-[nome].md`

### 3. Gere PRP-N (New) para Funcionalidades Totalmente Novas

Para cada novo PRP listado em `DELTA_REPORT.md §4`:

1. Siga o fluxo padrão de geração de PRP (seções 1-3 acima), **usando PRP_TEMPLATE.md**.
2. **Nomenclatura:** `PRP-N-[NNN]-[nome_descritivo].md`
   - Ex: `PRP-N-001-modulo-auditoria.md`
3. **Salve em:** `docs/prps/PRP-N-001-[nome].md`

### 4. Atualize Referências Cruzadas

- No PRP original (ex: PRP-007), adicione uma nota no topo:
  ```markdown
  > **⚠️ Alterado por:** PRP-A-001 — expansão do enum status.
  > Consulte o PRP-A para detalhes das mudanças. Este PRP permanece válido
  > para as partes não alteradas.
  ```
- No PRP-A, referencie o PRP original no cabeçalho (campo `PRP Original`).
- Verifique se dependências entre PRP-A/PRP-N e PRPs existentes estão corretas.

---

## ⚠️ REGRAS CRÍTICAS

1. **Auto-contido:** Um agente deve conseguir implementar o PRP lendo apenas este arquivo + templates referenciados.
2. **Granularidade:** Cada PRP deve ter entre 2 e 8 dias de esforço estimado. Se for maior, quebre em PRPs menores.
3. **Gherkin Obrigatório:** Todo requisito funcional deve ter pelo menos um cenário Gherkin.
4. **Rastreabilidade:** Cada PRP deve referenciar o(s) módulo(s) e spec(s) de origem.
5. **Idempotência:** Verifique existência dos arquivos de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os PRPs, **PARE** e apresente:

### Modo Padrão
1. **Resumo:** Quantos PRPs gerados, organizados por módulo.
2. **Grafo de Dependências:** Diagrama Mermaid ou tabela mostrando relações entre PRPs.
3. **Estimativa Total:** Soma das estimativas de todos os PRPs em dias.
4. **PRPs sem dependências:** Quais podem começar imediatamente (execução paralela).
5. **Lacunas:** Algum módulo ou requisito dos PRDs não foi coberto por PRPs?
6. **Próximos Passos:** Perguntas para validação humana sobre granularidade, dependências e escopo.

### Modo Delta
1. **Resumo:** Quantos PRP-A (amendment) e PRP-N (new) gerados.
2. **PRPs Originais Alterados:** Lista de PRPs existentes que receberam PRP-A.
3. **PRPs Novos:** Lista de PRP-N para funcionalidades novas.
4. **Mudanças Acumuladas:** Estimativa total de dias (PRP-A + PRP-N).
5. **Relação com DELTA_REPORT.md:** Os PRPs gerados cobrem todas as seções §3 e §4 do relatório?
6. **PRPs Originais Atualizados:** Verifique se todos os PRPs alterados receberam a anotação de referência ao PRP-A correspondente.
7. **Próximos Passos:** Validação humana sobre granularidade, precisão dos deltas e dependências.

**NÃO prossiga para o próximo passo. Aguarde validação humana (Gate 4).**
