# P2 — Enforcement Verification Log

One section per enforcement point (#1–#15). Record observed behavior + proof command.

> Scope of this file (part 1): enforcement points **#1, #2, #3, #4, #5, #13**
> (git / pre-commit / session teeth). Points #6–#12, #14, #15 are recorded in
> part 2 (Task 4). All triggers run inside the scratch worktree
> `/home/jcneto/Projetos/llc-audit-scratch` (branch `llc-audit-scratch` @ `a519d0f`)
> unless noted. Source under `.ace/scripts/*` is READ-ONLY for this audit; no
> pipeline source was modified.
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
