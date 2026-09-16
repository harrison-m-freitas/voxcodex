# Changelog do Contexto

## 2026-09-14 — Compatibility Corpus v1 — acquisition batch 3

- `CC-08` substituído explicitamente: Cartilha de Acessibilidade gov.br (PDF indisponível) → eMAG v3.1 oficial (HTML saved-page bundle);
- source bundle do CC-08 registrado com 54 artefatos e SHA-256 agregado;
- support tier de CC-08 alterado de Tier 1 para Experimental, coerente com HTML fora da claim Tier 1 do M2;
- corpus passa de 28/30 para **29/30**; shortlist permanece **12/12**;
- único pendente: `CC-15`;
- holdouts `CC-05`, `CC-07`, `CC-14`, `CC-18` permanecem frozen/unrevealed e `data/` histórico não é alterado.


## 2026-09-11 — v1.2 — Registro de M2.4–M2.6

- M2.4 — CBM Materialization & Validation aprovado e registrado;
- introduzidos `CanonicalDraft`, `MaterializationRun`, `MaterializationIssue`, evidence accountability e validation/freeze gates;
- registrados invariantes M01–M14;
- M2.5 — Reprocessing, Confidence & Provenance aprovado e registrado;
- fixados `ActivityFingerprint`, dependency-driven invalidation, confidence localizada, ReviewRisk, ReviewDecision, Usage/Cost e `ExecutionPlan`;
- registrados invariantes P01–P16;
- M2.6 — Compatibility Corpus & Exit Criteria aprovado e registrado;
- corpus separado em Regression Core, Compatibility Shortlist, Discovery Corpus e novos M2 Blind Holdouts;
- support tiers, evidence-accountability categories, silent-loss blocker e exit gates aprovados;
- registrados invariantes C01–C14;
- ADR expandido até AD-143;
- adicionados RISK-32–RISK-41;
- M2.1–M2.3 continuam frozen; M2.4–M2.6 estão aprovados, porém não frozen;
- próximo gate: review consolidado M2.1–M2.6 e freeze do M2 Design v0.1.

## 2026-09-11 — v1.1 — Freeze de design M2.1–M2.3

- M2.2 — Source Artifact & Evidence Model aprovado e congelado;
- M2.3 — Reconstruction Pipeline aprovado e congelado;
- definidos `SourceArtifact`, `SourceProfile`, `EvidenceSnapshot`, `EvidenceUnit`, `ReconstructionSnapshot`, `ReconstructionUnit`, `OpenStructuralState` e `ReconstructionIssue`;
- registrados invariantes E01–E10 e R01–R12;
- fixada separação native/geometric/logical reading order;
- fixado envelope comum de Evidence com payloads nativos extensíveis;
- fixada Reconstruction como DAG structure-first/deterministic-first/genre-agnostic;
- adicionados AD-099–AD-112 e RISK-26–RISK-31;
- criado `planning/M2-DESIGN-FREEZE-REVIEW.md`;
- criado `M2-DESIGN-FREEZE-MANIFEST.json` com snapshot de integridade do repositório;
- CBM v0.1 permanece inalterado;
- próximo gate: M2.4 — CBM Materialization & Validation.

## 2026-09-11 — v1.0 — Início do M2 / Boundary & Success Contract

- M2 nomeado **Document Reconstruction & CBM Materialization**;
- M2.1 — Boundary & Success Contract aprovado;
- fronteira definida como `SourceArtifact → Source Evidence → Document Reconstruction → CBM v0.1 CanonicalRevision → Validation/freeze`;
- Semantic Enrichment interpretativo, Narration, Performance e Audio mantidos downstream;
- Tier 1 inicial: PDF textual + Markdown; PDF mixed como Tier 1.5; OCR-heavy/EPUB/HTML/DOCX adiados no primeiro recorte;
- intermediários `EvidenceSnapshot` e `ReconstructionSnapshot` registrados conceitualmente como inspecionáveis;
- política determinístico → especializado → LLM → human review reafirmada;
- Compatibility Corpus aprovado como requisito transversal: shortlist 8–12 + corpus ampliado ~30;
- adicionada classificação `PROCESSING_FAILURE`, distinta de `MODEL_GAP`/`MODEL_FAILURE`;
- Schema Evolution Log passa a ser gate para mudanças futuras do CBM;
- criados `planning/M2-DOCUMENT-RECONSTRUCTION.md` e `planning/COMPATIBILITY-CORPUS.md`;
- ADR expandido até AD-098;
- adicionados RISK-23 a RISK-25;
- próximo passo: M2.2 — Source Artifact & Evidence Model.

