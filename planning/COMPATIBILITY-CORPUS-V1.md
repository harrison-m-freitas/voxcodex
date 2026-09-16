# Compatibility Corpus v1 — Concrete Registry

## Estado

- Curadoria concreta aprovada: **30 CorpusCases**.
- Compatibility Shortlist: **12 casos**, aquisição **12/12**.
- Aquisição em 2026-09-14: **30/30 do corpus total**.
- Compatibility Corpus v1: **FROZEN**; nenhum caso permanece pendente.
- M2 Blind Holdouts v1: **FROZEN / UNREVEALED**; SourceArtifacts `CC-05`, `CC-07`, `CC-14`, `CC-18` permanecem em quarentena integral.
- `data/` histórico permanece separado e não recebe os novos casos.

## Regras de identidade

Cada `CC-xx` representa uma manifestação concreta. O formato efetivamente adquirido é autoritativo para o caso até revisão explícita; o formato sugerido durante a curadoria permanece registrado como histórico. Arquivos adicionais da mesma obra não se tornam automaticamente um novo CorpusCase.

## Registry

| ID | Shortlist | Documento | Idioma | Formato concreto/alvo | Tier | Aquisição |
|---|---:|---|---|---|---|---|
| CC-01 | ★ | Constituição Federal de 1988 — texto atualizado | pt-BR | HTML saved-page bundle | Experimental | ✅ acquired |
| CC-02 |  | Código Civil — Lei 10.406 compilada | pt-BR | HTML saved-page bundle | Experimental | ✅ acquired |
| CC-03 | ★ | Tutorial oficial Python 3.14 em português | pt-BR | HTML documentation archive | Experimental | ✅ acquired |
| CC-04 | ★ | Os Lusíadas | pt | PDF | Tier 1 | ✅ acquired |
| CC-05 | ★ | Novo dicionário da língua portuguesa | pt | PDF | Tier 1 | ✅ acquired — 🔒 holdout |
| CC-06 |  | Dom Casmurro | pt-BR | EPUB3 | Experimental | ✅ acquired |
| CC-07 |  | Memórias Póstumas de Brás Cubas | pt-BR | PDF | Tier 1 | ✅ acquired — 🔒 holdout |
| CC-08 |  | eMAG — Modelo de Acessibilidade em Governo Eletrônico v3.1 | pt-BR | HTML saved-page bundle | Experimental | ✅ acquired |
| CC-09 | ★ | Guia Prático de Direitos de Acessibilidade | pt-BR | DOCX | Experimental | ✅ acquired |
| CC-10 |  | Hamlet: Drama em cinco Actos | pt | Plain text (TXT) | Experimental | ✅ acquired |
| CC-11 | ★ | The Republic of Plato | en | EPUB3 | Experimental | ✅ acquired |
| CC-12 | ★ | Histories, Vol. 1 | pt | PDF | Tier 1 | ✅ acquired |
| CC-13 | ★ | The Souls of Black Folk | en | EPUB3 | Experimental | ✅ acquired |
| CC-14 | ★ | The Rust Programming Language — source | en | Markdown source bundle (ZIP) | Tier 1 | ✅ acquired — 🔒 holdout |
| CC-15 |  | The Rust Programming Language — rendered | en | Rendered HTML documentation archive (ZIP) | Experimental | ✅ acquired |
| CC-16 | ★ | Dracula | en | EPUB3 | Experimental | ✅ acquired |
| CC-17 |  | Dracula — HTML manifestation | en | HTML download bundle (ZIP) | Experimental | ✅ acquired |
| CC-18 | ★ | Attention Is All You Need | en | PDF | Tier 1 | ✅ acquired — 🔒 holdout |
| CC-19 |  | CommonMark Specification — source spec.txt | en | Markdown-like source text (TXT) | Tier 1 | ✅ acquired |
| CC-20 |  | CommonMark Specification — rendered | en | HTML saved-page bundle | Experimental | ✅ acquired |
| CC-21 |  | RFC 9110 — HTTP Semantics | en | HTML saved-page bundle | Experimental | ✅ acquired |
| CC-22 |  | Euclid — First Six Books of the Elements | en | PDF | Tier 1 | ✅ acquired |
| CC-23 | ★ | Alice's Adventures in Wonderland — scanned edition | en | Scanned PDF | Experimental | ✅ acquired |
| CC-24 |  | Alice's Adventures in Wonderland — EPUB | en | EPUB3 | Experimental | ✅ acquired |
| CC-25 |  | NASA Systems Engineering Handbook | en | PDF | Tier 1 | ✅ acquired |
| CC-26 |  | The Life and Opinions of Tristram Shandy, Gentleman | en | EPUB3 | Experimental | ✅ acquired |
| CC-27 |  | The Divine Comedy — illustrated edition | en | EPUB3 | Experimental | ✅ acquired |
| CC-28 |  | Leaves of Grass | en | EPUB3 | Experimental | ✅ acquired |
| CC-29 |  | King James Bible | en | EPUB3 | Experimental | ✅ acquired |
| CC-30 |  | Mrs. Beeton's Book of Household Management | en | EPUB3 | Experimental | ✅ acquired |

