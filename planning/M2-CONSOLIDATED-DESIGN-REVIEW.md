# M2 — Consolidated Design Review (M2.1–M2.6)

## Resultado

**BLOCKED FOR FREEZE — arquitetura coerente, com 5 correções normativas obrigatórias antes do `M2 Design v0.1` freeze.**

Data: 2026-09-11

Escopo revisado:

- M2.1 — Boundary & Success Contract;
- M2.2 — Source Artifact & Evidence Model;
- M2.3 — Reconstruction Pipeline;
- M2.4 — CBM Materialization & Validation;
- M2.5 — Reprocessing, Confidence & Provenance;
- M2.6 — Compatibility Corpus & Exit Criteria;
- compatibilidade com `architecture/CBM-V0.1.md`;
- ADRs, requisitos, riscos, status e manifests relacionados.

O review não altera o CBM v0.1 nem aprova automaticamente as correções abaixo. M2.1–M2.3 permanecem historicamente congelados; qualquer emenda necessária a eles deve ser registrada por ADR corretivo antes do freeze consolidado.

---

# Blockers normativos

## B1 — Ownership das arestas de provenance: ProcessingActivity vs Derivation

### Problema

O `CBM v0.1` define:

- `ProcessingActivity` = metadata da execução (processor/model/prompt/config/timestamps/status/usage);
- `Derivation` = `activity_ref + input_refs + output_refs + derivation_kind + confidence_ref`.

Porém M2.3/M2.5 afirmam em pontos normativos que `ProcessingActivity` registra/declara diretamente `inputs/outputs`.

Isso conflita com o contrato congelado do CBM e, se implementado literalmente, criaria uma segunda autoridade de lineage.

Afeta pelo menos:

- `planning/M2-DOCUMENT-RECONSTRUCTION.md`, DAG/feedback de M2.3;
- seção `ProcessingActivity operacional` de M2.5;
- P02;
- requisitos derivados de M2.5;
- interpretação de AD-123/AD-124.

### Resolução recomendada

- `ProcessingActivity` continua sendo a unidade de execução.
- **Derivation é a autoridade das arestas causais `input_refs/output_refs`.**
- Dependency DAG e invalidação são derivados das `Derivation`s, agrupadas por activity.
- `ActivityFingerprint` usa os inputs planejados/efetivos (refs/digests) + metadata semântica da activity, sem adicionar `input_refs/output_refs` ao schema de `ProcessingActivity`.
- M2.3 deve receber emenda corretiva explícita, pois está frozen.

### Severidade

**BLOCKER.**

---

## B2 — Dupla autoridade na hierarquia de ReconstructionUnit

### Problema

`ReconstructionUnit` possui simultaneamente:

```text
parent_ref
child_refs[]
order_key
```

O design não declara qual lado é normativo. `parent_ref` e `child_refs` podem divergir, criando snapshots internamente inconsistentes e digests ambíguos.

É a mesma classe de problema que o freeze do CBM já evitou ao declarar autoridades únicas para ownership/membership.

### Resolução recomendada

- `parent_ref + order_key` tornam-se a autoridade normativa da hierarquia lógica.
- `child_refs`, se materializado, é apenas índice/projeção derivável e deve ser validado contra a autoridade normativa.
- Structured membership/topology especializada continua fora dessa relação de ownership quando necessário.
- Registrar ADR corretivo e novo invariante de Reconstruction (recomendado: R13) sem renumerar R01–R12.

### Severidade

**BLOCKER.**

---

## B3 — Bootstrap de CanonicalDocument / Work / Edition ausente

### Problema

M2 começa conceitualmente em `SourceArtifact` e M2.4 termina em `CanonicalRevision`, mas uma `CanonicalRevision` válida exige `canonical_document_ref`, enquanto `CanonicalDocument` exige `work_ref`, `edition_ref`, `source_artifact_refs` e ao menos uma revision.

O design atual não especifica:

- como o target `CanonicalDocument` é conhecido ou criado;
- de onde vêm `work_ref` e `edition_ref`;
- como ocorre a criação consistente de `CanonicalDocument + R1` na primeira materialização;
- como uma rematerialização escolhe o documento/revision-base correto.

Isso não exige entity resolution bibliográfica complexa, mas é precondição para produzir CBM v0.1 válido.

### Resolução recomendada

Introduzir um **contexto operacional de target/intake**, não uma nova primitiva do CBM, contendo no mínimo:

