#!/usr/bin/env python3
"""Constantes compartilhadas do prp_verify."""

from pathlib import Path

PRP_DIR = Path("docs/prps")
ARCHITECTURE_FILE = Path("docs/architecture/ARCHITECTURE.md")

CRITICAL = "CRITICAL"
WARN = "WARN"

# Raízes onde procurar arquivos declarados (bounded — nunca node_modules/.ace).
SEARCH_ROOTS = ["apps", "src", "packages", "."]
EXCLUDE_PARTS = {
    "node_modules",
    ".ace",
    "dist",
    ".git",
    "build",
    ".next",
    "coverage",
    ".turbo",
    "target",
}
