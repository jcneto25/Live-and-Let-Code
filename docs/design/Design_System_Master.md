# 🎨 [NOME DO SISTEMA] Design System
**Versão:** 1.0.0  
**Status:** Fundação | Em Expansão | Estável  
**Manutenção:** [Nome do Squad/Design Ops]  
**Link do Figma:** [URL] | **Link do Storybook/Code:** [URL]  

---

## 1. Filosofia e Princípios
> *O "porquê" do nosso design. Como tomamos decisões.*
- **Princípio 1 (ex: Clareza sobre Decoração):** A interface não deve competir com os dados.
- **Princípio 2 (ex: Acessibilidade Inegociável):** O sistema deve ser utilizável por qualquer pessoa, em qualquer dispositivo.
- **Tom de Voz:** [ex: Profissional, empático, direto, clínico].

---

## 2. Fundamentos (Design Tokens)
> *A base atômica. Mapeamento 1:1 entre Figma Variables e CSS/Tailwind.*

### 2.1. Paleta de Cores
| Categoria | Token / Nome | Hex / Valor | Uso Permitido |
| :--- | :--- | :--- | :--- |
| **Brand** | `primary` | `#13eca4` | CTAs principais, links, foco. |
| **Brand** | `primary-dark` | `#0eb57d` | Hover/Active de elementos primários. |
| **Neutral** | `surface` | `#ffffff` | Fundos de cards, modais e inputs. |
| **Neutral** | `background` | `#f6f8f7` | Fundo geral da aplicação (canvas). |
| **Neutral** | `text-main` | `#111816` | Textos principais, títulos. |
| **Neutral** | `text-sec` | `#61897c` | Textos secundários, labels, metadados. |
| **Neutral** | `border` | `#d4dcd8` | Bordas de inputs, cards, tabelas. |
| **Neutral** | `divider` | `#e8edea` | Divisores sutis entre seções. |
| **Semantic** | `success` / `success-bg`| `#22c55e` / `#dcfce7` | Sucesso, aprovação, status ativo. |
| **Semantic** | `critical` / `critical-bg`| `#ef4444` / `#fee2e2` | Erros, perigos, alertas críticos. |
| **Semantic** | `warning` / `warning-bg` | `#eab308` / `#fef9c3` | Atenção, pendências, prazos. |
| **Semantic** | `info` / `info-bg` | `#3b82f6` / `#dbeafe` | Informações, dicas, ajuda contextual. |

*Regra de Ouro:* Nunca usar a cor `primary` como cor de texto sobre fundo branco (falha no contraste). Use sempre `text-main`.

### 2.5. Tema Escuro (Dark Mode)
> *O sistema DEVE suportar tema escuro. Todos os tokens abaixo aplicam-se quando `data-theme="dark"` está ativo.*

| Categoria | Token / Nome | Hex / Valor | Substitui (Light) |
| :--- | :--- | :--- | :--- |
| **Neutral** | `surface` | `#1a1f1d` | `#ffffff` |
| **Neutral** | `background` | `#0f1412` | `#f6f8f7` |
| **Neutral** | `text-main` | `#e8edea` | `#111816` |
| **Neutral** | `text-sec` | `#8aa398` | `#61897c` |
| **Neutral** | `border` | `#2d3531` | `#d4dcd8` |
| **Neutral** | `divider` | `#232927` | `#e8edea` |

**Regras de Tema Escuro:**
- Cores semânticas (`success`, `critical`, `warning`, `info`) **não mudam de matiz** — apenas ajustam saturação (-10%) e luminosidade (+5%) para conforto visual em fundo escuro.
- Cores de marca (`primary`, `primary-dark`) permanecem idênticas.
- A transição entre temas deve ser animada com `transition: background-color 0.3s ease, color 0.3s ease`.
- O tema padrão do sistema respeita `prefers-color-scheme` do SO, com toggle manual que sobrescreve.

