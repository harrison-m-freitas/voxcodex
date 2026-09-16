# Contexto Canônico do Projeto

## Visão

A plataforma não é um simples conversor de texto para voz.

É um **sistema de publicação auditiva assistida por IA** capaz de:

- preservar a fonte original;
- reconstruir a estrutura documental;
- compreender a obra em nível estrutural e semântico;
- adaptar elementos visuais ou tipográficos para o meio auditivo;
- produzir roteiro narrável auditável;
- aplicar vozes, prosódia e pronúncia de modo consistente;
- sintetizar e validar áudio;
- manter proveniência completa;
- estimar custos antes da execução;
- permitir reprocessamento seletivo.

## Representações fundamentais

A obra é tratada em quatro camadas principais:

1. **Source Evidence**
   - arquivos originais;
   - páginas;
   - evidências de extração;
   - nunca sobrescritos.

2. **Canonical Book Model (CBM)**
   - estrutura lógica;
   - conteúdo canônico preservado;
   - normalizações como annotations/derivações, nunca substituição silenciosa;
   - relações semânticas qualificadas;
   - vínculos precisos com a fonte.

3. **Narration Model**
   - representação editorial preparada para áudio;
   - adaptações auditivas;
   - separação explícita entre conteúdo original e conteúdo auxiliar.

4. **Audio Performance / Rendering Model**
   - speaker;
   - voz;
   - pronúncia;
   - ritmo;
   - pausa;
   - intensidade;
   - direção de interpretação;
   - parâmetros de síntese.

## Invariantes arquiteturais

1. A fonte original é imutável.
2. Toda informação derivada conhece sua origem.
3. Conteúdo gerado nunca se apresenta silenciosamente como conteúdo do autor.
4. Transformações relevantes são versionadas e auditáveis.
5. Compreensão documental e geração de áudio são desacopladas.
6. Etapas caras devem ser reutilizáveis quando suas entradas não mudaram.
7. Confiança deve ser armazenada.
8. O sistema deve poder expressar incerteza.
9. Revisão humana deve permanecer possível nos pontos de maior risco.
10. O pipeline deve ser tratado conceitualmente como um DAG, não como sequência rígida.

## Decisões confirmadas

### Corpus do PoC

- **Fedra — Jean Racine**
  - valida teatro, personagens, diálogos, speaker attribution, prosódia e consistência de vozes.

- **Testes de Invasão: Uma introdução prática ao hacking — Georgia Weidman**
  - valida documento técnico, comandos, código, termos em inglês, figuras, tabelas,
    referências e preservação literal de conteúdo técnico.

### Idioma

- Português é **Tier 1** e requisito obrigatório.
- Inglês será aceito quando o suporte puder ser obtido sem grande aumento de complexidade.
- O PoC não exige arquitetura multilíngue completa.
- Tradução automática não faz parte do núcleo inicial.

### Produto-base

O produto-base é **Audiobook Fiel**.

Fiel não significa leitura mecânica.

Significa:

> preservar todo conteúdo semanticamente relevante da edição ingerida,
> permitindo somente adaptações necessárias ao meio auditivo,
> desde que sejam rastreáveis e não introduzam silenciosamente conteúdo autoral novo.

Modos `Enriquecido` e `Estudo` serão derivados do modo Fiel.

## Unidade de fidelidade

A fidelidade é relativa à **edição/fonte ingerida**, não a uma abstração histórica da obra.

Exemplo:

Uma tradução portuguesa de *Fedra* deve ser fiel àquela tradução/edição específica.

## Estado arquitetural

Hipótese de direção:

- monólito modular inicialmente;
- workflow durável;
- workers especializados quando necessário;
- armazenamento de objetos;
- metadata transacional;
- sem microserviços prematuros.

A arquitetura permaneceu agnóstica de stack até o freeze. O plano de implementação do M2 agora propõe uma baseline técnica local e conservadora: Python 3.14, Pydantic, SQLite/SQLAlchemy/Alembic, blob store content-addressed em filesystem, PyMuPDF, markdown-it-py, Typer, pytest/Hypothesis e RFC 8785.

## M1 — Canonical Representation — CONCLUÍDO

Escopo executado:

