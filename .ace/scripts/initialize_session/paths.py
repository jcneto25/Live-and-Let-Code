#!/usr/bin/env python3
"""initialize_session — constantes, mapas de step e logging."""

import logging
from pathlib import Path

from llc_steps import REGISTRY

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

ACE_DIR = Path(".ace")
INDEX_FILE = ACE_DIR / "index.json"
SESSIONS_DIR = ACE_DIR / "sessions"
TEMPLATE_FILE = ACE_DIR / "templates" / "session.template.md"
GRAPH_FILE = ACE_DIR / "dependency-graph.yaml"
WORKTREES_DIR = ACE_DIR / "worktrees"

# Fonte de verdade: llc_steps.REGISTRY. LLC_STEPS/VALID_STEPS ficam como shim de
# compat (assinatura antiga {numero: nome}) — agora incluem 10.5/10.6/10.7/11.1.
LLC_STEPS = {spec.number: spec.name for spec in REGISTRY.values()}
VALID_STEPS = frozenset(LLC_STEPS.keys())

# Mapeamento step → artefatos primários que a sessão cria/altera.
STEP_ARTIFACTS: dict[float, list[str]] = {
    0.0: ["ingestion_raw"],
    0.1: ["ingestion_converted"],
    0.5: ["visao_estrategica", "module_specs"],
    1:   ["glossario", "requisitos_funcionais", "requisitos_nao_funcionais",
          "regras_negocio", "workflows_bpmn", "perfis_permissoes",
          "catalogo_integracoes"],
    2:   ["prd_executivo", "prd_tecnico"],
    3:   ["prps"],
    4:   ["dependency_matrix", "plan", "execution_waves"],
    5:   ["architecture"],
    6:   ["tasks", "design_system"],
    7:   ["design_system"],
    8:   ["mock_data"],
    9:   ["test_guide", "coverage_baseline", "coverage_progress"],
    10:  ["readme", "deployment"],
    10.5: ["user_guide_skeleton", "user_guide_index", "user_guide_overview",
           "user_guide_profiles", "user_guide_pages"],
    11:  [],  # código — sem artefato próprio, mas impacta documentation via triggers_update
    11.1: ["owasp_hardening_report"],
    11.2: ["security_audit_report", "security_scan_outputs"],
    12:  ["null_safety_report"],
}
