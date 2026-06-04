# 📄 Template de Especificação de Requisitos Funcionais (Orientado a Workflow)
**Sistema:** [Nome do Sistema]  
**Documento de Referência:** VOLUME XX – WORKFLOWS E BPMN (Versão 3.0)  
**Data de Criação:** [Inserir Data]  
**Autor:** [Inserir Nome do Analista]  

---

## 1. Metadados do Requisito
| Campo | Descrição |
| :--- | :--- |
| **ID do Requisito** | `RF-[MÓDULO]-[NÚMERO]` (Ex: `RF-WF005-01`) |
| **Nome do Requisito** | Título curto e descritivo da funcionalidade. |
| **Workflow Associado** | Código e nome do workflow (Ex: `WF-005: Ciclo de Vida do Achado de Auditoria`). |
| **Prioridade** | Alta / Média / Baixa |
| **Regras de Negócio** | Códigos das RNs aplicáveis (Ex: `RN-ACH-001`, `RN-SEG-005`). |

## 2. Descrição Narrativa (User Story)
> **Como** [Perfil Responsável],  
> **Quero** [Realizar Evento/Ação no sistema],  
> **Para que** [Objetivo de negócio / Estado Destino seja alcançado].

## 3. Especificação da Transição de Estado
| Campo | Detalhe (Preencher com base na tabela de transições) |
| :--- | :--- |
| **Estado de Origem** | Código e Nome (Ex: `ACH-02 - Em Análise`) |
| **Evento (Gatilho)** | Nome da ação do usuário ou do sistema (Ex: `Validar`) |
| **Estado de Destino** | Código e Nome (Ex: `ACH-03 - Validado`) |
| **Condições de Guarda** | Condições que DEVEM ser verdadeiras para permitir a transição. |
| **Ações do Sistema** | Efeitos colaterais automáticos (Ex: Logs, notificações, cálculos). |
| **Responsável** | Perfil(s) autorizado(s) a executar o evento. |

## 4. Critérios de Aceite (Testes)
- [ ] O sistema deve bloquear a transição se [Condição de Guarda] não for atendida, exibindo a mensagem: "[Mensagem de erro]".
- [ ] Ao executar a ação, o sistema deve registrar no log auditável: timestamp, usuário, IP, estado anterior e estado posterior (Conforme RN de Integridade).
- [ ] O sistema deve disparar notificação para [Destinatário] via [Canal], conforme Matriz de Alertas.
- [ ] A regra de segregação de funções deve ser validada (o executor não pode ser o criador do objeto, se aplicável).

---

## 📝 Exemplos Preenchidos (Baseados no VOLUME XX)

### Exemplo 1: Requisito de Transição de Workflow (WF-005)
| Campo | Detalhe |
| :--- | :--- |
| **ID do Requisito** | `RF-WF005-01` |
| **Nome do Requisito** | Validação Metodológica de Achado de Auditoria |
| **Workflow Associado** | `WF-005: Ciclo de Vida do Achado de Auditoria` |
| **Prioridade** | Alta |
| **Regras de Negócio** | `RN-ACH-001` |

**Descrição Narrativa:**  
> **Como** Supervisor,  
> **Quero** validar um achado que está em análise,  
> **Para que** ele seja considerado metodologicamente completo e avance para o estado "Validado".

**Especificação da Transição:**
- **Estado de Origem:** `ACH-02 - Em Análise`
- **Evento:** `Validar`
- **Estado de Destino:** `ACH-03 - Validado`
- **Condições de Guarda:** Os campos Critério, Condição, Causa, Efeito, Risco e Evidência devem estar obrigatoriamente preenchidos.
- **Ações do Sistema:** Registrar log de auditoria da transição.
- **Responsável:** Supervisor

**Critérios de Aceite:**
- [ ] O sistema deve bloquear a ação "Validar" se qualquer um dos 6 campos metodológicos estiver vazio, exibindo: "Validação bloqueada: Preencha todos os campos metodológicos obrigatórios (RN-ACH-001)".
- [ ] O sistema deve gravar log imutável contendo: timestamp, ID do usuário Supervisor, IP, estado anterior (ACH-02) e posterior (ACH-03).
- [ ] O sistema deve validar que o Supervisor que executa a ação não é o mesmo usuário que criou o achado (RN-SEG-005).

---

### Exemplo 2: Requisito de Transição de Workflow (WF-007)
| Campo | Detalhe |
| :--- | :--- |
| **ID do Requisito** | `RF-WF007-05` |
| **Nome do Requisito** | Validação de Implementação de Recomendação |
| **Workflow Associado** | `WF-007: Recomendação em Monitoramento` |
| **Prioridade** | Alta |
| **Regras de Negócio** | `RN-MON-007` |

