---
name: llc-step-8
description: Pipeline LLC Passo 8: Setup do projeto e camada de dados mockados (JSON + MSW handlers) — fundação para o MVP.
version: 1.1.0
tags: [mvp, mock, foundation, llc-pipeline]
---

# LLC Skill: Step 8 — Setup do Projeto + Camada de Dados Mockados

**Pipeline:** Live and Let Code (LLC)  
**Fase:** MVP / Fundação  
**Depende de:** Steps 5 (Arquitetura), 6 (Tarefas), 7 (Design System) — todos validados  
**Escopo:** Setup do projeto, scaffolding e camada de dados mockados.  
**OBSERVAÇÃO:** A implementação das telas e componentes de UI será tratada em um subfluxo separado com aprovação visual prévia. Este passo PARA após a camada de dados mockados.  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-8` ou "Execute a skill llc-step-8".

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — stack definido (Step 5)
- [ ] `docs/planning/TASKS.md` — tarefas priorizadas (Step 6)
- [ ] `docs/design/DESIGN_SYSTEM.md` — padrões visuais (Step 7)
- [ ] `docs/business/specs/perfis_permissoes.md` — papéis de usuário
- [ ] `docs/business/specs/requisitos_funcionais.md` — escopo funcional
- [ ] `docs/business/specs/workflows_bpmn.md` — fluxos principais
- [ ] `docs/business/specs/glossario.md` — terminologia
- [ ] `docs/prps/PRP-*.md` — PRPs do núcleo

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-8` do pipeline LLC. Seu objetivo NESTE PASSO é **apenas** configurar o projeto e implementar a camada de dados mockados. A implementação de telas e componentes de UI será tratada em um passo subsequente com aprovação visual prévia.

### Filosofia da Fundação Mockada

```
Antes de construir telas, precisamos de:
1. Projeto rodando (stack, lint, type-check)
2. Dados mockados realistas (JSON por entidade)
3. Handlers de API mockados (MSW — CRUD completo)
4. Usuários mock por perfil (autenticação simplificada)

Com essa fundação, as telas serão construídas sobre dados
que já simulam o comportamento real do sistema.
```

### 1. Leia as Entradas e Planeje a Fundação

Leia e analise:
- `docs/architecture/ARCHITECTURE.md` — stack, estrutura de pastas, dependências.
- `docs/business/specs/perfis_permissoes.md` — papéis para criar usuários mock.
- `docs/business/specs/requisitos_funcionais.md` — entidades e operações do núcleo.
- `docs/business/specs/glossario.md` — nomes oficiais das entidades.
- `docs/business/specs/workflows_bpmn.md` — estados e transições a mockar.
- `docs/prps/PRP-*.md` — PRPs da Wave 1 para identificar entidades do núcleo.
- `docs/planning/TASKS.md` — tarefas de setup e scaffolding.

Identifique:
- Quais entidades compõem o núcleo do MVP?
- Quais PRPs da Wave 1 são cobertos por essas entidades?
- Quais estados cada entidade pode assumir (conforme BPMN)?

### 2. Configure o Projeto

- Inicialize o projeto com o stack definido em `ARCHITECTURE.md`.
- Configure a estrutura de pastas conforme o monorepo definido na arquitetura.
- Instale as dependências base (framework, UI library, testing).
- Configure lint, type-check, format e git hooks.
- **IMPORTANTE:** Instale e configure MSW (`msw`) como dependência de desenvolvimento.

### 3. Implemente a Camada de Dados Mockados

Crie a estrutura `mocks/` na raiz do projeto:

```
mocks/
├── data/
│   ├── users.json          # Usuários mock por perfil
│   ├── [entidade_1].json   # Dados mock da entidade 1
│   ├── [entidade_2].json   # Dados mock da entidade 2
│   └── ...
├── handlers/
│   ├── auth.ts             # Handlers de autenticação mock
│   ├── [modulo_1].ts       # Handlers do módulo 1
│   └── ...
├── browser.ts              # Setup MSW para browser (dev)
├── server.ts               # Setup MSW para testes
└── README.md               # Documentação da camada mock
```

#### Regras dos Dados Mockados

**users.json — Simulação de Perfis:**
```json
{
  "users": [
    {
      "id": "mock-user-001",
      "name": "Maria Gestora",
      "email": "gestora@mvp.local",
      "password": "123456",
      "role": "P01",
      "roleName": "Gestor da Unidade",
      "unidade": "SEC-ADM-01",
      "permissions": ["create", "read", "update", "delete", "approve"],
      "avatar": null
    },
    {
      "id": "mock-user-002",
      "name": "João Analista",
      "email": "analista@mvp.local",
      "password": "123456",
      "role": "P02",
      "roleName": "Analista",
      "unidade": "SEC-ADM-01",
      "permissions": ["create", "read", "update"],
      "avatar": null
    }
  ]
}
```

- Crie pelo menos UM usuário para CADA perfil definido em `perfis_permissoes.md`.
- Senha padrão: `123456` para todos os usuários mock.
- Cada usuário deve ter o conjunto correto de permissões conforme a matriz RBAC.
- Nomes realistas, emails no domínio `@mvp.local`, unidades organizacionais variadas.

