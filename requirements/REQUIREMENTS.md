# Requisitos Consolidados

## Confirmados

### Integridade

- fonte original preservada e imutável;
- nenhuma transformação destrutiva;
- provenance em toda derivação relevante;
- conteúdo do sistema explicitamente distinguível do conteúdo da obra;
- cobertura rastreável fonte → CBM → roteiro → áudio.

### Entrada

A arquitetura deve poder evoluir para suportar:

- EPUB;
- PDF textual;
- PDF escaneado;
- Markdown;
- TXT;
- HTML;
- DOCX;
- imagens de páginas.

O PoC não precisa implementar todos.

### Document Intelligence

Capacidade futura prevista para:

- OCR;
- layout;
- reading order;
- múltiplas colunas;
- notas;
- cabeçalhos/rodapés;
- hifenização;
- fórmulas;
- tabelas;
- figuras;
- teatro;
- poesia.

### Compreensão

- idioma;
- estrutura;
- gênero;
- estilo;
- personagens;
- narrador;
- speakers;
- citações;
- conceitos;
- referências internas;
- contexto entre capítulos.

### Áudio

- múltiplas vozes;
- Voice Registry;
- pronúncia;
- prosódia;
- pausas;
- emoção contextual sem caricatura;
- TTS desacoplado da camada editorial.

### Workflows

- jobs longos;
- checkpoints;
- retry;
- cancelamento;
- reprocessamento;
- idempotência;
- paralelismo;
- dependências.

### Qualidade

Detectar ou validar:

- texto perdido;
- duplicações;
- OCR incorreto;
- mudança de significado;
- speaker incorreto;
- pronúncia;
- cortes;
- inconsistência de volume;
- conteúdo inventado;
- segmentação incorreta.

### Custos

Antes:
- estimativa detalhada;
- intervalo provável;
- comparação de planos;
- estratégia de processamento explícita.

Depois:
- custo real;
- comparação estimado vs. real;
- calibração progressiva do estimador.

## Restrições canônicas confirmadas pelo M1

- estrutura lógica é independente de paginação física;
- Source Evidence deve preservar texto superficial e, quando relevante, geometria/tipografia/layout;
- índice físico da página e fólio/rótulo editorial são distintos;
- repetição física de running headers/fólios não gera duplicação lógica;
- evidência explícita e inferência semântica permanecem separadas;
- especializações de gênero/formato não são requisitos universais do núcleo;
- `textual_exact` é o padrão do modo Fiel para texto autoral/editorial narrável;
- fidelidade pode ser refinada localmente para `literal_exact`/`symbolic_exact` em spans/subunidades;
- tabelas/dados estruturados preservam topologia;
- representação superficial de valores permanece recuperável após parsing/normalização;
- conteúdo literal pode possuir estrutura interna sem ser achatado;
- conteúdo principal e callouts/anotações editoriais visualmente intercalados permanecem distinguíveis;
- decisões concretas de verbalização/narração permanecem fora do CBM.

## Contrato canônico aprovado no M1

O **`CBM v0.1` promovido** (`architecture/CBM-V0.1.md`) deve suportar:

- `CanonicalDocument` separado de `CanonicalRevision`;
- árvore lógica por `DocumentNode`;
- conteúdo granular por `ContentFragment`;
- `node_class` controlado e `role` namespaced/extensível;
- `SpeakerCue` sibling de `Speech`;
- Source Evidence fora do CBM, ligada por `SourceAnchor`;
- múltiplos anchors por objeto;
- fidelity por constraints ortogonais;
- `Entity` fora da árvore;
- `EntityMention` como Annotation;
- `Annotation` e `Relation` tipadas, direcionais e epistemicamente qualificadas;
- status `explicit`, `derived`, `inferred`, `human_asserted`;
- `ProcessingActivity` + `Derivation` para provenance;
- `RoleProfile` para extensão/validação;
- `TablePayload` para topologia tabular;
- `FormulaPayload` com separação entre representações da fonte e reconstruções com provenance;
- figuras multipainel endereçáveis por `structured.figure_panel`;
- conteúdo misto com ordem lógica única entre fragments e child nodes do mesmo parent;
- revisions `frozen` imutáveis;
- ValidationReport obrigatório para freeze;
- referência explícita da CanonicalRevision por artefatos downstream;
- 56 invariantes de schema S01–S56.

O CBM não deve incorporar decisões finais de narração, prosódia, vozes ou TTS.

### Evidência cross-genre

