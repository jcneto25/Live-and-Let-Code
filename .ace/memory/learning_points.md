# Learning Points Consolidados


## 2026-07-27-004

finalize_session.py grava completed_at no index.json mas SessionInfo não tinha o campo — qualquer initialize após uma sessão finalizada quebrava. Fix: unpacking tolerante com fields(). Dataclasses que hidratam JSON externo devem filtrar chaves desconhecidas.

## 2026-08-05-001

ADRs aceitos que descrevem o proprio tooling podem conter premissas factualmente incorretas sobre o codigo (ex.: ADR-0004 assumiu depends_on no StepSpec, inexistente). Toda afirmacao factual de um ADR sobre codigo deve ser verificada contra o repositorio antes do aceite — mesmo gap de classe advisory-vs-deterministico do GOV-001, na forma documental.

## 2026-08-05-003

Rodar a suite pytest completa de .ace/scripts/ cria sessoes orfas via llm_fallback do llc.py (3a reincidencia GOV-002). Ate o fix R7, suites devem rodar com --ignore de llc_replay/finalize_session/initialize_session ou com fixture de .ace isolado.

## 2026-08-05-004

A causa raiz das orfas GOV-002 nao era o llm_fallback em si, mas a manufatura silenciosa de task placeholder em session_start (task or f"Step {step}") combinada com --project nunca propagado pelo harness. Sentinel values devem ser rejeitados na camada deterministica (initialize_session), nao confiar que callers nunca os produzem.

## 2026-08-05-011

Trilha 0 do PRP-MAP completa em 1 dia (ACE-TAGS, GOV-002 fix, GOV-T1/T2/T3): politica ADR-0006 agora e enforced deterministicamente — qualquer dependencia nao registrada, nao pinada, sem licenca ou N2/N3 no caminho critico bloqueia via fitness-functions --check-governance.

## 2026-08-06-009

observability.py estava AUSENTE como módulo first-party (GOV-T2/R2) — causa das 6 falhas pré-existentes de test_observability.py. Implementado com somente stdlib para satisfazer o contrato do teste: sessions (total==completed+in_progress+other), worktrees, gates.failing (decision=rejected), govs (open/addressed/closed), waves; build_report() com SESSIONS_DIR monkeypatchável.
