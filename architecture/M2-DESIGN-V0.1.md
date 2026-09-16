# M2 Design v0.1 — Document Reconstruction & CBM Materialization

## Estado normativo

- status: **FROZEN**
- freeze date: **2026-09-11**
- baseline CBM: `architecture/CBM-V0.1.md`
- baseline CBM SHA-256: `788c2a8e6229d2141346f46cc80928d8df3c4ed6a2f323770865dab94ab12dd3`
- seções congeladas: **M2.1–M2.6**
- invariantes: **E01–E10, R01–R13, M01–M14, P01–P16, C01–C16**
- review de origem: `planning/M2-CONSOLIDATED-DESIGN-REVIEW.md`
- resolução: `planning/M2-CONSOLIDATED-DESIGN-RESOLUTION.md`
- implementação/stack: **não selecionadas neste freeze**

Este arquivo é o contrato arquitetural normativo congelado do M2. O documento `planning/M2-DOCUMENT-RECONSTRUCTION.md` permanece como histórico de elaboração. Manifests e snapshots anteriores continuam históricos e não são sobrescritos.

Princípios corretivos já incorporados: `Derivation` é a autoridade causal de lineage; `ReconstructionUnit.parent_ref + order_key` são a autoridade hierárquica; bootstrap canônico usa `CanonicalTargetContext`; revision frozen preserva seu freeze-authorizing `validation_report_ref`; blind protocol congela assertions/selection e candidate claims/config; `stale` é contextual; Evidence significance é policy-controlled; support gates são por tier; rebaseline exige decisão explícita.

---

## Pergunta do milestone

> Dado um arquivo real, o VoxCodex consegue preservar a evidência, reconstruir sua estrutura lógica e produzir automaticamente um CBM v0.1 auditável, validável e reprocessável?

---

# M2.1 — Boundary & Success Contract — FROZEN

## Fronteira

O M2 começa em um `SourceArtifact` e termina em uma `CanonicalRevision` conforme o **CBM v0.1**, validada e apta a ser congelada.

```text
SourceArtifact
      ↓
Intake / fingerprint
      ↓
Source inspection
      ↓
Source Evidence
      ↓
Document Reconstruction
      ↓
Canonical mapping
      ↓
CBM v0.1 CanonicalRevision
      ↓
Validation
      ↓
frozen CanonicalRevision
```

O M2 não tem como objetivo produzir Narration, Performance ou Audio.

### Fora da fronteira do M2

Permanece downstream, salvo o mínimo necessário para materializar estruturas explicitamente sustentadas pela fonte:

- entity resolution complexo;
- speaker attribution ambígua;
- POV/focalização interpretativa;
- interpretação literária global;
- resumo;
- adaptação editorial;
- Narration Model;
- Performance Model;
- TTS/audio.

Inferências semânticas não necessárias à reconstrução documental não são critério de fechamento do M2.

## Intermediários inspecionáveis

O pipeline não deve ser uma única função opaca `parse_document() -> CBM`.

```text
SourceArtifact
      ↓
EvidenceSnapshot
      ↓
ReconstructionSnapshot
      ↓
CanonicalRevision
```

Essa separação deve permitir diagnosticar se uma falha ocorreu em extração/evidência, reconstrução ou materialização canônica.

## Política de processamento

Preferência de escalonamento:

```text
parser/regra determinística
        ↓ quando insuficiente
modelo especializado
        ↓ quando necessário
LLM
        ↓ quando a ambiguidade justificar
human review
```

LLM não deve ser usado quando solução determinística ou especializada puder entregar qualidade equivalente de forma mais previsível.

## Formatos no primeiro recorte

### Tier 1

- PDF textual;
- Markdown.

### Tier 1.5

- PDF mixed/parcialmente visual.

O M2 deve preservar evidência e detectar limitações, mas OCR universal não é critério de fechamento.

### Adiados no primeiro recorte

- PDF predominantemente escaneado/OCR-heavy;
- EPUB;
- HTML;
- DOCX;
- suporte universal a containers.

## Critérios preliminares de sucesso

O M2 deve demonstrar, em fontes selecionadas:

1. nenhuma perda silenciosa conhecida;
2. `SourceAnchor`s reconstruíveis;
3. reading order lógico correto nos casos de conformidade;
4. continuidade entre páginas preservada;
5. running headers/fólios sem duplicação no logical tree;
6. code e terminal distinguíveis;
7. topologia de tabela preservada;
8. footnotes ligadas a seus markers quando sustentadas pela fonte;
9. mixed content texto↔fórmula mantendo ordem lógica;
10. região/evidência visual de fórmula preservada mesmo quando parsing simbólico falhar;
11. provenance para transformações relevantes;
12. `ValidationReport` para a revision produzida;
13. reprocessamento idempotente para mesma fonte/configuração quando aplicável;
14. possibilidade conceitual de reprocessar etapa sem reconstruir desnecessariamente toda a cadeia;
15. Compatibility Corpus executável sobre múltiplos documentos.

Não são critérios de fechamento do M2: 100% de speaker attribution/entity resolution, interpretação visual perfeita, AST matemática perfeita ou OCR universal.

Princípio de qualidade:

> Quando o sistema não souber, deve preservar evidência e representar incerteza; não inventar uma resolução para preencher a lacuna.

---

# M2.2 — Source Artifact & Evidence Model — FROZEN

## Objetivo

M2.2 é a camada de **memória física** do VoxCodex. Ela preserva o que existe/foi observado na fonte antes de qualquer reconstrução de capítulos, parágrafos, falas, tabelas, fórmulas ou outros papéis documentais.

Princípio central:

