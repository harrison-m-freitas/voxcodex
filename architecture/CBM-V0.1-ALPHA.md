# Canonical Book Model v0.1-alpha — Contrato Normativo Candidate

> **SUPERSEDED FOR CURRENT WORK:** este documento preserva o candidate `v0.1-alpha` usado na validação cross-genre. A baseline normativa corrente está em [`CBM-V0.1.md`](CBM-V0.1.md); [`CBM-V0.1-CANDIDATE.md`](CBM-V0.1-CANDIDATE.md) preserva o candidate congelado usado nos holdouts.


**Status:** `candidate cross-genre validated; pronto para revisão de freeze/promoção`  
**Schema version:** `0.1-alpha`  
**Data de consolidação inicial:** 2026-09-10  
**Base empírica:** F1/F2 (*Fedra*) + W1/W2 (Weidman) + C1 (Leandro Lima) + C2 (*Eternally Regressing Knight*) + C3 (Stewart)  
**Freeze:** não realizado  
**Holdouts cegos:** permanecem fechados até freeze/promoção para `CBM v0.1 candidate`

---

## 1. Propósito e fronteira

O Canonical Book Model (CBM) é a representação canônica versionada de uma edição ingerida. Ele preserva estrutura e conteúdo sustentados pela fonte e permite anexar conhecimento semântico sem transformar inferências em conteúdo da edição.

O CBM está entre Source Evidence e os artefatos derivados:

```text
SOURCE EVIDENCE
PDF / EPUB / imagem / TextSpan / PhysicalPage / Region / Typography
        │
        │ SourceAnchor
        ▼
CANONICAL BOOK MODEL
estrutura + conteúdo canônico
+ entities
+ annotations/relations qualificadas
+ fidelity
+ provenance
        │
        ▼
Semantic Enrichment / Narration Model
        │
        ▼
Performance Model
        │
        ▼
Audio
```

### Regra central

> Inferências podem coexistir com o conteúdo canônico, mas jamais o sobrescrevem. Conhecimento derivado ou inferido entra como `Annotation` ou `Relation`, com status epistemológico, evidência, confiança quando aplicável e provenance.

### Fora da fronteira do CBM

O CBM não contém decisões finais de:

- verbalização;
- leitura/omissão de `SpeakerCue`;
- prosódia;
- elenco de vozes;
- SSML;
- performance;
- TTS;
- áudio;
- explicações narrativas auxiliares;
- resumos narráveis.

Esses elementos pertencem a artefatos downstream.

---

## 2. Estratégia estrutural escolhida

Foram avaliadas hierarquia OO rígida, modelagem graph-first e núcleo composicional tipado.

A direção aprovada é **núcleo composicional tipado**:

```text
DocumentNode
+ ContentFragment
+ extensible role
+ optional StructuredPayload
+ SourceAnchor
+ Annotation
+ Relation
+ Entity
+ FidelityConstraint
+ Provenance
```

A árvore documental é a autoridade para estrutura lógica. Um grafo complementar representa relações e assertions semânticas. Source Evidence permanece fora do CBM e é alcançada por anchors.

Especializações de gênero ou formato não criam novas primitivas universais do core.

---

## 3. Cardinalidades

| Símbolo | Significado |
|---|---|
| `1` | exatamente um |
| `0..1` | opcional |
| `0..N` | zero ou muitos |
| `1..N` | pelo menos um |

IDs são persistentes e independentes de posição sequencial. A tecnologia de ID permanece decisão de implementação posterior.

---

# 4. Identidade e revisions

## 4.1 Hierarquia de identidade

```text
Work
└── Edition
    └── CanonicalDocument
        ├── CanonicalRevision R1
        ├── CanonicalRevision R2
        └── CanonicalRevision R3 ← active
```

- `Work`: obra intelectual.
- `Edition`: edição/manifestaçao concreta usada como unidade de fidelidade.
- `CanonicalDocument`: identidade durável do conjunto de representações canônicas daquela edição.
- `CanonicalRevision`: snapshot lógico versionado do estado canônico.

Fidelidade é relativa à edição/fonte ingerida, não a uma abstração ideal da obra histórica.

## 4.2 CanonicalDocument

```yaml
CanonicalDocument:
  id:
  schema_version:

  work_ref:
  edition_ref:

  source_artifact_refs: []

  active_revision_ref:
  revision_refs: []

  created_at:
```

| Campo | Card. | Regra |
|---|---:|---|
| `id` | 1 | obrigatório |
| `schema_version` | 1 | obrigatório |
| `work_ref` | 1 | obrigatório |
| `edition_ref` | 1 | obrigatório |
| `source_artifact_refs` | 1..N | obrigatório |
| `active_revision_ref` | 0..1 | se presente, aponta para revision `frozen` |
| `revision_refs` | 1..N | obrigatório |
| `created_at` | 1 | obrigatório |

