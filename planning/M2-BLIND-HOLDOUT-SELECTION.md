# M2 — Blind Holdout Selection v1 — FROZEN

**Data:** 2026-09-14  
**Status:** `FROZEN_UNREVEALED`  
**Baseline:** `architecture/M2-DESIGN-V0.1.md` + `architecture/CBM-V0.1.md`

## Regra de cegueira

A seleção foi executada sem extração de texto, renderização de páginas, inspeção visual ou análise semântica do conteúdo reservado. Foram usados somente hashes, tamanhos, contagem de páginas, metadados de membros ZIP e um seed determinístico cujo SHA-256 está no manifest.

Além do escopo selecionado, **o SourceArtifact inteiro de cada caso fica em quarentena** até o freeze do implementation candidate. Isso impede que processamento integral, logs, páginas adjacentes ou unpack acidental contaminem o blind test.

## Holdouts congelados

### M2-H1 — CC-07 — literary_prose_pdf

- source: `corpus/compatibility/CC-07/source/memoriasBras.pdf`
- support tier: `Tier 1`
- reserved evaluation scope: PDF physical pages 57–58 (1-based)
- whole source quarantine: **yes**

### M2-H2 — CC-18 — technical_scientific_pdf

- source: `corpus/compatibility/CC-18/source/Attention Is All You Need #U2014 PDF original.pdf`
- support tier: `Tier 1`
- reserved evaluation scope: PDF physical pages 9–10 (1-based)
- whole source quarantine: **yes**

### M2-H3 — CC-05 — structured_reference_pdf

- source: `corpus/compatibility/CC-05/source/Novo dicion#U00e1rio da l#U00edngua portuguesa.pdf`
- support tier: `Tier 1`
- reserved evaluation scope: PDF physical pages 834–835 (1-based)
- whole source quarantine: **yes**

### M2-H4 — CC-14 — tier1_markdown_technical

- source: `corpus/compatibility/CC-14/source/book-main.zip`
- support tier: `Tier 1`
- reserved evaluation scope: ZIP member `book-main/src/ch15-01-box.md` (hash frozen; content unopened)
- whole source quarantine: **yes**

## Coverage note

O design recomenda pelo menos PDF literário/prosa, PDF técnico, PDF matemático/estruturado e Markdown narrativa. O conjunto adquirido não contém uma nova narrativa Markdown ainda não vista; por isso H4 usa Markdown técnico Tier 1 do Rust Book. A narrativa Markdown continua coberta por C2 no Regression Core, mas não como nova evidência cega. Um H5 narrativo poderá ser adicionado **somente antes de qualquer implementação/tuning relevante**, mediante novo freeze versionado; não é requisito para este v1.

## Reveal gate

Os holdouts só podem ser revelados depois que um `M2 implementation candidate manifest` congelar: identidade de build/package, baseline CBM/schema, configuração semântica, processors/models/providers e reproducibility class, ValidationPolicy, versão das regression assertions e capability/support-tier claims.

Se um holdout falhar, ele se torna regression material. Ajustar o sistema usando esse conteúdo exige novo candidate e novo holdout para a claim afetada.

