# Paralelo entre o artigo "Cheap Code, Costly Judgment" e o workflow LLC

## Objetivo

Este documento compara o artigo [`article.md`](../article.md) com a documentacao principal do LLC:

- [`README.md`](../README.md)
- [`LLC_GUIDE.md`](../LLC_GUIDE.md)
- [`llc-pipeline-design.md`](../llc-pipeline-design.md)

O foco e identificar:

1. convergencias entre o artigo e o LLC;
2. lacunas expostas pelo artigo;
3. oportunidades concretas de evolucao da metodologia.

## Tese central do artigo

O artigo defende que, na era agentic, codigo fica barato e julgamento fica caro. O problema central deixa de ser "a IA consegue gerar codigo?" e passa a ser "como organizar arquitetura, contexto, controles, evidencias e feedback loops para que a velocidade agentic continue governavel?".

A contribuicao principal do artigo e a ideia de **governance conversion**:

`falha recorrente -> interpretacao humana -> governanca duravel -> restricao para agentes futuros`

Ou seja, progresso sustentavel nao vem apenas de prompts melhores ou revisao humana constante. Vem da capacidade de converter falhas reais em:

- arquitetura;
- controles;
- guardrails;
- tipos;
- lints;
- testes;
- gates;
- melhores mecanismos de contexto e despacho.

## Leitura do LLC a luz do artigo

O LLC ja esta conceitualmente muito proximo da visao do artigo. Ele nao trata desenvolvimento agentico apenas como automacao de implementacao; trata como um sistema governado por artefatos, gates, skills, harness, memoria e validacoes.

Isso aparece com clareza em alguns pilares da metodologia:

- documentacao como codigo;
- humano no controle;
- rastreabilidade total;
- paralelismo por PRPs;
- harness com sessao ACE;
- gates de validacao humana;
- fitness functions e validacoes deterministicas;
- seguranca, cobertura, PRP verify e hardening em camadas.

Em outras palavras: o LLC ja e mais "governance-centric" do que "velocity-centric".

## Convergencias fortes

### 1. Governanca no ambiente, nao na revisao humana continua

O artigo argumenta que revisao humana dentro do loop de implementacao satura em alta velocidade. O LLC vai na mesma direcao ao empurrar qualidade para o ambiente atraves de:

- `pre-commit.sh`
- `llm-validation.sh`
- `fitness-functions.py`
- `prp_verify`
- gates formais ao longo do pipeline

Essa e uma convergencia estrutural importante: ambos rejeitam a ideia de que revisar manualmente tudo seja um mecanismo escalavel.

### 2. Sistema legivel por agentes

O artigo valoriza um `agent-legible governance substrate`. O LLC constroi exatamente isso com:

- `AGENTS.md` e `CLAUDE.md`
- skills versionadas em `docs/skills/`
- templates explicitos
- artefatos padronizados
- `.ace/index.json`, sessoes, memoria e scripts de orquestracao

O conhecimento necessario para o agente atuar nao fica apenas em acordos sociais; ele e externalizado em arquivos e scripts.

### 3. Combinacao de controles probabilisticos e deterministicos

O artigo distingue controles "soft" de controles deterministas. O LLC tambem opera nessa combinacao:

- probabilisticos: skills, prompts, regras em arquivos de steering, orientacoes do harness;
- deterministicos: hooks, validacoes, fitness functions, coverage gate, gates de merge/execucao.

Essa mistura e uma das maiores forcas da metodologia.

### 4. Arquitetura e controle como respostas a falhas

O artigo mostra que falhas recorrentes podem ser tratadas de dois jeitos:

- por construcao: arquitetura que impede a falha;
- por deteccao: controles que barram ou revelam a falha cedo.

O LLC ja possui ambos os modos:

- arquitetura: Step 5, 5a, 5b, 5c, 5d, 8b, 10.9;
- controle: Gates, coverage, seguranca, null safety, PRP verify, arch fitness.

### 5. Velocidade com contencao

O artigo critica aceleracao sem controle. O LLC tenta resolver isso com:

- PRPs autocontidos;
- execution waves;
- git worktrees;
- smart skip no fluxo Delta;
- checkpoints QA e gates progressivos.

Isso esta bastante alinhado com a nocao de "governed throughput" do artigo.

## Onde o artigo expoe lacunas no LLC

### 1. O LLC e muito forte em governanca ex-ante, mas ainda menos explicito em governanca ex-post

O artigo insiste que muitos controles importantes nao sao conhecidos antes da execucao; eles sao descobertos durante o trabalho agentico. O LLC contempla aprendizado via ACE, Delta, learning points e evolucao do harness, mas esse loop ainda nao aparece como ritual central da metodologia.

Em resumo:

- o LLC planeja muito bem;
- o artigo mostra que tambem e preciso institucionalizar o aprendizado vindo das falhas.

### 2. Falta um protocolo formal de "failure -> governance conversion"

Hoje o LLC possui os ingredientes, mas ainda nao parece ter um subfluxo obrigatorio que diga:

