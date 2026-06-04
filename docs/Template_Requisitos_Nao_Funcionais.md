# ESPECIFICAÇÃO TÉCNICO-FUNCIONAL

# [NOME DO SISTEMA]

## VOLUME [XX] – REQUISITOS NÃO FUNCIONAIS

### Versão [X.X]

---

# 1. Objetivo

Este volume consolida os requisitos não funcionais do [NOME DO SISTEMA], reunindo especificações de performance, disponibilidade, segurança, escalabilidade, integração, usabilidade, manutenibilidade, conformidade legal, rastreabilidade, compatibilidade [e demais categorias relevantes ao projeto]. Os requisitos foram extraídos dos PRDs, volumes funcionais e especificações formais, complementados com valores de referência onde a documentação original era omissa.

---

# 2. Convenções

| Marca | Significado |
|-------|-------------|
| **[PRD]** | Requisito explicitamente declarado na documentação original |
| **[Inferido]** | Requisito derivado ou com valor de referência sugerido |

Cada requisito possui: ID, descrição, métrica/valor alvo, criticidade (Alta/Média/Baixa) e origem.

---

# 3. Performance (RNF-PERF)

**RNF-PERF-001.** [Descrição do requisito de performance. Ex.: As páginas de listagem deverão carregar em até X segundos para conjuntos de até N registros.] **[PRD/Inferido]**

**RNF-PERF-002.** [Descrição do requisito de performance.] **[PRD/Inferido]**

**RNF-PERF-003.** [Descrição do requisito de performance.] **[PRD/Inferido]**

**RNF-PERF-004.** [Descrição do requisito de performance.] **[PRD/Inferido]**

**RNF-PERF-005.** [Descrição do requisito de performance.] **[PRD/Inferido]**

---

# 4. Disponibilidade e Confiabilidade (RNF-DISP)

**RNF-DISP-001.** O sistema deverá ter disponibilidade mínima de **[XX,X%]** durante horário comercial ([horário] em dias úteis). **[PRD/Inferido]**

**RNF-DISP-002.** Módulos críticos [listar módulos] deverão ter disponibilidade de **[XX,X%]**. **[PRD/Inferido]**

**RNF-DISP-003.** Janelas de manutenção deverão ser agendadas fora do horário comercial, com comunicação prévia de no mínimo **[X horas/dias]**. **[Inferido]**

**RNF-DISP-004.** Backup deverá ser realizado com frequência **[diária (incremental) / semanal (completa) / outra]**, com cópia offsite. **[PRD/Inferido]**

**RNF-DISP-005.** O objetivo de tempo de recuperação (RTO) deverá ser inferior a **[X horas/minutos]**. **[Inferido]**

**RNF-DISP-006.** O objetivo de ponto de recuperação (RPO) deverá ser inferior a **[X horas/minutos]**. **[Inferido]**

**RNF-DISP-007.** Deverá existir plano de continuidade de negócio (BCP) específico para o sistema, com procedimentos documentados para falhas de infraestrutura, dados e segurança. **[PRD/Inferido]**

---

# 5. Segurança da Informação (RNF-SEGF)

**RNF-SEGF-001.** O sistema deverá suportar autenticação via **[LDAP/AD / SSO / SAML 2.0 / OIDC / outro]** institucional. **[PRD/Inferido]**

**RNF-SEGF-002.** Login local deverá ser permitido **apenas para contingência**, devidamente parametrizado e auditado. **[PRD/Inferido]**

**RNF-SEGF-003.** **MFA** deverá ser obrigatório para perfis críticos [listar perfis]. **[PRD/Inferido]**

**RNF-SEGF-004.** O controle de acesso deverá ser híbrido **[RBAC + ABAC / outro modelo]**, com restrições contextuais por [unidade, papel, nível de sigilo, etc.]. **[PRD/Inferido]**

**RNF-SEGF-005.** O sistema deverá garantir **segregação de funções**, impedindo: [listar conflitos de interesse específicos ao domínio]. **[PRD/Inferido]**

