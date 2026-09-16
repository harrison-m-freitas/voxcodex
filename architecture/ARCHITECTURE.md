# Arquitetura Conceitual

## Domínios

1. Source & Ingestion
2. Document Reconstruction
3. Canonical Content
4. Book Understanding
5. Editorial Adaptation
6. Voice & Performance
7. Audio Production
8. Workflow & Execution
9. Governance & Provenance
10. Economics

Preocupações transversais:

- observabilidade;
- segurança;
- human-in-the-loop;
- qualidade.

## Fluxo principal

```text
Book Project
    ↓
Source Evidence
    ↓
Document Reconstruction
    ↓
Canonical Book Model
    ↓
Semantic Enrichment
    ↓
Narration Model
    ↓
Audio Performance Model
    ↓
TTS Rendering
    ↓
Audio QA
    ↓
Audiobook Assembly
```

Em paralelo:

```text
Workflow Engine
Provenance Ledger
Cost Engine
Human Review
Observability
```

## Macroetapas

### A. Intake e evidência

- upload;
- fingerprint/checksum;
- inventário;
- inspeção barata;
- estimativa de complexidade;
- estimativa preliminar de custo.

### B. Reconstrução documental

EPUB:
```text
manifest → spine → XHTML → metadata → estrutura
```

PDF textual:
```text
text objects → geometria → reading order → estrutura
```

PDF escaneado:
```text
page image → preprocessing → layout → OCR → reading order → estrutura
```

### B.1. Evidência preservada antes da interpretação

A reconstrução não deve reduzir a fonte prematuramente a texto plano. Quando relevante, Source Evidence preserva:

- texto superficial;
- posição/region/bounding box;
- tipografia e ênfase;
- índice físico da página e fólio/rótulo impresso;
- ordem/estrutura visual;
- distinção entre conteúdo principal e anotações/callouts editoriais.

Essas propriedades são evidência; roles semânticos derivados permanecem separados e auditáveis.

### C. Compreensão

```text
segmentação estrutural
→ análise local
→ síntese global
→ refinamento semântico
→ reconciliação entre capítulos
```

### D. Preparação editorial

```text
CBM + interpretação + perfil da obra + preferências
→ planejamento de narração
→ Narration Model
```

### E. Produção sonora

```text
Narration
→ speaker assignment
→ pronúncia
→ performance instructions
→ TTS segmentation
→ synthesis
→ audio QA
→ assembly
```

## Distribuição das responsabilidades

### Determinístico

- hash;
- parsing de formatos;
- metadados simples;
- contagem;
- deduplicação exata;
- validações estruturais;
- cobertura;
- checks de integridade.

### Modelos especializados

- OCR;
- layout;
- rotação;
- perspectiva;
- qualidade visual;
- alguns tipos de document understanding.

### LLMs

- classificação literária;
- entidades;
- aliases;
- speaker attribution ambígua;
- interpretação semântica;
- adaptação de conteúdo visual;
- explicações;
- resumos;
- análise contextual.

### Humano

Prioritário quando houver alto impacto e baixa confiança:

- OCR crítico;
- speaker attribution;
- fórmulas;
- pronúncia;
- vozes;
- adaptações editoriais problemáticas.

## CBM v0.1 — PROMOTED

O contrato canônico corrente está especificado em `CBM-V0.1.md` (`schema_version=0.1`). `CBM-V0.1-CANDIDATE.md` permanece preservado como candidate congelado usado no blind holdout conformance; `CBM-V0.1-ALPHA.md` é o predecessor histórico pré-freeze.

A fronteira é:

```text
Source Evidence
      ↓ SourceAnchor
CanonicalRevision
      ├── Document Tree
      ├── ContentFragments
      ├── Entities
      ├── Annotations/Relations
      ├── StructuredPayloads
      ├── Fidelity
      └── Provenance
      ↓
Narration Model
```

Decisões arquiteturais relevantes:

- inferência não modifica content canônico;
- `DocumentNode` + `ContentFragment` compõem o núcleo estrutural;
- especializações usam roles/Role Profiles;
- TablePayload preserva topologia tabular e FormulaPayload preserva separação entre representações fonte/reconstruídas;
- fidelity usa constraints ortogonais;
- revisions frozen são imutáveis;
- lineage usa ProcessingActivity + Derivation;
- consumers downstream referenciam a CanonicalRevision exata;
- `technical.terminal_input` e `editorial.omission_marker` são extensões namespaced validadas nos holdouts.

O CBM passou pela validação cross-genre e pelo blind holdout conformance sem mudança de primitivas universais ou invariantes após o freeze. O promotion review resultou em `PASS`; M1 está concluído e `CBM v0.1` é a baseline normativa do M2.



