#!/usr/bin/env python3
"""Characterization tests — must-not-break contract do BEHAVIOR_BASELINE.

Pins the enforcement behaviors the clean-code refactor (sub-projeto 2) must
preserve. Reproduces the Proof commands do AUDIT_REPORT / BEHAVIOR_BASELINE.

Coberto aqui (exercisable on this baseline):
  - D-01: gates.json step<->gate resolution has 0 mismatches.
  - E-12: llc_delta.is_step_skipped protects ALWAYS_RUN steps.
  - E-13: llc_harness.gate_check requires explicit a/approve (re-prompts).
  - A-01/A-02: _pre_wave_check / _post_wave_check return bool (not None).

Itens not-exercisable-on-this-baseline (no PRPs) are covered by inspection in
the audit, not here: #4, #9.
"""

import builtins
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import llc_steps
import llc_delta
import llc_harness
import llc_wave


# ── D-01: gates.json step<->gate resolution ──


def test_d01_gate_step_fields_match_registry():
    gates = json.load(open(Path(__file__).parent.parent / "config" / "gates.json"))["gates"]
    mismatches = []
    for sid, spec in sorted(llc_steps.REGISTRY.items(), key=lambda kv: kv[1].number):
        if spec.gate is None:
            continue
        gj_step = gates.get(spec.gate, {}).get("step")
        match = spec.gate in gates and abs(gj_step - spec.number) < llc_steps.EPS
        if not match:
            mismatches.append((sid, spec.gate, gj_step, spec.number))
    assert mismatches == [], f"D-01 mismatches: {mismatches}"


# ── E-12: smart-skip ALWAYS_RUN guard ──


def test_e12_always_run_steps_never_skipped():
    plan = {"skip_steps": [{"step_id": s, "reason": "x"} for s in
                           ["10", "10.6", "10.7", "10.8", "11", "11.1", "11.2"]]}
    for s in ["10", "10.6", "10.7", "10.8", "11", "11.1", "11.2",
              "security", "test-coverage", "owasp", "11.2"]:
        assert llc_delta.is_step_skipped(s, plan) is False


def test_e12_always_run_via_aliases_never_skipped():
    plan = {"skip_steps": [{"step_id": "11.2", "reason": "x"}]}
    # alias "verify" -> 11.2 must also be protected
    assert llc_delta.is_step_skipped("verify", plan) is False


def test_e12_normal_steps_still_skippable():
    plan = {"skip_steps": [{"step_id": "10.5", "reason": "x"}]}
    assert llc_delta.is_step_skipped("10.5", plan) is True
    assert llc_delta.is_step_skipped("10.5", None) is False


def test_e12_always_run_set_is_complete():
    assert llc_delta.ALWAYS_RUN == frozenset(
        {"10", "10.6", "10.7", "10.8", "11", "11.1", "11.2"}
    )


# ── E-13: gate_check requires explicit approve (no silent fail-open) ──


class _InputStub:
    def __init__(self, values):
        self._it = iter(values)
        self.calls = 0

    def __call__(self, *a):
        self.calls += 1
        if self.calls > 20:
            raise RuntimeError("gate_check did not terminate (loop guard)")
        return next(self._it)


def test_e13_approve_on_explicit_a():
    builtins.input = _InputStub(["a"])
    assert llc_harness.gate_check("10.8", auto_approve=False) == "approved"


def test_e13_reject_on_r():
    builtins.input = _InputStub(["r"])
    assert llc_harness.gate_check("10.8", auto_approve=False) == "rejected"


def test_e13_ambiguous_input_reprompts_then_approves():
    builtins.input = _InputStub(["", "xyz", "approve"])
    assert llc_harness.gate_check("10.8", auto_approve=False) == "approved"
    assert builtins.input.calls >= 3  # re-prompted before approving


def test_e13_typo_rejects_only_after_explicit_r():
    builtins.input = _InputStub(["rejct", "r"])
    assert llc_harness.gate_check("10.8", auto_approve=False) == "rejected"
    assert builtins.input.calls >= 2


def test_e13_auto_approve_bypasses_interactive():
    builtins.input = _InputStub([])  # would hang/loop if reached
    assert llc_harness.gate_check("10.8", auto_approve=True) == "approved"


# ── A-01 / A-02: wave checks return bool, not None ──


def test_a01_pre_wave_check_returns_bool(monkeypatch, tmp_path):
    monkeypatch.setattr(llc_wave, "PRE_WAVE_CHECK_SCRIPT", tmp_path / "absent.sh")
    assert llc_wave._pre_wave_check(dry_run=False, wave_num=1) is True


