---
name: llc-step-7a-ux-heuristics
description: "Pipeline LLC Step 7a — UX Heuristics & Personas. Estabelece 10 hard gates de usabilidade e empatia que o agente carrega antes de gerar qualquer interface. Complementa Step 7 (Design System — tokens, componentes, padrões estruturais) com a dimensão humana: personas, heurísticas de Nielsen, anti-padrões éticos e padrões de implementação conscientes do usuário."
version: 1.0.0
tags: [ux, usability, heuristics, nielsen, personas, accessibility, design-patterns, anti-patterns, i18n, forms, llc-pipeline]
---

# LLC Skill: Step 7a — UX Heuristics & Personas

**Pipeline:** Live and Let Code (LLC)
**Fase:** UI/UX Foundation (sub-step of Step 7 — Design System)
**Depende de:** Step 7 (Design System validado)
**Executa antes de:** Step 8 (Setup + Mock), Step 11 (Execução dos PRPs)
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-7a-ux-heuristics` ou "Execute a skill llc-step-7a-ux-heuristics".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 7a --task "Enforcar UX Heuristics"`.

---

## 📋 Pré-requisitos

- [ ] `docs/design/DESIGN_SYSTEM.md` — tokens, componentes e padrões visuais (Step 7)
- [ ] `docs/business/specs/visao_estrategica_e_negocio.md` — identidade, propósito, público-alvo (Step 0.5)
- [ ] `docs/business/specs/perfis_permissoes.md` — perfis de usuário e níveis de acesso (Step 1)
- [ ] `docs/architecture/ARCHITECTURE.md` — stack frontend, frameworks (Step 5)

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.2 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 7a** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-7a.md`:
     ```markdown
     # Skip Note: Step 7a — UX Heuristics & Personas
     **Decisão:** Step pulado — personas, heurísticas e anti-padrões inalterados desde última execução.
     **Evidência:** `fitness-functions --check-ux` passa sem novas violações.
     **Validador:** [Nome] | **Data:** [YYYY-MM-DD]
     ```
   - **Não execute** as verificações nem aguarde Gate 7a.
   - Avance para Step 8.
3. Se DELTA_REPORT.md não existir: prossiga normalmente.

---

## 🎯 OBJETIVO

Estabelecer disciplina de UX **antes** da geração de interfaces, garantindo que toda tela respeite personas, heurísticas de usabilidade e padrões éticos. Complementa o Step 7 (Design System) que cobre a dimensão estrutural (tokens, componentes, padrões visuais) — esta skill cobre a dimensão humana (empatia, usabilidade, ética).

**Princípio fundamental:** O LLM gera UI funcional. Esta skill garante que gere UI *utilizável, inclusiva e ética*.

Esta skill atua em 5 frentes:

| Frente | Descrição | Referência |
|--------|-----------|------------|
| **Hard Gates** | 10 regras intransponíveis que o agente NUNCA deve violar | NN/g, WCAG 2.2 |
| **Persona Validation** | Checklist de validação por persona antes de cada tela | Cooper (1999), Goodwin (2009) |
| **Nielsen Heuristics** | 10 heurísticas com checklist por tela | Nielsen (1994, 2020) |
| **Anti-padrões** | 5 anti-padrões éticos/de usabilidade documentados com exemplos ❌/✅ | Brignull (2010), NN/g |
| **Padrões de Implementação** | 4 patterns reutilizáveis (useForm, FormField, showErrorAlert, i18n) | React/React Native best practices |

---

## 🛑 1. Hard Gates (Regras Intransponíveis)

*O agente NUNCA deve:*

1. **NUNCA** criar telas sem validar contra as personas do projeto.
   - Toda tela deve responder: *Quem* usa esta tela? *Qual* a necessidade? *Qual* o estado emocional esperado? *O que* esta persona NÃO precisa ver?
   - Se o projeto não tem personas definidas, este gate **bloqueia** até que personas sejam criadas (ver §2 — Persona Validation).
   - Exceção: telas puramente técnicas (admin panels, debug screens) — documentar isenção.

2. **NUNCA** implementar `Alert.alert()` / `alert()` / diálogo de erro sem ação de recuperação concreta.
   - Todo erro deve responder: *O que o usuário deve fazer agora?*
   - Não basta dizer "Algo deu errado" — informe a ação: "Tentar novamente", "Verificar conexão", "Falar com suporte".
   - Botão "OK" sozinho em diálogo de erro é **inaceitável** — sempre inclua ação de recuperação.

3. **NUNCA** criar formulários sem `useForm()` ou `FormField` padronizado.
   - Todo campo deve ter: label visível, hint text, validação inline, estado de erro com mensagem, estado de sucesso.
   - Formulários inline (ex: search bar, quick edit) são exceção documentada.
   - Placeholder **não** é label — placeholder desaparece quando o usuário digita (WCAG 3.3.2).

4. **NUNCA** implementar paywalls, cancelamentos ou downgrades como **Roach Motel** (fácil de entrar, difícil de sair).
   - Cancelar conta/premium deve ser **tão fácil quanto** assinar.
   - Número de passos para cancelar ≤ número de passos para assinar.
   - Não esconder botão de cancelamento, não exigir telefonema, não usar linguagem manipulativa.

5. **NUNCA** criar onboarding, diálogos de permissão ou popups com **Confirmshaming** (envergonhar o usuário por recusar).
   - Opção de recusa deve ser neutra ou positiva, nunca depreciativa.
   - ❌ "Não, prefiro continuar vulnerável" / ✅ "Não, obrigado"
   - ❌ "Não quero economizar dinheiro" / ✅ "Pular esta oferta"

6. **NUNCA** implementar sistemas autônomos (IA, automação, recomendações) sem controle explícito do usuário.
   - Usuário deve poder: desligar, ajustar intensidade, ver histórico de decisões, contestar resultado.
   - Toda decisão automática deve ser **explicável** em linguagem natural (não técnica).
   - Automações irreversíveis (ex: deletar dados, enviar para terceiros) exigem confirmação explícita.

7. **NUNCA** usar strings hardcoded visíveis ao usuário — toda string deve usar `t('key')` (i18n).
   - Strings visíveis: labels, botões, mensagens de erro, toasts, placeholders, títulos, tooltips.
   - Exceção: placeholders de desenvolvimento (substituídos antes do merge) e strings em testes.
   - Chave deve ser semântica: `t('checkout.payment.failed')`, não `t('err_01')`.

8. **NUNCA** criar listas com 20+ itens sem busca, filtro ou paginação.
   - Lista plana > 20 itens: adicionar search bar no topo.
   - Lista > 50 itens: search bar + filtros + paginação/virtualização.
   - Lista categorizável: agrupar por categoria + accordion.
   - Exceção: listas navegacionais hierárquicas (menu tree, breadcrumb path).

9. **NUNCA** criar telas com 15+ campos de formulário sem agrupamento (abas, seções, wizard, Quick Add).
   - 15-25 campos: agrupar em seções colapsáveis com títulos descritivos.
   - 25+ campos: dividir em wizard multi-etapas ou abas.
   - Campos opcionais: colapsar em "Advanced" / "Optional details".
   - Quick Add: fluxo simplificado com apenas campos obrigatórios + botão "Add Details" para o resto.

10. **NUNCA** criar interfaces de IA/voz/chatbot sem estados visíveis explícitos.
    - Estados obrigatórios: ouvindo/processando, falando/respondendo, erro (não entendi), idle, desconectado.
    - Transcrição visível do que foi entendido (antes de agir).
    - Botão de cancelar/interromper visível durante processamento.
    - Feedback de confiança: "Tenho 85% de certeza que você quis dizer X. Confirmar?"

---

## 👤 2. Persona Validation (Obrigatório Antes de Cada Tela)

Antes de implementar qualquer tela, o agente deve executar este raciocínio:

### 2.1 Template de Validação por Persona

```markdown
### 👤 Persona Validation: [Nome da Tela]