> **Source Evidence descreve observação da fonte; não decide ainda seu papel documental canônico.**

Assim, uma linha grande em negrito no topo da página pode ser evidência de tamanho, peso e posição sem ainda ser `text.heading`.

## Arquitetura aprovada

```text
SourceArtifact
      ↓ immutable bytes
SourceProfile
      ↓ inspection
EvidenceSnapshot
      ↓
EvidenceUnit*
      ↓
Document Reconstruction (M2.3)
```

A estratégia escolhida é **envelope comum + payloads específicos de formato**:

```text
COMMON EVIDENCE ENVELOPE
        ├── PDF payload
        ├── Markdown payload
        ├── futuro EPUB payload
        ├── futuro HTML payload
        └── futuro OCR payload
```

Não será usado nem um schema universal achatado para todos os formatos nem famílias totalmente independentes que eliminem contratos comuns.

## SourceArtifact

Representa a identidade dos bytes recebidos.

```yaml
SourceArtifact:
  id:
  media_type:
  original_filename:
  byte_size:
  checksum:
  acquisition:
    kind:
    original_uri?:
  created_at:
```

Regras:

- bytes originais são imutáveis;
- nome de arquivo não é identidade suficiente;
- artefatos reparados, normalizados, renderizados ou OCRizados são derivados, nunca sobrescrevem o original;
- transformação de um SourceArtifact gera `DerivedArtifact`/artefato derivado com provenance.

## SourceProfile

Inspeção barata usada para escolher rotas de processamento, sem elevar heurística operacional a verdade documental.

```yaml
SourceProfile:
  id:
  source_artifact_ref:
  format_family:
  declared_media_type:
  detected_media_type:
  language_hints: []
  characteristics: {}
  recommended_routes: []
  provenance_ref:
```

Exemplos de características PDF: page count, text layer, coverage, fonts, rotation, image coverage, páginas mixed. Markdown: encoding, headings, fences, links, tables, embedded HTML.

Regra explícita:

> `text_layer_present` não implica `text_layer_authoritative`.

Stewart permanece o caso de referência: texto extraído pode ser plausível e ainda destruir semântica matemática.

## EvidenceSnapshot

Cada execução de extração produz snapshot imutável e versionável.

```yaml
EvidenceSnapshot:
  id:
  source_artifact_ref:
  extraction_activity_ref:
  extraction_profile_ref:
  root_evidence_refs: []
  created_at:
  snapshot_digest:
```

Múltiplos snapshots/extractors podem coexistir para a mesma fonte. Um snapshot anterior nunca é apagado porque outro extractor foi considerado melhor.

## EvidenceUnit

Envelope operacional genérico da camada de evidência:

```yaml
EvidenceUnit:
  id:
  snapshot_ref:
  parent_ref:
  evidence_class:
  source_locator:
  surface:
  presentation:
  native_payload:
  confidence_ref:
  provenance_ref:
```

Vocabulário inicial de `evidence_class`:

```text
physical_page
region
line
text_span
glyph_run
asset
syntax_unit
```

Essas classes descrevem observação física/sintática. Elas deliberadamente não são `paragraph`, `heading`, `speech`, `table` ou `formula`.

## PDF evidence

PDF pode preservar, conforme disponibilidade e necessidade:

- páginas físicas;
- regiões;
- spans/linhas;
- glyph runs quando granularidade fina for necessária;
- geometria nativa + normalizada;
- typography/presentation;
- assets raster/vetoriais;
- payload nativo específico do adapter.

Typography pode preservar font family/size/weight/italic/baseline etc., mas nenhum atributo visual isolado possui semântica universal.

### Geometria

Preservar dois espaços quando disponíveis:

- geometria nativa do formato/extractor;
- geometria normalizada para consumo interoperável.

A normalização não substitui a evidência nativa.

### Granularidade adaptativa

Nem toda prosa precisa virar glyph-level evidence. Glyph runs tornam-se relevantes em regiões como matemática, símbolos ou PDFs problemáticos. O modelo admite granularidade variável para equilibrar custo e fidelidade.

## Markdown evidence

Markdown preserva raw source, ranges e sintaxe observável.

Exemplo:

```markdown
*O ar está pesado.*
```

Pode produzir `syntax_unit=emphasis`, mas `narrative.internal_thought` só aparece em Reconstruction/Semantic interpretation.

Assim:

```text
Markdown AST/syntax
≠
CBM structure/semantics
```

## Ordem

M2.2 separa:

```text
native/file order
visual/geometric order
logical reading order
```

Preserva as duas primeiras quando disponíveis e **não decide a terceira**. Logical reading order pertence a M2.3.

## Confidence e provenance

Evidence confidence mede confiança da observação/extração, não a confiança de classificação documental.

Cada EvidenceUnit deve ser rastreável a:

```text
SourceArtifact
+ ProcessingActivity
+ processor/version/configuration
```

Extração imperfeita permanece auditável; correções não reescrevem snapshots antigos.

## Overlays / extrações concorrentes

PDF text extractor, layout detector, renderer e OCR podem gerar evidências independentes sobre a mesma região. Não existe uma etapa obrigatória de fusão em uma EvidenceUnit “verdadeira”. A reconciliação pertence à Reconstruction.

## Relação com SourceAnchor

`SourceAnchor` continua no CBM e aponta de objetos canônicos para `SourceArtifact`/Evidence/locators. EvidenceUnit não depende do futuro CBM.

Direção:

```text
CBM object
   ↓ SourceAnchor
SourceArtifact / EvidenceUnit / locator
```

## Invariantes M2.2 — E01–E10