**RNF-SEGF-006.** O sistema deverá classificar informações em níveis: **[público, restrito, confidencial, sigiloso / ou outros níveis definidos pela instituição]**. **[PRD/Inferido]**

**RNF-SEGF-007.** A comunicação deverá utilizar **[TLS 1.3 / outro protocolo]** ou superior para todas as conexões. **[PRD/Inferido]**

**RNF-SEGF-008.** Dados sensíveis deverão ser criptografados em repouso com **[AES-256 / equivalente]**. **[PRD/Inferido]**

**RNF-SEGF-009.** O sistema deverá seguir as diretrizes **[OWASP ASVS / outro referencial]** para desenvolvimento seguro. **[Inferido]**

**RNF-SEGF-010.** O sistema deverá observar **[ISO 27001 / outra norma]** como referencial de gestão de segurança da informação. **[PRD/Inferido]**

**RNF-SEGF-011.** Senhas, quando utilizadas (contingência), deverão seguir política de complexidade institucional, com expiração e histórico. **[Inferido]**

**RNF-SEGF-012.** Sessões deverão ter timeout configurável (padrão: **[X minutos]** de inatividade), com renovação segura. **[Inferido]**

**RNF-SEGF-013.** O sistema deverá proteger-se contra as principais vulnerabilidades do **[OWASP Top 10 / outro referencial]**. **[Inferido]**

**RNF-SEGF-014.** Deverá existir controle de acesso baseado em **[IP/rede / outro critério]** para funções administrativas. **[Inferido]**

**RNF-SEGF-015.** Integrações com sistemas externos deverão utilizar autenticação mútua (mTLS) ou tokens JWT com rotação. **[Inferido]**

---

# 6. Escalabilidade (RNF-ESCA)

**RNF-ESCA-001.** A arquitetura deverá suportar **escalonamento horizontal** dos serviços de aplicação. **[PRD/Inferido]**

**RNF-ESCA-002.** O banco de dados deverá suportar estratégias de escalabilidade [read replicas, partitioning, connection pooling, etc.]. **[Inferido]**

**RNF-ESCA-003.** O armazenamento de arquivos deverá ser escalável independentemente do banco de dados relacional (object storage ou equivalente). **[Inferido]**

---

# 7. Interoperabilidade e Integração (RNF-INTE)

**RNF-INTE-001.** O sistema deverá adotar **arquitetura orientada a serviços e APIs RESTful**, com documentação **[OpenAPI 3.x / outro padrão]**. **[PRD/Inferido]**

**RNF-INTE-002.** Deverá integrar-se com **[LDAP/AD / SSO / outro sistema]** institucional para autenticação. **[PRD/Inferido]**

**RNF-INTE-003.** Deverá integrar-se com sistemas corporativos de **[RH / Financeiro / outro]** [descrever dados trocados]. **[PRD/Inferido]**

**RNF-INTE-004.** Deverá integrar-se com sistemas **[financeiros / orçamentários / outros]** [descrever dados trocados]. **[PRD/Inferido]**

**RNF-INTE-005.** Deverá integrar-se com plataformas de **[assinatura eletrônica / outro serviço]** [especificar padrão, ex.: ICP-Brasil]. **[PRD/Inferido]**

**RNF-INTE-006.** Deverá integrar-se com ferramentas de **[BI / outra plataforma]** para alimentação de dados analíticos. **[PRD/Inferido]**

**RNF-INTE-007.** Deverá suportar integração com sistemas de **[processos / outro domínio]** [descrever escopo]. **[PRD/Inferido]**

**RNF-INTE-008.** Integrações assíncronas deverão utilizar filas mensageiras (ex.: RabbitMQ, Kafka) para desacoplamento. **[Inferido]**

**RNF-INTE-009.** Cada integração deverá possuir SLA individual, com monitoramento de disponibilidade e latência. **[Inferido]**

