# Guia de Preenchimento — Template de Especificação Técnico-Funcional
## Volume I — Visão Estratégica e Negócio

Este guia explica **como preencher cada seção** do template de **Especificação Técnico-Funcional — Volume I: Visão Estratégica e Negócio**.

O objetivo é ajudar autores, analistas de negócio, gestores e equipes técnicas a produzir um documento **coerente, completo, rastreável e reutilizável**.

---

## 1. Como usar este guia

Para cada seção do template, este guia apresenta:
- **Finalidade da seção** — por que ela existe;
- **O que deve ser preenchido** — quais informações devem entrar;
- **Boas práticas** — como escrever melhor;
- **Erros comuns** — o que evitar;
- **Exemplo de preenchimento** — apenas ilustrativo.

> **Dica geral:** escreva de forma objetiva, institucional e verificável. Evite termos vagos como “melhorar bastante”, “modernizar tudo” ou “resolver todos os problemas”. Prefira formulações observáveis e auditáveis.

---

## 2. Orientações gerais de redação

### 2.1 Linguagem recomendada
- Use linguagem formal, clara e sem ambiguidades.
- Prefira frases curtas e objetivas.
- Use verbos no infinitivo para objetivos, escopo e benefícios: “automatizar”, “consolidar”, “padronizar”, “permitir”, “rastrear”.
- Mantenha consistência terminológica ao longo do documento.

### 2.2 Nível de detalhamento esperado
Este volume deve tratar da **visão estratégica e de negócio**, e não do detalhamento técnico de implementação.

Portanto:
- **inclua** contexto, objetivos, escopo, atores, processos, capacidades, princípios e indicadores;
- **não aprofunde excessivamente** em regras de tela, layouts, APIs, tabelas físicas, scripts ou detalhes de infraestrutura.

### 2.3 Critérios de qualidade do conteúdo
Antes de concluir o preenchimento, verifique se o texto está:
- **claro** — qualquer leitor institucional entende o que está sendo proposto;
- **completo** — não faltam informações essenciais;
- **coerente** — objetivos, escopo e benefícios se conectam entre si;
- **alinhado** — o documento conversa com a estratégia institucional;
- **evolutivo** — pode servir de base para volumes posteriores.

---

## 3. Guia de preenchimento por seção

## 3.1 Capa / Identificação do Documento

### Finalidade
Identificar formalmente o documento, sua versão e responsabilidade.

### O que preencher
- **Nome do sistema**;
- **Versão do documento**;
- **Data**;
- **Órgão ou unidade demandante**;
- **Responsável pelo documento**.

### Boas práticas
- Use nomenclatura oficial do projeto ou sistema.
- Controle a versão de forma explícita (ex.: 1.0, 1.1, 2.0).
- Se houver governança formal, inclua a unidade responsável pela manutenção do documento.

### Erros comuns
- Usar nome provisório em uma versão já oficial.
- Atualizar o conteúdo sem atualizar versão/data.
- Não identificar o responsável institucional.

### Exemplo
- **Sistema:** Sistema Corporativo de Gestão de Demandas Internas
- **Versão:** 1.0
- **Data:** 04/06/2026
- **Unidade Demandante:** Secretaria de Planejamento
- **Responsável:** Equipe de Transformação Digital

---

## 3.2 Seção 1 — Introdução

### 1.1 Objetivo do Documento

#### Finalidade
Explicar o que este documento é e para que ele servirá dentro do ciclo do projeto.

#### O que preencher
Descreva:
- o propósito do documento;
- seu papel como referência para etapas posteriores;
- os artefatos que dependerão dele.

#### Como escrever
Responda a estas perguntas:
- Este documento define o quê?
- Quem irá utilizá-lo?
- Quais entregas futuras dependem dele?

#### Boas práticas
- Deixe claro que este volume trata da **visão estratégica e de negócio**.
- Liste explicitamente os desdobramentos esperados, como requisitos, processos, dados e arquitetura.

#### Erros comuns
- Confundir objetivo do documento com objetivo do sistema.
- Escrever apenas uma frase genérica sem indicar uso prático.

#### Exemplo
“Este documento estabelece a visão estratégica, o escopo funcional e a arquitetura conceitual do sistema, servindo como base para requisitos funcionais, modelagem de processos, modelagem de dados e planejamento de desenvolvimento.”

---

### 1.2 Objetivo do Sistema

#### Finalidade
Explicar por que o sistema existe e qual problema institucional ele pretende resolver.

