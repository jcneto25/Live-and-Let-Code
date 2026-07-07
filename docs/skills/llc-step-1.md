---
name: llc-step-1
description: Pipeline LLC Passo 1: Gera 8 documentos de especificação (Glossário, RF, RNF, Regras de Negócio, BPMN, Perfis, Integrações) a partir da Visão e Módulos validados.
version: 1.0.0
tags: [specification, llc-pipeline]
---

# LLC Skill: Step 1 — 8 Especificações

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Specification  
**Depende de:** Step 0.5 (Visão + Módulos validados)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-1` ou "Execute a skill llc-step-1".
3. A IA usará as ferramentas de arquivo para gerar os documentos.

## 📋 Pré-requisitos

- [ ] `docs/business/specs/visao_estrategica_e_negocio.md` (validado no Step 0.5)
- [ ] `docs/business/specs/MOD-*.md` (módulos validados no Step 0.5)
- [ ] Templates: `docs/Template_Glossario.md`, `docs/Template_Requisitos_Nao_Funcionais.md`, `docs/template_requisitos_funcionais.md`, `docs/template_business_rules.md`, `docs/Template_WORKFLOWS_E_BPMN.md`, `docs/business/specs/perfis_permissoes.md`, `docs/Template_Catalogo_Integracoes.md`

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 1** estiver listado como "skip":
   - Gere um skip note em `docs/delta/skip-notes/step-1.md`:
     ```markdown
     # Skip Note: Step 1 — 7 Especificações
     **Decisão:** Step pulado — nenhum spec (glossário, RFs, RNFs, regras,
     workflows, perfis, integrações) é afetado nesta iteração.
     **Gate 2:** ✅ Auto-aprovado (reaproveitando aprovação anterior)
     ```
   - **PARE** e informe: "Step 1 pulado via Smart Skip. 7 specs existentes reaproveitados. Gate 2 auto-aprovado."
   - **Não prossiga para o próximo step.**
3. Se **Step 1** estiver listado como "executar" (modo diff): opere em modo **delta** — gere apenas addenda/alterações nos specs afetados, não reescreva do zero. Specs não listados no DELTA_REPORT.md §2.2 como "to_review" devem permanecer inalterados.
4. Se DELTA_REPORT.md não existir: prossiga no modo padrão (greenfield).

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-1` do pipeline LLC. Seu objetivo é gerar 8 documentos de especificação detalhada a partir da Visão Estratégica e Módulos validados no passo anterior.

## 🔍 Modo Interrogatório (Grill Me) — OBRIGATÓRIO

**ANTES de gerar qualquer artefato, execute esta fase:**

1. **Analise** a Visão e os Módulos em `docs/business/specs/` e identifique ambiguidades, lacunas, contradições e suposições implícitas.

2. **Apresente** ao usuário uma lista numerada de perguntas (máximo 8), ordenadas por criticidade (🔴 bloqueante, 🟡 alta, 🟢 média).

3. **Sugira** 2-3 respostas possíveis por pergunta. Aguarde a resposta do usuário.

4. O usuário pode responder seletivamente ou dizer **"prossiga com o que tem"**. Neste caso, use `[NÃO IDENTIFICADO]` para lacunas e `[SUPOSIÇÃO: ...]` para suposições.

5. Após as respostas, prossiga com a geração normal dos 7 specs.

**💡 Dica:** Ative o modo thinking/extended reasoning da sua LLM para esta fase.

### Documentos a Gerar

| # | Documento | Template | Destino |
|---|-----------|----------|---------|
| 1 | Glossário | `docs/Template_Glossario.md` | `docs/business/specs/glossario.md` |
| 2 | Requisitos Funcionais | `docs/template_requisitos_funcionais.md` | `docs/business/specs/requisitos_funcionais.md` |
| 3 | Requisitos Não Funcionais | `docs/Template_Requisitos_Nao_Funcionais.md` | `docs/business/specs/requisitos_nao_funcionais.md` |
| 4 | Regras de Negócio | `docs/template_business_rules.md` | `docs/business/specs/regras_negocio.md` |
| 5 | Workflows e BPMN | `docs/Template_WORKFLOWS_E_BPMN.md` | `docs/business/specs/workflows_bpmn.md` |
| 6 | Perfis e Permissões | `docs/Template_Perfis_Permissoes.md` | `docs/business/specs/perfis_permissoes.md` |
| 7 | Catálogo de Integrações | `docs/Template_Catalogo_Integracoes.md` | `docs/business/specs/catalogo_integracoes.md` |

### 1. Leia as Entradas
- Leia `docs/business/specs/visao_estrategica_e_negocio.md` — base para todos os documentos.
- Leia TODOS os `MOD-*.md` em `docs/business/specs/` — fonte de requisitos detalhados por módulo.
- Leia cada template listado na tabela acima.

### 2. Gere Cada Documento
- Preencha cada template com as informações extraídas da Visão e dos Módulos.
- Mantenha consistência terminológica entre todos os 7 documentos.
- Referencie módulos usando seus IDs (MOD-PLN-001, etc.) para rastreabilidade.
- Se um template tiver seções não cobertas pela documentação fonte, preencha com: `[NÃO IDENTIFICADO — requer validação humana]`.

### 3. Consistência Cruzada
- Após gerar todos os 7 documentos, faça uma verificação cruzada:
  - Termos do Glossário são usados consistentemente nos demais documentos?
  - Perfis listados em Perfis e Permissões aparecem nos Workflows BPMN?
  - Integrações do Catálogo são referenciadas nos Requisitos Funcionais?
  - Regras de Negócio estão refletidas nos Workflows?

---

## ⚠️ REGRAS CRÍTICAS

1. **Zero Alucinação:** Não invente. Tudo deve vir da Visão ou dos Módulos validados.
2. **Consistência:** Mesmos termos, mesmos nomes de perfil, mesmas siglas em todos os documentos.
3. **Rastreabilidade:** Cada requisito funcional deve referenciar o módulo de origem (MOD-XXX-NNN).
4. **Idempotência:** Antes de escrever, verifique se o arquivo existe. Se existir, pergunte se sobrescreve ou versiona.
5. **Cobertura Total:** Ao final, verifique se todos os módulos tiveram seus requisitos cobertos nos documentos gerados.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os 7 arquivos, **PARE** e apresente:

1. **Resumo:** Lista dos 7 documentos gerados com contagem de itens (ex: "32 requisitos funcionais, 12 regras de negócio, 8 perfis").
2. **Lacunas:** Seções com placeholder `[NÃO IDENTIFICADO...]`.
3. **Inconsistências:** Problemas de consistência cruzada encontrados e como foram resolvidos.
4. **Cobertura de Módulos:** Tabela mostrando qual módulo contribuiu para qual documento.
5. **Próximos Passos:** Sugestões de perguntas para validação humana.

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