### 2.2. Tipografia
**Família Principal:** [ex: Manrope, Inter, Roboto]
| Token | Tamanho (px/rem) | Peso | Line-Height | Uso |
| :--- | :--- | :--- | :--- | :--- |
| `display-lg` | 36px / 2.25rem | 800 | 1.2 | Títulos de Hero/Dashboard. |
| `heading-md` | 24px / 1.5rem | 700 | 1.25 | Títulos de Seção. |
| `body-md` | 16px / 1rem | 400 | 1.5 | Corpo de texto padrão, parágrafos. |
| `label-sm` | 14px / 0.875rem | 500 | 1.2 | Labels de formulário, badges. |
| `caption` | 12px / 0.75rem | 400 | 1.5 | Metadados, timestamps, ajuda. |

### 2.3. Espaçamento e Grid
Baseado em múltiplos de 4px ou 8px.
| Token | Valor | Uso Comum |
| :--- | :--- | :--- |
| `space-xs` | 4px | Espaçamento interno de ícones, badges. |
| `space-sm` | 8px | Gap entre elementos relacionados (ex: label e input). |
| `space-md` | 16px | Padding de botões, gap entre cards. |
| `space-lg` | 24px | Padding interno de Cards e Modais. |
| `space-xl` | 32px | Margens entre grandes seções da página. |

### 2.4. Elevação (Sombras) e Bordas
| Nível | Token | Sombra / Raio | Uso |
| :--- | :--- | :--- | :--- |
| **Level 0** | `radius-md` | `border: 1px solid` | Inputs, tabelas (plano). |
| **Level 1** | `shadow-sm` + `radius-lg` | `0 1px 3px rgba(0,0,0,0.1)` | Cards em repouso. |
| **Level 2** | `shadow-md` | `0 4px 6px rgba(0,0,0,0.1)` | Dropdowns, Popovers. |
| **Level 3** | `shadow-lg` | `0 10px 15px rgba(0,0,0,0.1)` | Modais, Dialogs. |

---

## 3. Layout e Responsividade
### 3.1. Breakpoints
| Nome | Largura | Colunas (Grid) | Padding da Página |
| :--- | :--- | :--- | :--- |
| `mobile` | < 640px | 4 | 16px |
| `tablet` | 640px - 1024px | 8 | 24px |
| `desktop` | > 1024px | 12 | 32px (Max-width: 1440px centralizado) |

### 3.2. Estrutura de Páginas
- **Sidebar:** Fixa (240px colapsada / 280px expandida). Recolhe para overlay (drawer) em `mobile`.
- **Topbar:** Altura fixa de 64px. Contém: breadcrumb, busca global, avatar/usuario, toggle de tema escuro.
- **Área de Conteúdo:** Scrollável independentemente da Topbar. Padding definido por breakpoint.

### 3.3. Modos de Densidade de Conteúdo
> *Para atender usuários casuais e usuários avançados (power users).*

| Modo | Padding de Célula | Altura de Linha (Tabela) | Gap entre Cards | Uso |
| :--- | :--- | :--- | :--- | :--- |
| **Comfortable** (padrão) | `space-md` (16px) | 56px | `space-lg` (24px) | Telas de consulta, dashboards. |
| **Compact** | `space-sm` (8px) | 40px | `space-md` (16px) | Telas operacionais, processamento em lote. |
| **Dense** | 4px | 32px | `space-sm` (8px) | Data grids, auditoria, exportação. |

- **Ativação:** Toggle "Compact Mode" no footer do sidebar ou atalho `Ctrl+Shift+D`.
- **Persistência:** Preferência salva em `localStorage` por usuário.
- **Responsividade:** Em `mobile`, forçar `Comfortable` independente da preferência.

### 3.4. Padrões Mobile-Specific
> *Comportamentos exclusivos de viewport < 640px.*

