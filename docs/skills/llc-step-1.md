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
- [ ] Templates: `docs/Template_Glossario.md`, `docs/Template_Requisitos_Nao_Funcionais.md`, `docs/template_requisitos_funcionais.md`, `docs/template_business_rules.md`, `docs/Template_WORKFLOWS_E_BPMN.md`, `docs/Template_Perfis_Permissoes.md`, `docs/Template_Catalogo_Integracoes.md`

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-1` do pipeline LLC. Seu objetivo é gerar 8 documentos de especificação detalhada a partir da Visão Estratégica e Módulos validados no passo anterior.

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