- F1/F2 — *Fedra*;
- W1/W2 — Weidman;
- C1 — Leandro Lima;
- C2 — *Eternally Regressing Knight*;
- C3 — Stewart;
- F-RND e W-RND — blind holdouts.

Resultados:

- golden slices: aprovados;
- C1/C2/C3: `PASS_WITH_EXTENSION`;
- F-RND: `PASS`;
- W-RND: `PASS_WITH_EXTENSION`;
- `MODEL_GAP=0`;
- `MODEL_FAILURE=0`;
- mudanças em primitivas universais após freeze: 0;
- mudanças em invariantes após freeze: 0.

O M1 produziu **18 invariantes arquiteturais M1-I01–M1-I18** e **56 invariantes de schema S01–S56**. Registro detalhado: `planning/M1-CANONICAL-REPRESENTATION.md`.

## CBM v0.1 — baseline normativa corrente

Contrato corrente:

`architecture/CBM-V0.1.md`

Estado:

- schema version: `0.1`;
- status: **PROMOTED**;
- promotion review: `PASS`;
- promotion date: 2026-09-11;
- M1: **COMPLETE**.

O contrato mantém:

- `CanonicalDocument` separado de `CanonicalRevision`;
- `DocumentNode` + `ContentFragment` como núcleo estrutural;
- `SpeakerCue` sibling de `Speech`;
- Source Evidence externa ligada por `SourceAnchor`;
- fidelity por constraints ortogonais;
- `Entity` fora da árvore;
- `Annotation`/`Relation` epistemicamente qualificadas;
- `SemanticRegistry` como autoridade de membership semântico;
- `ProcessingActivity` + `Derivation` para provenance;
- `TablePayload` e `FormulaPayload` para topologias especializadas;
- mixed-content ordering único;
- revisions frozen semanticamente imutáveis;
- ValidationPolicy/ValidationReport e digests para freeze.

Extensões observadas no blind holdout e promovidas ao vocabulário comprovado:

- `technical.terminal_input`;
- `editorial.omission_marker`.

### Trilha histórica/auditável

- `architecture/CBM-V0.1-ALPHA.md`;
- `architecture/CBM-V0.1-CANDIDATE.md`;
- `planning/M1-CBM-FREEZE-REVIEW.md`;
- `FREEZE-MANIFEST.json`;
- `planning/M1-HOLDOUT-CONFORMANCE.md`;
- `HOLDOUT-CONFORMANCE-MANIFEST.json`;
- `planning/M1-PROMOTION-REVIEW.md`;
- `PROMOTION-MANIFEST.json`.

O candidate congelado permanece imutável; a promoção foi feita em um novo documento normativo, sem reescrita retroativa.

## Itens deliberadamente adiados

Continuam não bloqueantes para o CBM v0.1:

- representação matemática concreta/AST;
- governança física de Role Profiles;
- formato físico/serialização;
- algoritmo de canonical serialization/digest;
- confidence calibration;
- interpretação semântica derivada de figures;
- escolhas de banco/ORM/API/workflow engine.

## M2 — Document Reconstruction & CBM Materialization — DESIGN v0.1 FROZEN

Estado:

- M2.1 — Boundary & Success Contract: **FROZEN**;
- M2.2 — Source Artifact & Evidence Model: **FROZEN**;
- M2.3 — Reconstruction Pipeline: **FROZEN**;
- M2.4 — CBM Materialization & Validation: **FROZEN**;
- M2.5 — Reprocessing, Confidence & Provenance: **FROZEN**;
- M2.6 — Compatibility Corpus & Exit Criteria: **FROZEN**;
- review consolidado: **PASS após B1–B5/Q1–Q8 corrigidos**;
- contrato normativo: `architecture/M2-DESIGN-V0.1.md`;
- stack de arquitetura: não normativa; baseline de implementação M2 selecionada nos planos em `docs/superpowers/plans/`.

Fluxo consolidado:

```text
ExecutionPlan
     │
SourceArtifact
  → SourceProfile
  → EvidenceSnapshot / EvidenceUnit
  → ReconstructionSnapshot / ReconstructionUnit
  → CanonicalDraft
  → CanonicalRevision CBM v0.1
  → ValidationReport / ValidationPolicy
  → frozen revision
```