O conteúdo efetivo não vive diretamente no `CanonicalDocument`.

## 4.3 CanonicalRevision

```yaml
CanonicalRevision:
  id:
  canonical_document_ref:

  revision_number:
  parent_revision_refs: []

  schema_version:

  root_node_ref:

  node_registry_ref:
  content_registry_ref:
  entity_registry_ref:
  semantic_registry_ref:
  structured_payload_registry_ref:

  source_mapping_manifest_ref:
  fidelity_manifest_ref:
  provenance_manifest_ref:

  validation_report_ref:

  lifecycle_state:

  created_by_activity_ref:
  created_at:

  content_digest:
```

| Campo | Card. | Regra |
|---|---:|---|
| `id` | 1 | obrigatório |
| `canonical_document_ref` | 1 | obrigatório |
| `revision_number` | 1 | sequência humana; não é identidade técnica |
| `parent_revision_refs` | 0..N | contrato admite DAG |
| `schema_version` | 1 | obrigatório |
| `root_node_ref` | 1 | obrigatório |
| registries | 1 cada | obrigatórios |
| `source_mapping_manifest_ref` | 0..1 | esperado antes de freeze |
| `fidelity_manifest_ref` | 0..1 | opcional no alpha |
| `provenance_manifest_ref` | 1 | obrigatório antes de freeze |
| `validation_report_ref` | 0..1 | obrigatório para `frozen` |
| `lifecycle_state` | 1 | obrigatório |
| `created_by_activity_ref` | 1 | obrigatório |
| `created_at` | 1 | obrigatório |
| `content_digest` | 0..1 | obrigatório para `frozen` |

### Lifecycle

```text
building → validated → frozen → superseded
                     ↘ invalid (quando necessário)
```

Estados permitidos:

- `building`
- `validated`
- `frozen`
- `superseded`
- `invalid`

Revisions `frozen` são semanticamente imutáveis. Correção/reprocessamento produz nova revision.

O contrato admite múltiplos pais, mas a implementação inicial será linear (`R1 → R2 → R3`) enquanto não houver necessidade real de merge.

---

# 5. Estrutura documental

## 5.1 DocumentNode

```yaml
DocumentNode:
  id:

  parent_ref:
  order_key:

  node_class:
  role:

  content_refs: []
  child_refs: []

  structured_payload_ref:

  source_anchor_refs: []

  fidelity_constraints: []

  annotation_refs: []
  relation_refs: []

  provenance_ref:

  status:
```

| Campo | Card. | Regra |
|---|---:|---|
| `id` | 1 | obrigatório |
| `parent_ref` | 0..1 | ausente apenas no root |
| `order_key` | 1 | ordem lógica independente da geometria da fonte |
| `node_class` | 1 | vocabulário pequeno/controlado |
| `role` | 1 | namespaced e extensível |
| `content_refs` | 0..N | fragments do node |
| `child_refs` | 0..N | filhos lógicos |
| `structured_payload_ref` | 0..1 | apenas quando árvore+fragments não bastam |
| `source_anchor_refs` | 0..N | evidência direta quando aplicável |
| `fidelity_constraints` | 0..N | constraints locais/default |
| `annotation_refs` | 0..N | annotations anexadas |
| `relation_refs` | 0..N | relações em que participa |
| `provenance_ref` | 1 | obrigatório |
| `status` | 1 | campo aceito no candidate; vocabulário local ainda será validado |

`PhysicalPage` nunca é pai lógico de `DocumentNode`.

### Mixed-content ordering

Quando um `DocumentNode` contém texto próprio intercalado com child nodes — por exemplo, prosa + fórmula inline + prosa — `ContentFragment.order_key` e `DocumentNode.order_key` dos filhos diretos participam do **mesmo espaço de ordenação lógica relativo ao parent**. `content_refs` e `child_refs` representam membership; não constituem duas sequências independentes para reconstrução.

```text
Paragraph
├── ContentFragment  order=10  "Suppose "
├── FormulaNode      order=20  f(x)
├── ContentFragment  order=30  " is defined when "
├── FormulaNode      order=40  x
└── ContentFragment  order=50  " is near..."
```

Regra validada em C3 (Stewart).

## 5.2 node_class

Vocabulário controlado inicial:

```text
root
division
block
structured_block
declaration
asset
```

O objetivo é manter `node_class` pequeno e estável.

## 5.3 role

`role` descreve o papel específico e é namespaced. O corpus-base e a validação cross-genre comprovaram famílias como:

```text
text.*
drama.*
poetry.*
technical.*
editorial.*
structured.*
narrative.*
math.*
pedagogy.*
```

Roles comprovados/aceitos no candidate incluem:

