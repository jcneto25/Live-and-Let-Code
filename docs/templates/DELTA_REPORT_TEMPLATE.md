# DELTA_REPORT.md — Relatório de Impacto de Mudanças

**Template:** v1.0.0  
**Pipeline:** Live and Let Code (LLC)  
**Gerado por:** Step Δ.0 (llc-step-delta-impact)  
**Quando usar:** Sempre que novos documentos de mudança forem recebidos para um sistema que já passou pelo pipeline LLC.

---

```
╔══════════════════════════════════════════════════════════════╗
║                    DELTA_REPORT.md                           ║
║         Análise de Impacto entre Versões                     ║
╚══════════════════════════════════════════════════════════════╝
```

## §1 Metadados da Iteração

| Campo | Valor |
|-------|-------|
| **Versão atual do sistema** | `v1.0` (ex: versão do último deploy) |
| **Iteração proposta** | `v2.0` |
| **Data da análise** | `YYYY-MM-DD` |
| **Classificação** | `[MAJOR / MINOR]` |
| **Novos documentos analisados** | `docs/business/ingestion/converted/[arquivos].md` |
| **Responsável pela análise** | `[nome/agente]` |

### Critérios de Classificação

**MAJOR** se qualquer um dos thresholds for atingido (marcar com ✅):

| Threshold | Status |
|-----------|--------|
| Afeta arquitetura (stack, ADRs, C4) | [ ] |
| Afeta Design System (tokens, componentes) | [ ] |
| Afeta perfis/permissoes | [ ] |
| Breaking changes em contratos de API | [ ] |
| Afeta 3+ PRPs existentes | [ ] |
| Afeta requisitos não-funcionais | [ ] |
| Afeta modelo de dados (migrations) | [ ] |

**MINOR** se apenas código/documentação for afetado (sem breaking changes):

| Threshold | Status |
|-----------|--------|
| 1-2 PRPs (código apenas) | [ ] |
| Novos RFs sem alterar existentes | [ ] |
| Hotfix / escopo cirúrgico | [ ] |
| Cosmética (UI/tradução) | [ ] |

---

## §2 Inventário de Artefatos

### 2.1 Artefatos Inalterados (skip — podem ser reaproveitados)

| Artefato | Caminho | Justificativa |
|----------|---------|---------------|
| `architecture` | `docs/architecture/ARCHITECTURE.md` | Stack e ADRs inalterados |
| `design_system` | `docs/design/DESIGN_SYSTEM.md` | Sem novos tokens ou componentes |
| `...` | `...` | `...` |

### 2.2 Artefatos a Revisar (precisam de validação humana)

| Artefato | Caminho | Impacto | Skill Sugerida |
|----------|---------|---------|----------------|
| `glossario` | `docs/business/specs/glossario.md` | +5 novos termos | llc-step-1 (diff mode) |
| `requisitos_funcionais` | `docs/business/specs/requisitos_funcionais.md` | RF-015 alterado, RF-016 novo | llc-step-1 (diff mode) |
| `...` | `...` | `...` | `...` |

### 2.3 Artefatos a Regenerar (precisam ser regerados do zero)

| Artefato | Caminho | Motivo | Skill |
|----------|---------|--------|-------|
| `prps` | `docs/prps/` | PRP-003 alterado, PRP-N-001 novo | llc-step-3 (delta mode) |
| `...` | `...` | `...` | `...` |

---

## §3 PRPs Afetados

### 3.1 PRPs Existentes Não Afetados

| PRP | Nome | Status |
|-----|------|--------|
| PRP-001 | Cadastro de Usuários | ✅ Mantido |
| PRP-002 | Recuperação de Senha | ✅ Mantido |
| ... | ... | ... |

### 3.2 PRPs Existentes com Alteração (PRP-A)

| PRP Original | PRP-A | Descrição da Mudança | Impacto |
|-------------|-------|---------------------|---------|
| PRP-003 | PRP-A-001 | Contrato `GET /api/relatorios` adiciona campo `periodo` | Breaking: resposta muda |
| PRP-007 | PRP-A-002 | Enum `status` expande de 2 para 4 valores | Migração de dados necessária |
| ... | ... | ... | ... |

### 3.3 PRPs Marcados para Deprecação

| PRP | Nome | Motivo | Alternativa |
|-----|------|--------|-------------|
| PRP-005 | Relatório Legacy | Substituído pelo novo módulo de BI | PRP-N-001 |
| ... | ... | ... | ... |