## 2026-09-11 — v0.9 — Promoção para CBM v0.1 e encerramento do M1

- executado promotion review após blind holdout conformance;
- resultado: **PASS**;
- criado `architecture/CBM-V0.1.md` como baseline normativa promovida (`schema_version=0.1`);
- candidate congelado preservado sem alteração como evidência histórica;
- incorporados ao vocabulário comprovado `technical.terminal_input` e `editorial.omission_marker`;
- invariantes permanecem M1-I01–I18 e S01–S56, sem alteração pós-freeze;
- `MODEL_GAP=0`, `MODEL_FAILURE=0` em cross-genre + holdouts;
- criado `planning/M1-PROMOTION-REVIEW.md`;
- ADR atualizado até AD-090;
- M1 — Canonical Representation marcado como **concluído**;
- próximo passo: definir formalmente o próximo milestone usando o `CBM v0.1` como baseline.

## 2026-09-11 — Blind holdout conformance concluído

- F-RND (*Fedra*, PDF p.33): `PASS`;
- W-RND (Weidman, PDF p.558 / fólio 559): `PASS_WITH_EXTENSION`;
- extensões observadas: `technical.terminal_input` e `editorial.omission_marker`;
- zero mudanças em primitivas universais e zero mudanças em invariantes;
- `MODEL_GAP=0`, `MODEL_FAILURE=0`;
- nenhuma página adjacente foi aberta;
- `architecture/CBM-V0.1-CANDIDATE.md` permaneceu byte-for-byte inalterado em relação ao freeze;
- criado `planning/M1-HOLDOUT-CONFORMANCE.md`;
- criado `HOLDOUT-CONFORMANCE-MANIFEST.json`;
- ADR atualizado até AD-086;
- próximo gate: promotion review para `CBM v0.1`.

## 2026-09-11 — v0.7 — Freeze do CBM v0.1 candidate

- executado review final de freeze após F1/F2/W1/W2 + C1/C2/C3;
- resultado do review: **PASS**;
- criado `architecture/CBM-V0.1-CANDIDATE.md` como contrato normativo congelado (`schema_version=0.1-candidate`);
- criado `planning/M1-CBM-FREEZE-REVIEW.md`;
- criado `FREEZE-MANIFEST.json` com hashes do contrato, review e corpus;
- resolvido ownership: `ContentFragment` possui um único `DocumentNode` owner e refs de payload components são não-owning;
- removido `DocumentNode.status`, que não possuía semântica/vocabulário validado;
- removido `schema_version` de `CanonicalDocument`; versão do schema é autoridade de `CanonicalRevision`;
- `SemanticRegistry` passa a ser autoridade de membership de Annotation/Relation; reverse refs locais são projeções deriváveis;
- clarificada imutabilidade: transições administrativas frozen→superseded/invalid não alteram payload nem content digest;
- `ValidationReport` passa a registrar `validation_policy_ref`; freeze de revision exige source mapping, provenance, validation report e digest;
- invariantes de schema expandidos para **S01–S56**;
- ADR expandido até **AD-083**;
- alpha preservado como predecessor histórico;
- holdouts F-RND p.33 e W-RND p.558 permaneceram fechados durante o review e agora estão liberados somente para blind conformance;
- qualquer alteração exigida por holdout deve gerar novo candidate/versionamento; o candidate congelado não será editado retroativamente.

## 2026-09-10 — v0.6 — Cross-genre C1–C3 incorporado

- concluída a validação cross-genre do `CBM v0.1-alpha candidate`;
- C1, C2 e C3: `PASS_WITH_EXTENSION`;
- zero novas primitivas universais;
- criado `planning/M1-CROSS-GENRE-VALIDATION.md`;
- incorporados vocabulários de footnotes/citations, narrativa, matemática e pedagogia;
- `FormulaPayload` validado/refinado com source vs reconstructed representations;
- `structured.figure_panel` validado;
- mixed-content ordering formalizado como S51;
- adicionado RISK-22 para corrupção semântica plausível em text layer matemático;
- ADR expandido até AD-076;
- holdouts F-RND e W-RND permanecem fechados;
- próximo gate: freeze/promoção para `CBM v0.1 candidate`.