#### O que preencher
- a missão principal da solução;
- o valor esperado para a organização;
- o tipo de atividade que será apoiada;
- os resultados pretendidos em alto nível.

#### Como escrever
Use a fórmula:

**“Disponibilizar uma solução para [o quê], com a finalidade de [resultado], apoiando [atividade institucional].”**

#### Boas práticas
- Expresse o objetivo em termos de negócio, não em termos apenas tecnológicos.
- Mostre claramente o benefício institucional.

#### Erros comuns
- Descrever funcionalidades em vez de objetivo.
- Redigir algo genérico demais, como “informatizar processos”.

#### Exemplo
“Disponibilizar uma plataforma corporativa integrada para gestão do ciclo de atendimento ao cidadão, com rastreabilidade, padronização e monitoramento de desempenho.”

---

### 1.3 Escopo

#### Finalidade
Delimitar o que o sistema vai abranger funcionalmente.

#### O que preencher
Liste os **grandes domínios de atuação** do sistema e, dentro de cada domínio, os principais itens cobertos.

#### Como escrever
Organize o escopo por agrupamentos lógicos, por exemplo:
- planejamento;
- execução;
- monitoramento;
- governança;
- qualidade;
- administração.

#### Boas práticas
- Use domínios amplos e internamente coerentes.
- Liste itens suficientes para caracterizar a cobertura funcional.
- Se necessário, mantenha uma subseção interna separando **o que está dentro** e **o que está fora do escopo**.

#### Erros comuns
- Misturar escopo com cronograma.
- Listar módulos muito detalhados ou prematuros.
- Omitir áreas relevantes que depois aparecerão nos requisitos.

#### Exemplo
**Planejamento**
- cadastro do universo de trabalho;
- priorização;
- programação anual.

**Execução**
- abertura de ciclos;
- registros operacionais;
- produção de artefatos;
- supervisão.

---

### 1.4 Público-Alvo

#### Finalidade
Identificar quem utilizará o sistema ou será impactado por ele.

#### O que preencher
Separe, quando fizer sentido, os públicos em:
- **internos**;
- **externos**.

Inclua perfis, áreas, unidades, parceiros institucionais, órgãos de controle, usuários finais ou gestores.

#### Boas práticas
- Descreva grupos de usuários, não nomes de pessoas.
- Prefira papéis funcionais: “analistas”, “gestores”, “supervisores”, “unidades demandantes”.

#### Erros comuns
- Misturar usuários do sistema com beneficiários indiretos sem distinção.
- Escrever grupos vagos como “todos os setores”.

#### Exemplo
**Internamente**
- analistas da área;
- coordenadores;
- gestores da unidade.

**Externamente**
- unidades demandantes;
- órgãos de governança;
- público consultivo autorizado.

---

### 1.5 Benefícios Esperados

#### Finalidade
Explicitar os ganhos que justificam o investimento e a priorização do sistema.

#### O que preencher
Organize os benefícios em categorias, por exemplo:
- **institucionais**;
- **operacionais**;
- **estratégicos**.

#### Como escrever
Cada benefício deve responder a uma pergunta de valor, como:
- que problema será reduzido?
- que capacidade será ampliada?
- que decisão será melhor suportada?

#### Boas práticas
- Use benefícios verificáveis.
- Relacione benefícios com dores ou gargalos reais.
- Mantenha alinhamento entre benefícios e objetivos estratégicos.

#### Erros comuns
- Repetir o objetivo do sistema com palavras diferentes.
- Usar benefícios não mensuráveis ou exagerados.

#### Exemplo
**Institucionais**
- fortalecimento da governança;
- aumento da padronização.

**Operacionais**
- redução de retrabalho;
- eliminação de controles paralelos.

**Estratégicos**
- apoio à priorização baseada em dados;
- melhoria da transparência gerencial.

---

### 1.6 Premissas

#### Finalidade
Registrar condições assumidas como verdadeiras para viabilizar a solução.

#### O que preencher
Liste dependências institucionais, organizacionais, normativas ou tecnológicas consideradas existentes ou disponíveis.

#### Boas práticas
- Redija premissas de forma objetiva.
- Inclua apenas aquilo que realmente condiciona o sucesso do projeto.

#### Erros comuns
- Confundir premissa com requisito.
- Transformar desejo em premissa (“haverá total adesão de todos os usuários”).

#### Exemplo
- Existência de normativo vigente sobre o processo.
- Disponibilidade de infraestrutura tecnológica corporativa.
- Existência de unidade gestora formal do processo.

