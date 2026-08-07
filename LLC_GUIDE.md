## Guia de Execucao — Live and Let Code (LLC)

**Versao:** 1.6.0
**Publico:** Desenvolvedores, Product Owners, Tech Leads
**Pre-requisito:** Leitura do [`llc-pipeline-design.md`](llc-pipeline-design.md) (visao geral da metodologia)

---

## 🚀 Modo Quickstart (Para iniciantes)

Para começar rapidamente, use o modo **quickstart** do pipeline:

```bash
# Instalar dependencias
pip install click

# Executar pipeline quickstart (3 gates principais)
python .ace/scripts/llc.py pipeline --quickstart --from 0

# Ver status
python .ace/scripts/llc.py status
```

**Modo quickstart inclui:**
- Gate 1: Visao + Modulos
- Gate 4: PRPs
- Gate 11: Execucao (PRPs sem UI)

Para projetos com UI, use o modo completo:

```bash
python .ace/scripts/llc.py pipeline --from 0 --to 11.1
```

---

## Antes de Começar

### O que você precisa

- Um cliente de IA terminal (Claude Code, opencode, Codex, Cursor CLI, etc.)
- Git instalado e configurado
- Um projeto de software a ser desenvolvido
- Documentos de domínio do negócio (manuais, atas, regulamentos, transcrições, guias operacionais)

### Estrutura Inicial

Clone o repositório LLC ou copie a estrutura de diretórios para seu projeto:

```bash
git clone https://github.com/jcneto25/Live-and-Let-Code.git seu-projeto
cd seu-projeto
```

A estrutura `docs/` contém todos os templates e skills necessários.

### Configurando as Skills para seu Cliente de IA

Os skills LLC são arquivos Markdown com YAML frontmatter. Cada cliente de IA terminal tem seu próprio diretório de skills. Copie (ou crie symlinks) dos arquivos de `docs/skills/` para o diretório apropriado:

| Cliente de IA | Diretório de Skills | Comando para configurar |
|---------------|--------------------|-------------------------|
| **Claude Code** | `.claude/skills/` | `cp docs/skills/llc-*.md .claude/skills/` |
| **opencode** | `.opencode/skills/<name>/SKILL.md` | `mkdir -p .opencode/skills/llc-step-0-1 && cp docs/skills/llc-step-0-1.md .opencode/skills/llc-step-0-1/SKILL.md` (repetir para cada skill) |
| **Codex** | `.codex/skills/` | `cp docs/skills/llc-*.md .codex/skills/` |
| **Cursor** | `.cursor/skills/` | `cp docs/skills/llc-*.md .cursor/skills/` |
| **GitHub Copilot CLI** | `.github/copilot/skills/` | `cp docs/skills/llc-*.md .github/copilot/skills/` |
| **Outros** | `.skills/` (padrão) | `cp docs/skills/llc-*.md .skills/` |

**Alternativa — sem copiar:** A maioria dos clientes aceita o caminho direto. Exemplo:

```
Execute a skill docs/skills/llc-step-0-1.md
```

**Invocação por alias:** Se o cliente suportar aliases de skill (ex: `@llc-step-0-1`), o nome no YAML frontmatter é usado automaticamente.

**Script rápido para opencode (bash):**
```bash
for f in docs/skills/llc-*.md; do
  name=$(basename "$f" .md)
  mkdir -p ".opencode/skills/$name"
  cp "$f" ".opencode/skills/$name/SKILL.md"
done
```

---

### Modo de Operação da LLM

O pipeline LLC tem dois momentos distintos que se beneficiam de modos de operação diferentes:

| Etapas | Modo Recomendado | Motivo |
|--------|------------------|--------|
| **Passos 0 a 10** (especificação e planejamento) | **Thinking / Reasoning** | Documentos exigem análise profunda, raciocínio multi-step e consistência cruzada entre artefatos. O modo thinking reduz alucinações e produz especificações mais coerentes. |
| **Ajustes pós-validação** | **Thinking / Reasoning** | Correções em documentos após um gate reprovado exigem compreensão do contexto completo e impacto das mudanças em artefatos interdependentes. |
| **Passo 11 — Execução** (desenvolvimento e testes) | **Regular / Default** | Implementação de PRPs e tarefas se beneficia de respostas mais rápidas. O código gerado é validado por testes automatizados, reduzindo o risco de alucinações. |
| **Subfluxo F1-F4** (prototipagem) | **Thinking / Reasoning** | Fases de discovery, tokens, wireframes e hi-fi exigem julgamento de design e consistência com o Design System. |
| **Subfluxo F5-F6** (código e validação) | **Regular / Default** | Geração de componentes e execução de testes seguem especificações já aprovadas. |

**Na prática:** Ative o modo thinking/extended reasoning da sua LLM para os passos 0 a 10 e para qualquer ajuste solicitado após validação. Use o modo normal para execução de código e testes.

---


### Usando o Thin Harness (recomendado)

A partir da versão 1.4.0, o LLC inclui um orquestrador CLI que automatiza o ciclo de vida de cada step:

```bash
# Instalar dependência única
pip install click

# Executar um step completo
python .ace/scripts/llc.py run --step 5 --task "Arquitetura do sistema"

# Pipeline completo (para em cada gate)
python .ace/scripts/llc.py pipeline --from 0

# Ver progresso
python .ace/scripts/llc.py status
```

**v2.0.0 — Wizard TUI (fonte: grafo) + relatórios de Evals:**

```bash
python .ace/scripts/llc.py wizard                    # Kanban alimentado pelo grafo do pipeline: caminho crítico 🔺, próximo step ➤, swimlanes por wave
python .ace/scripts/llc.py wizard --source index     # fallback: PipelineDataReader read-only
python .ace/scripts/llc.py eval --report             # dashboard Pareto custo×qualidade
python .ace/scripts/llc.py eval flow-report          # relatório de gargalos: critical_path × flow-metrics
```

O harness gerencia automaticamente: sessao ACE, context_seed, carregamento da skill,
invocacao do agente, gate de validacao e finalizacao. Se o cliente CLI estiver
disponivel (claude, opencode, codex, cursor), a invocacao e automatica. Caso
contrario, o prompt e exibido para copiar e colar manualmente.

