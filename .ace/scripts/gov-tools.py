#!/usr/bin/env python3
"""
Ferramentas CLI para o ciclo de vida GOV (Governance Artifact).

Comandos:
  list             Lista GOVs por status
  impact           Mostra GOVs relacionados a arquivos
  check-recurrence Varre sessões ACE em busca de reincidência

Uso:
    python .ace/scripts/gov-tools.py list
    python .ace/scripts/gov-tools.py list --status open
    python .ace/scripts/gov-tools.py list --status addressed --json
    python .ace/scripts/gov-tools.py impact --files "src/auth"
    python .ace/scripts/gov-tools.py impact --files "src/auth,src/users"
    python .ace/scripts/gov-tools.py check-recurrence
    python .ace/scripts/gov-tools.py check-recurrence --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

GOV_DIR = Path("docs/governance")
SESSIONS_DIR = Path(".ace/sessions")


# ── Parsing utilities ──

def parse_gov_field(text: str, field: str) -> str | None:
    # Tenta inline **Field**: value
    m = re.search(rf"\*\*{re.escape(field)}\*\*:\s*(.+)", text)
    if m:
        return m.group(1).strip()
    # Tenta ## Field header + conteúdo na linha seguinte
    m = re.search(rf"^##\s*{re.escape(field)}\s*$(.+?)(?=^##|\Z)", text, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1).strip().split("\n")[0].strip()
    return None


def load_all_govs() -> list[dict]:
    if not GOV_DIR.exists():
        return []
    govs = []
    for f in sorted(GOV_DIR.glob("GOV-*.md")):
        if f.name == "GOV-TEMPLATE.md":
            continue
        text = f.read_text(encoding="utf-8")
        govs.append({
            "file": f.name,
            "path": str(f),
            "status": (parse_gov_field(text, "Status") or "").lower(),
            "abertura": parse_gov_field(text, "Data de abertura") or "",
            "step_origem": parse_gov_field(text, "Step de origem") or "",
            "prp": parse_gov_field(text, "PRP relacionado") or "",
            "sintoma": parse_gov_field(text, "Sintoma") or "",
            "classe": parse_gov_field(text, "Classe de Falha") or "",
            "impacto": parse_gov_field(text, "Impacto") or "",
            "area": parse_gov_field(text, "Área Afetada") or "",
        })
    return govs


def load_sessions() -> list[dict]:
    if not SESSIONS_DIR.exists():
        return []
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        blockers = re.findall(r'<blocker[^>]*>(.*?)</blocker>', text, re.DOTALL)
        sessions.append({
            "file": f.name,
            "path": str(f),
            "blockers": [b.strip() for b in blockers if b.strip()],
        })
    return sessions


# ── Command: list ──

def cmd_list(args: argparse.Namespace):
    govs = load_all_govs()
    status_filter = args.status.lower() if args.status else None

    filtered = [g for g in govs if not status_filter or g["status"] == status_filter]
    filtered.sort(key=lambda g: g["file"])

    if args.json:
        print(json.dumps(filtered, indent=2, ensure_ascii=False))
        return

    if not filtered:
        print(f"Nenhum GOV encontrado{' com status ' + args.status if args.status else ''}.")
        return

    header = f"{'GOV':<20} {'Status':<12} {'Abertura':<12} {'Impacto':<10} {'Classe'}"
    print(f"\n{header}")
    print("-" * len(header))
    for g in filtered:
        print(f"{g['file']:<20} {g['status']:<12} {g['abertura']:<12} {g['impacto']:<10} {g['classe']}")
    print(f"\nTotal: {len(filtered)} GOVs")


# ── Command: impact ──

def cmd_impact(args: argparse.Namespace):
    govs = load_all_govs()
    target_files = [f.strip() for f in args.files.split(",") if f.strip()]

    affected = []
    for g in govs:
        area = g["area"].lower()
        for tf in target_files:
            if tf.lower() in area:
                affected.append(g)
                break

    if args.json:
        print(json.dumps(affected, indent=2, ensure_ascii=False))
        return

    if not affected:
        print(f"Nenhum GOV encontrado para os arquivos: {', '.join(target_files)}")
        return

    header = f"{'GOV':<20} {'Status':<12} {'Área Afetada':<25} {'Sintoma'}"
    print(f"\n{header}")
    print("-" * len(header))
    for g in affected:
        sintoma_short = g["sintoma"][:50] + "..." if len(g["sintoma"]) > 50 else g["sintoma"]
        print(f"{g['file']:<20} {g['status']:<12} {g['area']:<25} {sintoma_short}")
    print(f"\nTotal: {len(affected)} GOVs relacionados")


# ── Command: close ──

def cmd_close(args: argparse.Namespace):
    """Transição addressed → closed (R5). Exige 3 PRPs sem reincidência.

    Humano decide (gate 11.4); este comando apenas aplica a transição
    quando os critérios estão satisfeitos. Sem --confirm, é dry-run.
    """
    target = GOV_DIR / args.gov_file
    if not target.exists():
        print(f"❌ GOV não encontrado: {args.gov_file}", file=sys.stderr)
        return 1

    text = target.read_text(encoding="utf-8")
    status = (parse_gov_field(text, "Status") or "").lower()

    if status == "closed":
        print(f"❌ {args.gov_file} já está closed.", file=sys.stderr)
        return 1
    if status != "addressed":
        print(f"❌ Transição exige status 'addressed' (atual: '{status}').", file=sys.stderr)
        return 1

    recurrence = parse_gov_field(text, "Status da Reincidência") or ""
    import re as _re
    m = _re.search(r"(\d+)\s*/\s*3", recurrence)
    count = int(m.group(1)) if m else 0
    if count < 3:
        print(f"❌ Reincidência: {recurrence or 'não registrado'} — exige 3/3 PRPs sem reincidência.", file=sys.stderr)
        return 1

    if not args.confirm:
        print(f"🔍 dry-run — {args.gov_file} elegível para closed (3/3 PRPs sem reincidência).")
        print("   Reexecute com --confirm para aplicar.")
        return 0

    from datetime import date
    today = date.today().isoformat()
    new_text = text.replace("**Status**: addressed", "**Status**: closed")
    # Insere Data de fechamento após Data de instalação (ou de Status, se não houver)
    if "**Data de fechamento**" not in new_text:
        anchor = "**Data de instalação**"
        if anchor in new_text:
            lines = new_text.split("\n")
            out = []
            for ln in lines:
                out.append(ln)
                if ln.startswith(anchor):
                    out.append(f"**Data de fechamento**: {today}")
            new_text = "\n".join(out)
        else:
            new_text = new_text.replace(
                f"**Status**: closed",
                f"**Status**: closed\n**Data de fechamento**: {today}"
            )
    target.write_text(new_text, encoding="utf-8")
    print(f"✅ {args.gov_file} transicionado: addressed → closed em {today}")
    return 0


# ── Command: check-recurrence ──

def cmd_check_recurrence(args: argparse.Namespace):
    govs = load_all_govs()
    addressed_closed = [g for g in govs if g["status"] in ("addressed", "closed")]
    sessions = load_sessions()

    findings = []
    for g in addressed_closed:
        area_parts = [p.strip().lower() for p in g["area"].split(",") if p.strip()]
        for s in sessions:
            for blocker in s["blockers"]:
                blocker_lower = blocker.lower()
                # Match se blocker menciona área afetada do GOV
                for ap in area_parts:
                    if ap in blocker_lower:
                        findings.append({
                            "gov": g["file"],
                            "gov_status": g["status"],
                            "session": s["file"],
                            "blocker": blocker[:100] + "..." if len(blocker) > 100 else blocker,
                            "matched_area": ap,
                        })
                        break

    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
        return

    if not findings:
        print("Nenhuma reincidência potencial encontrada nas sessões ACE.")
        return

    print(f"\n⚠️  Possíveis reincidências detectadas ({len(findings)}):\n")
    header = f"{'GOV':<20} {'Status':<10} {'Sessão':<22} {'Blocker'}"
    print(header)
    print("-" * len(header))
    for f_item in findings:
        print(f"{f_item['gov']:<20} {f_item['gov_status']:<10} {f_item['session']:<22} {f_item['blocker']}")
    print()


# ── Main CLI ──

def main():
    parser = argparse.ArgumentParser(description="GOV Lifecycle Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = subparsers.add_parser("list", help="Lista GOVs por status")
    p_list.add_argument("--status", type=str, default=None,
                        help="Filtrar por status (open, addressed, closed)")
    p_list.add_argument("--json", action="store_true", help="Output JSON")

    # impact
    p_impact = subparsers.add_parser("impact", help="Mostra GOVs relacionados a arquivos")
    p_impact.add_argument("--files", type=str, required=True,
                          help="Arquivos alvo (separados por vírgula)")
    p_impact.add_argument("--json", action="store_true", help="Output JSON")

    # check-recurrence
    p_check = subparsers.add_parser("check-recurrence",
                                    help="Varre sessões ACE por reincidência")
    p_check.add_argument("--json", action="store_true", help="Output JSON")

    # close (R5)
    p_close = subparsers.add_parser("close",
                                    help="Transição addressed → closed (exige 3 PRPs sem reincidência)")
    p_close.add_argument("gov_file", help="Nome do arquivo GOV (ex.: GOV-001-slug.md)")
    p_close.add_argument("--confirm", action="store_true",
                         help="Aplica a transição (sem isso, é dry-run)")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "impact":
        cmd_impact(args)
    elif args.command == "check-recurrence":
        cmd_check_recurrence(args)
    elif args.command == "close":
        return cmd_close(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
