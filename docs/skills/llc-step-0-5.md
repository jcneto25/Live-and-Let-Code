---
name: llc-step-0-5
description: Pipeline LLC Passo 0.5: Gera Visão Estratégica e Especificação de Módulos a partir de documentos de ingestão de negócio.
version: 1.1.0
tags: [business-analysis, specification, llc-pipeline]
---

# LLC Skill: Step 0.5 — Visão Estratégica + Módulos

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Knowledge Ingestion → Specification  
**Mantenedor:** Equipe LLC  

## 🛠️ Como usar esta Skill no Claude CLI
1. Coloque este arquivo em `.claude/skills/` (global) ou `.claude/skills/` (local do projeto).
2. Invoque no chat usando: `@llc-step-0-5` ou "Execute a skill llc-step-0-5".
3. A IA assumirá automaticamente o modo de execução e usará as ferramentas de sistema de arquivos.

## 📋 Pré-requisitos (Verificação Automática)
Antes de iniciar, use a ferramenta `list_directory` ou `read_file` para verificar se os seguintes itens existem no diretório de trabalho atual:
- [ ] Diretório `docs/business/ingestion/` com documentos de domínio.
- [ ] `docs/template_visao_estrategica_e_negocio.md`
- [ ] `docs/guia_preenchimento_template_visao_estrategica_negocio.md`
- [ ] `docs/business/Template_Especificacao_Modulo.md`

*Se algum item faltar, PARE e liste os arquivos ausentes para o usuário.*

---

## 🎯 PROMPT DE EXECUÇÃO

Você está operando no modo de execução da skill `llc-step-0-5` do pipeline Live and Let Code (LLC). Seu objetivo é analisar a documentação de negócio e gerar artefatos de Visão Estratégica e Especificação de Módulos usando as ferramentas de arquivo disponíveis.

### 1. Leia e Compreenda (Use `read_file`)
- Leia TODOS os arquivos em `docs/business/ingestion/`.
- Extraia: domínios funcionais, processos, público-alvo, premissas, restrições, regras de negócio, integrações, perfis de usuário, objetivos estratégicos e indicadores.

### 2. Gere a Visão Estratégica e de Negócio
- Use o conteúdo de `docs/template_visao_estrategica_e_negocio.md` como base estrutural.
- Siga ESTRITAMENTE as regras de `docs/guia_preenchimento_template_visao_estrategica_negocio.md`.
- Preencha TODAS as seções. Não deixe placeholders `[ ]` vazios.
- Se a documentação não cobrir algum item, preencha com: `[NÃO IDENTIFICADO NA DOCUMENTAÇÃO — requer validação humana]`.
- **Ação:** Use `write_file` para salvar em: `docs/business/specs/visao_estrategica_e_negocio.md`.

### 3. Identifique e Especifique os Módulos do Sistema
- Decomponha o sistema em módulos funcionais independentes (domínios coesos).
- **Nomenclatura Obrigatória:** `MOD-[SIGLA_DOMINIO]-[NNN]_[nome_modulo].md`
  - `SIGLA_DOMINIO`: 3 letras maiúsculas (ex: PLN=Planejamento, EXE=Execução, CAD=Cadastros, ADM=Administração, REL=Relatórios, MON=Monitoramento, AUT=Autenticação, INT=Integrações).
  - `NNN`: número sequencial com 3 dígitos (001, 002, ...).
  - `nome_modulo`: minúsculas com underscores.
- Use `docs/business/Template_Especificacao_Modulo.md` para cada módulo.
- Se um módulo não tiver, por exemplo, workflow BPMN definido, sinalize com: `[A DEFINIR — validar com stakeholder]`.
- **Ação:** Use `write_file` para salvar cada módulo em `docs/business/specs/`.

### 4. Matriz de Rastreabilidade
- Produza uma tabela markdown indicando a origem de cada seção principal:

| Seção/Documento Gerado | Arquivo(s) de Origem em `ingestion/` |
|------------------------|--------------------------------------|
| Visão — Seção 1.2      | manual_processos_v3.pdf (p.4-7)      |
| Visão — Seção 1.4      | ata_reuniao_06-06.md                 |
| MOD-PLN-001 — RF       | regulamento_organizacional.md        |

---

## ⚠️ REGRAS CRÍTICAS DE EXECUÇÃO

1. **Zero Alucinação:** NÃO invente requisitos, funcionalidades ou regras. Tudo deve ter origem EXPLÍCITA na documentação de `ingestion/`.
2. **Gestão de Conflitos:** Se houver informação conflitante entre documentos, registre o conflito no documento de saída e solicite esclarecimento. Não escolha um lado arbitrariamente.
3. **Tom e Linguagem:** Use linguagem formal, institucional e objetiva. Mantenha consistência terminológica em todos os arquivos gerados.
4. **Idempotência e Segurança de Arquivo:** ANTES de usar `write_file`, verifique se o arquivo de destino já existe. Se existir, **PARE** e pergunte ao usuário: *"O arquivo [nome_do_arquivo] já existe. Deseja sobrescrevê-lo ou gerar uma nova versão com sufixo `_v2`?"*. Aguarde a resposta.
5. **Lacunas de Template:** Se um conceito importante aparecer na ingestão mas não houver seção correspondente no template, adicione uma nota na seção mais próxima do template.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os arquivos via `write_file`, **PARE A GERAÇÃO AUTOMÁTICA** e apresente apenas este resumo estruturado no chat:

1. **Nome do sistema e objetivo principal** (1 frase).
2. **Módulos identificados:** Lista com os nomes dos arquivos `MOD-...` gerados.
3. **Lacunas:** Quais seções ficaram com placeholders `[NÃO IDENTIFICADO...]`.
4. **Conflitos:** Quais conflitos foram encontrados na documentação de `ingestion`.
5. **Próximos Passos:** 3 a 5 sugestões de perguntas objetivas para validação humana com o stakeholder.

**NÃO prossiga para o próximo passo do pipeline. Aguarde explicitamente pela validação humana.**