**E01.** SourceArtifact representa bytes imutáveis.  
**E02.** Transformações nunca sobrescrevem SourceArtifact original.  
**E03.** EvidenceSnapshot é imutável e vinculado a uma atividade de extração.  
**E04.** Evidence descreve observação/sintaxe física, não papel documental canônico.  
**E05.** Typography/layout podem ser preservados como evidência sem implicar semântica.  
**E06.** Native order, geometric order e logical reading order são conceitos distintos.  
**E07.** Evidence confidence mede observação/extraction, não interpretação documental.  
**E08.** Payloads específicos de formato complementam, mas não substituem, o envelope comum.  
**E09.** CBM SourceAnchor pode referenciar evidência sem que EvidenceUnit dependa do CBM.  
**E10.** Extrações concorrentes/alternativas podem coexistir sem que uma apague a outra.

---

# M2.3 — Reconstruction Pipeline — FROZEN

## Objetivo

M2.3 transforma Evidence físico/sintático em **estrutura documental lógica reconstruída**, mantendo hipótese, confidence e provenance separados da evidência original.

Regra central:

```text
Evidence
   ↓
Reconstruction hypotheses
   ↓
resolved document structure
   ↓
CBM materialization (M2.4)
```

Não existe conversão direta Evidence → CBM.

## ReconstructionSnapshot

```yaml
ReconstructionSnapshot:
  id:
  source_evidence_refs: []
  reconstruction_activity_ref:
  reconstruction_profile_ref:
  root_unit_refs: []
  reconstruction_validation_ref:
  created_at:
  snapshot_digest:
```

É imutável e permite reprocessar reconstruction sem repetir necessariamente a extração. `reconstruction_validation_ref` aponta para um resultado operacional específico de Reconstruction; ele **não** reutiliza o `ValidationReport` canônico, que exige `revision_ref`.

## ReconstructionUnit

```yaml
ReconstructionUnit:
  id:
  reconstruction_snapshot_ref:
  parent_ref:
  order_key:
  reconstruction_class:
  evidence_refs: []
  child_refs: []
  properties: {}
  confidence_ref:
  provenance_ref:
```

Classes intermediárias iniciais:

```text
document
division_candidate
block_candidate
line_group
structured_candidate
auxiliary_candidate
```

A camada deve permitir hipótese incompleta/ambígua antes de materializar papéis canônicos.

Autoridade normativa da hierarquia: `parent_ref + order_key`. `child_refs`, se materializado, é apenas projeção/índice derivável e deve ser validado contra essa autoridade. Topologias/memberships especializadas de conteúdo estruturado permanecem governadas por seus contratos próprios.

## Estágios conceituais

```text
EvidenceSnapshot
       ↓
R0 — evidence normalization
       ↓
R1 — geometric grouping
       ↓
R2 — reading-order reconstruction
       ↓
R3 — block reconstruction
       ↓
R4 — structural classification
       ↓
R5 — cross-boundary reconciliation
       ↓
R6 — structured-content reconstruction
       ↓
R7 — document assembly
       ↓
ReconstructionValidation
       ↓
ready for M2.4
```

Esses são estágios conceituais/DAG de módulos, **não sete serviços**.

### R0 — Evidence normalization

Cria views comuns para comparação/acesso sem substituir native evidence. Normalizações Unicode ou geométricas são derivadas/views, nunca reescrita silenciosa de surface.

### R1 — Geometric grouping

Agrupa glyphs/spans/linhas/regiões/colunas quando necessário. Markdown pode praticamente pular esse estágio porque sua estrutura sequencial já é explícita.

### R2 — Reading order

Logical reading order é derivado e possui provenance/confidence. Native order e geometric order não são assumidos equivalentes ao reading order.

Ordem pode ser hierárquica/local; tabela/fórmula mantêm topologias próprias em vez de serem forçadas a uma sequência textual global.

### R3 — Block reconstruction

Agrupa evidência em candidatos como paragraph, heading, code/terminal, footnote, table etc., ainda podendo carregar múltiplos papéis candidatos.

Reconstrução de parágrafo deve lidar explicitamente com line wrap, hifenização de layout, continuidade entre colunas e páginas. `layout_dehyphenation` é uma derivação rastreável, não correção silenciosa.

### R4 — Structural classification

Resolve papéis documentais usando múltiplos sinais: typography, posição, spacing, recorrência, padrões textuais, vizinhança e contexto. Nenhum estilo isolado (`bold`, monospace etc.) possui significado universal.

Reconstrói também hipóteses de parent/child e hierarquia lógica.

### R5 — Cross-boundary reconciliation

Reconcilia unidades cortadas por:

- página;
- coluna;
- chunk;
- batch;
- worker.

Processing boundary nunca vira boundary documental sem evidência.

#### OpenStructuralState

```yaml
OpenStructuralState:
  open_units: []
  pending_continuations: []
  unresolved_boundaries: []
```

É estado operacional, não CBM, e permite manter parágrafo/fala/nota/etc. abertos até contexto suficiente.

Recorrência cross-page também auxilia detectar running headers/fólios e impedir duplicação lógica.

### R6 — Structured-content reconstruction

Módulos especializados podem reconstruir, quando necessário:

- Table;
- Code;
- Terminal;
- Formula;
- Figure.

Isso não implica microservices.

**Tables:** preservar rows/columns/cells/spans/topology antes de qualquer linearização.  
**Code:** preservar characters, indentation, line breaks e ordering.  
**Terminal:** distinguir prompt/input/output/control/omission quando evidência sustentar; baixa confiança pode manter papel menos específico.  
**Formula:** primeiro preservar/detectar região/evidência; symbolic reconstruction é opcional e derivada.  
**Figure:** detectar asset/region/caption/panels quando suportado; interpretação visual/descrição continua downstream.

