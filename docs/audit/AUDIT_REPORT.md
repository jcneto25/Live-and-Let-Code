# LLC Workflow & Gate Logic Audit — Report

Status: in progress. Findings appended by P2 (enforcement) and P3 (conformance).
Severity key: CRITICAL / HIGH / MEDIUM / LOW. See DEFECT_BACKLOG.md for the prioritized list.

## P1 Hypotheses

Raw self-check tool output captured under `docs/audit/raw/`. Nothing here is a
finding yet — these are top-line counts to be confirmed in P2/P3.

- **validate-tags.json**: `valid=false`, 12 total errors / 0 fixable (sessions completed sem `<dependencies>`). TO CONFIRM in P2/P3.
- **consistency-check.json**: 5 PRPs analyzed, 9 stub services, 2 OK, 9 divergences (stub marked ✅ in TASKS.md). TO CONFIRM in P2/P3.
- **fitness-functions.json**: 22 checks total, 0 blocked, 1 not-passed (`module_coverage: passed=None`, 0 violations). TO CONFIRM in P2/P3.
- **code-health.json**: 227 commits / 90d; alerts: 1 critical (Moved Code % = 0.0%), 2 high (Copy/Paste vs Moved; Legacy Touch %). TO CONFIRM in P2/P3.
- **prp-verify-all.json**: `{"prps": [], "critical": 0, "warn": 0}` — no PRPs found/verified. TO CONFIRM in P2/P3.
- **dependency-graph.yaml**: ERROR — `PRP não encontrado: docs/prps/PRP-001.md` (input missing on baseline). TO CONFIRM in P2/P3.
