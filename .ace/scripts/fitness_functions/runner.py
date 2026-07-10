#!/usr/bin/env python3
"""Orquestração e formatação de saída das fitness functions."""

import sys

from .checks_arch import (
    check_circular_deps,
    check_dependency_rule,
    check_domain_isolation,
    check_interface_coverage,
    check_module_coverage,
    check_use_case_size,
)
from .checks_clean import (
    check_class_max_deps,
    check_class_max_lines,
    check_dip_violation,
    check_function_max_lines,
    check_function_max_params,
    check_no_any_in_public,
    check_no_as_any,
    check_no_dead_code,
    check_no_empty_catch,
    check_no_empty_exceptions,
    check_no_generic_names,
    check_no_magic_numbers,
    check_no_noise_comments,
    check_prefer_const,
    check_readmodel_exists,
    check_repo_returns_readmodel,
)
from .config import severity_label


def run_checks(requested: list[str], config: dict, verbose: bool = False) -> dict:
    all_checks = {
        # Architecture checks
        "dependency_rule": check_dependency_rule,
        "circular_deps": check_circular_deps,
        "interface_coverage": check_interface_coverage,
        "domain_isolation": check_domain_isolation,
        "use_case_size": check_use_case_size,
        "module_coverage": check_module_coverage,
        # Clean Code checks
        "function_max_lines": check_function_max_lines,
        "function_max_params": check_function_max_params,
        "no_generic_names": check_no_generic_names,
        "class_max_lines": check_class_max_lines,
        "class_max_deps": check_class_max_deps,
        "dip_violation": check_dip_violation,
        "no_empty_exceptions": check_no_empty_exceptions,
        "no_empty_catch": check_no_empty_catch,
        "no_magic_numbers": check_no_magic_numbers,
        "no_dead_code": check_no_dead_code,
        "no_noise_comments": check_no_noise_comments,
        "prefer_const": check_prefer_const,
        "readmodel_exists": check_readmodel_exists,
        "repo_returns_readmodel": check_repo_returns_readmodel,
        "no_any_in_public": check_no_any_in_public,
        "no_as_any": check_no_as_any,
    }

    if "all" in requested:
        requested = list(all_checks.keys())

    results = {}
    for name in requested:
        if name in all_checks:
            if verbose:
                print(f"  Running {name}...", file=sys.stderr)
            results[name] = all_checks[name](config, verbose=verbose)

    return results


def format_human(results: dict, verbose: bool = False):
    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r.get("passed"))
    blocked = any(r.get("blocked") for r in results.values())
    failed_but_not_blocked = sum(
        1 for r in results.values() if not r.get("passed") and not r.get("blocked")
    )

    for name, result in results.items():
        status = "✅" if result.get("passed") else "🔴"
        if result.get("passed") is None:
            status = "⚠️"

        print(f"\n  {status} {result['label']}")
        print(f"     {result['description']}")

        if result.get("passed") is None and result.get("error"):
            print(f"     ⚠️  {result['error']}")
            continue

        if result.get("coverage_pct") is not None:
            print(
                f"     Cobertura: {result['coverage_pct']}% ({result.get('covered', '?')}/{result.get('total_services', '?')})"
            )
        if result.get("modules_analyzed") is not None:
            print(f"     Modulos analisados: {result['modules_analyzed']}")

        for v in result.get("violations", []):
            sev = severity_label(v.get("severity", "warn"))
            print(f"     {sev} {v.get('file', v.get('module', v.get('detail', '')))}")
            print(f"        {v['detail']}")
            if verbose and v.get("fix"):
                print(f"        💡 {v['fix']}")

        if not result.get("violations") and result.get("passed"):
            print(f"     ✅ Sem violacoes")

    print(f"\n{'=' * 50}")
    print(f"  Resultado: {passed_checks}/{total_checks} checks passaram")
    if blocked:
        print(f"  🔴 HA BLOQUEIOS — corrija antes do merge")
    elif failed_but_not_blocked > 0:
        print(f"  🟡 {failed_but_not_blocked} alerta(s) — registre em divida tecnica")
    else:
        print(f"  🟢 Tudo OK")
    print(f"{'=' * 50}")