---

## §4 Novos PRPs Necessários (PRP-N)

| PRP-N | Nome | Descrição | Depende de |
|-------|------|-----------|------------|
| PRP-N-001 | Módulo de Auditoria | Novo módulo baseado no perfil "auditor" | PRP-A-001 |
| PRP-N-002 | Dashboard BI | Relatórios consolidados com nova integração | PRP-N-001 |
| ... | ... | ... | ... |

---

## §5 Plano de Execução Sugerido

### 5.1 Steps a Executar

| Step | Skill | Motivo | Gate |
|------|-------|--------|------|
| Δ.1 | `llc-step-delta-grill` | Resolver ambiguidades identificadas | 👤 Δ.1 |
| 0.5 | `llc-step-0-5` (diff mode) | Addendum à visão: novo perfil "auditor" | 👤 1 |
| 1 | `llc-step-1` (diff mode) | Glossário expandido, RFs alterados | 👤 2 |
| 2 | `llc-step-2` | PRDs v2 | 👤 3 |
| 3 | `llc-step-3` (delta mode) | PRP-A-001, PRP-A-002, PRP-N-001 | 👤 4 |
| 4 | `llc-step-4` | Matriz + ondas atualizadas | 👤 5 |
| 6 | `llc-step-6` | Tarefas de alteração + novas | 👤 7 |
| 10 | `llc-step-10` | Docs do projeto atualizados | 👤 11 |
| 10.5 | `llc-user-guide` | User guide atualizado (se UI afetada) | 👤 11.5 |
| 10.6 | `llc-step-11-security` | Segurança (sempre) | 👤 11-SEC |
| 10.7 | `llc-step-12-null-safety` | Contratos (sempre) | 👤 12-NULL |
| 10.8 | `llc-step-10-8-test-coverage` | Cobertura (sempre) | 👤 10-COVERAGE |
| 11 | `llc-step-11` | Execução PRP-A + PRP-N | QA |
| 11.1 | `llc-step-11-owasp-security` | OWASP (sempre) | 👤 11-OWASP |
| 11.2 | `llc-step-11-2-prp-verify` | PRP Verify (sempre) | 🔴 11-VERIFY |

### 5.2 Steps a Pular

| Step | Justificativa | Artefatos Reaproveitados |
|------|---------------|--------------------------|
| 5 | Arquitetura inalterada — gate revalidado por referência à aprovação anterior | `ARCHITECTURE.md` v1 |
| 7 | Design System inalterado — sem novos tokens ou componentes | `DESIGN_SYSTEM.md` v1 |
| 8 | Modelo de dados inalterado (mocks existentes continuam válidos) | `mocks/` v1 |
| 9 | Estratégia de testes mantida | `TESTING_GUIDE.md`, `COVERAGE_BASELINE.md`, `COVERAGE_PROGRESS.md` v1 |

### 5.3 Estimativa de Esforço

| Atividade | Estimativa |
|-----------|------------|
| Steps de especificação (Δ.1 → 3) | 2 dias |
| Steps de planejamento (4, 6) | 1 dia |
| Steps de documentação (10, 10.5) | 1 dia |
| Steps de segurança (10.6-10.8) | 1 dia |
| Execução (PRP-A-001, PRP-A-002, PRP-N-001) | 8 dias |
| Hardening + Verify (11.1, 11.2) | 1 dia |
| **Total** | **14 dias** |

---

## §6 Riscos e Observações

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|-------|---------------|---------|-----------|
| 1 | PRP-A-001 (breaking change) pode afetar consumidores da API não documentados | Média | Alto | Mapear consumidores conhecidos; versionar API se necessário |
| 2 | Migração de dados do PRP-007 (enum expandido) pode causar downtime | Baixa | Médio | Script de migração em múltiplos passos; validar em staging |
| 3 | Novo perfil "auditor" pode exigir alterações no middleware de autenticação | Média | Alto | Incluir no PRP-A-001 |
| ... | ... | ... | ... | ... |

---

## §7 Aprovação

| Gate | Status | Revisor | Data |
|------|--------|---------|------|
| 👤 **Gate Δ.0** | `[pending / approved / rejected / conditional]` | `[nome]` | `YYYY-MM-DD` |

**Observações do revisor:**
```
[Espaço para feedback do gate]
```
