#!/usr/bin/env python3
"""Testes dos checks de Segurança (Ação 1) e UX (Ação 3) — Harness Preventivo LLC.

Cobre os 5 checks de segurança (llc-step-5d-secure-by-design §4) e os
5 checks de UX (llc-step-7a-ux-heuristics §5.5), executados via
`fitness-functions.py --check-security` / `--check-ux`.

Cada teste cria uma árvore src/ sintética em tmp_path e roda o check
com CWD trocado (SRC_DIR é relativo ao CWD).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from fitness_functions.checks_security import (
    check_no_asyncstorage_tokens,
    check_no_client_only_auth,
    check_no_hardcoded_secrets,
    check_no_sql_injection,
    check_user_id_in_tables,
)
from fitness_functions.checks_ux import (
    check_form_field_without_label,
    check_no_alert_without_recovery,
    check_no_confirmshaming,
    check_no_hardcoded_strings,
    check_no_roach_motel,
)

CONFIG = {
    "core_modules": ["auth"],
    "checks": {
        "no_hardcoded_secrets": {"enabled": True, "mode": "block"},
        "no_sql_injection": {"enabled": True, "mode": "block"},
        "no_asyncstorage_tokens": {"enabled": True, "mode": "block"},
        "no_client_only_auth": {"enabled": True, "mode": "warn"},
        "user_id_in_tables": {"enabled": True, "mode": "block"},
        "no_hardcoded_strings": {"enabled": True, "mode": "warn"},
        "no_confirmshaming": {"enabled": True, "mode": "warn"},
        "no_alert_without_recovery": {"enabled": True, "mode": "warn"},
        "no_roach_motel": {"enabled": True, "mode": "warn"},
        "form_field_without_label": {"enabled": True, "mode": "block"},
    },
}


def _write(base: Path, rel: str, content: str) -> None:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ── Segurança 1: no-hardcoded-secrets ────────────────────────────────────────


def test_hardcoded_jwt_secret_blocks(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/auth/config.service.ts",
        "const JWT_SECRET = 'supersecreta12345';\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_hardcoded_secrets(CONFIG)
    assert result["violations_count"] == 1
    assert result["blocked"] is True


def test_openai_key_detected(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/llm/client.service.ts",
        "const key = 'sk-abcdefghij1234567890ABCD';\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_hardcoded_secrets(CONFIG)
    assert result["violations_count"] == 1


def test_secret_in_spec_file_ignored(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/auth/auth.service.spec.ts",
        "const JWT_SECRET = 'apenas-para-teste-x';\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_hardcoded_secrets(CONFIG)
    assert result["violations_count"] == 0
    assert result["passed"] is True


# ── Segurança 2: no-sql-injection ────────────────────────────────────────────


def test_sql_template_literal_blocks(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/users/users.service.ts",
        "const rows = await db.query(`SELECT * FROM users WHERE id = ${id}`);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_sql_injection(CONFIG)
    assert result["violations_count"] == 1
    assert result["blocked"] is True


def test_parameterized_query_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/users/users.service.ts",
        "const rows = await db.query('SELECT * FROM users WHERE id = ?', [id]);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_sql_injection(CONFIG)
    assert result["passed"] is True


# ── Segurança 3: no-asyncstorage-tokens ──────────────────────────────────────


def test_asyncstorage_token_blocks(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/auth/session.service.ts",
        "await AsyncStorage.setItem('auth_token', token);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_asyncstorage_tokens(CONFIG)
    assert result["violations_count"] == 1
    assert result["blocked"] is True


def test_asyncstorage_preferences_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/settings/prefs.service.ts",
        "await AsyncStorage.setItem('theme', 'dark');\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_asyncstorage_tokens(CONFIG)
    assert result["passed"] is True


# ── Segurança 4: no-client-only-auth ─────────────────────────────────────────


def test_client_only_entitlement_warns(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/premium/PaywallScreen.tsx",
        "const [isPremium, setIsPremium] = useState(false);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_client_only_auth(CONFIG)
    assert result["violations_count"] == 1
    assert result["blocked"] is False  # warn, não block


def test_entitlement_with_backend_call_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/premium/PaywallScreen.tsx",
        "const [isPremium, setIsPremium] = useState(false);\n"
        "const { data } = await api.get('/entitlements');\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_client_only_auth(CONFIG)
    assert result["passed"] is True


# ── Segurança 5: user-id-in-tables ───────────────────────────────────────────


def test_domain_table_without_user_id_blocks(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "migrations/001_create_posts.sql",
        "CREATE TABLE posts (\n  id SERIAL PRIMARY KEY,\n  title TEXT\n);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_user_id_in_tables(CONFIG)
    assert result["violations_count"] == 1
    assert result["blocked"] is True


def test_domain_table_with_user_id_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "migrations/001_create_posts.sql",
        "CREATE TABLE posts (\n  id SERIAL PRIMARY KEY,\n  user_id INT NOT NULL\n);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_user_id_in_tables(CONFIG)
    assert result["passed"] is True


def test_system_table_without_user_id_ignored(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "migrations/000_migrations.sql",
        "CREATE TABLE migrations (\n  id SERIAL PRIMARY KEY,\n  name TEXT\n);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_user_id_in_tables(CONFIG)
    assert result["passed"] is True


def test_prisma_model_without_owner_blocks(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "prisma/schema.prisma",
        "model Post {\n  id    Int    @id\n  title String\n}\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_user_id_in_tables(CONFIG)
    assert result["violations_count"] == 1


# ── UX 1: no-hardcoded-strings ───────────────────────────────────────────────


def test_hardcoded_jsx_string_warns(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/screens/HomeScreen.tsx",
        "return <Text>Carregando dados</Text>;\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_hardcoded_strings(CONFIG)
    assert result["violations_count"] == 1
    assert result["blocked"] is False


def test_i18n_key_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/screens/HomeScreen.tsx",
        "return <Text>{t('home.loading')}</Text>;\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_hardcoded_strings(CONFIG)
    assert result["passed"] is True


# ── UX 2: no-confirmshaming ──────────────────────────────────────────────────


def test_confirmshaming_text_warns(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/screens/PaywallScreen.tsx",
        "<Button title=\"Não quero pagar menos\" />\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_confirmshaming(CONFIG)
    assert result["violations_count"] == 1


def test_neutral_refusal_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/screens/PaywallScreen.tsx",
        "<Button title=\"Agora não\" />\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_confirmshaming(CONFIG)
    assert result["passed"] is True


# ── UX 3: no-alert-without-recovery ──────────────────────────────────────────


def test_alert_without_buttons_warns(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/screens/SyncScreen.tsx",
        "Alert.alert('Erro', 'Falha ao sincronizar');\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_alert_without_recovery(CONFIG)
    assert result["violations_count"] == 1


def test_alert_with_recovery_action_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/screens/SyncScreen.tsx",
        "Alert.alert('Erro', 'Falha ao sincronizar', "
        "[{ text: 'Tentar novamente', onPress: retry }]);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_alert_without_recovery(CONFIG)
    assert result["passed"] is True


# ── UX 4: no-roach-motel ─────────────────────────────────────────────────────


def test_purchase_without_cancel_path_warns(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/premium/subscribe.service.ts",
        "await Purchases.purchasePackage(pkg);\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_roach_motel(CONFIG)
    assert result["violations_count"] == 1
    assert result["blocked"] is False


def test_purchase_with_cancel_path_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/premium/subscribe.service.ts",
        "await Purchases.purchasePackage(pkg);\n",
    )
    _write(
        tmp_path,
        "src/settings/subscription.service.ts",
        "export async function cancelSubscription() {}\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_no_roach_motel(CONFIG)
    assert result["passed"] is True


# ── UX 5: form-field-without-label ───────────────────────────────────────────


def test_input_without_label_blocks_in_core(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/screens/LoginScreen.tsx",
        "<TextInput value={email} onChangeText={setEmail} />\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_form_field_without_label(CONFIG)
    assert result["violations_count"] == 1
    assert result["blocked"] is True


def test_input_with_placeholder_passes(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "src/screens/LoginScreen.tsx",
        "<TextInput value={email} placeholder=\"E-mail\" onChangeText={setEmail} />\n",
    )
    monkeypatch.chdir(tmp_path)
    result = check_form_field_without_label(CONFIG)
    assert result["passed"] is True


# ── Contrato de saída (formato runner.py) ────────────────────────────────────


def test_result_contract_shape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for check in (
        check_no_hardcoded_secrets,
        check_no_sql_injection,
        check_no_asyncstorage_tokens,
        check_no_client_only_auth,
        check_user_id_in_tables,
        check_no_hardcoded_strings,
        check_no_confirmshaming,
        check_no_alert_without_recovery,
        check_no_roach_motel,
        check_form_field_without_label,
    ):
        result = check(CONFIG)
        for key in ("check", "label", "description", "passed", "blocked", "violations"):
            assert key in result, f"{check.__name__} sem chave '{key}'"
        # Sem src/ → baseline greenfield: 0 violações, passed
        assert result["passed"] is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
