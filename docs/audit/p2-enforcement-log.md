# P2 — Enforcement Verification Log

One section per enforcement point (#1–#15). Record observed behavior + proof command.

> Scope of this file: all 15 enforcement points.
> - **Part 1 (#1, #2, #3, #4, #5, #13):** git / pre-commit / session teeth —
>   run inside the scratch worktree `/home/jcneto/Projetos/llc-audit-scratch`
>   (branch `llc-audit-scratch` @ `a519d0f`).
> - **Part 2 (#6, #7, #8, #9, #10, #11, #12, #14, #15):** wave / verify /
>   fitness / skip teeth — run in the LLC repo itself
>   (`/home/jcneto/Projetos/Live-and-Let-Code`, branch
>   `api-design-enforcement-docs`). Part 2 records the **two CRITICAL defects
>   A-01 (#7) and A-02 (#6)** that gate the hotfix tasks (Task 7 / Task 8).
>
> Source under `.ace/scripts/*` is READ-ONLY for this audit; no pipeline source
> was modified.
>
> **Note on #1 (pre-commit hook):** No `pre-commit` git hook is installed in the
> repo or worktree (deliberate — `pre-commit.sh` is the reference hook that
> `cp`/`pre-commit install` would wire up). A plain `git commit` therefore does
> **not** trigger the enforcement. To verify the coverage logic, the exact check
> `pre-commit.sh` invokes (`python3 .ace/scripts/validate-tags.py --coverage`)
> was run directly, plus the full `bash .ace/scripts/pre-commit.sh` for the
> end-to-end behavior. Both are reproduced below.

---

## #1 pre-commit session coverage — code-without-session rejected

**Trigger** (actually run, in scratch worktree — no git hook is installed, so the
coverage check is invoked directly as `pre-commit.sh` would invoke it):

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
mkdir -p src && echo 'export const x = 1;' > src/probe.ts
git add src/probe.ts
python3 .ace/scripts/validate-tags.py --coverage; echo "COVERAGE_EXIT=$?"
# plus end-to-end:
bash .ace/scripts/pre-commit.sh; echo "PRECOMMIT_EXIT=$?"
```

**Observed:** `validate-tags.py --coverage` detected `src/probe.ts` as staged
code not referenced in any session's `<file_delta>` and exited **1** with:

```
❌ 1 arquivo(s) de código no commit não aparecem em <file_delta> de nenhuma
   sessão (src/probe.ts). Confirme que há uma sessão aberta cobrindo este trabalho.
❌ 1 problema(s) — bloqueando o commit.
COVERAGE_EXIT=1
```

The full `pre-commit.sh` then printed `❌ Commit bloqueado: há código no commit
sem sessão ACE correspondente.` and exited **1** (`PRECOMMIT_EXIT=1`). The
`if python .ace/scripts/validate-tags.py --coverage … else … exit 1` block at
`pre-commit.sh:20-31` is the blocking gate; on non-zero coverage it emits
`exit 1`.

> Implementation detail recorded: the scratch worktree already has one
> `in_progress` session, so the *first* coverage branch ("zero sessions") did
> not fire; the **second** branch — `_session_referenced_files()` finds the
> staged file absent from every `<file_delta>` (`validate-tags.py:290-302`) —
> is what produced the error. Both branches return non-zero and both block.
> The probe commit was discarded (`git reset`, `rm`); scratch HEAD returned to
> `a519d0f`, working tree clean.

**Proof:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
mkdir -p src && echo 'export const x = 1;' > src/probe.ts && git add src/probe.ts
python3 .ace/scripts/validate-tags.py --coverage; echo "exit=$?"   # expect 1
git reset -q HEAD src/probe.ts && rm -rf src
```

**Verdict:** **works** — code staged without a covering session is rejected
(exit 1) both by the coverage check and by the full `pre-commit.sh`. (Caveat,
not a defect: the hook is not auto-installed; enforcement depends on
`pre-commit install` / `cp … .git/hooks/pre-commit`, and is bypassable with
`git commit --no-verify`, which the script itself documents as "não
recomendado".)

---

## #2 pre-commit tag/index integrity

**Trigger:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
python3 .ace/scripts/validate-tags.py --strict; echo "exit=$?"
```

**Observed:** On a clean tree the validator ran the full integrity sweep
(`validate_index_json`, balanced-tag check, context_seed schema,
`<dependencies>` block, required/valid attributes) over the 1 session on disk
and printed `✅ Nenhum erro encontrado`, exiting **0**.

```
🔍 VALIDAÇÃO ACE — 1 sessão(ões)
✅ Nenhum erro encontrado
exit=0
```

`pre-commit.sh` additionally runs its own shell-level integrity checks
(index.json exists + valid JSON, every indexed session exists on disk, no
orphan `.md` in `.ace/sessions/`, completed sessions carry a complete
`<context_seed>`), `pre-commit.sh:33-101`, incrementing `ERRORS` on any
defect and exiting 1 at line 130 if `ERRORS > 0`.

**Proof:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
python3 .ace/scripts/validate-tags.py --strict; echo "exit=$?"   # expect 0 on clean tree
```

**Verdict:** **works** — integrity validator runs and passes on a clean tree
(exit 0); defects surface as non-zero via `--strict` / the `ERRORS` counter.

---

## #3 pre-commit impact+fitness advisory (non-blocking)

**Trigger:** static inspection of `pre-commit.sh` lines invoking the analyzers
(no live run needed — the control flow is the proof).

**Observed:** Both analyzers are invoked with their output deliberately
discarded / downgraded so a non-zero or empty result cannot block the commit:

- `impact-analyzer.py` — `pre-commit.sh:106`:
  `python .ace/scripts/impact-analyzer.py --staged --json 2>/dev/null && echo "✅ …" || echo "⚠️  Impact analyzer não executou …"`
  stderr is sent to `/dev/null` and the whole pipeline is wrapped in
  `|| echo` (advisory only). A failure prints a warning and continues.
- `fitness-functions.py` — `pre-commit.sh:108-122`: output is piped through a
  Python summarizer whose stderr is `2>/dev/null`, and the entire pipeline is
  followed by `|| echo "⚠️  Fitness functions não executou …"`. The summary
  prints `🔴 BLOQUEIO` textually when `blocked > 0`, but this string is never
  tested by `pre-commit.sh` and never increments `ERRORS`, so it is purely
  informational.

Neither call touches the `ERRORS` counter (`pre-commit.sh:125-131`), so neither
can cause `exit 1`.

**Proof:**

```bash
grep -n "impact-analyzer\|fitness-functions\|2>/dev/null\|ERRORS=" .ace/scripts/pre-commit.sh
```

**Verdict:** **works (as designed — advisory)** — impact + fitness output is
discarded/downgraded and never blocks the commit; this matches the spec intent
(#3 is an advisory tooth, not a hard block). Note this is by design, not a
defect: a fitness `BLOQUEIO` is surfaced only as visible text.

---

## #4 session_end CRITICAL merge block (prp_verify exit 2)

**Trigger:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
python3 .ace/scripts/prp_verify.py --prp PRP-001 --strict --json 2>&1 | head -40; echo "exit=${PIPESTATUS[0]}"
grep -n "block_merge\|_maybe_block_on_prp_verify\|LLC_PRP_NO_VERIFY" .ace/scripts/llc_harness.py
```

**Observed:** The live run could **not** exercise the blocking path on this
baseline:

```
❌ PRP não encontrado: PRP-001
exit=1
```

`prp_verify.py --prp PRP-001` exits **1** (PRP-not-found), not **2** (CRITICAL).
There is no `.ace/prps/` directory and no target PRPs in the LLC repo, so the
CRITICAL-exit (`== 2`) branch in `_run_prp_verify` (`llc_harness.py:252`) is
unreachable here. Per brief guidance, the verdict rests on the static evidence:

- `llc_harness.py:265` `_maybe_block_on_prp_verify(session_id, eff_step)` is the
  deterministic gate. It is called from `session_end` at line **358**:
  `if _maybe_block_on_prp_verify(real_id, eff_step): block_merge = True`
  (line **359**), and on the else branch `block_merge = False` (line **363**).
- When it returns True, `gate_decision` is forced to `"rejected"` (lines
  **360-361**) and `--block-merge` is appended to the `finalize_session.py`
  command (line **379-380**).
- `_run_prp_verify` (lines **241-262**) returns True **only** when
  `result.returncode == 2`; a "PRP not found" exit 1 returns False → no block
  (correct — a missing PRP is not a CRITICAL failure).
- Bypass: `LLC_PRP_NO_VERIFY=1` short-circuits to `return False` with a logged
  warning `⚠️  prp_verify BYPASSADO via LLC_PRP_NO_VERIFY=1` (lines **273-275**)
  — explicit, logged override (spec anchor #8).
- The block fires only for execution sessions (`canonical_id(eff_step) == "11"`,
  line **279**) that have a PRP associated via `_prp_from_index` (line **284**).

**Proof:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
python3 .ace/scripts/prp_verify.py --prp PRP-001 --strict --json; echo "exit=$?"   # 1 (PRP not found)
grep -n "block_merge\|_maybe_block_on_prp_verify\|LLC_PRP_NO_VERIFY\|returncode == 2" .ace/scripts/llc_harness.py
```

**Verdict:** **not-exercisable-on-this-baseline** (works-by-inspection). The
LLC baseline has no PRPs, so `prp_verify` cannot exit 2 here. Static evidence
shows the wiring is correct and sound: exit-2 → `block_merge=True` →
`gate_decision="rejected"` → `--block-merge` to `finalize_session.py`. The
`LLC_PRP_NO_VERIFY=1` bypass exists and is logged. (Live confirmation of the
exit-2 block path would require a repo with a real PRP carrying CRITICAL
pendências.)

---

## #5 finalize_session block-merge override

**Trigger:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
grep -n "block-merge\|block_merge\|gate_decision" .ace/scripts/finalize_session.py | head
```

**Observed:** `finalize_session.py` honors `--block-merge` as a hard override
that forces the merge to be skipped — it is the downstream consumer of #4's
`block_merge` flag:

- `finalize_session.py:510-512` defines the flag:
  `--block-merge … "Força gate_decision='rejected' … Usado pelo harness quando
  prp_verify encontra CRITICAL — impede o merge."`
- Lines **567-578**: `gate_decision` is first read from the session's recorded
  `<gate_result>` (line 567-571), then `if args.block_merge:` overrides it to
  `"rejected"` (lines **576-578**) and logs
  `⛔ --block-merge ativo: merge bloqueado (prp_verify CRITICAL)`.
- Line **581-582**: `if gate_decision:` calls
  `merge_and_cleanup_worktree(session_id, gate_decision, …)`.
- `merge_and_cleanup_worktree` (lines **49-89**): when `decision == 'approved'`
  it merges the branch into master (lines 73-78); otherwise (rejected) it
  **skips the merge** (`⏭️  Branch … não mergeado (gate: rejected)`, line 83)
  and **still removes the worktree** (line 85, `git worktree remove --force`).

So `--block-merge` → `rejected` → no merge + worktree removed. This confirms #5
is downstream of #4 and that a CRITICAL prp_verify result physically prevents
the worktree branch from entering master. Note: the override is unconditional
on the flag — `--block-merge` wins over any human `approved` `<gate_result>`,
matching the deterministic-acceptance intent of §8.7.

**Proof:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
grep -n "block-merge\|block_merge\|gate_decision\|merge_and_cleanup_worktree" .ace/scripts/finalize_session.py | head
sed -n '49,89p;510,582p' .ace/scripts/finalize_session.py
```

**Verdict:** **works (by inspection)** — `--block-merge` deterministically
forces `gate_decision='rejected'`, which skips the merge and removes the
worktree. Downstream of and consistent with #4.

---

## #13 gate_check human checkpoint — unknown input defaults to approved

**Trigger:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
grep -n "def gate_check\|approved\|decision" .ace/scripts/llc_harness.py | head -20
sed -n '68,94p' .ace/scripts/llc_harness.py
```

**Observed:** `gate_check` (`llc_harness.py:68-94`) is the human checkpoint. Its
decision logic:

```python
choice = input().strip().lower()
if choice in ("a", "approve"):
    return "approved"
elif choice in ("r", "reject"):
    return "rejected"
return "approved"          # ← line 94: fall-through for ANY other input
```

- **Unknown / empty / mistyped input defaults to `approved`** (line **94**).
  Only the exact tokens `r` / `reject` produce `rejected`; everything else
  (blank line, `x`, `no`, `n`, EOF-after-empty, a typo like `rejct`) approves.
  This is a **permissive fail-open**: the human gate cannot accidentally stall
  the pipeline, but it also cannot accidentally reject — rejection requires an
  explicit, exact `r`/`reject`.
- **`--auto-approve` auto-approves silently:** `gate_check(step, _output,
  auto_approve=False)` returns `"approved"` immediately when `auto_approve` is
  True (lines **81-83**, printing `⚡ Modo auto-aprove (CI).`).
  `--auto-approve` is wired from the CLI in `llc.py` (`run` line 134/186,
  `pipeline` 227/249, `wave_run` 486/495, `delta_start` 522/560) and threaded
  through the harness (`_run_delta_analysis` line 640, `_run_pipeline`
  line 675/694). Per spec anchor #8 the auto-approve path is logged/visible
  (the `⚡` print), not silent.
- There is **no timeout auto-approve** — the docstring (line 71) states
  "timeout NAO auto-aprova" and `input()` blocks indefinitely; the fail-open is
  purely the default-return, not a timer.

**Proof:**

```bash
cd /home/jcneto/Projetos/llc-audit-scratch
sed -n '68,94p' .ace/scripts/llc_harness.py
grep -n "auto_approve\|auto-approve\|gate_check(" .ace/scripts/llc.py .ace/scripts/llc_harness.py
```

**Verdict:** **bypassable (by design) / fail-open** — any input other than the
exact `r`/`reject` token approves, and `--auto-approve` approves without
interaction. This makes the gate non-blocking under ambiguity (a human who
presses Enter, mistypes, or runs in CI all get "approved"). Recorded as the
intended (permissive) behavior, not a hard defect, but worth flagging: the
"human checkpoint" provides no enforcement against an inattentive or
non-interactive operator.

---

## #6 post-wave CRITICAL block — `_post_wave_check` is a no-op returning None  (DEFECT A-02 — CRITICAL)

> **This is the hotfix evidence gate for Task 8 (A-02).** The probe output below
> is recorded verbatim.

**Trigger** (run in the LLC repo, branch `api-design-enforcement-docs`):

```bash
python3 - <<'PY'
import sys, os; sys.path.insert(0, ".ace/scripts")
os.environ.pop("LLC_PRP_NO_VERIFY", None)
import llc_wave
import pathlib
llc_wave.PRE_WAVE_CHECK_SCRIPT = pathlib.Path("/nonexistent/pre-wave-check.sh")
result = llc_wave._post_wave_check(dry_run=False, wave_num=1, prp_ids=None)
print("returned:", repr(result), "type:", type(result).__name__)
PY
```

**Observed (verbatim):**

```
returned: None type: NoneType
```

`_post_wave_check` (`.ace/scripts/llc_wave.py:514`) declares the outer
function but its **entire body is a nested `def _post_wave_check(...)`**
(`llc_wave.py:517`) that is **never called** — the outer function falls off
the end and returns `None`. The intended logic (run `pre-wave-check.sh`,
consistency-check, and `prp_verify` with a CRITICAL-exit block at
`llc_wave.py:589-629`, honoring `LLC_PRP_NO_VERIFY`) lives inside that nested
def and is unreachable dead code.

Consequence at the call site — `run_wave` `llc_wave.py:754`:

```python
if not _post_wave_check(dry_run=dry_run, wave_num=wave_num, prp_ids=prp_ids):
    logger.error(f"⛔ Wave {wave_num} — pós-onda bloqueada (prp_verify CRITICAL).")
    return False
```

`None` is falsy, so `not None == True` → `run_wave` would emit the
"pós-onda bloqueada" error and **return False** (wave reported as failed)
**regardless of the real PRP state** — the post-wave CRITICAL block neither
blocks correctly nor passes correctly; it makes every wave look blocked.
(Whether `run_wave` is reached at all depends on #7 below, which is itself
broken.)

**Proof:**

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

**Verdict:** **wrong (DEFECT A-02 — CRITICAL)** — `_post_wave_check` returns
`None` instead of `bool`; the post-wave CRITICAL block is inert and the
`if not …` guard misfires. This is the gate for hotfix Task 8.

---

## #7 pre-wave baseline check — `_pre_wave_check` is undefined (DEFECT A-01 — CRITICAL)

> **This is the hotfix evidence gate for Task 7 (A-01).** The probe output below
> is recorded verbatim.

**Trigger** (run in the LLC repo, branch `api-design-enforcement-docs`):

```bash
python3 - <<'PY'
import sys; sys.path.insert(0, ".ace/scripts")
import llc_wave
print("has _pre_wave_check:", hasattr(llc_wave, "_pre_wave_check"))
try:
    llc_wave._pre_wave_check(dry_run=True)
    print("callable: yes")
except NameError as e:
    print("NameError:", e)
except AttributeError as e:
    print("AttributeError:", e)
PY
```

**Observed (verbatim):**

```
has _pre_wave_check: False
AttributeError: module 'llc_wave' has no attribute '_pre_wave_check'
```

There is **no `def _pre_wave_check(...)`** in `llc_wave.py` at all. The
intended body (run `pre-wave-check.sh --build-only`, return False on a failed
build — `llc_wave.py:478-511`) is unreachable dead code **inside**
`_prp_to_keywords` (`llc_wave.py:454-475`): it sits **after** that function's
unconditional `return mapping.get(prp_id, [])` (`llc_wave.py:475`) and has only
a stray docstring where a `def` header should be. So the name `_pre_wave_check`
is never bound at module scope.

Consequence at the call site — `run_wave` `llc_wave.py:681`:

```python
if not _pre_wave_check(dry_run=dry_run, wave_num=wave_num):
    ...
    return False
```

Because `_pre_wave_check` is not a module global, executing line 681 raises
**`NameError`** at runtime — `run_wave` aborts before any PRP session opens.
The probe above exercises the attribute path (hence `AttributeError`); the
in-function call path would raise `NameError`. Either way the pre-wave
baseline gate does not work.

**Proof:**

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

**Verdict:** **wrong (DEFECT A-01 — CRITICAL)** — `_pre_wave_check` does not
exist; its body is dead code inside `_prp_to_keywords`, and `run_wave` would
raise `NameError` at line 681. This is the gate for hotfix Task 7.

---

## #8 backend-contract verify (API-first) — warn-by-default; blocks only on stubs

**Trigger:**

```bash
grep -n "_verify_backend_contracts\|is_stub_service\|return True\|_prp_to_keywords\|auto_approve\|return False" .ace/scripts/llc_wave.py | sed -n '1,30p'
sed -n '358,451p' .ace/scripts/llc_wave.py
```

**Observed:** `_verify_backend_contracts` (`llc_wave.py:358-451`) is the only
API-first enforcement. It is gated on `_is_ui_prp(prp_id, info)` at
`run_wave`'s call site (`llc_wave.py:723`) — i.e. only Trilha B (UI) PRPs are
checked. Behavior:

- **`dry_run` → returns True** (no check) — `llc_wave.py:370-372`.
- **No `api/` contracts and no OpenAPI/Swagger spec found → warns and
  `return True`** (`llc_wave.py:432-439`, comment "Don't block, just warn -
  could be a new project"). **API-first is warn-by-default**, not a hard
  block — a UI PRP with zero backend contracts proceeds.
- **Stubs detected (`is_stub_service` from `consistency-check.py`) →
  `return False`** (`llc_wave.py:441-448`) → at the call site
  (`llc_wave.py:725-735`) `run_wave` returns False **unless `auto_approve`**
  is set, in which case it logs "Continuando para próximo PRP (auto-approve)"
  and skips that PRP.

PRP→service matching uses the **hardcoded `PRP-001..014` keyword map** in
`_prp_to_keywords` (`llc_wave.py:459-474`: auth/perfis/universo/planos/…).
Any PRP outside this set (e.g. `PRP-015+`, or renamed services) matches
nothing → no contracts found → warn + pass.

**Proof:**

```bash
sed -n '358,451p' .ace/scripts/llc_wave.py     # full _verify_backend_contracts
grep -n "_is_ui_prp\|_verify_backend_contracts\|auto_approve" .ace/scripts/llc_wave.py
```

**Verdict:** **works (as designed — warn-by-default)** — API-first is the sole
enforcement, it does not block on missing contracts (warns + returns True),
and only blocks on detected stubs, bypassable via `--auto-approve`. The
hardcoded PRP-001..014 map is a fragility (not a defect in enforcement per se):
PRPs outside the map silently get "no contracts found → pass".

---

## #9 prp_verify RF→file + coverage — CRITICAL blocks, WARN never blocks

**Trigger:**

```bash
python3 .ace/scripts/prp_verify.py --prp PRP-001 --strict --json 2>&1 \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print({k:d.get(k) for k in ('critical','warnings','exit')})" 2>/dev/null \
  || echo "non-json or error"
python3 .ace/scripts/prp_verify.py --prp PRP-001 --strict --json 2>&1 | head -3; echo "exit=${PIPESTATUS[0]}"
```

**Observed (verbatim raw):**

```
❌ PRP não encontrado: PRP-001
exit=1
```

The JSON summary parse printed `non-json or error` because on this baseline
`prp_verify` emits the human-readable `❌ PRP não encontrado: PRP-001` and
exits **1** (PRP-not-found), not **2** (CRITICAL). There is no `.ace/prps/`
directory in the LLC repo and no target PRPs, so the CRITICAL-exit (`== 2`)
path — the one that blocks via #4 (`_run_prp_verify` returns True only on
`returncode == 2`, `llc_harness.py:252`) — is **not exercisable here**.

Enforcement semantics (confirmed by inspection of `prp_verify.py` + the #4
evidence in part 1): exit codes are **0 = clean**, **1 = PRP-not-found /
non-CRITICAL**, **2 = CRITICAL pendências**. Only exit 2 routes through
`_maybe_block_on_prp_verify` → `block_merge=True` → `gate_decision="rejected"`
(see #4). WARN-level pendências never produce exit 2 and therefore never
block. The `LLC_PRP_NO_VERIFY=1` env bypass (spec anchor #8) short-circuits
the whole check.

**Proof:**

```bash
python3 .ace/scripts/prp_verify.py --prp PRP-001 --strict --json; echo "exit=$?"   # 1 (PRP not found)
grep -n "returncode == 2\|CRITICAL\|return True\|return False" .ace/scripts/llc_harness.py | head
```

**Verdict:** **not-exercisable-on-this-baseline** (semantics confirmed by
inspection). The LLC repo has no PRPs, so `prp_verify` cannot exit 2 here.
The blocking semantics (exit 2 → block via #4; WARN → exit 0/1 → no block;
`LLC_PRP_NO_VERIFY=1` bypass) are sound per source. (Live confirmation of the
exit-2 path requires a repo with a real PRP carrying CRITICAL pendências.)

---

## #10 fitness block/warn policy — block/hybrid exit 1 without --strict; no env bypass

**Trigger:**

```bash
grep -n "mode\|core_modules\|blocked\|--strict" .ace/arch-config.yaml | head
python3 .ace/scripts/fitness-functions.py --all --json 2>&1 \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('blocked:', d.get('blocked'), 'warnings:', len(d.get('warnings',[])))" 2>/dev/null \
  || echo "see raw/fitness-functions.json"
sed -n '1882,1886p' .ace/scripts/fitness-functions.py
grep -n "LLC_PRP_NO_VERIFY\|os.environ.get\|getenv" .ace/scripts/fitness-functions.py
```

**Observed:** `.ace/arch-config.yaml` configures per-check `mode`: `block` /
`hybrid` (block for `core_modules`, warn otherwise) / `warn`. The live run on
this baseline (LLC repo, which has **0 services**) returned:

```
blocked: None warnings: 0
exit=0
```

(The brief's one-liner read a top-level `blocked` key, which is `None`; the
real per-check `blocked` flags nest under `results`, and the aggregate lives
in `summary.blocked` — `fitness-functions.py:1866`. With 0 services all
checks pass, so nothing blocks. This is expected — the tool targets a built
LLC project, not LLC's own repo.)

Exit-code policy (`fitness-functions.py:1882-1885`):

```python
has_blocks = output["summary"]["blocked"]
has_strict_fail = args.strict and (has_blocks or output["summary"]["warnings"] > 0)
sys.exit(1 if has_strict_fail or has_blocks else 0)
```

So: **`mode: block` or `mode: hybrid` violating a `core_module` → `has_blocks`
True → exit 1 even without `--strict`**; `mode: warn` → `has_blocks` False and
(without `--strict`) exit 0, surfacing only as visible `🟡` text.
`--strict` additionally turns warnings into exit 1. There is **no env bypass**
for fitness (spec anchor #8): `grep` for `LLC_PRP_NO_VERIFY` /
`os.environ.get` / `getenv` in `fitness-functions.py` returns nothing. The
only override is the CLI-level `--strict` flag and the (advisory) #3 wiring
in `pre-commit.sh`, which discards fitness output.

**Proof:**

```bash
python3 .ace/scripts/fitness-functions.py --all --json > /tmp/fit.json; echo "exit=$?"
python3 -c "import json;d=json.load(open('/tmp/fit.json'));print('summary:',d['summary'])"
sed -n '1882,1886p' .ace/scripts/fitness-functions.py
```

**Verdict:** **works (policy sound; scans-empty on this baseline)** —
block/hybrid core-module violations force exit 1 without `--strict`; warn mode
is advisory unless `--strict`; no env bypass exists. Could not produce a live
block on LLC's repo (0 services), so the exit-1 path rests on the static
evidence above.

---

## #11 test-coverage gate (CLI) — checklist + human checkpoint only

**Trigger:**

```bash
grep -n "test-coverage\|10.8\|gate_run\|gate_check\|GATE_ALIASES\|_show_gate_checklist" .ace/scripts/llc.py | head
sed -n '345,425p' .ace/scripts/llc.py
```

**Observed:** The test-coverage gate has **three names for one gate**: the
guide calls it `10-COVERAGE`, the config alias is `10.8`, and the CLI alias is
`test-coverage` (`llc.py:45` `"test-coverage": "10.8"`, `llc.py:88` `"10.8": {…}`).
`llc gate run --gate test-coverage` resolves the alias (`_get_gate_id`) and
then (`llc.py:408-425` `gate_run`):

1. in `--dry-run`: calls `_show_gate_checklist(gate_id)` — **prints the
   checklist and returns**;
2. otherwise: prints "🔍 Validando Gate …" and calls
   `decision = gate_check(gate_id, prp)` — the **human checkpoint** from #13,
   which (per #13) defaults to `approved` on any non-`r`/`reject` input and
   auto-approves under `--auto-approve`.

So `llc gate run --gate test-coverage` does **not** measure coverage itself —
it only displays the checklist and waits for a human A/R. The real coverage
enforcement lives elsewhere: `prp_verify.check_project_coverage`, invoked on
the CRITICAL path of #9 (and thus routed through #4's merge block). The CLI
gate is a prompt, not a meter.

**Proof:**

```bash
sed -n '345,425p' .ace/scripts/llc.py     # _show_gate_checklist + gate_run
grep -n '"test-coverage"\|"10.8"\|check_project_coverage' .ace/scripts/llc.py .ace/scripts/prp_verify.py
```

**Verdict:** **inert (checklist-only)** — `llc gate run --gate test-coverage`
prints the checklist + defers to the (fail-open) human `gate_check`; the
actual coverage threshold is enforced by `prp_verify.check_project_coverage`
(#9), not by this command. The 3-names-for-one-gate split (`10-COVERAGE` /
`10.8` / `test-coverage`) is a documentation/UX hazard.

---

## #12 smart-skip — no guardrail: any DELTA_REPORT skip is honored (MEDIUM)

**Trigger:**

```bash
grep -n "skip_steps\|is_step_skipped\|sempre\|always\|DELTA_REPORT\|always_exec\|protected" .ace/scripts/llc_delta.py | head
sed -n '132,175p' .ace/scripts/llc_delta.py
```

**Observed:** The skip decision (`llc_delta.py:132-143` `is_step_skipped`) is
driven **entirely** by the `skip_steps` list parsed from `DELTA_REPORT.md`:

```python
def is_step_skipped(step_id: str, delta_plan: dict | None) -> bool:
    if delta_plan is None:
        return False
    for skip in delta_plan.get("skip_steps", []):
        if skip["step_id"] == step_id:
            return True
    return False
```

There is **no validation** of the skipped step id against any allow-list, and
**no protection of "always-executed" steps**. A `grep` for `sempre` / `always`
/ `always_exec` / `protected` in `llc_delta.py` returns nothing — the code
does not encode the guide's rule that steps **10, 10.6, 10.7, 10.8, 11, 11.1,
11.2** must always run. If `DELTA_REPORT.md` lists e.g. `step_id: "11.2"` (the
PRP-acceptance gate) or `"10.8"` (coverage) under `skip_steps`,
`is_step_skipped` returns True and `generate_skip_note`
(`llc_delta.py:153-173`) even writes a note ending
`**Gate:** ✅ Auto-aprovado via Smart Skip`. So a malformed or adversarial
delta report can skip the deterministic PRP-acceptance and coverage gates,
defeating #4/#9/#11.

**Proof:**

```bash
sed -n '132,175p' .ace/scripts/llc_delta.py
grep -n "sempre\|always\|always_exec\|protected\|10.6\|10.7\|10.8\|11.1\|11.2" .ace/scripts/llc_delta.py   # → none
```

**Verdict:** **bypassable (MEDIUM)** — smart-skip trusts `DELTA_REPORT.md`
verbatim with no allowed-set check and no protection of always-executed steps;
a delta report can auto-approve-skip the PRP-acceptance (11.2) and coverage
(10.8) gates. This is a policy gap, not a mechanical bug — it needs a policy
decision (which steps are unskippable) before a hotfix, so it is escalated
rather than fixed inline.

---

## #14 replay zone-red gate — red-zone replay requires human gate-11 approval (else LLM fallback)

**Trigger:**

```bash
grep -n "is_red_zone\|red zone\|zone_red" .ace/scripts/llc_harness.py | head
sed -n '514,526p' .ace/scripts/llc_harness.py
```

**Observed:** During script replay, after architecture-version and pre-flight
checks, the harness runs the **zone check (R2)** (`llc_harness.py:514-520`):

```python
# 2c. Zone check (R2)
target_files = extract_files_from_script(script)
if any(is_red_zone(Path(f)) for f in target_files):
    print("🔴 Zona VERMELHA detectada. Gate humano necessario.")
    if gate_check(canonical_id(11), script) != "approved":
        log_replay_event("llm_fallback", None, reason="zone_red_rejected")
        return _llm_invoke(prompt, client)
```

So a replay that touches a red-zone file is **not** auto-replayed: it requires
a human `gate_check(canonical_id(11), …)` approval. If the human rejects (or,
per #13, anything other than the default-approve path), the replay **falls
back to the LLM** (`_llm_invoke`) rather than replaying the recorded script.
`is_red_zone` is imported at `llc_harness.py:108`. Note the precise semantics:
red-zone does **not** hard-stop the pipeline — it forces "human-review-OR-
regenerate-via-LLM". The recorded (potentially dangerous) script is never
silently replayed over red-zone files.

**Proof:**

```bash
sed -n '514,526p' .ace/scripts/llc_harness.py
grep -n "is_red_zone\|canonical_id(11)\|llm_fallback\|zone_red" .ace/scripts/llc_harness.py
```

**Verdict:** **works** — red-zone replay is gated behind human gate-11
approval; on rejection it falls back to LLM regeneration (and logs
`zone_red_rejected`). The recorded script is never auto-replayed into a
red-zone file. (Caveat carried from #13: the human `gate_check` is fail-open,
so an inattentive operator can still approve.)

---

## #15 consistency-check — advisory only, never blocks

**Trigger:**

```bash
grep -n "consistency-check\|consistency_check" .ace/scripts/llc_harness.py | head
sed -n '751,770p' .ace/scripts/llc_harness.py
```

**Observed:** `pipeline_run` runs `consistency-check.py` **after each step**
except the very early ones (`llc_harness.py:751-752`:
`if spec.id not in ["0", "0.1", "0.5", "1"]:`). Its output is printed to the
console (`llc_harness.py:763-768`: stdout lines echoed, stderr surfaced only
if it contains `ERRO`). But the result is **never tested** against the gate
decision: there is no `if result.returncode != 0: block/return False` — the
`except` branch (`llc_harness.py:769-770`) merely prints
`ℹ️  consistency-check não executado: …` and the loop continues to the next
step. A failing consistency-check cannot cause the pipeline to stop or a gate
to be rejected; it is purely informational. (The same advisory nature is
reproduced inside the dead `_post_wave_check` nested def, `llc_wave.py:562-585`,
which is itself unreachable — see #6.)

**Proof:**

```bash
sed -n '751,775p' .ace/scripts/llc_harness.py     # consistency-check block; no return/block on non-zero
grep -n "consistency-check" .ace/scripts/llc_harness.py
```

**Verdict:** **works (as designed — advisory)** — consistency-check runs after
each eligible step and surfaces drift, but its result is never wired to a
block; it never gates the pipeline. Matches the spec intent that
consistency-check is an advisory tooth, not a hard block.
