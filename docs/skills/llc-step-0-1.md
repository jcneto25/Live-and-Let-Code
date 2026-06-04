---
name: llc-step-0-1
description: Pipeline LLC Passo 0.1: Converte documentos raw (PDF, DOCX, HTML, etc.) para Markdown usando Docling, preparando os dados para ingestão pela IA.
version: 1.0.0
tags: [conversion, ingestion, markdown, llc-pipeline]
---

# LLC Skill: Step 0.1 — Conversão de Dados Raw → Markdown

**Pipeline:** Live and Let Code (LLC)  
**Fase:** Data Preparation  
**Depende de:** Step 0 (documentos carregados em `docs/business/ingestion/`)  
**Mantenedor:** Equipe LLC

## 🛠️ Como usar esta Skill

1. Coloque este arquivo em `.claude/skills/` ou na pasta `docs/skills/` do projeto.
2. Invoque no chat usando: `@llc-step-0-1` ou "Execute a skill llc-step-0-1".

## 📋 Pré-requisitos

- [ ] Documentos raw carregados em `docs/business/ingestion/` (PDF, DOCX, PPTX, HTML, TXT, imagens com texto)
- [ ] **Python 3.10+** instalado: `python --version`
  - Windows: `winget install Python.Python.3.12` ou https://python.org
  - macOS: `brew install python@3.12`
  - Linux: `sudo apt install python3`
- [ ] **pip** disponível: `pip --version` (já vem com Python 3.4+)
- [ ] **Docling** instalado: `pip install docling`
- [ ] Alternativa fallback: `pandoc` instalado (`choco install pandoc` / `brew install pandoc`)

---

## 🎯 PROMPT DE EXECUÇÃO

Você está executando a skill `llc-step-0-1` do pipeline LLC. Seu objetivo é converter todos os documentos raw em `docs/business/ingestion/` para Markdown puro, depositando o resultado em `docs/business/ingestion/converted/`. Este passo garante que a IA dos passos seguintes consuma dados com máxima eficiência de tokenização e mínimo ruído estrutural.

### Por que Markdown?

| Formato | Tokens por info útil | Ruído estrutural | Performance |
|---------|---------------------|------------------|-------------|
| Markdown | Baixo | Mínimo | ⭐⭐⭐⭐⭐ |
| JSON | Médio | Baixo-médio | ⭐⭐⭐⭐ |
| XML | Alto | Alto | ⭐⭐⭐ |
| HTML | Muito alto | Muito alto | ⭐⭐ |

Markdown vence porque:
1. **Eficiência de tokenização:** O tokenizador (BPE/SentencePiece) é treinado massivamente em Markdown.
2. **Baixa densidade de ruído:** Quase todos os tokens carregam semântica útil.
3. **Alinhamento com dados de treino:** A maior parte do corpus de treino de LLMs (GitHub, Reddit, documentação) está em Markdown.
4. **Mecanismo de atenção:** Cabeçotes de atenção reconhecem `#` como hierarquia, `-` como enumeração, `**` como ênfase — sem custo extra de parsing.

### 1. Verifique o Ambiente

Execute no terminal:
```bash
docling --version
```

Se não estiver instalado:
```bash
pip install docling
# ou
pipx install docling
```

**Fallback (se Docling não puder ser instalado):**
```bash
# Verifique o pandoc
pandoc --version

# Se não estiver instalado:
# Windows: choco install pandoc
# macOS: brew install pandoc
# Linux: sudo apt install pandoc
```

### 2. Liste os Arquivos de Entrada

Use ferramentas de arquivo para listar todos os documentos em `docs/business/ingestion/`:

- Ignore a subpasta `converted/` (se já existir de execução anterior).
- Ignore arquivos ocultos (começando com `.`).
- Classifique cada arquivo por formato: PDF, DOCX, PPTX, HTML, TXT, imagem (PNG/JPG/TIFF).

### 3. Crie a Pasta de Destino

```bash
mkdir -p docs/business/ingestion/converted
```

### 4. Converta os Arquivos

#### Com Docling (método primário)

Para cada arquivo em `docs/business/ingestion/`:

```bash
docling --to md --output docs/business/ingestion/converted/ "docs/business/ingestion/[nome_do_arquivo]"
```

O Docling suporta nativamente:
- **PDF:** Extrai texto, tabelas e estrutura de headings
- **DOCX:** Preserva formatação (negrito, itálico, listas, tabelas)
- **PPTX:** Extrai slides como seções Markdown
- **HTML:** Converte para Markdown limpo, removendo tags e scripts
- **Imagens (PNG/JPG/TIFF):** Aplica OCR e extrai texto

**Para cada arquivo convertido:**
- O nome do arquivo de saída deve ser: `[nome_original_sem_extensao].md`
- Ex: `manual_processos_v3.pdf` → `manual_processos_v3.md`
- Ex: `ata_reuniao_06-06.docx` → `ata_reuniao_06-06.md`

#### Com Pandoc (fallback)

Se o Docling não estiver disponível para algum formato:

