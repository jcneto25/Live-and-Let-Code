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

## 2026-10-09-005

A ORDEM DO STRIP E PARTE DO ALGORITMO (GOV-004, 4a instancia, superada pela 5a): com a lista de 6 corpos, o hook passou a acusar a propria sessao 005 — `<learning_point>` 1/0 e `` literal DENTRO do proprio corpo do context_seed) foi acusado, e eu quase tratei como falha do fix. Verificado: esse padrao e ambiguo por construcao (nao ha como distinguir fechamento real de citado) e NAO existe em nenhuma das 76 sessoes reais. Reclassificado como artefato do meu teste, nao do hook. Licao: antes de "corrigir" o codigo para satisfazer um teste, verificar se o teste descreve um caso real e bem-formado.

## 2026-10-09-005

AUTO-ENGANO CORRIGIDO (eu, 2026-10-09): o primeiro teste RED de isolamento PASSOU (3 passed) porque eu havia definido o fixture `autouse` DENTRO do proprio arquivo de teste — ele isolava apenas a si mesmo, e os outros modulos da suite continuavam sujando .ace/logs/. Um teste que se auto-isola nao prova nada sobre o isolamento da suite. Corrigido movendo o fixture para conftest.py e adicionando `test_isolation_fixture_is_not_local_to_this_module`, que falha se alguem repetir o erro. Licao: fixture autouse no mesmo modulo do teste nao testa isolamento coletivo.

## 2026-10-09-005

ROOT CAUSE MAIOR QUE O SINTOMA (eu, 2026-10-09): o vazamento de replay.jsonl nao vinha do trace_dir isolado — vinha de `llc_replay/constants.py::LOGS_DIR = Path(".ace/logs")`, relativo ao CWD. Duas consequencias com UMA causa: (1) `log_replay_event` escapava do LLC_TRACE_DIR e escrevia no repo durante os testes; (2) sob cwd diferente (ex.: rodar pytest de dentro de .ace/scripts) escrevia no lugar errado — que e exatamente a fragilidade `TestReplayRoutingHandling` relatada como "preexistente e nao relacionada" na verificacao anterior. Nao era fragilidade independente: era o mesmo defeito. Registrado aqui porque a ligacao nao estava feita.

## 2026-10-09-005

DISCREPANCIA COM O RELATORIO ANTERIOR — LOGS NAO ESTAVAM LIMPOS: a verificacao anterior afirmou "Logs .ace/logs/*.jsonl -> diff vazio, inclusive apos o re-run (o fixture autouse isola LLC_TRACE_DIR em tmp_path)". Medido nesta sessao: decisions.jsonl +79, replay.jsonl +26, events.jsonl +1. O fixture existe e funciona, mas cobre apenas llc_replay/tests/test_verify.py — a suite .ace/scripts/llc2/tests/ (19 linhas/execucao) escapava por LOGS_DIR. A generalizacao "os logs estao isolados" era falsa: estava isolada UMA suite, nao o conjunto.