**Dados de Entidade — Regras:**
- Cada entidade do modelo de dados do núcleo deve ter um arquivo JSON.
- **5 a 20 registros** por entidade, com dados realistas e contextualizados.
- Inclua diversidade de estados (ex: rascunho, em_andamento, concluído, cancelado).
- Inclua relacionamentos realistas entre entidades (FKs apontando para IDs de outros JSONs).
- Use datas, nomes e descrições que pareçam reais (nada de "teste", "foo", "bar", "asdf").
- Dados devem cobrir cenários: estado vazio, poucos registros, muitos registros.

**Handlers MSW — Regras:**
- Cada handler deve simular o comportamento real da API:
  - Delay de 200-500ms para simular latência de rede.
  - CRUD completo (GET list, GET by id, POST, PUT, DELETE) para cada entidade.
  - Filtros por query params (ex: `?status=concluido&unidade=SEC-ADM-01`).
  - Ordenação (ex: `?sort=created_at&order=desc`).
  - Paginação (ex: `?page=1&limit=20`).
- Handlers de auth:
  - POST `/auth/login` — valida email/senha contra `users.json`, retorna token JWT mock + dados do usuário.
  - GET `/auth/me` — retorna usuário logado a partir do token.
  - POST `/auth/logout` — invalida token.
- Simular erros realistas:
  - 400 — dados inválidos (campos obrigatórios faltando, formato inválido).
  - 401 — sem token ou token expirado.
  - 403 — permissão insuficiente para a operação.
  - 404 — recurso não encontrado.
  - 409 — conflito (ex: email já cadastrado).
  - 429 — rate limit excedido (após 10 requisições em 1s).
  - 500 — erro interno do servidor (simular aleatoriamente em 2% das requisições).

### 4. Atualize a Documentação de Planejamento

Após concluir os passos 2 e 3, atualize os documentos para refletir o progresso:

#### docs/planning/TASKS.md
- Marque como concluídas `[x]` as tarefas de setup e scaffolding executadas.
- Se alguma tarefa foi parcialmente concluída, marque como `[/]` e adicione nota.
- Atualize o campo `Status` de cada tarefa concluída.
- Adicione ao final do arquivo uma seção `## Log de Execução — Step 8` com:
  - Data e hora da execução.
  - Tarefas concluídas.
  - Arquivos criados (com caminhos).
  - Observações e decisões tomadas.

#### docs/prps/PRP-*.md
Para cada PRP da Wave 1:
- Atualize o campo `Status` de `pending` para `in-progress`.
- No `## Execution Log` do PRP, adicione entrada:
  ```
  | [DATA] | Step 8 — Fundação Mockada | Setup do projeto e camada mock implementados | [ARQUIVOS CRIADOS] |
  ```
- Se o PRP teve TODAS as suas entidades mockadas, marque a fase de dados como concluída no checklist interno.

#### docs/planning/EXECUTION_WAVES.md
- Na Wave 1, atualize o status da fase de fundação.
- Adicione nota sobre a conclusão da camada mock.

---

## ⚠️ REGRAS CRÍTICAS

1. **Escopo limitado:** Este passo NÃO implementa telas, componentes de UI ou fluxos de usuário. Apenas setup + camada de dados mockados.
2. **Mockado, mas realista:** Dados devem parecer reais. Nada de placeholders genéricos.
3. **Substituível:** A camada mock deve usar interfaces/contratos claros para ser trocada por API real sem reescrever consumers.
4. **Cobertura de perfis:** Todo perfil definido em `perfis_permissoes.md` deve ter pelo menos um usuário mock.
5. **Cobertura de estados:** Cada entidade deve ter registros em diferentes estados conforme BPMN.
6. **Handlers completos:** Todo endpoint do núcleo deve ter tratamento de erros realistas.
7. **Documentação atualizada:** TASKS.md, PRPs e WAVES devem refletir o progresso real.
8. **Idempotência:** Se o projeto já estiver inicializado, pergunte antes de sobrescrever. Se arquivos mock já existirem, pergunte se atualiza ou mantém.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após concluir os passos 2, 3 e 4, **PARE** e apresente:

1. **Projeto:** Estrutura de pastas criada, dependências instaladas, scripts configurados.
2. **Mocks — Usuários:** Quantos usuários mock criados, distribuídos por perfil.
3. **Mocks — Entidades:** Lista de arquivos JSON com contagem de registros e estados cobertos.
4. **Handlers:** Endpoints mockados implementados (contagem por módulo/entidade).
5. **Cobertura de Erros:** Quais códigos de erro HTTP estão simulados.
6. **Documentação Atualizada:** Resumo das alterações feitas em TASKS.md, PRPs e WAVES.
7. **PRPs em Progresso:** Quais PRPs tiveram status atualizado para `in-progress`.
8. **Próximos Passos:** "A fundação mockada está pronta. O próximo passo é o subfluxo de design e aprovação visual das telas antes da implementação dos componentes de UI."

**Este passo termina aqui. A implementação de telas e componentes de UI será realizada em um subfluxo separado com aprovação visual prévia.**