## Shortlist operacional

- `CC-01` — Constituição Federal de 1988 — texto atualizado — HTML saved-page bundle — Experimental
- `CC-03` — Tutorial oficial Python 3.14 em português — HTML documentation archive — Experimental
- `CC-04` — Os Lusíadas — PDF — Tier 1
- `CC-05` — Novo dicionário da língua portuguesa — PDF — Tier 1
- `CC-09` — Guia Prático de Direitos de Acessibilidade — DOCX — Experimental
- `CC-11` — The Republic of Plato — EPUB3 — Experimental
- `CC-12` — Histories, Vol. 1 — PDF — Tier 1
- `CC-13` — The Souls of Black Folk — EPUB3 — Experimental
- `CC-14` — The Rust Programming Language — source — Markdown source bundle (ZIP) — Tier 1
- `CC-16` — Dracula — EPUB3 — Experimental
- `CC-18` — Attention Is All You Need — PDF — Tier 1
- `CC-23` — Alice's Adventures in Wonderland — scanned edition — Scanned PDF — Experimental

A presença na shortlist **não altera o support tier**. HTML/EPUB/DOCX/scanned PDF permanecem experimentais no M2 quando fora da claim Tier 1.

## Blind holdouts v1

Os quatro SourceArtifacts reservados (`CC-05`, `CC-07`, `CC-14`, `CC-18`) não podem ser processados, desempacotados, renderizados ou inspecionados antes do freeze do implementation candidate. O protocolo e os escopos cegos permanecem em `corpus/manifests/M2-BLIND-HOLDOUT-SELECTION-V1.json`.

## Aquisições que diferem da curadoria inicial

- `CC-08` *Cartilha de Acessibilidade gov.br*: o candidato PDF ficou indisponível; por decisão explícita foi substituído pelo **eMAG v3.1 oficial**, adquirido como **HTML saved-page bundle**. O objetivo estrutural de acessibilidade/documento institucional é preservado, mas o support tier passa a **Experimental** por HTML estar fora do M2 Tier 1.

- `CC-04` *Os Lusíadas*: adquirido como **PDF**, não EPUB3.
- `CC-07` *Memórias Póstumas de Brás Cubas*: adquirido como **PDF**, não EPUB3.
- `CC-12` *Histories, Vol. 1*: adquirido como **PDF**, não EPUB3.
- `CC-03` Tutorial Python: **HTML ZIP** é a manifestação primária; EPUB preservado como auxiliar.
- `CC-14` Rust Book: ZIP do repositório com Markdown em `book-main/src/`; está em quarentena como holdout e não deve ser desempacotado.

## Aquisição concluída — 30/30

Nenhum CorpusCase permanece pendente. `CC-15` foi adquirido como archive HTML já renderizado da distribuição local `stable rust-docs`, independente do `CC-14` quarantined.

## Provenance de aquisição

A primeira aquisição (14 casos) está em `corpus/manifests/ACQUISITION-20260914.json`. O segundo lote foi recebido no upload `VoxCodex-20260914-163637.zip` e registra 14 novos casos em `corpus/manifests/ACQUISITION-20260914-BATCH2.json`. URLs candidatas verificadas permanecem nos `metadata.json`; o upload não embute prova confiável da URL exata usada para cada byte stream.

## Próximos gates

1. manter o Compatibility Corpus v1 congelado em 30/30;
2. manter os blind holdouts sem reveal;
3. escrever o plano de implementação do M2;
4. revelar holdouts somente após o freeze do implementation candidate, conforme protocolo M2.

## CC-15 — fechamento da aquisição

`CC-15` foi adquirido como `CC-15-rust-book-stable-html.zip`, uma manifestação HTML já renderizada proveniente da distribuição local `stable rust-docs`. O archive contém `index.html`, assets e páginas renderizadas; no registro foram observadas 676 entradas, 462 arquivos HTML e marca de geração `mdBook`, com identificador de Rust 1.90.0 no HTML raiz. O archive bruto é o SourceArtifact normativo; seu desempacotamento futuro será uma derivação de processamento.

A aquisição de `CC-15` foi deliberadamente independente do `CC-14` quarantined, portanto não ocorreu leitura, build ou desempacotamento do SourceArtifact reservado de Markdown para produzir esta manifestação.

## Freeze do Compatibility Corpus v1

Com `CC-01`–`CC-30` adquiridos, membership, manifestações concretas, metadata e bundle digests do Compatibility Corpus v1 ficam congelados. Mudanças futuras — nova edição, substituição de arquivo, alteração de manifestação ou inclusão/remoção de caso — exigem uma versão explícita posterior e não reescrevem v1. O freeze não revela nem altera os M2 Blind Holdouts v1.