```text
text.chapter
text.section
text.paragraph
text.heading
text.caption
text.list
text.list_item

drama.act
drama.scene
drama.speech
drama.speaker_cue
drama.participant_declaration

poetry.verse_line

technical.listing
technical.code_block
technical.code_line
technical.terminal_transcript
technical.terminal_command_line
technical.terminal_output_line
technical.terminal_control_line

editorial.admonition
editorial.callout_marker
editorial.footnote
editorial.footnote_marker

narrative.prologue
narrative.utterance
narrative.internal_thought
narrative.scene_break
narrative.embedded_song

math.expression
math.derivation

pedagogy.definition
pedagogy.example
pedagogy.problem_statement
pedagogy.solution
pedagogy.exercise_set
pedagogy.exercise
pedagogy.exercise_part
pedagogy.shared_instruction
pedagogy.tool_marker

structured.table
structured.figure
structured.figure_panel
structured.formula
```

Novos roles continuam sujeitos a Role Profiles e não alteram as primitivas universais.

---

# 6. Conteúdo granular

## 6.1 ContentFragment

```yaml
ContentFragment:
  id:
  owner_node_ref:

  order_key:

  fragment_class:
  role:

  surface:
    text:
    language:

  source_anchor_refs: []

  fidelity_constraints: []

  annotation_refs: []

  provenance_ref:
```

| Campo | Card. | Regra |
|---|---:|---|
| `id` | 1 | obrigatório |
| `owner_node_ref` | 1 | obrigatório no candidate atual |
| `order_key` | 1 | obrigatório |
| `fragment_class` | 1 | vocabulário controlado |
| `role` | 1 | namespaced |
| `surface.text` | 1 | obrigatório para conteúdo textual |
| `surface.language` | 1 | usa `und` quando língua não se aplica/não é determinada |
| `source_anchor_refs` | 0..N | quando há evidência direta |
| `fidelity_constraints` | 0..N | refinamento local |
| `annotation_refs` | 0..N | conhecimento adicional |
| `provenance_ref` | 1 | obrigatório |

### fragment_class

```text
text
literal
marker
symbol
```

Exemplos:

- prosa/verso → `text`;
- `chmod 700 myfile`, `011` → `literal`;
- `❶` → `marker`;
- símbolo matemático → `symbol`.

## 6.2 Surface preservation

`surface.text` preserva a representação sustentada pela fonte naquela revision.

Normalização não é campo substitutivo do fragment. Exemplo:

```text
surface: "esp’rança"

Annotation linguistic.normalization:
  normalized_text: "esperança"
```

O original continua recuperável.

---

# 7. Source Evidence e SourceAnchor

## 7.1 SourceArtifact

Contrato mínimo:

```yaml
SourceArtifact:
  id:
  media_type:
  original_filename:
  checksum:
  byte_size:
```

Source Artifact é imutável e identificado por checksum, não apenas por nome.

## 7.2 SourceAnchor

```yaml
SourceAnchor:
  id:

  source_artifact_ref:

  locator:
    source_page_index:
    printed_page_label:
    region:
    text_range:

  evidence_refs: []

  extraction_ref:

  confidence_ref:
```

Um anchor localiza; não afirma autoria nem interpretação semântica.

### source_page_index vs printed_page_label

São conceitos distintos:

```yaml
source_page_index: 96
printed_page_label: "97"
```

`printed_page_label` é string para comportar `iv`, `97a`, `A-3` etc.

### Region

Forma conceitual canônica:

```yaml
region:
  coordinate_space: normalized
  x: 0.11
  y: 0.32
  width: 0.72
  height: 0.04
```

A geometria nativa do extrator permanece na Source Evidence.

### text_range

Ranges devem ser relativos a uma evidência de extração identificada, nunca a um texto global implícito e mutável.

### Cardinalidade

Um objeto pode possuir `0..N` anchors. Um node cross-page usa múltiplos anchors em vez de uma região fictícia.

---

# 8. Fidelidade

## 8.1 FidelityConstraint

A política fundamental não é um enum único. O alpha usa constraints ortogonais:

```yaml
FidelityConstraint:
  dimension:
  requirement:
```

Dimensões aprovadas:

```text
lexical
character
structure
symbolic
ordering
```

Requirement inicial:

```text
preserve_exactly
```

## 8.2 Perfis convenientes

`textual_exact`, `literal_exact` e equivalentes podem existir como aliases/perfis.

```text
textual_exact =
  lexical: preserve_exactly
  ordering: preserve_exactly

literal_exact =
  character: preserve_exactly
  ordering: preserve_exactly
```

Tabela normalmente exige:

```text
structure: preserve_exactly
ordering: preserve_exactly
lexical: preserve_exactly
```

e uma célula `011` pode acrescentar `character: preserve_exactly`.

## 8.3 Herança

Constraints podem ser herdadas por descendentes/subunidades e refinadas para maior rigor.

Uma constraint herdada não pode ser enfraquecida silenciosamente.

---

# 9. Entidades

## 9.1 Entity

```yaml
Entity:
  id:

  entity_class:
  canonical_label:

  aliases: []

  annotation_refs: []
  relation_refs: []

  provenance_ref:
```