> **⚡ Early Commitment + Deterministic Replay (v1.5.0):** O harness classifica
> automaticamente cada tarefa em 4 tipos e reutiliza caminhos de execucao aprovados
> para tarefas repetidas — reduzindo o custo de tokens em ate 99%. Para detalhes,
> consulte o [FAQ](FAQ.md#-early-commitment--deterministic-replay).

### Garantindo o registro de sessões no `.ace` (tool-agnostic)

O fluxo `llc run --step N` já é **agnóstico ao cliente de IA**: o harness faz
`initialize_session.py → carrega a skill → invoca o agente CLI (claude/opencode/codex/cursor, ou imprime o prompt) → finalize_session.py`.
O problema não é executar o fluxo — é **garantir** que o agente entre por ele em vez de
codar "direto". Codar fora do ciclo deixa `.ace/index.json` com `sessions: []`: o trabalho
existiu, mas não há histórico que prove a entrega incremental.

O LLC aplica **defense in depth** — camadas com papéis distintos:

| Camada | Mecanismo | Força | Tool-agnostic? |
|--------|-----------|-------|:---:|
| **Contrato** | `AGENTS.md`/`CLAUDE.md` declaram "todo trabalho vira sessão" | Advisory (define a regra) | ✅ |
| **Procedimento** | skill do step (auto-carregada pelo `llc run`) | Advisory (operacionaliza) | ✅ |
| **Garantia** | `pre-commit.sh` + `validate-tags.py --coverage`: commit com código sem sessão é **rejeitado** pelo git | **Determinística** | ✅ |
| **Self-validation** | `llm-validation.sh`: 8 checks pós-geração (secrets, SQL injection, `return null`, placeholder tests…) — o agente executa antes de reportar task concluída; hook `ace-llm-validation` repete a barreira no commit | **Determinística** | ✅ |
| **UX por cliente** | hook do cliente (ex.: Claude Code `PreToolUse`) bloqueia edição sem sessão aberta | Determinística | ❌ (por cliente) |

A camada que **realmente garante** o registro é o **pre-commit do git** — o git o executa
independente do agente que fez o commit. Instale no projeto-alvo:

```bash
cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
# ou, com o framework pre-commit: pre-commit install
```

Para enforcement *durante* a sessão (antes do commit), use o hook do seu cliente.
Snippets prontos (Claude Code `PreToolUse` + `SessionStart`) em
[`docs/templates/hooks/claude-code-session-hooks.md`](docs/templates/hooks/claude-code-session-hooks.md).

> O pre-commit pode ser contornado com `git commit --no-verify` (sob responsabilidade do
> operador). Nenhum mecanismo é 100% — mas, em camadas, mudam o jogo de "o agente esqueceu"
> para "alguém precisou contornar ativamente". Detalhes no
> [`llc-pipeline-design.md` §8.7](llc-pipeline-design.md#87-registro-garantido-de-sessões-session-enrollment-enforcement).

## Passo a Passo

### 📋 Visao Geral do Pipeline (23 etapas pipeline + 2 delta)

```
Greenfield / Documentos novos:
Step 0   → Ingestao de documentos
Step 0.1 → Conversao para Markdown (Docling)
Step 0.5 → Visao Estrategica + Modulos       👤 Gate 1
Step 1   → 7 Especificacoes                  👤 Gate 2
Step 2   → PRDs (Executivo + Tecnico)         👤 Gate 3
Step 2.5 → Casos de Uso (LLC)                👤 Gate 3.5
Step 3   → PRPs                               👤 Gate 4
Step 4   → Planejamento                       👤 Gate 5
Step 5   → Arquitetura                        👤 Gate 6
Step 5a  → Architecture Patterns              👤 Gate 6a
Step 5b  → API Design Enforcement             👤 Gate 6b
Step 5c  → Clean Code Enforcement             👤 Gate 8.5
Step 5d  → Secure-by-Design                   👤 Gate 5d
Step 6   → Tarefas                            👤 Gate 7
Step 7   → Design System                      👤 Gate 8
Step 8   → Setup + Mock Data                  👤 Gate 9
Step 9   → Testing Docs                       👤 Gate 10
Step 10  → Project Docs + Steering Files      👤 Gate 11
Step 10.5 → Manual do Usuario                 👤 Gate 11.5
Step 10.6 → Auditoria (SCA+SAST+Secrets)  👤 Gate 11-SEC
Step 10.7 → Contratos de Dados            👤 Gate 12-NULL
Step 10.8 → Cobertura de Testes               👤 Gate 10.8
Step 11  → Execucao (PRPs)                    QA Checkpoints
Step 11.1 → Hardening (post-code)         👤 Gate 11-OWASP

Fluxo Delta (mudancas em sistema existente):
Step Δ.0 → Delta Impact Analysis              👤 Gate Δ.0
Step Δ.1 → Grill Me de Mudanca                👤 Gate Δ.1
Steps 0.5-11 → Smart Skip (pula inalterados)  👤 Gates auto-aprovados
```

### ⚠️ Atencao: Voce tem documentacao previa?

**Se SIM** (já existem manuais, atas, regulamentos) → siga para o Passo 0.

**Se NÃO** (sistema novo, sem documentação) → execute o fluxo greenfield:

```
Execute a skill docs/skills/llc-step-0-greenfield.md
```

A IA conduzirá uma entrevista estruturada em 4 dimensões (15 perguntas no total) e gerará a base documental. Depois, prossiga normalmente para o Step 0.5.

---

### Passo 0: Carregue os Documentos de Domínio

**Você faz:** Coloque todos os documentos de negócio na pasta `docs/business/ingestion/`.

Formatos aceitos: `.pdf`, `.docx`, `.pptx`, `.html`, `.txt`, imagens com texto (PNG/JPG/TIFF).

Exemplos do que colocar:
- Transcrições de reuniões com stakeholders
- Manuais de processos organizacionais
- Regulamentos e legislação aplicável
- Atas de decisões arquiteturais
- Guias operacionais da unidade demandante

---

### Passo 0.1: Conversão para Markdown (Docling) 🆕

**Você faz:** Execute o skill de conversão:

```
Execute a skill docs/skills/llc-step-0-1.md
```

**A IA faz:**
- Detecta todos os formatos em `docs/business/ingestion/` (PDF, DOCX, PPTX, HTML)
- Converte cada arquivo para Markdown usando **Docling** (ou Pandoc como fallback)
- Deposita os arquivos `.md` convertidos em `docs/business/ingestion/converted/`
- Gera `_CONVERSION_REPORT.md` com estatísticas e status de cada arquivo

**Pré-requisito único:** Python 3.10+ + `pip install docling`

**Por que Markdown?** Menos tokens, menos ruído estrutural, melhor compreensão pela IA. PDFs e DOCsX têm tags pesadas que consomem tokens desnecessários.

---

### Passo 0.5: Visão Estratégica + Módulos

**Você faz:** Execute o skill no seu cliente de IA:

```
Execute a skill docs/skills/llc-step-0-5.md
```

**A IA faz:**
- Lê todos os arquivos em `docs/business/ingestion/converted/` (Markdown puro)
- Gera `docs/business/specs/visao_estrategica_e_negocio.md` (visão do sistema)
- Gera arquivos `MOD-[SIGLA]-[NNN]_[nome].md` (um por módulo identificado)

**Você valida:** 👤 Gate 1
- A visão cobre todo o escopo do negócio?
- Os módulos estão corretamente identificados e nomeados?
- Alguma seção ficou com `[NÃO IDENTIFICADO]`? Se sim, complemente.

**Só avance quando aprovar.**

---

### Passo 1: 7 Especificações

**Você faz:**

```
Execute a skill docs/skills/llc-step-1.md
```

**A IA faz:** Gera 7 documentos em `docs/business/specs/`:
1. `glossario.md`
2. `requisitos_funcionais.md`
3. `requisitos_nao_funcionais.md`
4. `regras_negocio.md`
5. `workflows_bpmn.md`
6. `perfis_permissoes.md`
7. `catalogo_integracoes.md`

**Você valida:** 👤 Gate 2
- Termos do glossário estão consistentes entre os documentos?
- Os perfis de acesso cobrem todos os atores?
- As integrações listadas batem com a realidade?

**Só avance quando aprovar.**

---

### Passo 2: PRDs (Executivo + Técnico)

**Você faz:**

```
Execute a skill docs/skills/llc-step-2.md
```

**A IA faz:** Gera em `docs/prd/`:
- `executive_PRD.md` — para stakeholders e gestores (linguagem institucional)
- `PRD_tecnico_institucional.md` — para a equipe de desenvolvimento (linguagem técnica)

**Você valida:** 👤 Gate 3
- O PRD executivo comunica o valor do sistema claramente?
- O PRD técnico cobre todos os requisitos dos specs?
- Ambos são consistentes entre si?

**Só avance quando aprovar.**

---

### Passo 2.5: Casos de Uso (LLC)

#### Step 2.5 — Casos de Uso (LLC)

> 📖 Skill: `docs/skills/llc-step-2-5.md`

Deriva Casos de Uso dos PRDs validados. Cada CU descreve um objetivo de negócio com atores, fluxos e regras. Servem como âncora de rastreabilidade entre negócio e técnica.

**Entrada:** PRDs validados (Step 2), specs, módulos
**Saída:** `docs/business/use-cases/CU-NNN-[nome].md` + `INDEX.md`
**Gate:** 👤 Gate 3.5 — Aprovação em lote dos CUs

#### 👤 Gate 3.5 — Aprovação dos Casos de Uso

**Checklist:**
- [ ] CUs cobrem todos os objetivos de negócio dos PRDs?
- [ ] Cada CU tem atores identificados?
- [ ] Granularidade adequada (≤15 passos no fluxo principal)?
- [ ] Matriz de rastreabilidade CU↔RF completa?
- [ ] INDEX.md atualizado com todos os CUs?

**Só avance quando aprovar.**

---

### Passo 3: PRPs (Project Requirement Proposals)

**Você faz:**

```
Execute a skill docs/skills/llc-step-3.md
```

**A IA faz:** Gera arquivos `PRP-001-[nome].md`, `PRP-002-[nome].md`, etc. em `docs/prps/`. Cada PRP é um contrato auto-contido de implementação.

**Você valida:** 👤 Gate 4
- A granularidade dos PRPs está adequada (2-8 dias cada)?
- As dependências entre PRPs fazem sentido?
- Nenhum requisito do PRD ficou sem PRP?

**Só avance quando aprovar.**

---

### Passo 4: Planejamento (Matriz + Plano + Ondas)

**Você faz:**

```
Execute a skill docs/skills/llc-step-4.md
```

**A IA faz:** Gera em `docs/planning/`:
- `DEPENDENCY_MATRIX.md` — grafo de dependências e caminho crítico
- `PLAN.md` — roadmap, milestones, DoD
- `EXECUTION_WAVES.md` — ondas de execução com PRPs agrupados

**Você valida:** 👤 Gate 5
- As ondas estão bem agrupadas?
- O caminho crítico é realista?
- O tempo total estimado faz sentido?

**Só avance quando aprovar.**

---

### Passo 5: Arquitetura

**Você faz:**

```
Execute a skill docs/skills/llc-step-5.md
```

**A IA faz:** Gera:
- `docs/architecture/ARCHITECTURE.md` — documento principal com stack, C4, segurança, CI/CD
- `docs/architecture/adr/ADR-*.md` — **ADRs em arquivos individuais** (template em `ADR_TEMPLATE.md`)
- `.ace/arch-config.yaml` — configuração das fitness functions (módulos core e thresholds)

**Seções expandidas do template ARCHITECTURE_TEMPLATE.md:**
- **Stack tecnológico** com justificativas e alternativas descartadas
- **Diagramas C4** (contexto, containers, componentes)
- **ADRs em arquivos separados** (diff granular, referência individual em PRs)
- **Camada de Domínio e Ports & Adapters** — estrutura intra-módulo (`domain/`, `application/`, `infrastructure/`), regras DIP, exemplo de código
- **Casos de Uso** — one class per use case com `execute(dto)`
- **Comunicação entre Módulos** — EventEmitter2 para monólito, matriz de eventos pub/sub
- **Fitness Functions** — `.ace/arch-config.yaml` com módulos core e thresholds
- **Estratégia de segurança e CI/CD**

**Você valida:** 👤 Gate 6
- O stack é viável no seu ambiente?
- As decisões arquiteturais são justificadas?
- Os RNFs de performance e segurança estão endereçados?
- Os ADRs estão em arquivos separados e endereçam os 5 tópicos obrigatórios?
- A configuração de fitness functions (.ace/arch-config.yaml) está correta?

**Só avance quando aprovar.**

---

### Passo 5a: Architecture Patterns (Padrões Arquiteturais Obrigatórios)

> **OBRIGATÓRIO** — Este sub-step deve ser executado após o Step 5 e antes do Step 8.
> Os padrões definidos aqui são vinculantes e verificados por fitness functions automatizadas.

**Você faz:**

```
Execute a skill docs/skills/llc-step-5a-architecture-patterns.md
```

**A IA faz:** Usa o template `docs/templates/ARCHITECTURE_PATTERNS_TEMPLATE.md` para definir e documentar:
- **Clean Architecture Layers** — estrutura `domain/`, `application/`, `infrastructure/` por módulo
- **Repository Pattern** — interfaces `I{Nome}Repository` + implementações `Prisma{Nome}Repository`
- **Domain Layer Puro** — entidades de domínio sem decoradores, sem imports de framework
- **Use Cases** — uma classe por caso de uso com método `execute(dto)`
- **Event Bus** — comunicação assíncrona entre módulos via EventEmitter2

**Artefatos gerados/atualizados:**
- `docs/architecture/ARCHITECTURE.md` — seções §7, §8, §9 expandidas com exemplos de código
- `.ace/arch-config.yaml` — configuração completa das fitness functions (25+ rules)
- `docs/architecture/adr/ADR-008` a `ADR-011` — ADRs para Repository Pattern, Domain Layer, Use Cases, Event Bus

**Você valida:** 👤 Gate 6a
- Os padrões arquiteturais estão adequados ao projeto (greenfield vs brownfield)?
- O `.ace/arch-config.yaml` reflete os módulos core corretos?
- Os ADRs 008-011 estão criados e justificados?
- A estrutura de pastas intra-módulo está definida?

**Só avance quando aprovar.**

---

### Passo 5b: API Design Enforcement (Design de API — Obrigatório)

**Você faz:**

```
Execute a skill docs/skills/llc-step-5b-api-design.md
```

**A IA faz:** Executa o pipeline de API Design baseado no processo ADD-R (Higginbotham):

1. **Align** — Verifica alinhamento dos recursos com domínio de negócio (Vision + Modules + 7 Specs)
2. **Define** — Define contratos de recursos, operações, parâmetros, status codes
3. **Design** — Gera `docs/templates/CONTROLLER_TEMPLATE.ts` customizado por módulo
4. **Refine** — Executa fitness functions (`--check-api-design`) para validar:
   - Naming consistency (PT/EN, camelCase query params, kebab-case paths)
   - REST semantics (PUT vs PATCH, RPC endpoints → PATCH { status })
   - Nested resources modeling
   - Duplicate endpoint detection
   - HTTP status code decorators (@HttpCode)
   - Error response documentation (@ApiResponse 401/403/404/422)
   - Pagination coverage + standard envelope
   - API versioning (api/v1/ prefix)
   - OpenAPI spec existence + completeness
   - HATEOAS links in responses
   - BearerAuth security scheme

**Artefatos gerados/atualizados:**
- `docs/api/openapi.yaml` — OpenAPI 3.0 spec completo
- `docs/templates/CONTROLLER_TEMPLATE.ts` — Template customizado por módulo
- Controllers NestJS atualizados conforme template
- `.ace/arch-config.yaml` — Regras de API design ativadas

**Você valida:** 👤 Gate 6b
- OpenAPI spec existe em `docs/api/openapi.yaml` e é válida?
- Todos os controllers seguem o template padronizado?
- Fitness functions `--check-api-design` passam sem bloqueios?
- Recursos aninhados modelados corretamente (ex: `/auditorias/:id/achados`)?
- Endpoints RPC migrados para PATCH { status }?
- Paginação implementada em todos os endpoints de lista?
- Versionamento `api/v1/` presente em todos os controllers?

**Só avance quando aprovar.**

---

### Passo 5c: Clean Code Enforcement (Obrigatório)

> **OBRIGATÓRIO** — Este sub-step deve ser executado após o Step 5b e antes do Step 6.
> As 29 verificações de Clean Code são vinculantes e verificadas por fitness functions automatizadas.

**Você faz:**

```
Execute a skill docs/skills/llc-step-5c-clean-code.md
```

**A IA faz:** Executa o pipeline de Clean Code consolidado (29 checks em 7 dimensões):

1. **Funções** — Tamanho (≤20 linhas), Parâmetros (≤3), Responsabilidade única
2. **Classes** — SRP, ≤5 deps, ≤100 linhas, DIP, Coesão, Entidades ricas, Use Cases
3. **Nomes** — Sem `data`/`dto`/`result`/`info`/`obj`, Verbos em métodos, Consistência PT/EN
4. **Erros** — Zero exceções vazias, Zero catch vazio, Magic numbers → constantes
5. **Smells** — Código morto, Comentários ruído, `let`→`const`, `as any` proibido
6. **ReadModels** — Repositórios retornam ReadModels tipados, Zero `any` em público
7. **Deep Clean** — CQS, `return null`, data clumps, flag arguments, primitive obsession, validação ausente, pass-through (skill `llc-step-clean-code-deep`)

**Artefatos gerados/atualizados:**
- `.ace/arch-config.yaml` — Regras de Clean Code ativadas/thresholds por módulo
- `docs/architecture/adr/ADR-012` a `ADR-014` — ReadModels, Use Cases, Thresholds
- Relatórios de violações por arquivo: linha, regra, sugestão de fix

**Você valida:** 👤 Gate 8.5
- Fitness functions `--check-clean-code` passam sem **bloqueios**?
- Zero injeção de `PrismaService` em services/use-cases?
- Todos os repositórios retornam `XxxReadModel` tipado?
- Entidades de domínio têm métodos de negócio (não anêmicas)?
- Use Cases separados por operação (não service monolítico)?
- Nomes semânticos em todo código novo (`auditoriaEncontrada` vs `data`)?
- Zero exceções vazias (`NotFoundException('')`)?
- Zero `as any` em assinaturas públicas?
- **Deep Clean:** `--check-deep-clean --strict` passa sem bloqueios em módulos core (CQS, `return null`, flag arguments, validação ausente)?
- ADRs criados para decisões de Clean Code?

**Só avance quando aprovar.**

---

### Passo 5d: Secure-by-Design Enforcement (Obrigatório)

> **OBRIGATÓRIO** — Este sub-step deve ser executado após o Step 5c e antes do Step 6.
> Estabelece 10 hard gates de segurança que o agente carrega antes de gerar qualquer código.

**Você faz:**

```
Execute a skill docs/skills/llc-step-5d-secure-by-design.md
```

**A IA faz:** Estabelece o framework Secure-by-Design com:

1. **10 Hard Gates** — regras intransponíveis: NUNCA hardcode secrets, NUNCA usar XOR/MD5, NUNCA reusar IV, NUNCA AsyncStorage para tokens, NUNCA SQL com interpolação, NUNCA logar PII, NUNCA fallback que conceda privilégios, NUNCA validar premium no client, NUNCA AES-CBC, NUNCA tabelas sem user_id
2. **Threat Modeling Check** — 6 perguntas obrigatórias antes de cada feature (dados PII? armazenamento? proteção em repouso? em trânsito? acesso? fail-closed?)
3. **4 Safe Code Templates** — piiEncryption (AES-256-GCM), secureStorage (fail-closed), parameterizedQueries (anti-injeção), entitlementValidation (fail-safe)
4. **5 Fitness Functions de Segurança** — no-hardcoded-secrets, no-sql-injection, no-asyncstorage-tokens, no-client-only-auth, user-id-in-tables

**Artefatos gerados/atualizados:**
- `.ace/arch-config.yaml` — expandido com `security_rules`
- `docs/architecture/adr/ADR-018-secure-by-design.md`
- Fitness functions `--check-security` configuradas

**Você valida:** 👤 Gate 5d
- As 10 hard gates fazem sentido para o domínio do projeto?
- Algum template precisa de adaptação ao stack específico?
- Fitness functions `--check-security --strict` passam sem bloqueios?
- ADR-018 criado e justificado?
- Exceções documentadas (ex: projeto sem banco de dados → regra #10 não se aplica)?

**Só avance quando aprovar.**

---

### Passo 6: Tarefas

**Você faz:**

```
Execute a skill docs/skills/llc-step-6.md
```

**A IA faz:** Gera `docs/planning/TASKS.md` com:
- Tarefas concretas por PRP (scaffolding, backend, frontend, testes)
- Agentes atribuídos (dev_agent, qa_agent, security_agent)
- Paralelização explícita (✅ paralelo, ⚠️ após setup, ❌ sequencial)
- Estimativas em horas/dias

**Você valida:** 👤 Gate 7
- Todas as tarefas são acionáveis e sem ambiguidade?
- Os agentes estão corretamente atribuídos?
- As estimativas são realistas?

**Só avance quando aprovar.**

---

### Passo 7: Design System

**Você faz:**

```
Execute a skill docs/skills/llc-step-7.md
```

**A IA faz:** Gera `docs/design/DESIGN_SYSTEM.md` preenchendo o template `Design_System_Master.md` com:
- Design tokens (cores, tipografia, espaçamento, dark mode)
- Biblioteca de componentes (variantes, estados, props)
- Padrões de interface (tabelas, formulários, navegação, dashboards)
- Micro-interações e matriz de estados

**Você valida:** 👤 Gate 8
- A paleta de cores reflete a identidade do projeto?
- Todos os componentes têm estados definidos (loading, empty, error)?
- O Design System cobre os fluxos do sistema?

**Só avance quando aprovar.**

---

### Passo 8: Setup + Camada de Dados Mockados

**Você faz:**

```
Execute a skill docs/skills/llc-step-8.md
```

**A IA faz:**
- Inicializa o projeto com o stack definido (lint, type-check, dependências)
- Cria `mocks/data/` com JSONs realistas (usuários por perfil + entidades)
- Cria `mocks/handlers/` com CRUD completo via MSW
- Atualiza `TASKS.md` e PRPs com progresso

**Você valida:** 👤 Gate 9
- O projeto compila e roda localmente?
- Os dados mock são realistas e cobrem todos os perfis?
- Os handlers simulam erros corretamente?

**Só avance quando aprovar.**

---

### Passo 8b: Repository Pattern (Obrigatório)

> **OBRIGATÓRIO** — Este sub-step deve ser executado após o Step 8 (setup + mocks) e antes do Step 11 (Execução).
> Implementa o Repository Pattern com interfaces (Ports & Adapters) em todos os módulos.

**Você faz:**

```
Execute a skill docs/skills/llc-step-8b-repository-pattern.md
```

**A IA faz:** Usa o template `docs/templates/REPOSITORY_PATTERN_TEMPLATE.md` para implementar:
- Interfaces de repositório `I{Nome}Repository` em `src/*/domain/repositories/`
- Implementações Prisma `Prisma{Nome}Repository` em `src/*/infrastructure/repositories/`
- Mappers Prisma → Domain em `src/*/infrastructure/mappers/`
- Bindings de Injeção de Dependência nos modules (`{ provide: I*Repository, useClass: Prisma*Repository }`)
- Atualiza Services para injetar interfaces (`@Inject(I*Repository)`), não `PrismaService`

**Artefatos gerados:**
- `src/*/domain/repositories/i*.repository.ts` — interfaces
- `src/*/infrastructure/repositories/prisma-*.repository.ts` — implementações
- `src/*/infrastructure/mappers/*.mapper.ts` — mappers
- `src/*/*.module.ts` — bindings DI atualizados
- `src/*/*.service.ts` — services atualizados para usar interfaces

**Você valida:** 👤 Gate 9b
- `grep -r "PrismaService" src/*/domain/ src/*/application/ src/*/use-cases/` — retorna vazio?
- Interfaces existem para todos aggregate roots?
- Implementações Prisma existem e delegam corretamente?
- Mappers cobrem todos os campos da entidade de domínio?
- Bindings DI existem em todos os modules?
- Fitness function `repository-pattern` passa: `python .ace/scripts/fitness-functions.py --check repository-pattern`?

**Só avance quando aprovar.**

---

### Passo 9: Documentação de Testes

**Você faz:**

```
Execute a skill docs/skills/llc-step-9.md
```

**A IA faz:** Gera em `docs/testing/`:
- `TESTING_GUIDE.md` — filosofia, pirâmide, templates de teste, estratégia de mocks
- `COVERAGE_BASELINE.md` — baseline de cobertura (ponto zero)
- `COVERAGE_PROGRESS.md` — metas por fase e tabela de progresso semanal

**Você valida:** 👤 Gate 10
- Os comandos de teste batem com o stack definido?
- Os thresholds de cobertura estão realistas (80% unitários, 70% integração)?
- Os templates de teste são reutilizáveis?

**Só avance quando aprovar.**

---

### Passo 10: Documentos do Projeto

**Você faz:**

```
Execute a skill docs/skills/llc-step-10.md
```

**A IA faz:**
- `README.md` na raiz — portal de entrada com badges, stack, como rodar, docs
- `docs/DEPLOYMENT.md` — ambientes, pipeline CI/CD, variáveis, rollback, monitoramento
- `CLAUDE.md` — arquivo de steering do projeto (stack, domínio, arquitetura, restrições, comandos)
- `AGENTS.md` — arquivo de steering do desenvolvedor (protocolo epistêmico, zonas, TDD), com o **Master Prompt** injetado a partir de `docs/templates/MASTER_PROMPT_TEMPLATE.md` — 5 harness blocks (SECURITY, ARCHITECTURE, CLEAN_CODE, TDD, DEVOPS — 28 regras rastreáveis a fitness functions) + gates obrigatórios (lint, build, arch:check, test, coverage)

#### CLAUDE.md vs AGENTS.md: Qual usar?

| Arquivo | Conteúdo | Quem usa |
|---------|----------|----------|
| **CLAUDE.md** | O QUE é o projeto — stack, domínio, DB, arquitetura, restrições LLC | Claude Code (exclusivo) |
| **AGENTS.md** | COMO o desenvolvedor trabalha — zonas, TDD, handoff, Grill Me | Padrão emergente: Cursor, Codex, Copilot CLI, opencode |

**Se sua ferramenta NÃO suporta `CLAUDE.md`:** Consolide tudo no `AGENTS.md` — adicione as seções de projeto (stack, domínio, restrições) ao template do AGENTS. O `<!-- @include AGENTS.md -->` no CLAUDE.md garante que ferramentas que suportam ambos não dupliquem regras.

**Você valida:** 👤 Gate 11
- Um dev novo consegue rodar o projeto em ≤ 10 min seguindo o README?
- O DEPLOYMENT cobre rollback e monitoramento?
- Não há secrets ou credenciais expostos?
- O Master Prompt foi injetado no `AGENTS.md` com todos os placeholders (`{{LINT_CMD}}`, `{{TEST_CMD}}`…) resolvidos para o stack do projeto?

**Só avance quando aprovar.**

---

### Passo 10.5: Manual do Usuario 🆕

**Voce faz:**

```
Execute a skill docs/skills/llc-user-guide.md
```

**A IA faz:**
- Le todos os PRPs e extrai as paginas declaradas na secao `user_docs`
- Gera `docs/user-guide/USER_GUIDE.md` — esqueleto completo com indice e navegacao
- Gera `docs/user-guide/index.md` — pagina inicial do manual
- Gera `docs/user-guide/visao-geral.md` — visao geral em linguagem de usuario final
- Gera `docs/user-guide/perfis/index.md` — guia indexado por perfil

**Voce valida:** 👤 Gate 11.5
- A estrutura cobre todos os modulos?
- Os perfis tem paginas relevantes?
- O indice e navegavel?
- A linguagem e adequada ao usuario final?

**So avance quando aprovar.**

---

### Passo 10.6: Auditoria de Seguranca 🆕

**Voce faz:**

```
Execute a skill docs/skills/llc-step-11-security.md
```

**A IA faz:**
- Executa **SCA** (npm audit ou pip-audit) — varredura de vulnerabilidades em dependencias
- Executa **SAST** (Semgrep) — analise estatica de codigo
- Executa **Secret Scanning** (Gitleaks) — deteccao de credenciais expostas
- Classifica achados por severidade (CVSS): 🔴 Critico (≥ 9.0), 🟡 Alto (7.0–8.9), 🟢 Medio/Baixo (< 7.0)
- Gera `docs/security/SECURITY_AUDIT_REPORT.md` com relatorio consolidado e recomendacoes

**Voce valida:** 👤 Gate 11-SEC
- 0 vulnerabilidades criticas (CVSS ≥ 9.0)?
- Nenhum secret real exposto (falsos positivos em mocks/docs sao ok)?
- Vulnerabilidades altas revisadas e decisao registrada?

**So avance quando aprovar.**

---

### Passo 10.7: Validacao de Contratos de Dados 🆕

**Voce faz:**

```
Execute a skill docs/skills/llc-step-12-null-safety.md
```

**A IA faz:**
- Le todos os PRPs e extrai definicoes de dados (TypeScript, Python, Prisma, tabelas Markdown)
- Verifica se todo campo declara nulabilidade explicita (`?`, `| null`, `Optional`)
- Verifica se campos nulaveis tem fallback documentado
- Verifica se endpoints declaram `maxBodySize`, `rateLimit`, `maxItems` (A06 — DoS prevention)
- Verifica se todo endpoint POST/PUT/PATCH tem schema de validacao (Zod, Pydantic, etc.)
- Gera `docs/security/NULL_SAFETY_REPORT.md` com inventario completo

**Voce valida:** 👤 Gate 12-NULL
- 0 campos sem especificacao de nulabilidade?
- 0 endpoints sem schema de validacao?
- Payload limits declarados nos PRPs?

**So avance quando aprovar.**

---

### Passo 10.8: Cobertura de Testes (Test Coverage Gate) 🆕

**Voce faz:**

```
Execute a skill docs/skills/llc-step-10-8-test-coverage.md
```

**A IA faz:**
- Executa `python .ace/scripts/llc.py gate run --gate test-coverage`
- Verifica cobertura global: statements ≥ 80%, branches ≥ 70%, functions ≥ 80%, lines ≥ 80%
- Verifica **zero arquivos de implementação com 0% de cobertura** (CRITICAL)
- Verifica caminhos críticos (auth, pagamentos, mutações de dados) ≥ 90%
- Detecta regressão de cobertura > 5% vs. baseline anterior
- Gera relatório em `docs/testing/COVERAGE_REPORT.md` no formato padrão

**Voce valida:** 👤 Gate 10.8
- 0 arquivos de implementação com 0% cobertura?
- Thresholds globais atingidos (statements ≥ 80%, branches ≥ 70%, functions ≥ 80%, lines ≥ 80%)?
- Caminhos críticos ≥ 90%?
- Sem regressão > 5% vs. baseline?

**So avance quando aprovar.**

---

### Passo 11: Execucao

**Agora comeca o desenvolvimento.** Voce tem duas trilhas:

> **🔀 Isolamento automatico via git worktree:** A skill `llc-ace-context` cria automaticamente
> um worktree isolado para cada sessao de execucao (Step >= 11 ou quando `--prp` e informado).
> Cada PRP roda em seu proprio diretorio fisico (`prp-{id}/wave-{n}`), com `node_modules`,
> `dist/` e `.env` independentes — paralelismo real sem colisao de arquivos.
>
Ao finalizar, se o gate for `approved`, o branch e mergeado automaticamente e o worktree
> removido. Se `rejected`, o worktree e descartado sem merge.

> **🤖 Self-validation pós-geração:** antes de reportar qualquer task como concluída, o agente
> executa `bash .ace/scripts/llm-validation.sh` — 8 verificações sobre o código gerado
> (5 bloqueantes: secrets hardcoded, SQL com interpolação, `return null` em services, SQL fora
> de repositories, placeholder tests; 3 advertências: delays em testes, `any` em signatures,
> `console.*`). O hook `ace-llm-validation` no `.pre-commit-config.yaml` repete a barreira no commit.

### Passo 11a: Domain Modeling (Modelagem de Domínio — Obrigatório Pré-Execution)

> **OBRIGATÓRIO** — Para cada PRP core, execute este sub-step **antes** de iniciar a implementação (Trilha A ou B).
> Gera as entidades de domínio, use cases e interfaces de repositório específicas do PRP.

**Você faz:**

```
Execute a skill docs/skills/llc-step-11a-domain-modeling.md --prp PRP-001
```

**A IA faz:** Usa o template `docs/templates/DOMAIN_MODEL_TEMPLATE.md` para gerar:
- Entidades de domínio puras em `domain/`
- Use cases com `execute(dto)` em `application/use-cases/`
- Interfaces de repositório (se não existirem do Step 8b)
- PRP atualizado com §7 completo

**Você valida:** 👤 Gate 11-PRE
- Entidades refletem as regras de negócio do PRP?
- Use cases cobrem todos os RFs do PRP?
- Interfaces de repositório são consistentes com Step 8b?
- Contratos de dados (§7 do PRP) estão completos?

**Só avance para Trilha A/B quando aprovar.**

#### Trilha A: PRPs sem UI (backend, infra)

```
Execute as tarefas do TASKS.md diretamente com agentes de desenvolvimento.
Cada PRP sem UI e implementado sequencialmente ou em paralelo (conforme matriz).
```

#### Trilha B: PRPs com UI (frontend) — Subfluxo de Prototipagem

Para cada módulo ou PRP que envolva telas, execute:

```
Execute a skill docs/skills/llc-subflow-prototyping.md --module MOD-PLN-001
```

> **⚡ API-first enforcement:** Antes de iniciar F5 (Código), o harness executa verificação automática de contratos de backend via `_verify_backend_contracts()` em `llc_wave.py`. Se endpoints declarados no PRP não existirem ou forem stubs (`return []`), a onda **bloqueia** — o frontend não avança sobre contratos inexistentes. Isso previne o padrão: "TASKS.md marca ✅ → agente assume pronto → cria UI com placeholder → service ainda é `return []`".

O subfluxo tem 6 fases:

| Fase | O que acontece | Você faz |
|------|---------------|----------|
| **F1** Discovery | IA gera personas e journey maps | Revisa |
| **F2** Tokens | IA gera tokens CSS/JSON do Design System | Revisa |
| **F3** Lo-Fi | IA gera wireframes de baixa fidelidade | Revisa |
| **F4** Hi-Fi | IA gera protótipo de alta fidelidade | 🔴 **CHECKPOINT VISUAL** — Aprova o visual |
| **F5** Código | IA gera componentes e páginas | Revisa |
| **F6** Validação | IA valida usabilidade, a11y, responsividade | Revisa |

---

### Passo 11.2: PRP Verify (Aceite Mecânico de PRP)

**Antes do merge, o PRP passa por verificação mecânica de aceite.** O `prp_verify.py`
cruza cada RF declarado na §2 do PRP com os arquivos reais de teste e implementação.

> **Enforcement mecânico:** O `session_end()` do harness bloqueia o merge em CRITICAL
> (arquivo declarado ausente, stub, componente faltando). Bypass: `LLC_PRP_NO_VERIFY=1`
> (logado — veja `llc-pipeline-design.md §8.7`).
>
> **Novo:** `prp_verify.py` agora executa `check_project_coverage()` — verifica cobertura
> global do projeto (não só do PRP). Thresholds: statements ≥ 80%, branches ≥ 70%,
> functions ≥ 80%, lines ≥ 80%; **0 arquivos com 0% cobertura**; caminhos críticos ≥ 90%.

```
Execute a skill docs/skills/llc-step-11-2-prp-verify.md
```

**A IA faz:**
- Executa `python .ace/scripts/prp_verify.py --prp {ID} --strict --json`
- Emite relatório RF-por-RF com evidências de implementação
- Registra `<gate_result step="11.2">` com a decisão

**Nota:** `_post_wave_check()` também bloqueia ondas com CRITICAL — a verificação
ocorre tanto no nível de PRP individual (session_end) quanto no nível de onda
(pós-onda). A verificação de cobertura do projeto inteiro roda como parte do `prp_verify.py --all`.

### Passo 11b: Arch Fitness (Fitness Functions Arquiteturais — Obrigatório no PRP Verify)

> **OBRIGATÓRIO** — Executado como parte do `prp_verify.py` e do Gate 11.2.
> Verifica se a implementação do PRP viola alguma fitness function arquitetural.

**Execução automática:**
- `prp_verify.py` chama internamente `fitness-functions.py --all --strict`
- Também executável manualmente: `python .ace/scripts/fitness-functions.py --all --strict`

**Checks validados (conforme `.ace/arch-config.yaml`):**
- **Dependency Rule** — domínio não importa infraestrutura
- **Circular Dependencies** — sem ciclos entre módulos
- **Interface Coverage** — todos aggregate roots têm `I{Nome}Repository`
- **Domain Isolation** — `domain/` não importa `@prisma/client`, `repositories/`, `prisma/`
- **Use Case Size** — use cases ≤ 200 linhas, responsabilidade única
- **Module Coverage** — módulos core ≥ 90% cobertura, demais ≥ 80%
- **Clean Code + Deep Clean + Segurança + UX** — 34 checks adicionais via `--check-clean-code`, `--check-deep-clean`, `--check-security`, `--check-ux` (40 checks no total com `--all`)

**Você valida:** 👤 Gate 11.2 inclui fitness functions
- `python .ace/scripts/fitness-functions.py --all --strict` passa (exit 0)?
- Nenhuma violação BLOCKING em módulos core?
- Violações WARNING são aceitáveis com justificativa documentada?

**Só aprove se fitness functions passarem.**

---

---

## 🔄 Modo Delta: Mudancas em Sistema Existente

**Quando usar:** Quando o sistema ja passou pelo pipeline completo ao menos uma vez e novos documentos de mudança chegam.

### Visao Geral

O fluxo delta substitui os Steps 0-0.1 por uma **analise de impacto** focada no que muda, e introduz **Smart Skip** para reaproveitar artefatos inalterados:

```
Novos documentos em ingestion/
    ↓
[Thin Harness] llc delta start --iteration v2
    ↓
Step Δ.0 → impact-analyzer.py --classify → DELTA_REPORT.md (major/minor)
    ↓ 👤 Gate Δ.0
Step Δ.1 → Grill Me de Mudança (8 perguntas focadas no delta)
    ↓ 👤 Gate Δ.1
[Thin Harness] llc pipeline --delta --iteration v2
    ↓ Smart Skip
Steps inalterados → ⏭️ Skip Note + Gate auto-aprovado
Steps afetados     → ✅ Execução normal (modo diff/addendum)
    ↓
PRP-A (amendment) para mudancas em PRPs existentes
PRP-N (new) para funcionalidades totalmente novas
    ↓
Execucao, verificacao e deploy
```

### Comandos do Thin Harness para Modo Delta

```bash
# 1. Iniciar analise de impacto
llc delta start --iteration v2

# 2. Ver o plano delta
llc delta plan

# 3. Executar pipeline com smart skip
llc pipeline --delta --iteration v2

# 4. Executar step unico com smart skip
llc run --step 3 --delta

# 5. Modo CI/CD (auto-aprova todos os gates)
llc pipeline --delta --iteration v2 --auto-approve
```

### Classificacao Major vs Minor

A classificacao e feita automaticamente pelo `impact-analyzer.py --classify`:

**MAJOR** se afeta: arquitetura, design system, perfis/permissoes, migrations/schema, config de infraestrutura, ou 3+ PRPs.

**MINOR** se afeta apenas: 1-2 PRPs (codigo apenas), novos RFs sem alterar existentes, hotfix, cosmetico.

### Smart Skip (Steps Condicionais)

Os seguintes steps sao automaticamente pulados se o DELTA_REPORT.md indicar que nao sao afetados:

| Step | Pular quando | Gate |
|------|-------------|------|
| 0.5 (Visao) | Escopo/visao inalterados | ✅ Auto-aprovado |
| 1 (Specs) | Nenhum spec afetado | ✅ Auto-aprovado |
| 2 (PRDs) | PRDs inalterados | ✅ Auto-aprovado |
| 5 (Arquitetura) | Stack/ADRs inalterados | ✅ Auto-aprovado |
| 5d (Secure-by-Design) | Regras de segurança inalteradas | ✅ Auto-aprovado |
| 7 (Design System) | Tokens/componentes inalterados | ✅ Auto-aprovado |
| 8 (Setup + Mock) | Modelo de dados inalterado | ✅ Auto-aprovado |
| 9 (Testing Docs) | Estrategia de testes mantida | ✅ Auto-aprovado |
| 10.5 (User Guide) | UI inalterada | ✅ Auto-aprovado |

Steps **sempre executados** (mesmo em modo delta): 10 (Project Docs), 10.6-10.8 (Seguranca), 11 (Execucao), 11.1 (OWASP), 11.2 (PRP Verify).

### PRP de Alteracao (PRP-A)

Para mudancas em funcionalidades existentes, o Step 3 (modo delta) gera **PRP-A** (Amendment) em vez de PRPs inteiramente novos. O template esta em `docs/templates/PRP_AMENDMENT_TEMPLATE.md` e inclui:

- Referencia ao PRP original
- Resumo do delta (RFs novos, alterados, removidos)
- Contratos de API em diff (antes vs depois, com indicador de breaking change)
- Arquivos a modificar vs criar vs remover
- Garantia de nao regressao (testes inalterados continuam passando)

---

## Fluxo de Aprovação

```
                    👤 = Gate humano obrigatório
                    🔴 = Checkpoint visual obrigatório

Step 0 ──→ Step 0.1 ──→ Step 0.5 ──👤──→ Step 1 ──👤──→ Step 2 ──👤──→ Step 3 ──👤──→
Step 4 ──👤──→ Step 5 ──👤──→ Step 5a ──👤──→ Step 5b ──👤──→ Step 5c ──👤──→ Step 5d ──👤──→ Step 6 ──👤──→ Step 7 ──👤──→
Step 8 ──👤──→ Step 9 ──👤──→ Step 10 ──👤──→
Step 10.5 ──👤──→ Step 10.6 ──👤──→ Step 10.7 ──👤──→ Step 10.8 ──👤──→

Step 11:
  ├── PRPs sem UI → agente direto
  └── PRPs com UI → F1→F2→F3→F4─🔴─→F5→F6
```

**Regra de ouro:** Nenhum passo avança sem o gate anterior aprovado.

---

## Dicas Práticas

### Se um skill falhar
- Leia o erro. A IA vai reportar o que deu errado.
- Corrija a entrada (ex: documento faltando, template incompleto).
- Re-execute o skill.

### Se um gate for reprovado
- Anote o que precisa ser ajustado.
- Peça à IA para corrigir: "O glossário está inconsistente com os requisitos funcionais. Corrija."
- Re-valide.

### Monitorando a Saúde do Código

Com múltiplos agentes atuando em paralelo, é essencial monitorar métricas estruturais:

```
Execute a skill docs/skills/llc-code-health.md
```

Ou diretamente via script:

```
python .ace/scripts/code-health.py --since "30 days ago"
```

O script analisa métricas estruturais + cobertura de testes:

**Métricas estruturais:**
- **% Moved Code:** taxa de código reorganizado em módulos (alerta se < 10%)
- **Copy/Paste vs Moved:** duplicação superando reuso (alerta se copy > moved)
- **% Legacy Touch:** código antigo sendo refatorado (alerta se < 20%)

**Cobertura de testes (novo):**
- **Global statements ≥ 80%**, branches ≥ 70%, functions ≥ 80%, lines ≥ 80%
- **CRÍTICO:** 0 arquivos de implementação com 0% cobertura
- **Caminhos críticos** (auth, pagamentos, mutações de dados) ≥ 90%
- **Regressão de cobertura:** queda > 5% = alerta crítico

Se alertas críticos forem disparados, agende uma onda de refatoração cross-PRP.

### Verificando Conformidade Arquitetural (Fitness Functions)

A partir da v1.7.0, o LLC inclui **fitness functions** para validacao arquitetural automatizada:

```bash
# Executar todas as fitness functions
python .ace/scripts/fitness-functions.py --all

# Modo estrito (exit code 1 se houver violacao)
python .ace/scripts/fitness-functions.py --all --strict

# JSON para integracao com ferramentas
python .ace/scripts/fitness-functions.py --all --json
```

As fitness functions verificam: Dependency Rule (Ports & Adapters), dependencias circulares, cobertura de interfaces (DIP), isolamento do dominio, tamanho de use cases e cobertura por modulo. O comportamento (block vs warn) e configurado em `.ace/arch-config.yaml`.

### Ferramentas Transversais do Pipeline

Alem dos steps principais, o LLC inclui ferramentas que operam entre etapas. Consulte o [`llc-pipeline-design.md`](llc-pipeline-design.md) para documentacao completa:

| Ferramenta | Skill / Script | Funcao | Pipeline Design |
|-----------|----------------|--------|:--------------:|
| **Analisador de Impacto** | `llc-impact-analyzer` | Detecta quais artefatos downstream sao afetados por alteracoes. Use antes de refatorar. | [§9](llc-pipeline-design.md#9-rastreabilidade-e-analise-de-impacto) |
| **Fitness Functions** | `fitness-functions.py` | [NOVO] Verifica conformidade arquitetural: Dependency Rule, DIP, modulos isolados. | [§11](llc-pipeline-design.md#11-fitness-functions---conformidade-arquitetural) |
| **Code Health** | `llc-code-health` | Monitora metricas estruturais (Moved Code, Copy/Paste, Legacy Touch). Use a cada onda. | [§10](llc-pipeline-design.md#10-saude-estrutural-do-codigo-code-health) |
| **ACE Context** | `llc-ace-context` | Protocolo de continuidade entre sessoes. Gerenciado automaticamente pelo harness. | [§8](llc-pipeline-design.md#8-ace--agentic-context-engineering) |

**Modos de operacao da LLM:** Para Steps 0-10 (especificacao), use modo Thinking/Reasoning. Para Step 11 (execucao), modo Regular. Para correcoes pos-gate reprovado, modo Thinking. Veja a tabela completa acima em [Modo de Operacao da LLM](#modo-de-operacao-da-llm).

### Se precisar recomeçar um passo
- Skills são idempotentes. A IA perguntará antes de sobrescrever arquivos existentes.
- Responda "sim, sobrescreva" ou "não, crie uma nova versão com sufixo _v2".

### Trabalhando em equipe
- O pipeline suporta múltiplos usuários. Cada gate é um ponto natural de sincronização.
- Use branches Git para isolar o trabalho de cada passo, se desejar.
- Os artefatos são arquivos Markdown — use PRs para revisão colaborativa.

---

## Referência Rápida

| Quero... | Comando |
|----------|---------|
| Iniciar o pipeline | `Execute a skill docs/skills/llc-step-0-1.md` (conversão) |
| Iniciar fluxo delta | `llc delta start --iteration v2` |
| Ver plano delta | `llc delta plan` |
| Executar pipeline delta | `llc pipeline --delta --iteration v2` |
| Executar step com smart skip | `llc run --step 3 --delta` |
| Pular para um passo específico | `Execute a skill docs/skills/llc-step-N.md` certificando-se de que os gates anteriores foram aprovados |
| Prototipar um módulo | `Execute a skill docs/skills/llc-subflow-prototyping.md --module MOD-PLN-001` |
| Gerar manual do usuario | `Execute a skill docs/skills/llc-user-guide.md` |
| Garantir que toda onda vire sessão no `.ace` | Instale o pre-commit: `cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit` (ver [§8.7](llc-pipeline-design.md#87-registro-garantido-de-sessões-session-enrollment-enforcement)) |
| Verificar cobertura de testes (Gate 10.8) | `python .ace/scripts/llc.py gate run --gate test-coverage` |
| Executar pre-wave-check (build + boot + health + coverage) | `bash .ace/scripts/pre-wave-check.sh` |
| Verificar conformidade arquitetural | `python .ace/scripts/fitness-functions.py --all` |
| Ver código health trends + fitness | `python .ace/scripts/code-health.py --since "30 days ago" --json --fitness` |
| Abrir a TUI do wizard (Kanban do grafo) | `python .ace/scripts/llc.py wizard` (caminho crítico 🔺, próximo step ➤, swimlanes por wave; fallback `--source index`) |
| Relatório de gargalos (critical_path × flow-metrics) | `python .ace/scripts/llc.py eval flow-report` |
| Dashboard Pareto custo×qualidade | `python .ace/scripts/llc.py eval --report` |
| Verificar conformidade arquitetural | `python .ace/scripts/fitness-functions.py --all` |
| Ver o design completo | Leia [`llc-pipeline-design.md`](llc-pipeline-design.md) |
| Ver a estrutura de diretórios | Leia [`llc-pipeline-design.md` §2](llc-pipeline-design.md#2-arquitetura-de-diretórios) |
| Entender um termo | Leia [`llc-pipeline-design.md` §8](llc-pipeline-design.md#8-glossário-llc) |

---

## Próximos Passos Após o Pipeline

1. O MVP mockado está rodando → valide com stakeholders
2. CHECKPOINT MVP aprovado → implemente integrações reais
3. Integrações funcionando → implante em staging
4. Testes de aceite passando → implante em produção
5. Monitore e itere
