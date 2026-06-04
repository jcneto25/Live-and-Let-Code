# Especificação Formal de Requisitos – [NOME DO SISTEMA]

> **Como usar este template:** substitua os campos entre colchetes `[...]` pelas informações do seu projeto. Mantenha a numeração hierárquica dos códigos (RF, RN, RNF) e ajuste ou remova as seções que não se aplicam ao seu contexto.

---

## 1. Finalidade

**RQ-001.** Este documento especifica, em formato formal e enumerado, os requisitos funcionais (RF), regras de negócio (RN) e requisitos não funcionais (RNF) do [NOME DO SISTEMA], sistema destinado a [DESCRIÇÃO RESUMIDA DO PROPÓSITO DO SISTEMA].

**RQ-002.** O sistema deverá atender à visão de [VISÃO ESTRATÉGICA DO PRODUTO], suportando [PRINCIPAIS CAPACIDADES ESPERADAS: rastreabilidade, segurança, integração, etc.].

---

## 2. Escopo Geral

**RQ-003.** O [NOME DO SISTEMA] deverá abranger, no mínimo, os seguintes domínios funcionais: [DOMÍNIO 1], [DOMÍNIO 2], [DOMÍNIO 3], [DOMÍNIO N].

**RQ-004.** O ciclo macro do sistema deverá contemplar a seguinte sequência de valor: [ETAPA 1] → [ETAPA 2] → [ETAPA 3] → [ETAPA N].

---

# 3. Requisitos Funcionais (RF)

## 3.1. Segurança, Administração e Controle de Acesso

**RF-ADM-001.** O sistema deverá suportar autenticação por [MECANISMO: LDAP/AD, SSO, OAuth 2.0, etc.], com login local apenas para contingência.

**RF-ADM-002.** O sistema deverá utilizar controle de acesso baseado em [RBAC / ABAC / híbrido], contemplando restrições por [perfil, unidade, contexto, papel no processo, etc.].

**RF-ADM-003.** O sistema deverá permitir o cadastro, atualização, inativação e bloqueio de usuários, com vínculo à [unidade organizacional / cargo / e-mail institucional / status funcional].

**RF-ADM-004.** O sistema deverá suportar, no mínimo, os seguintes perfis de acesso: [PERFIL 1], [PERFIL 2], [PERFIL 3], [PERFIL N].

**RF-ADM-005.** O sistema deverá suportar delegações temporárias de atribuições, com identificação de delegante, delegado, período e justificativa.

**RF-ADM-006.** O sistema deverá aplicar segregação de funções, impedindo que [EXEMPLO: o mesmo usuário execute e aprove a mesma ação].

**RF-ADM-007.** O sistema deverá classificar informações e documentos nos níveis: [público / restrito / confidencial / sigiloso] ou conforme política institucional aplicável.

**RF-ADM-008.** O sistema deverá registrar trilha de auditoria para autenticação, inclusões, alterações, exclusões lógicas, aprovações e publicações.

---

## 3.2. Cadastros e Base de Configuração

**RF-CAD-001.** O sistema deverá manter cadastro de [ENTIDADE PRINCIPAL], contemplando atributos como [ATRIBUTO 1], [ATRIBUTO 2], [ATRIBUTO N].

**RF-CAD-002.** O sistema deverá suportar a hierarquia: [NÍVEL 1] → [NÍVEL 2] → [NÍVEL 3] → [NÍVEL N].

**RF-CAD-003.** O sistema deverá permitir vinculação de [ENTIDADE A] a [ENTIDADE B] para fins de [FINALIDADE DA ASSOCIAÇÃO].

**RF-CAD-004.** O sistema deverá manter [BANCO/REPOSITÓRIO DE RECURSO REUTILIZÁVEL], classificado por [ATRIBUTOS DE CLASSIFICAÇÃO].

**RF-CAD-005.** O sistema deverá permitir parametrização de [TIPOS / TABELAS DE DOMÍNIO], incluindo: [PARÂMETRO 1], [PARÂMETRO 2], [PARÂMETRO N].

**RF-CAD-006.** O sistema deverá suportar templates e modelos documentais parametrizáveis para: [DOCUMENTO 1], [DOCUMENTO 2], [DOCUMENTO N].

---

## 3.3. [MÓDULO 1 – ex.: Planejamento]

**RF-[SIG]-001.** O sistema deverá permitir [FUNCIONALIDADE PRINCIPAL DO MÓDULO], com workflow contendo as etapas: [ETAPA 1], [ETAPA 2], [ETAPA N].

**RF-[SIG]-002.** O sistema deverá permitir versionamento, aprovação e controle de alterações formais de [ENTIDADE GERENCIADA].

**RF-[SIG]-003.** O sistema deverá calcular/manter [CÁLCULO OU INDICADOR PRINCIPAL], considerando [VARIÁVEIS ENVOLVIDAS].

**RF-[SIG]-004.** O sistema deverá permitir simulação de cenários, incluindo [VARIAÇÃO 1], [VARIAÇÃO 2] e [VARIAÇÃO N].