**Descrição Narrativa:**  
> **Como** Auditor,  
> **Quero** validar as evidências de implementação enviadas pela unidade auditada,  
> **Para que** a recomendação possa ser classificada como "Validada" ou retornada para correção.

**Especificação da Transição:**
- **Estado de Origem:** `REC-05 - Em Validação`
- **Evento:** `Validar implementação`
- **Estado de Destino:** `REC-06 - Validada`
- **Condições de Guarda:** Evidência anexada deve ser suficiente e consistente.
- **Ações do Sistema:** Registrar log.
- **Responsável:** Auditor

**Critérios de Aceite:**
- [ ] O sistema deve exigir o upload ou vínculo de pelo menos um arquivo/documento como evidência antes de habilitar o botão "Validar implementação".
- [ ] O sistema deve impedir que o Auditor que validou a implementação seja o mesmo que registrou o achado original (Segregação de Funções).
- [ ] Ao validar, o sistema deve registrar log auditável e permitir o avanço para `REC-06`.

---

### Exemplo 3: Requisito de Transição de Workflow (WF-001)
| Campo | Detalhe |
| :--- | :--- |
| **ID do Requisito** | `RF-WF001-01` |
| **Nome do Requisito** | Submissão do PALP para Revisão Técnica |
| **Workflow Associado** | `WF-001: Ciclo de Vida do PALP` |
| **Prioridade** | Alta |
| **Regras de Negócio** | N/A (Regra de fluxo padrão) |

**Descrição Narrativa:**  
> **Como** Auditor Líder ou Coordenador,  
> **Quero** submeter o PALP em rascunho para revisão,  
> **Para que** a equipe AUDIN possa realizar a revisão metodológica.

**Especificação da Transição:**
- **Estado de Origem:** `PALP-01 - Rascunho`
- **Evento:** `Submeter à revisão`
- **Estado de Destino:** `PALP-02 - Em Revisão Técnica`
- **Condições de Guarda:** Ao menos 1 auditoria proposta deve estar cadastrada no plano.
- **Ações do Sistema:** Notificar revisores.
- **Responsável:** Auditor Líder / Coordenador

**Critérios de Aceite:**
- [ ] O sistema deve verificar a contagem de auditorias propostas no PALP. Se for igual a 0, bloquear a transição com a mensagem: "É necessário incluir ao menos 1 auditoria proposta antes de submeter à revisão".
- [ ] Ao transitar com sucesso, o sistema deve disparar notificação (Sistema + E-mail) para os perfis de Revisor de Qualidade e Supervisor.

---

### Exemplo 4: Requisito de Regra Cross-Workflow (Restrição Global)
| Campo | Detalhe |
| :--- | :--- |
| **ID do Requisito** | `RF-GLB-001` |
| **Nome do Requisito** | Segregação de Funções na Aprovação/Revisão |
| **Workflow Associado** | Global (WF-001, WF-002, WF-004, WF-006, WF-009) |
| **Prioridade** | Crítica |
| **Regras de Negócio** | `RN-SEG-005` |

**Descrição Narrativa:**  
> **Como** Administrador do Sistema / Auditor de Conformidade,  
> **Quero** que o sistema impeça que o criador de um documento seja o mesmo que o aprova ou revisa,  
> **Para que** seja garantida a segregação de funções e a integridade do processo.

**Especificação da Regra:**
- **Escopo:** Transições de "Aprovar", "Validar" ou "Revisar" nos workflows de PALP, PAA, Papel de Trabalho, Relatório e Plano de Ação.
- **Condição de Guarda:** `ID_Usuario_Atual != ID_Usuario_Criador_Objeto`
- **Ação do Sistema:** Bloquear a transição e exibir mensagem de erro.

**Critérios de Aceite:**
- [ ] Se o usuário que criou o "Papel de Trabalho" (PT-01) tentar executar a ação "Aprovar" (PT-03), o sistema deve bloquear a ação.
- [ ] Mensagem exibida ao bloquear: "Ação negada: Violação de segregação de funções (RN-SEG-005). O aprovador/revisor não pode ser o autor do documento."
- [ ] A tentativa de violação deve ser registrada no log de segurança do sistema.

---

## 💡 Instruções de Uso para a Equipe de Desenvolvimento e QA
1. **Rastreabilidade:** Mantenha o campo "Regras de Negócio" sempre preenchido para vincular o requisito funcional às RNs definidas no VOLUME XX.
2. **Imutabilidade:** Todos os requisitos que envolvem transição de estado devem incluir, nos Critérios de Aceite, a geração do **Log Auditável** (timestamp, usuário, IP, estados), conforme a seção *6.2 Integridade e Imutabilidade*.
3. **Automação de Testes:** Os "Critérios de Aceite" estão formatados para serem convertidos diretamente em scripts de teste BDD (Gherkin) ou casos de teste manuais no Jira/Azure DevOps.