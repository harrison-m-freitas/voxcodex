# M2 — Design Freeze Review through M2.3

## Resultado

**PASS — design aprovado/congelado até M2.3.**

Data: 2026-09-11

## Escopo congelado

- M2.1 — Boundary & Success Contract;
- M2.2 — Source Artifact & Evidence Model;
- M2.3 — Reconstruction Pipeline;
- Compatibility Corpus / Schema Evolution policy já aprovada como requisito transversal.

Não estão congelados:

- M2.4 — CBM Materialization & Validation;
- M2.5 — Reprocessing, confidence & provenance;
- M2.6 — Compatibility Corpus & exit criteria executáveis;
- stack, storage, ORM, workflow engine, serialization física e providers.

## Verificações arquiteturais

1. `CBM v0.1` permanece baseline normativa sem alteração.
2. Source Evidence e Reconstruction são camadas externas/anteriores ao CBM e não reabrem o core.
3. `EvidenceSnapshot` e `ReconstructionSnapshot` são imutáveis/versionáveis e mantêm provenance.
4. reading order lógico é responsabilidade da Reconstruction, não da Evidence.
5. page/chunk/batch/worker não se tornam boundaries documentais automaticamente.
6. incerteza pode sobreviver via `ReconstructionIssue`; perda silenciosa não é aceita.
7. módulos especializados para tabela/código/terminal/fórmula/figura não exigem parser por gênero.
8. M2 continua restrito a SourceArtifact → CanonicalRevision CBM v0.1; Semantic Enrichment e Narration permanecem downstream.

## Invariantes congelados nesta etapa

### Evidence
E01–E10.

### Reconstruction
R01–R12.

## Gate seguinte

Projetar M2.4 — **CBM Materialization & Validation** sem modificar M2.1–M2.3 salvo evidência nova registrada em ADR.