---

### 1.7 Restrições

#### Finalidade
Registrar limitações ou condicionantes obrigatórios do projeto.

#### O que preencher
Inclua restrições de:
- conformidade legal;
- segurança da informação;
- orçamento;
- tecnologia;
- prazos institucionais;
- sigilo;
- interoperabilidade.

#### Boas práticas
- Diferencie restrições de premissas: restrição limita; premissa sustenta.
- Registre apenas restrições reais e justificáveis.

#### Erros comuns
- Usar a seção para listar riscos.
- Descrever restrições vagas sem impacto concreto.

#### Exemplo
- observância obrigatória à legislação de proteção de dados;
- uso da infraestrutura homologada pelo órgão;
- respeito aos perfis de sigilo e trilhas de auditoria.

---

### 1.8 Glossário

#### Finalidade
Padronizar o significado dos principais termos usados no documento.

#### O que preencher
Inclua termos técnicos, institucionais, jurídicos ou operacionais que possam gerar interpretação ambígua.

#### Boas práticas
- Defina cada termo em linguagem simples.
- Priorize termos realmente relevantes para compreensão do sistema.
- Mantenha consistência com normativos institucionais.

#### Erros comuns
- Repetir definições óbvias ou desnecessárias.
- Inserir definições muito longas ou normativamente confusas.

#### Exemplo
**Demanda** — solicitação registrada no sistema para tratamento por unidade responsável.

**Evidência** — informação que comprova execução, decisão ou resultado de uma atividade.

---

### 1.9 Acrônimos

#### Finalidade
Facilitar a leitura do documento e padronizar siglas utilizadas.

#### O que preencher
Monte uma tabela com:
- sigla;
- descrição completa.

#### Boas práticas
- Inclua apenas siglas usadas no documento.
- Adote a forma oficial de cada acrônimo.

#### Erros comuns
- Usar sigla não listada na tabela.
- Duplicar siglas semelhantes sem distinção.

#### Exemplo
| Sigla | Descrição |
|---|---|
| PAA | Plano Anual de Atuação |
| BI | Business Intelligence |
| API | Application Programming Interface |

---

## 3.3 Seção 2 — Referencial Normativo

### Finalidade
Demonstrar a base legal, regulatória, metodológica e institucional que legitima e orienta a solução.

### O que preencher
Liste leis, resoluções, portarias, manuais, políticas, frameworks, normas técnicas e referenciais metodológicos relevantes.

### Como escrever
Para cada item, informe:
- nome do normativo ou referencial;
- breve explicação sobre sua relevância para o sistema.

### Boas práticas
- Comece pelos marcos legais mais amplos.
- Depois apresente normas institucionais e referenciais especializados.
- Mantenha ordem lógica ou hierárquica.

### Erros comuns
- Apenas citar normas sem explicar a relação com o sistema.
- Incluir normas sem aplicabilidade real.
- Omitir referências fundamentais de conformidade.

### Exemplo
**Lei Geral de Proteção de Dados**  
Estabelece princípios e obrigações para tratamento de dados pessoais, com impacto direto sobre perfis de acesso, guarda de informações e rastreabilidade.

**Política de Segurança da Informação do Órgão**  
Define requisitos institucionais obrigatórios para autenticação, controle de acesso e tratamento de ativos informacionais.

---

## 3.4 Seção 3 — Arquitetura de Negócio

### 3.1 Visão Geral

#### Finalidade
Apresentar uma visão executiva do processo ou ecossistema de negócio suportado pelo sistema.

#### O que preencher
Descreva o ciclo de negócio de ponta a ponta que a solução deverá apoiar.

#### Boas práticas
- Foque no fluxo institucional, não na tecnologia.
- Mostre início, meio e fim do processo.

#### Exemplo
“O sistema deverá suportar o ciclo completo de gestão de demandas, desde o registro inicial até a avaliação dos resultados e melhoria contínua.”

---

### 3.2 Modelo Operacional / Modelo de Governança

#### Finalidade
Explicar como os atores institucionais se organizam e interagem no contexto do sistema.

#### O que preencher
Descreva grupos, camadas, linhas, instâncias ou níveis organizacionais envolvidos, tais como:
- executores;
- supervisores;
- instâncias de governança;
- beneficiários externos.

#### Boas práticas
- Mostre responsabilidades de cada grupo.
- Destaque relações de supervisão, controle, validação ou decisão.

#### Erros comuns
- Descrever organograma completo em vez do arranjo funcional relevante.
- Omitir atores com papel decisório.

