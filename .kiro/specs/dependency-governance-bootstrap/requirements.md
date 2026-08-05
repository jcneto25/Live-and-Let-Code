# Requirements Document

## Introduction

Esta feature cria `.ace/config/dependencies.yaml` — o registro central SBOM-like de todas as dependências externas do LLC (Live and Let Code), conforme mandatado pelo ADR-0006 (Governança de Dependências Externas).

O arquivo é o artefato fundacional da trilha de governança: sem ele, a fitness function `dependency-governance` (PRP-GOV-T3) não pode ser implementada, e qualquer nova dependência continua sendo adotada sem critério formal.

**Escopo:** criação de um único arquivo YAML (`dependencies.yaml`) sem modificar nenhum arquivo existente, sem adicionar dependências Python novas (N0 — apenas stdlib).

---

## Glossary

- **SBOM (Software Bill of Materials)**: inventário estruturado de todos os componentes de software de um sistema, incluindo licenças, versões e metadados de risco.
- **Dependencies_Registry**: o arquivo `.ace/config/dependencies.yaml` — registro central único de todas as dependências externas do LLC.
- **Dependency_Entry**: um item da lista `dependencies` dentro do `dependencies_registry`, representando uma única dependência externa.
- **N1_Dependency**: dependência de nível 1 — biblioteca Python importada e distribuída junto ao LLC (ex.: `click`, `pyyaml`, `textual`, `tiktoken`).
- **Critical_Path**: caminho de execução do harness LLC que, se falhar, impede a operação via `llc run` ou `llc pipeline`.
- **Fallback**: mecanismo alternativo que permite ao LLC continuar operando quando a dependência está ausente.
- **Bus_Factor**: indicador da concentração de mantenedores de um projeto; `community` = múltiplos mantenedores ativos; `1` = único mantenedor.
- **Review_Interval**: periodicidade (em dias) para revisar o registro de cada dependência quanto a mudanças de licença, versão e bus factor.
- **Degradation_Test**: referência a um teste automatizado que valida o comportamento do LLC na ausência de uma dependência específica.
- **Admission_Checklist**: conjunto de 10 critérios obrigatórios definidos no ADR-0006 §2.3 que toda dependência N1+ deve satisfazer para ser integrada.

---

## Requirements

### Requirement 1: Criação do arquivo de registro central

**User Story:** Como mantenedor do LLC, quero que o arquivo `.ace/config/dependencies.yaml` exista com estrutura SBOM-like válida, para que o registro central de governança esteja disponível como base para a fitness function e auditorias futuras.

#### Acceptance Criteria

1. THE `dependencies_registry` SHALL existir no caminho `.ace/config/dependencies.yaml` com conteúdo YAML sintaticamente válido e parseável via `yaml.safe_load()`.
2. THE `dependencies_registry` SHALL conter os campos de cabeçalho: `version` (inteiro), `updated_at` (string ISO-8601), e `review_interval_days` (inteiro).
3. THE `dependencies_registry` SHALL conter `review_interval_days: 90`, configurando revisão trimestral conforme ADR-0006 §2.7.
4. THE `dependencies_registry` SHALL conter uma chave `dependencies` mapeando para uma lista de `dependency_entry` objetos.
5. IF o arquivo `.ace/config/dependencies.yaml` já existir com conteúdo, THEN THE `dependencies_registry` SHALL preservar o conteúdo existente sem sobrescrevê-lo.

---

### Requirement 2: Campos obrigatórios por entrada (Admission Checklist ADR-0006 §2.3)

**User Story:** Como mantenedor do LLC, quero que cada entrada de dependência satisfaça o checklist de admissão do ADR-0006, para que nenhuma dependência entre sem análise formal de risco.

#### Acceptance Criteria

1. EVERY `dependency_entry` SHALL conter os campos: `name`, `version`, `level`, `license`, `bus_factor`, `purpose`, `critical_path`, `fallback`, `last_reviewed`, `next_review`.
2. EVERY `dependency_entry` WHERE `level` equals `1` SHALL ter `version` especificada como range pinado (nunca o literal `latest`).
3. EVERY `dependency_entry` SHALL ter `last_reviewed` preenchido com a data de criação do arquivo.
4. EVERY `dependency_entry` SHALL ter `next_review` calculado como `last_reviewed` + `review_interval_days` dias.
5. IF um `dependency_entry` representa uma dependência cujo `bus_factor` equals `1` OU cuja versão é pré-1.0, THEN THE `dependency_entry` SHALL conter `experimental: true`.

---

### Requirement 3: Registro da dependência `click`

**User Story:** Como mantenedor do LLC, quero que `click` esteja registrado como N1 no `dependencies_registry`, para que o backbone do CLI do LLC esteja documentado na governança.

#### Acceptance Criteria