### Footnotes e references

Reconstrução separa:

- detection de marker/reference mention;
- resolution de target.

Detectar referência sem resolvê-la é válido e preferível a inventar target.

### R7 — Document assembly

Produz uma estrutura lógica suficiente para M2.4 materializar CBM sem reabrir a fonte de forma opaca:

```text
ReconstructedDocument
├── logical hierarchy
├── logical ordering
├── blocks
├── inline composition
├── structured candidates
├── source evidence links
├── confidence
├── unresolved issues
└── provenance
```

## ReconstructionIssue

Incerteza/falha local é primeira classe:

```yaml
ReconstructionIssue:
  id:
  issue_type:
  severity:
  affected_refs: []
  message:
  confidence_ref:
  suggested_action:
```

Exemplos:

```text
ambiguous_reading_order
unresolved_continuation
possible_table
formula_parse_failed
footnote_target_missing
role_low_confidence
```

Falha de interpretação não autoriza perda de evidência. Uma região pode permanecer parcialmente compreendida e ainda assim seguir para review/materialização conservadora.

## Confidence e human review

Confidence deve poder ser localizada em decisões como grouping, reading order, role, continuation, table topology e reference resolution. Scores não precisam ser campos fixos universais, mas devem ser associáveis à decisão que qualificam.

Human review é orientado a regiões/decisões de risco, não ao livro inteiro por padrão.

## DAG e feedback controlado

Os estágios podem formar DAG. Por exemplo, table detection pode alterar reading order local. Iterações/reprocessamentos devem ser `ProcessingActivity` explícitas, associadas a `Derivation`s que registram as arestas causais `input_refs/output_refs`; reason/configuration pertencem à metadata/configuração da execução. Loops opacos não são permitidos.

## Genre-agnostic

Gênero não é roteador primário:

```text
NÃO:
detect genre → choose parser

SIM:
detect structures → reconstruct → document profile may emerge
```

Livros podem combinar prosa, cartas, tabelas, poesia, código, footnotes e outros fenômenos independentemente do gênero editorial declarado.

## Golden reconstruction cases

A primeira suíte deve reaproveitar:

- F1 — SpeakerCue/Speech/verse;
- F2 — continuidade cross-page;
- W1 — listing + terminal + code + note;
- W2 — table + callout;
- C1 — columns + footnotes;
- C2 — Markdown narrative + inline formatting;
- C3 — math + figures + exercises;
- F-RND — página iniciando no meio da fala;
- W-RND — terminal input/output + omission marker.

## Invariantes M2.3 — R01–R13

**R01.** Reconstruction nunca altera EvidenceSnapshot.  
**R02.** Toda unidade reconstruída aponta para evidência ou derivação que justifique sua existência.  
**R03.** Logical reading order é derivado; nunca presumido igual ao native order.  
**R04.** Processing/chunk boundaries não criam boundaries documentais automaticamente.  
**R05.** Unidades podem permanecer abertas através de páginas/chunks até reconciliação.  
**R06.** Recorrência física não implica duplicação lógica.  
**R07.** Classificação documental pode usar múltiplos sinais; nenhum estilo visual isolado possui semântica universal.  
**R08.** Structured content preserva topologia relevante antes de qualquer linearização.  
**R09.** Incerteza é representada; o pipeline não inventa resolução apenas para completar o documento.  
**R10.** Falha de interpretação não autoriza perda de evidência.  
**R11.** ReconstructionSnapshot é imutável e versionável.  
**R12.** Gênero não é requisito nem roteador primário de reconstrução.  
**R13.** `parent_ref + order_key` são a autoridade normativa da hierarquia de `ReconstructionUnit`; `child_refs`, se persistido, é somente projeção derivável e deve ser consistente com essa autoridade.

---

# M2.4 — CBM Materialization & Validation — FROZEN

## Objetivo

M2.4 transforma um `ReconstructionSnapshot` resolvido em uma `CanonicalRevision` conforme `CBM v0.1` e prova que o resultado satisfaz o contrato canônico. **M2.4 não reinterpreta a fonte, não redefine reading order e não substitui decisões de Reconstruction.**

Fluxo aprovado:

```text
ReconstructionSnapshot
        ↓
CanonicalDraft
        ↓
structural/schema validation
        ↓
CanonicalRevision building
        ↓
full validation
        ↓
validated
        ↓
freeze autorizado pela policy
```

`CanonicalDraft` é conceito operacional do M2, não nova primitiva normativa do CBM.

## CanonicalTargetContext

Antes da primeira materialização, M2.4 recebe um contexto operacional de target/intake; ele **não** é nova primitiva CBM.

```yaml
CanonicalTargetContext:
  canonical_document_ref?:
  work_ref:
  edition_ref:
  source_artifact_refs: []
  base_revision_ref?:
  assertion_provenance_ref:
```

- se `canonical_document_ref` existir, a materialização produz uma nova revision para esse documento;
- na primeira materialização, `Work`/`Edition` refs vêm de metadata de intake ou assertion humana auditável — M2 não inventa identidade bibliográfica;
- `CanonicalDocument` e a primeira `CanonicalRevision` são provisionados de forma logicamente consistente/atômica;
- `base_revision_ref` é opcional e identifica a lineage correta em rematerializações.

## MaterializationRun

```text
MaterializationRun
├── reconstruction_snapshot_ref
├── target_schema_version = 0.1
├── activity_ref
├── configuration_ref
├── draft_ref
├── resulting_revision_ref
└── status
```

