# M2 Plan 04 lineage resolution

Status: **RESOLVED**

The divergent branch `m2-plan04-materialization-validation` is a superseded historical implementation line and is not part of the normative M2 lineage.

## Normative lineage

`m2-plan04-cbm-materialization` → `m2-plan05-reprocessing-provenance` → `m2-plan06-corpus-candidate-freeze`

## Historical preservation

The original final state of the superseded branch is preserved at:

- archive branch: `archive/m2-plan04-materialization-validation-70b75d4`
- original final commit: `70b75d4ef8de91d7fb74df817c70e50d91befa88`

The live historical branch was tombstoned after archival: its automatic schema-generation workflow was disabled and the branch was marked `SUPERSEDED`.

## Rationale

The divergent line contains an earlier alternative CBM v0.1 implementation. The consolidated `m2-plan04-cbm-materialization` line has the accepted canonical gate evidence and is the sole supported base for Plans 05 and 06.

The superseded branch must not be merged into the normative line.

## Holdout integrity

This lineage resolution does not access, reveal, unpack, parse, re-hash, or tune against any blind holdout SourceArtifact. CC-05, CC-07, CC-14, and CC-18 remain frozen and unrevealed.