- target `CanonicalDocument` existente **ou** dados/referências necessários para provisioná-lo;
- `work_ref`;
- `edition_ref`;
- `source_artifact_ref(s)`;
- `base_revision_ref` opcional para rematerialização.

Para a primeira revision, `CanonicalDocument` e `R1` devem ser materializados consistentemente/atomicamente do ponto de vista lógico. M2 não deve inventar Work/Edition: refs vêm de intake metadata ou assertion humana auditável.

### Severidade

**BLOCKER.**

---

## B4 — Revalidation de revision frozen está ambígua

### Problema

M2.5 afirma que mudança apenas de `ValidationPolicy` pode revalidar a mesma revision sem rematerialização. Isso é útil, mas o CBM v0.1 torna uma revision frozen semanticamente imutável e inclui `validation_report_ref` no objeto.

Sem regra explícita, uma implementação poderia substituir `validation_report_ref` de uma revision frozen, violando S42/S54/S55.

M2.4 também usa termos genéricos (`provenance`, `source mapping/accountability`) onde o CBM exige refs concretas para freeze.

### Resolução recomendada

- Uma revision frozen pode receber **ValidationReports suplementares externos**, pois cada report referencia `revision_ref`.
- O `validation_report_ref` já associado à revision frozen é o **freeze-authorizing report** e não é substituído.
- Se uma nova policy precisar tornar-se a base autoritativa de um novo freeze, criar nova revision/fluxo explícito; nunca mutar a revision frozen.
- Alinhar o freeze gate aos nomes exatos do CBM v0.1:
  - `source_mapping_manifest_ref` obrigatório;
  - `provenance_manifest_ref` obrigatório;
  - `validation_report_ref` obrigatório;
  - `content_digest` obrigatório;
  - `fidelity_manifest_ref` continua opcional no v0.1.
- “ValidationPolicy versionada” significa identidade/configuração imutável e referenciável; não implica adicionar silenciosamente um campo `version` ao schema congelado.

### Severidade

**BLOCKER.**

---

## B5 — Blind-holdout protocol ainda não congela suficientemente a claim avaliada

### Problema

M2.6 congela holdouts e candidate antes do reveal, mas não especifica explicitamente que a **capability claim/support tier e as assertions** também estão congeladas.

Sem isso, após uma falha seria possível reduzir Tier/claim e transformar retroativamente o resultado em “compatível com a claim”, enfraquecendo o valor do holdout.

Também falta definir o conteúdo mínimo do candidate manifest usado no blind test.

### Resolução recomendada

Antes de implementação/tuning relevante:

1. congelar manifests de assertions do Regression Core;
2. congelar seleção dos M2 holdouts (fonte/scope/hash/método de seleção) sem abrir conteúdo.

Antes do reveal dos holdouts:

3. congelar um **M2 implementation candidate manifest** contendo, no mínimo:
   - build/commit/package identity;
   - baseline CBM/schema;
   - semantic configuration;
   - processor/model/provider identities e reproducibility class;
   - ValidationPolicy;
   - versões das assertions;
   - support tiers/capability claims avaliadas.

Após reveal, downgrade de capability/support tier não pode converter retroativamente FAIL em PASS; mudança de claim exige novo candidate e novo holdout para a nova claim.

Recomendação: adicionar invariantes C15–C16 para esses dois gates.

### Severidade

**BLOCKER.**

---

# Clarificações obrigatórias antes do freeze

Estas não exigem reabrir o core do CBM, mas devem ser incorporadas ao design consolidado para eliminar ambiguidades de implementação.

## Q1 — `stale` é estado contextual, não mutação do artefato

Artefatos permanecem imutáveis. “Stale” deve ser calculado/registrado em índice/planner context relativo a uma target lineage, e não como mutação do payload/digest do artefato histórico.

## Q2 — Artefatos operacionais M2 não são novas primitivas CBM

Deixar explícito que conceitos como `SourceProfile`, `EvidenceSnapshot/Unit`, `ReconstructionSnapshot/Unit`, `OpenStructuralState`, `ReconstructionIssue`, `CanonicalDraft`, `MaterializationRun/Issue`, `ActivityFingerprint`, `ExecutionPlan`, `ReviewRisk`, `ReviewDecision` e `DerivedArtifact` são contratos operacionais do M2, não extensões silenciosas do núcleo CBM.

`DerivedArtifact` deve ser entendido como termo operacional guarda-chuva até seu schema físico ser definido.