#### Exemplo
**Primeiro nível** — unidades executoras do processo.

**Segundo nível** — áreas de supervisão e conformidade.

**Terceiro nível** — instância de avaliação independente e consolidação gerencial.

---

### 3.3 Cadeia de Valor / Fluxo de Valor

#### Finalidade
Representar, em alto nível, as etapas que geram valor no processo de negócio.

#### O que preencher
Liste a sequência lógica das principais etapas, da origem até a entrega de resultado.

#### Boas práticas
- Use nomes curtos e compreensíveis.
- Mantenha o encadeamento lógico.
- Evite excesso de detalhes.

#### Exemplo
Demanda → Triagem → Priorização → Execução → Resultado → Monitoramento → Aprendizado institucional

---

### 3.4 Macroprocessos da Unidade/Área

#### Finalidade
Organizar o negócio em blocos funcionais amplos.

#### O que preencher
Liste e descreva os macroprocessos relevantes da área responsável ou do domínio atendido pelo sistema.

#### Boas práticas
- Um macroprocesso deve representar uma grande função de negócio.
- A descrição deve indicar propósito e escopo do macroprocesso.

#### Erros comuns
- Confundir macroprocesso com atividade específica.
- Criar macroprocessos redundantes.

#### Exemplo
**Planejamento** — define prioridades, metas e capacidade operacional.

**Execução** — realiza as atividades finalísticas do processo.

**Monitoramento** — acompanha resultados, pendências e efetividade.

---

### 3.5 Capacidades de Negócio

#### Finalidade
Indicar o que a organização precisa ser capaz de fazer com apoio do sistema.

#### O que preencher
Descreva capacidades institucionais como:
- priorizar;
- registrar;
- monitorar;
- analisar;
- reutilizar conhecimento;
- assegurar conformidade.

#### Boas práticas
- Escreva como “Capacidade de...”.
- Mantenha foco em negócio, não em funcionalidade de tela.

#### Erros comuns
- Listar apenas módulos do sistema.
- Confundir capacidade com indicador.

#### Exemplo
**Gestão do Conhecimento** — capacidade de armazenar, recuperar e reaproveitar informações institucionais relevantes.

---

### 3.6 Princípios Norteadores

#### Finalidade
Definir valores e diretrizes que devem orientar o desenho e a evolução da solução.

#### O que preencher
Liste princípios como:
- transparência;
- integridade;
- rastreabilidade;
- eficiência;
- acessibilidade;
- segurança;
- independência;
- melhoria contínua.

#### Boas práticas
- Cada princípio deve vir acompanhado de uma breve explicação aplicável ao sistema.
- Use princípios realmente úteis para orientar decisões posteriores.

#### Erros comuns
- Inserir princípios genéricos sem consequência prática.
- Repetir benefícios ou objetivos nesta seção.

#### Exemplo
**Rastreabilidade** — toda ação relevante no sistema deverá possuir histórico verificável.

---

### 3.7 Objetivos Estratégicos do Sistema

#### Finalidade
Traduzir a visão da solução em resultados estratégicos pretendidos.

#### O que preencher
Liste objetivos numerados (por exemplo, OE-01, OE-02 etc.) com formulações curtas e diretas.

#### Boas práticas
- Comece com verbo no infinitivo ou com formulação objetiva.
- Mantenha conexão direta com benefícios e indicadores.

#### Erros comuns
- Criar objetivos redundantes.
- Formular objetivos que não possam ser acompanhados.

#### Exemplo
- OE-01 — Padronizar o fluxo institucional de tratamento de demandas.
- OE-02 — Ampliar a transparência dos resultados.
- OE-03 — Melhorar a capacidade de priorização com base em dados.

---

### 3.8 Indicadores Estratégicos

#### Finalidade
Definir como os objetivos estratégicos poderão ser acompanhados.

#### O que preencher
Agrupe indicadores por perspectiva, dimensão ou macrotema, como:
- planejamento;
- execução;
- qualidade;
- governança;
- transparência.

#### Boas práticas
- Prefira indicadores objetivos e calculáveis.
- Sempre que possível, pense em fórmula, fonte de dados e periodicidade, mesmo que isso fique detalhado em outro volume.

#### Erros comuns
- Listar métricas sem relação com objetivos.
- Misturar indicadores com atividades.

#### Exemplo
**Execução**
- percentual de demandas concluídas no prazo;
- tempo médio de atendimento.

**Qualidade**
- índice de retrabalho;
- percentual de registros completos.

