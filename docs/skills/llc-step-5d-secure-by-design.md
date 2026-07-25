---
name: llc-step-5d-secure-by-design
description: Pipeline LLC Step 5d — Secure-by-Design Enforcement. Estabelece 10 hard gates de segurança que o agente carrega antes de gerar qualquer código. Complementa Steps 11-Security (pré-execução SCA+SAST+secrets) e 11-OWASP (hardening pós-implementação) com prevenção no momento da geração.
version: 1.0.0
tags: [security, secure-by-design, owasp, encryption, auth, pii, sql-injection, secrets, fail-closed, llc-pipeline]
---

# LLC Skill: Step 5d — Secure-by-Design Enforcement

**Pipeline:** Live and Let Code (LLC)
**Fase:** Architecture (sub-step of Step 5 — after Step 5c Clean Code Enforcement)
**Depende de:** Step 5c (Clean Code Enforcement validado)
**Executa antes de:** Step 6 (Tasks) e Step 8 (Setup + Mock)
**Mantenedor:** Equipe LLC

---

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-5d-secure-by-design` ou "Execute a skill llc-step-5d-secure-by-design".
3. Pelo Thin Harness (recomendado): `python .ace/scripts/llc.py run --step 5d --task "Enforcar Secure-by-Design"`.

---

## 📋 Pré-requisitos

- [ ] `docs/architecture/ARCHITECTURE.md` — stack, frameworks, auth strategy (Step 5)
- [ ] `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` — padrões arquiteturais (Step 5a)
- [ ] `.ace/arch-config.yaml` — configuração de fitness functions (Step 5a, será expandido)
- [ ] `docs/business/specs/perfis_permissoes.md` — perfis de acesso e matriz RBAC (Step 1)
- [ ] `docs/security/SECURITY_AUDIT_REPORT_TEMPLATE.md` — template do relatório de segurança (Step 11)

---

## 🔄 Modo Delta — Smart Skip Check

**Se `docs/planning/DELTA_REPORT.md` existir e estiver aprovado (Gate Δ.0):**

1. Leia a seção §5.3 (Steps a Pular) do DELTA_REPORT.md.
2. Se **Step 5d** estiver listado como "skip":
   - Gere skip note em `docs/delta/skip-notes/step-5d.md`:
     ```markdown
     # Skip Note: Step 5d — Secure-by-Design Enforcement
     **Decisão:** Step pulado — regras de segurança inalteradas desde última execução.
     **Evidência:** Fitness functions `--check-security` passam sem violações novas.
     **Validador:** [Nome] | **Data:** [YYYY-MM-DD]
     ```
   - **Não execute** as verificações nem aguarde Gate 5d.
   - Avance para Step 6.
3. Se DELTA_REPORT.md não existir: prossiga normalmente.

---

## 🎯 OBJETIVO

Estabelecer regras de segurança que o agente **carrega antes de gerar qualquer código**, complementando a detecção reativa dos Steps 11-Security (SCA + SAST + secrets pré-execução) e 11-OWASP (hardening pós-implementação).

**Princípio fundamental:** É mais barato prevenir código inseguro do que detectá-lo depois.

Esta skill atua em 4 frentes:

| Frente | Descrição | Referência |
|--------|-----------|------------|
| **Hard Gates** | 10 regras intransponíveis que o agente NUNCA deve violar | OWASP Top 10:2021 |
| **Threat Modeling** | 6 perguntas de raciocínio obrigatório antes de cada feature | STRIDE / LINDDUN |
| **Safe Code Templates** | 4 templates de código seguro que o agente deve usar | OWASP Cheat Sheets |
| **Fitness Functions** | 5 verificações automatizadas de segurança | `.ace/arch-config.yaml` |

---

## 🛑 1. Hard Gates (Regras Intransponíveis)

*O agente NUNCA deve:*

1. **NUNCA** hardcode keys, secrets, tokens ou passwords no código fonte.
   - Derivar de variáveis de ambiente (`process.env.SECRET`), EAS Secrets, SecureStore (mobile) ou Keychain/Keystore.
   - Exceção: valores em `.env.example` (documentação, sem valores reais).

2. **NUNCA** usar fallback criptográfico fraco (XOR, MD5, SHA1 para senhas, DES, RC4).
   - Se a criptografia forte falhar, o sistema deve **falhar fechado** (throw error).
   - "Fail-open" (fallback para plaintext) é inaceitável.

3. **NUNCA** reusar IV (Initialization Vector) em criptografia simétrica.
   - Usar `crypto.getRandomValues()` para gerar IV fresco **a cada operação**.
   - IV estático (`new Uint8Array(16)` com zeros) é equivalente a texto plano.

4. **NUNCA** armazenar tokens de autenticação, chaves de criptografia ou PII em `AsyncStorage` (ou equivalente não seguro).
   - Mobile: `expo-secure-store` (iOS Keychain / Android Keystore).
   - Web: cookies `httpOnly` + `secure` + `sameSite=strict`.
   - Backend: secrets manager / vault.

5. **NUNCA** interpolar valores em queries SQL usando template literals (`${var}`).
   - Usar **exclusivamente** parâmetros bind (`?` ou `$1`).
   - Para SQL dinâmico (cláusulas SET/WHERE variáveis), usar **allowlist** de colunas.

6. **NUNCA** logar PII (emails, telefones, CPF, CNPJ, endereços, cartões) ou stack traces completos em produção.
   - Usar `sanitizeForLogging()` que aplica regex de redação.
   - Logs de debug (`console.log`, `logger.debug`) devem ser desativados em builds de produção (`__DEV__`).

7. **NUNCA** permitir fallback que conceda privilégios (premium, admin) se a verificação falhar.
   - "Se offline e cache expirou → Free Tier" (nunca assumir Premium).
   - "Se backend inacessível → negar acesso" (nunca conceder admin por timeout).

8. **NUNCA** validar entitlements (premium, permissões, limites) apenas no client-side.
   - Backend é a única fonte da verdade para autorização.
   - Client-side é apenas UX (esconder/mostrar UI) — nunca enforcement.

9. **NUNCA** usar AES-CBC para dados sensíveis.
   - Usar **exclusivamente AES-256-GCM** (criptografia autenticada).
   - GCM provê confidencialidade + integridade + autenticidade em um único algoritmo.

10. **NUNCA** criar tabelas de entidades de domínio sem coluna de propriedade (`user_id` / `owner_id`).
    - Toda query de leitura/escrita deve filtrar por `user_id`.
    - `user_id` deve ser obtido de forma segura (token JWT validado, não parâmetro de requisição).

---

## 🧠 2. Threat Modeling Check (Obrigatório Antes de Cada Feature)

Antes de implementar qualquer feature que envolva dados sensíveis, rede ou permissões, o agente deve executar este raciocínio (Chain of Thought):

```markdown
### 🛡️ Threat Modeling Check