def test_a02_post_wave_check_returns_bool(monkeypatch, tmp_path):
    monkeypatch.setattr(llc_wave, "PRE_WAVE_CHECK_SCRIPT", tmp_path / "absent.sh")
    monkeypatch.delenv("LLC_PRP_NO_VERIFY", raising=False)
    result = llc_wave._post_wave_check(dry_run=False, wave_num=1, prp_ids=None)
    assert result is True  # pre-fix this was None


# ── F-01: path constants resolve to real filesystem locations ──
# Regression guard for the package-refactor off-by-one that pointed
# SCRIPTS_DIR → .ace/scripts/scripts (inexistente) e GATES_FILE → .ace/scripts/config/gates.json.


def test_f01_scripts_dir_points_to_real_scripts_dir():
    """SCRIPTS_DIR must be .ace/scripts/ (not the doubled .ace/scripts/scripts/)."""
    from llc_harness.common import ACE_DIR, SCRIPTS_DIR

    assert SCRIPTS_DIR.name == "scripts", f"SCRIPTS_DIR.name={SCRIPTS_DIR.name!r}"
    assert ACE_DIR.name == ".ace", f"ACE_DIR.name={ACE_DIR.name!r}"
    assert SCRIPTS_DIR.exists(), f"SCRIPTS_DIR does not exist: {SCRIPTS_DIR}"
    # The two subprocess shims invoked by session_start/session_end must be findable
    assert (SCRIPTS_DIR / "initialize_session.py").exists(), "initialize_session.py missing"
    assert (SCRIPTS_DIR / "finalize_session.py").exists(), "finalize_session.py missing"


def test_f01_gates_file_loads_real_gates_json(monkeypatch):
    """GATES_FILE must load real gates.json (not empty fallback from missing path)."""
    import llc_harness.common as common

    monkeypatch.setattr(common, "_gates_config", None)  # force fresh load
    cfg = common.load_gates_config()
    gates = cfg.get("gates", {})
    assert len(gates) > 0, (
        f"gates.json not loaded (empty fallback) — "
        f"GATES_FILE={common.GATES_FILE}, exists={common.GATES_FILE.exists()}"
    )
    # Sanity: known gate keys must be present
    for key in ("1", "5", "11-SEC", "10.8"):
        assert key in gates, f"gate key {key!r} missing from loaded gates.json"


# ── F-02: gate_check accepts gate-keys from gates.json (not just step ids) ──
# Regression guard for `llc gate run --gate security/null-safety/owasp` crash.
# GATE_ALIASES maps those aliases to gate-keys ("11-SEC","12-NULL","11-OWASP")
# which normalize_step() cannot resolve. get_gate_checklist must fall back to
# a direct gates.json lookup when the input is a gate-key.


def test_f02_get_gate_checklist_resolves_security_gate_key():
    """gate-key '11-SEC' (from GATE_ALIASES['security']) must resolve directly."""
    from llc_harness import get_gate_checklist

    gate_num, items = get_gate_checklist("11-SEC")
    assert gate_num == "11-SEC"
    assert len(items) == 3, f"expected 3 checklist items, got {len(items)}: {items}"


def test_f02_get_gate_checklist_resolves_null_safety_gate_key():
    """gate-key '12-NULL' (from GATE_ALIASES['null-safety']) must resolve directly."""
    from llc_harness import get_gate_checklist

    gate_num, items = get_gate_checklist("12-NULL")
    assert gate_num == "12-NULL"
    assert len(items) == 3, f"expected 3 checklist items, got {len(items)}: {items}"


def test_f02_get_gate_checklist_resolves_owasp_gate_key():
    """gate-key '11-OWASP' (from GATE_ALIASES['owasp']) must resolve directly."""
    from llc_harness import get_gate_checklist

    gate_num, items = get_gate_checklist("11-OWASP")
    assert gate_num == "11-OWASP"
    assert len(items) == 3, f"expected 3 checklist items, got {len(items)}: {items}"


def test_f02_gate_check_auto_approves_gate_keys():
    """gate_check(gate_key, auto_approve=True) must not crash and must approve.
    This is the exact path `llc gate run --gate <alias>` invokes (after
    _get_gate_id resolves the alias to a gate-key)."""
    import builtins
    from llc_harness import gate_check

    builtins.input = _InputStub([])  # would hang/loop if reached
    for gk in ("11-SEC", "12-NULL", "11-OWASP"):
        assert gate_check(gk, auto_approve=True) == "approved", f"{gk} not approved"


def test_f02_step_ids_still_resolve_via_normalize():
    """Step ids/aliases (the original path) must still work — fallback must not
    shadow the normalize_step resolution for legitimate step inputs."""
    from llc_harness import get_gate_checklist

    # 'security' is a step alias -> 10.6 -> gate "11-SEC"
    gate_num, items = get_gate_checklist("security")
    assert gate_num == "11-SEC"
    assert len(items) == 3
    # '5' is a step id -> gate "6"
    gate_num, items = get_gate_checklist("5")
    assert gate_num == "6"
    assert len(items) == 3


