# Architecture Decision Log

| ID | Decisão | Estado | Motivo resumido |
|---|---|---|---|
| AD-001 | Fonte original é imutável | aceita | fidelidade |
| AD-002 | CBM separado da fonte | aceita | normalização sem destruir evidência |
| AD-003 | Narration Model separado do CBM | aceita | separar conteúdo e adaptação |
| AD-004 | Performance Model separado da narração | aceita | desacoplar edição de TTS |
| AD-005 | Toda derivação relevante possui provenance | aceita | auditabilidade |
| AD-006 | Pipeline conceitualmente como DAG | aceita | paralelismo e reprocessamento |
| AD-007 | Artefatos intermediários são versionáveis | aceita | reuso e comparação |
| AD-008 | Custo é estimado antes de etapas caras | aceita | controle econômico |
| AD-009 | Preferir solução determinística quando suficiente | aceita | custo e previsibilidade |
| AD-010 | Human-in-the-loop orientado a risco/confiança | aceita | qualidade sem revisão universal |
| AD-011 | Evitar microserviços inicialmente | aceita | evitar overengineering |
| AD-012 | Abstrações multi-provider somente onde houver valor concreto | proposta | evitar abstração prematura |
| AD-013 | Corpus PoC = Fedra + Weidman | aceita | gêneros complementares |
| AD-014 | Português é Tier 1 | aceita | escopo inicial |
| AD-015 | Inglês com suporte oportunista | aceita | baixo custo incremental |
| AD-016 | Tradução fora do PoC | aceita | reduzir escopo |
| AD-017 | Audiobook Fiel é o produto-base | aceita | referência editorial |
| AD-018 | Fiel permite adaptação auditiva rastreável | aceita | adequação ao meio sem enriquecimento oculto |
| AD-019 | Fidelidade depende do tipo de conteúdo | aceita | prosa ≠ código ≠ fórmula |
| AD-020 | Narrabilidade é independente da fidelidade | aceita | separar preservação de apresentação |
| AD-021 | M1 usa 4 golden slices + 2 páginas holdout cegas | aceita | testar conformidade e generalização sem enviesar o schema |
| AD-022 | Holdouts F-RND p.33 e W-RND p.558 permanecem fechados até o freeze do CBM v0.1 candidate | aceita | preservar teste de surpresa real |
| AD-023 | PhysicalPage não é pai lógico do conteúdo canônico | aceita | fronteiras físicas podem cortar fala, parágrafo ou outro nó lógico |
| AD-024 | Source surface text permanece recuperável após normalizações | aceita | preservar fielmente a edição ingerida |
| AD-025 | Character, SpeakerCue e Speech são conceitos distintos | aceita | separar entidade, evidência textual e unidade lógica de fala |
| AD-026 | Evidência explícita e inferência semântica não são colapsadas | aceita | impedir que interpretação adquira falsa autoridade de fonte |
| AD-027 | VerseLine possui identidade própria e é independente de Sentence | aceita | preservar forma literária sem conflar estrutura poética e linguística |
| AD-028 | Decisão concreta de narração pertence ao Narration Model/perfil, não ao CBM | aceita | mesma fonte admite estratégias sonoras diferentes sem mudar o canônico |
| AD-029 | Literatura no modo Fiel usa `textual_exact` como política primária | aceita | equivalência apenas semântica permitiria paráfrases incompatíveis com fidelidade literária |
| AD-030 | Fronteiras de processamento não encerram unidades lógicas | aceita | páginas, chunks, batches ou workers podem cortar uma mesma estrutura; continuidade deve ser preservada ou reconciliada |
| AD-031 | Estado declarado não equivale a transição inferida | aceita | listas de participantes ou estados explícitos não devem ser convertidos silenciosamente em eventos de entrada/saída |
| AD-032 | Papel documental não muda por implicação semântica | aceita | uma fala que descreve uma ação continua sendo fala; eventos/referências inferidos são anotações derivadas |
| AD-033 | Especializações de gênero não contaminam o núcleo do CBM | aceita | Act, Scene, SceneParticipantDeclaration, TerminalTranscript etc. podem existir como extensões/roles sem virar requisitos universais |
| AD-034 | M1 terá validação cross-genre antes dos holdouts cegos | aceita | testar generalização em romance, webnovel e outro material técnico antes do teste-surpresa intraobra |
| AD-035 | Generalizar `textual_exact` para texto autoral/editorial narrável do modo Fiel | aceita | fidelidade textual não depende do gênero; literatura e prosa técnica não devem ser parafraseadas silenciosamente |
| AD-036 | Propriedades visuais da fonte podem constituir evidência semântica | aceita | tipografia/layout podem distinguir prompt, input, callout e outros papéis sem que estilo e semântica sejam colapsados |
| AD-037 | Repetição física/editorial não cria duplicação lógica | aceita | running headers e fólios repetem-se por paginação, não por nova estrutura canônica |
| AD-038 | Fidelity Policy admite refinamento local em spans/subunidades | aceita | um parágrafo textual_exact pode conter comando/IP/token que exige literal_exact |
| AD-039 | Preservação literal não implica achatamento estrutural | aceita | terminal, código e outros conteúdos podem ser literal_exact e ainda conservar estrutura interna |
| AD-040 | Dados estruturados preservam topologia canônica | aceita | tabelas não podem ser substituídas por linearização textual quando relações linha/coluna carregam significado |
| AD-041 | Representação superficial é distinta de valor interpretado | aceita | lexemas como `011` devem sobreviver mesmo quando houver valor binário/numericamente derivado |
| AD-042 | Adjacência visual não implica origem/função semântica comum | aceita | callouts editoriais podem estar intercalados em saída literal sem fazer parte dela |
| AD-043 | CBM adota núcleo composicional tipado em vez de hierarquia OO rígida ou graph-first puro | aceita | preservar estrutura lógica com extensibilidade por roles e grafo semântico complementar |
| AD-044 | Inferências coexistem no CBM somente como Annotation/Relation qualificadas e nunca sobrescrevem conteúdo canônico | aceita | transformar evidence ≠ inference em propriedade estrutural |
| AD-045 | DocumentNode representa estrutura lógica e ContentFragment representa conteúdo granular | aceita | permitir granularidade sem transformar cada span em node estrutural |
| AD-046 | node_class é vocabulário pequeno/controlado e role é namespaced/extensível | aceita | evitar overfitting de gênero sem perder validação |
| AD-047 | surface.text permanece canônico dentro da revision; normalizações são annotations/derivações | aceita | preservar forma da edição e auditabilidade |
| AD-048 | SpeakerCue é sibling de Speech e ambos se ligam por Relations | aceita | speaker cue pode existir/ser ausente independentemente da unidade de fala |
| AD-049 | StructuredPayload é excepcional; TablePayload é o primeiro payload plenamente definido | aceita | usar payload apenas quando árvore+fragments não preservarem a topologia |
| AD-050 | SourceAnchor é separado da Source Evidence, admite múltiplos anchors e geometria canônica normalizada | aceita | desacoplar localização canônica de extratores/provedores específicos |
| AD-051 | Fidelity usa constraints ortogonais em vez de enum único | aceita | representar simultaneamente fidelidade lexical, de caracteres, estrutural, simbólica e de ordem |
| AD-052 | Constraints de fidelity são herdáveis e só podem ser refinadas para maior rigor sem transformação explícita | aceita | impedir enfraquecimento silencioso de garantias |
| AD-053 | Provenance separa ProcessingActivity de Derivation e unifica determinístico, IA e humano | aceita | lineage uniforme e auditável |
| AD-054 | Entity vive fora da árvore; EntityMention é Annotation | aceita | manter identidade global independente de ocorrências textuais |
| AD-055 | Annotation e Relation são tipadas/namespaced e carregam status epistemológico | aceita | evitar semantic bag e falsa equivalência entre explícito, derivado e inferido |
| AD-056 | Eventos semânticos ficam como Annotation no alpha; cross-reference separa mention de target resolvido | aceita | evitar ontologia temporal prematura e preservar referências não resolvidas |
| AD-057 | RoleProfile é o mecanismo de contrato/validação para especializações | aceita | permitir extensões sem modificar primitivas do core |
| AD-058 | Figure e Formula entram no alpha apenas com fronteiras mínimas sustentadas pela fonte | aceita | evitar overengineering sem corpus suficiente |
| AD-059 | CanonicalDocument é identidade durável e CanonicalRevision é snapshot lógico versionado | aceita | separar identidade da edição de estados reprocessados |
| AD-060 | Revisions frozen são imutáveis; correção/reprocessamento cria nova revision | aceita | preservar histórico e reprodutibilidade |
| AD-061 | Contrato admite DAG de revisions, mas implementação inicial será linear | aceita | não bloquear evolução sem construir branching/merge prematuramente |
| AD-062 | Membership de revision é explícito por registries e objetos imutáveis podem ser reutilizados sem derivação artificial | aceita | reprocessamento seletivo com provenance sem ruído |
| AD-063 | Revision frozen exige ValidationReport; active_revision aponta apenas para frozen | aceita | criar fronteira segura para consumers downstream |
| AD-064 | Derived artifacts downstream referenciam explicitamente a CanonicalRevision consumida | aceita | reprodutibilidade ponta a ponta |
| AD-065 | schema_version e revision_number são dimensões independentes; migração de schema é ProcessingActivity | aceita | distinguir evolução do contrato de evolução do conteúdo |
| AD-066 | CBM v0.1-alpha é candidate para validação cross-genre, ainda não frozen | aceita | submeter o contrato consolidado a corpus externo antes dos holdouts |
| AD-067 | C1 valida footnotes, citações/referências externas e listas por extensões, sem mudar o core | aceita | layout em colunas, notes e targets externos foram representáveis por roles/annotations/relations e SourceAnchors |
| AD-068 | Funções semânticas podem coincidir com DocumentNode inteiro ou existir como Annotation em span/fragment | aceita | C2 mostrou fala/pensamento como bloco autônomo e também inline dentro de parágrafo |
| AD-069 | Speaker/thinker narrativo são Relations contextuais e podem permanecer não resolvidos | aceita | webnovel não possui SpeakerCue teatral e o sistema não deve fabricar falantes para preencher lacunas |
| AD-070 | Manifestações/traduções em idiomas diferentes não são fundidas automaticamente no mesmo CBM | aceita | diferenças editoriais EN/PT-BR exigem preservar evidência de cada manifestação; alignment fica futuro/downstream |
| AD-071 | FormulaPayload é especialização validada e separa representações da fonte de representações reconstruídas | aceita | Stewart demonstrou necessidade de topologia simbólica e provenance sem promover reconstrução a conteúdo original |
| AD-072 | Conteúdo misto usa um único espaço lógico de order_key entre fragments e child nodes do mesmo parent | aceita | matemática inline exige reconstruir texto → fórmula → texto sem duas ordens concorrentes |
| AD-073 | Figuras multipainel são endereçáveis por `structured.figure_panel`; interpretação visual permanece derivada | aceita | referências a painéis exigem granularidade sem tornar análise do gráfico parte da fonte |
| AD-074 | Estruturas pedagógicas e matemáticas específicas usam roles/relations, não primitivas universais | aceita | Definition, Example, Solution, Exercise e derivations foram representáveis pelo mecanismo de extensão |
| AD-075 | Text layer de PDF matemático é evidência não autoritativa quando perde estrutura; reconstrução exige evidência visual/layout e provenance | aceita | C3 mostrou perdas plausíveis de operadores, scripts e relações bidimensionais |
| AD-076 | Validação cross-genre C1–C3 concluída com PASS_WITH_EXTENSION e zero mudanças em primitivas universais | aceita | core composicional generalizou para teologia, webnovel e cálculo; próximo gate é freeze/promoção antes dos holdouts |
| AD-077 | `ContentFragment.owner_node_ref` permanece um único `DocumentNode`; refs de componentes de StructuredPayload são não-owning | aceita | C1–C3 não demonstraram necessidade de ownership polimórfico; evita generalização prematura |
| AD-078 | `DocumentNode.status` é removido do v0.1 candidate | aceita | campo obrigatório sem vocabulário/semântica validada não deve ser congelado |
| AD-079 | `schema_version` pertence à CanonicalRevision, não ao CanonicalDocument | aceita | um mesmo documento pode possuir revisions em schemas diferentes após migração |
| AD-080 | SemanticRegistry é a autoridade de membership de Annotation/Relation; reverse refs locais são projeções deriváveis | aceita | preservar reuso imutável de nodes/fragments/entities quando apenas a camada semântica muda |
| AD-081 | Mudanças administrativas frozen→superseded/invalid não alteram payload nem content_digest | aceita | reconciliar lifecycle posterior com imutabilidade sem perder auditabilidade |
| AD-082 | ValidationReport registra ValidationPolicy; revision frozen exige source mapping, provenance, validation report e content digest | aceita | freeze precisa ser reproduzível e verificável contra policy explícita |
| AD-083 | CBM v0.1 candidate (`schema_version=0.1-candidate`) é congelado para blind holdout conformance | aceita | freeze review passou após resolver blockers; holdouts podem ser abertos sem permitir ajuste retroativo do candidate |