| Padrão | Comportamento | Observações |
| :--- | :--- | :--- |
| **Navegação inferior (Bottom Nav)** | Barra fixa com 3-5 ícones + labels curtos. Surge quando Sidebar desaparece. | Altura: 56px. Substitui sidebar, NÃO tabs. |
| **Ações swipe** | Swipe left = ação secundária (editar). Swipe right = ação primária (concluir/aprovar). | Aplicável em listas e cards. Fundo colorido revelado no swipe. |
| **Pull to refresh** | Gesto de arrastar para baixo recarrega dados da tela atual. | Indicador visual de refresh no topo. |
| **Sheet inferior (Bottom Sheet)** | Substituto de Modais em mobile. Surge da borda inferior, altura máxima 75vh. | Para ações rápidas: filtros, sorting, criação rápida. |
| **Toque longo (Long Press)** | Abre menu contextual (Context Menu) com ações secundárias. | 500ms de hold. Alternativa a botões de ação inline. |
| **Inputs full-width** | Em mobile, inputs ocupam 100% da largura. Labels acima do campo (não ao lado). | Placeholder visível mesmo com label. |
| **FAB (Floating Action Button)** | Botão circular no canto inferior direito para ação principal da tela. | 56x56px. Elevação `shadow-lg`. Esconde ao scroll para baixo. |

---

## 4. Biblioteca de Componentes
> *Definição de variantes, estados e propriedades (Props). Cada componente DEVE expor uma interface TypeScript documentada.*

### 4.0. Especificação de Props (Formato Obrigatório)
> *Todo componente da biblioteca DEVE ser documentado com a tabela de props abaixo.*

| Prop | Tipo | Obrigatório | Padrão | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| `variant` | `"primary" \| "secondary" \| "ghost" \| "danger"` | Não | `"primary"` | Estilo visual do componente. |
| `size` | `"sm" \| "md" \| "lg"` | Não | `"md"` | Dimensão do componente. |
| `isDisabled` | `boolean` | Não | `false` | Desabilita interação e aplica estilo `Disabled`. |
| `isLoading` | `boolean` | Não | `false` | Exibe indicador de carregamento e desabilita interação. |
| `leftIcon` | `IconName` | Não | — | Ícone à esquerda do conteúdo. |
| `rightIcon` | `IconName` | Não | — | Ícone à direita do conteúdo. |
| `onClick` | `() => void` | Sim (se interativo) | — | Callback de clique. |
| `ariaLabel` | `string` | Sim (se sem texto) | — | Label para leitores de tela. |
| `dataTestId` | `string` | Sim | — | Identificador para testes automatizados. |

### 4.1. Botões (Button)
**Variantes:** `Primary`, `Secondary`, `Ghost`, `Danger`.
**Tamanhos:** `sm` (32px), `md` (40px), `lg` (48px).
**Estados Obrigatórios:** `Default`, `Hover`, `Active/Pressed`, `Focus` (ring), `Disabled`, `Loading`.
- **Regra:** Apenas **UM** botão `Primary` por viewport/seção principal.
- **Loading:** Substitui `leftIcon` por spinner. Mantém largura original para evitar layout shift.
- **Danger:** Requer confirmação se ação for destrutiva. Exibir `confirmDialog` antes de executar `onClick`.

### 4.2. Campos de Formulário (Input)
**Elementos:** Label (obrigatório), Input, Helper Text, Error Message.
**Estados:** `Empty`, `Filled`, `Focused`, `Error`, `Disabled`, `Read-only`, `Loading` (async validation).
**Variantes:** `Text`, `Number`, `Password`, `Email`, `Textarea`, `Select`, `MultiSelect`, `DatePicker`, `FileUpload`.
- **Regra:** O foco deve ser sempre visível (`ring-2 ring-primary`). Mensagens de erro devem aparecer *abaixo* do campo, em `text-critical`.
- **Helper Text:** Máximo 60 caracteres. Explica o formato esperado ou fornece exemplo.
- **Character Count:** Exibir para campos com limite (ex: "42/200"). Mostrar apenas quando restam < 20% do limite.

### 4.3. Cards
**Variantes:** `Interactive` (clicável, com hover), `Static` (apenas exibição), `Bordered`.
**Estados:** `Default`, `Hover` (interactive only), `Selected`, `Disabled`, `Loading` (skeleton).
- **Regra:** Cards interativos devem ter cursor pointer e elevar a sombra no hover.
- **Selected:** Borda `primary`, background sutil `primary` a 5% de opacidade, checkmark no canto superior direito.
- **Skeleton:** Placeholder animado com `background: linear-gradient(90deg, border 25%, divider 50%, border 75%)` e `background-size: 200% 100%` com animação de shimmer.

