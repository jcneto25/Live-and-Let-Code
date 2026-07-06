# EXECUTION_WAVES_EXEMPLO.md

## Onda 1: Fundação e Autenticação

Esta onda cobre os componentes críticos básicos do sistema.

| PRP | Descrição | Estimativa | Dependencies |
|-----|-----------|------------|--------------|
| PRP-001 | Cadastro Básico de Usuários | 3 dias | - |
| PRP-002 | Autenticação JWT | 2 dias | PRP-001 |
| PRP-003 | Gerenciamento de Perfis | 3 dias | PRP-001 |

**Meta da Onda:** Sistema básico de login funcional

---

## Onda 2: Cadastros Principais

| PRP | Descrição | Estimativa | Dependencies |
|-----|-----------|------------|--------------|
| PRP-004 | Cadastro de Planos | 4 dias | Onda 1 completa |
| PRP-005 | CRUD de Auditorias | 5 dias | PRP-004 |

**Meta da Onda:** Módulo principal de auditorias funcional

---

## Onda 3: Relatórios e Visualização

| PRP | Descrição | Estimativa | Dependencies |
|-----|-----------|------------|--------------|
| PRP-006 | Dashboard de KPIs | 4 dias | PRP-004, PRP-005 |
| PRP-007 | Exportação de Relatórios | 3 dias | Onda 3 (início) |

**Meta da Onda:** Visualização de dados implementada

---

## Notas

- Toda onda passa por **Security Audit (pre-code)** e **OWASP Hardening (post-code)**
- Gates humanos obrigatórios após cada onda
- PRPs dentro da mesma onda podem ser executados em paralelo