1. **Quais dados são PII ou sensíveis?**
   (Ex: endereço, telefone, token JWT, chave de API, CPF)

2. **Onde serão armazenados?**
   (Ex: SQLite no dispositivo, PostgreSQL no backend, SecureStore para tokens)

3. **Como serão protegidos em repouso?**
   (Ex: AES-256-GCM com chave per-user derivada do Keystore)

4. **Como serão protegidos em trânsito?**
   (Ex: HTTPS com TLS 1.3, SSL Pinning para mobile, certificados validados)

5. **Quem tem acesso?**
   (Ex: Query filtrada por `user_id`? Endpoint tem middleware de auth? Perfil tem permissão?)

6. **O que acontece se falhar?**
   (Ex: Se SecureStore falhar, fallback para AsyncStorage? NÃO — lançar erro e bloquear operação)
```

**Regra de saída:** Se o agente não consegue responder a TODAS as 6 perguntas, a feature **não está pronta** para implementação.

---

## 🏗️ 3. Safe Code Templates

Templates de referência que o agente deve usar ao gerar código nos domínios sensíveis abaixo.

### 3.1 Criptografia de PII (AES-256-GCM)

```typescript
// TEMPLATE: src/utils/piiEncryption.ts
// REGRA: Key NUNCA hardcoded. Derivar de SecureStore/Keychain por usuário.
// REGRA: IV NUNCA reusado. crypto.getRandomValues() por operação.
// REGRA: Algoritmo SEMPRE AES-256-GCM (nunca CBC).

const ALGORITHM = 'AES-GCM';
const KEY_LENGTH = 256;
const IV_LENGTH = 12; // 96 bits recomendado para GCM

