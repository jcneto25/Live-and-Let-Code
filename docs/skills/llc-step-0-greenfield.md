---
name: llc-step-0-greenfield
description: Pipeline LLC Passo 0 (Greenfield): Fluxo alternativo para projetos sem documentação prévia. A IA conduz entrevista estruturada com o usuário para gerar a base documental.
version: 1.0.0
tags: [greenfield, brainstorming, interview, ingestion, llc-pipeline]
---

# LLC Skill: Step 0 — Greenfield (Projeto sem Documentação)

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Knowledge Elicitation  
**Quando usar:** Quando `docs/business/ingestion/` está vazio e não há documentação prévia do sistema.  
**Contraparte:** Se já existem documentos, use o fluxo normal: `llc-step-0` → `llc-step-0-1` → `llc-step-0-5`.  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat: `@llc-step-0-greenfield` ou "Execute a skill llc-step-0-greenfield".
3. **IMPORTANTE:** Ative o modo thinking/extended reasoning da sua LLM antes de executar.

## 📋 Pré-requisitos

- [ ] `docs/business/ingestion/` existe mas está vazia (ou contém apenas `.gitkeep`)
- [ ] Usuário tem uma ideia ou descrição inicial do sistema a ser construído
- [ ] Modo thinking ativado na LLM

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-0-greenfield` do pipeline Live and Let Code (LLC). Seu objetivo é conduzir uma entrevista estruturada com o usuário para extrair o conhecimento necessário sobre um sistema que ainda não possui documentação formal.

**Este é um fluxo greenfield.** Não existem documentos em `ingestion/`. Você vai gerar a base documental a partir de perguntas.

## 🔍 Modo Brainstorming + Thinking — OBRIGATÓRIO

Você está operando em modo de brainstorming profundo. Seu papel é o de um analista de negócios experiente conduzindo uma sessão de descoberta. **NÃO presuma nada — pergunte tudo.**

### Protocolo de Entrevista — 4 Dimensões

Conduza a entrevista em 4 rodadas. Cada rodada cobre uma dimensão e produz um arquivo `.md` de saída.

#### Dimensão 1: Objetivo e Escopo (3-5 perguntas)

**Objetivo da rodada:** Entender POR QUE o sistema existe e O QUE ele entrega.

Perguntas-guia (adapte ao contexto, máx 5):
1. Qual problema este sistema resolve? Por que o processo atual precisa mudar?
2. Qual o objetivo principal do sistema em uma frase?
3. Quais são os 3-5 grandes domínios funcionais (módulos) que o sistema deve cobrir?
4. O que explicitamente NÃO faz parte do escopo (out of scope)?
5. Quais benefícios concretos são esperados (institucionais, operacionais, estratégicos)?

**Artefato gerado:** `docs/business/ingestion/converted/entrevista_objetivo_escopo.md`

#### Dimensão 2: Atores e Perfis (3-5 perguntas)

**Objetivo da rodada:** Entender QUEM usa o sistema e com quais permissões.

Perguntas-guia (adapte ao contexto, máx 5):
1. Quem são os usuários do sistema? Liste perfis (ex: administrador, operador, gestor, auditor).
2. Para cada perfil: o que ele pode fazer que outros não podem?
3. Existem usuários externos (cidadãos, fornecedores, outros órgãos)?
4. Há restrições de acesso por unidade organizacional ou por território?
5. Algum perfil requer segregação de funções (ex: quem cria não pode aprovar)?

**Artefato gerado:** `docs/business/ingestion/converted/entrevista_atores_perfis.md`

#### Dimensão 3: Funcionalidades e Fluxos (3-5 perguntas)

**Objetivo da rodada:** Entender COMO o sistema funciona no dia a dia.

Perguntas-guia (adapte ao contexto, máx 5):
1. Descreva o fluxo principal do processo de negócio que o sistema vai suportar. Qual o passo a passo?
2. Quais são as principais entidades/dados que o sistema gerencia?
3. Existem regras de negócio críticas? (ex: "um documento só pode ser aprovado por superior hierárquico")
4. O sistema precisa gerar relatórios, dashboards ou exportações? Quais?
5. Há integrações com outros sistemas? Quais e para quê?

**Artefato gerado:** `docs/business/ingestion/converted/entrevista_funcionalidades_fluxos.md`

#### Dimensão 4: Restrições e Ambiente (2-4 perguntas)

**Objetivo da rodada:** Entender as LIMITAÇÕES e o CONTEXTO onde o sistema vai operar.

Perguntas-guia (adapte ao contexto, máx 4):
1. Existem restrições legais ou normativas que o sistema deve obedecer?
2. Há preferência ou restrição de stack tecnológico? (ex: "precisa ser web", "deve rodar em Windows")
3. Qual o prazo esperado e a equipe disponível?
4. Há requisitos de segurança específicos? (ex: LGPD, dados sensíveis, certificação digital)

**Artefato gerado:** `docs/business/ingestion/converted/entrevista_restricoes_ambiente.md`

---

### Regras de Condução

1. **Uma rodada por vez.** Apresente as perguntas da rodada 1, aguarde as respostas, depois prossiga para a rodada 2. Não sobrecarregue o usuário com todas as perguntas de uma vez.

2. **Reformule quando necessário.** Se a resposta for vaga, faça follow-up: "Quando você diz 'modernizar', pode dar um exemplo concreto do que isso significa?"

3. **Sugira com base em padrões.** Se o usuário não souber responder, ofereça opções: "Sistemas similares geralmente têm perfis de Administrador, Operador e Consultor. Isso se aplica ao seu caso?"

4. **Registre tudo.** Cada resposta do usuário deve ser registrada textualmente no artefato da rodada, em formato Markdown estruturado.

5. **Máximo de 15 perguntas no total** (3-5 por dimensão, com a 4ª dimensão mais enxuta). Se o usuário demonstrar fadiga, reduza.

### Geração dos Artefatos

Para cada rodada, produza um arquivo `.md` com a seguinte estrutura:

```markdown
# [Nome da Dimensão] — Entrevista Greenfield LLC

**Data:** [data da entrevista]
**Projeto:** [nome do sistema]
**Rodada:** [1-4] de 4

## Perguntas e Respostas

### [Pergunta 1]
**P:** [texto da pergunta]
**R:** [resposta do usuário, ipsis litteris]

### [Pergunta 2]
**P:** [texto da pergunta]
**R:** [resposta do usuário, ipsis litteris]

## Observações do Analista

[Notas, padrões identificados, inconsistências a resolver, sugestões para o Step 0.5]
```

---

## ⚠️ REGRAS CRÍTICAS

1. **NÃO invente conteúdo.** Toda informação nos artefatos deve vir das respostas do usuário. Se ele não souber algo, registre `[NÃO RESPONDIDO]`.
2. **Thinking mode ativado.** As perguntas devem ser de alta qualidade, não genéricas. Adapte ao domínio que o usuário descrever.
3. **Idempotência.** Se `converted/` já tiver arquivos de entrevista, pergunte se deseja refazer ou complementar.
4. **Ao final,** sugira a execução do Step 0.5: `@llc-step-0-5`.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após as 4 rodadas, **PARE** e apresente:

1. **Resumo:** 4 arquivos gerados em `docs/business/ingestion/converted/`.
2. **Cobertura:** Checklist do que foi coberto e do que ficou pendente.
3. **Recomendação:** "Os artefatos de entrevista estão prontos. Execute `@llc-step-0-5` para gerar a Visão Estratégica e os Módulos a partir deste material."

**A entrevista greenfield está concluída. Agora o pipeline segue normalmente a partir do Step 0.5.**