### 4.4. Badges / Status
**Variantes:** `Success`, `Warning`, `Critical`, `Info`, `Neutral`.
**Tamanhos:** `sm` (20px), `md` (24px).
**Formatos:** `Pill` (arredondado), `Dot` (círculo + texto), `Counter` (número).
- **Regra:** Sempre usar o par semântico (ex: Fundo `success-bg` com Texto `success`). Nunca usar apenas a cor sólida para texto pequeno.
- **Counter:** Exibe número dentro do badge. Máximo exibido: "99+".

### 4.5. Modal / Dialog
**Variantes:** `Default` (centrado), `Sheet` (lateral direita 480px), `FullScreen` (mobile).
**Tamanhos:** `sm` (400px), `md` (560px), `lg` (720px), `xl` (960px).
**Estados:** `Open`, `Closing` (animação de saída).
**Estrutura Obrigatória:**
1. **Overlay:** `background: rgba(0,0,0,0.5)`, `backdrop-filter: blur(2px)`. Fecha ao clicar (exceto se `isPersistent`).
2. **Header:** Título + descrição opcional + botão de fechar (X).
3. **Body:** Conteúdo scrollável se exceder 70vh.
4. **Footer:** Ações (Cancelar | Confirmar). Confirmar é sempre `Primary`.
- **Regra:** Foco capturado dentro do modal (trap focus). `Escape` fecha. Animação: fade in (200ms) + scale (0.95 → 1).

### 4.6. Dropdown / Popover
**Estados:** `Closed`, `Open`, `Opening` (transição).
**Posicionamento:** Automático (bottom / top / left / right) baseado em espaço disponível. Usar `floating-ui` ou equivalente.
**Conteúdo:** Lista de ações, formulário rápido, ou conteúdo informativo.
- **Regra:** Fechar ao clicar fora, pressionar `Escape`, ou selecionar item (se menu).
- **Submenus:** Expandir no hover (200ms delay) ou clique. Posicionar à direita do item pai.

### 4.7. Tabs
**Variantes:** `Underline` (padrão), `Pills`, `Segmented` (iOS-style).
**Estados por Tab:** `Default`, `Hover`, `Active`, `Disabled`.
**Scroll:** Se tabs excederem a largura, habilitar scroll horizontal com botões de navegação (chevron left/right).
- **Regra:** Tab ativa DEVE ser distinguível por cor (`primary`) e indicador visual (underline de 2px ou fundo preenchido).
- **Conteúdo:** Renderizar apenas o painel ativo. Animar transição com fade (150ms).

### 4.8. Tooltip
**Gatilhos:** `Hover` (desktop), `Long Press` (mobile).
**Delay:** 300ms para aparecer, 0ms para desaparecer.
**Posicionamento:** Top por padrão. Auto-ajuste para evitar corte.
- **Conteúdo:** Máximo 150 caracteres. Texto curto e informativo.
- **Acessibilidade:** Conteúdo também disponível via `aria-describedby`.

---

## 5. Padrões de Interface (Patterns)
> *Como combinamos componentes para resolver fluxos complexos.*

### 5.1. Tabelas de Dados (Data Tables)
- **Cabeçalho:** Fixo no topo ao rolar a tabela (sticky header).
- **Linhas:** Altura conforme modo de densidade. Alternar cores de fundo a cada 2 linhas para legibilidade (zebra striping).
- **Ordenação:** Clique no cabeçalho alterna ASC → DESC → nenhum. Ícone de seta indica direção ativa.
- **Seleção:** Checkbox na primeira coluna para seleção múltipla. Header checkbox = selecionar/desselecionar todos.
- **Paginação:** Inferior direita. Mostrar: "1-20 de 342" + controles (Anterior, 1, 2, 3, ..., 18, Próximo). Opção de itens por página: 20, 50, 100.
- **Ações:** Botões de ação por linha devem usar `Ghost` ou ícones para não poluir visualmente.
- **Colunas redimensionáveis:** Permitir drag na borda direita do header para redimensionar.
- **Empty State:** Se não houver dados, exibir ilustração + texto + CTA (ex: "Nenhum registro encontrado. [Criar Novo]").
- **Loading State:** Skeleton rows (5-10 linhas fantasma) enquanto dados carregam.
- **Error State:** Mensagem inline no corpo da tabela: "Erro ao carregar dados. [Tentar novamente]".
- **Exportação:** Botão "Exportar" acima da tabela (CSV, PDF, Excel). Respeita filtros ativos.