async function getUserEncryptionKey(userId: string): Promise<CryptoKey> {
  const stored = await SecureStore.getItemAsync(`pii_key_${userId}`);
  if (!stored) {
    throw new SecurityError(
      `Encryption key not found for user ${userId}. Cannot proceed.`
    );
  }
  // Derivar CryptoKey do material armazenado
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    base64ToArrayBuffer(stored),
    { name: ALGORITHM, length: KEY_LENGTH },
    false,
    ['encrypt', 'decrypt']
  );
  return keyMaterial;
}

async function encryptPii(
  plaintext: string,
  userId: string
): Promise<{ ciphertext: ArrayBuffer; iv: Uint8Array }> {
  const key = await getUserEncryptionKey(userId);
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));

  const encoded = new TextEncoder().encode(plaintext);
  const ciphertext = await crypto.subtle.encrypt(
    { name: ALGORITHM, iv },
    key,
    encoded
  );

  return { ciphertext, iv };
}

async function decryptPii(
  ciphertext: ArrayBuffer,
  iv: Uint8Array,
  userId: string
): Promise<string> {
  const key = await getUserEncryptionKey(userId);

  const decrypted = await crypto.subtle.decrypt(
    { name: ALGORITHM, iv },
    key,
    ciphertext
  );

  return new TextDecoder().decode(decrypted);
}
```

### 3.2 Armazenamento Seguro (Fail-Closed)

```typescript
// TEMPLATE: src/utils/secureStorage.ts
// REGRA: NUNCA fazer fallback para AsyncStorage.
// REGRA: Se SecureStore indisponível → lançar erro (fail-closed).

import * as SecureStore from 'expo-secure-store';

export const secureStorage = {
  async getItem(key: string): Promise<string | null> {
    try {
      return await SecureStore.getItemAsync(key);
    } catch (error) {
      // NUNCA fallback para AsyncStorage
      throw new SecurityError(
        `SecureStore read failed for key '${key}'. AsyncStorage fallback is FORBIDDEN.`
      );
    }
  },

  async setItem(key: string, value: string): Promise<void> {
    try {
      await SecureStore.setItemAsync(key, value);
    } catch (error) {
      throw new SecurityError(
        `SecureStore write failed for key '${key}'. Data not persisted.`
      );
    }
  },

  async deleteItem(key: string): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(key);
    } catch (error) {
      throw new SecurityError(
        `SecureStore delete failed for key '${key}'.`
      );
    }
  },
};
```

### 3.3 Queries SQL Parametrizadas (Anti-Injeção)

```typescript
// TEMPLATE: src/services/repositories/baseRepository.ts
// REGRA: NUNCA usar template literal para valores SQL.
// REGRA: SQL dinâmico usa ALLOWLIST de colunas.

// ✅ CORRETO — parâmetros bind
const getUserById = async (id: number): Promise<User | null> => {
  const result = await db.getAsync<UserRow>(
    'SELECT * FROM users WHERE id = ?',
    [id]
  );
  return result ? mapRowToUser(result) : null;
};

// ✅ CORRETO — SQL dinâmico com allowlist
const ALLOWED_SORT_COLUMNS = ['name', 'created_at', 'updated_at'] as const;

const listUsers = async (sortBy: string): Promise<User[]> => {
  if (!ALLOWED_SORT_COLUMNS.includes(sortBy as any)) {
    throw new ValidationError(`Invalid sort column: ${sortBy}`);
  }
  // SEGURO: sortBy validado contra allowlist
  const result = await db.getAllAsync<UserRow>(
    `SELECT * FROM users ORDER BY ${sortBy} ASC`
  );
  return result.map(mapRowToUser);
};

// ❌ PROIBIDO — template literal em valor SQL
// const sql = `SELECT * FROM users WHERE id = ${userId}`;  // SQL INJECTION
// const sql = `UPDATE users SET name = '${name}' WHERE id = ${id}`;  // SQL INJECTION
```

### 3.4 Validação de Entitlements (Fail-Safe)

```typescript
// TEMPLATE: src/services/entitlementService.ts
// REGRA: Backend é única fonte da verdade.
// REGRA: Cache local com TTL curto (5 min).
// REGRA: Se offline e cache expirou → DEFAULT PARA FREE.

const ENTITLEMENT_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutos

