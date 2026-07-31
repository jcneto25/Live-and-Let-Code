#!/usr/bin/env python3
"""
Calcula métricas de governança a partir dos GOVs em docs/governance/.

Métricas:
  - failure_to_control_lead_time: tempo médio (dias) entre abertura e instalação
  - structural_failure_recurrence_rate: % de GOVs que reabriram sobre total de closed

Uso:
    python .ace/scripts/governance-metrics.py
    python .ace/scripts/governance-metrics.py --json
    python .ace/scripts/governance-metrics.py --verbose
"""

import argparse
import json
import re
import sys
from datetime import datetime, date
from pathlib import Path
from statistics import mean

GOV_DIR = Path("docs/governance")
DATE_FMT = "%Y-%m-%d"


def parse_gov_field(text: str, field: str) -> str | None:
    """Extrai o valor de um campo — inline (**Campo**: valor) ou seção (## Campo)."""
    m = re.search(rf"\*\*{re.escape(field)}\*\*:\s*(.+)", text)
    if m:
        return m.group(1).strip()
    m = re.search(rf"^##\s*{re.escape(field)}\s*$(.+?)(?=^##|\Z)", text, re.MULTILINE | re.DOTALL)
    if m:
        return m.group(1).strip().split("\n")[0].strip()
    return None


def parse_date(raw: str) -> date | None:
    """Tenta fazer parse de uma data no formato YYYY-MM-DD."""
    try:
        return datetime.strptime(raw.strip(), DATE_FMT).date()
    except (ValueError, AttributeError):
        return None


def load_govs() -> list[dict]:
    """Carrega todos os GOVs de docs/governance/GOV-*.md."""
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
            "status": parse_gov_field(text, "Status"),
            "abertura": parse_date(parse_gov_field(text, "Data de abertura") or ""),
            "instalacao": parse_date(parse_gov_field(text, "Data de instalação") or ""),
            "fechamento": parse_date(parse_gov_field(text, "Data de fechamento") or ""),
            "classe": parse_gov_field(text, "Classe de Falha"),
            "impacto": parse_gov_field(text, "Impacto"),
            "decisao": parse_gov_field(text, "Decisão"),
            "area": parse_gov_field(text, "Área Afetada"),
        })
    return govs


def calc_lead_times(govs: list[dict]) -> list[float]:
    """Calcula lead time (dias) para cada GOV addressed/closed com data de instalação."""
    lead_times = []
    for g in govs:
        if g["status"] in ("addressed", "closed") and g["abertura"] and g["instalacao"]:
            delta = (g["instalacao"] - g["abertura"]).days
            if delta >= 0:
                lead_times.append(delta)
    return lead_times


def calc_recurrence_rate(govs: list[dict]) -> tuple[int, int, float | None]:
    """Calcula taxa de reincidência: % de GOVs closed que reabriram."""
    closed = [g for g in govs if g["status"] == "closed"]
    if not closed:
        return 0, 0, None
    reopened = 0
    for g in closed:
        text = Path(g["path"]).read_text(encoding="utf-8")
        status_field = parse_gov_field(text, "Status da Reincidência")
        # reopened if status field mentions recurrence or reabertura
        if status_field and ("reincid" in status_field.lower() or "reabert" in status_field.lower()):
            reopened += 1
    return reopened, len(closed), (reopened / len(closed)) * 100 if closed else None


def generate_report(govs: list[dict], verbose: bool = False) -> dict:
    lead_times = calc_lead_times(govs)
    reopened, total_closed, recurrence_rate = calc_recurrence_rate(govs)

    report = {
        "total_govs": len(govs),
        "by_status": {
            "open": len([g for g in govs if g["status"] == "open"]),
            "addressed": len([g for g in govs if g["status"] == "addressed"]),
            "closed": total_closed,
        },
        "failure_to_control_lead_time_days": round(mean(lead_times), 1) if lead_times else None,
        "failure_to_control_samples": len(lead_times),
        "structural_failure_recurrence_rate_pct": round(recurrence_rate, 1) if recurrence_rate is not None else None,
        "reopened_govs": reopened,
        "total_closed_govs": total_closed,
    }

    if verbose:
        report["lead_time_details"] = [
            {
                "file": g["file"],
                "abertura": str(g["abertura"]) if g["abertura"] else None,
                "instalacao": str(g["instalacao"]) if g["instalacao"] else None,
                "lead_time_days": (g["instalacao"] - g["abertura"]).days
                if g["abertura"] and g["instalacao"]
                else None,
            }
            for g in govs
            if g["status"] in ("addressed", "closed") and g["abertura"] and g["instalacao"]
        ]
        report["govs"] = [
            {
                "file": g["file"],
                "status": g["status"],
                "classe": g["classe"],
                "impacto": g["impacto"],
                "area": g["area"],
            }
            for g in govs
        ]

    return report


def main():
    parser = argparse.ArgumentParser(description="Calcula métricas de governança LLC")
    parser.add_argument("--json", action="store_true", help="Output em JSON")
    parser.add_argument("--verbose", action="store_true", help="Inclui detalhes por GOV")
    args = parser.parse_args()

    govs = load_govs()
    report = generate_report(govs, verbose=args.verbose)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*55}")
        print("  MÉTRICAS DE GOVERNANÇA")
        print(f"{'='*55}")
        print(f"  Total GOVs:              {report['total_govs']}")
        print(f"  ├─ open:                 {report['by_status']['open']}")
        print(f"  ├─ addressed:            {report['by_status']['addressed']}")
        print(f"  └─ closed:               {report['by_status']['closed']}")
        print()
        lead = report["failure_to_control_lead_time_days"]
        print(f"  failure_to_control_lead_time: {lead} dias" if lead is not None else "  failure_to_control_lead_time: N/A (sem GOVs addressed/closed com data de instalação)")
        print(f"  (amostras: {report['failure_to_control_samples']})" if report["failure_to_control_samples"] else "")
        print()
        rec = report["structural_failure_recurrence_rate_pct"]
        print(f"  structural_failure_recurrence_rate: {rec}%" if rec is not None else "  structural_failure_recurrence_rate: N/A (sem GOVs closed)")
        print(f"  (reabertos: {report['reopened_govs']} / {report['total_closed_govs']})" if report["total_closed_govs"] else "")
        print(f"{'='*55}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