**RF-[SIG]-005.** O sistema deverá gerar alertas automáticos para [EVENTO OU CONDIÇÃO QUE DISPARA O ALERTA].

> 💡 *Duplique esta seção para cada módulo adicional do sistema, ajustando o sigla e os requisitos.*

---

## 3.4. [MÓDULO 2 – ex.: Execução / Operação]

**RF-[SIG]-001.** O sistema deverá permitir a abertura e gestão de [OBJETO OPERACIONAL], com registro de [ATRIBUTOS ESSENCIAIS].

**RF-[SIG]-002.** O sistema deverá manter registro de [EVENTO OPERACIONAL] com data, hora, responsável, resultado e evidência associada.

**RF-[SIG]-003.** O sistema deverá controlar o status de [OBJETO] por meio de workflow com as etapas: [ETAPA 1] → [ETAPA 2] → [ETAPA N].

**RF-[SIG]-004.** O sistema deverá permitir upload, download e gestão de evidências/documentos com controle de versão e assinatura eletrônica.

**RF-[SIG]-005.** O sistema deverá suportar requisição de informações externas, com rastreio de solicitação, prazo, resposta e pendência.

---

## 3.5. [MÓDULO 3 – ex.: Resultados / Achados]

**RF-[SIG]-001.** O sistema deverá registrar [RESULTADO PRINCIPAL] com os atributos: tipo, descrição, [CRITÉRIO], [CAUSA], [EFEITO], risco associado, gravidade e recomendação.

**RF-[SIG]-002.** O sistema deverá suportar workflow de validação de [RESULTADO], com etapas de: elaboração, revisão, aprovação e encaminhamento.

**RF-[SIG]-003.** O sistema deverá permitir encaminhamento de [RESULTADO] para manifestação formal da [PARTE INTERESSADA] antes da publicação.

**RF-[SIG]-004.** O sistema deverá registrar a análise e a decisão sobre as manifestações recebidas, com justificativa.

**RF-[SIG]-005.** O sistema deverá gerar automaticamente quadro consolidado de resultados, incluindo: [CAMPO 1], [CAMPO 2], responsáveis, prazos e status.

**RF-[SIG]-006.** O sistema deverá identificar automaticamente reincidência de [TIPO DE PROBLEMA] por [AGRUPAMENTO: unidade, processo, causa, etc.].

---

## 3.6. Relatórios, Comunicação e Publicação

**RF-REL-001.** O sistema deverá emitir, no mínimo, os seguintes tipos de documentos: [DOCUMENTO 1], [DOCUMENTO 2], [DOCUMENTO N].

**RF-REL-002.** O sistema deverá montar automaticamente o [DOCUMENTO PRINCIPAL] com estrutura padronizada e anexos referenciados.

**RF-REL-003.** O sistema deverá suportar múltiplos templates de [DOCUMENTO] por tipo de [PROCESSO / CONTEXTO].

**RF-REL-004.** O sistema deverá implementar fluxo de publicação com, no mínimo: rascunho, revisão, aprovação, ciência e publicação.

**RF-REL-005.** O sistema deverá suportar assinatura eletrônica [INSTITUCIONAL / DIGITAL / ICP-BRASIL] e integração com [ASSINADOR / SISTEMA EXTERNO].

**RF-REL-006.** O sistema deverá controlar visibilidade de documentos conforme: perfil de acesso, classificação da informação, unidade e papel do usuário.

---

## 3.7. Monitoramento e Acompanhamento

**RF-MON-001.** O sistema deverá manter cadastro de [ITENS EM MONITORAMENTO] contendo: código, descrição, responsável, unidade, prazo e status.

**RF-MON-002.** O sistema deverá permitir registro de [PLANO DE AÇÃO / RESPOSTA] com: ação, responsável, prazo, recursos e indicador de conclusão.

**RF-MON-003.** O sistema deverá suportar workflow de [PLANO DE AÇÃO]: elaboração, análise, aprovação, execução e validação.

**RF-MON-004.** O sistema deverá suportar ciclos de monitoramento periódico, contínuo e extraordinário.

**RF-MON-005.** O sistema deverá manter histórico de evolução de status ao longo do tempo, com rastreabilidade completa.

**RF-MON-006.** O sistema deverá registrar avaliação de [IMPLEMENTAÇÃO / EFETIVIDADE] baseada em evidências, consistência e abrangência.

**RF-MON-007.** O sistema deverá retroalimentar automaticamente [MÓDULO DE PLANEJAMENTO / RISCO] com os dados de efetividade do monitoramento.

---

## 3.8. Indicadores, Dashboards e Analytics

**RF-IND-001.** O sistema deverá calcular e exibir, no mínimo, os seguintes indicadores: [INDICADOR 1], [INDICADOR 2], [INDICADOR N].

**RF-IND-002.** O sistema deverá disponibilizar dashboards por perfil, com visões de: [VISÃO 1 – ex.: executiva], [VISÃO 2 – ex.: operacional], [VISÃO N].

**RF-IND-003.** O sistema deverá permitir exportação de dados e relatórios nos formatos: PDF, XLSX e [FORMATO ADICIONAL].

