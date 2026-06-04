---
name: llc-step-4
description: Pipeline LLC Passo 4: Gera artefatos de planejamento (Matriz de Dependências, Plano e Ondas de Execução) a partir dos PRPs.
version: 1.0.0
tags: [planning, waves, llc-pipeline]
---

# LLC Skill: Step 4 — Planejamento (Matrix + Plan + Waves)

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Planning  
**Depende de:** Step 3 (PRPs validados)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-4` ou "Execute a skill llc-step-4".

## 📋 Pré-requisitos

- [ ] PRPs em `docs/prps/PRP-*.md` (validados no Step 3)
- [ ] `docs/planning/DEPENDENCY_MATRIX_TEMPLATE.md`
- [ ] `docs/planning/PLAN_TEMPLATE.md`
- [ ] `docs/planning/EXECUTION_WAVES_TEMPLATE.md`

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-4` do pipeline LLC. Seu objetivo é transformar os PRPs em um plano de execução estruturado com matriz de dependências, roadmap e ondas.

### Documentos a Gerar

| # | Documento | Template | Destino |
|---|-----------|----------|---------|
| 1 | Matriz de Dependências | `docs/planning/DEPENDENCY_MATRIX_TEMPLATE.md` | `docs/planning/DEPENDENCY_MATRIX.md` |
| 2 | Plano de Entregas | `docs/planning/PLAN_TEMPLATE.md` | `docs/planning/PLAN.md` |
| 3 | Ondas de Execução | `docs/planning/EXECUTION_WAVES_TEMPLATE.md` | `docs/planning/EXECUTION_WAVES.md` |

### 1. Leia as Entradas
- Leia TODOS os PRPs em `docs/prps/`.
- Extraia de cada PRP: ID, estimativa, dependências, complexidade, prioridade, módulo de origem.
- Leia os três templates em `docs/planning/`.

### 2. Gere a Matriz de Dependências
- Mapeie o grafo completo de dependências entre PRPs.
- Identifique o caminho crítico (critical path).
- Calcule o tempo total estimado (sequencial vs. paralelo).
- Agrupe PRPs por afinidade e dependências para definir ondas.
- Salve em: `docs/planning/DEPENDENCY_MATRIX.md`.

### 3. Gere o Plano de Entregas (PLAN.md)
- Roadmap com milestones e datas-alvo.
- Definição de Done (DoD) para o projeto.
- Estratégia de deploy (dev, staging, prod).
- Master PRP List com estimativas e status.
- Velocity tracker e burndown inicial.
- Salve em: `docs/planning/PLAN.md`.

### 4. Gere as Ondas de Execução (EXECUTION_WAVES.md)
- Agrupe PRPs em ondas (Waves) de 1 a 2 semanas cada.
- Critérios para agrupamento:
  - PRPs sem dependências → Onda 1
  - PRPs cujas dependências estão em ondas anteriores → ondas subsequentes
  - Máximo de 4-6 PRPs por onda (evitar gargalos)
- Para cada onda: PRPs incluídos, datas, time alocado, riscos.
- Salve em: `docs/planning/EXECUTION_WAVES.md`.

---

## ⚠️ REGRAS CRÍTICAS

1. **Caminho Crítico:** Deve ser explícito e visível na matriz.
2. **Paralelismo:** Maximize PRPs executáveis em paralelo dentro de cada onda.
3. **Realismo:** Estimativas devem somar folga de 20% para imprevistos.
4. **Rastreabilidade:** Cada PRP na matriz deve linkar para seu arquivo em `docs/prps/`.
5. **Idempotência:** Verifique existência dos arquivos de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar os 3 arquivos, **PARE** e apresente:

1. **Matriz:** Quantos PRPs, quantas dependências, duração do caminho crítico.
2. **Plano:** Quantas ondas, tempo total estimado, data prevista de conclusão.
3. **Paralelismo:** Economia de tempo vs. execução sequencial (ex: "35 dias em paralelo vs. 75 dias sequencial = 53% de economia").
4. **Ondas:** Resumo de cada onda (PRPs, duração, time necessário).
5. **Próximos Passos:** Perguntas para validação humana sobre prioridades e alocação de time.

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