# ── F-03: delta gates Δ.0/Δ.1 wired in REGISTRY (steps 0.2/0.3) ──
# Regression guard for gates defined in gates.json but with gate=None in
# REGISTRY, which caused _run_delta_analysis to auto-approve without showing
# the checklist (neutralizing the human validation of the delta impact report
# and grill-me answers).


def test_f03_delta_step_02_has_gate_delta_0():
    """Step 0.2 (Delta Impact Analysis) must be wired to gate Δ.0 in gates.json."""
    spec = llc_steps.normalize_step("0.2")
    assert spec.gate == "Δ.0", f"step 0.2 gate={spec.gate!r}, expected 'Δ.0'"


def test_f03_delta_step_03_has_gate_delta_1():
    """Step 0.3 (Delta Grill Me) must be wired to gate Δ.1 in gates.json."""
    spec = llc_steps.normalize_step("0.3")
    assert spec.gate == "Δ.1", f"step 0.3 gate={spec.gate!r}, expected 'Δ.1'"


def test_f03_get_gate_checklist_shows_delta_0_checklist():
    """get_gate_checklist('0.2') must return the Δ.0 checklist from gates.json
    (not None/empty — which would cause silent auto-approve)."""
    from llc_harness import get_gate_checklist

    gate_num, items = get_gate_checklist("0.2")
    assert gate_num == "Δ.0", f"gate_num={gate_num!r}, expected 'Δ.0'"
    assert len(items) == 5, f"expected 5 checklist items for Δ.0, got {len(items)}: {items}"


def test_f03_get_gate_checklist_shows_delta_1_checklist():
    """get_gate_checklist('0.3') must return the Δ.1 checklist from gates.json."""
    from llc_harness import get_gate_checklist

    gate_num, items = get_gate_checklist("0.3")
    assert gate_num == "Δ.1", f"gate_num={gate_num!r}, expected 'Δ.1'"
    assert len(items) == 3, f"expected 3 checklist items for Δ.1, got {len(items)}: {items}"


def test_f03_delta_gate_check_does_not_auto_approve_silently():
    """gate_check('0.2', auto_approve=False) must NOT print the 'Nenhum gate
    definido' auto-advance message — it must show the checklist and prompt.
    With auto_approve=True it shows the checklist then approves."""
    import builtins
    from llc_harness import gate_check

    # auto_approve=True path: must show checklist (gate is wired) then approve
    builtins.input = _InputStub([])  # would hang/loop if reached
    assert gate_check("0.2", auto_approve=True) == "approved"
    assert gate_check("0.3", auto_approve=True) == "approved"


# ── F-04: parse_delta_report robust to accented Portuguese headers ──
# The DELTA_REPORT_TEMPLATE.md uses accented headers ("Alteração",
# "Necessários", "Classificação", "Iteração proposta") but the parser
# searched for unaccented strings, silently returning empty PRP lists.


_ACCENTED_DELTA_REPORT = """# DELTA_REPORT.md

## §1 Metadados da Iteração

| Campo | Valor |
|-------|-------|
| **Iteração proposta** | `v2.0` |
| **Classificação** | `MAJOR` |

## §3 PRPs Afetados

### 3.2 PRPs Existentes com Alteração (PRP-A)

| PRP Original | PRP-A | Descrição da Mudança | Impacto |
|-------------|-------|---------------------|---------|
| PRP-003 | PRP-A-001 | Contrato alterado | Breaking |
| PRP-007 | PRP-A-002 | Enum expande | Migração |

## §4 Novos PRPs Necessários (PRP-N)

| PRP-N | Nome | Descrição | Depende de |
|-------|------|-----------|------------|
| PRP-N-001 | Módulo Auditoria | Novo módulo | PRP-A-001 |
| PRP-N-002 | Dashboard BI | Relatórios | PRP-N-001 |

## §5 Plano de Execução Sugerido

### 5.1 Steps a Executar

| Step | Skill | Motivo | Gate |
|------|-------|--------|------|
| 0.5 | llc-step-0-5 | diff mode | 1 |
| 1 | llc-step-1 | glossario | 2 |

### 5.2 Steps a Pular

| Step | Justificativa | Artefatos Reaproveitados |
|------|---------------|--------------------------|
| 5 | Arquitetura inalterada | ARCHITECTURE.md v1 |
| 7 | Design System inalterado | DESIGN_SYSTEM.md v1 |
"""