M2.4 fixa materialização predominantemente determinística, `SourceAnchor`/Fidelity/Provenance sistemáticos, evidence accountability, validation em camadas e freeze controlado por policy versionada. Invariantes: **M01–M14**.

M2.5 fixa `ActivityFingerprint`, cache com provenance correta, dependency-driven invalidation, confidence localizada, ReviewRisk separado, human review auditável, Usage/Cost e ExecutionPlan/dry-run. Invariantes: **P01–P16**. `Derivation` é a autoridade de lineage causal; `stale` é contextual.

M2.6 fixa Regression Core, Compatibility Shortlist, Discovery Corpus e novos M2 Blind Holdouts, support tiers, evidence-accountability categories e exit gates que incluem idempotência/selective reprocessing e blind conformance. Invariantes: **C01–C16**.

Documento: `planning/M2-DOCUMENT-RECONSTRUCTION.md`.

Snapshot de registro não-frozen: `M2.4-M2.6-REGISTRATION-MANIFEST.json`.

## Compatibility Corpus e evolução de schema

`CBM v0.1` permanece baseline estável. Estratégia:

- Regression Core: F1/F2/W1/W2/C1/C2/C3/F-RND/W-RND;
- Compatibility Shortlist: aproximadamente 8–12 materiais;
- Discovery Corpus: aproximadamente 30 materiais;
- M2 Blind Holdouts: casos novos, congelados antes da implementação;
- resultados: `PASS`, `PASS_WITH_EXTENSION`, `PROCESSING_FAILURE`, `MODEL_GAP`, `MODEL_FAILURE`;
- `PROCESSING_FAILURE` não reabre automaticamente o CBM;
- mudanças normativas exigem Schema Evolution Log + novo candidate/versionamento + regressão;
- known significant silent loss bloqueia M2 para capability declarada.

Shortlist inicial: Constituição Federal, *A República*, *Histórias*, *The Souls of Black Folk*, *The Rust Programming Language*, tutorial Python PT-BR, *Dracula* e artigo científico moderno com matemática/figuras/bibliografia.

Documento: `planning/COMPATIBILITY-CORPUS.md`.

## Próxima etapa

Revisar o roadmap e os seis planos em `docs/superpowers/plans/`; depois iniciar o Plan 01. M2 Blind Holdouts v1 permanecem unrevealed até o implementation candidate freeze.

## M2 consolidated design review — 2026-09-11

O review consolidado inicialmente retornou `BLOCKED_FOR_FREEZE`, mas B1–B5/Q1–Q8 foram resolvidos sem mudança no core do CBM v0.1. O freeze review final retornou `PASS`; contrato normativo: `architecture/M2-DESIGN-V0.1.md`. Próximo gate: revisão humana e plano de implementação.


## M2 final design freeze — 2026-09-11

Os cinco blockers e oito clarificações do review consolidado foram resolvidos sem alterar o core do `CBM v0.1`. Foram adicionados `R13` e `C15–C16`; `ProcessingActivity/Derivation`, hierarchy authority, CanonicalTargetContext, supplemental revalidation, blind candidate claims, evidence significance, support-tier gating, staleness/addressability e rebaseline governance foram fechados. Contrato congelado: `architecture/M2-DESIGN-V0.1.md`.

## Compatibility Corpus v1 — concrete acquisition — 2026-09-14

Curadoria concreta fechada em **30 CorpusCases**. Shortlist operacional fechada em **12**: CC-01, CC-03, CC-04, CC-05, CC-09, CC-11, CC-12, CC-13, CC-14, CC-16, CC-18 e CC-23. Em 2026-09-14 todos os 12 estão adquiridos e **30/30** casos totais possuem fonte local. O Compatibility Corpus v1 está **FROZEN**.

Novos arquivos não são incorporados ao `data/` histórico: ficam em `corpus/compatibility/CC-xx/`, com metadata, hashes e acquisition manifest. `data/` permanece reservado aos artefatos históricos já usados nos freezes anteriores. Formato concreto adquirido prevalece no CorpusCase e divergências da curadoria inicial são registradas. M2 Blind Holdouts v1 já foram selecionados e permanecem FROZEN / UNREVEALED; `CC-05`, `CC-07`, `CC-14`, `CC-18` seguem em quarentena integral.