## 2026-09-10 — v0.5 — CBM v0.1-alpha candidate

- aprovadas e consolidadas as Seções 1–7 do Canonical Book Model;
- criado `architecture/CBM-V0.1-ALPHA.md` como contrato normativo do `CBM v0.1-alpha candidate`;
- escolhido núcleo composicional tipado (`DocumentNode` + `ContentFragment` + roles + grafo semântico complementar);
- inferências formalmente restritas a `Annotation`/`Relation`; não podem sobrescrever conteúdo canônico;
- `node_class` definido como vocabulário pequeno/controlado e `role` como namespace extensível;
- aprovada a decisão `SpeakerCue` sibling de `Speech`, ligados por Relations;
- SourceAnchor formalizado com SourceArtifact imutável, índice físico vs. fólio, regiões normalizadas e múltiplos anchors;
- Fidelity Policy consolidada em constraints ortogonais: lexical, character, structure, symbolic e ordering;
- formalizados `Entity`, `Annotation`, `Relation`, `Confidence` e status epistemológicos `explicit`, `derived`, `inferred`, `human_asserted`;
- Role Profiles aprovados como mecanismo de extensão/validação;
- TablePayload definido como primeiro StructuredPayload plenamente especificado;
- Figure/Formula limitados a fronteiras mínimas até validação com corpus real;
- provenance consolidada em `ProcessingActivity` + `Derivation`;
- `CanonicalDocument` separado de `CanonicalRevision`; revisions frozen são imutáveis;
- contrato admite DAG de revisions, com implementação inicial linear;
- registries/manifests, ValidationReport/ValidationPolicy e content digests incorporados conceitualmente;
- definidos 50 invariantes de schema S01–S50;
- ADR expandido até AD-066;
- registrado um ponto ainda aberto: ownership de ContentFragment referenciado por componentes de StructuredPayload;
- próxima etapa: validação cross-genre; holdouts cegos permanecem fechados.

## 2026-09-09 — v0.4 — M1/W1 + W2 e fechamento dos golden slices

- concluídos e aprovados W1 (Weidman, PDF p.112) e W2 (Weidman, PDF p.96);
- revisado M1-I07: `textual_exact` passa a ser política padrão para texto autoral/editorial narrável no modo Fiel, independentemente do gênero;
- aprovados M1-I12 a M1-I18;
- registrado que tipografia/layout podem ser evidência semântica sem se confundirem com a semântica derivada;
- registrado que running headers e fólios repetidos não criam duplicação lógica;
- fidelidade passa a admitir refinamento local em spans/subunidades;
- preservação literal deixa explícito que código, terminal e outros conteúdos estruturados não podem ser achatados em strings opacas;
- tabelas passam a exigir preservação de topologia estrutural;
- separado lexema superficial de valor interpretado/normalizado (`011` ≠ inteiro 11);
- registrado que adjacência visual não implica origem semântica comum, cobrindo callouts editoriais intercalados em saídas de terminal;
- confirmadas as distinções `Listing` (função editorial) vs. `TerminalTranscript`/`CodeBlock` (natureza do conteúdo);
- registrados índice físico da página vs. fólio impresso, referências resolvidas e notas da fonte vs. conteúdo auxiliar do sistema;
- os quatro golden slices F1/F2/W1/W2 estão concluídos;
- total de invariantes aprovados do M1: 18;
- F-RND p.33 e W-RND p.558 permanecem fechados;
- próxima ação: consolidar `CBM v0.1-alpha` e executar validação cross-genre.


## 2026-09-09 — v0.3 — M1/F2 e validação cross-genre