```bash
# PDF → Markdown
pandoc "docs/business/ingestion/arquivo.pdf" -t markdown -o "docs/business/ingestion/converted/arquivo.md"

# DOCX → Markdown
pandoc "docs/business/ingestion/arquivo.docx" -t markdown -o "docs/business/ingestion/converted/arquivo.md"

# HTML → Markdown
pandoc "docs/business/ingestion/arquivo.html" -t markdown -o "docs/business/ingestion/converted/arquivo.md"
```

### 5. Verificação Pós-Conversão

Para cada arquivo convertido, faça uma verificação rápida:

- [ ] O arquivo .md de saída existe e não está vazio (> 0 bytes)
- [ ] Headings foram preservados (o documento tem estrutura `#`, `##`)
- [ ] Tabelas foram convertidas (há `|` pipes indicando tabelas)
- [ ] Listas foram preservadas (itens com `-` ou `1.`)
- [ ] Texto formatado (negrito `**`, itálico `*`) foi mantido

Se um arquivo convertido estiver vazio ou ilegível:
- Registre no relatório de conversão como `⚠️ FALHA PARCIAL — verificar arquivo original`.
- Não delete o original.

### 6. Gere o Relatório de Conversão

Crie `docs/business/ingestion/converted/_CONVERSION_REPORT.md`:

```markdown
# Relatório de Conversão — Step 0.1

**Data:** [DATA DA EXECUÇÃO]
**Ferramenta:** Docling [VERSÃO] / Pandoc [VERSÃO]
**Total de arquivos processados:** [N]
**Convertidos com sucesso:** [N]
**Falhas:** [N]
**Avisos:** [N]

## Arquivos Convertidos

| # | Arquivo Original | Formato | Tamanho (orig.) | Tamanho (.md) | Status | Observações |
|---|------------------|---------|-----------------|---------------|--------|-------------|
| 1 | `manual_v3.pdf` | PDF | 2.1 MB | 45 KB | ✅ Sucesso | 12 headings, 3 tabelas |
| 2 | `ata_06-06.docx` | DOCX | 156 KB | 12 KB | ✅ Sucesso | — |
| 3 | `regulamento.html` | HTML | 89 KB | 18 KB | ✅ Sucesso | Tags removidas |
| 4 | `foto_quadro.jpg` | JPG | 3.4 MB | 2 KB | ⚠️ Parcial | OCR extraiu apenas título. Verificar original. |
| 5 | `arquivo_corrompido.pdf` | PDF | 0 KB | — | ❌ Falha | Arquivo original vazio ou corrompido |

## Estatísticas

- **Formatos encontrados:** PDF (X), DOCX (Y), HTML (Z), TXT (W)
- **Total de texto Markdown gerado:** [X] KB
- **Redução média de tamanho:** [X]% (remoção de ruído estrutural)

## Próximos Passos

Os arquivos convertidos em `converted/` estão prontos para o Step 0.5.
Execute: `@llc-step-0-5` ou "Execute a skill llc-step-0-5".
```

### 7. Tratamento de Erros

| Situação | Ação |
|----------|------|
| Arquivo original corrompido (0 bytes) | ❌ Pular. Registrar no relatório como falha. |
| Formato não suportado (.exe, .dll, .zip) | ⚠️ Pular. Registrar no relatório com aviso: "Formato não suportado — ignorado". |
| Docling/Pandoc não instalado | ❌ PARAR. Instruir o usuário a instalar: `pip install docling`. |
| Arquivo convertido vazio | ⚠️ Registrar no relatório. Sugerir verificação manual do original. |
| Nome de arquivo com espaços ou caracteres especiais | Usar aspas duplas no comando: `"docs/business/ingestion/meu arquivo.pdf"`. |

---

## ⚠️ REGRAS CRÍTICAS

1. **NÃO modifique os originais:** Os arquivos em `ingestion/` permanecem intactos. A conversão vai para `converted/`.
2. **Preserve nomes:** `manual_v3.pdf` → `manual_v3.md`. Facilita rastreabilidade.
3. **Relatório obrigatório:** `_CONVERSION_REPORT.md` DEVE ser gerado ao final.
4. **Idempotência:** Se `converted/` já existir, pergunte: "A pasta converted/ já existe. Deseja sobrescrever todos os arquivos ou apenas reprocessar os novos?"
5. **Sem invenção:** A conversão é automática. Não adicione, resuma ou modifique conteúdo dos documentos.

---

## 📤 SAÍDA ESPERADA E FINALIZAÇÃO

Após concluir a conversão, **PARE** e apresente:

1. **Resumo:** Total de arquivos processados, convertidos com sucesso, falhas.
2. **Relatório:** Caminho do `_CONVERSION_REPORT.md` gerado.
3. **Falhas:** Se houve falhas, liste os arquivos problemáticos e a ação recomendada.
4. **Próximos Passos:** "Os arquivos em `converted/` estão prontos. Execute o Step 0.5 com `@llc-step-0-5`."

**Este passo termina aqui. A conversão está concluída.**
