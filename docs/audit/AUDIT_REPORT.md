# LLC Workflow & Gate Logic Audit — Report

> Synthesis of P2 (enforcement, points #1–#15) and P3 (conformance drift,
> D-01/D-02) into a prioritized, decision-ready report. The companion
> `DEFECT_BACKLOG.md` holds one row per finding; `BEHAVIOR_BASELINE.md` is the
> refactor's must-not-break contract.

**Scope:** the 15 LLC enforcement teeth + the step/gate conformance model.
**Baseline:** `a519d0f` (P1 scratch reference for git/pre-commit/session teeth,
#1–#5/#13) and the committed state of branch `api-design-enforcement-docs`
(P2 wave/verify/fitness/skip teeth, #6–#12/#14/#15; P3 drift). The audit ran
against **committed** state only — no `.ace/scripts/*` source was modified by
the verification pass (the two A-01/A-02 hotfixes are the exception and are
documented in §4).
**Severity key:** CRITICAL / HIGH / MEDIUM / LOW. INFO = working-as-designed,
not a defect.

---

## 1. Executive summary

**Finding counts by severity:**

| Severity | Count | IDs |
|----------|-------|-----|
| CRITICAL | 2 | A-01, A-02 |
| HIGH     | 0 | — |
| MEDIUM   | 2 | E-13, E-12 |
| LOW      | 2 | E-11, D-01 |
| INFO (working-as-designed / out-of-scope) | 3 | D-02, ADV-03, ADV-15 |

**Status:**

- **Hotfixed-in-audit: 2** — the two CRITICAL gate-logic defects **A-01**
  (`_pre_wave_check` undefined → `NameError`) and **A-02**
  (`_post_wave_check` no-op → returns `None`), fixed under Task 7 / Task 8 with
  RED→GREEN TDD and committed (`607a1b8`, `e02a544`). Post-hotfix both functions
  return `bool` in all paths (verified: `_pre_wave_check` → `True`,
  `_post_wave_check` → `True` on a missing-script path).
- **Open: 4** — E-13 (gate_check fail-open), E-12 (smart-skip no guardrail),
  E-11 (test-coverage CLI gate is checklist-only), D-01 (3 stale `step` fields).
- **Escalated (need a policy decision before a hotfix): 2** — **E-12** (which
  steps are unskippable?) and **E-13** (is fail-open intentional, or should
  ambiguity require an explicit approve?). These cannot be fixed inline without
  a design call; see §5.
- **Out-of-scope: 1** — D-02 (steps 5a/5b/5c unwired; pending reverted in-flight
  work).
- **INFO / not defects: 2** — ADV-03 (#3 pre-commit impact+fitness is advisory
  by design), ADV-15 (#15 consistency-check is advisory by design).

**Headline:** the pipeline had **two CRITICAL defects that made the wave engine
non-functional** (pre-wave aborted with `NameError`; post-wave always reported
"blocked"). Both are now fixed. The remaining open items are MEDIUM policy gaps
(silent-bypass surfaces) and LOW doc/UX hazards — none block the wave engine,
but E-12 and E-13 together mean a **non-interactive or inattentive operator, or
a malformed `DELTA_REPORT.md`, can auto-approve-skip the PRP-acceptance (11.2)
and coverage (10.8) gates**, defeating the deterministic merge block (#4/#5).
Those need decisions, not just code.

---

## 2. Enforcement findings (#1–#15)

One line each: verdict + proof pointer into `p2-enforcement-log.md`.

| # | Point | Verdict | Proof |
|---|-------|---------|-------|
| #1 | pre-commit session coverage (code-without-session rejected) | **works** — `validate-tags.py --coverage` exits 1 on staged code with no covering session; `pre-commit.sh` then exits 1. Caveat: hook not auto-installed; bypassable with `--no-verify` (documented "não recomendado"). | P2 #1 |
| #2 | pre-commit tag/index integrity | **works** — `validate-tags.py --strict` exits 0 on a clean tree; `pre-commit.sh` shell checks increment `ERRORS` and exit 1 on defect. | P2 #2 |
| #3 | pre-commit impact+fitness advisory (non-blocking) | **works (as designed — advisory)** — both analyzers' output is discarded/downgraded; never touches `ERRORS`. INFO, not a defect (ADV-03). | P2 #3 |
| #4 | session_end CRITICAL merge block (prp_verify exit 2) | **not-exercisable on this baseline** (LLC repo has no PRPs; `prp_verify` exits 1, not 2) — **works-by-inspection**: exit-2 → `_maybe_block_on_prp_verify` True → `block_merge=True` → `gate_decision="rejected"` → `--block-merge`. `LLC_PRP_NO_VERIFY=1` is the logged bypass. | P2 #4 |
| #5 | finalize_session block-merge override | **works (by inspection)** — `--block-merge` forces `gate_decision='rejected'`, skips merge, removes worktree; unconditional on the flag (wins over human `approved`). Downstream of #4. | P2 #5 |
| #6 | post-wave CRITICAL block — `_post_wave_check` | **was CRITICAL defect A-02** (returned `None`); **hotfixed-in-audit** — now returns `bool` in all paths, so `if not _post_wave_check(...)` actually gates. | P2 #6 |
| #7 | pre-wave baseline check — `_pre_wave_check` | **was CRITICAL defect A-01** (undefined → `NameError`); **hotfixed-in-audit** — now a module-level `def` returning `bool`, so the call site no longer raises. | P2 #7 |
| #8 | backend-contract verify (API-first) | **works (as designed — warn-by-default)** — warns + passes on missing contracts; blocks only on detected stubs, bypassable via `--auto-approve`. Fragility (not a defect): hardcoded `PRP-001..014` map. | P2 #8 |
| #9 | prp_verify RF→file + coverage (CRITICAL blocks, WARN never) | **not-exercisable on this baseline** (no PRPs) — **semantics confirmed by inspection**: exit 2 → block via #4; WARN → exit 0/1 → no block; `LLC_PRP_NO_VERIFY=1` bypass. | P2 #9 |
| #10 | fitness block/warn policy (no env bypass) | **works (policy sound; scans-empty here)** — block/hybrid core-module violations force exit 1 without `--strict`; warn is advisory unless `--strict`; no env bypass (`grep` for `LLC_PRP_NO_VERIFY`/`getenv` returns nothing). | P2 #10 |
| #11 | test-coverage gate (CLI) | **inert (checklist-only)** — `llc gate run --gate test-coverage` prints checklist + defers to fail-open `gate_check`; real coverage enforcement lives in `prp_verify.check_project_coverage` (#9). 3-names-for-one-gate split is a doc/UX hazard → **E-11 (LOW)**. | P2 #11 |
| #12 | smart-skip — no guardrail | **bypassable (MEDIUM)** — `is_step_skipped` trusts `DELTA_REPORT.md` verbatim; no allow-list, no protection of always-executed steps (10.6/10.7/10.8/11.1/11.2). A delta report can auto-approve-skip PRP-acceptance + coverage → **E-12 (MEDIUM, escalated)**. | P2 #12 |
| #13 | gate_check human checkpoint | **bypassable (by design) / fail-open** — any input other than exact `r`/`reject` approves; `--auto-approve` approves without interaction (logged). No timeout auto-approve → **E-13 (MEDIUM, escalated)**. | P2 #13 |
| #14 | replay zone-red gate | **works** — red-zone replay requires human gate-11 approval; on rejection falls back to LLM regeneration (logs `zone_red_rejected`). Recorded script never auto-replayed into red-zone files. (Caveat: relies on #13's fail-open `gate_check`.) | P2 #14 |
| #15 | consistency-check (advisory) | **works (as designed — advisory)** — runs after each eligible step, output printed, result never wired to a block. INFO, not a defect (ADV-15). | P2 #15 |

**Verdict tally:** works / as-designed = 9 (#1, #2, #3, #5, #8, #10, #14, #15,
plus #4/#9 by inspection); not-exercisable-but-sound = 2 (#4, #9); hotfixed = 2
(#6→A-02, #7→A-01); open defects = 3 (#11→E-11, #12→E-12, #13→E-13).

---

## 3. Conformance findings (D-01, D-02)

Canonical model = `llc_steps.py` (`REGISTRY` / `normalize_step`). Drift =
mismatch vs guide / skills / `gates.json`.

- **D-01 (LOW, conformance-drift) — 3 stale `step` display fields.** Gates
  `11-SEC`, `12-NULL`, `11-OWASP` carry pre-renumber `step` values (`11`, `12`,
  `11`) instead of `10.6`, `10.7`, `11.1`. The gate **keys** all resolve
  correctly from `llc_steps` (19/19 `in_gj=True`, 16/19 `match=True`); only the
  human-facing display field is stale. No enforcement or code-path depends on
  it. → **open, doc-only / sub-project-2.**

- **D-02 (INFO, out-of-scope) — steps 5a/5b/5c unwired.** `normalize_step(
  "5.1"/"5b"/"5c")` raises `UnknownStepError`; the skills exist on disk
  (untracked) but the pipeline wiring is the reverted in-flight work.
  **Important:** the large gate-remap drift that originally motivated Task 9
  (missing gates 4/5, key collisions, 10 mis-pointed gates) **does not exist**
  at baseline `a519d0f` — gates 4/5 are present and keys align. Do NOT apply any
  gate remap or add gates 4/5. → **out-of-scope** (pending reverted in-flight
  work).

---

## 4. Hotfixes applied (A-01, A-02) — RED → GREEN

Both CRITICAL defects were in `.ace/scripts/llc_wave.py`; both made the wave
engine non-functional. Source was otherwise READ-ONLY for this audit.

### A-01 — `_pre_wave_check` undefined (CRITICAL) → `hotfixed-in-audit`

- **RED:** `has _pre_wave_check: False`; `AttributeError: module 'llc_wave' has
  no attribute '_pre_wave_check'`. The intended body was dead code *inside*
  `_prp_to_keywords` after its `return`, with only a stray docstring where the
  `def` header should be. At the call site (`run_wave:681`)
  `if not _pre_wave_check(...)` raised **`NameError`** — `run_wave` aborted
  before any PRP session opened.
- **Fix (Task 7, commit `607a1b8`):** restored a module-level
  `def _pre_wave_check(dry_run=False, wave_num=0) -> bool:` placed immediately
  before `_post_wave_check`; removed the dead block from `_prp_to_keywords`
  (which again ends cleanly at its `return`).
- **GREEN:** `TestPreWaveCheck` 2/2 passing; post-fix probe returns
  `True` (`bool`) on a missing-script path. Full suite: no new failures
  (4 pre-existing failures unrelated to A-01).

### A-02 — `_post_wave_check` no-op returning `None` (CRITICAL) → `hotfixed-in-audit`

- **RED:** `_post_wave_check` returned `None type: NoneType`. The outer `def`
  declared the function but its **entire body was a nested `def
  _post_wave_check(...)`** that was never called — the outer function fell off
  the end and returned `None`. At the call site (`run_wave:754`)
  `if not None == True` → `run_wave` always emitted "pós-onda bloqueada" and
  returned `False` — every wave looked blocked regardless of the real PRP state.
- **Fix (Task 8, commit `e02a544`):** de-nested — added `-> bool` to the outer
  signature, deleted the inner `def` header, de-indented its body into the
  outer function. Returns `bool` in all paths (`True` on
  script-missing/dry-run/bypass/success, `False` on `prp_verify` CRITICAL).
- **GREEN:** `TestPostWaveCheck` 1/1 passing; post-fix probe returns
  `True` (`bool`). Full suite: no new failures (same 4 pre-existing failures).

**Both hotfixes are characterized as "the wave engine now runs at all."** They
do not change enforcement *semantics* — they restore the wiring the semantics
were already written against. The deterministic merge block (#4/#5), the
fitness policy (#10), and the PRP-verify CRITICAL path (#9) were already correct
by inspection; they were simply unreachable because the wave engine could not
complete a wave.

---

## 5. Open / escalated backlog (decisions needed)

These four items are **open** — they survive the audit. E-12 and E-13 are
**escalated**: they need a policy decision before a hotfix can be written,
because the "correct" behavior is a product/architecture call, not a bug fix.

| ID | Sev | Why it's open | Decision needed | Impact if left |
|----|-----|---------------|-----------------|----------------|
| **E-13** | MEDIUM | `gate_check` fail-open: unknown/empty/mistyped input defaults to `approved` (`llc_harness.py:94`). | Is fail-open intentional? If yes, document it. If no, require explicit `a`/`approve` for approve and treat unknown/empty as `pending` (re-prompt) or a non-default. | A non-interactive or inattentive operator silently approves every gate, including zone-red replay (#14) and the test-coverage CLI gate (#11). |
| **E-12** | MEDIUM | smart-skip trusts `DELTA_REPORT.md` verbatim; no allow-list, no protection of always-executed steps (`llc_delta.py:132-143`). | Define the unskippable set (guide says 10, 10.6, 10.7, 10.8, 11, 11.1, 11.2) and encode it as an `ALWAYS_RUN` set that `is_step_skipped` returns `False` for. | A malformed or adversarial `DELTA_REPORT.md` auto-approve-skips the PRP-acceptance (11.2) and coverage (10.8) gates, defeating #4/#9/#11. |
| **E-11** | LOW | `llc gate run --gate test-coverage` is a checklist + fail-open human checkpoint; real coverage enforcement is in `prp_verify.check_project_coverage`. 3-names-for-one-gate split. | Doc-only: clarify in guide/help that this command is a prompt, not a meter; point to `prp_verify`. Optionally collapse the alias split. | User confusion: operators think the CLI gate enforces coverage; it does not. |
| **D-01** | LOW | 3 stale `step` display fields in `gates.json` (`11-SEC`, `12-NULL`, `11-OWASP`). | Doc-only: update the three fields to `10.6`/`10.7`/`11.1`. No code path depends on them. | Cosmetic drift between `gates.json` display fields and `llc_steps.py` numbers. |

> **Compounding note (E-12 × E-13):** these two are independent but stack. A
> non-interactive CI run under `--auto-approve` (E-13) **plus** a delta report
> that lists `11.2` under `skip_steps` (E-12) means the PRP-acceptance gate is
> both auto-approved (gate_check) and skipped (smart-skip) — the deterministic
> merge block (#4/#5) never sees a rejection because the gate never runs. Fixing
> E-12 (the allow-list) is the higher-leverage of the two; E-13 is the broader
> fail-open posture.

---

## 6. Handoff to sub-project 2 (clean-code refactor)

The audit's downstream consumer is **sub-project 2**: the clean-code refactor of
`.ace/scripts/*`. That refactor must not break the enforcement teeth this audit
verified. The contract is:

1. **`BEHAVIOR_BASELINE.md` is the must-not-break contract.** Every block
   (Intended / Actual / Proof / Gap) is a behavior the refactor must preserve.
   The refactor's tests must reproduce the Proof commands and assert the
   Intended behavior holds. The two CRITICAL gaps (A-01, A-02) are now
   **fixed** — their `Gap` reads "fixed in audit (Task N)" — so the refactor's
   baseline already includes the corrections; do not regress them.

2. **`refactor-wave` backlog items** (consume, don't re-litigate):
   - **E-12** — when refactoring `llc_delta.py`, add the `ALWAYS_RUN` allow-list
     and make `is_step_skipped` return `False` for those steps. (Still needs the
     policy decision in §5 on the exact set, but the code slot is in the
     smart-skip module.)
   - **E-13** — when refactoring `gate_check`, surface the fail-open decision
     (whichever way §5 resolves it) so the refactor encodes the chosen policy,
     not the current silent default.

3. **`doc-only` backlog items** (fold into the refactor's doc pass):
   - **D-01** — update the three stale `step` fields in `gates.json`.
   - **E-11** — clarify the test-coverage CLI gate's role; point to
     `prp_verify.check_project_coverage` as the real meter.

4. **Do NOT carry forward:**
   - **D-02** (5a/5b/5c unwired) — out of scope; pending reverted in-flight work.
     Re-wiring those steps is a separate initiative, not part of the clean-code
     refactor.
   - **The gate-remap drift from the original Task 9 brief** — it does not exist
     at this baseline (gates 4/5 present, keys align, 16/19 match). The only
     drift is D-01 (cosmetic). The characterization test
     (`test_llc_steps.py`, commit `fc886bf`) pins the current step↔gate mapping
     as the regression guard; the refactor must keep it green.

5. **Out-of-scope teeth, by design (not defects — do not "fix" them):**
   - **#3 (ADV-03)** — pre-commit impact+fitness is advisory; the refactor must
     keep it non-blocking.
   - **#15 (ADV-15)** — consistency-check is advisory; the refactor must keep its
     result unwired from the gate decision (it surfaces drift, it does not
     block).

---

*Synthesized by Task 10 of the LLC Workflow & Gate Logic Audit. Source evidence:
`p2-enforcement-log.md`, `p3-conformance-findings.md`, `BEHAVIOR_BASELINE.md`,
`DEFECT_BACKLOG.md` (all in this directory).*

---

## Acceptance Sign-off

Task 11 (final) verification against the 6 acceptance criteria. Each criterion
recorded PASS/FAIL with evidence; rerun + cleanup confirmed below.

1. **All 15 enforcement points have a baseline tuple — PASS.**
   `BEHAVIOR_BASELINE.md` has **17 `### ` blocks**: the 15 enforcement points
   (`### #1` … `### #15`, all present) plus the 2 conformance-drift blocks
   (`### D-01`, `### D-02`). Each block records Intended / Actual / Proof / Gap.

2. **Every drift catalogued — PASS.**
   `DEFECT_BACKLOG.md` contains both drift rows: **D-01** (3 stale `step`
   display fields, LOW) and **D-02** (steps 5a/5b/5c unwired, INFO/out-of-scope).

3. **Every backlog item has severity/proof/fix-target — PASS.**
   Backtick-aware parse of the 9-row table (A-01, A-02, E-13, E-12, E-11, D-01,
   D-02, ADV-03, ADV-15) finds **zero empty `Severity` / `Proof` / `Fix target`
   cells.** (An initial naïve pipe-split falsely flagged ADV-03's `Proof` cell —
   that was a parser artifact from literal `||` / `2>/dev/null` shell tokens
   inside the cell's backticked code; the cell is fully populated.)

4. **Every §4 anchor confirmed or refuted — PASS.** All anchors appear with a
   verdict in `AUDIT_REPORT.md` and/or the backlog:
   - **A-01** — confirmed CRITICAL, hotfixed-in-audit (§4, commit `607a1b8`).
   - **A-02** — confirmed CRITICAL, hotfixed-in-audit (§4, commit `e02a544`).
   - **D-01** — confirmed LOW, open/doc-only (§3, §5).
   - **D-02** — confirmed INFO, out-of-scope (§3, §6).
   - **smart-skip (E-12)** — confirmed MEDIUM, escalated (§2 #12, §5).
   - **silent-bypass / fail-open (E-13)** — confirmed MEDIUM, escalated (§2 #13, §5).

5. **Hotfixes green + suite passes — PASS.**
   `cd .ace/scripts && python3 -m pytest test_llc_wave.py test_llc_steps.py -v` →
   **32 passed, 4 failed.** The 4 failures are the known pre-existing Path-mock
   failures in `test_llc_wave.py` (`TestPrpInfo::test_init_with_tasks`,
   `TestStripPlaceholders::test_removes_multiple_placeholders`,
   `TestParseExecutionWaves::test_parses_waves_with_prps`,
   `TestParseTasks::test_returns_prps_from_headings`) — all in parsing/mock
   helpers, unrelated to the hotfixes or the characterization test, and
   acceptable per the brief. The hotfix tests (`TestPreWaveCheck` 2/2,
   `TestPostWaveCheck` 1/1) and both `test_llc_steps.py` characterization tests
   PASS. Commits confirmed: `git log | grep audit-hotfix` → 2
   (`607a1b8` A-01, `e02a544` A-02); `git log | grep 'test(audit)'` → 1
   (`fc886bf`, Task 9).

6. **Rerunnability — PASS (2 minor recipe-fidelity gaps, both known/acceptable).**
   `bash docs/audit/audit-recipe.sh` exits **0** (no unhandled errors; every
   command is `|| true`-guarded) and **regenerates 5/7 raw outputs** with fresh
   content + mtimes (`validate-tags.json`, `consistency-check.json`,
   `fitness-functions.json`, `code-health.json`, `prp-verify-all.json`). The
   `code-health.json` delta is the legitimate commit-count drift since baseline
   (227→236 commits analyzed). Two minor gaps:
   - **`dependency-graph.yaml` is not regenerated** — the recipe's line 11
     references `docs/prps/PRP-001.md`, which does not exist in this repo
     (`ERROR: PRP não encontrado`); the `-o` file is left containing that error
     string (same state as the committed baseline). This is the known
     recipe-fidelity gap from Task 2; flagged as minor, not a failure.
   - **`llc_steps_registry.json` is not in the recipe** — it is a P3 artifact
     (Task 5), captured separately. Minor recipe-completeness note.

**Rerun verified:** 2026-07-09 — recipe exits 0, regenerates the 5 self-check
outputs; 2 known minor gaps noted above (dependency-graph input missing,
llc_steps_registry not in recipe).

**Cleanup confirmed:** scratch worktree `../llc-audit-scratch` removed
(`git worktree remove --force`) and throwaway branch `llc-audit-scratch`
(deleted at `a519d0f`) deleted (`git branch -D`); `git worktree list` now shows
only the main worktree at `aa9d45f [api-design-enforcement-docs]`.