**Persona Primária:** [Nome da persona]
- **Quem é?** [1-2 frases — papel, contexto, limitação relevante]
- **O que precisa nesta tela?** [Tarefa principal — verbo + objeto]
- **Estado emocional esperado:** [Ex: apressado, curioso, frustrado, focado]
- **O que NÃO precisa ver?** [Informação/opção que distrai ou confunde]

**Persona Secundária:** [Nome ou "N/A"]
- **Diferença da primária:** [Permissão, necessidade, contexto diferente]

**Decisão de Design:**
- [O que foi removido/escondido com base nas personas?]
- [O que foi priorizado visualmente?]
- [Qual o caminho feliz de 1-2 passos para a tarefa principal?]
```

### 2.2 Exemplo Preenchido

```markdown
### 👤 Persona Validation: Tela de Transferência Bancária

**Persona Primária:** Maria — Correntista, 45 anos, usa app diariamente
- **Quem é?** Professora, familiarizada com tecnologia mas não especialista.
  Usa óculos para leitura (visão reduzida para texto pequeno).
- **O que precisa nesta tela?** Transferir dinheiro para filho na universidade.
  Faz isso toda semana — valor e destino raramente mudam.
- **Estado emocional esperado:** Apressada (quer resolver rápido no intervalo).
  Levemente ansiosa (medo de errar valor/destino).
