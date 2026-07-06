# Guia Rápido — Live and Let Code (LLC)

**Versão:** 1.5.0  
**Tempo estimado:** 30 minutos para setup, 2-3 horas para MVP

---

## 🚀 Instalação Rápida

```bash
# 1. Clonar o LLC
git clone https://github.com/jcneto25/Live-and-Let-Code.git seu-projeto
cd seu-projeto

# 2. Instalar dependência
pip install click

# 3. Instalar hook do git (recomendado)
cp .ace/scripts/pre-commit.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

---

## 📋 Checklist de Início

- [ ] Documentos de negócio em `docs/business/ingestion/`
- [ ] Python 3.10+ instalado
- [ ] Click instalado (`pip install click`)
- [ ] Hook git configurado (opcional, mas recomendado)

---

## 🎯 Pipeline Quickstart (Recomendado para Iniciantes)

O modo quickstart executa apenas os gates essenciais:

```bash
# 1. Executar pipeline quickstart
python .ace/scripts/llc.py pipeline --quickstart --from 0

# 2. Ver progresso
python .ace/scripts/llc.py status
```

**O que o quickstart inclui:**
- Gate 1: Visão + Módulos
- Gate 4: PRPs (Project Requirement Proposals)
- Gate 11: Execução (PRPs sem UI)

---

## 🔄 Pipeline Completo (Para projetos com UI)

```bash
python .ace/scripts/llc.py pipeline --from 0 --to 11.1
```

**Passos completos:**
1. Visão + Módulos
2. 7 Especificações
3. PRDs
4. PRPs
5. Planejamento
6. Arquitetura
7. Tarefas
8. Design System
9. Setup + Mock Data
10. Testes
11. Project Docs
12. User Guide
13. Security Audit
14. Null Safety
15. Execução
16. Hardening OWASP

---

## ⚡ Comandos Essenciais

| Comando | Descrição |
|---------|-----------|
| `llc pipeline --quickstart` | Pipeline simplificado (3 gates) |
| `llc pipeline --from 0 --to 5` | Pipeline personalizado |
| `llc run --step 5 --task "Arquitetura"` | Executar step específico |
| `llc gate list` | Listar gates disponíveis |
| `llc gate run --gate security` | Validar security gate |
| `llc status` | Ver progresso do pipeline |

---

## 🔍 Diagnóstico Rápido

```bash
# Ver status do pipeline
python .ace/scripts/llc.py status

# Ver worktrees ativos
git worktree list

# Ver sessões ACE
cat .ace/index.json | jq '.sessions[-3:]'

# Consistency check
python .ace/scripts/consistency-check.py --json
```

---

## 📚 Recursos Adicionais

| Documento | Descrição |
|-----------|-----------|
| [`TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) | Resolução de problemas comuns |
| [`llc-pipeline-design.md`](llc-pipeline-design.md) | Especificação completa |
| [`docs/templates/`](docs/templates/) | Templates com exemplos |
| [`docs/skills/`](docs/skills/) | Skills available para AI client |

---

## 🐛 Erros Comuns

| Erro | Solução |
|------|---------|
| "Click não instalado" | `pip install click` |
| "EXECUTION_WAVES.md não encontrado" | Executar `llc run --step 4 --task "Planejamento"` |
| "Gate reprovado" | Verificar `docs/security/` e corrigir issues |
| "Consistency check falhou" | Rodar `python .ace/scripts/consistency-check.py` |

---

## 📞 Suporte

- Leitura obrigatória: [`TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)
- Design completo: [`llc-pipeline-design.md`](llc-pipeline-design.md)
- Templates: [`docs/templates/`](docs/templates/)

---

**Bom desenvolvimento!** 🎉