Estados operacionais: `building`, `validating`, `succeeded`, `failed`.

## CanonicalDraft

O draft pode estar incompleto e conter issues enquanto é construído. Uma `CanonicalRevision frozen` não pode.

Conceitualmente agrega:

- root lógico;
- node/content/entity/semantic/structured-payload registries;
- source anchors;
- provenance;
- materialization issues.

## Mapping controlado

Quando M2.3 já resolveu `resolved_role`, parent lógico, order e evidence refs, M2.4 faz mapping predominantemente determinístico:

```text
ReconstructionUnit(block_candidate, text.paragraph)
→ DocumentNode(block, text.paragraph)
```

Nem toda ReconstructionUnit vira `DocumentNode`: conteúdo inline pode virar `ContentFragment`; structured candidates viram `DocumentNode + StructuredPayload`; assertions documentais resolvidas podem virar `Annotation`/`Relation`.

## SourceAnchor

Source-derived canonical content deve ser ligado sistematicamente à evidência quando aplicável:

```text
CBM object
  → SourceAnchor
  → EvidenceUnit/locator
  → SourceArtifact
```

Anchors podem ser granulares ou agregados/derivados. Objetos que atravessam páginas usam múltiplos anchors; não se fabricam regiões físicas impossíveis.

## Fidelity

Fidelity é aplicada por policy/RoleProfile, nunca ad hoc:

- prosa autoral/editorial → lexical/ordering conforme perfil fiel;
- comando/código literal → character/ordering exact;
- tabela → structure/ordering exact;
- verso → lexical/ordering exact;
- refinamentos locais podem aumentar rigor, nunca reduzi-lo silenciosamente.

O validator precisa conseguir calcular fidelity efetiva mesmo que a implementação não copie constraints herdadas para todos os descendants.

## StructuredPayload materialization

M2.4 materializa, sem reconstruir novamente:

- `TablePayload` a partir de table candidate resolvido;
- `FormulaPayload` preservando source representation e, quando disponível, reconstructed representation com provenance;
- figure/panels e demais structured specializations já resolvidas em M2.3.

Parse matemático perfeito não é requisito de validade se a representação da fonte estiver preservada e o limite estiver explicitamente registrado.

## Semântica documental permitida

Pode ser materializada quando já foi resolvida documentalmente em M2.3, por exemplo:

- footnote marker → footnote;
- SpeakerCue → Speech;
- caption → figure;
- ReferenceMention → target documental;
- Listing contains TerminalTranscript.

Semantic Enrichment interpretativo permanece downstream: emoção, significado, POV complexo, causalidade, interpretação literária etc.

## Validation em camadas

A validação é organizada em:

1. **Schema validation** — tipos, cardinalidades, IDs e refs;
2. **Structural validation** — árvore, ordering, RoleProfile, payload/topologia;
3. **Traceability/Fidelity validation** — source mapping, provenance e constraints;
4. **Cross-object integrity** — relações, registries, structured consistency;
5. **Evidence accountability/coverage** — evidência significativa contabilizada.

### Evidence accountability

Evidence significativa não mapeada deve ser classificada explicitamente, por exemplo:

- `canonicalized`;
- `intentionally_noncanonical`;
- `unresolved`;
- `suspected_loss`.

Running headers/fólios podem ser não-canônicos sem serem “perdidos”. `suspected_loss` significativo é blocker conforme policy.

A definição de “evidência significativa”, sua severity e o tratamento de `suspected_loss` são controlados por policy/configuração versionada ligada à `ValidationPolicy`; não existe threshold global implícito.

## ValidationPolicy e freeze

A identidade/configuração da `ValidationPolicy` usada deve ser imutável e referenciável; isso não adiciona campo novo ao schema congelado do CBM. Uma revision vai de `building` para `validated` somente quando todos os required checks executarem. O freeze exige, conforme o `CBM v0.1`:

- nenhum blocking failure;
- `content_digest` calculado;
- `source_mapping_manifest_ref` obrigatório;
- `provenance_manifest_ref` obrigatório;
- `validation_report_ref` obrigatório e apontando para o **freeze-authorizing report**;
- `fidelity_manifest_ref` continua opcional no v0.1.

Uma `CanonicalRevision` frozen pode receber `ValidationReport`s suplementares externos porque cada report referencia `revision_ref`, mas seu `validation_report_ref` autorizador original não é substituído. Se uma nova policy precisar autorizar novo freeze, usa-se nova revision/fluxo explícito; a revision frozen não é mutada.

`validation succeeded` e `freeze authorized` são eventos conceitualmente distintos.

## Idempotência

Mesmo `ReconstructionSnapshot` + schema + configuração semanticamente relevante deve produzir resultado semanticamente equivalente e, idealmente, o mesmo canonical digest, ainda que IDs operacionais de execução variem.

## MaterializationIssue

Falhas de mapping/materialization ficam explícitas e classificáveis, por exemplo:

- `processing_error`;
- `unsupported_extension`;
- `schema_violation`;
- `possible_model_gap`.

Vocabulário namespaced extensível não implica mudança de core; necessidade de nova primitiva universal é tratada como possível `MODEL_GAP`.

## Invariantes M2.4 — M01–M14