- concluído e aprovado F2 (*Fedra*, PDFs p. 10–11);
- confirmados os sete invariantes de F1;
- aprovados M1-I08, M1-I09 e M1-I10;
- aprovado M1-I11: especializações de gênero não contaminam o núcleo universal do CBM;
- registrado que fronteiras operacionais de página/chunk/batch/worker não encerram estruturas lógicas;
- diferenciados estado declarado, transição inferida e papel documental original;
- `SceneParticipantDeclaration` mantido como conceito teatral/específico, não como requisito universal do núcleo;
- adicionada validação cross-genre antes dos holdouts cegos, incluindo romance adicional, webnovel e outro material técnico quando disponível;
- adicionado RISK-11: overfitting do CBM ao gênero/formato do corpus-base;
- F-RND p.33 e W-RND p.558 continuam fechados;
- próxima ação: M1.1 W1, Weidman PDF p.112.
## 2026-09-09 — v0.2 — M1/F1 registrado

- iniciado o milestone M1 — Canonical Representation;
- fixado corpus de conformidade em 4 golden slices + 2 holdouts cegos;
- reservadas as páginas F-RND p.33 e W-RND p.558 sem análise até o freeze do CBM v0.1 candidate;
- fixadas as edições/arquivos concretos do PoC e seus SHA-256;
- concluído e aprovado F1 (*Fedra*, PDF p. 6);
- registrados sete invariantes do F1;
- `PhysicalPage` removida da hierarquia lógica do conteúdo e tratada por `SourceAnchor`;
- separados conceitualmente `Character`, `SpeakerCue` e `Speech`;
- estabelecida distinção obrigatória entre evidência explícita e inferência semântica;
- estabelecida identidade própria de `VerseLine`, independente de `Sentence`;
- movida a decisão concreta de apresentação sonora para Narration Model/perfil;
- criada e aceita a política `textual_exact` para literatura no modo Fiel;
- próxima ação: M1.1 F2, páginas 10–11 de *Fedra*.

## 2026-09-09 — v0.1

Criada a base documental do projeto.

Consolidado:

- visão do produto;
- domínios;
- arquitetura conceitual;
- invariantes;
- Canonical Book Model inicial;
- provenance/versionamento;
- corpus do PoC;
- português como Tier 1;
- inglês oportunista;
- Audiobook Fiel como produto-base;
- Fidelity Policy;
- Narration Policy;
- critérios de sucesso do PoC;
- ADR inicial;
- registro de riscos;
- questões em aberto.

Próxima etapa:
formalizar CBM e contratos entre Source, Canonical, Narration, Performance e Audio.

## 2026-09-11 — M2 consolidated design review

- executado review consolidado M2.1–M2.6 contra `CBM v0.1`, ADRs, requirements, risks e manifests;
- resultado: **BLOCKED_FOR_FREEZE**;
- zero mudanças exigidas no core do `CBM v0.1`;
- identificados 5 blockers normativos: ownership ProcessingActivity/Derivation, autoridade da hierarquia ReconstructionUnit, bootstrap CanonicalDocument/Work/Edition, revalidation de revision frozen e protocolo de candidate/claims para blind holdouts;
- registradas 8 clarificações obrigatórias antes do freeze;
- criado `planning/M2-CONSOLIDATED-DESIGN-REVIEW.md`;
- nenhuma correção arquitetural foi aplicada silenciosamente; próximo gate é aprovação/resolução dos findings seguida de freeze final.


## 2026-09-11 — M2 Design v0.1 — final freeze

- resolvidos B1–B5 e Q1–Q8 do review consolidado;
- `Derivation` fixada como autoridade causal de input/output;
- adicionada autoridade hierárquica `parent_ref + order_key` em Reconstruction (`R13`);
- introduzido `CanonicalTargetContext` operacional para bootstrap canônico;
- congelada semântica de revalidation de frozen revision via reports suplementares;
- blind protocol endurecido com freeze de assertions/holdout selection e candidate claims/config (`C15–C16`);
- `stale` formalizado como estado contextual; evidence/provenance frozen deve permanecer endereçável;
- significance de Evidence e Compatibility gates tornados policy/support-tier controlled;
- criado `architecture/M2-DESIGN-V0.1.md` e freeze manifest final;
- nenhuma mudança no core/S01–S56 do `CBM v0.1`;
- stack/serialization/providers continuam não selecionados.

## 2026-09-14 — Compatibility Corpus v1 — shortlist acquisition complete

