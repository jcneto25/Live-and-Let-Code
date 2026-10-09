"""PRP-ACE-TAGS (GOV-003/R1): taxonomia de tags do ADR-0002 (HITL), ADR-0005
(Eval Harness) e AGENTS.md (Progress Reflection) reconhecida pelo validate-tags.py.

Formatos canônicos (pós-R1):
  <user_response type="question|artifact_review|scope" ...><question/><answer/></user_response>
  <eval_metrics timestamp="...">...</eval_metrics>
  <task_completed id="..." prp="..." status="done|partial">...</task_completed>
  <gate_result step="..." decision="..." waiver="true|false"><waiver_note>...</waiver_note></gate_result>
"""
import importlib.util
from pathlib import Path

# validate-tags.py tem hífen no nome — import via importlib
_SPEC = importlib.util.spec_from_file_location(
    "validate_tags", Path(__file__).parent / "validate-tags.py")
vt = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(vt)

P = Path("dummy-session.md")


def _msgs(errors):
    return [e.message for e in errors]


class TestUserResponse:
    def test_unbalanced_user_response_flagged(self):
        content = '<user_response type="question"><question>q?</question>'
        errors = vt.validate_balanced_tags(content, P)
        assert any("user_response" in m for m in _msgs(errors))

    def test_user_response_requires_type(self):
        content = "<user_response><question>q?</question><answer>a</answer></user_response>"
        errors = vt.validate_required_attributes(content, P)
        assert any("user_response" in m and "type" in m for m in _msgs(errors))

    def test_user_response_type_values(self):
        content = '<user_response type="bogus">x</user_response>'
        errors = vt.validate_attribute_values(content, P)
        assert any("user_response" in m for m in _msgs(errors))

    def test_valid_user_response_passes(self):
        content = ('<user_response type="question" question_id="q-1">'
                   "<question>q?</question><answer>a</answer></user_response>")
        assert vt.validate_balanced_tags(content, P) == []
        assert vt.validate_required_attributes(content, P) == []
        assert vt.validate_attribute_values(content, P) == []


class TestEvalMetrics:
    def test_unbalanced_eval_metrics_flagged(self):
        content = '<eval_metrics timestamp="2026-08-05T10:00:00">\n  step: "5"'
        errors = vt.validate_balanced_tags(content, P)
        assert any("eval_metrics" in m for m in _msgs(errors))

    def test_valid_eval_metrics_passes(self):
        content = ('<eval_metrics timestamp="2026-08-05T10:00:00">\n'
                   '  step: "5"\n  total_tokens: 15500\n  source: "level_1"\n</eval_metrics>')
        assert vt.validate_balanced_tags(content, P) == []


class TestTaskCompleted:
    def test_task_completed_requires_id_and_status(self):
        content = "<task_completed>texto</task_completed>"
        errors = vt.validate_required_attributes(content, P)
        assert any("task_completed" in m and "id" in m for m in _msgs(errors))
        assert any("task_completed" in m and "status" in m for m in _msgs(errors))

    def test_task_completed_status_values(self):
        content = '<task_completed id="T-1" prp="—" status="wip">x</task_completed>'
        errors = vt.validate_attribute_values(content, P)
        assert any("task_completed" in m for m in _msgs(errors))

    def test_valid_task_completed_passes(self):
        content = '<task_completed id="FDN-001" prp="PRP-001" status="done">x</task_completed>'
        assert vt.validate_balanced_tags(content, P) == []
        assert vt.validate_required_attributes(content, P) == []
        assert vt.validate_attribute_values(content, P) == []