**M01.** M2.4 não reinterpreta Evidence nem redefine logical reading order.  
**M02.** Toda unidade canônica materializada é justificável por Reconstruction/Evidence/Provenance.  
**M03.** Materialização deve ser semanticamente determinística para entradas/configuração equivalentes.  
**M04.** CanonicalDraft pode ser incompleto; CanonicalRevision frozen não.  
**M05.** Source-derived canonical content é rastreável à fonte quando aplicável.  
**M06.** StructuredPayload deriva de StructuredCandidate compatível ou derivação explícita equivalente.  
**M07.** Fidelity constraints são aplicadas por policy/role e nunca enfraquecidas silenciosamente.  
**M08.** Semântica documental resolvida pode ser materializada; enrichment interpretativo permanece downstream.  
**M09.** Evidence significativa não mapeada é contabilizada explicitamente.  
**M10.** Falha de materialization/validation não autoriza perda ou sobrescrita dos snapshots de entrada.  
**M11.** ValidationReport e ValidationPolicy usados no freeze são versionados/reproduzíveis.  
**M12.** Apenas revision sem blocking failures pode ser frozen.  
**M13.** Extension vocabulary não implica mudança de core; necessidade de nova primitiva deve ser reportada como possível MODEL_GAP.  
**M14.** Mesmo ReconstructionSnapshot + schema + configuração deve produzir resultado semanticamente idempotente.

---

# M2.5 — Reprocessing, Confidence & Provenance — FROZEN

## Objetivo

Evitar o modelo “mudou uma coisa → refaça o livro inteiro”. Outputs relevantes são imutáveis/versionados, atividades declaram dependências e o DAG permite reutilização e reprocessamento seletivo.

## ProcessingActivity operacional

No M2, `ProcessingActivity` é a unidade de execução e registra processor/version, configuração semanticamente relevante, status, usage/cost e timestamps. As arestas causais `input_refs/output_refs` pertencem **normativamente a `Derivation`**, que referencia a activity. Exemplos de activities incluem source inspection, extraction, layout detection, reconstruction, table/formula reconstruction, materialization, validation e manual review.

Inputs devem ser identificados por refs/digests imutáveis.

## ActivityFingerprint e cache

Conceitualmente:

```text
ActivityFingerprint =
  activity_type
  + processor/version
  + semantic configuration
  + input digests
  + relevant schema/profile versions
```

Cache reuse é permitido somente quando compatibilidade dos inputs/configuração estiver estabelecida. Reuso não cria provenance falsa: o output continua ligado à activity que realmente o produziu.

## Dependency-driven invalidation

Invalidação propaga-se pelas dependências reais downstream derivadas das `Derivation`s e de suas arestas `input_refs/output_refs`, agrupadas pelas `ProcessingActivity`s correspondentes, em vez de uma matriz global hard-coded. Devem ser possíveis níveis document-level, stage-level e region/unit-level.

`stale` é estado contextual calculado/registrado pelo planner/índice em relação a uma target lineage; não é mutação do payload ou digest do artefato histórico. O artefato permanece historicamente auditável.

## Retry vs reprocessing

- falha transitória sem output válido pode ser retried conforme policy;
- mudança de input/model/prompt/config/algoritmo cria nova ProcessingActivity;
- outputs parciais só são reutilizáveis quando a unidade foi declarada atomicamente completa.

## Confidence localizada

Confidence qualifica a decisão específica, por exemplo:

- extraction/OCR confidence;
- reconstruction/continuation confidence;
- role confidence;
- anchor/alignment confidence;
- semantic inference confidence.

Não existe `document_confidence` universal. Scores de produtores/tipos distintos não são considerados comparáveis sem calibração explícita.

## ReviewRisk

Risk é distinto de confidence. Priorização de human review considera incerteza, impacto documental/semântico e custo downstream. Não há fórmula numérica congelada nesta etapa.

## ReviewDecision

Correção humana é uma atividade/derivação auditável, não `UPDATE` silencioso. Decisões podem aceitar, corrigir, rejeitar ou adiar; `human_asserted` registra origem, não verdade eterna.

## Provenance vs Observability

- **Provenance:** origem/derivação, inputs, outputs, processor, configuração;
- **Observability:** duração, latência, memória, stack de erro, retries, queue wait etc.

São modelos relacionados, mas distintos.

## Natureza dos artefatos operacionais

`SourceProfile`, `EvidenceSnapshot/Unit`, `ReconstructionSnapshot/Unit`, `OpenStructuralState`, `ReconstructionIssue`, `CanonicalDraft`, `CanonicalTargetContext`, `MaterializationRun/Issue`, `ActivityFingerprint`, `ExecutionPlan`, `ReviewRisk`, `ReviewDecision` e `DerivedArtifact` são **contratos operacionais do M2**, não novas primitivas do núcleo CBM. `DerivedArtifact` é termo operacional guarda-chuva até definição do schema físico.

Artefatos de evidence/provenance referenciados por uma revision frozen devem permanecer endereçáveis durante a política de retenção/auditoria aplicável; imutabilidade sem resolvibilidade não satisfaz provenance.

## Usage, custos e ExecutionPlan

Cada ProcessingActivity pode ter `UsageRecord`. Operações caras devem poder gerar antes da execução um `ExecutionPlan` com:

- planned activities;
- reuse candidates;
- invalidated artifacts;
- estimated usage/cost;
- expensive calls/resources esperados.

Depois da execução, usage/cost real pode ser comparado à estimativa.

Dry-run é suportado conceitualmente: plano não é lineage executado.

## Reproducibility class

Processors podem ser determinísticos, seeded, non-deterministic ou externally-variable. Não se promete reproducibilidade que o provider/modelo não consegue garantir. Prompt e configuração que alteram o resultado fazem parte do fingerprint; logging/telemetria operacional não.

## Failure/retry policy

Falhas podem ser classificadas operacionalmente como transitórias, input permanente, processor bug, policy block, resource limit ou external dependency. Retry cego universal não é permitido.

