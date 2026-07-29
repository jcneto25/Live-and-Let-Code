# Caso de Uso: [{CU-NNN}] — [{Nome Descritivo}]

> **ID:** CU-{NNN} | **Módulo:** {MOD-XXX} | **Ator(es):** {quem executa}
> **Prioridade:** {Crítico / Alto / Médio / Baixo} | **Status:** {⏳ / ✅ / 🔄}
> **Criado em:** {YYYY-MM-DD} | **Última atualização:** {YYYY-MM-DD}
> **PRP de origem:** {PRP-NNN ou —}

---

## 1. Objetivo de Negócio
{Uma frase clara: POR QUE este caso de uso existe. Valor para o negócio.}

## 2. Atores
| Ator | Tipo | Descrição |
|------|------|-----------|
| {Perfil} | Primário / Secundário | {O que este ator faz} |

## 3. Pré-condições
{O que DEVE ser verdade ANTES deste CU poder ser executado.}

## 4. Fluxo Principal
| Passo | Ação do Ator | Resposta do Sistema | Validação |
|-------|-------------|---------------------|-----------|
| 1 | {Ação} | {Resposta} | {Regra de negócio} |
| 2 | ... | ... | ... |

## 5. Fluxos Alternativos / Exceções
| ID | Condição | Comportamento esperado |
|----|----------|----------------------|
| ALT-01 | {Ex: dados inválidos} | {Mensagem de erro, sem persistir} |
| EXC-01 | {Ex: rede indisponível} | {Retry + mensagem} |

## 6. Pós-condições
{O que DEVE ser verdade DEPOIS do CU ser concluído com sucesso.}

## 7. Regras de Negócio Envolvidas
| ID RN | Regra | Origem |
|-------|-------|--------|
| RN-XXX | {Regra} | spec/PRD §X |

## 8. RFs de Origem (Rastreabilidade)
| RF ID | RF | Coberto por este CU? |
|-------|----|---------------------|
| RF-XXX.1 | {Requisito} | ✅ Sim / ⚠️ Parcial / ❌ Não |

## 9. PRPs Vinculados (Matriz de Rastreabilidade)
| PRP | ID | Status | Relação |
|-----|----|--------|---------|
| {PRP-NNN} | PRP-XXX | ⏳/✅/🔄 | Implementa / Afeta parcialmente |

## 10. Métricas de Sucesso (Opcional)
{Como o negócio saberá que este CU agregou valor. Ex: "redução de 30% no tempo de X".}
