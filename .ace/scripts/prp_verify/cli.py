#!/usr/bin/env python3
"""CLI do prp_verify (Step 11.2 do LLC)."""

import argparse
import json
import sys

from .constants import CRITICAL
from .models import VerifyResult
from .verify import discover_prps, resolve_prp_path, verify_prp


def main():
    parser = argparse.ArgumentParser(
        description="Verificação mecânica de aceite de PRP (Step 11.2 do LLC)"
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--prp", help="ID do PRP (ex: PRP-001) ou caminho")
    g.add_argument("--all", action="store_true", help="Verifica todos os PRP-*.md")
    parser.add_argument(
        "--strict", action="store_true", help="Exit 2 se houver CRITICAL"
    )
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    args = parser.parse_args()

    if args.all:
        prps = discover_prps()
        if not prps:
            msg = "Nenhum PRP encontrado em docs/prps/ (apenas PRP_TEMPLATE.md)."
            if args.json:
                print(
                    json.dumps(
                        {"prps": [], "critical": 0, "warn": 0}, ensure_ascii=False
                    )
                )
            else:
                print(f"ℹ️  {msg}")
            return 0
    else:
        path = resolve_prp_path(args.prp)
        if path is None:
            print(f"❌ PRP não encontrado: {args.prp}", file=sys.stderr)
            return 1
        prps = [path]

    results = [verify_prp(p) for p in prps]
    total_critical = sum(r.critical for r in results)
    total_warn = sum(r.warns for r in results)

    if args.json:
        print(
            json.dumps(
                {
                    "prps": [r.to_dict() for r in results],
                    "critical": total_critical,
                    "warn": total_warn,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        for r in results:
            print(f"\n{'=' * 60}")
            print(f"📋 {r.prp} — {r.critical} CRITICAL, {r.warns} WARN")
            print(f"{'=' * 60}")
            if not r.findings:
                print("✅ Nenhuma pendência encontrada.")
            for f in r.findings:
                glyph = "⛔" if f.severity == CRITICAL else "⚠️ "
                rf = f" [{f.rf}]" if f.rf else ""
                fl = f" ({f.file})" if f.file else ""
                print(f"  {glyph} {f.severity} {f.code}{rf}{fl}")
                print(f"      {f.message}")
        print(f"\n{'=' * 60}")
        print(
            f"Total: {total_critical} CRITICAL, {total_warn} WARN "
            f"({len(results)} PRP(s))"
        )
        print(f"{'=' * 60}")

    if args.strict and total_critical > 0:
        return 2
    return 0