### 5.2. Formulários Longos
- Dividir em "Cards" ou "Steps" (Assistente/Wizard).
- Salvar rascunho automático a cada 30s (se aplicável). Indicador: "Rascunho salvo às 14:32".
- Agrupar campos relacionados visualmente (Fieldset com legenda).
- **Dirty State:** Alertar ao tentar sair com alterações não salvas: "Você possui alterações não salvas. Deseja sair?"
- **Progresso:** Em wizards, mostrar steps (1 de 5) com indicador visual de progresso.

### 5.3. Feedback do Sistema (Toasts / Alerts)
- **Toast (Canto superior direito):** Para feedback efêmero (ex: "Salvo com sucesso"). Desaparece em 5s. Máximo de 3 toasts simultâneos.
  - Variantes: `Success`, `Error`, `Warning`, `Info`.
  - Ação opcional: "Desfazer" (ex: após exclusão).
- **Inline Alert (Topo da página/seção):** Para avisos persistentes (ex: "Sua sessão expira em 5 min").
  - Persiste até ação do usuário ou condição resolvida.
  - Pode conter CTA (ex: "Renovar sessão").
- **Confirmation Dialog:** Para ações destrutivas. Título + descrição + Cancelar | Confirmar (Danger).

### 5.4. Padrões de Navegação
> *Como o usuário se move entre páginas, seções e fluxos.*

| Padrão | Uso | Comportamento |
| :--- | :--- | :--- |
| **Breadcrumb** | Navegação hierárquica (Home > Módulo > Detalhe) | Sempre visível abaixo da Topbar. Último item = página atual (não clicável). |
| **Tabs de Página** | Sub-seções dentro de uma página (ex: Detalhe | Histórico | Anexos) | Abaixo do título da página. Mantém estado ao trocar de aba. |
| **Wizard (Assistente)** | Fluxos multi-etapas (ex: Cadastro, Configuração inicial) | Passos numerados no topo. Botões: Voltar | Próximo/Avançar. Barra de progresso. |
| **Drawer Lateral** | Painel de detalhes ou formulário rápido que não substitui a página atual | Abre da direita (480px). Overlay semi-transparente. Fecha no X ou Escape. |
| **Voltar (Back)** | Retorno à página anterior | Botão na Topbar ou gesto de swipe (mobile). Preserva estado da página anterior (scroll, filtros). |
| **Atalhos de Teclado** | Navegação rápida para power users | `Ctrl+K` = busca global. `Ctrl+Shift+D` = toggle densidade. `Esc` = fechar modal/drawer. Exibir atalhos em tooltip. |

### 5.5. Padrões de Validação de Formulários
> *Comportamento consistente de validação em todos os formulários do sistema.*

| Momento | Comportamento | Exemplo |
| :--- | :--- | :--- |
| **On Blur** (padrão) | Valida ao sair do campo. Mensagem de erro abaixo do input. | Usuário digita email inválido → ao sair do campo, aparece "Formato de email inválido". |
| **On Submit** | Valida todos os campos ao submeter. Foca no primeiro campo com erro. Scroll até ele. | Ao clicar "Salvar", campos obrigatórios vazios mostram erro simultaneamente. |
| **Async (Server-side)** | Validações que dependem do servidor (ex: email já cadastrado). Exibir spinner no input durante validação. | Input loading → "Verificando disponibilidade..." → "Email já cadastrado". |
| **Real-time** (opcional) | Valida enquanto digita, mas apenas após o primeiro blur. Aplicar debounce de 500ms. | Campo de senha: após primeiro blur, valida força da senha a cada alteração. |
| **Submission State** | Durante envio: desabilitar botão, mostrar spinner, texto muda para "Salvando...". | Após sucesso: toast "Salvo com sucesso". Após erro: inline alert com mensagem do servidor. |

