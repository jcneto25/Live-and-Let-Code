#!/usr/bin/env python3
"""Configuração e modo de severidade das fitness functions."""

import yaml
from pathlib import Path

ARCH_CONFIG_PATH = Path(".ace/arch-config.yaml")
SRC_DIR = Path("src")

DEFAULT_ARCH_CONFIG = {
    "version": "1.0",
    "core_modules": [],
    "checks": {
        "dependency_rule": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "circular_deps": {
            "enabled": True,
            "mode": "block",
        },
        "interface_coverage": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "threshold": 100,
        },
        "domain_isolation": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "use_case_size": {
            "enabled": True,
            "mode": "warn",
            "max_methods": 8,
        },
        "module_coverage": {
            "enabled": True,
            "mode": "warn",
            "threshold": 60,
        },
        # Clean Code Checks
        "function_max_lines": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "max_lines": 20,
        },
        "function_max_params": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "max_params": 3,
        },
        "no_generic_names": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "forbidden": [
                "data",
                "dto",
                "result",
                "info",
                "obj",
                "item",
                "entity",
                "model",
                "temp",
                "tmp",
                "value",
            ],
        },
        "class_max_lines": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "max_lines": 100,
        },
        "class_max_deps": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
            "max_deps": 5,
        },
        "dip_violation": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "no_empty_exceptions": {
            "enabled": True,
            "mode": "block",
        },
        "no_empty_catch": {
            "enabled": True,
            "mode": "block",
        },
        "no_magic_numbers": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "no_dead_code": {
            "enabled": True,
            "mode": "block",
        },
        "no_noise_comments": {
            "enabled": True,
            "mode": "warn",
        },
        "prefer_const": {
            "enabled": True,
            "mode": "warn",
        },
        "readmodel_exists": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "repo_returns_readmodel": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "no_any_in_public": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
        "no_as_any": {
            "enabled": True,
            "mode": "hybrid",
            "block_for": "core_modules",
        },
    },
}


def load_arch_config() -> dict:
    if ARCH_CONFIG_PATH.exists():
        try:
            import yaml

            with open(ARCH_CONFIG_PATH) as f:
                return yaml.safe_load(f) or DEFAULT_ARCH_CONFIG
        except Exception:
            return dict(DEFAULT_ARCH_CONFIG)
    return dict(DEFAULT_ARCH_CONFIG)


def is_core_module(module_name: str, config: dict) -> bool:
    return module_name in config.get("core_modules", [])


def check_mode(check_name: str, module_name: str, config: dict) -> str:
    check = config.get("checks", {}).get(check_name, {})
    mode = check.get("mode", "warn")
    if mode == "hybrid":
        block_for = check.get("block_for", "core_modules")
        if block_for == "core_modules" and is_core_module(module_name, config):
            return "block"
        return "warn"
    return mode


def severity_label(mode: str) -> str:
    return "🔴" if mode == "block" else "🟡" if mode == "warn" else "🟢"