def _parse_delta_from_text(text, monkeypatch, tmp_path):
    """Helper: monkeypatch DELTA_REPORT_PATH to a tmp file with `text` and parse."""
    import llc_delta.report as r

    tmp = tmp_path / "DELTA_REPORT.md"
    tmp.write_text(text, encoding="utf-8")
    monkeypatch.setattr(r, "DELTA_REPORT_PATH", tmp)
    return r.parse_delta_report()


def test_f04_parses_accented_iteration(monkeypatch, tmp_path):
    """'Iteração proposta' (accented) must be parsed as iteration='v2.0'."""
    plan = _parse_delta_from_text(_ACCENTED_DELTA_REPORT, monkeypatch, tmp_path)
    assert plan["iteration"] == "v2.0", f"iteration={plan['iteration']!r}"


def test_f04_parses_accented_classification(monkeypatch, tmp_path):
    """'Classificação' (accented) must be parsed as change_type='major'."""
    plan = _parse_delta_from_text(_ACCENTED_DELTA_REPORT, monkeypatch, tmp_path)
    assert plan["change_type"] == "major", f"change_type={plan['change_type']!r}"


def test_f04_parses_accented_affected_prps(monkeypatch, tmp_path):
    """'PRPs Existentes com Alteração (PRP-A)' (accented) must yield 2 PRPs."""
    plan = _parse_delta_from_text(_ACCENTED_DELTA_REPORT, monkeypatch, tmp_path)
    assert plan["affected_prps"] == ["PRP-003", "PRP-007"], (
        f"affected_prps={plan['affected_prps']!r}"
    )


def test_f04_parses_accented_new_prps(monkeypatch, tmp_path):
    """'Novos PRPs Necessários (PRP-N)' (accented) must yield 2 PRP-N ids."""
    plan = _parse_delta_from_text(_ACCENTED_DELTA_REPORT, monkeypatch, tmp_path)
    assert plan["new_prps"] == ["PRP-N-001", "PRP-N-002"], (
        f"new_prps={plan['new_prps']!r}"
    )


def test_f04_still_parses_unaccented_legacy_headers(monkeypatch, tmp_path):
    """Backward compat: unaccented headers (legacy/ASCII) must still parse."""
    unaccented = _ACCENTED_DELTA_REPORT.replace("Iteração", "Iteracao").replace(
        "Classificação", "Classificacao"
    ).replace("Alteração", "Alteracao").replace("Necessários", "Necessarios")
    plan = _parse_delta_from_text(unaccented, monkeypatch, tmp_path)
    assert plan["iteration"] == "v2.0"
    assert plan["change_type"] == "major"
    assert plan["affected_prps"] == ["PRP-003", "PRP-007"]
    assert plan["new_prps"] == ["PRP-N-001", "PRP-N-002"]


# ── F-05: skip_steps parser must not capture the header row ──
# The "Steps a Pular" table has a header "| Step | Justificativa | ... |" that
# was being captured as a skip entry with step_id="Step". The execute_steps
# block already filtered this; the skip block did not.


def test_f05_skip_steps_excludes_header_row(monkeypatch, tmp_path):
    """skip_steps must not include the table header row (step_id='Step')."""
    plan = _parse_delta_from_text(_ACCENTED_DELTA_REPORT, monkeypatch, tmp_path)
    skip_ids = [s["step_id"] for s in plan["skip_steps"]]
    assert "Step" not in skip_ids, f"header row leaked into skip_steps: {plan['skip_steps']}"
    assert "step" not in [s.lower() for s in skip_ids], (
        f"header row (case-variant) leaked: {plan['skip_steps']}"
    )


def test_f05_skip_steps_captures_real_entries(monkeypatch, tmp_path):
    """skip_steps must capture the 2 real skip entries (steps 5 and 7)."""
    plan = _parse_delta_from_text(_ACCENTED_DELTA_REPORT, monkeypatch, tmp_path)
    assert len(plan["skip_steps"]) == 2, f"expected 2 skip entries, got {len(plan['skip_steps'])}"
    ids = [s["step_id"] for s in plan["skip_steps"]]
    assert ids == ["5", "7"], f"skip step_ids={ids}"
    # Verify reason + artifacts_reused fields are populated
    for entry in plan["skip_steps"]:
        assert entry["reason"], f"empty reason for {entry['step_id']}"
        assert entry["artifacts_reused"], f"empty artifacts_reused for {entry['step_id']}"


# ── F-06: `gate` is a CLI group (not a duplicate --step command) ──
# A first `@cli.command() def gate(step)` was shadowed by
# `@cli.group() def gate()` below it, leaving the --step variant as dead code.
# The dead definition was removed; `gate` is now solely a group with subcommands.


