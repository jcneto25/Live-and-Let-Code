---
template_version: "1.0.0"
template_name: "llc-step-2-5"
last_updated: "2026-07-28"
---

# Step 2.5 — Casos de Uso

## Pré-requisitos

### Modo Padrão (Greenfield)
- [ ] `docs/prd/executive_PRD.md` e `docs/prd/PRD_tecnico_institucional.md` (validados no Step 2)
- [ ] 7 specs em `docs/business/specs/` (base de referência)
- [ ] `docs/business/specs/MOD-*.md` (módulos validados)
- [ ] `docs/business/use-cases/TEMPLATE_CU.md`

### Modo Delta
- [ ] `docs/planning/DELTA_REPORT.md` aprovado (Gate Δ.0)
- [ ] Step Δ.1 concluído
- [ ] CUs existentes em `docs/business/use-cases/` (versão atual)

## Modo de Execução

### Passo 1: Ler PRDs validados
Leia `docs/prd/executive_PRD.md` e `docs/prd/PRD_tecnico_institucional.md`. Extraia todos os objetivos de negócio, funcionalidades descritas e atores mencionados.

### Passo 2: Ler specs de negócio
Leia as 7 specs em `docs/business/specs/`. Identifique regras de negócio, atores e requisitos não-funcionais relevantes.

### Passo 3: Ler módulos
Leia `docs/business/specs/MOD-*.md` para entender a estrutura modular do sistema.

### Passo 4: Gerar lista preliminar de CUs
Para cada objetivo de negócio identificado nos PRDs, gere um CU seguindo o template em `docs/business/use-cases/TEMPLATE_CU.md`. Regras:
- Cada CU descreve **um** objetivo de negócio claro
- Cada CU mapeia para **exatamente 1 módulo**
- Fluxo principal com **≤15 passos** (CUs maiores são subdivididos)
- Todos os atores do Step 1 devem aparecer em pelo menos 1 CU

### Passo 5: Apresentar lista para aprovação
Apresente a lista de CUs ao usuário em tabela:
| CU | Módulo | Objetivo | Atores | # Passos |
|----|--------|----------|--------|----------|

Aguarde aprovação, ajustes ou rejeição.

### Passo 6: Gerar arquivos CU
Após aprovação, gere cada arquivo `CU-NNN-[nome].md` em `docs/business/use-cases/`.

### Passo 7: Gerar INDEX.md
Gere `docs/business/use-cases/INDEX.md` com a matriz de rastreabilidade (CU ↔ RF ↔ PRP).

## Regras Críticas

1. **Nada novo** — Casos de Uso derivam dos PRDs/specs, nunca inventam funcionalidades
2. **Granularidade 1:1** — cada CU mapeia para 1 PRP; CUs muito grandes (>15 passos no fluxo) são subdivididos antes de virar PRPs
3. **Rastreabilidade bidirecional** — cada CU referencia RFs de origem (§8); cada PRP futuro referencia o CU de origem
4. **INDEX.md é a matriz** — tabela consolidada: CU | Atores | Módulo | RFs | PRP | Status

## Modo Delta (Smart Skip)

- Se Step 2 for "skip" → Step 2.5 também é pulado
- Se Step 2 for re-executado → Step 2.5 também é re-executado
- Se apenas PRPs novos → novos CUs são gerados, existentes permanecem

## Saída Esperada

Após gerar os CUs, a skill PARE e apresente:

1. **Resumo:** Quantos CUs gerados, organizados por módulo
2. **Atores cobertos:** Todos os perfis do Step 1 estão representados?
3. **Cobertura de PRDs:** Todos os objetivos de negócio do PRD executivo têm pelo menos 1 CU?
4. **Granularidade:** Algum CU com >15 passos que precise ser subdividido?
5. **Próximos Passos:** Perguntas para validação humana (Gate 3.5)

## Validação

- [ ] Todos os objetivos de negócio dos PRDs têm pelo menos 1 CU
- [ ] Todos os atores do Step 1 aparecem em pelo menos 1 CU
- [ ] Nenhum CU excede 15 passos no fluxo principal
- [ ] Cada CU referencia RFs de origem (§8)
- [ ] INDEX.md está completo e atualizado