Classes iniciais:

```text
person
character
organization
place
concept
work
artifact
software
other
```

Entities vivem fora da árvore documental.

## 9.2 Aliases e mentions

Mention contextual não vira alias global automaticamente.

`"um pai"` pode resolver para Teseu como `EntityMention` inferida, sem adicionar `"pai"` à lista global de aliases.

---

# 10. Annotation

```yaml
Annotation:
  id:

  target_ref:
  annotation_type:

  value:

  epistemic_status:

  evidence_refs: []

  confidence_ref:

  provenance_ref:
```

`annotation_type` é namespaced, por exemplo:

```text
semantic.entity_mention
semantic.reference_mention
semantic.event
semantic.quotation

linguistic.language
linguistic.normalization

technical.binary_value
technical.command_parse

citation.scripture_reference
citation.bibliographic_reference

narrative.utterance
narrative.internal_thought
narrative.point_of_view
narrative.focalization
narrative.sound_effect

quality.requires_review
```

Cada tipo de annotation define contrato próprio para `value`; `value` não deve virar um bag genérico sem schema.

### EntityMention

É uma Annotation:

```yaml
annotation_type: semantic.entity_mention
value:
  surface: "Teseu"
  entity_ref: entity_teseu
epistemic_status: explicit
```

ou:

```yaml
value:
  surface: "um pai"
  entity_ref: entity_teseu
epistemic_status: inferred
```

Eventos semânticos permanecem annotations no alpha, em vez de virar entidade/event type de primeira classe.

---

# 11. Relation

```yaml
Relation:
  id:

  subject_ref:
  predicate:
  object_ref:

  epistemic_status:

  evidence_refs: []

  confidence_ref:

  provenance_ref:
```

`predicate` é namespaced:

```text
document.introduces
document.refers_to

dramatic.identifies_speaker
dramatic.speaker
dramatic.declares_participant

semantic.interrupts
semantic.same_entity_as
semantic.attributed_to

editorial.explains_callout
editorial.refers_to_note

narrative.speaker
narrative.thinker

pedagogy.applies_to
math.transforms_to
```

Relations são direcionais. Inversas são derivadas por padrão e não precisam ser duplicadas.

### SpeakerCue e Speech — decisão formal

`SpeakerCue` é **sibling** de `Speech`, não child obrigatório.

```text
Scene
├── SpeakerCue
└── Speech
```

Ligação:

```text
SpeakerCue ──document.introduces────────→ Speech
SpeakerCue ──dramatic.identifies_speaker→ Character
Speech     ──dramatic.speaker───────────→ Character
```

A última relação pode ser `derived` a partir das duas primeiras.

### Função semântica em bloco ou span

C2 confirmou que uma função como fala, pensamento ou citação pode coincidir com um bloco documental inteiro **ou** ocupar apenas parte de um parágrafo:

- unidade autônoma na edição → `DocumentNode` + role especializado;
- função restrita a trecho de outro bloco → `Annotation` sobre `ContentFragment`/span.

Speaker/thinker é expresso por `Relation` e pode permanecer não resolvido. O sistema não cria entidade/falante fictício apenas para preencher uma lacuna.

---

# 12. Epistemologia e confiança

## 12.1 epistemic_status

Vocabulário inicial:

```text
explicit
derived
inferred
human_asserted
```

- `explicit`: declarado diretamente pela fonte;
- `derived`: obtido por regra/transformação determinística;
- `inferred`: exige interpretação;
- `human_asserted`: afirmado/revisado explicitamente por humano.

O contrato evita o termo `fact`.

## 12.2 Confidence

```yaml
Confidence:
  value:
  scale:
  basis:
```

Exemplos:

```yaml
value: 1.0
scale: deterministic
basis: direct_structure
```

```yaml
value: 0.86
scale: probability_like
basis: model_output
```

Scores de modelos diferentes não são presumidos diretamente comparáveis.

Confidence serve inicialmente para auditoria, priorização de revisão e human-in-the-loop; não é uma política universal automática.

---

# 13. StructuredPayload e RoleProfile

## 13.1 Regra de escolha

Usar, nesta ordem:

```text
1. DocumentNode + role + ContentFragment
2. hierarquia DocumentNode → child nodes
3. StructuredPayload somente quando 1+2 não preservarem a topologia
```

Uma especialização só é justificada quando muda estrutura, fidelidade ou validação.

## 13.2 RoleProfile

```yaml
RoleProfile:
  role:
  allowed_node_classes: []
  allowed_parent_roles: []
  allowed_child_roles: []

  structured_payload_kind:

  default_fidelity_constraints: []

  semantic_requirements: []
```

Role Profiles validam extensões sem criar herança OO por gênero.

---

# 14. Especializações comprovadas

## 14.1 Drama

```text
drama.act
drama.scene
drama.speech
drama.speaker_cue
drama.participant_declaration
```

