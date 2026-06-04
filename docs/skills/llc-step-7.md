---
name: llc-step-7
description: Pipeline LLC Passo 7: Gera Design System completo com tokens, componentes, padrões e acessibilidade.
version: 1.0.0
tags: [design-system, ui, llc-pipeline]
---

# LLC Skill: Step 7 — Design System

**Pipeline:** Live and Let Code (LLC)  
**Fase:** UI/UX Foundation  
**Depende de:** Step 5 (Arquitetura validada)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-7` ou "Execute a skill llc-step-7".

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` (stack frontend definido no Step 5)
- [ ] `docs/business/specs/visao_estrategica_e_negocio.md` (identidade institucional)
- [ ] `docs/business/specs/perfis_permissoes.md` (para UI consciente de permissões)
- [ ] `docs/design/Design_System_Master.md` (template expandido)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-7` do pipeline LLC. Seu objetivo é gerar um Design System completo e pronto para implementação, preenchendo o template `Design_System_Master.md` com decisões concretas baseadas na identidade do projeto e stack definido.

### 1. Leia as Entradas
- Leia `docs/design/Design_System_Master.md` — template com todas as seções.
- Leia `docs/architecture/ARCHITECTURE.md` — stack frontend (React/Vue/Next), bundler, CSS strategy.
- Leia `docs/business/specs/visao_estrategica_e_negocio.md` — identidade, propósito, público-alvo.
- Leia `docs/business/specs/perfis_permissoes.md` — níveis de acesso para permission-aware UI.

### 2. Preencha o Design System

#### Filosofia e Princípios
- Derive princípios de design da identidade institucional e do público-alvo.
- Ex: sistema de auditoria → princípios de clareza, rastreabilidade, seriedade.

#### Design Tokens
- **Cores:** Defina paleta de marca, neutra e semântica. Use tons institucionais se houver.
- **Tipografia:** Escolha font family (Google Fonts ou institucional). Defina escala.
- **Espaçamento:** Base 4px ou 8px. Defina tokens.
- **Elevação:** Sombras para cards, dropdowns, modais.
- **Dark Mode:** Tokens completos para tema escuro.

#### Layout e Responsividade
- Breakpoints (mobile, tablet, desktop).
- Estrutura de páginas (sidebar, topbar, conteúdo).
- Modos de densidade (comfortable, compact, dense).
- Padrões mobile (bottom nav, swipe, FAB, bottom sheet).

#### Biblioteca de Componentes
- **Para CADA componente** (Button, Input, Card, Badge, Modal, Dropdown, Tabs, Tooltip, Table, Form):
  - Variantes e tamanhos.
  - Estados obrigatórios (default, hover, focus, active, disabled, loading, error).
  - Props TypeScript (tabela com nome, tipo, obrigatoriedade, padrão, descrição).
  - Regras de uso (ex: apenas 1 Primary Button por viewport).

#### Padrões de Interface
- Tabelas de dados (sticky header, ordenação, paginação, empty/loading/error).
- Formulários (wizard, validação, dirty state, submission).
- Feedback (toasts, alerts, confirmation dialogs).
- Navegação (breadcrumb, tabs, wizard, drawer, atalhos de teclado).
- Permission-Aware UI (ocultar, desabilitar, read-only, 403).
- Dashboards e visualização de dados (KPI cards, gráficos, filtros).

#### Micro-Interações e Animações
- Catálogo de animações com nome, gatilho, duração, easing.
- Transições de página.
- Estados de carregamento (skeleton, spinner, progress bar).
- Feedback tátil (mobile).

#### Matriz de Estados
- Estados universais para todos componentes.
- Estados específicos por tipo de componente.

### 3. Adapte ao Stack
- Se Tailwind: tokens como variáveis CSS + `tailwind.config.ts`.
- Se Styled Components: tokens como `ThemeProvider`.
- Se CSS Modules: tokens como arquivo `tokens.css`.

### 4. Salve
- Salve o documento preenchido em: `docs/design/DESIGN_SYSTEM.md`.

---

## ⚠️ REGRAS CRÍTICAS

1. **Concreto, não genérico:** Substitua todos os placeholders `[ex: ...]` por decisões reais baseadas no projeto.
2. **Acessibilidade obrigatória:** Contraste, foco visível, touch targets, aria labels — tudo preenchido.
3. **Consistente com Arquitetura:** O Design System deve ser implementável com o stack definido no Step 5.
4. **Cores com propósito:** Cada cor semântica deve ter justificativa de uso. Nada de "cor bonita".
5. **Idempotência:** Verifique existência do arquivo de saída antes de sobrescrever.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após gerar o documento, **PARE** e apresente:

1. **Paleta:** Cores primárias e semânticas definidas com hex.
2. **Tipografia:** Font family e escala.
3. **Componentes:** Lista dos componentes documentados com contagem de variantes.
4. **Padrões:** Padrões de interface especificados.
5. **Cobertura de Estados:** Todos os componentes têm loading, empty, error definidos?
6. **Permissões:** Estratégia de permission-aware UI definida?
7. **Próximos Passos:** Perguntas para validação humana (foco em identidade visual e usabilidade).

**NÃO prossiga para o próximo passo. Aguarde validação humana.**
