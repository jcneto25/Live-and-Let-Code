# Snippet — Claude Code Hooks for Guaranteed ACE Session Registration

**Purpose:** ensure every code edit happens inside an open ACE session,
**regardless of whether the agent "remembers"** to open the session.

> **Important framing:** the **tool-agnostic** mechanism that actually guarantees
> registration in `.ace` is the **git pre-commit hook**
> (`.ace/scripts/pre-commit.sh` + `validate-tags.py --coverage`) — git runs it no
> matter which AI client made the commit. The hooks below are **per-client (Claude
> Code)**: they provide enforcement/UX *during* the session, before the commit. Use
> both in layers.

## Prerequisites (in the target project)

- `.ace/scripts/` with `initialize_session.py`, `finalize_session.py`, `validate-tags.py`, `llc.py`.
- `jq` installed (to read `.ace/index.json`).
- Git pre-commit hook installed: `cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`
  (or `pre-commit install` if you use the framework).

---

## Snippet A — PreToolUse Guard (recommended)

Blocks `Edit`/`Write`/`MultiEdit` when there is **no `in_progress` session**. This is the
layer that directly prevents the "wave executed without a session" failure mode: the agent
simply cannot edit code without first opening the session.

**1. Wrapper** — copy `require-ace-session.sh` (next to this file) into the target project:

```bash
mkdir -p .ace/scripts/hooks
cp docs/templates/hooks/require-ace-session.sh .ace/scripts/hooks/require-ace-session.sh
chmod +x .ace/scripts/hooks/require-ace-session.sh
```

**2. Register it in `.claude/settings.json** (project) or `~/.claude/settings.json` (user):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .ace/scripts/hooks/require-ace-session.sh"
          }
        ]
      }
    ]
  }
}
```

With this, any attempt to edit code without an `in_progress` session is denied by the
Claude Code harness, with a message instructing the agent to open the session.

---

## Snippet B — Auto-open session on SessionStart (optional, convenience)

Automatically opens a session when the conversation starts, so the agent begins already
"inside" the ACE cycle. `--step`/`--task` come from environment variables or defaults.

`.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python .ace/scripts/initialize_session.py --step ${LLC_STEP:-11} --task \"${LLC_TASK:-auto}\" --json"
          }
        ]
      }
    ]
  }
}
```

> **Do not** automate `finalize_session.py` on `Stop`: that event fires on every agent
> stop (including mid-conversation), closing sessions prematurely. Keep `finalize`
> explicit at the actual end of the work, or rely on the pre-commit gate to guarantee
> registration.

---

## Quick install (summary)

```bash
# 1. Guard wrapper (Snippet A)
mkdir -p .ace/scripts/hooks
cp docs/templates/hooks/require-ace-session.sh .ace/scripts/hooks/
chmod +x .ace/scripts/hooks/require-ace-session.sh

# 2. Register hook(s) in .claude/settings.json (paste the JSON above)

# 3. Tool-agnostic guarantee (git pre-commit)
cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#   or: pre-commit install
```

---

## Caveats

- **The Claude Code hooks schema evolves.** The blocking mechanism via **exit code 2**
  (`require-ace-session.sh`) is the stable form; the JSON form (`permissionDecision: deny`)
  also exists, but verify the current schema in the Claude Code docs for your version.
- **Bypass:** client hooks can be disabled by the user. The layer that cannot be "forgotten"
  is the git pre-commit hook (bypassable only with `git commit --no-verify`).
- **`.claude/` is per-clone** (LLC gitignore). Place the wrapper at a versioned path
  (`.ace/scripts/hooks/`) and reference it from `.claude/settings.json`.
- **Other clients (Codex, Cursor, opencode):** each has its own equivalent hook/automation
  mechanism. The contract is the same — "require an ACE session before editing/committing
  code" — expressed in `AGENTS.md`. The git pre-commit hook covers them all.