`drama.participant_declaration` é específico de formato/gênero; não é primitiva universal.

## 14.2 Poetry

`poetry.verse_line` possui identidade própria e é independente de segmentações linguísticas como Sentence/Clause.

## 14.3 Code

```text
technical.code_block
└── technical.code_line*
```

Lineação/whitespace significativo precisam permanecer reconstruíveis.

## 14.4 Terminal

Terminal é distinto de código:

```text
technical.terminal_transcript
├── technical.terminal_command_line
├── technical.terminal_output_line
└── technical.terminal_control_line
```

Uma command line pode conter fragments distintos:

```text
technical.terminal_prompt
technical.command
```

## 14.5 Listing

`technical.listing` é função editorial e não determina a natureza do conteúdo.

Pode conter `CodeBlock`, `TerminalTranscript` ou outro conteúdo.

## 14.6 Admonition

```text
editorial.admonition
```

Tipo (`note`, `warning`, `tip` etc.) pode ser annotation. Uma nota da fonte permanece distinta de uma nota gerada pelo VoxCodex.

## 14.7 Footnotes, listas e referências externas — C1

C1 validou:

```text
editorial.footnote
editorial.footnote_marker
text.list
text.list_item
```

O marker e a note são ligados por `editorial.refers_to_note`. Referências bíblicas e bibliográficas usam annotations `citation.scripture_reference` e `citation.bibliographic_reference`; citações podem usar `semantic.quotation`. Targets externos não exigem que o objeto referenciado pertença à árvore do livro.

## 14.8 Narrativa — C2

C2 validou:

```text
narrative.prologue
narrative.utterance
narrative.internal_thought
narrative.scene_break
narrative.embedded_song
```

Speaker e thinker usam `narrative.speaker` / `narrative.thinker`. POV/focalização permanecem annotations. `SpeakerCue` não é requisito para fala narrativa e uma atribuição pode permanecer não resolvida.

## 14.9 Matemática e pedagogia — C3

C3 validou roles como:

```text
math.expression
math.derivation
pedagogy.definition
pedagogy.example
pedagogy.problem_statement
pedagogy.solution
pedagogy.exercise_set
pedagogy.exercise
pedagogy.exercise_part
pedagogy.shared_instruction
pedagogy.tool_marker
```

Essas estruturas permanecem extensões/Role Profiles. `pedagogy.applies_to` representa, por exemplo, instrução compartilhada por vários exercícios.

---

# 15. TablePayload

Tabela é o primeiro StructuredPayload plenamente definido pelo golden corpus.

```yaml
TablePayload:
  id:

  row_count:
  column_count:

  cells: []
```

```yaml
TableCell:
  id:

  row:
  column:

  row_span:
  column_span:

  cell_role:

  content_refs: []
  source_anchor_refs: []

  fidelity_constraints: []

  annotation_refs: []
```

Roles iniciais de célula:

```text
header
body
stub
```

A topologia é definida por `row`, `column`, `row_span`, `column_span`, não pela ordem de serialização do array.

Componentes internos semanticamente endereçáveis possuem IDs.

### Caption

Caption é conteúdo editorial linear (`text.caption`) e não deve ser duplicada dentro do TablePayload.

### Exemplo `011`

```text
ContentFragment.surface = "011"

Annotation technical.binary_value:
  radix = 2
  integer_value = 3
  bit_width = 3
```

A interpretação não substitui a superfície.

---

# 16. Figure e Formula — especializações validadas no cross-genre

## 16.1 Figure

```yaml
DocumentNode:
  node_class: asset
  role: structured.figure
```

A figura referencia o asset/evidência original. Caption da edição é canônica; descrição gerada por IA não pode ser promovida silenciosamente a caption.

C3 validou figuras multipainel:

```text
Figure
├── FigurePanel (a)
├── FigurePanel (b)
└── FigurePanel (c)
```

Cada painel relevante usa `structured.figure_panel`, pode ter `SourceAnchor` próprio e participar de referências como `Figure 2(b)`. Labels editoriais permanecem distintos dos IDs canônicos.

Interpretação de gráficos/diagramas é conhecimento derivado e não altera o asset/caption da fonte.

## 16.2 Formula

```yaml
DocumentNode:
  node_class: structured_block
  role: structured.formula
```

C3 confirmou que matemática em PDF não pode ser representada confiavelmente apenas pelo text layer e que estrutura bidimensional/simbólica precisa permanecer reconstruível e auditável.

```yaml
FormulaPayload:
  id:
  source_representation_refs: []
  reconstructed_representation_refs: []
  fidelity_constraints: []
```

Regras:

- `source_representation_refs` preserva representações efetivamente presentes/sustentadas pela fonte;
- `reconstructed_representation_refs` aponta para representações matemáticas reconstruídas;
- reconstrução exige provenance explícita e confidence quando aplicável;
- representação reconstruída nunca é tratada como representação original;
- fidelity estrutural/simbólica pode ser exigida pelo payload;
- nenhuma AST matemática universal é escolhida no `v0.1-alpha`.

