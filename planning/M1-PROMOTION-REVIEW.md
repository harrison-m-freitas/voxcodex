# M1 — Promotion Review do CBM v0.1

**Data:** 2026-09-11  
**Candidate avaliado:** `architecture/CBM-V0.1-CANDIDATE.md`  
**Candidate SHA-256 no freeze:** `22392650f6a63531bb7cb034c55c68e612970df13557747787050f84269aed58`  
**Resultado:** `PASS`  
**Decisão:** promover para `CBM v0.1` e encerrar o M1

---

## 1. Objetivo do gate

O promotion review verifica se o candidate congelado possui evidência suficiente para se tornar a baseline normativa `CBM v0.1`, sem reabrir o core após os testes cegos.

Critérios de promoção:

1. candidate permanece idêntico ao freeze durante os holdouts;
2. F1/F2/W1/W2 aprovados;
3. C1/C2/C3 sem `MODEL_GAP` ou `MODEL_FAILURE`;
4. F-RND/W-RND sem alteração de primitivas universais ou invariantes;
5. extensões observadas nos holdouts cabem no mecanismo namespaced já congelado;
6. não existem blockers normativos abertos para a representação canônica v0.1;
7. itens adiados são explicitamente classificados como implementação, downstream ou evolução futura.

---

## 2. Evidência revisada

### Golden slices

| Slice | Resultado |
|---|---|
| F1 — *Fedra* p.6 | aprovado |
| F2 — *Fedra* pp.10–11 | aprovado |
| W1 — Weidman p.112 | aprovado |
| W2 — Weidman p.96 | aprovado |

Produziram M1-I01–M1-I18 e fundamentaram o core inicial.

### Cross-genre

| Slice | Resultado | Core change |
|---|---|---:|
| C1 — Leandro Lima | `PASS_WITH_EXTENSION` | 0 |
| C2 — *Eternally Regressing Knight* | `PASS_WITH_EXTENSION` | 0 |
| C3 — Stewart | `PASS_WITH_EXTENSION` | 0 |

Resultado agregado: `MODEL_GAP=0`, `MODEL_FAILURE=0`.

### Blind holdouts

| Holdout | Resultado | Core/invariant change |
|---|---|---:|
| F-RND — *Fedra* p.33 | `PASS` | 0 |
| W-RND — Weidman p.558 | `PASS_WITH_EXTENSION` | 0 |

W-RND observou duas extensões compatíveis com roles namespaced já permitidos:

- `technical.terminal_input`;
- `editorial.omission_marker`.

Nenhuma página adjacente foi consultada no teste cego.

---

## 3. Integridade do candidate

O candidate congelado não foi editado para acomodar os holdouts.

```text
freeze SHA-256:
22392650f6a63531bb7cb034c55c68e612970df13557747787050f84269aed58

post-holdout SHA-256:
22392650f6a63531bb7cb034c55c68e612970df13557747787050f84269aed58
```

O promotion review preserva `architecture/CBM-V0.1-CANDIDATE.md` como evidência histórica. A promoção cria `architecture/CBM-V0.1.md`; não reescreve o candidate.

---

## 4. Review normativo

### Core universal

Nenhuma nova primitiva universal é necessária após os holdouts. Permanecem como núcleo:

- `CanonicalDocument` / `CanonicalRevision`;
- `DocumentNode` / `ContentFragment`;
- `SourceArtifact` / `SourceAnchor`;
- `FidelityConstraint`;
- `Entity`;
- `Annotation` / `Relation`;
- `ProcessingActivity` / `Derivation`;
- registries/manifests/validation;
- `StructuredPayload` apenas quando árvore + fragments não preservam a topologia.

### Invariantes

S01–S56 permanecem inalterados. Os holdouts não demonstraram necessidade de S57 nem de revisão de qualquer invariante congelado.

### Extensões de W-RND

`technical.terminal_input` e `editorial.omission_marker` são promovidos ao vocabulário comprovado de extensões do `v0.1` porque:

- são namespaced;
- não mudam `node_class`/`fragment_class`;
- não alteram cardinalidade do core;
- não alteram ownership;
- não alteram SourceAnchor, fidelity, provenance ou lifecycle;
- são compatíveis com S05, S31 e S40.

### Questões adiadas

Continuam não bloqueantes:

- representação matemática concreta (MathML/AST/etc.);
- registry físico/versionamento de Role Profiles;
- serialização física do CBM;
- canonical serialization/digest algorithm;
- confidence calibration;
- interpretação semântica de figures;
- escolhas de banco/ORM/API/workflow.

Essas questões não impedem o contrato conceitual v0.1 e devem ser tratadas em milestones posteriores quando houver decisão de implementação ou nova evidência.

---

## 5. Decisão de promoção

**PASS.** O `CBM v0.1 candidate` demonstrou conformidade em:

```text
4 golden slices
3 corpora cross-genre
2 blind holdouts
```

sem `MODEL_GAP`, `MODEL_FAILURE`, alteração de primitiva universal ou alteração de invariante após o freeze.

A baseline normativa passa a ser:

```text
architecture/CBM-V0.1.md
schema_version = 0.1
status = PROMOTED
```

O candidate congelado, seu freeze manifest e o holdout manifest permanecem como trilha de auditoria.

---

## 6. Encerramento do M1

O M1 — **Canonical Representation** é considerado concluído após esta promoção.

Entregáveis do milestone:

- 18 invariantes arquiteturais M1-I01–M1-I18;
- 56 invariantes de schema S01–S56;
- `CBM v0.1` normativo;
- corpus/golden/cross-genre/holdout evidence;
- freeze review e manifests auditáveis;
- risk/ADR/context atualizados.

O próximo passo é definir formalmente o milestone seguinte usando `CBM v0.1` como baseline. O core não deve ser reaberto sem nova evidência empírica e versionamento explícito.
