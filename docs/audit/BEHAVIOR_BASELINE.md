# Behavior Baseline (refactor must-not-break contract)

One block per enforcement point: **Intended / Actual / Proof / Gap**.

This baseline consolidates the P2 enforcement observations (`p2-enforcement-log.md`,
points #1–#15) and the P3 conformance drift findings (`p3-conformance-findings.md`,
D-01/D-02) into the refactor's must-not-break contract (audit sub-project 2). Each
block records the **Intended** behavior (from guide/skill), the **Actual** behavior
(observed in P2/P3), the **Proof** command that reproduces it, and the **Gap**
(none, or a one-line description).

> Source under `.ace/scripts/*` was READ-ONLY for this audit. The two CRITICAL wave
> defects are **A-01 (#7)** and **A-02 (#6)**; their Gap is recorded as the defect
> and is **not** marked fixed — the hotfixes land in Task 7 (A-01) / Task 8 (A-02),
> after which their Gap will be updated to "fixed in audit (Task N)".

---

## Enforcement points (#1–#15)

### #1 pre-commit session coverage — code-without-session rejected
- **Intended:** A staged code file not referenced in any session's `<file_delta>` is rejected (commit blocked).
- **Actual:** `validate-tags.py --coverage` detects the staged file as uncovered, prints `❌ 1 arquivo(s) de código … não aparecem em <file_delta>`, exits **1**; the full `pre-commit.sh` then prints `❌ Commit bloqueado …` and exits **1** (`PRECOMMIT_EXIT=1`). Works.
- **Proof:**
  ```bash
  cd /home/jcneto/Projetos/llc-audit-scratch
  mkdir -p src && echo 'export const x = 1;' > src/probe.ts && git add src/probe.ts
  python3 .ace/scripts/validate-tags.py --coverage; echo "exit=$?"   # expect 1
  git reset -q HEAD src/probe.ts && rm -rf src
  ```
- **Gap:** none (caveat, not a defect: hook not auto-installed; bypassable with `git commit --no-verify`, which the script itself documents as "não recomendado").

### #2 pre-commit tag/index integrity
- **Intended:** Pre-commit runs the full integrity sweep (index.json, balanced tags, context_seed schema, `<dependencies>` block, required/valid attributes) and blocks on defect.
- **Actual:** On a clean tree the validator prints `✅ Nenhum erro encontrado` and exits **0**. `pre-commit.sh` runs its own shell-level integrity checks (index.json exists + valid JSON, every indexed session exists on disk, no orphan `.md`, completed sessions carry a complete `<context_seed>`) incrementing `ERRORS` and exiting 1 at line 130 if `ERRORS > 0`. Works.
- **Proof:**
  ```bash
  cd /home/jcneto/Projetos/llc-audit-scratch
  python3 .ace/scripts/validate-tags.py --strict; echo "exit=$?"   # expect 0 on clean tree
  ```
- **Gap:** none.

### #3 pre-commit impact+fitness advisory (non-blocking)
- **Intended:** impact-analyzer + fitness-functions output is advisory only — never blocks the commit (spec: #3 is an advisory tooth, not a hard block).
- **Actual:** `impact-analyzer.py` (`pre-commit.sh:106`) stderr → `/dev/null`, wrapped in `|| echo` (advisory). `fitness-functions.py` (`pre-commit.sh:108-122`) piped through a summarizer whose stderr is `2>/dev/null`, followed by `|| echo`. A textual `🔴 BLOQUEIO` is never tested and never increments `ERRORS` (`pre-commit.sh:125-131`). Neither call touches the `ERRORS` counter. Works as designed.
- **Proof:**
  ```bash
  grep -n "impact-analyzer\|fitness-functions\|2>/dev/null\|ERRORS=" .ace/scripts/pre-commit.sh
  ```
- **Gap:** none (by design: a fitness `BLOQUEIO` surfaces only as visible text).

### #4 session_end CRITICAL merge block (prp_verify exit 2)
- **Intended:** When `prp_verify` exits **2** (CRITICAL pendências), `session_end` sets `block_merge=True`, forces `gate_decision="rejected"`, and appends `--block-merge` to `finalize_session.py`. `LLC_PRP_NO_VERIFY=1` is the explicit logged bypass.
- **Actual:** Not-exercisable-on-this-baseline (LLC repo has no PRPs; `prp_verify --prp PRP-001` exits **1**, PRP-not-found, not 2). Static evidence shows the wiring is sound: `_maybe_block_on_prp_verify(session_id, eff_step)` (`llc_harness.py:265`) is called from `session_end` (lines **358-363**); on True it forces `gate_decision="rejected"` (lines **360-361**) and appends `--block-merge` (lines **379-380**). `_run_prp_verify` returns True **only** when `result.returncode == 2` (line **252**); exit 1 returns False → no block. `LLC_PRP_NO_VERIFY=1` short-circuits to `return False` with a logged warning (lines **273-275**). Block fires only for execution sessions (`canonical_id(eff_step) == "11"`, line **279**) with an associated PRP.
- **Proof:**
  ```bash
  cd /home/jcneto/Projetos/llc-audit-scratch
  python3 .ace/scripts/prp_verify.py --prp PRP-001 --strict --json; echo "exit=$?"   # 1 (PRP not found)
  grep -n "block_merge\|_maybe_block_on_prp_verify\|LLC_PRP_NO_VERIFY\|returncode == 2" .ace/scripts/llc_harness.py
  ```
- **Gap:** none (not-exercisable here; works-by-inspection). Live confirmation of the exit-2 block path requires a repo with a real PRP carrying CRITICAL pendências.

### #5 finalize_session block-merge override
- **Intended:** `finalize_session.py --block-merge` is a hard override that forces `gate_decision='rejected'`, skipping the merge and removing the worktree (downstream consumer of #4; deterministic acceptance of §8.7).
- **Actual:** Works (by inspection). `--block-merge` defined at `finalize_session.py:510-512`; `gate_decision` read from `<gate_result>` (lines 567-571) then overridden to `"rejected"` when `args.block_merge` (lines **576-578**, logging `⛔ --block-merge ativo: merge bloqueado …`); line **581-582** calls `merge_and_cleanup_worktree(session_id, gate_decision, …)`. On `rejected`, merge is skipped (`⏭️  Branch … não mergeado`, line 83) but the worktree is still removed (line 85, `git worktree remove --force`). The override is unconditional on the flag — wins over any human `approved`.
- **Proof:**
  ```bash
  cd /home/jcneto/Projetos/llc-audit-scratch
  grep -n "block-merge\|block_merge\|gate_decision\|merge_and_cleanup_worktree" .ace/scripts/finalize_session.py | head
  sed -n '49,89p;510,582p' .ace/scripts/finalize_session.py
  ```
- **Gap:** none.

### #6 post-wave CRITICAL block — `_post_wave_check` is a no-op returning None  (DEFECT A-02 — CRITICAL)
- **Intended:** `_post_wave_check` runs `pre-wave-check.sh`, consistency-check, and `prp_verify` after each wave; on a CRITICAL (`prp_verify` exit 2) it returns False so `run_wave` blocks the wave (`llc_wave.py:589-629`), honoring `LLC_PRP_NO_VERIFY`.
- **Actual:** **Inert (DEFECT A-02 — CRITICAL).** `_post_wave_check` (`llc_wave.py:514`) declares the outer function but its **entire body is a nested `def _post_wave_check(...)`** (`llc_wave.py:517`) that is **never called** — the outer function falls off the end and returns `None`. Probe verbatim: `returned: None type: NoneType`. The intended logic lives inside the nested def as unreachable dead code. At the call site `run_wave` (`llc_wave.py:754`): `if not _post_wave_check(...)` — `None` is falsy, so `not None == True` → `run_wave` emits the "pós-onda bloqueada" error and **returns False** regardless of the real PRP state — every wave looks blocked.
- **Proof:**
  ```bash
  python3 - <<'PY'
  import sys, os; sys.path.insert(0, ".ace/scripts")
  os.environ.pop("LLC_PRP_NO_VERIFY", None)
  import llc_wave, pathlib
  llc_wave.PRE_WAVE_CHECK_SCRIPT = pathlib.Path("/nonexistent/pre-wave-check.sh")
  print("returned:", repr(llc_wave._post_wave_check(dry_run=False, wave_num=1, prp_ids=None)))
  PY
  # → returned: None
  sed -n '514,520p' .ace/scripts/llc_wave.py     # outer def + nested def, no call
  ```
- **Gap:** **DEFECT A-02 (CRITICAL)** — `_post_wave_check` returns `None` instead of `bool`; the post-wave CRITICAL block is inert and the `if not …` guard misfires. (To be hotfixed in Task 8; Gap will be updated to "fixed in audit (Task 8)" after that task. **Not yet fixed.**)

### #7 pre-wave baseline check — `_pre_wave_check` is undefined (DEFECT A-01 — CRITICAL)
- **Intended:** `_pre_wave_check` runs `pre-wave-check.sh --build-only` before each wave and returns False on a failed build so `run_wave` aborts before any PRP session opens (`llc_wave.py:478-511`).
- **Actual:** **Crashes (DEFECT A-01 — CRITICAL).** There is **no `def _pre_wave_check(...)`** in `llc_wave.py` at all — the intended body is dead code **inside** `_prp_to_keywords` (`llc_wave.py:454-475`), sitting **after** that function's unconditional `return mapping.get(prp_id, [])` (line **475**) with only a stray docstring where a `def` header should be. Probe verbatim: `has _pre_wave_check: False` / `AttributeError: module 'llc_wave' has no attribute '_pre_wave_check'`. At the call site `run_wave` (`llc_wave.py:681`): `if not _pre_wave_check(...)` — because the name is not a module global, executing line 681 raises **`NameError`** at runtime; `run_wave` aborts before any PRP session opens.
- **Proof:**
  ```bash
  python3 - <<'PY'
  import sys; sys.path.insert(0, ".ace/scripts")
  import llc_wave, inspect, textwrap
  print("has _pre_wave_check:", hasattr(llc_wave, "_pre_wave_check"))
  print("dead body inside _prp_to_keywords (after its return, llc_wave.py:478-511):")
  src = inspect.getsource(llc_wave._prp_to_keywords)
  print(textwrap.indent(src[src.find('# ── Pré/Pós'):], '  ') if '# ── Pré/Pós' in src else '  (dead tail present after return)')
  PY
  grep -n "def _pre_wave_check\|def _prp_to_keywords\|return mapping.get" .ace/scripts/llc_wave.py
  ```
- **Gap:** **fixed in audit (Task 7)** — `_pre_wave_check` is now a module-level `def _pre_wave_check(dry_run: bool = False, wave_num: int = 0) -> bool:` placed immediately before `_post_wave_check`; the dead block was removed from `_prp_to_keywords` (which again ends cleanly at its `return`). TDD: RED (`ImportError: cannot import name '_pre_wave_check'`) → GREEN (2/2 `TestPreWaveCheck` passing); full suite has no new failures (4 pre-existing failures unrelated to A-01).

### #8 backend-contract verify (API-first) — warn-by-default; blocks only on stubs
- **Intended:** API-first enforcement checks UI PRPs for backend contracts; missing contracts warn (don't block); detected stub services block (unless `--auto-approve`).
- **Actual:** `_verify_backend_contracts` (`llc_wave.py:358-451`) is the only API-first enforcement, gated on `_is_ui_prp(prp_id, info)` at `run_wave`'s call site (`llc_wave.py:723`) — only Trilha B (UI) PRPs are checked. `dry_run` → returns True (lines 370-372); no `api/` contracts and no OpenAPI/Swagger → warns + `return True` (lines 432-439, "Don't block, just warn"); stubs detected (`is_stub_service`) → `return False` (lines 441-448) → at the call site (lines 725-735) `run_wave` returns False **unless `auto_approve`**, in which case it logs "Continuando para próximo PRP (auto-approve)" and skips that PRP. PRP→service matching uses the hardcoded `PRP-001..014` keyword map in `_prp_to_keywords` (lines 459-474). Works as designed.
- **Proof:**
  ```bash
  sed -n '358,451p' .ace/scripts/llc_wave.py     # full _verify_backend_contracts
  grep -n "_is_ui_prp\|_verify_backend_contracts\|auto_approve" .ace/scripts/llc_wave.py
  ```
- **Gap:** fragility (not an enforcement defect): the hardcoded PRP-001..014 map means PRPs outside the set (PRP-015+, renamed services) match nothing → "no contracts found → warn + pass".

### #9 prp_verify RF→file + coverage — CRITICAL blocks, WARN never blocks
- **Intended:** `prp_verify` exit codes: **0 = clean**, **1 = PRP-not-found / non-CRITICAL**, **2 = CRITICAL pendências**. Only exit 2 routes through #4 to `block_merge=True`. WARN-level pendências never block. `LLC_PRP_NO_VERIFY=1` is the bypass.
- **Actual:** Not-exercisable-on-this-baseline. The LLC repo has no `.ace/prps/` directory; `prp_verify --prp PRP-001 --strict --json` emits `❌ PRP não encontrado: PRP-001` and exits **1** (not 2), so the CRITICAL-exit (`== 2`) path that blocks via #4 is unreachable here. Semantics confirmed by inspection: exit 2 → `_maybe_block_on_prp_verify` returns True → `block_merge=True` → `gate_decision="rejected"`; WARN → exit 0/1 → no block; `LLC_PRP_NO_VERIFY=1` short-circuits the whole check.
- **Proof:**
  ```bash
  python3 .ace/scripts/prp_verify.py --prp PRP-001 --strict --json; echo "exit=$?"   # 1 (PRP not found)
  grep -n "returncode == 2\|CRITICAL\|return True\|return False" .ace/scripts/llc_harness.py | head
  ```
- **Gap:** none (not-exercisable here; semantics confirmed by inspection). Live confirmation of the exit-2 path requires a repo with a real PRP carrying CRITICAL pendências.

### #10 fitness block/warn policy — block/hybrid exit 1 without --strict; no env bypass
- **Intended:** Per-check `mode` (`block`/`hybrid`/`warn`) in `.ace/arch-config.yaml`; `block` or `hybrid` (violating a `core_module`) → exit 1 even without `--strict`; `warn` → exit 0 (advisory) unless `--strict`. No env bypass for fitness (spec anchor #8).
- **Actual:** Works (policy sound; scans-empty on this baseline). `.ace/arch-config.yaml` configures per-check `mode`. Live run on LLC repo (which has **0 services**) returned `blocked: None warnings: 0 exit=0` (the top-level `blocked` key is `None`; per-check `blocked` flags nest under `results`, aggregate in `summary.blocked` — `fitness-functions.py:1866`). Exit-code policy (`fitness-functions.py:1882-1885`): `has_blocks = output["summary"]["blocked"]`; `has_strict_fail = args.strict and (has_blocks or warnings > 0)`; `sys.exit(1 if has_strict_fail or has_blocks else 0)`. `grep` for `LLC_PRP_NO_VERIFY` / `os.environ.get` / `getenv` in `fitness-functions.py` returns nothing — no env bypass.
- **Proof:**
  ```bash
  python3 .ace/scripts/fitness-functions.py --all --json > /tmp/fit.json; echo "exit=$?"
  python3 -c "import json;d=json.load(open('/tmp/fit.json'));print('summary:',d['summary'])"
  sed -n '1882,1886p' .ace/scripts/fitness-functions.py
  ```
- **Gap:** none (could not produce a live block on LLC's repo — 0 services; the exit-1 path rests on static evidence).

### #11 test-coverage gate (CLI) — checklist + human checkpoint only
- **Intended:** `llc gate run --gate test-coverage` enforces the test-coverage gate.
- **Actual:** Inert (checklist-only). The gate has three names for one gate (`10-COVERAGE` / `10.8` / `test-coverage`; `llc.py:45,88`). `gate_run` (`llc.py:408-425`): in `--dry-run` prints the checklist (`_show_gate_checklist`) and returns; otherwise prints "🔍 Validando Gate …" and calls `gate_check(gate_id, prp)` — the human checkpoint from #13 (fail-open: defaults to `approved` on any non-`r`/`reject` input, auto-approves under `--auto-approve`). The command does **not** measure coverage itself; the real coverage threshold lives in `prp_verify.check_project_coverage`, invoked on the CRITICAL path of #9 (and routed through #4's merge block).
- **Proof:**
  ```bash
  sed -n '345,425p' .ace/scripts/llc.py     # _show_gate_checklist + gate_run
  grep -n '"test-coverage"\|"10.8"\|check_project_coverage' .ace/scripts/llc.py .ace/scripts/prp_verify.py
  ```
- **Gap:** documentation/UX hazard — 3-names-for-one-gate split (`10-COVERAGE` / `10.8` / `test-coverage`).

### #12 smart-skip — no guardrail: any DELTA_REPORT skip is honored (MEDIUM)
- **Intended:** Smart-skip honors `skip_steps` from `DELTA_REPORT.md` but protects "always-executed" steps (per the guide: 10, 10.6, 10.7, 10.8, 11, 11.1, 11.2 must always run).
- **Actual:** Bypassable (MEDIUM). `is_step_skipped` (`llc_delta.py:132-143`) is driven **entirely** by the `skip_steps` list parsed from `DELTA_REPORT.md` — there is **no validation** of the skipped step id against any allow-list and **no protection of always-executed steps**. `grep` for `sempre` / `always` / `always_exec` / `protected` in `llc_delta.py` returns nothing. A `DELTA_REPORT.md` listing e.g. `step_id: "11.2"` (PRP-acceptance) or `"10.8"` (coverage) under `skip_steps` returns True, and `generate_skip_note` (`llc_delta.py:153-173`) writes a note ending `**Gate:** ✅ Auto-aprovado via Smart Skip`. A malformed or adversarial delta report can auto-approve-skip the PRP-acceptance and coverage gates, defeating #4/#9/#11.
- **Proof:**
  ```bash
  sed -n '132,175p' .ace/scripts/llc_delta.py
  grep -n "sempre\|always\|always_exec\|protected\|10.6\|10.7\|10.8\|11.1\|11.2" .ace/scripts/llc_delta.py   # → none
  ```
- **Gap:** policy gap (MEDIUM) — smart-skip trusts `DELTA_REPORT.md` verbatim with no allowed-set check and no protection of always-executed steps; escalated (needs a policy decision on which steps are unskippable before a hotfix).

### #13 gate_check human checkpoint — unknown input defaults to approved
- **Intended:** `gate_check` is the human A/R checkpoint; spec anchor #8 says the auto-approve path is logged/visible, not silent. No timeout auto-approve (docstring: "timeout NAO auto-aprova").
- **Actual:** Bypassable (by design) / fail-open. `gate_check` (`llc_harness.py:68-94`): `choice = input().strip().lower()`; `a`/`approve` → `approved`; `r`/`reject` → `rejected`; **fall-through returns `approved`** (line **94**) for ANY other input (blank line, `x`, `no`, `n`, EOF-after-empty, a typo like `rejct`). `--auto-approve` auto-approves silently with `⚡ Modo auto-aprove (CI).` print (lines 81-83), wired from the CLI in `llc.py` (`run`, `pipeline`, `wave_run`, `delta_start`) and threaded through the harness. There is **no timeout auto-approve** — `input()` blocks indefinitely; the fail-open is purely the default-return.
- **Proof:**
  ```bash
  cd /home/jcneto/Projetos/llc-audit-scratch
  sed -n '68,94p' .ace/scripts/llc_harness.py
  grep -n "auto_approve\|auto-approve\|gate_check(" .ace/scripts/llc.py .ace/scripts/llc_harness.py
  ```
- **Gap:** by-design fail-open (not a hard defect) — the "human checkpoint" provides no enforcement against an inattentive or non-interactive operator; flagged.

### #14 replay zone-red gate — red-zone replay requires human gate-11 approval (else LLM fallback)
- **Intended:** A script replay touching a red-zone file is not auto-replayed; it requires a human gate-11 approval. On rejection it falls back to LLM regeneration (and logs `zone_red_rejected`). The recorded script is never silently replayed over red-zone files.
- **Actual:** Works. During script replay, after architecture-version and pre-flight checks, the harness runs the zone check (R2) (`llc_harness.py:514-520`): `target_files = extract_files_from_script(script)`; `if any(is_red_zone(Path(f)) for f in target_files):` prints `🔴 Zona VERMELHA detectada.`; `if gate_check(canonical_id(11), script) != "approved":` → `log_replay_event("llm_fallback", None, reason="zone_red_rejected")` and `return _llm_invoke(prompt, client)`. `is_red_zone` imported at `llc_harness.py:108`. Red-zone does **not** hard-stop — it forces "human-review-OR-regenerate-via-LLM".
- **Proof:**
  ```bash
  sed -n '514,526p' .ace/scripts/llc_harness.py
  grep -n "is_red_zone\|canonical_id(11)\|llm_fallback\|zone_red" .ace/scripts/llc_harness.py
  ```
- **Gap:** none (caveat carried from #13: the human `gate_check` is fail-open, so an inattentive operator can still approve).

### #15 consistency-check — advisory only, never blocks
- **Intended:** consistency-check is an advisory tooth — it surfaces drift after each step but never gates the pipeline.
- **Actual:** Works (as designed — advisory). `pipeline_run` runs `consistency-check.py` **after each step** except the early ones (`llc_harness.py:751-752`: `if spec.id not in ["0", "0.1", "0.5", "1"]:`); output is printed (lines 763-768: stdout echoed, stderr surfaced only if it contains `ERRO`). The result is **never tested** against the gate decision — no `if result.returncode != 0: block/return False`; the `except` branch (lines 769-770) merely prints `ℹ️  consistency-check não executou: …` and the loop continues. A failing consistency-check cannot stop the pipeline or reject a gate. (Same advisory nature reproduced inside the dead `_post_wave_check` nested def, `llc_wave.py:562-585`, itself unreachable — see #6.)
- **Proof:**
  ```bash
  sed -n '751,775p' .ace/scripts/llc_harness.py     # consistency-check block; no return/block on non-zero
  grep -n "consistency-check" .ace/scripts/llc_harness.py
  ```
- **Gap:** none (by design: advisory, never blocks).

---

## Conformance drift findings (D-01, D-02)

Canonical model = `llc_steps.py`. Drift = mismatch vs guide / skills / `gates.json`.

### D-01 three stale `step` fields in gates.json (LOW)
- **Intended:** Every gate's `step` field in `.ace/config/gates.json` matches the canonical step number in `llc_steps.REGISTRY` (within `EPS`).
- **Actual:** Three stale `step` fields: `11-SEC` has `"step": 11` (should be 10.6), `12-NULL` has `"step": 12` (should be 10.7), `11-OWASP` has `"step": 11` (should be 11.1). The gate **KEYS** all resolve correctly from `llc_steps` (`in_gj=True` for all 19); only the display/lookup `step` field is stale. Of 19 steps with gates, **16 match**, **3 mismatch** (`match=False`). No missing keys, no collisions.
- **Proof:**
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
- **Gap:** 3 stale step-fields; LOW; backlog (no fix in this audit).

### D-02 steps 5a/5b/5c unwired (out of scope)
- **Intended:** Steps 5a (Architecture Patterns), 5b (API Design), 5c (Clean Code) are part of the pipeline and resolvable via `normalize_step`.
- **Actual:** Steps 5a/5b/5c are **NOT** in the committed `REGISTRY` — `normalize_step("5.1"/"5b"/"5c")` raises `UnknownStepError`. The skills `llc-step-5b-api-design.md`, `llc-step-5c-clean-code.md`, `llc-step-api-design.md` exist on disk (untracked) but the pipeline wiring is the reverted in-flight work. (NOTE: the large gate-remap drift that motivated the original Task 9 — missing gates 4/5, key collisions, 10 mis-pointed gates — DOES NOT EXIST at baseline `a519d0f`; gates 4/5 are present and keys align. Do NOT apply any gate remap or add gates 4/5.)
- **Proof:**
  ```bash
  python3 - <<'PY'
  import sys; sys.path.insert(0, ".ace/scripts")
  import llc_steps
  for s in ("5.1", "5b", "5c"):
      try:
          llc_steps.normalize_step(s); print(s, "→ resolved")
      except llc_steps.UnknownStepError as e:
          print(s, "→ UnknownStepError")
  PY
  ```
- **Gap:** 5a/5b/5c unwired; out of scope (pending reverted in-flight work).