- concretizados 30 CorpusCases (`CC-01`–`CC-30`);
- shortlist fixada em 12 casos e aquisição concluída 12/12;
- corpus total adquirido: 14/30; 16 casos pendentes;
- adicionada árvore `corpus/compatibility/` sem alterar `data/` histórico;
- hashes/tamanhos registrados por caso e snapshot em `corpus/manifests/ACQUISITION-20260914.json`;
- formatos concretos de CC-04, CC-07 e CC-12 registrados como PDF, divergindo da curadoria inicial;
- Python EPUB preservado como auxiliar de CC-03; Rust repository ZIP preservado como acquisition bundle de CC-14;
- blind holdouts M2 continuam não selecionados;
- próximo gate: adquirir/verificar os 16 restantes, depois congelar holdouts e escrever plano de implementação.

## 2026-09-14 — M2 blind holdouts v1 + regression assertions freeze

- selecionados e congelados quatro blind holdouts novos: M2-H1..M2-H4;
- seleção feita sem inspeção/renderização/extraction de conteúdo reservado;
- SourceArtifacts CC-07, CC-18, CC-05 e CC-14 colocados em quarentena integral até implementation candidate freeze;
- congeladas Regression Assertions v1 para os nove casos já conhecidos;
- holdout/regr assertions manifests versionados sob `corpus/manifests/`;
- aquisição dos 16 casos restantes continua independente do blind freeze;
- próximo gate após aquisição: M2 implementation plan; reveal só ocorrerá após candidate freeze.


## 2026-09-14 — Compatibility Corpus v1 — acquisition batch 2

- incorporados 14 novos CorpusCases a partir de `VoxCodex-20260914-163637.zip` sobre a baseline M2 Holdouts v1 frozen;
- corpus passa de 14/30 para **28/30**; shortlist permanece **12/12**;
- pendentes confirmados: `CC-08, CC-15`;
- `CC-05`, `CC-07`, `CC-14`, `CC-18` permaneceram integralmente em quarentena e suas cópias duplicadas no upload não foram importadas;
- `data/` histórico da baseline não foi alterado;
- hashes, tamanhos, formatos concretos e entrypoints registrados nos `metadata.json`;
- criado `corpus/manifests/ACQUISITION-20260914-BATCH2.json`;
- próximo gate: adquirir `CC-08, CC-15` e fechar Compatibility Corpus v1 em 30/30 antes do plano de implementação.


## 2026-09-14 — Compatibility Corpus v1 — final freeze 30/30

- adquirido `CC-15` como `CC-15-rust-book-stable-html.zip`, archive HTML já renderizado da distribuição local stable rust-docs;
- CC-15 foi adquirido independentemente de `CC-14`, preservando a quarentena do blind holdout Markdown;
- Compatibility Corpus v1 chega a **30/30**, shortlist **12/12**, e é congelado;
- membership, manifestações concretas, metadata e bundle digests de v1 passam a ser imutáveis por política;
- M2 Blind Holdouts v1 permanecem frozen/unrevealed;
- próximo gate: plano de implementação do M2.


## 2026-09-14 — M2 implementation plan authored

- Added master implementation roadmap plus six executable subplans under `docs/superpowers/plans/`.
- Selected a conservative local M2 implementation baseline without changing frozen architecture or CBM v0.1.
- Kept CC-05, CC-07, CC-14 and CC-18 quarantined/unrevealed through implementation-candidate freeze.
- Corrected current status references to Compatibility Corpus v1 FROZEN 30/30.

## 2026-09-14 — M2 Plan 01 inline implementation checkpoint

- iniciada execução inline do roadmap M2 em workspace/branch isolados;
- implementados bootstrap Python/CLI, digests/IDs, blob store content-addressed, contratos frozen, SQLite dependency DAG + Alembic e corpus quarantine guard;
- suite compatível da sandbox: 18 passed, 1 skipped (Hypothesis ausente);
- migration 0001 validada em SQLite limpo;
- teste de quarentena confirma bloqueio antes de `Path.open`; zero source reads dos quatro blind holdouts;
- baseline declarada Python 3.14.7/uv 0.12.x preservada; `uv.lock` não foi fabricado porque a sandbox só oferece Python 3.13.5/uv 0.10.0 e não consegue resolver a toolchain/dependências;
- Plan 01 fica `functional_implemented_environment_gate_pending`; Plan 02 bloqueado até execução do gate exato.