### 5.6. UI Consciente de Permissões (Permission-Aware UI)
> *Elementos da interface devem reagir ao perfil e permissões do usuário. Baseado na matriz de Perfis e Permissões do projeto.*

| Nível | Comportamento | Exemplo |
| :--- | :--- | :--- |
| **Ocultar** | Elemento não renderiza se usuário não tem permissão. | Botão "Excluir" não aparece para perfil sem permissão de exclusão. |
| **Desabilitar** | Elemento visível mas não interativo. Tooltip explica o motivo. | Botão "Aprovar" cinza com tooltip: "Apenas o Gestor da Unidade pode aprovar". |
| **Read-only** | Campos exibidos como texto não editável (não como input disabled). | Usuário visualiza dados de outra unidade: todos os campos em modo leitura. |
| **Filtro Automático** | Dados exibidos são filtrados por escopo do usuário. | Lista de registros mostra apenas os da unidade do usuário (exceto perfis com escopo Global). |
| **Mensagem de Acesso Restrito** | Se usuário tentar acessar rota não autorizada, exibir página 403 com: "Você não possui permissão para acessar esta área." | Acesso negado + link para "Voltar ao início". |

### 5.7. Visualização de Dados (Dashboards & BI)
> *Padrões para gráficos, KPIs e painéis analíticos.*

| Elemento | Especificação | Observações |
| :--- | :--- | :--- |
| **KPI Card** | Valor numérico grande (display-lg) + label + variação % (verde/vermelho) | Exibir tendência: seta para cima (positivo) ou para baixo (negativo). |
| **Gráfico de Linhas** | Eixo X: tempo. Eixo Y: valor. Máximo 5 séries. | Linhas com 2px de espessura. Pontos de dados apenas no hover. |
| **Gráfico de Barras** | Barras com 8px de border-radius e 16px de gap. | Cores: usar paleta com no máximo 6 cores distintas e acessíveis. |
| **Gráfico de Pizza/Rosca** | Máximo 6 fatias. Ordenar por valor decrescente. | Exibir % dentro ou ao lado da fatia. Agrupar fatias pequenas em "Outros". |
| **Tabela de Dados Analítica** | Linhas ordenáveis, heatmap opcional (cor de fundo baseada em valor) | Suportar exportação e drill-down (clique na linha → detalhamento). |
| **Filtros de Dashboard** | Barra superior com: período (date range picker), filtros dropdown, botão "Aplicar". | Filtros persistidos na URL para compartilhamento. |
| **Cores para Gráficos** | Usar paleta semântica + cores neutras. Evitar vermelho/verde como única diferenciação (daltonismo). | Usar padrões ou ícones como reforço visual. |
| **Estado Vazio** | Ilustração + "Nenhum dado disponível para o período selecionado." | Sugerir ajuste de filtros. |
| **Carregamento** | Skeleton específico: placeholder do gráfico com shimmer. | Não usar spinner genérico — manter layout estável. |
| **Responsividade** | Em mobile: gráficos empilham verticalmente. Simplificar (ex: pizza → barra horizontal, linha → sparkline). | KPI cards reduzem para 2 colunas. |

---

## 6. Acessibilidade (a11y) - OBRIGATÓRIO
- [ ] **Contraste:** Todo texto normal deve ter ratio de 4.5:1. Texto grande 3:1.
- [ ] **Alvos de Toque:** Botões e links devem ter no mínimo 44x44px (recomendado 48px).
- [ ] **Foco Visível:** Navegação via `TAB` deve exibir um anel de foco (`focus-visible`) de no mínimo 2px em torno do elemento.
- [ ] **Ícones:** Ícones que representam ações (ex: lixeira) devem ter `aria-label` ou `title` para leitores de tela. Ícones puramente decorativos devem ter `aria-hidden="true"`.

---