## Reprocessamento parcial

Region-level repair é permitido, mas deve incluir um reconciliation radius/dependency closure suficiente para restaurar consistência. Mudança material em Reconstruction gera nova CanonicalRevision e novo ValidationReport. Mudança apenas de ValidationPolicy pode produzir **ValidationReport suplementar externo** para a mesma revision sem rematerialização; se a revision já estiver frozen, seu `validation_report_ref` autorizador original não é substituído.

## Human review queue

Issues e validation checks alimentam priorização por risco; revisão integral de todo livro não é default.

## Invariantes M2.5 — P01–P16

**P01.** Outputs relevantes de processamento são imutáveis e versionados.  
**P02.** Toda ProcessingActivity declara processor e configuração semanticamente relevante; `Derivation` é a autoridade normativa de `input_refs/output_refs` e referencia a activity que executou a transformação.  
**P03.** Reprocessamento cria novos artefatos/atividades; não sobrescreve outputs anteriores.  
**P04.** Cache reuse só é permitido com inputs/configuração semanticamente compatíveis.  
**P05.** Cache reuse não cria provenance falsa.  
**P06.** Invalidação propaga-se por dependências reais downstream, não por matriz global hard-coded.  
**P07.** `stale` é estado contextual relativo a uma target lineage, nunca mutação do artefato; o artefato histórico permanece auditável.  
**P08.** Confidence qualifica decisões específicas e não é agregada ingenuamente em score documental único.  
**P09.** Scores de tipos/produtores distintos não são presumidos comparáveis sem calibração.  
**P10.** Review risk é conceito distinto de confidence.  
**P11.** Correção humana é ProcessingActivity/Derivation auditável e não mutação silenciosa.  
**P12.** Provenance e observability são modelos relacionados, porém distintos.  
**P13.** Uso e custo são atribuíveis a ProcessingActivities.  
**P14.** Operações caras devem poder gerar ExecutionPlan/estimativa quando dados necessários existirem.  
**P15.** Retry transitório não mascara mudança de input/model/configuração como mesma execução.  
**P16.** Reprocessamento parcial inclui dependências necessárias para restaurar consistência.

---

# M2.6 — Compatibility Corpus & Exit Criteria — FROZEN

## Objetivo

O M2 só termina quando o pipeline produz CBM v0.1 válido/reproduzível sobre uma suíte conhecida e passa por novos holdouts cegos não usados durante desenvolvimento.

## Papéis do corpus

Quatro grupos têm funções distintas:

```text
A — Regression Core
B — Compatibility Shortlist
C — Discovery Corpus
D — M2 Blind Holdouts
```

### Regression Core

F1/F2/W1/W2, C1/C2/C3 e F-RND/W-RND tornam-se golden reconstruction/materialization cases. Eles testam assertions estruturais/semânticas, não snapshots serializados completos.

Assertions podem cobrir Evidence, Reconstruction, CBM, Provenance e Validation.

### Compatibility Shortlist

Alvo: 8–12 documentos estruturalmente adversariais. Shortlist inicial continua documentada em `planning/COMPATIBILITY-CORPUS.md`. A presença na shortlist **não cria implicitamente uma capability claim**: cada `CorpusCase` é avaliado segundo seu `support_tier`. Tier 1 é exit-gated; Tier 1.5 tem obrigações de preservation; Experimental/Deferred são discovery/out-of-scope conforme declarado.

### Discovery Corpus

Alvo aproximado: 30 materiais. Serve como sensor de fenômenos desconhecidos; todo problema observado é classificado/registrado, mas nem todo achado fora do support tier bloqueia M2.

### M2 Blind Holdouts

Holdouts antigos do M1 agora são regressão e **não** podem servir de teste cego do M2. Novos holdouts devem ser selecionados/congelados antes da implementação e permanecer fechados até o candidate de implementação ser congelado.

Recomendação mínima: quatro holdouts cobrindo PDF literário/prosa, PDF técnico, PDF matemático/estruturado e Markdown narrativa.

## CorpusCase

Cada caso deve registrar conceitualmente source, scope, format, language, structural features, expected assertions, allowed extensions, support tier e corpus role.

## Resultado por caso

- `PASS`;
- `PASS_WITH_EXTENSION`;
- `PROCESSING_FAILURE`;
- `MODEL_GAP`;
- `MODEL_FAILURE`.

`PROCESSING_FAILURE` nunca reabre automaticamente o CBM.

## Support tiers

- **Tier 1:** supported / exit-gated;
- **Tier 1.5:** best-effort, mas evidence preservation obrigatória;
- **Experimental:** discovery only;
- **Deferred:** fora do escopo corrente.

M2 mantém PDF textual + Markdown em Tier 1 e PDF mixed em Tier 1.5.

## Cross-format equivalence

Quando a mesma manifestação/edição existir em containers diferentes, `EquivalenceCase` pode verificar equivalência documental/semântica aproximada sem exigir Source Evidence ou IDs iguais.

## M2 blind protocol

Há dois gates de congelamento. Antes de implementação/tuning relevante, congelam-se os manifests de assertions do Regression Core e a seleção dos holdouts (source/scope/hash/método de seleção) sem revelar o conteúdo. Antes do reveal, congela-se um **M2 implementation candidate manifest** contendo no mínimo:

- build/commit/package identity;
- baseline CBM/schema;
- semantic configuration;
- processor/model/provider identities e reproducibility class;
- ValidationPolicy;
- versões das assertions;
- support tiers/capability claims avaliadas.

Então:

