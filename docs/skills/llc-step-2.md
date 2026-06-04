---
name: llc-step-2
description: Pipeline LLC Passo 2: Gera PRD Executivo e PRD Técnico Institucional a partir das 8 especificações validadas.
version: 1.0.0
tags: [prd, specification, llc-pipeline]
---

# LLC Skill: Step 2 — PRDs (Executivo + Técnico)

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Product Requirements  
**Depende de:** Step 1 (8 Especificações validadas)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-2` ou "Execute a skill llc-step-2".

## 📋 Pré-requisitos

- [ ] 7 documentos de especificação em `docs/business/specs/` (validados no Step 1)
- [ ] `docs/prd/template_prd_executivo_institucional.md`
- [ ] `docs/prd/template_prd_tecnico_institucional.md`

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-2` do pipeline LLC. Seu objetivo é sintetizar as 8 especificações em dois PRDs com públicos distintos.

### Documentos a Gerar

| # | Documento | Template | Público | Tom |
|---|-----------|----------|---------|-----|
| 1 | PRD Executivo | `docs/prd/template_prd_executivo_institucional.md` | Gestores, stakeholders | Institucional, valor de negócio, alto nível |
| 2 | PRD Técnico | `docs/prd/template_prd_tecnico_institucional.md` | Equipe de desenvolvimento, arquitetos | Técnico, preciso, completo |

### 1. Leia as Entradas
- Leia TODOS os 7 documentos em `docs/business/specs/` (glossário, RF, RNF, regras de negócio, BPMN, perfis, integrações).
- Leia `docs/business/specs/visao_estrategica_e_negocio.md`.
- Leia os dois templates de PRD em `docs/prd/`.

### 2. Gere o PRD Executivo
- Foco em: visão, objetivos de negócio, escopo, benefícios esperados, métricas de sucesso.
- Linguagem acessível a não-técnicos.
- Evite jargão técnico. Explique conceitos quando necessário.
- Destaque o valor institucional e o alinhamento estratégico.
- Seções de tecnologia devem ser resumidas (máximo 1 parágrafo por tópico).
- Salve em: `docs/prd/executive_PRD.md`.

### 3. Gere o PRD Técnico
- Foco em: requisitos detalhados, stack tecnológico, arquitetura conceitual, contratos de API, modelo de dados, integrações, restrições técnicas.
- Linguagem técnica e precisa. Use diagramas Mermaid quando aplicável.
- Inclua TODOS os requisitos funcionais e não-funcionais.
- Detalhe perfis, permissões e regras de autorização.
- Salve em: `docs/prd/PRD_tecnico_institucional.md`.

### 4. Verificação de Consistência entre PRDs
- O escopo do PRD Executivo está contido no PRD Técnico?
- Métricas de sucesso do Executivo são endereçadas pelos RNFs do Técnico?
- Ambos usam a mesma terminologia do Glossário?

---

## ⚠️ REGRAS CRÍTICAS

1. **Dois públicos, mesma verdade:** Os PRDs NÃO podem se contradizer. O Técnico expande o Executivo, nunca diverge.
2. **Rastreabilidade:** Cada afirmação no PRD deve ter origem nos specs do Step 1.
3. **Nada novo:** Não introduza requisitos, funcionalidades ou restrições que não estejam nos specs validados.
4. **Tom adequado:** Executivo = institucional e estratégico. Técnico = preciso e completo.
5. **Idempotência:** Verifique existência dos arquivos de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os 2 arquivos, **PARE** e apresente:

1. **PRD Executivo:** Resumo em 3 bullets do que cobre.
2. **PRD Técnico:** Contagem de seções e requisitos cobertos.
3. **Consistência:** Problemas de alinhamento entre os dois PRDs (se houver).
4. **Cobertura dos Specs:** Algum spec do Step 1 não foi adequadamente coberto?
5. **Próximos Passos:** Perguntas para validação humana (separadas por perfil: gestor e técnico).

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