## 7. Iconografia
**Biblioteca Base:** [ex: Material Symbols, Phosphor Icons, Lucide]
**Estilo:** [ex: Outlined, Rounded, Weight 400]
**Tamanhos Padrão:**
- `xs`: 16px (Dentro de badges, textos)
- `sm`: 20px (Dentro de botões, inputs)
- `md`: 24px (Navegação, ações padrão)
- `lg`: 32px (Empty states, destaques)

---

## 8. Micro-Interações e Animações
> *Movimento com propósito. Toda animação DEVE ter duração, easing e gatilho documentados.*

### 8.1. Princípios de Animação
- **Duração máxima:** 300ms para transições de UI. 500ms para transições de página.
- **Easing padrão:** `cubic-bezier(0.4, 0, 0.2, 1)` (Material Design standard).
- **Easing de entrada:** `cubic-bezier(0, 0, 0.2, 1)` (acceleration).
- **Easing de saída:** `cubic-bezier(0.4, 0, 1, 1)` (deceleration).
- **Redução de movimento:** Respeitar `prefers-reduced-motion`. Se ativo, todas as animações devem ser instantâneas (0ms) ou reduzidas a opacidade.

### 8.2. Catálogo de Animações

| Nome | Gatilho | Duração | Easing | Descrição |
| :--- | :--- | :--- | :--- | :--- |
| `fade-in` | Elemento entra no DOM | 200ms | standard | `opacity: 0 → 1` |
| `fade-out` | Elemento sai do DOM | 150ms | standard | `opacity: 1 → 0` |
| `scale-in` | Modal/Dialog abre | 200ms | standard | `opacity: 0 → 1` + `scale: 0.95 → 1` |
| `scale-out` | Modal/Dialog fecha | 150ms | standard | `opacity: 1 → 0` + `scale: 1 → 0.95` |
| `slide-up` | Sheet/Drawer abre | 250ms | deceleration | `transform: translateY(100%) → 0` |
| `slide-down` | Sheet/Drawer fecha | 200ms | acceleration | `transform: translateY(0) → 100%` |
| `slide-left` | Navegação para próxima página | 300ms | standard | `transform: translateX(30px) → 0` + fade |
| `expand` | Accordion/Dropdown abre | 200ms | standard | `max-height: 0 → auto` + `opacity: 0 → 1` |
| `collapse` | Accordion/Dropdown fecha | 150ms | standard | `max-height: auto → 0` + `opacity: 1 → 0` |
| `pulse` | Indicador de atenção (ex: nova notificação) | 2s loop | ease-in-out | `scale: 1 → 1.05 → 1` (3 repetições) |
| `spin` | Indicador de carregamento circular | loop | linear | `rotate: 0 → 360deg` (duração: 750ms por volta) |
| `shimmer` | Skeleton loader | 1.5s loop | ease-in-out | `background-position: -200% → 200%` |
| `shake` | Erro de validação em input | 400ms | ease-in-out | `translateX: 0 → -4px → 4px → -2px → 2px → 0` |

### 8.3. Transições de Página / Rota
| Transição | Descrição | Uso |
| :--- | :--- | :--- |
| **Push** | Página atual desliza para esquerda, nova página entra da direita | Navegação para frente (ex: Lista → Detalhe) |
| **Pop** | Inverso de Push (direita → esquerda) | Navegação para trás (ex: Detalhe → Lista) |
| **Replace** | Fade out → Fade in sem deslocamento | Troca de aba, filtro aplicado |
| **Modal** | Scale + fade (não desloca página anterior) | Modal, Dialog, Drawer |

### 8.4. Feedback Tátil (Haptic)
> *Aplicável em dispositivos mobile com suporte a vibração.*

| Interação | Tipo de Feedback | Intensidade |
| :--- | :--- | :--- |
| Botão Primary pressionado | `light` | Suave |
| Ação destrutiva confirmada | `heavy` | Forte |
| Swipe action ativada | `medium` | Média |
| Pull to refresh atinge threshold | `light` | Suave |
| Erro de validação | `warning` (padrão duplo) | Média |

### 8.5. Estados de Carregamento (Loading States)
> *Regra: NUNCA mostrar tela branca durante carregamento. Sempre usar skeleton ou progress indicator.*