C1 (teologia/prosa expositiva), C2 (webnovel/narrativa) e C3 (cálculo/textbook) foram concluídos com `PASS_WITH_EXTENSION`. Nenhum exigiu nova primitiva universal. Em matemática, o text layer de PDF não pode ser assumido como autoritativo quando divergir da evidência visual; reconstruções simbólicas exigem provenance.

### Evidência blind holdout e promoção

F-RND resultou em `PASS`; W-RND em `PASS_WITH_EXTENSION`, observando `technical.terminal_input` e `editorial.omission_marker`. Nenhum holdout exigiu mudança de primitiva universal, invariante ou contrato congelado. O promotion review foi `PASS` e o M1 foi encerrado com 18 invariantes arquiteturais e S01–S56.

## Hipóteses atuais

- qualidade é prioritária sobre baixa latência;
- processamento pode ser assíncrono;
- artefatos intermediários podem ser preservados;
- processamento por capítulo/bloco será útil;
- reprocessamento seletivo será frequente;
- haverá poucos usuários simultâneos no início;
- revisão humana poderá ser usada em casos de baixa confiança.

## Fora do PoC

- suporte universal a todos os formatos;
- matemática científica avançada;
- interpretação universal de diagramas;
- audiobook multilíngue completo;
- tradução sincronizada;
- marketplace de vozes;
- app mobile;
- fine-tuning próprio;
- treinamento de OCR/TTS;
- microserviços extensivos;
- Kubernetes como requisito;
- event sourcing completo.


## Requisitos confirmados para M2 — Document Reconstruction & CBM Materialization

M2.1 aprovou os seguintes requisitos de fronteira:

- entrada conceitual: `SourceArtifact`;
- saída: `CanonicalRevision` conforme CBM v0.1, validada e apta a freeze;
- preservar Source Evidence rica antes da reconstrução lógica;
- permitir inspeção separada de Evidence, Reconstruction e Canonical materialization;
- manter provenance das transformações relevantes;
- distinguir reading order físico de ordem lógica;
- suportar continuidade entre páginas/chunks;
- evitar duplicação lógica de running headers/fólios;
- preservar topologias estruturadas (ex.: tabelas) e evidência visual matemática quando parsing falhar;
- Tier 1 inicial: PDF textual e Markdown;
- PDF mixed/parcialmente visual: Tier 1.5;
- OCR universal, EPUB, HTML e DOCX não são requisito de fechamento no primeiro recorte do M2;
- Semantic Enrichment interpretativo, Narration, Performance e Audio ficam fora da fronteira;
- estratégia de processamento: determinístico → especializado → LLM → revisão humana conforme necessidade;
- Compatibility Corpus obrigatório como mecanismo de regressão/descoberta;
- distinguir `PROCESSING_FAILURE` de `MODEL_GAP` e `MODEL_FAILURE`;
- novo caso não altera automaticamente CBM v0.1; mudança normativa exige Schema Evolution Log e versionamento explícito.

### Requisitos congelados em M2.2 — Source Artifact & Evidence Model

- `SourceArtifact` imutável por bytes/checksum;
- transformações criam artefatos derivados, nunca sobrescrevem a fonte;
- `SourceProfile` apenas para inspeção/roteamento;
- `EvidenceSnapshot` imutável, versionável e coexistente entre extractors;
- `EvidenceUnit` como envelope comum com payload nativo extensível;
- preservar surface, geometry, typography/presentation e assets quando relevantes;
- granularidade adaptativa até glyphs quando necessário;
- Markdown AST/syntax é evidência de sintaxe, não estrutura semântica canônica;
- separar native order, geometric order e logical reading order;
- evidence confidence não equivale a reconstruction confidence;
- `SourceAnchor` aponta do CBM para evidence sem dependência reversa;
- invariantes E01–E10.

### Requisitos congelados em M2.3 — Reconstruction Pipeline

- camada intermediária `ReconstructionSnapshot`/`ReconstructionUnit` entre Evidence e CBM;
- grouping, reading order, block reconstruction, classification, boundary reconciliation, structured reconstruction e assembly como estágios conceituais/DAG;
- `OpenStructuralState` para unidades que atravessam páginas/colunas/chunks/batches/workers;
- `ReconstructionIssue` para incerteza/falha local sem perda de evidência;
- logical reading order sempre derivado, nunca presumido igual ao native order;
- reconstrução de hifenização/continuidade é derivação rastreável;
- structured content preserva topologia antes da linearização;
- formula symbolic reconstruction é opcional se região/evidência visual estiver preservada;
- reference detection e target resolution são passos distintos;
- human review orientado a decisões/regiões de risco;
- gênero não é roteador primário;
- invariantes R01–R13.