## Q3 — `ReconstructionSnapshot.validation_ref` não aponta para CBM ValidationReport

`ValidationReport` do CBM exige `revision_ref`. Portanto o `validation_ref` de Reconstruction deve apontar para um report/resultado operacional específico de reconstruction, ou ser removido futuramente. Ele não pode reutilizar semanticamente o `ValidationReport` canônico.

## Q4 — Significância de Evidence precisa ser policy-controlled

“Significant evidence”, accountability e severity não devem depender de threshold global implícito. A regra deve ser versionada e ligada à ValidationPolicy ou configuração por ela referenciada, para tornar `suspected_loss`/blocker reproduzível.

## Q5 — Compatibility Shortlist pode conter múltiplos support tiers

A shortlist inicial inclui materiais/formats que podem permanecer Experimental/Deferred no M2. O gate deve ser avaliado **por `CorpusCase.support_tier`**, não pela mera presença na shortlist. Tier 1 é exit-gated; Tier 1.5 tem preservation obligations; Experimental/Deferred não adquirem claim implícita.

## Q6 — MODEL_GAP não pode rebaselinar M2 silenciosamente

`M2 Design v0.1` tem `CBM v0.1` como baseline. Se um MODEL_GAP in-scope exigir e promover novo schema, o M2 precisa de ADR/rebaseline explícito ou nova versão do design; não se troca `0.1` por `0.2` silenciosamente mantendo o mesmo freeze.

## Q7 — Evidência/provenance referenciada precisa permanecer endereçável

EvidenceSnapshots/units e artifacts de lineage referenciados por uma revision frozen devem permanecer resolvíveis pelo período de retenção/auditoria definido. Imutabilidade sem addressability não preserva provenance.

## Q8 — Governança do freeze documental

`M2-DESIGN-FREEZE-MANIFEST.json` é um snapshot histórico válido do pacote congelado até M2.3; o working document `planning/M2-DOCUMENT-RECONSTRUCTION.md` evoluiu depois, portanto seu hash corrente naturalmente não coincide com o snapshot antigo.

No freeze completo, recomenda-se criar um arquivo normativo imutável dedicado, por exemplo:

```text
architecture/M2-DESIGN-V0.1.md
```

mais um novo manifest de freeze, mantendo o planning document como histórico de elaboração.

---

# Verificações que passaram

1. `architecture/CBM-V0.1.md` continua byte-a-byte inalterado com SHA-256 `788c2a8e6229d2141346f46cc80928d8df3c4ed6a2f323770865dab94ab12dd3`.
2. Os 8 arquivos de `data/` permanecem iguais aos hashes registrados no snapshot M2.4–M2.6.
3. ADRs estão contínuos de AD-001 a AD-143, sem gaps/duplicações.
4. Invariantes registrados estão completos: E01–E10, R01–R12, M01–M14, P01–P16, C01–C14.
5. `M2.4-M2.6-REGISTRATION-MANIFEST.json` corresponde integralmente aos hashes atuais dos arquivos que declara.
6. Todos os JSONs de estado/manifest carregam como JSON válido.
7. M2.4 mantém corretamente a fronteira Reconstruction→CBM e não introduz interpretação semântica global.
8. M2.5 preserva corretamente os princípios de cache sem provenance falsa, confidence localizada, cost attribution e dependency-driven invalidation — após corrigir B1/B4.
9. M2.6 separa corretamente regression/compatibility/discovery/holdout e PROCESSING_FAILURE/MODEL_GAP/MODEL_FAILURE — após endurecer B5.
10. Stack, storage, serialization, workflow engine e providers continuam deliberadamente não selecionados.

---

# Veredito

O desenho M2.1–M2.6 é **arquiteturalmente sólido e compatível com a direção do CBM**, mas o freeze completo agora seria prematuro porque B1–B5 permitem implementações que quebrariam contratos já congelados ou reduziriam a força dos gates experimentais.

Resultado do review:

```text
M2 consolidated design review: BLOCKED_FOR_FREEZE
CBM v0.1 changes required: 0
M2 corrective decisions required: 5
M2 clarifications required: 8
stack decisions required now: 0
```

## Próximo gate recomendado

Aprovar as resoluções B1–B5 e as clarificações Q1–Q8, registrá-las por ADR (incluindo emendas explícitas a M2.3 onde necessário), atualizar M2.4–M2.6 e então executar uma verificação final de freeze para produzir `M2 Design v0.1` normativo + manifest.