Docs: `planning/COMPATIBILITY-CORPUS-V1.md`, `corpus/COMPATIBILITY-CORPUS-V1.json`, `corpus/manifests/ACQUISITION-20260914.json`. Remaining-source queue: `planning/COMPATIBILITY-CORPUS-ACQUISITION-QUEUE.md`.

## M2 Blind Holdouts v1 — frozen 2026-09-14

Quatro novos holdouts M2 foram selecionados deterministicamente e permanecem não revelados. Casos reservados/quarentenados: CC-07, CC-18, CC-05, CC-14. A seleção está em `corpus/manifests/M2-BLIND-HOLDOUT-SELECTION-V1.json`; regression assertions v1 em `corpus/manifests/M2-REGRESSION-ASSERTIONS-V1.json`. Não processar/inspecionar esses SourceArtifacts antes do freeze do implementation candidate.


## Compatibility Corpus v1 — acquisition batch 2 — 2026-09-14

Segundo lote registrado sobre a baseline com holdouts já congelados. Foram incorporados 14 novos CorpusCases, elevando a aquisição para **28/30** naquele lote; o batch 3 incorporou o CC-08 substituto e o batch 4 fechou CC-15, levando o estado corrente a **30/30 FROZEN**. Duplicatas em `data/` dos SourceArtifacts em quarentena não foram importadas; `CC-05`, `CC-07`, `CC-14` e `CC-18` continuam frozen/unrevealed. Manifest: `corpus/manifests/ACQUISITION-20260914-BATCH2.json`.


## Compatibility Corpus v1 — acquisition batch 3 — 2026-09-14

`CC-08` foi substituído explicitamente pela manifestação oficial **eMAG — Modelo de Acessibilidade em Governo Eletrônico v3.1**, adquirida como bundle HTML salvo pelo navegador. A fonte oficial declara versão 3.1 (abril de 2014) e licença CC BY 4.0. Como HTML permanece fora do Tier 1 do M2, `CC-08` passa de Tier 1 para **Experimental**. Após o batch 4 de `CC-15`, o corpus está em **30/30 FROZEN**. Manifest: `corpus/manifests/ACQUISITION-20260914-BATCH3.json`.


## Compatibility Corpus v1 — final freeze — 2026-09-14

`CC-15` foi adquirido como archive HTML já renderizado da distribuição `stable rust-docs`, independente do `CC-14` quarantined. O corpus chega a **30/30**, shortlist **12/12**, e é congelado como Compatibility Corpus v1. Membership, manifestações concretas, metadata e bundle digests de v1 não devem ser alterados retroativamente. Blind holdouts `CC-05`, `CC-07`, `CC-14`, `CC-18` permanecem frozen/unrevealed. Próximo gate: plano de implementação do M2.


## Implementation Plan — 2026-09-14

Roadmap mestre: `docs/superpowers/plans/2026-09-14-m2-master-implementation-roadmap.md`. Foram separados seis subplanos executáveis: foundation/contracts, source evidence, reconstruction, materialization/validation, reprocessing/provenance/cost e corpus/candidate/holdout. O plano preserva o CBM v0.1, o Compatibility Corpus v1 30/30 e a quarentena de CC-05/CC-07/CC-14/CC-18.

## Estado de implementação M2 — 2026-09-14

- Execução inline selecionada para o roadmap M2.
- Plan 01 — Foundation & Contracts: implementação funcional realizada em branch local isolada `m2-plan01`.
- Implementados: bootstrap do pacote/CLI, digests/IDs, blob store content-addressed, contratos source/provenance, metadata SQLite/DAG, migrations e quarentena programática dos blind holdouts.
- Verificação compatível da sandbox: `18 passed, 1 skipped`; o skip é exclusivamente o property test Hypothesis indisponível no ambiente.
- A sandbox possui Python 3.13.5/uv 0.10.0 e não consegue resolver a baseline Python 3.14.7/uv 0.12.x; por isso `uv.lock` e o gate exato permanecem pendentes.
- Os SourceArtifacts `CC-05`, `CC-07`, `CC-14` e `CC-18` permanecem frozen/unrevealed e não foram abertos.
- Plan 02 não deve iniciar antes do gate exato do Plan 01.