- **O que NÃO precisa ver?** Opções de investimento, saldo de poupança,
  ofertas de crédito, notícias do mercado financeiro.

**Persona Secundária:** João — Gerente de conta (acesso administrativo)
- **Diferença da primária:** Vê limites diários, aprova transferências acima do
  teto, acessa log de todas as transações do cliente.

**Decisão de Design:**
- Destino rápido: sugestão automática do filho (último destinatário).
- Valor pré-preenchido com o valor da última transferência (editável).
- Botão "Repetir última" como atalho principal (1 toque).
- Confirmação visual clara: foto do destinatário + nome grande + valor em destaque.
- Sem cross-sell: zero ofertas de produtos na tela de transferência.
```

### 2.3 Regras de Persona

- **Mínimo 1 persona primária** por projeto. Ideal: 2-3 personas cobrindo os perfis de acesso.
- Se o projeto não tem personas, a primeira sessão Step 7a deve **criá-las** (2-4 personas baseadas nos perfis de `perfis_permissoes.md`).
- Persona não é demographic fluff — é **padrão de comportamento observável** que afeta decisões de design.
- Formato: `docs/business/personas.md` ou seção no `DESIGN_SYSTEM.md`.

---

## 📐 3. 10 Heurísticas de Nielsen — Checklist por Tela

Checklist baseado nas 10 heurísticas de Jakob Nielsen (1994, atualizado 2020). Validar **cada tela** contra estas 10 dimensões.

| # | Heurística | Pergunta de Validação | ❌ Falha se... |
|---|-----------|----------------------|---------------|
| **1** | **Visibilidade do estado do sistema** | O usuário sabe o que está acontecendo agora? | Sem indicador de loading, sem feedback após ação, sem breadcrumb de navegação |
| **2** | **Correspondência com o mundo real** | A linguagem e ícones são familiares ao usuário? | Usa jargão técnico (ex: "Erro 500"), ícone abstrato para conceito concreto, ordenação não natural |
| **3** | **Controle e liberdade do usuário** | O usuário pode desfazer/voltar facilmente? | Sem botão Voltar, sem Undo, sem Cancelar, modal sem X, wizard sem "Anterior" |
| **4** | **Consistência e padrões** | Comportamentos iguais têm aparência igual? | Botão primário azul em uma tela e verde em outra, "Salvar" às vezes no topo às vezes no fim, datas em formatos diferentes |
| **5** | **Prevenção de erros** | O design impede erros antes que aconteçam? | Sem validação inline, sem confirmação para ações destrutivas, sem disabled state em botão que não deveria ser clicado |
| **6** | **Reconhecimento em vez de memorização** | Opções estão visíveis (não escondidas em menus)? | Ações frequentes em menu hambúrguer, passo-a-passo sem mostrar passos, campo sem autocomplete com valores conhecidos |
| **7** | **Flexibilidade e eficiência de uso** | Usuários frequentes têm atalhos? | Sem atalhos de teclado, sem swipe actions, sem "Repetir última", fluxo de 5 passos para tarefa semanal |
| **8** | **Design estético e minimalista** | Cada elemento é essencial? | Informação raramente usada compete com informação essencial, 3+ CTAs na mesma tela, texto que ninguém lê |
| **9** | **Ajuda no reconhecimento e correção de erros** | Mensagens de erro ajudam a resolver? | "Erro desconhecido", "Algo deu errado", código de erro sem explicação, sem sugestão de próximo passo |
| **10** | **Ajuda e documentação** | Ajuda está disponível quando necessário? | Sem tooltip em campo complexo, sem link para FAQ/ajuda, sem hint text, onboarding único que não pode ser reconsultado |

### 3.1 Template de Checklist por Tela

```markdown
### Nielsen Checklist: [Nome da Tela]

