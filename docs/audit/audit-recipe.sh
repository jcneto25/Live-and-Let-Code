#!/usr/bin/env bash
# Rerunnable record of the LLC workflow/gate audit. Run on a clean checkout.
# Each P1–P5 task appends its commands here with `>> "$0"` or by editing.
set -u
echo "[audit-recipe] $(date -u +%FT%TZ) start"
python3 .ace/scripts/validate-tags.py --strict --json > docs/audit/raw/validate-tags.json 2>&1 || true
python3 .ace/scripts/consistency-check.py --json --strict > docs/audit/raw/consistency-check.json 2>&1 || true
python3 .ace/scripts/fitness-functions.py --all --json > docs/audit/raw/fitness-functions.json 2>&1 || true
python3 .ace/scripts/code-health.py --since "90 days ago" --fitness --json > docs/audit/raw/code-health.json 2>&1 || true
python3 .ace/scripts/prp_verify.py --all --json > docs/audit/raw/prp-verify-all.json 2>&1 || true
python3 .ace/scripts/dependency-graph-generator.py --prps docs/prps/PRP-001.md -o docs/audit/raw/dependency-graph.yaml 2>&1 || true