## M2 — Document Reconstruction & CBM Materialization

M2.1 aprovou a fronteira operacional inicial do próximo milestone:

```text
SourceArtifact
    ↓
Source Inspection
    ↓
Source Evidence / EvidenceSnapshot
    ↓
Document Reconstruction / ReconstructionSnapshot
    ↓
CBM v0.1 CanonicalRevision
    ↓
Validation
    ↓
frozen CanonicalRevision
```

Princípios:

- evidência é preservada antes da interpretação;
- intermediários são inspecionáveis e reprocessáveis;
- falha de extração/reconstrução deve ser distinguível de lacuna do CBM;
- processamento determinístico é preferido quando suficiente;
- Semantic Enrichment interpretativo permanece downstream do M2;
- Tier 1 inicial: PDF textual + Markdown; PDF mixed é Tier 1.5;
- OCR universal e suporte inicial a EPUB/HTML/DOCX não bloqueiam o M2.

O Compatibility Corpus passa a ser mecanismo transversal de QA, com classificação explícita de `PROCESSING_FAILURE` separada de `MODEL_GAP`/`MODEL_FAILURE`. Detalhes: `../planning/M2-DOCUMENT-RECONSTRUCTION.md` e `../planning/COMPATIBILITY-CORPUS.md`.

## M2 — Source Evidence e Reconstruction — baseline congelada até M2.3

O caminho aprovado antes da materialização canônica é:

```text
SourceArtifact
  → SourceProfile
  → EvidenceSnapshot / EvidenceUnit
  → ReconstructionSnapshot / ReconstructionUnit
  → M2.4 Canonical materialization
  → CBM v0.1 CanonicalRevision
```

`EvidenceUnit` preserva observação física/sintática e payload nativo; não contém role canônico. `ReconstructionUnit` representa hipóteses/estrutura lógica derivada, com confidence/provenance e issues explícitos. Reading order é derivado na Reconstruction. `OpenStructuralState` impede que página/chunk/batch/worker imponham fronteiras documentais artificiais.

A Reconstruction é conceptualmente um DAG de grouping, ordering, classification, cross-boundary reconciliation, structured reconstruction e assembly. Esses estágios não implicam microservices. Gênero não é roteador primário; módulos estruturais especializados são acionados pelo conteúdo/evidência.

Invariantes aprovados nesta camada: E01–E10 e R01–R13; `parent_ref + order_key` são autoridade hierárquica de ReconstructionUnit.

## M2 — Materialization, reprocessing e validation gates

M2.4–M2.6 completam conceitualmente o caminho:

```text
SourceArtifact
  → EvidenceSnapshot
  → ReconstructionSnapshot
  → CanonicalDraft
  → CanonicalRevision CBM v0.1
  → ValidationReport/Policy
  → frozen revision
```

M2.4 é fronteira de **materialização**, não de nova interpretação: gera DocumentNodes/ContentFragments/StructuredPayloads/SourceAnchors/Fidelity/Provenance a partir de Reconstruction resolvida e executa validação em schema, estrutura, traceability/fidelity, integridade cross-object e evidence accountability.

M2.5 torna o pipeline um DAG reprocessável: `ProcessingActivity` + fingerprints semânticos + dependency-driven invalidation + cache provenance + confidence localizada + ReviewRisk + Usage/Cost + `ExecutionPlan`. Reprocessamento parcial cria novos artefatos; outputs anteriores permanecem auditáveis.

M2.6 transforma corpus em QA executável: Regression Core, Compatibility Shortlist, Discovery Corpus e novos Blind Holdouts. Known significant silent loss bloqueia M2; `PROCESSING_FAILURE` continua distinto de inadequação do CBM. Exit exige validation/freeze, traceability, idempotência, selective reprocessing e conformance cega.

O `M2 Design v0.1` completo está congelado em `M2-DESIGN-V0.1.md` após correções do review consolidado. Nenhuma alteração de core foi feita no CBM v0.1; stack e implementação continuam deliberadamente não selecionadas.



## M2 — Correções finais de autoridade e governança

- `Derivation` é autoridade causal de input/output; `ProcessingActivity` descreve execução.
- Reconstruction hierarchy usa `parent_ref + order_key`; `child_refs` é projeção.
- `CanonicalTargetContext` operacional resolve bootstrap de CanonicalDocument/Work/Edition.
- revision frozen mantém seu freeze-authorizing `validation_report_ref`; revalidation posterior é suplementar externa.
- `stale` é contextual; evidence/provenance de revisions frozen deve permanecer endereçável.
- blind holdouts congelam assertions/selection e depois candidate identity/config/claims antes do reveal.
- Compatibility gates são por support tier; MODEL_GAP que mude schema exige rebaseline explícito.
