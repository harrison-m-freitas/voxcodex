# Plataforma de Audiobooks Inteligentes — Base de Contexto

Este diretório é a **fonte de verdade do projeto**.

Seu objetivo é impedir que decisões arquiteturais, hipóteses, requisitos, riscos e escopo do PoC
fiquem dispersos apenas no histórico de conversa.

## Como usar

Sempre que uma decisão relevante for tomada:

1. atualizar `PROJECT_CONTEXT.md`;
2. registrar a decisão em `decisions/ADR-LOG.md`;
3. atualizar o documento temático correspondente;
4. atualizar `CHANGELOG.md`;
5. se necessário, alterar `STATUS.json`.

## Ordem recomendada de leitura

1. `PROJECT_CONTEXT.md`
2. `requirements/REQUIREMENTS.md`
3. `architecture/ARCHITECTURE.md`
4. `architecture/CANONICAL-BOOK-MODEL.md`
5. `architecture/CBM-V0.1.md` — baseline normativa corrente
6. `architecture/M2-DESIGN-V0.1.md` — contrato normativo congelado do M2
7. `planning/M2-DOCUMENT-RECONSTRUCTION.md` — histórico de elaboração do M2
8. `planning/COMPATIBILITY-CORPUS.md` — regressão/descoberta e evolução de schema
9. `M2-DESIGN-V0.1-FREEZE-MANIFEST.json` — freeze final do M2 Design v0.1
10. `planning/OPEN-QUESTIONS.md`
11. `decisions/ADR-LOG.md`
12. `risks/RISK-REGISTER.md`
13. `planning/M1-PROMOTION-REVIEW.md`
14. `PROMOTION-MANIFEST.json`
15. `architecture/CBM-V0.1-CANDIDATE.md` — candidate congelado/histórico
16. `planning/M1-CBM-FREEZE-REVIEW.md`
17. `FREEZE-MANIFEST.json`
18. `planning/M1-HOLDOUT-CONFORMANCE.md`
19. `HOLDOUT-CONFORMANCE-MANIFEST.json`
20. `architecture/CBM-V0.1-ALPHA.md` — histórico pré-freeze
21. `planning/M1-CANONICAL-REPRESENTATION.md`
22. `planning/M1-CROSS-GENRE-VALIDATION.md`
23. `poc/POC.md`
24. `planning/FUTURE.md`

## Estado atual

- M1 — **Canonical Representation: CONCLUÍDO**.
- Golden slices F1/F2/W1/W2: concluídos e aprovados.
- Cross-genre C1/C2/C3: `PASS_WITH_EXTENSION`, zero mudanças no core universal.
- Blind holdouts: F-RND=`PASS`; W-RND=`PASS_WITH_EXTENSION`; `MODEL_GAP=0`, `MODEL_FAILURE=0`.
- CBM normativo corrente: **`v0.1` PROMOTED** (`schema_version=0.1`) em `architecture/CBM-V0.1.md`.
- Invariantes: **18 arquiteturais + S01–S56**.
- Candidate congelado e manifests permanecem preservados como trilha de auditoria.
- Baseline tecnológica de implementação M2: **selecionada no implementation plan**; o contrato arquitetural continua independente da stack.
- Corpus do PoC: **Fedra** + **Testes de Invasão**.
- Produto-base: **Audiobook Fiel**.
- M2 — **Document Reconstruction & CBM Materialization: DESIGN v0.1 FROZEN**.
- M2.1–M2.6: **APROVADOS E CONGELADOS** após review consolidado e correções B1–B5/Q1–Q8.
- Fronteira M2: `SourceArtifact → Source Evidence → Document Reconstruction → CBM v0.1 CanonicalRevision → Validation/freeze`.
- Tier 1 inicial: **PDF textual + Markdown**; PDF mixed é Tier 1.5; OCR-heavy/EPUB/HTML/DOCX ficam adiados no primeiro recorte.
- Compatibility Corpus: shortlist de regressão **8–12** + corpus ampliado de descoberta **~30**, com Schema Evolution Log.
- Plano de implementação do M2: **aprovado e em execução inline**; o Plan 01 — Foundation & Contracts possui implementação funcional e aguarda apenas o gate ambiental exato Python 3.14.7/uv lock antes de promoção.

Para o milestone corrente, leia primeiro `architecture/M2-DESIGN-V0.1.md`, depois `planning/COMPATIBILITY-CORPUS.md`. Para o encerramento do M1, consulte `planning/M1-PROMOTION-REVIEW.md`.


## Estado corrente do design M2

M2.1–M2.6 estão congelados no contrato `architecture/M2-DESIGN-V0.1.md`, com manifest final `M2-DESIGN-V0.1-FREEZE-MANIFEST.json`. O freeze histórico M2.1–M2.3 permanece preservado em `M2-DESIGN-FREEZE-MANIFEST.json`.

## M2 consolidated review status

O review consolidado inicialmente encontrou 5 blockers; todos foram resolvidos em `planning/M2-CONSOLIDATED-DESIGN-RESOLUTION.md`. O freeze review final retornou `PASS`; ver `planning/M2-FINAL-FREEZE-REVIEW.md`.


## M2 Design v0.1

Contrato arquitetural congelado do milestone M2: `architecture/M2-DESIGN-V0.1.md`. Review final: `planning/M2-FINAL-FREEZE-REVIEW.md`. A implementação foi iniciada pelo Plan 01 após o freeze; o contrato arquitetural deste arquivo permanece inalterado.

## Compatibility Corpus v1

O corpus concreto pré-implementação está em `corpus/`. São 30 casos curados e adquiridos; a shortlist está 12/12 e o **Compatibility Corpus v1 está FROZEN 30/30**. Veja `planning/COMPATIBILITY-CORPUS-V1.md`.


## Plano de implementação M2

O roadmap e seis subplanos executáveis estão em `docs/superpowers/plans/`. A baseline proposta é Python 3.14 + Pydantic + SQLite/SQLAlchemy/Alembic + filesystem content-addressed + PyMuPDF + markdown-it-py. Nenhum holdout M2 pode ser processado antes do candidate freeze.


## Desenvolvimento M2

O setup reproduzível, migrations, comandos de teste, artifact store e regra de quarentena estão em `docs/development.md`. A implementação do Plan 01 preserva a baseline Python 3.14.7 declarada; o lock exato deve ser produzido em ambiente com essa toolchain disponível.
