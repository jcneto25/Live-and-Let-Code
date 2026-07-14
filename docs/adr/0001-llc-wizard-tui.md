# ADR-0001: LLC Wizard como TUI com Textual

> **Status:** Proposto
> **Data:** 2026-07-11
> **Decidido por:** Equipe LLC (sessao de Grilling + Domain Modeling)

---

## Contexto

O LLC opera exclusivamente via CLI (`llc.py`) e agentes de IA em terminal. O usuario solicitou uma interface grafica web para orquestrar o pipeline com indicadores de progresso e gates didaticos. Apos analise, identificamos que uma TUI no terminal preserva melhor o ethos terminal-first do LLC, elimina a complexidade de servidor web/BFF, e entrega resultado visual rico com custo de implementacao muito menor.

## Decisao

**Construir o Wizard como TUI (Terminal UI) com o framework Textual (Python 3.10+ async), como camada de apresentacao sobre o `llc.py` existente.**

Especificamente:

1. **Stack:** Textual (widgets ricos, async, suporte a Workers para subprocess). Nada de servidor web, nada de browser.
2. **Layout:** 3 paineis fixos — sidebar esquerda (lista de steps com status), area principal dividida em contexto (topo) e output/gate (base).
3. **Gates:** Checklists interativas item-por-item renderizadas a partir de `.ace/config/gates.json`, com suporte a modo bypass (`--auto-approve`).
4. **Handoff com agente:** Modo primario: wrapper sobre `llc.py` via subprocess, capturando stdout/stderr em tempo real. Modo fallback: prompt formatado para copia-cola no cliente de IA do usuario.
5. **Progresso:** Barra horizontal + lista de steps com icones de status (concluido, em andamento, pendente, gate pendente, falhou).

## Alternativas Consideradas

| Alternativa | Por que rejeitamos |
|-------------|-------------------|
| **GUI Web (React/Vue + servidor)** | Exige BFF, servidor HTTP, roteamento, autenticacao. Alto custo de implementacao. Quebra o ethos terminal-first. Adiciona superficie de seguranca desnecessaria. Contraria "No Over-Engineering". |
| **Terminal embutido no browser (xterm.js)** | Fragil: subprocess no browser + xterm.js + proxy WebSocket. Complexidade desproporcional ao beneficio. |
| **API-based agent abstraction** | Adiciona camada de abstracao sobre clientes de IA que ja funcionam. Viola "No Over-Engineering" e o principio tool-agnostic (o Wizard abstrairia o que nao precisa abstrair). |
| **CLI enriquecida (rich, nao-TUI)** | Menor esforco, mas entrega experiencia inferior: sem navegacao por teclado, sem widgets interativos, sem atualizacao em tempo real. Nao e um "Wizard" de fato. |
| **urwid / npyscreen** | Bibliotecas maduras porem com API mais verbosa e menos widgets que Textual. Textual oferece layout declarativo, temas, e Workers para subprocess. |

## Consequencias

**Positivas:**
- Preserva o ethos terminal-first do LLC — o Wizard roda onde o `llc.py` ja roda
- Zero custo de infraestrutura: sem servidor, sem deploy, sem auth
- Reutiliza 100% do harness existente (`llc.py`, `initialize_session.py`, `finalize_session.py`, `gates.json`)
- Textual suporta Workers async — ideal para subprocess de longa duracao (steps)
- Layout de 3 paineis e possivel com `Horizontal`/`Vertical` containers nativos do Textual

**Negativas:**
- Limitado ao terminal — usuarios que esperam uma GUI web nao serao atendidos
- Textual e uma dependencia nova no projeto (~300KB). Nao e pesada, mas e mais uma
- TUI nao e acessivel via leitores de tela como uma GUI web seria

**Riscos:**
- Se o Textual evoluir com breaking changes, o Wizard precisa acompanhar. Mitigacao: pin de versao no `requirements.txt`
- Subprocess de longa duracao (`llc.py` steps) pode travar se o Textual nao gerenciar Workers corretamente. Mitigacao: testar com steps reais antes de declarar estavel
