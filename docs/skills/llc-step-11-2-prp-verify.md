---
name: llc-step-11-2-prp-verify
description: Pipeline LLC — Aceite mecânico de PRP. Verifica se cada RF declarado na §2 tem arquivos de teste/impl reais (não stub), se os componentes da §6 existem, e se os testes da §9 não são teatro. O merge é bloqueado automaticamente pelo session_end() se houver CRITICAL.
version: 1.0.0
tags: [prp, verification, acceptance, gate, llc-pipeline]
---

# LLC Skill: Step 11.2 — PRP Verify (Aceite de PRP)

**Pipeline:** Live and Let Code (LLC)
**Fase:** Pós-Implementação / Pré-Merge
**Depende de:** Step 11 (PRP implementado com código + testes), Gate 11.1-OWASP aprovado
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-11-2-prp-verify` ou "Execute a skill llc-step-11-2-prp-verify".
3. Execute APÓS a implementação do PRP (código e testes escritos) e APÓS o hardening OWASP.

> **⚠️ Nota:** Esta skill é **advisory** — o guia humano para a cerimônia de aceite.
> O **enforcement mecânico** está no `session_end()` do harness (Step 11.2 determinístico),
> que bloqueia o merge em CRITICAL. A skill existe para dar visibilidade e gerar o
> relatório RF-por-RF antes do merge.

## 📋 Pré-requisitos

- [ ] PRP implementado (código escrito, testes passando)
- [ ] `docs/prps/PRP-{ID}.md` — PRP com §2 preenchida (colunas Teste(s) e Arquivo(s) impl)
- [ ] Gate 11-OWASP aprovado (hardening pós-código concluído)
- [ ] `python .ace/scripts/prp_verify.py` — engine de verificação (já incluso no harness)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-11-2-prp-verify` do pipeline LLC. Seu objetivo
é verificar mecanicamente se o PRP concluído tem evidências reais de implementação
para cada RF declarado — e emitir um relatório de gaps RF-por-RF.

### 1. Identifique o PRP Alvo

- Obtenha o ID do PRP concluído (ex.: `PRP-001`) do contexto da sessão.
- Confirme com o humano: *"Vou verificar o aceite mecânico de {PRP-ID}. Prosseguir?"*

### 2. Execute o `prp_verify.py`

```bash
python .ace/scripts/prp_verify.py --prp {PRP-ID} --strict --json
```

**Flags:**
- `--prp {ID}` — PRP alvo (ex.: `PRP-001`)
- `--strict` — exit code 2 se houver CRITICAL (bloqueante)
- `--json` — output estruturado para parsing

### 3. Leia o Resultado

O output JSON tem esta estrutura:

```json
{
  "prps": [
    {
      "prp": "PRP-001",
      "critical": 0,
      "warn": 1,
      "findings": [
        {
          "severity": "WARN",
          "code": "stub_test",
          "message": "possível teatro de testes em tests/stub_test.py: ...",
          "rf": "",
          "file": "tests/stub_test.py"
        }
      ]
    }
  ],
  "critical": 0,
  "warn": 1
}
```

**Interpretação das severidades:**

| Severidade | Significado | Ação |
|---|---|---|
| 🔴 **CRITICAL** | Arquivo declarado ausente, stub, ou componente faltando | **Bloqueia merge** — corrija antes de avançar |
| 🟡 **WARN** | Stub-test, PRP legado sem rastreabilidade, endpoint não localizado | Revise e documente justificativa na §11 do PRP |

### 4. Emita os Bloqueadores

Para cada finding **CRITICAL**, emita um `<blocker>`:

```xml
<blocker resolved="false">PRP-001: RF-001.1 — arquivo declarado ausente: src/services/patient.service.ts</blocker>
```

Para cada finding **WARN** aceito com justificativa, registre na seção §11 do PRP:

```markdown
| {DATA} | WARN aceito: {código} — {justificativa} | {contexto} | {impacto} | {ação futura} | Aceito |
```

### 5. Registre a Decisão do Gate

```xml
<gate_result step="11.2" decision="approved" reviewer="llc-step-11-2-prp-verify">
  PRP-001: 0 CRITICAL, 2 WARN (justificados na §11). Aceite mecânico aprovado.
</gate_result>
```

Ou, se houver CRITICAL:

```xml
<gate_result step="11.2" decision="rejected" reviewer="llc-step-11-2-prp-verify">
  PRP-001: 1 CRITICAL (RF-001.1 — arquivo ausente). Correção necessária antes do merge.
</gate_result>
```

---

## ⚠️ REGRAS CRÍTICAS

1. **Nunca marque ✅ com CRITICAL aberto:** Se `prp_verify --strict` retornar exit 2,
   o merge está bloqueado mecanicamente pelo `session_end()`. A skill não pode
   contrapor o enforcement — registre os blockers e escale.

2. **WARNs aceitos exigem justificativa:** WARNs (stub-test, PRP legado, endpoint
   não localizado) podem ser aceitos, mas a justificativa DEVE ser registrada na
   seção §11 do PRP (Dívida Técnica e Decisões). Sem justificativa, o WARN é uma
   pendência não endereçada.

3. **Bypass explícito e logado:** Se o humano decidir fazer merge mesmo com CRITICAL,
   o bypass é `LLC_PRP_NO_VERIFY=1` (documentado em §8.7 da pipeline design).
   Isso é logado e deve ser uma exceção explícita — jamais use sem registro.

4. **PRPs legados (sem §2 cols):** Recebem WARN automático — não bloqueiam, mas
   a verificação manual é necessária. Documente a verificação manual na §11.

5. **Idempotência:** Re-execução desta skill sobrescreve o `<gate_result>` anterior
   (o `session_end()` é idempotente — só registra o primeiro `<gate_result>` real).

---

## 📤 SAÍDA ESPERADA

- Relatório RF-por-RF com findings (lido do stdout do `prp_verify.py`)
- Bloqueadores emitidos para cada CRITICAL
- `<gate_result step="11.2">` registrado na sessão
- Justificativas de WARN registradas na §11 do PRP (se aplicável)

---

### Próximos Passos

- **Aprovado (0 CRITICAL):** Prossiga para merge do PRP (via `session_end()` do harness).
- **Rejeitado (CRITICAL):** Corrija as pendências (implemente arquivos ausentes, remova
  stubs) e re-execute esta skill.
- **Bypass:** Use `LLC_PRP_NO_VERIFY=1` apenas em emergência documentada.
