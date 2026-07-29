#!/usr/bin/env python3
"""Checks de UX (strings hardcoded, confirmshaming, alerts, roach motel, labels).

Estes 5 checks implementam a Fitness Function de UX do Step 7a
(UX Heuristics & Personas §5.5), executados via `fitness-functions.py --check-ux`.

Ref: Harness Preventivo LLC §2.3 — Ação 3 (Skill llc-step-7a-ux-heuristics).
"""

import re

from .config import SRC_DIR, check_mode
from .helpers import find_ts_files, module_name_from_path, read_file_safe

_EXCLUDED_PARTS = {
    "test", "tests", "__tests__", "spec", "specs",
    "mock", "mocks", "example", "examples", "fixtures",
}


def _is_excluded(path) -> bool:
    if any(part.lower() in _EXCLUDED_PARTS for part in path.parts):
        return True
    name = path.name.lower()
    return ".test." in name or ".spec." in name


# ── 1. no-hardcoded-strings ──────────────────────────────────────────────────

# Texto visível entre tags JSX: inicial maiúscula + 3+ letras (provável string de UI)
_HARDCODED_JSX_TEXT = re.compile(r">\s*[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{3,}[^<{]*<")


def check_no_hardcoded_strings(config: dict, verbose: bool = False) -> dict:
    """Detecta strings visíveis hardcoded em JSX — toda string de UI deve usar t('key')."""
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if ts_file.suffix != ".tsx" or _is_excluded(ts_file):
            continue
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        for i, line in enumerate(content.split("\n")):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if _HARDCODED_JSX_TEXT.search(line):
                mode = check_mode("no_hardcoded_strings", module, config)
                violations.append({
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"String visível hardcoded na linha {i + 1}: {stripped[:80]}",
                    "fix": "Usar t('chave.i18n') — nenhuma string de UI hardcoded",
                    "line": i + 1,
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_hardcoded_strings",
        "label": "No Hardcoded Strings",
        "description": "Strings visíveis devem usar t('key') para i18n",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 2. no-confirmshaming ─────────────────────────────────────────────────────

_CONFIRMSHAMING = re.compile(
    r"(?i)(?:prefiro|n[aã]o\s+quero|n[aã]o\s+me\s+importo|sou|estou)\s+"
    r"(?:pagar|perder|continuar|ficar|ser|estar)"
)


def check_no_confirmshaming(config: dict, verbose: bool = False) -> dict:
    """Detecta textos depreciativos em opções de recusa (dark pattern Confirmshaming)."""
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if _is_excluded(ts_file):
            continue
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        for i, line in enumerate(content.split("\n")):
            if _CONFIRMSHAMING.search(line):
                mode = check_mode("no_confirmshaming", module, config)
                violations.append({
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"Possível confirmshaming na linha {i + 1}: {line.strip()[:80]}",
                    "fix": "Opção de recusa neutra: 'Agora não' / 'Continuar sem premium'",
                    "line": i + 1,
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_confirmshaming",
        "label": "No Confirmshaming",
        "description": "Opções de recusa devem ser neutras — sem texto depreciativo",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 3. no-alert-without-recovery ─────────────────────────────────────────────

# Alert.alert('Titulo', 'Mensagem') sem 3º argumento (array de botões/ações)
_ALERT_NO_BUTTONS = re.compile(
    r"Alert\.alert\s*\(\s*['\"`][^'\"`]*['\"`]\s*,\s*['\"`][^'\"`]*['\"`]\s*\)"
)


def check_no_alert_without_recovery(config: dict, verbose: bool = False) -> dict:
    """Detecta Alert.alert de erro sem botões de ação (sem caminho de recuperação)."""
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if _is_excluded(ts_file):
            continue
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        for i, line in enumerate(content.split("\n")):
            if _ALERT_NO_BUTTONS.search(line):
                mode = check_mode("no_alert_without_recovery", module, config)
                violations.append({
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"Alert.alert sem ação de recuperação na linha {i + 1}",
                    "fix": (
                        "Adicionar botões acionáveis: "
                        "Alert.alert(t, m, [{ text: 'Tentar novamente', onPress: retry }])"
                    ),
                    "line": i + 1,
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_alert_without_recovery",
        "label": "No Alert Without Recovery",
        "description": "Alerts de erro devem oferecer pelo menos uma ação de recuperação",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 4. no-roach-motel ────────────────────────────────────────────────────────

_PURCHASE_FLOW = re.compile(
    r"(?i)(purchasePackage|purchaseProduct|requestSubscription|"
    r"\.subscribe\s*\(|startCheckout|createCheckoutSession)"
)
_CANCEL_FLOW = re.compile(
    r"(?i)(cancelSubscription|unsubscribe|manageSubscription|"
    r"cancel[_-]?plan|showManageSubscriptions|deleteAccount)"
)


def check_no_roach_motel(config: dict, verbose: bool = False) -> dict:
    """Heurística Roach Motel: existe fluxo de assinatura/compra sem fluxo de cancelamento.

    Se algum arquivo inicia compra/assinatura, deve existir em src/ pelo menos
    um caminho de cancelamento/gestão da assinatura.
    """
    purchase_files = []
    has_cancel_path = False

    for ts_file in find_ts_files(SRC_DIR):
        if _is_excluded(ts_file):
            continue
        content = read_file_safe(ts_file)
        if _PURCHASE_FLOW.search(content):
            purchase_files.append(ts_file)
        if _CANCEL_FLOW.search(content):
            has_cancel_path = True

    violations = []
    if purchase_files and not has_cancel_path:
        for ts_file in purchase_files:
            module = module_name_from_path(ts_file) or ""
            mode = check_mode("no_roach_motel", module, config)
            violations.append({
                "file": str(ts_file),
                "module": module,
                "severity": mode,
                "detail": (
                    "Fluxo de assinatura/compra sem nenhum fluxo de "
                    "cancelamento/gestão em src/ (padrão Roach Motel)"
                ),
                "fix": "Implementar cancelSubscription/manageSubscription acessível ao usuário",
            })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "no_roach_motel",
        "label": "No Roach Motel",
        "description": "Sair de uma assinatura deve ser tão fácil quanto entrar",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }


# ── 5. form-field-without-label ──────────────────────────────────────────────

_INPUT_TAG = re.compile(r"<(TextInput|Input|input)\b([^>]*)/?>")
_LABEL_ATTRS = re.compile(r"(?i)(label|aria-label|accessibilityLabel|placeholder)\s*=")


def check_form_field_without_label(config: dict, verbose: bool = False) -> dict:
    """Detecta inputs sem label/placeholder associado — todo campo precisa de rótulo."""
    violations = []

    for ts_file in find_ts_files(SRC_DIR):
        if ts_file.suffix != ".tsx" or _is_excluded(ts_file):
            continue
        module = module_name_from_path(ts_file)
        if module is None:
            continue

        content = read_file_safe(ts_file)
        for i, line in enumerate(content.split("\n")):
            m = _INPUT_TAG.search(line)
            if m and not _LABEL_ATTRS.search(m.group(2)):
                mode = check_mode("form_field_without_label", module, config)
                violations.append({
                    "file": str(ts_file),
                    "module": module,
                    "severity": mode,
                    "detail": f"<{m.group(1)}> sem label/placeholder na linha {i + 1}",
                    "fix": "Associar label visível (FormField) ou placeholder/accessibilityLabel",
                    "line": i + 1,
                })

    passed = len(violations) == 0
    blocked = any(v["severity"] == "block" for v in violations)
    return {
        "check": "form_field_without_label",
        "label": "Form Field Without Label",
        "description": "Todo input deve ter label visível ou placeholder/accessibilityLabel",
        "passed": passed,
        "blocked": blocked,
        "violations_count": len(violations),
        "violations": violations,
    }