C3 validou limits, fractions, superscripts/subscripts, piecewise/cases e derivação multilinha. `math.derivation` pode conter `math.expression` ordenadas. `math.transforms_to` só é criado quando a transformação for efetivamente analisada/derivada.

## 16.3 Math extraction evidence rule

O text layer de PDF matemático é apenas uma fonte de evidência. Se ele perde ou contradiz estrutura visual, não é promovido automaticamente a superfície canônica da fórmula.

Reconstrução pode combinar glyphs, geometria/layout, baseline, scripts, fractions/brackets e região visual, sempre com `Derivation(kind=reconstructed)` e anchors para a evidência original.

---

# 17. Provenance

## 17.1 ProcessingActivity

```yaml
ProcessingActivity:
  id:
  type:

  processor:
    kind:
    name:
    version:

  model:
    provider:
    name:
    version:

  prompt_ref:
  configuration_ref:

  started_at:
  completed_at:

  status:

  usage_ref:
```

Campos de modelo/prompt são ausentes quando não aplicáveis.

Exemplos de activity:

```text
pdf_text_extraction
layout_reconstruction
ocr
speaker_attribution
entity_resolution
table_reconstruction
manual_review
schema_migration
```

## 17.2 Derivation

```yaml
Derivation:
  id:

  activity_ref:

  input_refs: []
  output_refs: []

  derivation_kind:

  confidence_ref:
```

Kinds iniciais:

```text
extracted
reconstructed
normalized
inferred
manually_asserted
corrected
```

Determinístico, OCR, LLM e humano participam do mesmo modelo de lineage.

Correção não apaga o estado anterior; produz nova derivação/revision.

---

# 18. Registries e manifests

Uma revision manifesta membership por registries:

```text
NodeRegistry
ContentRegistry
EntityRegistry
SemanticRegistry
StructuredPayloadRegistry
```

A existência de um objeto no armazenamento não implica pertencimento a uma revision.

Objetos imutáveis não alterados podem pertencer a múltiplas revisions sem uma derivação artificial de “reuse”.

Manifests conceituais:

- `SourceMappingManifest`
- `FidelityManifest`
- `ProvenanceManifest`

Manifests agregam/indexam informação existente e não são segunda fonte de verdade.

---

# 19. Validation

## 19.1 ValidationReport

```yaml
ValidationReport:
  id:
  revision_ref:

  validator_suite_version:

  checks: []

  result:
  created_at:
```

```yaml
ValidationCheck:
  code:
  severity:
  status:
  object_refs: []
  message:
```

Status:

```text
PASS
WARN
FAIL
```

Severity:

```text
info
warning
error
critical
```

Uma revision `frozen` exige ValidationReport compatível com a ValidationPolicy.

## 19.2 ValidationPolicy

```yaml
ValidationPolicy:
  id:
  profile:
  blocking_severities: []
  required_checks: []
```

O PoC poderá usar um perfil único inicialmente.

---

# 20. Digests e reprocessamento

Uma revision frozen possui `content_digest` baseado em representação canônica determinística.

Objetos endereçáveis devem poder possuir fingerprint/digest para detectar mudanças granulares e permitir reprocessamento seletivo.

`schema_version` e `revision_number` são dimensões independentes.

Exemplo:

```text
R8 / schema 0.1-alpha
    ↓ schema_migration
R9 / schema 0.2
```

Migração de schema também é ProcessingActivity e produz nova revision.

Derived artifacts downstream devem registrar exatamente qual revision consumiram:

```text
CBM R8
↓
Narration N14
↓
Performance P21
↓
Audio A39
```

---

# 21. Exemplo mínimo — Fedra

```text
Act
└── Scene
    ├── SpeakerCue
    ├── Speech
    │   ├── VerseLine
    │   └── VerseLine
    ├── SpeakerCue
    └── Speech
```

Relações:

```text
SpeakerCue ──dramatic.identifies_speaker→ Character
SpeakerCue ──document.introduces────────→ Speech
Speech     ──dramatic.speaker───────────→ Character
```

Um `Speech` pode ter anchors em mais de uma página.

`SpeakerCue`, `Speech` e `Character` permanecem objetos distintos.

---

# 22. Exemplo mínimo — Weidman

```text
Section
├── Paragraph
│   └── ReferenceMention("tabela 2.1")
├── Table
│   └── TablePayload
├── Paragraph
│   └── technical.command fragment
└── TerminalTranscript
    ├── TerminalCommandLine
    └── TerminalOutputLine
```

Cross-reference:

```text
Annotation semantic.reference_mention
        ↓
Relation document.refers_to
        ↓
Table 2.1
```

Callout `❶` pode ser fragment separado de output literal e relacionado à explicação editorial por Relation.

---

# 22.1 Validação cross-genre incorporada

