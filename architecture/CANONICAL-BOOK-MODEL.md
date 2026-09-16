# Canonical Book Model — Visão e Estado

## Estado atual

O M1 foi concluído e o contrato canônico foi promovido para:

> **`CBM v0.1 — PROMOTED`**

Especificação normativa corrente: [`CBM-V0.1.md`](CBM-V0.1.md).

Trilha histórica/auditável:

- [`CBM-V0.1-CANDIDATE.md`](CBM-V0.1-CANDIDATE.md) — candidate congelado usado nos holdouts;
- [`CBM-V0.1-ALPHA.md`](CBM-V0.1-ALPHA.md) — predecessor pré-freeze;
- `planning/M1-CBM-FREEZE-REVIEW.md`;
- `planning/M1-HOLDOUT-CONFORMANCE.md`;
- `planning/M1-PROMOTION-REVIEW.md`.

A evidência empírica cobre F1/F2/W1/W2, C1/C2/C3 e os dois blind holdouts. O resultado agregado foi `MODEL_GAP=0`, `MODEL_FAILURE=0` e zero mudanças em primitivas universais/invariantes após o freeze. W-RND adicionou somente `technical.terminal_input` e `editorial.omission_marker` ao vocabulário extensível.

## Objetivo

Criar uma representação independente do formato de entrada, preservando vínculo auditável com a edição/fonte e distinguindo rigorosamente:

```text
estrutura/conteúdo canônico
≠
evidência física
≠
assertions semânticas
≠
representação para narração
```

## Núcleo aprovado

```text
CanonicalDocument
└── CanonicalRevision
    ├── Document Tree
    │   └── DocumentNode
    │       ├── ContentFragment
    │       ├── child DocumentNodes
    │       └── StructuredPayload? 
    │
    ├── Entity Registry
    ├── Semantic Layer
    │   ├── Annotation
    │   └── Relation
    │
    ├── Source Mapping
    │   └── SourceAnchor
    │
    ├── FidelityConstraint
    │
    ├── Provenance
    │   ├── ProcessingActivity
    │   └── Derivation
    │
    └── Validation
        └── ValidationReport
```

Source Evidence permanece fora do CBM e é referenciada por `SourceAnchor`.

Narration/Performance/Audio permanecem downstream.

## Modelo de extensão

O CBM não usa uma grande hierarquia OO por gênero.

A direção aprovada é:

```text
DocumentNode
+ node_class controlado
+ role namespaced/extensível
+ ContentFragment
+ Annotation/Relation
+ optional StructuredPayload
```

Especializações como:

- `drama.scene`;
- `drama.speech`;
- `technical.terminal_transcript`;
- `technical.code_block`;
- `structured.table`;

não se tornam primitivas universais.

## SpeakerCue e Speech

Decisão aprovada:

```text
Scene
├── SpeakerCue
└── Speech
```

São siblings ligados por relações explícitas.

`Character`, `SpeakerCue` e `Speech` permanecem conceitos distintos.

## Fidelity

Fidelity foi consolidada como constraints ortogonais:

```text
lexical
character
structure
symbolic
ordering
```

com requirement inicial `preserve_exactly`.

Perfis como `textual_exact` e `literal_exact` são aliases convenientes sobre conjuntos de constraints.

## Structured payloads

`StructuredPayload` só é usado quando tree + fragments não preservam adequadamente a topologia.

`TablePayload` permanece o payload tabular plenamente definido. C3 validou `FormulaPayload` como especialização necessária, separando representações da fonte de reconstruções com provenance. Figuras multipainel foram validadas com `structured.figure_panel`. Uma AST matemática universal continua adiada.

## Versionamento

`CanonicalDocument` é a identidade durável.

`CanonicalRevision` é o snapshot lógico versionado.

```text
building → validated → frozen → superseded
```

Revisions frozen são imutáveis. Correções e reprocessamentos produzem novas revisions.

O contrato admite DAG de revisions, mas a implementação inicial será linear.

## Provenance e epistemologia

Todo processamento usa o mesmo modelo de lineage:

```text
ProcessingActivity
        ↓
Derivation
```

independentemente de ser:

- parser determinístico;
- OCR;
- LLM;
- humano;
- migração.

Assertions semânticas usam:

```text
explicit
derived
inferred
human_asserted
```

Inferências nunca alteram diretamente conteúdo canônico.

## Invariantes

Os golden slices produziram **18 invariantes arquiteturais M1-I01–M1-I18**.

O `CBM v0.1` define **56 invariantes de schema S01–S56**.

A lista normativa completa está em `CBM-V0.1.md` (S01–S56).

## Questões ainda abertas

Após a promoção permanecem como itens não bloqueantes:

- representação matemática estruturada concreta/AST;
- Role Profile registry;
- serialização física;
- digest/canonical serialization;
- confidence calibration;
- interpretação semântica derivada de figures.

## Blind holdout conformance

Relatório: `planning/M1-HOLDOUT-CONFORMANCE.md`.

- F-RND: `PASS`;
- W-RND: `PASS_WITH_EXTENSION`;
- extensões promovidas: `technical.terminal_input`, `editorial.omission_marker`;
- core changes: 0;
- `MODEL_GAP`: 0;
- `MODEL_FAILURE`: 0.

## Promotion review

Resultado: **PASS**. Baseline corrente: `architecture/CBM-V0.1.md` (`schema_version=0.1`). O M1 está encerrado.

## Próximo passo

M2 foi iniciado com `CBM v0.1` como baseline normativa. Próximo design gate: **M2.2 — Source Artifact & Evidence Model**. Ver `../planning/M2-DOCUMENT-RECONSTRUCTION.md`.