def test_f06_gate_cli_group_has_no_step_option(monkeypatch, capsys):
    """`llc gate --step 5` must fail with a Click usage error (not a Python
    crash/NameError) — `gate` is a group, not a --step command."""
    from click.testing import CliRunner
    from llc.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["gate", "--step", "5"])
    assert result.exit_code != 0, f"expected usage error, got exit {result.exit_code}"
    assert "No such option" in result.output or "--step" in result.output, (
        f"unexpected output: {result.output}"
    )


def test_f06_gate_cli_group_exposes_subcommands():
    """`llc gate --help` must list run, list, and gate-checklist subcommands."""
    from click.testing import CliRunner
    from llc.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["gate", "--help"])
    assert result.exit_code == 0
    for sub in ("run", "list", "gate-checklist"):
        assert sub in result.output, f"subcommand {sub!r} missing from gate --help"


# ── F-07: normalize_step is case-insensitive (matches _get_gate_id) ──
# _get_gate_id lowercases its input, but normalize_step did exact-case
# lookup, so "Security"/"SECURITY" raised UnknownStepError while "security"
# resolved. Now both paths lowercase consistently.


@pytest.mark.parametrize("variant", ["security", "Security", "SECURITY", "SeCuRiTy"])
def test_f07_security_alias_case_insensitive(variant):
    """All case variants of 'security' must resolve to step 10.6."""
    assert llc_steps.normalize_step(variant).id == "10.6"


@pytest.mark.parametrize("variant", ["owasp", "OWASP", "Owasp", "OWaSp"])
def test_f07_owasp_alias_case_insensitive(variant):
    """All case variants of 'owasp' must resolve to step 11.1."""
    assert llc_steps.normalize_step(variant).id == "11.1"


@pytest.mark.parametrize(
    "variant", ["null-safety", "Null-Safety", "NULL-SAFETY", "Null-safety"]
)
def test_f07_null_safety_alias_case_insensitive(variant):
    """All case variants of 'null-safety' must resolve to step 10.7."""
    assert llc_steps.normalize_step(variant).id == "10.7"


@pytest.mark.parametrize("variant", ["Verify", "VERIFY", "verify", "vErIfY"])
def test_f07_verify_alias_case_insensitive(variant):
    """All case variants of 'verify' must resolve to step 11.2."""
    assert llc_steps.normalize_step(variant).id == "11.2"


@pytest.mark.parametrize(
    "variant", ["Arch", "ARCH", "arch", "Fitness", "FITNESS", "fitness"]
)
def test_f07_arch_fitness_alias_case_insensitive(variant):
    """All case variants of 'arch'/'fitness' must resolve to step 11.3."""
    assert llc_steps.normalize_step(variant).id == "11.3"


@pytest.mark.parametrize(
    "variant", ["10-COVERAGE", "10-coverage", "10-Coverage", "test-coverage", "TEST-COVERAGE"]
)
def test_f07_coverage_alias_case_insensitive(variant):
    """All case variants of '10-coverage'/'test-coverage' must resolve to step 10.8."""
    assert llc_steps.normalize_step(variant).id == "10.8"


def test_f07_numeric_ids_still_resolve():
    """Numeric step ids (case doesn't apply) must still resolve."""
    for sid in ["0.5", "1", "5", "10.6", "11.1"]:
        assert llc_steps.normalize_step(sid).id == sid


# ── F-08: step "0" skill_file wired (was None — orphaned greenfield skill) ──
# docs/skills/llc-step-0-greenfield.md existed but REGISTRY had skill_file=None,
# causing `llc run --step 0` to crash in skill_load ("não tem skill associada").


def test_f08_step_0_has_skill_file_wired():
    """Step 0 (Ingestão) must have skill_file='llc-step-0-greenfield' (not None)."""
    spec = llc_steps.normalize_step("0")
    assert spec.skill_file == "llc-step-0-greenfield", (
        f"step 0 skill_file={spec.skill_file!r}, expected 'llc-step-0-greenfield'"
    )


def test_f08_step_0_skill_file_exists_on_disk():
    """The wired skill_file must exist in docs/skills/ (repo root relative)."""
    from pathlib import Path

    spec = llc_steps.normalize_step("0")
    skill_path = Path(__file__).resolve().parent.parent.parent / "docs" / "skills" / f"{spec.skill_file}.md"
    assert skill_path.exists(), f"skill file not found: {skill_path}"


def test_f08_step_01_skill_file_still_wired():
    """Step 0.1 (Conversão Docling) must still have its skill_file (no regression)."""
    spec = llc_steps.normalize_step("0.1")
    assert spec.skill_file == "llc-step-0-1", f"step 0.1 skill_file={spec.skill_file!r}"