1. detectar falha recorrente;
2. classificar se a falha e local ou estrutural;
3. decidir se a resposta correta e arquitetura, controle ou ambos;
4. instalar o mecanismo;
5. registrar a mudanca;
6. medir se houve reducao da reincidencia.

Esse ponto e provavelmente a principal contribuicao pratica que o artigo sugere para o LLC.

### 3. Context injection pode evoluir de contextualizacao geral para contextualizacao cirurgica

O artigo destaca `dynamic context injection`: selecionar apenas as restricoes e convencoes relevantes para o alvo da mudanca. O LLC ja usa contexto comprimido, hierarchy e harness, mas pode avancar para um despacho mais preciso por:

- modulo;
- arquivos afetados;
- PRP;
- regras de arquitetura aplicaveis;
- lints e gates relevantes;
- historico de falhas daquela area.

### 4. Falta metrificar governabilidade acumulada

O artigo sugere que o indicador correto nao e volume de codigo nem numero de tarefas, mas capacidade de transformar atividade agentic em progresso duravel. O LLC tem metricas de fluxo e qualidade, mas ainda pode ganhar metricas de governanca acumulada.

## Melhorias propostas para o LLC

### Prioridade 1 - Criar um subfluxo oficial de Governance Conversion

Adicionar um step ou substep formal, por exemplo `11.4 Governance Conversion`, com o seguinte fluxo:

1. registrar falha observada;
2. classificar `local` ou `estrutural`;
3. escolher resposta:
   - ajuste pontual;
   - novo guardrail;
   - nova regra arquitetural;
   - novo teste/lint/fitness function;
   - novo padrao de briefing;
4. registrar artefato de governanca;
5. validar em gate proprio;
6. promover para harness, docs ou arquitetura.

### Prioridade 2 - Criar um artefato para falhas estruturais

Criar algo como:

- `docs/governance/GOV-001-<nome>.md`

Campos sugeridos:

- sintoma;
- contexto;
- classe de falha;
- impacto;
- evidencia;
- causa estrutural;
- decisao tomada;
- mecanismo instalado;
- area afetada;
- validacao posterior;
- status da reincidencia.

### Prioridade 3 - Formalizar a distincao entre controles probabilisticos e deterministicos

Essa classificacao pode aparecer na documentacao do LLC para esclarecer o papel de cada mecanismo:

- probabilisticos: skills, prompts, steering files, brief templates;
- deterministicos: hooks, lints, testes, types, fitness functions, merge/deploy gates.

Isso ajuda a evitar expectativas erradas sobre o que cada camada realmente garante.

### Prioridade 4 - Implementar context injection por impacto

O harness pode montar o contexto do agente com base em:

- PRP atual;
- arquivos-alvo;
- modulo do dominio;
- regras de arquitetura do modulo;
- gates e checks aplicaveis;
- falhas historicas relacionadas.

Isso reduz custo, ruido e retrabalho.

### Prioridade 5 - Medir "governed throughput"

Criar metricas novas, por exemplo:

- `failure_to_control_lead_time`
- `structural_failure_recurrence_rate`
- `governed_throughput`
- `guardrail_coverage_by_module`
- `time_to_harden_after_first_failure`

Essas metricas aproximam o LLC da tese do artigo de que o alvo nao e apenas velocidade, mas velocidade governavel.

### Prioridade 6 - Definir autoridade para alterar a governanca

O artigo mostra que falhas estruturais persistem quando quem enxerga o problema nao consegue mudar o ambiente. O LLC pode explicitar:

- quem pode promover uma falha em novo guardrail;
- quando isso exige ADR;
- quando basta update de harness;
- quando vira nova fitness function;
- quando deve alterar skill/template.

### Prioridade 7 - Consolidar observabilidade agentica

O artigo trata observabilidade como parte da governanca. O LLC pode fortalecer esse eixo com um inventario mais claro de:

- sessoes;
- worktrees ativas;
- waves em execucao;
- checkpoints falhos;
- guardrails disparados;
- reincidencias por modulo.

## Avaliacao final

O artigo nao contradiz o LLC; ele reforca a direcao geral da metodologia.

A principal conclusao deste paralelo e:

> O LLC ja e forte como sistema de governanca ex-ante e de validacao em camadas, mas pode evoluir bastante se transformar a **governanca ex-post descoberta por falhas** em um componente explicito, rastreavel e mensuravel da metodologia.

Em termos praticos, a melhor evolucao para o LLC nao parece ser "mais steps", e sim um novo loop oficial de endurecimento:

`execucao -> falha estrutural -> conversao em governanca -> propagacao para proximas execucoes`

Se esse loop for institucionalizado, o LLC tende a ficar menos dependente de operadores muito experientes e mais capaz de acumular maturidade de forma reutilizavel.

## Recomendacao

Como proximo passo, vale transformar esta analise em uma proposta metodologica concreta, por exemplo:

- um ADR da metodologia;
- um novo documento `docs/governance-conversion.md`;
- ou uma extensao do `llc-pipeline-design.md` com um novo substep dedicado.