```text
freeze assertions + holdout selection
→ implement/tune
→ freeze implementation candidate + claims/config
→ reveal H1..Hn
→ execute pipeline
→ evaluate without tuning
```

Falha não pode ser convertida em sucesso por tuning sobre o mesmo holdout nem por downgrade retroativo de capability/support tier. Após ajuste ou mudança de claim, o caso revelado vira regressão e um **novo candidate + novo holdout** é necessário para avaliar a nova claim.

## Métricas/gates úteis

Seis famílias principais:

1. preservation / evidence accountability;
2. structural correctness;
3. traceability;
4. validation;
5. reproducibility/idempotence;
6. selective reprocessing efficiency.

Métrica agregada simples de “accuracy” não substitui severity/assertions estruturais.

Evidence accountability classifica evidência significativa em `canonicalized`, `intentionally_noncanonical`, `unresolved` ou `suspected_loss`. **Known silent loss de conteúdo significativo bloqueia M2.**

## Testes obrigatórios de reprocessing

O fechamento do M2 deve demonstrar pelo menos:

- ValidationPolicy muda → apenas validation reruns;
- reconstruction localizada muda → Evidence é reutilizada e somente dependências afetadas são reprocessadas;
- Evidence muda em região/página → downstream afetado é invalidado e áreas independentes são reutilizadas.

## Exit gates

### Regression Core

Todos os casos conhecidos precisam satisfazer suas assertions versionadas.

### Compatibility Shortlist

Para capabilities Tier 1: nenhum `MODEL_FAILURE`/`MODEL_GAP` não resolvido e nenhuma perda significativa silenciosa inexplicada. `PROCESSING_FAILURE` precisa ser corrigido ou a capability claim explicitamente reduzida.

### Discovery Corpus

Não precisa estar todo verde; todo achado precisa estar classificado e registrado, e só bloqueia quando contradiz capability/support tier declarado ou revela falha fundamental.

### Provenance

Objetos representativos (paragraph, verse, terminal command, table cell, footnote, formula) devem demonstrar lineage fim a fim CBM → materialization → reconstruction → evidence → source.

### Validation

Saídas principais terminam em `CanonicalRevision frozen` com ValidationReport e ValidationPolicy conhecidos/versionados.

### Reproducibility/reprocessing

Idempotência/reuso e selective reprocessing são demonstrados, não apenas presumidos.

### Blind holdouts

Candidate congelado precisa passar sem `MODEL_GAP`, `MODEL_FAILURE`, perda significativa silenciosa ou `PROCESSING_FAILURE` incompatível com a capability claim.

## Schema Evolution durante M2

`MODEL_GAP` não modifica CBM v0.1 silenciosamente. Abre observação no Schema Evolution Log e, se justificado, novo candidate/versionamento + regression antes de promoção. Como `M2 Design v0.1` tem `CBM v0.1` como baseline, qualquer schema promovido diferente exige ADR e rebaseline explícito/nova versão do design antes de alterar a claim do M2.

## Definition of Done do M2

M2 está concluído quando, para o escopo Tier 1, VoxCodex consegue ingerir uma fonte, preservar evidência suficiente, reconstruir estrutura lógica, materializar CBM v0.1 rastreável, validar/congelar a revision, reproduzir/reprocessar seletivamente, classificar falhas/incertezas e passar por regressão + holdouts cegos.

## Invariantes M2.6 — C01–C16

**C01.** Regression cases possuem assertions explícitas e versionadas.  
**C02.** Golden tests validam semântica/estrutura, não serialização acidental.  
**C03.** Compatibility, discovery e holdout possuem funções distintas.  
**C04.** PROCESSING_FAILURE é distinto de MODEL_GAP e MODEL_FAILURE.  
**C05.** Problema de pipeline não é corrigido modificando o CBM sem evidência de inadequação do modelo.  
**C06.** Discovery findings são registrados mesmo quando não bloqueiam o milestone.  
**C07.** Capability claims são explícitas por support tier.  
**C08.** Perda silenciosa conhecida de conteúdo significativo bloqueia M2.  
**C09.** Evidence não canônica é contabilizada como intentionally excluded/noncanonical, unresolved ou suspected loss.  
**C10.** Reproducibility/idempotence é testada, não presumida.  
**C11.** Selective reprocessing é demonstrado com dependências reais.  
**C12.** Holdouts do M2 permanecem cegos até o candidate de implementação ser congelado.  
**C13.** Falha em holdout não pode ser transformada em sucesso por tuning sobre o mesmo holdout.  
**C14.** Schema evolution descoberta pelo corpus usa versionamento explícito e não modifica CBM v0.1 retroativamente.  
**C15.** Assertions do Regression Core e seleção dos blind holdouts são congeladas antes de implementação/tuning relevante; conteúdo de holdout permanece não revelado.  
**C16.** Antes do reveal, o implementation candidate congela identidade, baseline, configuração semântica, processors/models/providers, ValidationPolicy, versões das assertions e capability/support-tier claims; downgrade posterior não converte FAIL retroativamente em PASS.

---

# Compatibility Corpus como requisito transversal

O M2 deve diferenciar falha do modelo de falha do pipeline:

```text
PASS
PASS_WITH_EXTENSION
PROCESSING_FAILURE
MODEL_GAP
MODEL_FAILURE
```

- shortlist de regressão: ~8–12 materiais;
- corpus de descoberta: ~30 materiais;
- seleção por fenômenos estruturais e formatos;
- mesma obra em múltiplos containers pode testar equivalência canônica;
- mudança normativa do CBM exige `Schema Evolution Log` e novo candidate/versionamento explícito.

Documento: `planning/COMPATIBILITY-CORPUS.md`.

---
