# Questões em Aberto

## Estado

O **`CBM v0.1` foi promovido em 2026-09-11** e o M1 — Canonical Representation foi encerrado.

Contrato normativo corrente: `architecture/CBM-V0.1.md`  
Promotion review: `planning/M1-PROMOTION-REVIEW.md`  
Candidate/freeze preservados como histórico auditável.

Não há blocker normativo aberto para o CBM v0.1; os itens abaixo foram deliberadamente adiados para implementação, downstream ou evolução futura.

## Itens deliberadamente adiados — não bloqueantes

1. **Representação matemática estruturada concreta** — MathML, AST própria ou outra serialização; `FormulaPayload` já separa source vs reconstructed representations.
2. **Governança de Role Profiles** — registry físico, versionamento e política de namespaces.
3. **Canonical serialization e digests** — semântica do digest está definida; algoritmo/formato determinístico ainda não.
4. **Confidence calibration** — scores entre processors/modelos não são assumidos comparáveis.
5. **Interpretação semântica de figuras** — figure/panel é canônico; interpretação visual continua derivada.
6. **Formato físico/serialização do CBM** — JSON Schema, Pydantic, Protobuf etc.

## Decisões tecnológicas deliberadamente adiadas

- banco relacional/documental;
- representação física do grafo semântico;
- workflow engine;
- estratégia de cache/retries;
- providers de OCR/LLM/TTS;
- embeddings/vector database;
- armazenamento físico de prompts/respostas.

## Decisões downstream ainda abertas

- schema do Narration Model;
- contrato Narration → Performance;
- SSML vs JSON vs DSL;
- Voice/Character Voice Registry;
- Pronunciation Dictionary;
- política de invalidação/reprocessamento CBM → Narration → Performance → Audio;
- granularidade final de audio segments;
- estratégia de custo/usage por activity.

## Questões abertas específicas do M2

As seis seções arquiteturais M2.1–M2.6 estão aprovadas e congeladas em `architecture/M2-DESIGN-V0.1.md`.

Questões deliberadamente deixadas para review/implementação, sem decisão prematura:

- schema físico/serialização de EvidenceSnapshot, ReconstructionSnapshot, CanonicalDraft e ExecutionPlan;
- algoritmo de canonical digest/fingerprint e normalização determinística;
- estratégia de IDs estáveis vs IDs operacionais;
- armazenamento/indexação do dependency DAG e cache;
- thresholds/policies concretas de validation, confidence e ReviewRisk;
- taxonomia operacional final de failure/retry;
- granularidade atômica inicial para partial outputs e region-level reprocessing;
- representação física de UsageRecord/pricing/cost;
- mecanismo executável das assertions do Compatibility Corpus;
- representação matemática concreta (MathML/AST/etc.) permanece evolução/implementação, não blocker do design;
- providers externos de OCR/LLM continuam deliberadamente não selecionados; a baseline local do M2 foi escolhida no plano de implementação e não inclui esses providers.

## Próximo passo

Revisar `docs/superpowers/plans/2026-09-14-m2-master-implementation-roadmap.md` e os seis subplanos. Após aprovação, iniciar pelo Plan 01 mantendo os quatro holdouts frozen/unrevealed.

O CBM v0.1 continua baseline normativa estável; qualquer necessidade de evolução deve usar Schema Evolution Log e novo candidate/versionamento explícito.

## Findings do review consolidado M2.1–M2.6 — RESOLVIDOS

O review inicial está em `planning/M2-CONSOLIDATED-DESIGN-REVIEW.md`; as resoluções B1–B5/Q1–Q8 estão em `planning/M2-CONSOLIDATED-DESIGN-RESOLUTION.md`. O freeze review final retornou `PASS` em `planning/M2-FINAL-FREEZE-REVIEW.md`.


## Estado após freeze do M2 Design v0.1

Os findings B1–B5 e Q1–Q8 do review consolidado foram resolvidos em `planning/M2-CONSOLIDATED-DESIGN-RESOLUTION.md`. Não há blocker arquitetural aberto para o freeze do M2 Design v0.1.

O plano de implementação agora fixa uma baseline física inicial para schema/serialização, digests, storage/indexação, bibliotecas locais e mecanismo executável das assertions. Permanecem deliberadamente adaptáveis durante a implementação: thresholds concretos, políticas de ReviewRisk/failure, tuning de reconstrução e qualquer eventual provider externo de OCR/LLM.

Próximo gate: revisão dos planos de implementação; depois, execução do Plan 01.
