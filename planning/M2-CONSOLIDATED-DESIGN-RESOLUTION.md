# M2 — Resolução dos findings do review consolidado

Data: 2026-09-11  
Review de origem: `planning/M2-CONSOLIDATED-DESIGN-REVIEW.md`  
Resultado: **B1–B5 e Q1–Q8 RESOLVIDOS**.

## Blockers

- **B1 — RESOLVIDO:** `Derivation` é autoridade normativa de `input_refs/output_refs`; `ProcessingActivity` permanece unidade/metadata de execução. Dependency DAG e invalidation derivam das `Derivation`s.
- **B2 — RESOLVIDO:** `parent_ref + order_key` são autoridade hierárquica de `ReconstructionUnit`; `child_refs` é apenas projeção derivável. Novo invariante `R13`.
- **B3 — RESOLVIDO:** criado `CanonicalTargetContext` operacional para target existente ou provisionamento auditável de `CanonicalDocument`, com `work_ref`, `edition_ref`, `source_artifact_refs` e `base_revision_ref?`.
- **B4 — RESOLVIDO:** `validation_report_ref` de revision frozen é o freeze-authorizing report e não pode ser substituído. Revalidation posterior cria reports suplementares externos. Freeze gate usa os refs exatos do CBM v0.1.
- **B5 — RESOLVIDO:** protocolo cego passa a congelar assertions + seleção dos holdouts antes do tuning e implementation candidate + claims/configuração antes do reveal. Novos invariantes `C15–C16`.

## Clarificações

- **Q1:** `stale` é estado contextual do planner/índice, nunca mutação do artefato histórico.
- **Q2:** conceitos operacionais M2 não são novas primitivas CBM; `DerivedArtifact` é termo guarda-chuva operacional.
- **Q3:** `ReconstructionSnapshot.reconstruction_validation_ref` aponta para validação operacional de reconstruction, não para CBM `ValidationReport`.
- **Q4:** significância/accountability/severity de Evidence é controlada por policy/configuração versionada referenciada pela ValidationPolicy.
- **Q5:** gates da Compatibility Shortlist são avaliados por `CorpusCase.support_tier`; shortlist não implica support claim.
- **Q6:** promoção de novo schema após MODEL_GAP exige ADR/rebaseline explícito ou nova versão do M2 Design.
- **Q7:** Evidence/provenance referenciados por frozen revision devem permanecer endereçáveis durante a retention/audit policy.
- **Q8:** o contrato imutável final é `architecture/M2-DESIGN-V0.1.md`; o freeze histórico anterior de M2.1–M2.3 permanece preservado.

## Impacto no CBM

Nenhuma alteração em `architecture/CBM-V0.1.md`, nenhuma nova primitiva universal e nenhuma mudança em S01–S56.
