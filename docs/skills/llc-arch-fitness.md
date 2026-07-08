---
name: llc-arch-fitness
description: Verifica conformidade arquitetural via fitness functions — Dependency Rule, DIP, isolamento de domínio, dependências circulares, tamanho de use cases e cobertura por módulo. Gate 11-ARCH.
version: 1.0.0
tags: [architecture, fitness, quality, gate, llc-pipeline]
---

# LLC Skill: Architecture Fitness — Gate 11-ARCH

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Quality Assurance — Architecture Compliance  
**Quando usar:** Após Step 11 (Execução), antes do merge. Também executado automaticamente no pre-commit hook.  
**Pré-requisito:** Step 11 concluído, `.ace/arch-config.yaml` existente (gerado pelo Step 5).  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `docs/skills/` do projeto (já está lá).
2. Invoque no chat: `@llc-arch-fitness` ou "Execute a skill llc-arch-fitness".
3. Ou via Thin Harness: `python .ace/scripts/fitness-functions.py --all --json`

## 📋 Pré-requisitos

- [ ] `.ace/arch-config.yaml` — gerado pelo Step 5 (Arquitetura), define `core_modules` e thresholds
- [ ] `.ace/scripts/fitness-functions.py` — script de verificação
- [ ] Código implementado (Step 11 concluído)
- [ ] Projeto compila e testes passam

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-arch-fitness` do pipeline LLC. Seu objetivo é verificar a **conformidade arquitetural** do código implementado, executando as 6 fitness functions e registrando o resultado no Gate 11-ARCH.

### 1. Execute as Fitness Functions

```bash
python .ace/scripts/fitness-functions.py --all --json
```

Analise a saída JSON. Para cada check, verifique:

| Check | O que verifica | Passou se |
|-------|---------------|-----------|
| `dependency_rule` | Services não importam Prisma/infra diretamente | 0 violações em core modules |
| `circular_deps` | Nenhum módulo tem dependência circular | 0 ciclos |
| `interface_coverage` | Todo service tem interface (DIP) | 100% em core modules |
| `domain_isolation` | Domínio não importa infraestrutura | 0 violações em core modules |
| `use_case_size` | Services ≤ 8 métodos públicos | Apenas alertas (não bloqueia) |
| `module_coverage` | Cobertura mínima por módulo | Core ≥ 70%, geral ≥ 60% |

### 2. Classifique os Resultados

Para cada violação, classifique por severidade:

| Severidade | Significado | Ação |
|-----------|-------------|------|
| 🔴 **CRITICAL** | Core module violou regra com mode=block | **Bloqueia o merge** — correção obrigatória antes de prosseguir |
| 🟡 **WARNING** | Módulo periférico violou regra, ou alerta de use case size | **Registra em dívida técnica** — não bloqueia, mas documenta |
| 🟢 **PASS** | Sem violações | Segue sem ação |

### 3. Registre o Resultado

**Se aprovado (0 CRITICAL):**
- Gate 11-ARCH: ✅ APROVADO
- Registre no ACE: `<gate_result step="11-ARCH" decision="approved">`
- Prossiga para o merge

**Se rejeitado (1+ CRITICAL):**
- Gate 11-ARCH: ❌ REJEITADO
- Registre no ACE: `<gate_result step="11-ARCH" decision="rejected">`
- Liste as violações e as correções necessárias
- **Não prossiga para o merge** até que as violações sejam corrigidas

**Se aprovado com alertas:**
- Gate 11-ARCH: ✅ APROVADO (com ressalvas)
- Registre os alertas como `<learning_point priority="medium">` no ACE
- Crie tarefas de dívida técnica no TASKS.md

### 4. Ações Corretivas por Tipo de Violação

| Check | Correção Recomendada |
|-------|---------------------|
| `dependency_rule` | Extrair dependência de Prisma/infra para interface. Criar `I{nome}Repository` e implementar `Prisma{nome}Repository`. O service passa a depender da interface |
| `circular_deps` | Identificar o ciclo. Extrair tipos compartilhados para um módulo comum. Alternativa: usar eventos para quebrar o ciclo |
| `interface_coverage` | Criar arquivo `I{nome}.interface.ts` no mesmo diretório do service, com os métodos públicos |
| `domain_isolation` | Mover a dependência de infra para fora do domínio. Usar inversão de dependência |
| `use_case_size` | Extrair grupos de métodos em classes separadas: `Criar{nome}UseCase`, `Listar{nome}UseCase` |
| `module_coverage` | Adicionar testes unitários para o módulo. Focar nos caminhos críticos primeiro |

---

## ⚠️ REGRAS CRÍTICAS

1. **Core modules bloqueiam, periféricos alertam.** A distinção está em `.ace/arch-config.yaml` (gerado pelo Step 5). Não altere o config sem aprovação do arquiteto.

2. **Não silencie violações sem registro.** Se uma violação em módulo periférico for aceita, registre como `<learning_point priority="medium">` com justificativa.

3. **Fitness functions não substituem code review.** Elas pegam violações estruturais automatizáveis, mas não avaliam design, legibilidade ou adequação ao domínio.

4. **Reexecute após correção.** Após corrigir violações, execute `fitness-functions.py --all --strict` novamente para confirmar a correção antes do merge.

5. **Integração contínua.** No CI/CD, use `--strict --json` para falhar o pipeline automaticamente se houver violações.

---

## 📤 SAÍDA ESPERADA

1. **Resultado do Gate 11-ARCH:**
   - `decision: approved` — merge liberado
   - `decision: rejected` — merge bloqueado (core module violou)
   - `decision: conditional` — aprovado com alertas registrados

2. **Registro ACE:**
   ```xml
   <gate_result step="11-ARCH" decision="approved" reviewer="harness">
     dependency_rule: 0 violations (✅), circular_deps: 0 cycles (✅),
     interface_coverage: 85% (🟡 2 warnings, registered as technical debt),
     use_case_size: 3 warnings (🟡 registered as improvement backlog)
   </gate_result>
   ```

3. **Se houver dívida técnica:** Tarefas adicionadas em TASKS.md §Technical Debt
