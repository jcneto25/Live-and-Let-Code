#!/usr/bin/env python3
"""fitness-functions — verificação arquitetural automatizada (Ingeno ch16).

Pacote resultante do refactor clean-code (sub-projeto 2). Submódulos:
  - config:    arquivo de config (.ace/arch-config.yaml), DEFAULT_ARCH_CONFIG, modos
  - helpers:   find_ts_files, module_name_from_path, read_file_safe, contagem de linhas
  - checks_arch: checks arquiteturais (dependency/circular/interface/domain/usecase/coverage)
  - checks_clean: checks de Clean Code (funções/classes/erros/smells/type-safety)
  - runner:    run_checks (registry) + format_human
  - cli:       entrypoint de linha de comando

Este __init__ re-exporta a API completa para manter o runner
`fitness-functions.py` (subprocess, usado por code-health.py) funcionando.
"""

from .config import (
    ARCH_CONFIG_PATH,
    DEFAULT_ARCH_CONFIG,
    SRC_DIR,
    check_mode,
    is_core_module,
    load_arch_config,
    severity_label,
)
from .helpers import (
    count_effective_lines,
    extract_constructor_params,
    find_ts_files,
    module_name_from_path,
    read_file_safe,
)
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
from .runner import format_human, run_checks
from .cli import main

__all__ = [
    "ARCH_CONFIG_PATH",
    "DEFAULT_ARCH_CONFIG",
    "SRC_DIR",
    "check_mode",
    "is_core_module",
    "load_arch_config",
    "severity_label",
    "count_effective_lines",
    "extract_constructor_params",
    "find_ts_files",
    "module_name_from_path",
    "read_file_safe",
    "check_circular_deps",
    "check_dependency_rule",
    "check_domain_isolation",
    "check_interface_coverage",
    "check_module_coverage",
    "check_use_case_size",
    "check_class_max_deps",
    "check_class_max_lines",
    "check_dip_violation",
    "check_function_max_lines",
    "check_function_max_params",
    "check_no_any_in_public",
    "check_no_as_any",
    "check_no_dead_code",
    "check_no_empty_catch",
    "check_no_empty_exceptions",
    "check_no_generic_names",
    "check_no_magic_numbers",
    "check_no_noise_comments",
    "check_prefer_const",
    "check_readmodel_exists",
    "check_repo_returns_readmodel",
    "format_human",
    "run_checks",
    "main",
]