class TestProseMentions:
    """Regressão: sessão 2026-07-31-001 linha 57 — '<task_completed> emitidos
    na época' é prosa, não tag. Sessões são imutáveis (append-only): o
    validador deve ignorar menções sem atributos, sem fechamento na mesma
    linha e com texto após a tag na mesma linha."""

    def test_prose_mention_without_attrs_not_flagged(self):
        content = (
            "     <task_completed> emitidos na época. Registrados aqui.\n"
            '<task_completed id="GOV-001" prp="PRP-GOV-001" status="done">x</task_completed>\n'
        )
        assert vt.validate_balanced_tags(content, P) == []
        assert vt.validate_required_attributes(content, P) == []

    def test_real_tag_without_attrs_still_flagged(self):
        # tag real (fechada na mesma linha) sem atributos continua inválida
        content = "<task_completed>texto</task_completed>"
        errors = vt.validate_required_attributes(content, P)
        assert any("task_completed" in m for m in _msgs(errors))

    def test_inline_prose_citation_on_real_tag_line_is_ignored(self):
        content = (
            '<action type="file_modify"><description>cita '
            '`<action>` e fecha aqui</description></action>\n'
        )
        errors = vt.validate_balanced_tags(content, P)
        assert errors == []

    def test_learning_point_can_quote_its_own_tag_without_false_positive(self):
        content = (
            '<learning_point priority="high">A correção cita '
            '`<learning_point priority="high">` no texto.</learning_point>\n'
        )
        errors = vt.validate_balanced_tags(content, P)
        assert errors == []

    def test_inline_action_citation_does_not_trigger_required_type(self):
        content = (
            '<action type="file_modify"><description>cita '
            '`<action>` no texto</description></action>\n'
        )
        errors = vt.validate_required_attributes(content, P)
        assert errors == []

    def test_inline_learning_point_citation_does_not_trigger_priority(self):
        content = (
            '<learning_point priority="high">A correção cita '
            '`<learning_point>` no texto.</learning_point>\n'
        )
        errors = vt.validate_required_attributes(content, P)
        assert errors == []

    def test_gate_archive_is_not_session_input(self):
        # Âncora na raiz do repo: o teste deve passar tanto rodando da raiz
        # quanto de .ace/scripts — cwd não pode definir a existência do arquivo
        # (regressão da suíte full, que executa com cwd=.ace/scripts).
        repo_root = Path(__file__).resolve().parents[2]
        gate_archive = repo_root / ".ace/gates/2026-10-07-007.md"
        assert gate_archive.exists()
        errors = vt.validate_yaml_front_matter(
            gate_archive.read_text(encoding="utf-8"), gate_archive
        )
        assert errors, "gate sem frontmatter deve ser rejeitado como input de sessão"

    def test_fix_does_not_append_close_for_balanced_structural_tags(self, tmp_path):
        content = (
            '<learning_point priority="high">A correção cita '
            '`<learning_point priority="high">` no texto.</learning_point>\n'
        )
        session = tmp_path / "session.md"
        session.write_text(content, encoding="utf-8")
        assert vt.fix_unbalanced_tags(session) is False
        assert session.read_text(encoding="utf-8") == content


class TestGateResultWaiver:
    def test_gate_result_with_waiver_passes(self):
        content = ('<gate_result step="5" decision="approved" waiver="true">'
                   "<waiver_note>justificativa com 10+ chars</waiver_note></gate_result>")
        assert vt.validate_required_attributes(content, P) == []
        assert vt.validate_attribute_values(content, P) == []
        assert vt.validate_balanced_tags(content, P) == []

    def test_gate_result_invalid_waiver_value(self):
        content = '<gate_result step="5" decision="approved" waiver="sim">x</gate_result>'
        errors = vt.validate_attribute_values(content, P)
        assert any("waiver" in m for m in _msgs(errors))

    def test_gate_result_still_requires_step_decision(self):
        # formato antigo do ADR-0002 §7.2 (approved=/waiver= sem step/decision) é inválido
        content = '<gate_result approved="true" waiver="true">x</gate_result>'
        errors = vt.validate_required_attributes(content, P)
        assert any("'step'" in m for m in _msgs(errors))
        assert any("'decision'" in m for m in _msgs(errors))