**RF-IND-004.** O sistema deverá suportar filtros e agrupamentos por: [DIMENSÃO 1], [DIMENSÃO 2], período e [DIMENSÃO N].

**RF-IND-005.** O sistema deverá disponibilizar API ou mecanismo de integração para consumo de dados por sistemas de BI externos [se aplicável].

---

# 4. Regras de Negócio (RN)

**RN-001.** [DESCRIÇÃO DA REGRA DE NEGÓCIO 1 – obrigações, restrições ou cálculos que governam o comportamento do sistema independentemente de interface].

**RN-002.** [DESCRIÇÃO DA REGRA DE NEGÓCIO 2].

**RN-003.** [DESCRIÇÃO DA REGRA DE NEGÓCIO 3].

> 💡 *Regras de negócio descrevem restrições ou obrigações do domínio. Ex.: "Não é permitido encerrar [OBJETO] sem ao menos um [ITEM OBRIGATÓRIO] associado."*

---

# 5. Requisitos Não Funcionais (RNF)

## 5.1. Desempenho

**RNF-DES-001.** O sistema deverá responder a consultas simples em até [X segundos] para [N% dos usuários simultâneos].

**RNF-DES-002.** O sistema deverá suportar [N usuários simultâneos] sem degradação de desempenho.

## 5.2. Disponibilidade e Continuidade

**RNF-DIS-001.** O sistema deverá ter disponibilidade mínima de [99,X%] no horário de [JANELA DE OPERAÇÃO].

**RNF-DIS-002.** O sistema deverá suportar plano de contingência e recuperação com RTO de [X horas] e RPO de [Y horas].

## 5.3. Segurança da Informação

**RNF-SEG-001.** O sistema deverá criptografar dados em trânsito utilizando [TLS 1.2+] e dados em repouso com [AES-256 ou equivalente].

**RNF-SEG-002.** O sistema deverá realizar backups automáticos com frequência mínima [diária/semanal] e retenção de [N dias].

**RNF-SEG-003.** O sistema deverá estar em conformidade com [LGPD / GDPR / norma aplicável].

## 5.4. Usabilidade e Acessibilidade

**RNF-USA-001.** O sistema deverá ter interface responsiva, compatível com navegadores [LISTA DE BROWSERS] e dispositivos [desktop / mobile / tablet].

**RNF-USA-002.** O sistema deverá atender ao nível de acessibilidade [WCAG 2.1 AA ou equivalente].

## 5.5. Manutenibilidade e Integrações

**RNF-MAN-001.** O sistema deverá disponibilizar APIs REST documentadas para integração com [SISTEMAS EXTERNOS].

**RNF-MAN-002.** O sistema deverá ser implantável em ambiente [on-premises / cloud / híbrido], com suporte a conteinerização [Docker/Kubernetes, se aplicável].

**RNF-MAN-003.** O sistema deverá possuir documentação técnica atualizada de arquitetura, APIs e procedimentos operacionais.

---

# 6. Restrições e Premissas

**RST-001.** [RESTRIÇÃO TECNOLÓGICA, LEGAL OU ORGANIZACIONAL – ex.: "O sistema deverá ser desenvolvido em tecnologia X conforme padrão institucional"].

**RST-002.** [PREMISSA – ex.: "Pressupõe-se que os dados históricos de [ENTIDADE] serão migrados antes da entrada em produção"].

**RST-003.** [DEPENDÊNCIA EXTERNA – ex.: "A funcionalidade Y depende da disponibilidade da API do sistema Z"].

---

# 7. Rastreabilidade

| Código RF/RN/RNF | Módulo | Fonte / Documento de Origem | Prioridade | Status |
|---|---|---|---|---|
| RF-ADM-001 | Administração | [Documento Fonte] | Alta | Pendente |
| RF-CAD-001 | Cadastros | [Documento Fonte] | Alta | Pendente |
| RF-[SIG]-001 | [Módulo] | [Documento Fonte] | Média | Pendente |
| RN-001 | [Módulo] | [Documento Fonte] | Alta | Pendente |
| RNF-SEG-001 | Segurança | [Documento Fonte] | Alta | Pendente |

> 💡 *Prioridade sugerida: Alta / Média / Baixa. Status sugerido: Pendente / Em desenvolvimento / Homologado / Cancelado.*

---

# 8. Validação de Completude

## Critérios de Aceite do Documento

1. Todos os domínios funcionais do escopo (seção 2) estão cobertos por ao menos um RF.
2. Todas as regras de negócio críticas estão formalizadas na seção 4.
3. Os RNFs cobrem, no mínimo: desempenho, disponibilidade, segurança e usabilidade.
4. A matriz de rastreabilidade (seção 7) está preenchida para todos os requisitos.
5. Não há requisitos ambíguos ou sem critério de verificação.

## Parecer Final

**Parecer:** *(A ser preenchido após revisão técnica e aprovação das partes interessadas.)*

---

*Documento gerado com base no padrão de especificação formal adotado. Versão: [X.Y] | Data: [DD/MM/AAAA] | Responsável: [NOME / ÁREA]*