async function checkPremiumStatus(userId: string): Promise<boolean> {
  try {
    // 1. Tentar backend (fonte da verdade)
    const backendStatus = await api.get<EntitlementResponse>(
      `/users/${userId}/entitlements`
    );
    await cacheEntitlement(userId, backendStatus);
    return backendStatus.isPremium;
  } catch (error) {
    // 2. Offline: usar cache local com TTL
    const cached = await getCachedEntitlement(userId);
    if (cached && !isExpired(cached, ENTITLEMENT_CACHE_TTL_MS)) {
      return cached.isPremium;
    }

    // 3. FAIL-SAFE: cache expirado ou inexistente → Free Tier
    logger.warn('Entitlement check failed, defaulting to Free Tier', {
      userId,
      error: sanitizeForLogging(error),
    });
    return false; // NUNCA assumir premium por dados locais stale
  }
}
```

---

## 🚦 4. Fitness Functions de Segurança

Estas 5 verificações são executadas via `fitness-functions.py --check-security` e adicionadas ao `.ace/arch-config.yaml`.

| # | Check | Descrição | Severidade |
|---|-------|-----------|------------|
| 1 | `no-hardcoded-secrets` | Regex para JWT secrets, API keys, passwords hardcoded | block |
| 2 | `no-sql-injection` | Template literals em queries SQL (possível injection) | block |
| 3 | `no-asyncstorage-tokens` | `AsyncStorage.setItem` com keys sensíveis (token, secret, key, password) | block |
| 4 | `no-client-only-auth` | Verificação de auth/entitlements apenas no client (sem backend correspondente) | warn |
| 5 | `user-id-in-tables` | Tabelas de entidades de domínio sem coluna `user_id`/`owner_id` | block |

### Expansão do `.ace/arch-config.yaml`

```yaml
# Adicionar ao .ace/arch-config.yaml existente (Step 5a)
security_rules:
  - name: "no-hardcoded-secrets"
    check: "regex_pattern"
    patterns:
      - "JWT_SECRET\\s*=\\s*['\"][^'\"]{8,}['\"]"
      - "sk-[0-9a-zA-Z]{20,}"
      - "ghp_[0-9a-zA-Z]{36}"
      - "AIza[0-9A-Za-z_-]{35}"
      - "private.*key.*=\\s*['\"][^'\"]{10,}['\"]"
      - "api[_-]?key\\s*=\\s*['\"][^'\"]{8,}['\"]"
      - "password\\s*=\\s*['\"][^'\"]{1,}['\"]"
    exclude_patterns:
      - "**/test/**"
      - "**/spec/**"
      - "**/mock/**"
      - "**/.env.example"
      - "**/*.test.ts"
      - "**/*.spec.ts"
    severity: "error"
    message: "Hardcoded secret detected. Use environment variables or secrets manager."

  - name: "no-sql-injection"
    check: "regex_pattern"
    patterns:
      - "`\\s*(SELECT|INSERT|UPDATE|DELETE)\\s.*\\$\\{"
      - "`\\s*(SELECT|INSERT|UPDATE|DELETE)\\s.*\\+\\s*[a-zA-Z]"
    exclude_patterns:
      - "**/test/**"
      - "**/spec/**"
      - "**/mock/**"
      - "**/repositories/**"  # Permitido apenas em repositories
    severity: "error"
    message: "SQL with template literal interpolation detected. Use parameterized queries (?)."

  - name: "no-asyncstorage-tokens"
    check: "regex_pattern"
    patterns:
      - "AsyncStorage\\.(setItem|getItem)\\(.*(token|secret|key|password|credential)"
    severity: "error"
    message: "Sensitive data in AsyncStorage detected. Use SecureStore/Keychain."

  - name: "no-client-only-auth"
    check: "semantic"
    heuristic: "Verificação de entitlements apenas no client (useState isPremium sem chamada backend)"
    severity: "warning"
    message: "Client-only entitlement check. Backend must be the source of truth."

  - name: "user-id-in-tables"
    check: "schema_check"
    heuristic: "Tabelas de domínio (não de sistema) sem coluna user_id/owner_id"
    severity: "error"
    message: "Domain table without user_id/owner_id column. Multi-tenant isolation required."
```

### Comando de Execução

```bash
# Executa todos os 5 checks de segurança
python .ace/scripts/fitness-functions.py --check-security --strict