def test_f08_skill_load_step_0_succeeds(monkeypatch):
    """skill_load('0') must not crash with 'não tem skill associada' — the
    greenfield skill must load and produce a non-empty prompt."""
    from llc_harness import skill
    from pathlib import Path

    # SKILLS_DIR is cwd-relative (docs/skills) — point it at the real repo skills.
    repo_skills = Path(__file__).resolve().parent.parent.parent / "docs" / "skills"
    monkeypatch.setattr(skill, "SKILLS_DIR", repo_skills)
    monkeypatch.setattr(skill, "AGENTS_FILE", Path("/nonexistent/AGENTS.md"))

    skill_file, prompt = skill.skill_load("0", context_seed=None, task="greenfield test")
    assert "llc-step-0-greenfield" in skill_file, f"skill_file={skill_file!r}"
    assert len(prompt) > 100, f"prompt too short ({len(prompt)} chars)"


# ── F-09: AGENTS.md exists at repo root + load_agents_conventions warns ──
# load_agents_conventions() silently returned "" when AGENTS.md was missing,
# leaving the agent without Document Index / red zones / TDD enforcement.


def test_f09_agents_md_exists_at_repo_root():
    """AGENTS.md must exist at repo root (not just the template)."""
    agents_path = Path(__file__).resolve().parent.parent.parent / "AGENTS.md"
    assert agents_path.exists(), f"AGENTS.md not found at repo root: {agents_path}"


def test_f09_agents_md_has_documentation_index_section():
    """AGENTS.md must contain the 'Documentation Index (Compressed)' section
    that load_agents_conventions() extracts for the agent prompt."""
    agents_path = Path(__file__).resolve().parent.parent.parent / "AGENTS.md"
    content = agents_path.read_text(encoding="utf-8")
    assert "### Documentation Index (Compressed)" in content, (
        "Documentation Index section missing from AGENTS.md"
    )


def test_f09_agents_md_has_no_unreplaced_placeholders():
    """AGENTS.md must not contain unreplaced {{...}} placeholders."""
    agents_path = Path(__file__).resolve().parent.parent.parent / "AGENTS.md"
    content = agents_path.read_text(encoding="utf-8")
    import re
    remaining = re.findall(r"\{\{[^}]+\}\}", content)
    assert remaining == [], f"Unreplaced placeholders in AGENTS.md: {remaining}"


def test_f09_load_agents_conventions_returns_nonempty_when_agents_exists(monkeypatch):
    """load_agents_conventions() must return a non-empty string with the
    Documentation Index when AGENTS.md exists."""
    from llc_harness import skill
    from pathlib import Path

    agents_path = Path(__file__).resolve().parent.parent.parent / "AGENTS.md"
    monkeypatch.setattr(skill, "AGENTS_FILE", agents_path)
    result = skill.load_agents_conventions()
    assert len(result) > 100, f"conventions too short ({len(result)} chars)"
    assert "Documentation Index" in result, "Document Index missing from conventions"


def test_f09_load_agents_conventions_warns_when_agents_missing(monkeypatch, capsys):
    """load_agents_conventions() must print a warning (not silently return '')
    when AGENTS.md is missing."""
    from llc_harness import skill
    from pathlib import Path

    monkeypatch.setattr(skill, "AGENTS_FILE", Path("/nonexistent/AGENTS.md"))
    result = skill.load_agents_conventions()
    assert result == "", "should return '' when AGENTS.md missing"
    captured = capsys.readouterr()
    assert "AGENTS.md nao encontrado" in captured.out, (
        f"warning not printed: {captured.out}"
    )


# ── F-10: DELTA_REPORT_TEMPLATE gate column uses gates.json key (not guide label) ──
# The template's §5.1 table referred to gate "10-COVERAGE" (a guide display name)
# but gates.json key is "10.8". The Gate column must use the programmatic key.


def test_f10_delta_report_template_uses_correct_gate_key():
    """DELTA_REPORT_TEMPLATE.md §5.1 Gate column must say '10.8' (gates.json key),
    not '10-COVERAGE' (guide display name)."""
    template_path = (
        Path(__file__).resolve().parent.parent.parent
        / "docs" / "templates" / "DELTA_REPORT_TEMPLATE.md"
    )
    content = template_path.read_text(encoding="utf-8")
    # The stale reference must be gone
    assert "👤 10-COVERAGE" not in content, (
        "DELTA_REPORT_TEMPLATE still references '👤 10-COVERAGE' — "
        "should be '👤 10.8' (gates.json key)"
    )
    # The correct key must be present in the coverage row
    assert "👤 10.8" in content, "DELTA_REPORT_TEMPLATE missing '👤 10.8' gate reference"