| Corpus | Resultado | Extensão principal |
|---|---|---|
| C1 — Leandro Lima, teologia/prosa expositiva | `PASS_WITH_EXTENSION` | footnotes, citações/referências externas, listas |
| C2 — *Eternally Regressing Knight*, webnovel | `PASS_WITH_EXTENSION` | narrativa, utterance/thought, speaker/thinker por Relation |
| C3 — Stewart, cálculo | `PASS_WITH_EXTENSION` | FormulaPayload refinado, figure panels, pedagogia, mixed-content ordering |

Nenhum corpus exigiu nova primitiva universal. Registro completo: `planning/M1-CROSS-GENRE-VALIDATION.md`.

---

# 23. Invariantes de schema S01–S51

## Estrutura e conteúdo

**S01.** Todo `DocumentNode`, exceto root, possui parent lógico.  
**S02.** `SourceArtifact`/`PhysicalPage` não podem ser parents lógicos de conteúdo canônico.  
**S03.** Todo `ContentFragment` possui exatamente um `owner_node_ref` no candidate atual.  
**S04.** `surface.text` não é alterado silenciosamente dentro de uma revision.  
**S05.** `node_class` e `fragment_class` usam vocabulários controlados; `role` é extensível/namespaced.  
**S06.** Assertions inferidas precisam de evidence e provenance.  
**S07.** `StructuredPayload` não substitui a representação sustentada pela fonte.  
**S08.** Constraints de fragment podem ser mais rigorosas que as do node pai.  
**S09.** Relation/Annotation semântica nunca altera diretamente o content canônico.  
**S10.** Objetos canônicos relevantes devem ser rastreáveis à Source Evidence ou a derivação/provenance que os sustenta, conforme sua natureza.

## SourceAnchor, fidelity e provenance

**S11.** Todo `SourceAnchor` referencia `SourceArtifact` imutável.  
**S12.** `source_page_index` e `printed_page_label` são conceitos distintos.  
**S13.** Um objeto pode possuir múltiplos SourceAnchors.  
**S14.** SourceAnchor localiza evidência; não implica autoria nem interpretação semântica.  
**S15.** Constraints podem ser herdadas e refinadas para maior rigor.  
**S16.** Constraint herdada não pode ser enfraquecida silenciosamente.  
**S17.** Toda Derivation referencia uma ProcessingActivity.  
**S18.** Relation/Annotation `inferred` exige evidence e provenance; confidence é exigida quando a atividade a produz/declara.  
**S19.** Correções produzem nova derivação/revision e preservam o estado anterior.  
**S20.** Provenance não depende de o agente ser humano, LLM ou software determinístico.

## Semântica

**S21.** Entity vive fora da árvore documental e possui identidade independente de mentions.  
**S22.** EntityMention nunca altera o surface content que a originou.  
**S23.** Mention contextual não vira alias global automaticamente.  
**S24.** Toda Annotation possui target explícito e tipo namespaced.  
**S25.** Cada `annotation_type` define contrato próprio para `value`.  
**S26.** Relations são direcionais e usam predicates namespaced.  
**S27.** Relation inferida precisa permanecer auditável por evidence/provenance/confidence quando aplicável.  
**S28.** Relações inversas não são persistidas quando puderem ser derivadas com segurança.  
**S29.** Entity resolution/merge é auditável e não apaga silenciosamente identidades anteriores.  
**S30.** Texto gerado não é armazenado dentro de Relation como substituto de artefato derivado próprio.

## Extensões e structured payloads

**S31.** Especializações de gênero/formato são expressas por Role Profiles/roles, não por novas primitivas universais do core.  
**S32.** StructuredPayload só é usado quando tree + fragments não preservam adequadamente a topologia relevante.  
**S33.** StructuredPayload contém estrutura sustentada pela fonte; interpretação derivada fica em Annotation/Relation.  
**S34.** Componentes internos de payload semanticamente endereçáveis possuem identidade estável.  
**S35.** TablePayload preserva coordenadas, spans e conteúdo de células.  
**S36.** Listing é função editorial e não determina o tipo do conteúdo contido.  
**S37.** CodeBlock e TerminalTranscript são estruturas distintas.  
**S38.** Descrição gerada de figura não é promovida silenciosamente a caption da fonte.  
**S39.** Representação matemática reconstruída não é tratada como representação original sem provenance explícita.  
**S40.** Role Profiles validam extensões sem modificar as primitivas do core.

## Revisions e lifecycle

