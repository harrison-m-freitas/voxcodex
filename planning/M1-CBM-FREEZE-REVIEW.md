# M1 — CBM Freeze Review

**Data:** 2026-09-11  
**Objeto:** `CBM v0.1-alpha candidate` após F1/F2/W1/W2 + C1/C2/C3  
**Resultado:** **PASS — promovido e congelado como `CBM v0.1 candidate`**  
**Schema version congelada:** `0.1-candidate`

## Escopo do review

O review verificou consistência entre o contrato normativo, invariantes, decisões ADR, lifecycle/versionamento, semantic layer, structured payloads, validação cross-genre e gates de holdout. Os holdouts F-RND p.33 e W-RND p.558 **não foram abertos**.

## Blockers encontrados e resolvidos antes do freeze

### FR-01 — `DocumentNode.status` obrigatório sem contrato

O alpha carregava `status` como campo obrigatório, mas sem vocabulário nem semântica demonstrada pelo corpus. Congelar isso criaria um campo normativo indefinido.

**Resolução:** removido do `v0.1 candidate`. Estado de revisão permanece em `CanonicalRevision.lifecycle_state`; necessidades locais futuras devem ser justificadas por corpus.

### FR-02 — dupla autoridade de `schema_version`

`CanonicalDocument` e `CanonicalRevision` continham `schema_version`, enquanto o próprio modelo admite revisions do mesmo documento em schemas diferentes.

**Resolução:** `schema_version` pertence exclusivamente a `CanonicalRevision`.

### FR-03 — refs semânticas locais contradiziam reuso imutável

`DocumentNode`, `ContentFragment`, `Entity` e `TableCell` carregavam refs locais para annotations/relations. Isso contradizia a decisão de reutilizar objetos imutáveis quando apenas a Semantic Layer muda.

**Resolução:** `SemanticRegistry` passa a ser a autoridade de membership. Reverse indexes são projeções físicas opcionais e deriváveis.

### FR-04 — ownership de fragment em StructuredPayload

O alpha mantinha em aberto se `TableCell.content_refs` deveria transformar a célula em owner do fragment.

**Resolução:** não. `ContentFragment` possui exatamente um `DocumentNode` owner; componentes de payload referenciam fragments sem ownership. C1–C3 não apresentaram evidência para generalização de owner.

### FR-05 — lifecycle pós-freeze vs imutabilidade

O contrato permite marcar uma revision frozen posteriormente como `superseded` ou `invalid`, o que precisava ser reconciliado com imutabilidade.

**Resolução:** lifecycle posterior é metadata administrativa; payload canônico e `content_digest` permanecem imutáveis.

### FR-06 — policy de validação não estava registrada no report

O alpha exigia compatibilidade com `ValidationPolicy`, mas o `ValidationReport` não registrava qual policy havia sido aplicada.

**Resolução:** adicionado `validation_policy_ref`; para uma revision frozen também são explicitamente obrigatórios source mapping, provenance manifest, validation report e content digest.

## Itens revisados e considerados não bloqueantes

- AST/serialização matemática concreta permanece adiada; `FormulaPayload` já preserva source vs reconstructed representations com provenance.
- Role Profile registry físico/versionamento pode ser definido na implementação.
- algoritmo de digest/canonical serialization permanece decisão de implementação, não de semântica do core.
- confidence calibration entre processors permanece futura.
- interpretação de figuras permanece derivada; estrutura de figure/panel já é representável.
- tecnologia de serialização, banco, ORM, API e workflow permanecem fora do M1.

## Evidência de generalização

- F1/F2: teatro/verso — aprovado;
- W1/W2: conteúdo técnico, terminal, tabela/callout — aprovado;
- C1: teologia/prosa expositiva — `PASS_WITH_EXTENSION`;
- C2: webnovel/narrativa — `PASS_WITH_EXTENSION`;
- C3: cálculo/textbook matemático — `PASS_WITH_EXTENSION`;
- mudanças de primitivas universais durante C1–C3: **0**;
- `MODEL_GAP`: **0**;
- `MODEL_FAILURE`: **0**.

## Invariantes após review

- M1 arquiteturais: **18**;
- schema: **S01–S56**.

S52–S56 formalizam as resoluções de freeze sobre ownership, SemanticRegistry, lifecycle/digest, validation policy e autoridade de schema version.

## Decisão de freeze

O contrato em `architecture/CBM-V0.1-CANDIDATE.md` está **congelado para blind holdout conformance**. Não pode ser editado para acomodar F-RND/W-RND depois que forem revelados. Qualquer necessidade normativa encontrada nos holdouts deve gerar um novo candidate/versionamento explícito.

## Próximo gate

Agora é permitido abrir:

- F-RND — *Fedra*, PDF p.33;
- W-RND — Weidman, PDF p.558.

O resultado deve ser classificado como `PASS`, `PASS_WITH_EXTENSION`, `MODEL_GAP` ou `MODEL_FAILURE`.