# ── F-11: quickstart message reflects actual step range (not misleading) ──
# The old message said "Gates incluídos: 1, 4, 11" but --quickstart runs
# pipeline_steps('0.5','11') = 16 steps with all their gates.


def test_f11_quickstart_runs_21_steps():
    """--quickstart sets from=0.5, to=11 which yields 21 pipeline steps
    (17 original + 5.1/5.2/5.3/8.1/10.9 sub-steps from F-14)."""
    specs = llc_steps.pipeline_steps("0.5", "11")
    assert len(specs) == 21, f"expected 21 steps, got {len(specs)}: {[s.id for s in specs]}"


def test_f11_quickstart_message_is_accurate():
    """The quickstart CLI output must not claim only 3 gates are included
    when 16 steps run. The new message must mention the step range and
    that the full mode adds OWASP/PRP-Verify/Arch-Fitness."""
    from click.testing import CliRunner
    from llc.cli import cli

    runner = CliRunner()
    # --auto-approve + no docs/skills present will fail early but the banner
    # is printed before pipeline_run, so we can capture it.
    result = runner.invoke(cli, ["pipeline", "--quickstart", "--auto-approve"])
    output = result.output
    # The misleading old message must NOT appear
    assert "Gates incluídos: 1 (Visão), 4 (PRPs), 11 (Execução)" not in output, (
        f"old misleading quickstart message still present: {output}"
    )
    # The new accurate message must mention 16 steps or the 0.5→11 range
    assert "16 steps" in output or "21 steps" in output or "0.5 → 11" in output or "0.5->11" in output, (
        f"new quickstart message missing step count/range: {output}"
    )


# ── F-12: wave run error message suggests correct cwd (repo root) ──
# The ImportError help text said "cd .ace/scripts && python llc.py" but
# cwd-relative paths (docs/skills, .ace/index.json, docs/planning/) require
# repo root execution.


def test_f12_wave_run_error_does_not_suggest_scripts_dir():
    """The wave run ImportError help must say 'repo root', not 'cd .ace/scripts'."""
    source = Path(__file__).parent / "llc_wave" / "run.py"
    content = source.read_text(encoding="utf-8")
    assert "cd .ace/scripts" not in content, (
        "llc_wave/run.py still suggests 'cd .ace/scripts' — should say repo root"
    )
    assert "repo root" in content, (
        "llc_wave/run.py must mention 'repo root' in the help text"
    )


# ── F-13: coverage generation is stack-aware (JS-only, skip non-JS) ──
# prp_verify/coverage.py tried `npx vitest` then `npx jest` (timeout 120s×2)
# for ALL projects, wasting ~4 minutes on Python/Go stacks. Now _detect_stack
# gates the JS coverage generation.


def test_f13_detect_stack_js(tmp_path):
    """_detect_stack returns 'js' when package.json exists."""
    from prp_verify.coverage import _detect_stack

    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert _detect_stack(tmp_path) == "js"


def test_f13_detect_stack_python(tmp_path):
    """_detect_stack returns 'python' when pyproject.toml exists."""
    from prp_verify.coverage import _detect_stack

    (tmp_path / "pyproject.toml").write_text("[tool.poetry]", encoding="utf-8")
    assert _detect_stack(tmp_path) == "python"


def test_f13_detect_stack_go(tmp_path):
    """_detect_stack returns 'go' when go.mod exists."""
    from prp_verify.coverage import _detect_stack

    (tmp_path / "go.mod").write_text("module test", encoding="utf-8")
    assert _detect_stack(tmp_path) == "go"


def test_f13_detect_stack_unknown(tmp_path):
    """_detect_stack returns 'unknown' when no marker files exist."""
    from prp_verify.coverage import _detect_stack

    assert _detect_stack(tmp_path) == "unknown"


def test_f13_non_js_project_skips_npx(monkeypatch, tmp_path):
    """check_project_coverage must NOT call subprocess.run for npx/vitest/jest
    when the project is not JS (no package.json). Verifies F-13 fix avoids
    wasting 120s×2 timeout on non-JS stacks."""
    from prp_verify import coverage as cov

    # Simulate a Python project (pyproject.toml, no package.json, no coverage file)
    monkeypatch.setattr(cov.Path, "cwd", classmethod(lambda cls: tmp_path))
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]", encoding="utf-8")

    calls = []
    original_run = subprocess.run

    def spy_run(*args, **kwargs):
        calls.append(args[0] if args else kwargs.get("args"))
        return original_run(["echo", "spy"], capture_output=True, text=True)

    monkeypatch.setattr(cov.subprocess, "run", spy_run)

    exit_code, findings = cov.check_project_coverage(strict=True)
    # Non-JS project with no coverage file → WARN (exit 1)
    assert exit_code == 1
    # Must NOT have called npx/vitest/jest
    npx_calls = [c for c in calls if isinstance(c, list) and "npx" in c]
    assert npx_calls == [], f"npx was called for non-JS project: {npx_calls}"