| AD-084 | F-RND (*Fedra* p.33) passa blind conformance sem extensão ou mudança de core | aceita | continuidade de fala cross-page, transição de cena, speaker cues, participant declaration e versos foram representados diretamente pelo candidate congelado |
| AD-085 | W-RND (Weidman p.558) passa com extensões namespaced `technical.terminal_input` e `editorial.omission_marker` | aceita | interação literal e omissão editorial exigem apenas vocabulário extensível; tipografia permanece evidência e nenhuma primitiva/invariante muda |
| AD-086 | Blind holdout conformance é concluído sem MODEL_GAP/MODEL_FAILURE e com zero mudanças no core universal | aceita | F-RND=PASS e W-RND=PASS_WITH_EXTENSION; candidate congelado permanece inalterado e fica elegível para promotion review de CBM v0.1 |
| AD-087 | CBM v0.1 candidate é promovido formalmente para `CBM v0.1` após promotion review `PASS` | aceita | golden slices, cross-genre e blind holdouts concluíram sem MODEL_GAP/MODEL_FAILURE nem mudança pós-freeze no core/invariantes |
| AD-088 | `technical.terminal_input` e `editorial.omission_marker` entram no vocabulário comprovado do v0.1 como extensões namespaced | aceita | W-RND validou ambos e o mecanismo de extensão congelado já os comporta sem alteração normativa do core |
| AD-089 | M1 — Canonical Representation é encerrado com `architecture/CBM-V0.1.md` como baseline normativa | aceita | os gates empíricos e de integridade foram concluídos; itens restantes são implementação/downstream/evolução e não bloqueiam o contrato canônico |
| AD-090 | Candidate, freeze manifest e holdout manifest permanecem históricos e imutáveis após a promoção | aceita | preservar trilha auditável; evolução futura usa versionamento explícito em vez de reescrita retroativa |
| AD-091 | M2 é `Document Reconstruction & CBM Materialization` e vai de SourceArtifact a CanonicalRevision CBM v0.1 validada/frozen | aceita | provar produção automática do contrato canônico sem misturar ainda Narration/Audio |
| AD-092 | Semantic Enrichment interpretativo e Narration/Performance/Audio permanecem downstream do M2 | aceita | separar reconstrução documental de interpretação e produção sonora para diagnosticar falhas |
| AD-093 | Tier 1 inicial do M2 é PDF textual + Markdown; PDF mixed é Tier 1.5; OCR-heavy/EPUB/HTML/DOCX ficam adiados no primeiro recorte | aceita | maximizar profundidade no corpus já disponível sem suporte universal prematuro |
| AD-094 | M2 preserva intermediários inspecionáveis entre SourceArtifact, Source Evidence, Reconstruction e CanonicalRevision | aceita | distinguir perda de extração, erro de reconstrução e erro de materialização canônica |
| AD-095 | M2 mantém política determinístico → modelo especializado → LLM → human review conforme necessidade | aceita | previsibilidade/custo e uso de IA apenas onde a ambiguidade justificar |
| AD-096 | Compatibility Corpus distingue `PROCESSING_FAILURE` de `MODEL_GAP` e `MODEL_FAILURE` | aceita | impedir que bugs/limitações do pipeline sejam tratados como defeitos do CBM |
| AD-097 | CBM v0.1 permanece baseline estável; expansão usa shortlist 8–12 + corpus de descoberta ~30 + Schema Evolution Log | aceita | ampliar abstração durante processamento real sem reabrir o core a cada documento novo |
| AD-098 | Compatibility Corpus deve cobrir fenômenos estruturais e formatos; mesma obra em múltiplos containers pode testar equivalência canônica | aceita | detectar vazamento de peculiaridades de parser/container para o modelo canônico |
| AD-099 | SourceArtifact representa bytes imutáveis; reparos/normalizações produzem artefatos derivados | aceita | preservar integridade da fonte e auditabilidade |
| AD-100 | SourceProfile é inspeção operacional e não autoridade documental | aceita | rota de processamento não deve ser confundida com verdade canônica |
| AD-101 | EvidenceSnapshot é imutável/versionável e múltiplas extrações podem coexistir | aceita | comparar extractors e reprocessar sem apagar evidência anterior |
| AD-102 | Source Evidence usa envelope EvidenceUnit comum com payload nativo extensível | aceita | unificar provenance/anchors sem achatar particularidades de PDF/Markdown/futuros formatos |
| AD-103 | Evidence preserva geometry/typography/surface como observação sem semântica automática | aceita | evitar bold=heading, monospace=code e outros atalhos incorretos |
| AD-104 | Native order, geometric order e logical reading order são separados; logical order pertence à Reconstruction | aceita | PDF object/layout order não é autoridade de leitura |
| AD-105 | Evidence confidence qualifica observação/extraction e não classificação documental | aceita | evitar misturar confiança de OCR/span com confiança de heading/role |
| AD-106 | Existe camada ReconstructionSnapshot/ReconstructionUnit entre Evidence e CBM | aceita | permitir corrigir hipóteses estruturais sem alterar evidência nem materializar CBM cedo demais |
| AD-107 | Reconstruction é organizada em estágios conceituais/DAG, não em serviços obrigatórios | aceita | permitir grouping/order/classification/structured reconstruction com feedback controlado sem microservices prematuros |
| AD-108 | OpenStructuralState preserva unidades abertas através de páginas/colunas/chunks/batches/workers | aceita | processing boundaries não podem encerrar estrutura lógica |
| AD-109 | ReconstructionIssue representa incerteza/falha local e interpretação parcial é válida | aceita | não inventar resolução nem perder evidência para completar documento |
| AD-110 | Structured reconstruction preserva topologia antes de linearização e usa módulos especializados quando necessário | aceita | tabelas, terminal, código, fórmulas e figuras exigem estrutura própria sem contaminar core |
| AD-111 | Reconstruction é structure-first, deterministic-first e genre-agnostic | aceita | gênero não é roteador primário; estruturas reais podem cruzar gêneros |
| AD-112 | M2.1–M2.3 são congelados como baseline de design antes de M2.4 | aceita | preservar contexto/decisões aprovadas e impedir drift enquanto materialization/validation ainda serão desenhados |
| AD-113 | M2.4 usa CanonicalDraft operacional antes de CanonicalRevision validada | aceita | separar construção incompleta de snapshot canônico íntegro |
| AD-114 | Materialização Reconstruction→CBM é predominantemente determinística e não reinterpreta reading order | aceita | preservar fronteira M2.3/M2.4 e diagnóstico de falhas |
| AD-115 | SourceAnchors são gerados sistematicamente para conteúdo source-derived quando aplicável | aceita | garantir traceability fim a fim sem inventar regiões cross-page |
| AD-116 | Fidelity é aplicada por RoleProfile/policy e validada por effective constraints | aceita | evitar regras ad hoc e enfraquecimento silencioso |
| AD-117 | StructuredPayload é materializado a partir de StructuredCandidate resolvido; M2.4 não reconstrói novamente | aceita | manter responsabilidade estrutural em M2.3 |
| AD-118 | M2.4 materializa semântica documental resolvida, mas Semantic Enrichment interpretativo permanece downstream | aceita | separar relações editoriais de interpretação literária/semântica |
| AD-119 | Validation ocorre em camadas: schema, structure, traceability/fidelity, cross-object integrity e evidence accountability | aceita | detectar perda/violação mesmo quando JSON é estruturalmente válido |
| AD-120 | Evidence significativa não mapeada deve ser explicitamente contabilizada e suspected silent loss pode bloquear freeze | aceita | não confundir não-canônico intencional com perda silenciosa |
| AD-121 | Freeze de CanonicalRevision exige ValidationPolicy versionada, ausência de blockers, digest, provenance e source mapping/accountability | aceita | freeze reproduzível e auditável |
| AD-122 | Materialização deve ser semanticamente idempotente para ReconstructionSnapshot/schema/config equivalentes | aceita | habilitar cache, comparação e reprocessamento seguro |
| AD-123 | ProcessingActivity é unidade operacional de lineage para extraction, reconstruction, materialization, validation e review | aceita | unificar provenance sem acoplar domínio a processor específico |
| AD-124 | ActivityFingerprint usa inputs, processor/version, config semanticamente relevante e schema/profile versions | aceita | cache/reuse baseado em equivalência de execução e não apenas filename |
| AD-125 | Cache reuse preserva provenance original e não cria derivação falsa | aceita | auditabilidade do output reutilizado |
| AD-126 | Invalidação é dirigida pelo DAG real de dependências downstream | aceita | evitar matriz global frágil e permitir reprocessing seletivo |
| AD-127 | Confidence permanece localizada e scores distintos não são comparáveis sem calibração | aceita | evitar score documental enganoso e thresholds universais inválidos |
| AD-128 | ReviewRisk é distinto de confidence e revisão humana é registrada como ProcessingActivity/Derivation | aceita | priorizar revisão por impacto sem mutação silenciosa |
| AD-129 | Provenance e observability são modelos distintos embora correlacionáveis | aceita | lineage não deve ser reduzido a logs operacionais |
| AD-130 | Usage/cost são atribuíveis a ProcessingActivity e operações caras suportam ExecutionPlan/dry-run quando possível | aceita | estimar/reconciliar custo e reuso antes da execução |
| AD-131 | Configuração semântica participa do fingerprint; configuração puramente operacional não | aceita | evitar invalidação/cache miss por mudanças irrelevantes ao output |
| AD-132 | Reprocessamento parcial exige dependency closure/reconciliation suficiente para restaurar consistência | aceita | evitar patch local cego que quebra contexto adjacente |
| AD-133 | Compatibility Corpus possui papéis separados: Regression Core, Compatibility Shortlist, Discovery Corpus e M2 Blind Holdouts | aceita | cada conjunto tem função/gate diferente e evita contaminação experimental |
| AD-134 | Golden tests usam assertions estruturais/semânticas por camada em vez de snapshots serializados completos | aceita | testar contrato sem acoplar a IDs/serialização acidental |
| AD-135 | Support tiers são explícitos: Tier 1, Tier 1.5, Experimental e Deferred | aceita | capability claims e exit gates precisam ser verificáveis por escopo |
| AD-136 | Holdouts do M1 viram regressão; M2 exige novos blind holdouts selecionados antes da implementação | aceita | preservar teste cego real para o pipeline M2 |
| AD-137 | Conhecida perda silenciosa de conteúdo significativo bloqueia M2 | aceita | preservação é requisito mais forte que accuracy agregada |
| AD-138 | Evidence accountability usa categorias canonicalized/intentionally_noncanonical/unresolved/suspected_loss | aceita | distinguir exclusão editorial legítima de evidência não explicada |
| AD-139 | Selective reprocessing e idempotência são exit gates demonstrados, não apenas propriedades arquiteturais | aceita | provar reuse/invalidation reais antes de encerrar M2 |
| AD-140 | Discovery Corpus não precisa estar todo verde; todo achado deve ser classificado e registrado | aceita | usar corpus como sensor sem bloquear por capacidades explicitamente fora do tier |
| AD-141 | Falha em blind holdout não pode ser convertida em sucesso por tuning sobre o mesmo holdout | aceita | preservar validade experimental; caso revelado vira regressão |
| AD-142 | Schema Evolution descoberta no M2 usa log + novo candidate/versionamento e nunca reescreve CBM v0.1 | aceita | manter baseline estável e evolução auditável |
| AD-143 | M2.4–M2.6 estão aprovados; próximo gate é review consolidado M2.1–M2.6 antes do freeze completo | aceita | corrigir contradições entre seções antes de plano de implementação/stack |
| AD-144 | Derivation é a autoridade das arestas causais input/output; ProcessingActivity permanece unidade de execução | aceita | eliminar dupla autoridade de lineage e manter compatibilidade com CBM v0.1 |
| AD-145 | ReconstructionUnit usa parent_ref + order_key como autoridade hierárquica; child_refs é projeção derivável | aceita | evitar divergência de ownership/hierarquia |
| AD-146 | M2 usa CanonicalTargetContext operacional para bootstrap de Work/Edition/CanonicalDocument | aceita | materializar primeira CanonicalRevision sem inventar identidade bibliográfica |
| AD-147 | ValidationReport autorizador de freeze em revision frozen é imutável; revalidation posterior é suplementar externa | aceita | preservar imutabilidade de revision e permitir novas policies sem rematerialização |
| AD-148 | Blind protocol congela assertions/holdout selection e depois candidate identity/config/claims antes do reveal | aceita | impedir claim drift e tuning retroativo |
| AD-149 | Contratos operacionais M2 são separados das primitivas CBM; reconstruction validation é operacional própria | aceita | evitar extensão silenciosa do core e conflito com ValidationReport canônico |
| AD-150 | Significância de Evidence e gates de Compatibility são policy-controlled e avaliados por support tier | aceita | tornar accountability reproduzível sem ampliar claims implicitamente |
| AD-151 | Staleness é contextual e lineage evidence/provenance de frozen revisions deve permanecer endereçável | aceita | preservar imutabilidade e auditabilidade prática |
| AD-152 | M2 Design v0.1 tem CBM v0.1 como baseline e freeze normativo próprio; rebaseline exige decisão/versionamento explícitos | aceita | evitar troca silenciosa de baseline e separar working docs de contrato congelado |

