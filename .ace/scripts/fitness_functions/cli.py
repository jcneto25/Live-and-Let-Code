#!/usr/bin/env python3
"""CLI das fitness functions."""

import argparse
import json
import sys

from .config import load_arch_config
from .runner import format_human, run_checks


def main():
    parser = argparse.ArgumentParser(
        description="Fitness Functions — verificacao arquitetural automatizada"
    )
    # Architecture checks
    parser.add_argument("--all", action="store_true", help="Executa todos os checks")
    parser.add_argument("--check-deps", action="store_true", help="Dependency Rule")
    parser.add_argument(
        "--check-circular", action="store_true", help="Dependencias circulares"
    )
    parser.add_argument(
        "--check-interfaces", action="store_true", help="Cobertura de interfaces"
    )
    parser.add_argument(
        "--check-domain", action="store_true", help="Isolamento do dominio"
    )
    parser.add_argument(
        "--check-usecase", action="store_true", help="Tamanho dos use cases"
    )
    parser.add_argument(
        "--check-coverage", action="store_true", help="Cobertura por modulo"
    )
    # Clean Code checks
    parser.add_argument(
        "--check-functions",
        action="store_true",
        help="Clean Code: Functions (max lines, params, generic names)",
    )
    parser.add_argument(
        "--check-naming", action="store_true", help="Clean Code: Naming (generic names)"
    )
    parser.add_argument(
        "--check-classes",
        action="store_true",
        help="Clean Code: Classes (max lines, deps, DIP)",
    )
    parser.add_argument(
        "--check-errors",
        action="store_true",
        help="Clean Code: Errors (empty exceptions, empty catch)",
    )
    parser.add_argument(
        "--check-smells",
        action="store_true",
        help="Clean Code: Smells (magic numbers, dead code, noise comments, const)",
    )
    parser.add_argument(
        "--check-readmodels",
        action="store_true",
        help="Clean Code: ReadModels & Type Safety",
    )
    # Deep Clean checks (Ação 4 — Harness Preventivo LLC)
    parser.add_argument(
        "--check-deep-clean",
        action="store_true",
        help="Deep Clean: CQS, null, data clumps, flags, primitives, validation, pass-through",
    )
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument(
        "--strict", action="store_true", help="Exit code 1 se violacao ou bloqueio"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Detalhes e sugestoes de correcao"
    )
    args = parser.parse_args()

    requested = []
    if args.all:
        requested = ["all"]
    # Architecture
    if args.check_deps:
        requested.append("dependency_rule")
    if args.check_circular:
        requested.append("circular_deps")
    if args.check_interfaces:
        requested.append("interface_coverage")
    if args.check_domain:
        requested.append("domain_isolation")
    if args.check_usecase:
        requested.append("use_case_size")
    if args.check_coverage:
        requested.append("module_coverage")
    # Clean Code
    if args.check_functions:
        requested.extend(
            ["function_max_lines", "function_max_params", "no_generic_names"]
        )
    if args.check_naming:
        requested.append("no_generic_names")
    if args.check_classes:
        requested.extend(["class_max_lines", "class_max_deps", "dip_violation"])
    if args.check_errors:
        requested.extend(["no_empty_exceptions", "no_empty_catch"])
    if args.check_smells:
        requested.extend(
            ["no_magic_numbers", "no_dead_code", "no_noise_comments", "prefer_const"]
        )
    if args.check_readmodels:
        requested.extend(
            [
                "readmodel_exists",
                "repo_returns_readmodel",
                "no_any_in_public",
                "no_as_any",
            ]
        )
    # Deep Clean
    if args.check_deep_clean:
        requested.extend(
            [
                "no_cqs_violation",
                "no_null_return",
                "no_data_clump",
                "no_flag_arguments",
                "no_primitive_obsession",
                "max_function_lines_deep",
                "no_missing_validation",
                "no_pass_through",
            ]
        )

    if not requested:
        parser.print_help()
        sys.exit(0)

    config = load_arch_config()
    results = run_checks(requested, config, verbose=args.verbose)

    output = {
        "config": {
            "core_modules": config.get("core_modules", []),
        },
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results.values() if r.get("passed")),
            "blocked": any(r.get("blocked") for r in results.values()),
            "warnings": sum(
                1
                for r in results.values()
                if not r.get("passed")
                and not r.get("blocked")
                and r.get("passed") is not None
            ),
        },
    }

    if args.json:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        format_human(results, verbose=args.verbose)

    has_blocks = output["summary"]["blocked"]
    has_strict_fail = args.strict and (has_blocks or output["summary"]["warnings"] > 0)

    sys.exit(1 if has_strict_fail or has_blocks else 0)