- [ ] #1 Visibilidade — loading, feedback, breadcrumb definidos?
- [ ] #2 Mundo real — linguagem do usuário, não do sistema?
- [ ] #3 Controle — voltar, desfazer, cancelar disponíveis?
- [ ] #4 Consistência — cores, posições, formatos idênticos ao Design System?
- [ ] #5 Prevenção — validação inline, confirmação destrutiva, disabled states?
- [ ] #6 Reconhecimento — ações frequentes visíveis, autocomplete onde aplicável?
- [ ] #7 Eficiência — atalhos para usuários frequentes?
- [ ] #8 Minimalismo — cada elemento na tela tem justificativa?
- [ ] #9 Recuperação — erros explicam o que fazer?
- [ ] #10 Ajuda — tooltips, hints, link para ajuda disponíveis?

**Violações:** [Listar #N e ação corretiva]
**Aprovado para implementação:** [Sim/Não — se Não, corrigir violações primeiro]
```

---

## ❌ 4. Anti-Padrões de UX

### 4.1 Confirmshaming

**Sintoma:** Diálogo que envergonha o usuário por recusar uma opção.

```tsx
// ❌ Confirmshaming — envergonha por recusar
<Modal visible={showOffer}>
  <Text>Assine Premium por apenas R$ 9,90/mês!</Text>
  <Button title="Sim, quero economizar!" onPress={subscribe} />
  <Button title="Não, prefiro pagar mais caro" onPress={close} />
</Modal>

// ❌ Confirmshaming — deprecia a escolha do usuário
<Dialog>
  <Text>Ativar notificações?</Text>
  <Button title="SIM! Quero ficar por dentro" />
  <Button title="Não, não me importo com novidades" />
</Dialog>
```

```tsx
// ✅ Neutro — respeita a escolha do usuário
<Modal visible={showOffer}>
  <Text>Assine Premium por R$ 9,90/mês</Text>
  <Text>Inclui: relatórios avançados, exportação, suporte prioritário</Text>
  <Button title="Assinar Premium" onPress={subscribe} variant="primary" />
  <Button title="Agora não" onPress={close} variant="ghost" />
</Modal>

// ✅ Neutro — informa sem julgar
<Dialog>
  <Text>Ativar notificações?</Text>
  <Text>Você receberá alertas de segurança e atualizações importantes.</Text>
  <Button title="Ativar" />
  <Button title="Agora não" />
</Dialog>
```

**Regra:** O texto do botão de recusa deve descrever a **ação** (fechar, pular, recusar), nunca qualificar a **pessoa** (desinteressada, desinformada, mão-de-vaca).

### 4.2 Roach Motel

**Sintoma:** Fácil de entrar, difícil de sair. Assinar é 1 clique. Cancelar exige telefonema, formulário impresso ou navegação por 5 páginas.

```tsx
// ❌ Roach Motel — cancelar exige 5 passos, assinar exige 1
// Tela de assinatura: 1 botão "Assinar" → confirmado!
// Tela de cancelamento:
//   Step 1: "Tem certeza?" → Step 2: "Sentiremos falta" →
//   Step 3: "Ligue para 0800" → Step 4: "Preencha formulário" →
//   Step 5: "Enviaremos email em 5 dias úteis"
```

```tsx
// ✅ Cancelamento tão fácil quanto assinatura
function CancelSubscriptionScreen() {
  return (
    <Screen>
      <Text variant="h2">Cancelar Premium</Text>
      <Text>Você perderá acesso a:</Text>
      <BulletList items={['Relatórios avançados', 'Suporte prioritário']} />
      <Text>Seus dados serão preservados por 90 dias caso mude de ideia.</Text>
      <Button title="Cancelar Premium" onPress={confirmCancel} variant="danger" />
      <Button title="Manter Premium" onPress={goBack} variant="ghost" />
    </Screen>
  );
}
```

**Regra:** `steps(cancelar) ≤ steps(assinar)`. Sempre.

### 4.3 Mystery Meat

**Sintoma:** Elemento interativo cuja função só é descoberta após interação. Ícones sem label, botões sem texto, gestos secretos.

```tsx
// ❌ Mystery Meat — ícone sem label, hover obrigatório para descobrir
<Toolbar>
  <IconButton icon="star" />   {/* O que faz? Favoritar? Avaliar? */}
  <IconButton icon="dots" />   {/* O que faz? Menu? Mais opções? */}
  <IconButton icon="arrow" />  {/* O que faz? Voltar? Avançar? Baixar? */}
</Toolbar>

// ❌ Mystery Meat — gesto secreto, sem affordance
<View onSwipeLeft={deleteItem}>  {/* Usuário descobre deletando sem querer */}
  <Text>{item.name}</Text>
</View>
```

```tsx
// ✅ Label visível + ícone de apoio
<Toolbar>
  <IconButton icon="star" label="Favoritar" />
  <IconButton icon="dots" label="Mais opções" />
  <IconButton icon="arrow-left" label="Voltar" />
</Toolbar>

// ✅ Gesto com affordance visual + confirmação
<SwipeableRow
  onSwipeLeft={showDeleteConfirm}
  rightAction={{ icon: 'trash', label: 'Deletar', color: 'danger' }}
>
  <Text>{item.name}</Text>
</SwipeableRow>
```

**Regra:** Função de todo elemento interativo deve ser compreensível **antes** da interação. Ícone + label sempre que possível.

### 4.4 Falta de Recovery

**Sintoma:** Erro sem caminho de recuperação. Usuário recebe mensagem de erro e não sabe o que fazer.

```tsx
// ❌ Sem recovery — o usuário fica paralisado
try {
  await api.fetchData();
} catch (error) {
  Alert.alert('Erro', 'Não foi possível carregar os dados.');
  // E agora? Usuário olha para a tela sem saber o que fazer.
}

// ❌ Mensagem técnica inútil para o usuário
Alert.alert('Erro', 'ECONNREFUSED 192.168.1.1:5432');
```

```tsx
// ✅ Recovery — ação concreta + explicação em linguagem do usuário
function showErrorAlert(error: ApiError) {
  Alert.alert(
    'Não foi possível carregar seus dados',
    'Verifique sua conexão de internet e tente novamente.',
    [
      { text: 'Tentar novamente', onPress: () => refetch(), style: 'default' },
      { text: 'Usar dados offline', onPress: () => loadFromCache() },
      { text: 'Falar com suporte', onPress: () => openSupportChat() },
    ]
  );
}
```

**Regra:** Toda mensagem de erro visível ao usuário deve incluir **pelo menos uma** ação de recuperação concreta. Nunca apenas "OK".

### 4.5 Autonomia sem Controle

**Sintoma:** Sistema toma decisões pelo usuário sem explicar, permitir ajuste ou oferecer override.

```tsx
// ❌ Autonomia sem controle — IA decide e usuário não sabe por quê
function SmartCategorizer({ transaction }) {
  const category = aiCategorize(transaction.description);
  // Categoria atribuída automaticamente, sem explicação, sem opção de mudar
  return <Badge>{category}</Badge>;
}

// ❌ Configuração aplicada sem confirmação
function AutoOptimizer() {
  useEffect(() => {
    aiOptimizeSettings(); // Altera configurações do usuário sem perguntar
  }, []);
}
```

```tsx
// ✅ Controle explícito — explicação + ajuste manual
function SmartCategorizer({ transaction }) {
  const { category, confidence } = aiCategorize(transaction.description);

  return (
    <View>
      <Badge>{category}</Badge>
      {confidence < 0.85 && (
        <Text variant="caption">
          Não tenho certeza desta categoria. Toque para alterar.
        </Text>
      )}
      <Button title="Alterar categoria" onPress={showCategoryPicker} variant="link" />
    </View>
  );
}

// ✅ Configuração com consentimento explícito
function AutoOptimizer() {
  return (
    <Banner
      title="Otimização disponível"
      description="Encontramos 3 configurações que podem melhorar sua experiência: [lista]. Deseja aplicar?"
      actions={[
        { title: 'Aplicar todas', onPress: applyAll },
        { title: 'Revisar uma a uma', onPress: reviewIndividually },
        { title: 'Agora não', onPress: close },
      ]}
    />
  );
}
```

**Regra:** Toda decisão automática deve ser: (1) explicável, (2) ajustável, (3) reversível. O usuário é o **controlador final**, não a IA.

---

## 🏗️ 5. Padrões de Implementação

### 5.1 useForm — Formulário Padronizado

Hook que garante consistência em todos os formulários do projeto.

```typescript
// Template: src/hooks/useForm.ts
// Garante: label, hint, validação inline, estado de erro, dirty tracking

interface UseFormOptions<T> {
  initialValues: T;
  validate: (values: T) => Partial<Record<keyof T, string>>;
  onSubmit: (values: T) => Promise<void>;
}

function useForm<T extends Record<string, any>>(options: UseFormOptions<T>) {
  const [values, setValues] = useState(options.initialValues);
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Set<keyof T>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const validateField = (name: keyof T) => {
    const fieldErrors = options.validate(values);
    setErrors(prev => ({ ...prev, [name]: fieldErrors[name] }));
  };

  const handleChange = (name: keyof T, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    if (touched.has(name)) validateField(name);
  };

  const handleBlur = (name: keyof T) => {
    setTouched(prev => new Set(prev).add(name));
    validateField(name);
  };

  const handleSubmit = async () => {
    // Touch all fields to show all errors on submit attempt
    const allFields = new Set(Object.keys(values) as (keyof T)[]);
    setTouched(allFields);

    const allErrors = options.validate(values);
    setErrors(allErrors);

    if (Object.values(allErrors).some(Boolean)) return;

    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await options.onSubmit(values);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : 'Erro ao enviar. Tente novamente.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    values, errors, touched, isSubmitting, submitError,
    handleChange, handleBlur, handleSubmit,
    isValid: !Object.values(errors).some(Boolean),
    isDirty: touched.size > 0,
  };
}
```

### 5.2 FormField — Campo Padronizado

Wrapper que aplica label, hint, validação e estados de erro automaticamente.

```typescript
// Template: src/components/FormField.tsx
// Garante: label visível, hint text, erro inline, acessibilidade

interface FormFieldProps {
  label: string;          // Sempre visível (não usar só placeholder)
  hint?: string;          // Texto de ajuda abaixo do campo
  error?: string;         // Mensagem de erro (undefined = válido)
  required?: boolean;     // Mostra asterisco
  children: React.ReactNode; // O input em si
}

function FormField({ label, hint, error, required, children }: FormFieldProps) {
  const id = useId();
  return (
    <View className="form-field">
      <Label htmlFor={id}>
        {label}
        {required && <Text className="required-indicator" aria-hidden>*</Text>}
      </Label>
      {React.cloneElement(children as React.ReactElement, {
        id,
        'aria-invalid': !!error,
        'aria-describedby': error ? `${id}-error` : hint ? `${id}-hint` : undefined,
      })}
      {hint && !error && (
        <Text id={`${id}-hint`} className="hint-text">{hint}</Text>
      )}
      {error && (
        <Text id={`${id}-error`} className="error-text" role="alert">{error}</Text>
      )}
    </View>
  );
}
```

### 5.3 showErrorAlert — Diálogo de Erro com Recovery

Função que substitui `Alert.alert()` genérico por diálogo com ação de recuperação.

```typescript
// Template: src/utils/showErrorAlert.ts
// Garante: toda mensagem de erro tem ação de recuperação

interface ErrorAlertOptions {
  title: string;           // O que deu errado (linguagem do usuário)
  message: string;         // Por que aconteceu + o que fazer
  recoveryAction: {        // Ação principal de recuperação
    label: string;         // Verbo + objeto: "Tentar novamente"
    onPress: () => void;
  };
  secondaryAction?: {      // Ação alternativa
    label: string;         // "Usar dados offline", "Falar com suporte"
    onPress: () => void;
  };
}

function showErrorAlert({
  title, message, recoveryAction, secondaryAction
}: ErrorAlertOptions) {
  const buttons: AlertButton[] = [
    { text: recoveryAction.label, onPress: recoveryAction.onPress, style: 'default' },
  ];
  if (secondaryAction) {
    buttons.push({ text: secondaryAction.label, onPress: secondaryAction.onPress });
  }
  buttons.push({ text: 'Fechar', style: 'cancel' }); // Sempre permitir dismiss

  Alert.alert(title, message, buttons);
}

// Uso:
// showErrorAlert({
//   title: 'Falha no pagamento',
//   message: 'Seu cartão foi recusado. Verifique os dados ou use outro cartão.',
//   recoveryAction: { label: 'Tentar novamente', onPress: retryPayment },
//   secondaryAction: { label: 'Usar outro cartão', onPress: changeCard },
// });
```

### 5.4 i18n — Internacionalização Obrigatória

Wrapper que garante que toda string visível passe pelo sistema de tradução.

```typescript
// Template: src/utils/i18n.ts
// Garante: toda string visível é traduzível
// Hard gate #7: NUNCA usar string hardcoded visível ao usuário

const translations: Record<string, Record<string, string>> = {
  'checkout.payment.title': {
    pt: 'Pagamento',
    en: 'Payment',
  },
  'checkout.payment.failed': {
    pt: 'Falha no pagamento',
    en: 'Payment failed',
  },
  'common.tryAgain': {
    pt: 'Tentar novamente',
    en: 'Try again',
  },
  'common.cancel': {
    pt: 'Cancelar',
    en: 'Cancel',
  },
};

type Locale = 'pt' | 'en';

let currentLocale: Locale = 'pt';

export function setLocale(locale: Locale) {
  currentLocale = locale;
}

export function t(key: string, fallback?: string): string {
  const entry = translations[key];
  if (!entry) {
    if (process.env.NODE_ENV === 'development') {
      console.warn(`[i18n] Missing translation key: "${key}"`);
    }
    return fallback ?? key;
  }
  return entry[currentLocale] ?? entry['pt'] ?? fallback ?? key;
}

// Fitness function: detecta strings hardcoded em JSX
// Regex: >[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{3,}.*<
// (string com inicial maiúscula + 3+ caracteres entre tags — provável texto visível)
```

### 5.5 Fitness Function — UX Checks

Integração com `fitness-functions.py --check-ux`:

```bash
# Executa verificações de UX
python .ace/scripts/fitness-functions.py --check-ux --strict

# Checks incluídos:
# 1. no-hardcoded-strings — strings visíveis sem t('key')
# 2. no-confirmshaming — padrões de texto depreciativo em botões
# 3. no-alert-without-recovery — Alert.alert sem ação de recuperação
# 4. no-roach-motel — fluxo de cancelamento > fluxo de assinatura (heurística)
# 5. form-field-without-label — input sem label visível associado
```

```yaml
# Expansão do .ace/arch-config.yaml (Step 5a) com UX rules:
ux_rules:
  - name: "no-hardcoded-strings"
    check: "regex_pattern"
    patterns:
      - ">[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{3,}.*<"  # Texto visível hardcoded
    exclude_patterns:
      - "**/test/**"
      - "**/*.test.*"
      - "**/*.spec.*"
    severity: "warning"
    message: "Hardcoded user-visible string. Use t('key') for i18n."

  - name: "no-confirmshaming"
    check: "regex_pattern"
    patterns:
      - "(?:prefiro|não quero|não me importo|sou|estou)\\s+(?:pagar|continuar|ficar|ser|estar)"
    exclude_patterns:
      - "**/test/**"
      - "**/*.test.*"
    severity: "warning"
    message: "Possible confirmshaming detected. Refusal option should be neutral."

  - name: "no-alert-without-recovery"
    check: "regex_pattern"
    patterns:
      - "Alert\\.alert\\s*\\(\\s*['\"][^'\"]+['\"]\\s*,\\s*['\"][^'\"]+['\"]\\s*\\]\\s*\\)"
    severity: "warning"
    message: "Alert.alert without recovery action button. Add at least one actionable button."

  - name: "form-field-without-label"
    check: "regex_pattern"
    patterns:
      - "<(?:TextInput|Input|input).*(?!.*(?:label|aria-label|placeholder)).*\\/>"
    severity: "error"
    message: "Form input without label. Every input must have an associated visible label."
```

---

## 📝 6. Prompt de Execução

Você está executando a skill `llc-step-7a-ux-heuristics` do pipeline LLC. Seu objetivo é **estabelecer a disciplina de UX** que será aplicada em toda sessão de geração de interfaces.

### 6.1 Leia as Entradas

- `docs/design/DESIGN_SYSTEM.md` — tokens, componentes, padrões visuais (Step 7)
- `docs/business/specs/visao_estrategica_e_negocio.md` — identidade, propósito, público-alvo (Step 0.5)
- `docs/business/specs/perfis_permissoes.md` — perfis de usuário (Step 1)
- `docs/architecture/ARCHITECTURE.md` — stack frontend (Step 5)

### 6.2 Execute as Verificações

1. **Crie ou valide Personas:** Se `docs/business/personas.md` não existe, crie 2-4 personas baseadas nos perfis de acesso e visão estratégica. Se existe, valide consistência.
2. **Valide os Hard Gates:** Confirme que o AGENTS.md referencia as 10 regras intransponíveis (§1).
3. **Verifique os Padrões:** Confirme que os 4 padrões de implementação (§5) estão acessíveis ao agente.
4. **Execute UX Fitness Functions:** `fitness-functions.py --check-ux` para estabelecer baseline.
5. **Expanda o Design System:** Adicione seção de heurísticas e anti-padrões ao `DESIGN_SYSTEM.md`.

### 6.3 Regras Críticas

- **Stack-awareness:** Adaptar padrões ao stack real (React Native → `Alert.alert`; Web → toast notifications; CLI → `console.error` com sugestão).
- **Personas não são opcionais:** Se não existem, o primeiro output desta skill são as personas. Sem personas, hard gate #1 bloqueia toda geração de tela.
- **i18n desde o início:** Mesmo projeto monolíngue, usar `t('key')` desde a primeira string. Adicionar i18n depois de 500 strings hardcoded é inviável.

---

## 📤 7. Saída Esperada e Finalização

Após executar esta skill, **PARE** e apresente:

1. **Personas:** Quantas personas foram criadas/validadas? Cobrem todos os perfis de acesso?
2. **Hard Gates:** As 10 regras foram injetadas no AGENTS.md ou equivalente?
3. **Padrões:** Os 4 padrões (useForm, FormField, showErrorAlert, i18n) estão acessíveis?
4. **Fitness Functions:** `fitness-functions --check-ux` executou? Resultado do baseline?
5. **Próximos Passos:** "UX Heuristics ativo. Toda geração de tela agora exige validação de persona + checklist Nielsen + anti-padrões verificados."

**Gate 7a — Validação Humana:**
- [ ] As personas são representativas do público real do projeto?
- [ ] As 10 hard gates fazem sentido para o tipo de aplicação (mobile/web/voice/CLI)?
- [ ] Nielsen Checklist foi aplicado a pelo menos 1 tela como exercício?
- [ ] Os 4 padrões de implementação são compatíveis com o stack?
- [ ] Algum anti-padrão é particularmente relevante para este domínio? (Ex: Roach Motel crítico para SaaS com subscription)
- [ ] Exceções documentadas (ex: app de voz → gate #10 expandido; app CLI → gate #3 adaptado)?

**NÃO prossiga para Step 8 sem Gate 7a aprovado.**

---

## 🔗 8. Integração com Outros Steps

| Step | Integração |
|------|------------|
| **0.5 Visão Estratégica** | Fornece identidade e público-alvo para personas |
| **1 Perfis** | Perfis de acesso → personas + permission-aware UI |
| **5 Arquitetura** | Stack frontend define implementação dos padrões |
| **7 Design System** | Skill 7a expande o DS com heurísticas e anti-padrões |
| **8 Setup + Mock** | Setup de i18n, configuração de eslint-plugin-i18n |
| **10 AGENTS.md** | Hard gates injetados no Master Prompt |
| **11 Execução PRPs** | Validação de persona + checklist Nielsen antes de cada tela |
| **11b Arch Fitness** | Re-execução de `--check-ux` no PRP Verify |

---

## 📚 9. Referências

- **Nielsen, J. (1994, atualizado 2020)** — *10 Usability Heuristics for User Interface Design*. NN/g (Nielsen Norman Group). nngroup.com.
- **Cooper, A. (1999)** — *The Inmates Are Running the Asylum: Why High-Tech Products Drive Us Crazy*. Sams. Introdução ao design baseado em personas.
- **Goodwin, K. (2009)** — *Designing for the Digital Age: How to Create Human-Centered Products and Services*. Wiley.
- **Brignull, H. (2010)** — *Deceptive Patterns (Dark Patterns)*. deceptive.design. Tipologia de padrões enganosos.
- **WCAG 2.2 (2023)** — *Web Content Accessibility Guidelines*. W3C. w3.org/WAI/WCAG22. Critérios 3.3.2 (Labels), 2.4.7 (Focus Visible), 4.1.3 (Status Messages).
- **Norman, D. (2013)** — *The Design of Everyday Things*. Basic Books. Affordances, signifiers, mappings, feedback.
- **Krug, S. (2014)** — *Don't Make Me Think, Revisited*. New Riders. Usabilidade intuitiva, teste de usabilidade com 3 usuários.
- **Molich, R. & Nielsen, J. (1990)** — Heuristic Evaluation of User Interfaces. ACM CHI'90.
- **ISO 9241-210:2019** — Ergonomics of human-system interaction — Human-centred design for interactive systems.