# Opções:
# --strict  → falha se houver violação block
# --verbose → detalhes por arquivo
```

---

## 📝 5. Prompt de Execução

Você está executando a skill `llc-step-5d-secure-by-design` do pipeline LLC. Seu objetivo é **estabelecer as regras de Secure-by-Design** que serão injetadas em toda sessão subsequente de geração de código.

### 5.1 Leia as Entradas

- `docs/architecture/ARCHITECTURE.md` — stack, frameworks, bibliotecas (Step 5)
- `docs/architecture/ARCHITECTURE_PATTERNS_TEMPLATE.md` — padrões arquiteturais (Step 5a)
- `.ace/arch-config.yaml` — configuração fitness functions existente (Step 5a)
- `docs/business/specs/perfis_permissoes.md` — perfis de acesso, RBAC (Step 1)

### 5.2 Execute as Verificações

1. **Valide os Hard Gates:** Confirme que o AGENTS.md (ou equivalente) referencia as 10 regras intransponíveis (§1).
2. **Verifique os Templates:** Confirme que os 4 safe code templates (§3) estão acessíveis ao agente (em `docs/templates/` ou `.claude/skills/`).
3. **Expanda o arch-config.yaml:** Adicione as 5 fitness functions de segurança (§4) ao `.ace/arch-config.yaml`.
4. **Execute as Fitness Functions:** Rode `fitness-functions.py --check-security --strict` para estabelecer baseline.
5. **Gere o ADR:** Crie `docs/architecture/adr/ADR-018-secure-by-design.md` documentando as decisões.

### 5.3 Regras Críticas

- **Anti-alucinação:** As fitness functions devem ser executadas com código real. Se não houver código ainda (greenfield), marque baseline como "0 violações — projeto vazio".
- **Fail-closed é default:** Sempre que houver dúvida entre "permitir" ou "bloquear", escolher bloquear.
- **Idempotência:** Re-execução sobrescreve `.ace/arch-config.yaml` apenas na seção `security_rules`. Outras seções são preservadas.
- **Stack-awareness:** Adaptar os templates (§3) ao stack real do projeto (React Native/Expo → SecureStore; Next.js → cookies httpOnly; Python → cryptography library).

---

## 📤 6. Saída Esperada e Finalização

Após executar esta skill, **PARE** e apresente:

1. **Hard Gates:** As 10 regras foram injetadas no AGENTS.md ou equivalente?
2. **Templates:** Os 4 safe code templates estão acessíveis ao agente?
3. **Fitness Functions:** `fitness-functions.py --check-security` executou? Resultado do baseline?
4. **ADR-018:** Criado e justificado?
5. **Próximos Passos:** "Secure-by-Design ativo. Próxima sessão de geração de código carregará estas regras automaticamente."

**Gate 5d — Validação Humana:**
- [ ] As 10 hard gates fazem sentido para o domínio do projeto?
- [ ] Algum template precisa de adaptação ao stack específico?
- [ ] Fitness functions `--check-security --strict` passam sem bloqueios?
- [ ] ADR-018 criado e justificado?
- [ ] Exceções documentadas (ex: projeto sem banco de dados → regra #10 não se aplica)?

**NÃO prossiga para Step 6 sem Gate 5d aprovado.**

---

## 🔗 7. Integração com Outros Steps

| Step | Integração |
|------|------------|
| **5a Architecture Patterns** | Expande `.ace/arch-config.yaml` com `security_rules` |
| **5c Clean Code** | Complementa — Clean Code + Secure Code = qualidade total |
| **10 AGENTS.md** | Hard gates injetados no Master Prompt |
| **11-Security** | Pré-execução SCA+SAST+secrets (detecta o que passou pela prevenção) |
| **11-OWASP** | Hardening pós-código (verifica o que foi implementado) |
| **11b Arch Fitness** | Re-executa `--check-security` no PRP Verify (regressão) |

---

## 📚 8. Referências

- **OWASP Top 10:2021** — A01 Broken Access Control, A02 Cryptographic Failures, A03 Injection, A04 Insecure Design, A05 Security Misconfiguration, A07 Auth Failures
- **OWASP Cheat Sheet Series** — Cryptographic Storage, SQL Injection Prevention, Authentication, Logging
- **CWE Top 25** — CWE-798 (Hardcoded Credentials), CWE-89 (SQL Injection), CWE-327 (Weak Crypto), CWE-532 (Sensitive Data in Logs)
- **NIST SP 800-175B** — Deterministic Random Bit Generator (DRBG) for IV generation
- **STRIDE** — Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege (threat modeling framework)
- **Defesa em Profundidade (Gupta)** — Fail-Closed, Zero Trust, Defense in Depth