### Requisitos aprovados em M2.4 — CBM Materialization & Validation

- `CanonicalDraft` operacional separa construção incompleta de `CanonicalRevision` validada;
- M2.4 não redefine logical reading order nem reinterpreta Evidence;
- mapping Reconstruction→CBM deve ser predominantemente determinístico;
- `SourceAnchor` deve ser gerado sistematicamente para conteúdo source-derived quando aplicável;
- fidelity é aplicada por RoleProfile/policy e effective constraints devem ser validáveis;
- StructuredPayload deriva de StructuredCandidate resolvido, sem reconstrução duplicada em M2.4;
- semântica documental resolvida pode ser materializada; Semantic Enrichment interpretativo permanece downstream;
- validação cobre schema, structure, traceability/fidelity, cross-object integrity e evidence accountability;
- evidence significativa não mapeada deve ser explicitamente classificada;
- freeze exige ValidationPolicy versionada, ausência de blockers, digest, provenance e source mapping/accountability;
- materialização deve ser semanticamente idempotente para inputs/schema/config equivalentes;
- invariantes M01–M14.

### Requisitos aprovados em M2.5 — Reprocessing, Confidence & Provenance

- outputs relevantes imutáveis/versionados e lineage por `ProcessingActivity`;
- `ActivityFingerprint` baseado em inputs/digests, processor/version, config semântica e schema/profile;
- cache reuse preserva provenance original;
- invalidação propagada pelas dependências reais downstream;
- confidence localizada por decisão e não comparável entre produtores sem calibração;
- ReviewRisk distinto de confidence; human review auditável como derivação;
- provenance separado de observability;
- usage/cost atribuível por activity;
- `ExecutionPlan`/dry-run para estimar atividades, reuso, invalidação e custo quando possível;
- config semântica participa do fingerprint; config operacional não;
- reprocessamento parcial inclui dependency closure/reconciliation necessário;
- invariantes P01–P16.

### Requisitos aprovados em M2.6 — Compatibility Corpus & Exit Criteria

- quatro papéis: Regression Core, Compatibility Shortlist, Discovery Corpus e M2 Blind Holdouts;
- golden tests baseados em assertions estruturais/semânticas, não snapshots serializados completos;
- support tiers explícitos para capability claims;
- M1 holdouts viram regressão; M2 exige novos blind holdouts congelados antes da implementação;
- known silent loss de conteúdo significativo bloqueia M2;
- evidence accountability distingue canonicalized, intentionally_noncanonical, unresolved e suspected_loss;
- idempotência e selective reprocessing devem ser demonstrados;
- Compatibility Shortlist Tier 1 não pode encerrar com MODEL_GAP/MODEL_FAILURE não resolvido ou perda significativa silenciosa;
- Discovery Corpus pode conter achados abertos se classificados e fora das claims/gates declaradas;
- blind holdout failure não pode ser “corrigida” tuning sobre o mesmo holdout;
- Schema Evolution usa log + novo candidate/versionamento;
- invariantes C01–C16.



### Requisitos corretivos do freeze final do M2 Design v0.1

- `Derivation` é a autoridade de `input_refs/output_refs`; `ProcessingActivity` não duplica essas arestas.
- `ReconstructionUnit.parent_ref + order_key` são normativos; `child_refs` é derivável (`R13`).
- primeira materialização recebe `CanonicalTargetContext` com target existente ou refs auditáveis de Work/Edition/Source; M2 não inventa identidade bibliográfica.
- `validation_report_ref` de frozen revision é freeze-authorizing e imutável; revalidation gera reports suplementares externos.
- freeze usa `source_mapping_manifest_ref`, `provenance_manifest_ref`, `validation_report_ref` e `content_digest` conforme CBM v0.1; `fidelity_manifest_ref` permanece opcional.
- `stale` é contextual, não mutação; evidence/provenance de frozen revisions permanece endereçável conforme retention/audit policy.
- artefatos operacionais M2 não são primitivas do core CBM.
- significance/accountability de Evidence é policy-controlled/versionada.
- Compatibility gates são avaliados por support tier.
- blind protocol congela assertions + holdout selection antes do tuning e candidate identity/config/claims antes do reveal (`C15–C16`).
- MODEL_GAP que exija novo schema requer rebaseline explícito/nova versão do design.
- contrato normativo congelado: `architecture/M2-DESIGN-V0.1.md`.
