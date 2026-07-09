#!/usr/bin/env bash
# Rerunnable record of the LLC workflow/gate audit. Run on a clean checkout.
# Each P1–P5 task appends its commands here with `>> "$0"` or by editing.
set -u
echo "[audit-recipe] $(date -u +%FT%TZ) start"