---

## 3.5 Seção 4 — Visão Macro da Solução

### 4.1 Domínios Funcionais

#### Finalidade
Apresentar uma decomposição ampla da solução em áreas funcionais.

#### O que preencher
Liste os principais domínios ou blocos funcionais esperados, sem entrar ainda em requisitos detalhados.

#### Boas práticas
- Use nomes claros e estáveis.
- Garanta compatibilidade entre domínios funcionais e escopo apresentado na introdução.

#### Erros comuns
- Detalhar excessivamente telas e menus.
- Criar domínios com sobreposição conceitual.

#### Exemplo
- Cadastro e parametrização;
- Planejamento;
- Execução;
- Monitoramento;
- Relatórios e painéis;
- Administração e segurança.

---

### 4.2 Fluxo Corporativo Principal

#### Finalidade
Consolidar, de forma sintética, o fluxo principal que a solução deverá apoiar.

#### O que preencher
Liste as etapas centrais do fluxo em sequência lógica.

#### Boas práticas
- Mantenha alinhamento com cadeia de valor e escopo.
- Use uma sequência compreensível por público técnico e negocial.

#### Erros comuns
- Criar fluxo divergente das seções anteriores.
- Inserir atividades periféricas como se fossem centrais.

#### Exemplo
Cadastro → Planejamento → Priorização → Execução → Consolidação → Monitoramento → Avaliação → Melhoria contínua

---

## 3.6 Seção 5 — Diretrizes para os Volumes Subsequentes

### Finalidade
Indicar quais temas deverão ser aprofundados nas próximas entregas documentais.

### O que preencher
Liste os artefatos ou conteúdos que serão detalhados em volumes subsequentes, como:
- requisitos funcionais;
- casos de uso;
- regras de negócio;
- perfis e permissões;
- modelo de dados;
- integrações;
- dashboards;
- critérios de aceitação;
- requisitos não funcionais.

### Boas práticas
- Use esta seção como ponte entre visão estratégica e detalhamento técnico-funcional.
- Garanta que os próximos volumes cubram tudo o que a visão macro prometeu.

### Erros comuns
- Repetir conteúdo técnico já detalhado neste volume.
- Omitir itens críticos para continuidade do projeto.

### Exemplo
“Os volumes subsequentes detalharão requisitos funcionais, regras de negócio, perfis de acesso, integrações, modelo conceitual de dados e critérios de aceite.”

---

## 4. Checklist final de revisão

Antes de finalizar o documento, verifique:

### Coerência estratégica
- [ ] O objetivo do sistema está claro?
- [ ] O escopo está alinhado aos benefícios esperados?
- [ ] Os objetivos estratégicos dialogam com os indicadores?

### Coerência documental
- [ ] Os termos do glossário aparecem de forma consistente?
- [ ] As siglas utilizadas foram listadas?
- [ ] O fluxo principal está coerente com os macroprocessos?

### Coerência institucional
- [ ] O referencial normativo está suficiente?
- [ ] As premissas e restrições estão realistas?
- [ ] O público-alvo foi identificado corretamente?

### Qualidade de redação
- [ ] O texto está objetivo e sem ambiguidades?
- [ ] Há excesso de detalhamento técnico indevido neste volume?
- [ ] O documento pode servir de base para próximos volumes?

---

## 5. Recomendações práticas de preenchimento

### Sequência recomendada de elaboração
1. Preencha a capa e a identificação do documento.
2. Redija objetivo do documento e objetivo do sistema.
3. Delimite o escopo.
4. Identifique os públicos-alvo.
5. Registre benefícios, premissas e restrições.
6. Monte glossário e acrônimos.
7. Estruture o referencial normativo.
8. Desenhe a arquitetura de negócio.
9. Defina a visão macro da solução.
10. Feche com as diretrizes dos volumes subsequentes.

### Sequência recomendada de validação
Valide o documento com três perspectivas:
- **negócio** — a área demandante confirma aderência do conteúdo;
- **governança** — a gestão confirma alinhamento institucional;
- **tecnologia** — a equipe técnica confirma viabilidade para desdobramento posterior.

---

## 6. Observação final

Este guia foi elaborado para apoiar o preenchimento de um template de **Visão Estratégica e Negócio**. Ele não substitui a validação institucional, jurídica, metodológica ou técnica necessária em cada projeto.

Quando houver conflito entre este guia e normativos oficiais do órgão, devem prevalecer os normativos e padrões institucionais vigentes.