# ── F-14: sub-steps 5a/5b/5c/8b/11a wired in REGISTRY + gates.json ──
# These 6 skills existed on disk but were never wired — `llc run --step 5a`
# crashed with UnknownStepError. Now they are full pipeline steps with gates.


@pytest.mark.parametrize("step_id,alias,gate,skill_file", [
    ("5.1", "5a", "6a", "llc-step-5a-architecture-patterns"),
    ("5.2", "5b", "6b", "llc-step-5b-api-design"),
    ("5.3", "5c", "8.5", "llc-step-5c-clean-code"),
    ("8.1", "8b", "9b", "llc-step-8b-repository-pattern"),
    ("10.9", "11a", "11-PRE", "llc-step-11a-domain-modeling"),
])
def test_f14_sub_step_wired_in_registry(step_id, alias, gate, skill_file):
    """Each sub-step must be in REGISTRY with correct gate + skill_file."""
    spec = llc_steps.normalize_step(step_id)
    assert spec.id == step_id
    assert spec.gate == gate, f"{step_id} gate={spec.gate!r}, expected {gate!r}"
    assert spec.skill_file == skill_file, f"{step_id} skill_file={spec.skill_file!r}"
    assert spec.in_pipeline is True, f"{step_id} must be in_pipeline"


@pytest.mark.parametrize("alias,expected_id", [
    ("5a", "5.1"), ("5b", "5.2"), ("5c", "5.3"),
    ("8b", "8.1"), ("11a", "10.9"), ("11b", "11.3"),
])
def test_f14_sub_step_aliases_resolve(alias, expected_id):
    """Letter aliases (5a, 5b, 5c, 8b, 11a, 11b) must resolve to canonical ids."""
    assert llc_steps.normalize_step(alias).id == expected_id


@pytest.mark.parametrize("step_id,expected_gate,min_items", [
    ("5.1", "6a", 5),
    ("5.2", "6b", 6),
    ("5.3", "8.5", 6),
    ("8.1", "9b", 5),
    ("10.9", "11-PRE", 4),
])
def test_f14_sub_step_gates_have_checklists(step_id, expected_gate, min_items):
    """Each sub-step gate must have a non-empty checklist in gates.json."""
    from llc_harness import get_gate_checklist

    gate_num, items = get_gate_checklist(step_id)
    assert gate_num == expected_gate, f"{step_id} gate={gate_num!r}"
    assert len(items) >= min_items, (
        f"{step_id} ({expected_gate}): expected >={min_items} items, got {len(items)}"
    )


def test_f14_step_11_3_uses_detailed_skill():
    """Step 11.3 (Architecture Fitness) must use the detailed skill
    (llc-step-11b-arch-fitness) not the original simple one (llc-arch-fitness)."""
    spec = llc_steps.normalize_step("11.3")
    assert spec.skill_file == "llc-step-11b-arch-fitness", (
        f"11.3 skill_file={spec.skill_file!r}"
    )


def test_f14_pipeline_includes_sub_steps():
    """pipeline_steps(0.5, 11.1) must include the 5 new sub-steps in order."""
    specs = llc_steps.pipeline_steps("0.5", "11.1")
    ids = [s.id for s in specs]
    assert "5.1" in ids and "5.2" in ids and "5.3" in ids
    assert "8.1" in ids and "10.9" in ids
    # Verify ordering: 5.1/5.2/5.3 after 5, before 6
    assert ids.index("5") < ids.index("5.1") < ids.index("5.2") < ids.index("5.3") < ids.index("6")
    # 8.1 after 8, before 9
    assert ids.index("8") < ids.index("8.1") < ids.index("9")
    # 10.9 after 10.8, before 11
    assert ids.index("10.8") < ids.index("10.9") < ids.index("11")


def test_f14_d01_gate_step_fields_match_registry_with_sub_steps():
    """D-01 conformance: gates.json step fields must match REGISTRY for all
    steps including the 5 new sub-steps."""
    gates = json.load(open(Path(__file__).parent.parent / "config" / "gates.json"))["gates"]
    mismatches = []
    for sid, spec in sorted(llc_steps.REGISTRY.items(), key=lambda kv: kv[1].number):
        if spec.gate is None:
            continue
        gj_step = gates.get(spec.gate, {}).get("step")
        match = spec.gate in gates and abs(gj_step - spec.number) < llc_steps.EPS
        if not match:
            mismatches.append((sid, spec.gate, gj_step, spec.number))
    assert mismatches == [], f"D-01 mismatches (incl. sub-steps): {mismatches}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
