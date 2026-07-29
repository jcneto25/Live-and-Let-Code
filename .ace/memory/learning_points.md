# Learning Points Consolidados


## 2026-07-27-004

finalize_session.py grava completed_at no index.json mas SessionInfo não tinha o campo — qualquer initialize após uma sessão finalizada quebrava. Fix: unpacking tolerante com fields(). Dataclasses que hidratam JSON externo devem filtrar chaves desconhecidas.