**RNF-INTE-010.** O sistema deverá disponibilizar **webhooks** para notificação de eventos relevantes a sistemas externos. **[Inferido]**

---

# 8. Usabilidade e Acessibilidade (RNF-USAB)

**RNF-USAB-001.** A interface deverá seguir o **[e-MAG / WCAG 2.1 nível AA / outro padrão de acessibilidade]**. **[PRD/Inferido]**

**RNF-USAB-002.** A interface deverá ser **responsiva**, adaptando-se a diferentes resoluções de tela. **[Inferido]**

**RNF-USAB-003.** O idioma padrão deverá ser **[português brasileiro (PT-BR) / outro idioma]**. **[PRD/Inferido]**

**RNF-USAB-004.** A navegação deverá ser orientada por **[processo / função / outro critério]**, com fluxos distintos para [listar fluxos principais]. **[PRD/Inferido]**

**RNF-USAB-005.** Campos obrigatórios deverão ser visualmente identificados, com mensagens de validação claras. **[Inferido]**

**RNF-USAB-006.** O sistema deverá disponibilizar sistema de **notificações e alertas** por perfil, com indicadores visuais de ações pendentes. **[PRD/Inferido]**

**RNF-USAB-007.** A interface deverá seguir **padrão visual institucional** [descrever ou referenciar guia de identidade visual]. **[PRD/Inferido]**

---

# 9. Manutenibilidade (RNF-MANU)

**RNF-MANU-001.** O sistema deverá adotar **arquitetura modular**, com módulos independentes e interfaces bem definidas. **[PRD/Inferido]**

**RNF-MANU-002.** O design deverá ser **API-first**, com todas as funcionalidades acessíveis via API documentada. **[Inferido]**

**RNF-MANU-003.** O sistema deverá manter **versionamento nativo** dos objetos versionáveis [listar objetos]. **[PRD/Inferido]**

**RNF-MANU-004.** Deverá existir **segregação de ambientes** (desenvolvimento, homologação, produção) com processos formais de promoção. **[Inferido]**

**RNF-MANU-005.** A cobertura de testes automatizados deverá ser de no mínimo **[XX%]** para lógica de negócio crítica. **[Inferido]**

**RNF-MANU-006.** Parâmetros de configuração [listar tipos de parâmetros] deverão ser **parametrizáveis sem alteração de código**. **[PRD/Inferido]**

---

# 10. Conformidade Legal e Normativa (RNF-CONF)

**RNF-CONF-001.** O sistema deverá observar a **[LGPD / GDPR / outra legislação de proteção de dados]** para tratamento de dados pessoais. **[PRD/Inferido]**

**RNF-CONF-002.** O sistema deverá estar aderente às **[Resoluções / Normas / Regulamentos]** aplicáveis [listar normativos relevantes ao domínio]. **[PRD/Inferido]**

**RNF-CONF-003.** O sistema deverá observar a **[Lei de Acesso à Informação / outra legislação]** para classificação e disponibilização de informações. **[PRD/Inferido]**

**RNF-CONF-004.** O sistema deverá seguir as **[Normas Globais de Auditoria Interna / outro referencial]** e o modelo **[IA-CM / COSO / outro]**. **[PRD/Inferido]**

**RNF-CONF-005.** O sistema deverá observar as **políticas institucionais** de segurança da informação, gestão de riscos e governança [da instituição]. **[PRD/Inferido]**

---

# 11. Auditoria e Rastreabilidade (RNF-AUDI)

**RNF-AUDI-001.** Toda operação relevante deverá gerar **log auditável** contendo: data/hora, usuário, IP de origem, operação realizada, entidade e identificador do registro. **[PRD/Inferido]**

**RNF-AUDI-002.** Logs de auditoria deverão ser **imutáveis e permanentes** (política WORM — Write Once Read Many). **[PRD/Inferido]**

**RNF-AUDI-003.** Logs deverão ser retidos por no mínimo **[X anos]**, conforme requisitos institucionais e normativos. **[Inferido]**