1. THE `dependencies_registry` SHALL conter um `dependency_entry` com `name: click`.
2. WHEN o `dependency_entry` `click` é avaliado, THE `dependency_entry` SHALL ter `level: 1`, `license: BSD-3-Clause`, e `bus_factor: community`.
3. WHEN o `dependency_entry` `click` é registrado no `dependencies_registry`, THE `dependency_entry` SHALL ter `level: 1` antes de poder ter `critical_path: true`; uma entrada com `level` diferente de `1` não pode ter `critical_path: true`.
4. WHEN o `dependency_entry` `click` é registrado no `dependencies_registry`, THE `dependency_entry` SHALL ter `version` validada como range pinado na faixa `>=8.0,<9.0`, nunca o literal `latest`.

---

### Requirement 4: Registro da dependência `pyyaml`

**User Story:** Como mantenedor do LLC, quero que `pyyaml` esteja registrado como N1 no `dependencies_registry` com fallback documentado, para que exista um plano de degradação caso a biblioteca seja removida.

#### Acceptance Criteria

1. THE `dependencies_registry` SHALL conter um `dependency_entry` com `name: pyyaml`.
2. WHEN o `dependency_entry` `pyyaml` é avaliado, THE `dependency_entry` SHALL ter `level: 1`, `license: MIT`, e `bus_factor: community`.
3. WHEN o `dependency_entry` `pyyaml` é avaliado, THE `dependency_entry` SHALL ter `critical_path: false`.
4. WHEN o `dependency_entry` `pyyaml` é avaliado, THE `dependency_entry` SHALL ter `fallback` descrevendo o uso de `json` da stdlib Python para configurações simples como mecanismo substituto.

---

### Requirement 5: Registro da dependência `textual`

**User Story:** Como mantenedor do LLC, quero que `textual` esteja registrado como N1 no `dependencies_registry` com fallback e referência ao teste de degradação, para que a política de degradação graciosa do Wizard esteja rastreável.

#### Acceptance Criteria

1. THE `dependencies_registry` SHALL conter um `dependency_entry` com `name: textual`.
2. WHEN o `dependency_entry` `textual` é avaliado, THE `dependency_entry` SHALL ter `level: 1`, `license: MIT`, e `bus_factor: community`.
3. WHEN o `dependency_entry` `textual` é avaliado, THE `dependency_entry` SHALL ter `critical_path: false`.
4. WHEN o `dependency_entry` `textual` é avaliado, THE `dependency_entry` SHALL ter `fallback` descrevendo que `llc run` e `llc pipeline` continuam funcionando via CLI puro quando `textual` está ausente.
5. WHEN o `dependency_entry` `textual` é avaliado, THE `dependency_entry` SHALL ter `degradation_test` apontando para o teste `test_select_runner_falls_back_when_no_agent` do PRP-WIZARD-1A.
6. WHEN o `dependency_entry` `textual` é avaliado, THE `dependency_entry` SHALL ter `version` na faixa `>=0.80.0,<1.0` e `notes` indicando que a API é instável por ser 0.x.

---

### Requirement 6: Registro da dependência `tiktoken`

**User Story:** Como mantenedor do LLC, quero que `tiktoken` esteja registrado como N1 opcional no `dependencies_registry`, para que o fallback de estimativa de tokens por contagem esteja documentado formalmente.

#### Acceptance Criteria

1. THE `dependencies_registry` SHALL conter um `dependency_entry` com `name: tiktoken`.
2. WHEN o `dependency_entry` `tiktoken` é avaliado, THE `dependency_entry` SHALL ter `level: 1`, `license: MIT`, e `bus_factor: community`.
3. WHEN o `dependency_entry` `tiktoken` é avaliado, THE `dependency_entry` SHALL ter `critical_path: false` e `optional: true`.
4. WHEN o `dependency_entry` `tiktoken` é avaliado, THE `dependency_entry` SHALL ter `fallback` descrevendo estimativa por contagem de palavras multiplicada por fator heurístico como mecanismo substituto de nível 3.
5. WHEN o `dependency_entry` `tiktoken` é avaliado, THE `dependency_entry` SHALL ter `version` na faixa `>=0.7.0,<1.0`.

---

### Requirement 7: Restrições de implementação

**User Story:** Como arquiteto do LLC, quero que a criação do `dependencies.yaml` não introduza nenhuma dependência Python nova nem modifique nenhum arquivo existente, para que a entrega seja cirurgicamente isolada e reversível.

#### Acceptance Criteria

1. THE `dependencies_registry` SHALL ser criado usando exclusivamente funcionalidades da stdlib Python (N0), sem importar nenhuma biblioteca externa nova além das já registradas.
2. THE implementation SHALL não modificar nenhum arquivo existente no repositório além de criar `.ace/config/dependencies.yaml`.
3. THE `dependencies_registry` SHALL ser validado como YAML sintaticamente correto pelo comando `python -c "import yaml; yaml.safe_load(open('.ace/config/dependencies.yaml'))"` sem erros.
4. WHEN o `dependencies_registry` é inspecionado, THE `dependencies_registry` SHALL não conter nenhum campo com o valor literal `latest` em nenhum `version`.
5. THE implementation SHALL não modificar nenhum arquivo existente no repositório, incluindo arquivos criados na mesma sessão de trabalho — somente a criação de `.ace/config/dependencies.yaml` é permitida.
