# P3 — Conformance Drift Findings

Canonical model = llc_steps.py. Drift = mismatch vs guide / skills / gates.json.

## Step→Gate resolution

Dumped canonical model (Step 1):

```bash
python3 .ace/scripts/llc_steps.py > docs/audit/raw/llc_steps_registry.json
```

Resolution table (Step 2) — for each step in the registry, resolve `gate`
against `gates.json` programmatically and record whether the gate exists and
whether `gates[gate]["step"]` matches the canonical step number (within `EPS`):

```bash
python3 - <<'PY'
import json, sys
sys.path.insert(0, ".ace/scripts")
import llc_steps
gates = json.load(open(".ace/config/gates.json"))["gates"]
print(f"{'step':>5} {'num':>5} {'gate':>10} {'in_gj':>6} {'gj_step':>8} {'match':>6} {'label':<24}")
for sid, spec in sorted(llc_steps.REGISTRY.items(), key=lambda kv: kv[1].number):
    if spec.gate is None:
        continue
    in_gj = spec.gate in gates
    gj_step = gates.get(spec.gate, {}).get("step")
    match = in_gj and abs(gj_step - spec.number) < llc_steps.EPS
    label = gates.get(spec.gate, {}).get("label", "<MISSING>")[:24]
    print(f"{sid:>5} {spec.number:>5} {spec.gate:>10} {str(in_gj):>6} {str(gj_step):>8} {str(match):>6} {label:<24}")
PY
```

Output at baseline `a519d0f` (BASE commit `f0150fe`):

```
 step   num       gate  in_gj  gj_step  match label
  0.5   0.5          1   True      0.5   True Visao Estrategica + Modu
    1   1.0          2   True        1   True 7 Especificacoes
    2   2.0          3   True        2   True PRDs
    3   3.0          4   True        3   True PRPs
    4   4.0          5   True        4   True Planejamento
    5   5.0          6   True        5   True Arquitetura
    6   6.0          7   True        6   True Tarefas
    7   7.0          8   True        7   True Design System
    8   8.0          9   True        8   True Setup + Mock
    9   9.0         10   True        9   True Testing Docs
   10  10.0         11   True       10   True Project Docs
 10.5  10.5       11.5   True     10.5   True User Guide
 10.6  10.6     11-SEC   True       11  False Security Audit
 10.7  10.7    12-NULL   True       12  False Null Safety
 10.8  10.8       10.8   True     10.8   True Test Coverage Gate
 11.1  11.1   11-OWASP   True       11  False OWASP Hardening
 11.2  11.2  11-VERIFY   True     11.2   True PRP Verify
 11.3  11.3    11-ARCH   True     11.3   True Architecture Compliance
```

Summary: 18 steps with gates; **15 match**, **3 mismatch** (`match=False`).
All 18 gate keys exist (`in_gj=True`) — no missing keys, no collisions. The 3
mismatches are stale `step` *fields* (display/lookup values), not bad gate keys.

## Drift findings

- **D-01 (LOW, conformance-drift):** Three stale `step` fields in `gates.json`:
  `11-SEC` has `"step": 11` (should be 10.6), `12-NULL` has `"step": 12`
  (should be 10.7), `11-OWASP` has `"step": 11` (should be 11.1). The gate KEYS
  all resolve correctly from `llc_steps`; only the display/lookup `step` field
  is stale. → backlog/doc-only (LOW; not a P5 hotfix). Verified by the
  resolution table in Step 2.

- **D-02 (OUT OF SCOPE — pending in-flight work):** Steps 5a (Architecture
  Patterns), 5b (API Design), 5c (Clean Code) are NOT in the committed
  `REGISTRY` (normalize_step("5.1"/"5b"/"5c") raises `UnknownStepError`). The
  skills `llc-step-5b-api-design.md`, `llc-step-5c-clean-code.md`,
  `llc-step-api-design.md` exist on disk (untracked) but the pipeline wiring is
  the reverted in-flight work. Document and EXCLUDE from this baseline's scope.

- **NOTE:** The large gate-remap drift that motivated the original Task 9
  (missing gates 4/5, key collisions, 10 mis-pointed gates) DOES NOT EXIST at
  baseline `a519d0f` — gates 4/5 are present and keys align. Do NOT apply any
  gate remap or add gates 4/5.

## Disposition

- D-01 → backlog (LOW).
- D-02 → out of scope (pending in-flight work).