**RNF-AUDI-004.** Toda exclusão deverá ser **lógica** (soft delete), sem remoção física de registros relevantes. **[PRD/Inferido]**

**RNF-AUDI-005.** O sistema deverá manter **trilha de decisões** (aprovações, rejeições, publicações, encerramentos) vinculada ao respectivo objeto e ao agente decisor. **[PRD/Inferido]**

---

# 12. Compatibilidade (RNF-COMP)

**RNF-COMP-001.** O sistema deverá suportar os navegadores **[Chrome, Firefox, Edge / outros]** em suas versões mais recentes. **[Inferido]**

**RNF-COMP-002.** O sistema deverá ser uma **aplicação web**, sem necessidade de instalação de software cliente. **[PRD/Inferido]**

**RNF-COMP-003.** Relatórios e documentos deverão ser exportáveis em **[PDF, DOCX, XLSX, HTML / outros formatos]**. **[PRD/Inferido]**

**RNF-COMP-004.** Dados deverão ser disponibilizáveis para consumo por ferramentas de **[BI / outras ferramentas]** corporativas. **[PRD/Inferido]**

**RNF-COMP-005.** O sistema deverá suportar **[publicação em portal institucional / outro canal]** para documentos públicos. **[PRD/Inferido]**

---

# 13. Inteligência Artificial (RNF-IART)

**RNF-IART-001.** [Se aplicável] Consultas baseadas em **RAG** (Retrieval-Augmented Generation) deverão responder em até **[X segundos]**. **[PRD/Inferido]**

**RNF-IART-002.** [Se aplicável] O sistema deverá suportar **múltiplos provedores de LLM**, com abstração de infraestrutura. **[PRD/Inferido]**

**RNF-IART-003.** [Se aplicável] Modelos de IA deverão poder operar **on-premises** para dados sigilosos. **[PRD/Inferido]**

**RNF-IART-004.** [Se aplicável] O banco de dados vetorial deverá escalar para **[milhões / outra escala]** de documentos indexados. **[Inferido]**

**RNF-IART-005.** [Se aplicável] Classificações e sugestões geradas por IA deverão ser passíveis de **revisão humana** (human-in-the-loop). **[PRD/Inferido]**

**RNF-IART-006.** [Se aplicável] O sistema deverá fornecer **explicabilidade (XAI)** para decisões automatizadas. **[Inferido]**

**RNF-IART-007.** [Se aplicável] O uso de IA deverá observar as **[Resoluções / Normas sobre IA]** [especificar órgão regulador]. **[PRD/Inferido]**

---

# 14. [Categoria Adicional – Personalizável] (RNF-[SIGLA])

**RNF-[SIGLA]-001.** [Descrição do requisito.] **[PRD/Inferido]**

**RNF-[SIGLA]-002.** [Descrição do requisito.] **[PRD/Inferido]**

---

# 15. Resumo por Criticidade

| Criticidade | Quantidade | Categorias |
|-------------|-----------|------------|
| **Alta** | [X] | [Listar categorias de alta criticidade] |
| **Média** | [X] | [Listar categorias de média criticidade] |
| **Baixa** | [X] | [Listar categorias de baixa criticidade] |

---

# 16. Considerações

Os requisitos marcados como **[Inferido]** são sugestões baseadas em boas práticas de sistemas corporativos [do setor / da instituição]. Devem ser validados com a equipe técnica [da instituição] antes da implementação. Os requisitos marcados como **[PRD]** são derivados diretamente da documentação funcional existente.

---

# Histórico de Revisões

| Versão | Data | Autor | Descrição das Alterações |
|--------|------|-------|--------------------------|
| 1.0 | [DD/MM/AAAA] | [Nome] | Criação do documento |
| 1.1 | [DD/MM/AAAA] | [Nome] | [Descrição da alteração] |

---

Fim dos Requisitos Não Funcionais – Versão [X.X]