| AD-153 | Compatibility Corpus v1 é fixado em 30 CorpusCases concretos | aceita | transformar a estratégia de ~30 materiais em conjunto identificável e testável antes do plano de implementação |
| AD-154 | Compatibility Shortlist v1 é fixada em 12 casos: CC-01, CC-03, CC-04, CC-05, CC-09, CC-11, CC-12, CC-13, CC-14, CC-16, CC-18 e CC-23 | aceita | maximizar cobertura estrutural/formatos sem confundir shortlist com support claim |
| AD-155 | Novas aquisições do Compatibility Corpus vivem em `corpus/compatibility/`; `data/` histórico permanece preservado | aceita | impedir mistura/regressão dos artefatos M1/M2 já congelados |
| AD-156 | O formato efetivamente adquirido é autoritativo para o CorpusCase; desvios da curadoria inicial são registrados, não convertidos silenciosamente | aceita | CorpusCase deve representar SourceArtifact/manifestação concreta e auditável |
| AD-157 | Arquivos alternativos recebidos para o mesmo caso permanecem auxiliares até criação explícita de outro CorpusCase | aceita | evitar que uma aquisição incidental altere o tamanho/identidade do corpus |

| AD-158 | M2 Blind Holdout Selection v1 congela quatro casos Tier 1 antes da implementação | aceita | cumprir C12/C15 e preservar teste cego real do pipeline M2 |
| AD-159 | Seleção de holdout usa método determinístico baseado em SHA-256 e somente metadados estruturais; conteúdo selecionado não é inspecionado | aceita | tornar seleção reproduzível sem contaminar o conteúdo |
| AD-160 | SourceArtifact inteiro de cada caso com holdout fica em quarentena até o implementation candidate freeze | aceita | impedir que whole-document processing, unpack ou contexto adjacente revelem o holdout indiretamente |
| AD-161 | Regression Assertions v1 para F1/F2/W1/W2/C1/C2/C3/F-RND/W-RND são congeladas antes do tuning M2 | aceita | impedir moving-target tests e satisfazer o primeiro gate do blind protocol |
| AD-162 | H4 usa Markdown técnico do Rust Book; ausência de novo Markdown narrativo cego é registrada como cobertura não bloqueante | aceita | manter Tier 1 Markdown blind sem reutilizar C2 já conhecido; recomendação de narrativa não é invariant obrigatório |

| AD-163 | CC-08 é substituído explicitamente por eMAG v3.1 oficial em HTML saved-page bundle; support tier passa a Experimental | aceita | o PDF originalmente curado ficou indisponível; eMAG preserva o stress de acessibilidade/documento institucional, e HTML não amplia a claim Tier 1 do M2 |

| AD-164 | CC-15 é adquirido como archive HTML já renderizado da distribuição local stable rust-docs, independente do CC-14 quarantined | aceita | fechar a equivalência Rust source/rendered sem contaminar o blind holdout Markdown |
| AD-165 | Compatibility Corpus v1 é congelado em 30/30; mudanças futuras de membership/manifestação exigem nova versão explícita | aceita | impedir corpus drift durante implementação e preservar reprodutibilidade dos gates M2 |
| AD-166 | Freeze do Compatibility Corpus v1 não revela, desempacota nem altera os SourceArtifacts de holdout CC-05/CC-07/CC-14/CC-18 | aceita | manter validade do blind protocol enquanto o plano e a implementação M2 avançam |