| Cenário | Tratamento | Exemplo |
| :--- | :--- | :--- |
| **Carregamento inicial da página** | Skeleton screen: placeholders com shimmer que mapeiam o layout final | Tabela → 10 linhas fantasma + header. Card → retângulo com shimmer. |
| **Ação de botão** | Spinner substitui ícone + texto muda (ex: "Salvar" → "Salvando...") + botão disabled | Texto do botão deve manter mesma largura para evitar layout shift. |
| **Carregamento sob demanda** | Spinner inline no local do conteúdo ou no final da lista (infinite scroll) | "Carregando mais..." no rodapé da lista. |
| **Background refresh** | Indicador sutil no topo da página (barra fina de progresso ou pulse no título) | Atualização silenciosa de dados em tempo real. |
| **Upload de arquivo** | Barra de progresso com % + nome do arquivo + cancelar | Progress bar com `primary`; ao concluir, fade para `success`. |

---

## 9. Matriz de Estados dos Componentes
> *Tabela obrigatória: todo componente DEVE implementar todos os estados aplicáveis listados abaixo.*

### 9.1. Estados Universais (aplicam-se a todos os componentes interativos)

| Estado | Descrição | Gatilho | Tratamento Visual |
| :--- | :--- | :--- | :--- |
| **Default** | Estado de repouso inicial | Componente montado | Estilo base documentado. |
| **Hover** | Cursor sobre o elemento | `:hover` (desktop) | Elevação ou mudança sutil de cor. `cursor: pointer` se interativo. |
| **Focus** | Elemento recebe foco via teclado | `:focus-visible` | `box-shadow: 0 0 0 2px var(--color-primary)` com offset de 2px do elemento. |
| **Active / Pressed** | Elemento sendo pressionado | `:active` | Escurecer 10% ou escala 0.98. Duração: 100ms. |
| **Disabled** | Interação bloqueada | Prop `isDisabled={true}` | Opacidade 40%. `cursor: not-allowed`. Remover todos os handlers. |
| **Loading** | Operação assíncrona em andamento | Prop `isLoading={true}` | Spinner + desabilitar interação. Manter largura para evitar layout shift. |
| **Error** | Estado de erro irrecuperável | Prop `error={message}` | Mensagem de erro + ícone `critical`. Botão "Tentar novamente" quando aplicável. |

### 9.2. Estados Específicos por Tipo de Componente

| Componente | Estados Adicionais | Descrição |
| :--- | :--- | :--- |
| **Tabela / Lista** | `Empty`, `Loading` (skeleton), `Error`, `Filtered Empty` | Filtered Empty: "Nenhum resultado para o filtro aplicado. [Limpar filtros]". |
| **Formulário** | `Pristine`, `Dirty`, `Submitting`, `Submitted (Success)`, `Submitted (Error)` | Dirty: indicador visual (asterisco ou barra lateral) nos campos alterados. |
| **Card Interativo** | `Selected`, `Highlighted` (novo registro) | Selected: borda primary + checkmark. Highlighted: animação pulse por 3s. |
| **Modal** | `Open`, `Closing` | Closing: animação de saída antes de remover do DOM (150ms). |
| **Toast** | `Entering`, `Visible`, `Exiting` | Entering: slide da direita + fade. Exiting: fade out. |
| **Upload** | `Idle`, `Uploading`, `Processing`, `Complete`, `Error` | Cada arquivo mostra seu estado individual. |

---

## 10. Governança e Contribuição
### 10.1. Como solicitar um novo componente?
1. Verificar se o componente já existe no Storybook/Figma.
2. Abrir uma Issue no repositório `[Link]` com o template "Novo Componente".
3. Anexar caso de uso, exemplos de uso e rascunho.

### 10.2. Versionamento
- O Design System segue o padrão **Semantic Versioning (SemVer)**.
- **Major (1.0.0):** Quebra de compatibilidade (ex: mudança na cor primária, remoção de um componente).
- **Minor (1.1.0):** Adição de novos componentes ou tokens (retrocompatível).
- **Patch (1.0.1):** Correção de bugs visuais ou de documentação.