**S41.** `CanonicalDocument` identifica o conjunto durável; conteúdo pertence a `CanonicalRevision`.  
**S42.** `CanonicalRevision` frozen é semanticamente imutável.  
**S43.** Reprocessamento/correção que altera estado canônico produz nova revision.  
**S44.** `schema_version` e `revision_number` são dimensões independentes.  
**S45.** `active_revision_ref` aponta apenas para revision frozen.  
**S46.** Objetos imutáveis não alterados podem pertencer a múltiplas revisions sem derivação artificial.  
**S47.** Toda revision frozen possui ValidationReport compatível com sua ValidationPolicy.  
**S48.** Revisions `invalid`/`superseded` permanecem auditáveis e não são eliminadas silenciosamente.  
**S49.** Derived artifacts downstream referenciam explicitamente a revision do CBM consumida.  
**S50.** Manifests agregam/indexam informação existente; não constituem segunda fonte de verdade.  
**S51.** Em conteúdo misto, `ContentFragment` e child `DocumentNode` diretamente pertencentes ao mesmo parent compartilham uma única ordem lógica por `order_key`; `content_refs` e `child_refs` não criam ordens concorrentes.

---

# 24. Invariantes arquiteturais M1-I01–M1-I18

O schema acima implementa **18 invariantes arquiteturais** empíricos aprovados durante F1/F2/W1/W2:

1. page boundary ≠ semantic boundary;
2. source surface preservation;
3. `SpeakerCue` ≠ `Character` ≠ `Speech`;
4. evidence ≠ inference;
5. `VerseLine` identity ≠ `Sentence`;
6. narration outside CBM;
7. faithful authored-text fidelity;
8. structural continuity across processing boundaries;
9. declared state ≠ inferred transition;
10. canonical role ≠ semantic implication;
11. genre specialization must not contaminate core;
12. source presentation may carry semantic evidence;
13. physical recurrence ≠ logical duplication;
14. fidelity is locally refinable;
15. literal fidelity ≠ semantic flattening;
16. structural fidelity of structured data;
17. surface representation ≠ interpreted value;
18. visual adjacency ≠ common semantic origin.

---

# 25. Conformidade v0.1-alpha

Uma implementação só pode alegar conformidade conceitual com `CBM v0.1-alpha` se suportar pelo menos:

- `CanonicalDocument`;
- `CanonicalRevision`;
- `DocumentNode`;
- `ContentFragment`;
- `SourceArtifact`;
- `SourceAnchor`;
- `FidelityConstraint`;
- `Entity`;
- `Annotation`;
- `Relation`;
- `ProcessingActivity`;
- `Derivation`;
- `ValidationReport`;
- `TablePayload` quando houver conteúdo tabular;
- `FormulaPayload` quando houver matemática cuja topologia/simbolismo não possa ser preservado adequadamente apenas por fragments/árvore.

Roles específicos são exigidos apenas quando o documento contém aquela estrutura.

---

# 26. Questões deliberadamente abertas no candidate

A validação cross-genre foi concluída. Permanecem abertas questões que não exigem redesign do core antes do freeze:

1. **Ownership de fragments em StructuredPayload:** `ContentFragment.owner_node_ref` continua apontando para o `DocumentNode` contêiner enquanto componentes como `TableCell.content_refs` referenciam fragments. C1–C3 não demonstraram necessidade suficiente para mudar o core.
2. **Vocabulário de `DocumentNode.status`:** o campo existe, mas seus valores normativos ainda não foram necessários pelo corpus.
3. **Representação matemática estruturada concreta:** `FormulaPayload` foi validado/refinado, mas MathML, AST própria ou outra serialização ainda não foi escolhida.
4. **Governança de Role Profiles:** registry físico/versionamento ainda serão definidos.
5. **Serialização física do CBM:** JSON Schema, Pydantic, Protobuf, SQL etc. continuam fora de escopo.
6. **Digest/canonical serialization:** requisito aprovado; algoritmo não escolhido.
7. **Confidence calibration:** comparação/calibração entre modelos permanece futura.
8. **Interpretação semântica de figuras:** figures/panels foram validados estruturalmente; interpretação visual continua derivada.

---

# 27. Estado e próximo gate

```text
CBM v0.1-alpha candidate — CROSS-GENRE VALIDATED
```

```text
C1 — teologia/prosa expositiva   PASS_WITH_EXTENSION
C2 — webnovel/narrativa          PASS_WITH_EXTENSION
C3 — matemática/textbook         PASS_WITH_EXTENSION
Universal core primitive changes 0
```

Registro: `planning/M1-CROSS-GENRE-VALIDATION.md`.

Próximo gate:

```text
revisão final de freeze/promoção
        ↓
CBM v0.1 candidate (frozen para teste)
        ↓
abrir F-RND + W-RND
        ↓
blind conformance result
```

Os holdouts continuam fechados e não foram usados em C1–C3.

---

## 28. Decisões explicitamente adiadas

Não fazem parte deste contract freeze:

- stack de persistência;
- ORM;
- API;
- workflow engine;
- embeddings/vector DB;
- Narration Model schema;
- Performance Model;
- Voice Registry;
- TTS/SSML;
- tradução;
- AST matemática universal;
- interpretação universal de figuras.

Esses itens só serão decididos quando houver requisitos concretos suficientes.
