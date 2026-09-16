# M1 — Canonical Representation

## Objetivo

Provar, antes de qualquer automação, que o modelo canônico do VoxCodex consegue representar fielmente trechos reais e heterogêneos das duas obras do PoC, preservando estrutura, conteúdo, evidência de origem e espaço para derivações futuras.

O M1 não seleciona stack definitiva e não implementa parser, LLM, TTS, banco ou workflow.

## Definition of Done

O M1 estará concluído quando, para qualquer elemento das amostras de conformidade, for possível responder sem ambiguidade:

1. o que o elemento é;
2. onde ele está na fonte;
3. a que estrutura lógica pertence;
4. quem fala, quando aplicável;
5. qual conteúdo precisa permanecer literal ou textual;
6. qual política de fidelidade se aplica;
7. como uma camada de narração poderá tratá-lo;
8. qual é sua origem editorial observável;
9. quais relações possui com outros elementos;
10. como qualquer transformação posterior será rastreada até a evidência de fonte.

## Corpus de conformidade

O M1 usa quatro amostras conhecidas, uma etapa de validação cross-genre e duas amostras holdout cegas.

| ID | Obra | Amostra | Finalidade | Estado |
|---|---|---|---|---|
| F1 | *Fedra* | PDF p. 6 — Ato I, Cena I | ato, cena, participantes, speaker cue, speech, verso | analisado |
| F2 | *Fedra* | PDFs p. 10–11 — transições entre cenas | fronteiras estruturais e continuidade | analisado |
| F-RND | *Fedra* | PDF p. 33 | holdout cego / surpresa | **PASS — aberto somente após freeze** |
| W1 | Weidman | PDF p. 112 — trecho técnico | listagem, terminal, prosa, código, nota, comando | analisado |
| W2 | Weidman | PDF p. 96 — tabela e chmod | tabela, referência visual, dados estruturados, literal técnico | analisado |
| W-RND | Weidman | PDF p. 558 | holdout cego / surpresa | **PASS_WITH_EXTENSION — aberto somente após freeze** |

### Regra do holdout

F-RND e W-RND foram escolhidas antes do freeze do CBM e não devem ser analisadas para influenciar o schema. Depois do `CBM v0.1 candidate`, serão abertas e classificadas como:

- `PASS`: representável naturalmente;
- `PASS_WITH_EXTENSION`: exige apenas extensão prevista, sem alterar o núcleo;
- `MODEL_GAP`: revela deficiência do modelo que exige alteração do CBM;
- `MODEL_FAILURE`: abstração fundamental não representa corretamente o conteúdo.

## Validação cross-genre

Depois de W1/W2 será consolidado um `CBM v0.1-alpha`. Antes de abrir F-RND e W-RND, esse modelo será testado contra materiais que não participaram de seu desenho:

- 1–2 páginas de pelo menos um romance adicional;
- 1–2 páginas de outro livro/documento técnico, se disponível;
- um capítulo ou trecho substancial de webnovel.

Essa etapa responde a uma pergunta diferente dos holdouts: **o modelo generaliza entre gêneros e formatos?** Os holdouts, por sua vez, testam conteúdo inesperado dentro das próprias obras-base.

Regra: estruturas específicas encontradas em *Fedra* ou Weidman não são promovidas automaticamente ao núcleo do CBM. Primeiro devem ser classificadas como primitiva universal, role/anotação, especialização de gênero/formato ou artefato apenas de fonte.

## Fontes fixadas para o PoC

### Fedra

- Arquivo: `data/Fedra - Jean Racine - 2013.pdf`
- Título: *Fedra*
- Autor: Jean Racine
- Título original: *Phèdre* (1677)
- Tradução: Sebastião Francisco de Mendo Trigoso (1773–1821)
- Edição: Centaur Editions, 2013
- Páginas PDF: 69
- SHA-256: `ec048480453a3e04d54188d06fac15b55dea8270f7f971acf2d0bbcfd6c5ef59`

### Testes de Invasão

- Arquivo: `data/Testes de Invas#U00e3o Uma introdu#U00e7#U00e3o pr#U00e1tica ao hacking (Weidman, G.).pdf`
- Título: *Testes de Invasão: Uma introdução prática ao hacking*
- Autora: Georgia Weidman
- Título original: *Penetration Testing: A Hands-On Introduction to Hacking*
- Tradução: Lúcia A. Kinoshita
- Edição em português: Novatec Editora Ltda., 2014
- ISBN: 978-85-7522-558-5
- Páginas PDF: 575
- SHA-256: `db06828cb749082e0885060f2a3ff23ee8a175b78f7d6dfefe184bb172b735bd`

A unidade de fidelidade do VoxCodex é a edição/fonte ingerida, não uma abstração histórica da obra.

---

# M1.1 — F1: Fedra, PDF p. 6

## Estado

**Concluído e aprovado em 2026-09-09.**

## Inventário observado

A página inicia formalmente a peça com:

```text
ATO PRIMEIRO
  CENA I
    HIPÓLITO, TERAMENE

    HIPÓLITO
      [7 versos]

    TERAMENE
      [14 versos]

    HIPÓLITO
      [4 versos visíveis nesta página]
      [...a fala continua na página seguinte]
```

Identificadores de observação usados apenas durante a descoberta:

| ID | Evidência | Papel observado |
|---|---|---|
| F1-O01 | `ATO PRIMEIRO` | marcador estrutural de ato |
| F1-O02 | `CENA I` | marcador estrutural de cena |
| F1-O03 | `HIPÓLITO, TERAMENE` | declaração explícita dos participantes da cena |
| F1-O04 | `HIPÓLITO` | speaker cue explícito |
| F1-O05 | sete linhas poéticas | primeira fala de Hipólito |
| F1-O06 | `TERAMENE` | speaker cue explícito |
| F1-O07 | quatorze linhas poéticas | fala de Teramene |
| F1-O08 | `HIPÓLITO` | novo speaker cue explícito |
| F1-O09 | quatro linhas poéticas visíveis | início de nova fala de Hipólito |
| F1-O10 | fim físico da página | interrupção física, não semântica |

## Descobertas arquiteturais

### 1. Estrutura lógica e estrutura física são topologias diferentes

Uma fala pode atravessar páginas. Portanto, `PhysicalPage` não deve ser pai lógico de `Speech`, `Paragraph`, `VerseLine` ou equivalentes. A estrutura lógica aponta para a estrutura física por `SourceAnchor`.

### 2. Character, SpeakerCue e Speech são conceitos distintos

- `Character`: entidade semântica persistente;
- `SpeakerCue`: evidência textual impressa que identifica o locutor;
- `Speech`: unidade lógica de fala.

Atribuição de speaker baseada em cue explícito deve poder carregar evidência forte e rastreável.

### 3. Declaração de participantes não é inferência de presença

`HIPÓLITO, TERAMENE` é informação explicitamente declarada pela edição. Inferências futuras de entrada, saída ou presença em cena não podem sobrescrever essa evidência.

### 4. VerseLine precisa sobreviver como unidade literária

A lineação poética pertence à forma da edição. Ela não deve ser achatada para um parágrafo único, mesmo que a futura síntese de voz não faça pausa em cada verso.

### 5. VerseLine não equivale a Sentence

Estrutura poética e estrutura linguística podem se sobrepor de maneiras diferentes. Sentenças, cláusulas e spans devem poder existir como anotações/segmentações independentes da árvore literária.

### 6. Relações semânticas inferidas não são fatos da fonte

Exemplo: uma relação `interrupts` entre duas falas pode ser fortemente inferível pelo texto e pela pontuação, mas continua sendo inferência, não evidência impressa explícita.

### 7. A forma superficial da edição deve permanecer recuperável

Grafias, pontuação e formas históricas da edição não podem ser silenciosamente modernizadas. Qualquer `normalized_text` futuro é derivado de `source_surface_text` e não o substitui.

### 8. A origem segura no nível do trecho é SOURCE_EDITION

Não se deve inferir autoria granular de pontuação, capitalização, cabeçalhos ou decisões editoriais quando a edição não permite demonstrá-la. Autor, tradutor e editor pertencem ao provenance/metadata da edição; atribuições granulares só devem ocorrer com evidência suficiente.

### 9. A decisão concreta de narração não pertence ao CBM

O CBM registra o que o elemento é. O Narration Model/perfil decide como representá-lo em áudio. Exemplo: um `SpeakerCue` pode ser lido por um narrador único e omitido em uma dramatização multi-voz sem que o conteúdo canônico mude.

## Sete invariantes aprovados

**M1-I01 — Page boundary ≠ semantic boundary**  
Fronteiras físicas da fonte não criam automaticamente fronteiras semânticas no CBM.

**M1-I02 — Source surface preservation**  
O texto superficial da fonte deve permanecer recuperável mesmo quando houver normalização posterior.

**M1-I03 — Speaker separation**  
`SpeakerCue`, `Character` e `Speech` são conceitos diferentes e não devem ser colapsados.

**M1-I04 — Evidence ≠ inference**  
Informação explicitamente declarada pela fonte e informação inferida semanticamente devem permanecer distinguíveis.

**M1-I05 — VerseLine identity**  
`VerseLine` possui identidade literária própria e não deve ser tratado como sinônimo de `Sentence`.

**M1-I06 — Narration outside CBM**  
Decisões concretas de apresentação sonora pertencem ao Narration Model/perfil, não ao CBM.

**M1-I07 — Faithful authored-text fidelity**  
No modo Fiel, texto autoral/editorial narrável exige `textual_exact` como política padrão independentemente do gênero: preservar palavras, ordem textual e conteúdo linguístico da edição; alterações textuais exigem transformação explícita e rastreável.

## Direção conceitual após F1

F1 aponta para três mecanismos complementares:

```text
Árvore documental/literária
    Act → Scene → Speech → VerseLine

Grafo semântico
    Character → speaker_of → Speech
    Scene → declares_participant → Character
    EntityMention → refers_to → Entity

Source Anchors
    Canonical node/span → SourceArtifact / PhysicalPage / Region / Range
```

Nenhum desses mecanismos substitui os outros.

## Conceitos cuja necessidade foi demonstrada por F1

- Work
- Edition
- SourceArtifact
- PhysicalPage
- Act
- Scene
- SceneParticipantDeclaration
- Character
- CharacterReference
- SpeakerCue
- Speech
- VerseLine
- TextSpan / surface text
- EntityMention
- SemanticRelation
- SourceAnchor
- Confidence
- Provenance

Esta lista é um inventário de conceitos, **não uma decisão de criar uma classe para cada item**.

## Impacto na Fidelity Policy

A tabela inicial `prosa/dialogue → semantic_exact` é insuficiente para literatura no modo Fiel.

Direção aprovada:

| Conteúdo | Política |
|---|---|
| prosa literária / diálogo / verso | `textual_exact` |
| código / comandos / URLs / IPs | `literal_exact` |
| matemática | `symbolic_exact` |
| estrutura editorial recorrente | `structural` |
| ativos visuais | `referenced_asset` |

`semantic_exact` pode continuar existindo para transformações em que equivalência semântica seja realmente aceitável, mas não é suficiente como política primária da obra literária no modo Fiel.

## Próxima ação após F1 — concluída

Executar **M1.1 — F2**, usando as páginas 10–11 de *Fedra* para testar:

- fronteira entre cenas;
- continuidade estrutural;
- participantes por cena;
- mudanças de locutor;
- diferença entre informação explícita da edição e inferências de entrada/saída;
- capacidade dos invariantes de F1 de sobreviver a uma transição dramática real.

Esta ação foi concluída em F2; a consolidação mostrou que a taxonomia dramática deve permanecer como especialização, não como núcleo universal.

---

# M1.1 — F2: Fedra, PDFs p. 10–11

## Estado

**Concluído e aprovado em 2026-09-09.**

## Inventário observado

F2 cobre três cenas do Ato I e duas continuidades cross-page:

- a página 10 começa no meio de uma fala de Teramene cujo speaker cue está na página 9;
- a Cena I termina na página 10;
- `CENA II` declara `HIPÓLITO, ENONE, TERAMENE`;
- uma fala de Enone começa na página 10 e continua na página 11;
- `CENA III` declara `FEDRA, ENONE`;
- uma fala de Enone começa na página 11 e continua na página 12.

A inspeção das páginas 9 e 12 foi limitada às bordas necessárias para confirmar essas continuidades. Os holdouts F-RND p.33 e W-RND p.558 permaneceram fechados.

## Descobertas

### Continuidade estrutural atravessa limites operacionais

Uma página pode começar sem speaker cue ou marcador estrutural suficiente para interpretar corretamente seu primeiro conteúdo. Portanto, o futuro reconstrutor precisa transportar contexto/estado estrutural aberto ou reconciliar fronteiras posteriormente.

### Declarações estruturais não são eventos

A mudança de `HIPÓLITO, ENONE, TERAMENE` para `FEDRA, ENONE` fornece evidência estrutural de composição de cena, mas não autoriza fabricar direções como `[Teramene sai.]`. Entrada/saída são derivações semânticas separadas e devem manter provenance/confidence.

### Função documental e implicação semântica são ortogonais

A fala de Enone contém `Ela chega.`. O trecho pode implicar a entrada de Fedra, mas continua sendo fala de Enone. Uma eventual representação de `Fedra enters` é derivada e não substitui o papel documental do verso.

## Invariantes aprovados em F2

**M1-I08 — Structural continuity across processing boundaries**  
Fronteiras operacionais de página, chunk, batch ou worker não encerram implicitamente unidades lógicas. Estado aberto deve ser preservado ou reconciliado.

**M1-I09 — Declared state ≠ inferred transition**  
Estado/composição declarados explicitamente pela fonte não equivalem automaticamente a eventos temporais ou causais inferidos.

**M1-I10 — Canonical role ≠ semantic implication**  
O papel documental original de um trecho não muda por causa de uma ação, referência ou evento que seu conteúdo possa implicar.

## Correção cross-genre aprovada após F2

**M1-I11 — Genre specialization must not contaminate the canonical core**  
Estruturas específicas de gênero/formato devem permanecer especializações, roles ou extensões sobre primitivas canônicas mais gerais. Elas não podem tornar-se requisitos universais do núcleo apenas por terem aparecido no corpus-base.

Consequência imediata: `SceneParticipantDeclaration` é uma necessidade confirmada para *Fedra*, mas não é considerada primitiva universal. Seu mecanismo físico permanece em aberto até a validação cross-genre.

## Estado acumulado dos invariantes

Os invariantes M1-I01 a M1-I11 estão **aprovados**. Nenhum dos sete invariantes de F1 foi revogado por F2.

## Próxima ação após F2 — concluída

W1 e W2 foram executados e aprovados. As descobertas estão registradas abaixo.
---

# M1.1 — W1: Weidman, PDF p. 112

## Estado

**Concluído e aprovado em 2026-09-09.**

Foram consultadas apenas as páginas adjacentes necessárias para confirmar contexto e limites. W-RND p.558 permaneceu fechado.

## Inventário observado

W1 contém, na mesma página:

- running header e fólio impresso;
- `Listagem 3.1` com caption;
- transcrição de terminal com prompt, comando digitado, saída, `^C` e estatísticas;
- prosa técnica;
- heading `Script Bash simples`;
- código-fonte Bash;
- nota/admonition da própria edição;
- comando `chmod 744 pingscript.sh`;
- referência cruzada para `listagem 3.1` na página anterior.

## Descobertas

### Função editorial e natureza do conteúdo são ortogonais

`Listing` não é sinônimo de `CodeBlock` ou `TerminalTranscript`. Uma listagem é um artefato editorial rotulado que pode conter diferentes naturezas de conteúdo.

### Source presentation pode ser evidência

A própria obra instrui o leitor a digitar o código em negrito, e o PDF diferencia prompt e entrada digitada por spans/fontes. Tipografia/layout devem poder sobreviver na Source Evidence quando semanticamente relevantes.

### Running header não recria Chapter

`Capítulo 3 ■ Programação` no topo é elemento recorrente de página, não uma nova instância lógica de capítulo.

### Fidelidade precisa ser local

Um parágrafo `textual_exact` pode conter `Ctrl-C`, IP, comando ou outro span que exija `literal_exact`.

### Conteúdo literal continua estruturável

Uma transcrição de terminal pode preservar literalmente a superfície e ainda distinguir prompt, input, output e controles; código pode preservar linhas/whitespace e continuar semanticamente analisável.

## Revisão aprovada de M1-I07

**M1-I07 — Faithful authored-text fidelity**  
No modo Fiel, `textual_exact` é a política padrão para texto autoral/editorial narrável independentemente do gênero. Conteúdo localmente mais sensível pode exigir políticas mais rígidas.

## Invariantes aprovados em W1

**M1-I12 — Source presentation may carry semantic evidence**  
Tipografia, layout, ênfase, posicionamento e propriedades visuais devem permanecer disponíveis quando puderem servir como evidência semântica; a semântica derivada permanece separada dessas propriedades físicas.

**M1-I13 — Physical recurrence ≠ logical duplication**  
Elementos repetidos por paginação/projeto editorial não criam automaticamente novas unidades na estrutura lógica.

**M1-I14 — Fidelity is locally refinable**  
Uma unidade pode possuir política de fidelidade padrão e conter spans/subunidades com políticas mais rigorosas.

**M1-I15 — Literal fidelity ≠ semantic flattening**  
Preservação literal é compatível com estrutura interna; código, terminal e outros conteúdos não devem ser achatados em strings opacas.

## Requisitos de contrato revelados por W1

- `PhysicalPage` distingue índice físico da fonte e fólio/rótulo impresso;
- cross-reference separa menção textual de target/resolução;
- nota/admonition da fonte permanece distinta de conteúdo auxiliar gerado pelo VoxCodex;
- `TerminalTranscript` e `CodeBlock` são naturezas diferentes de conteúdo;
- roles internos como prompt/input/output podem ser annotations/subestruturas, sem necessidade de se tornarem primitivas universais.

---

# M1.1 — W2: Weidman, PDF p. 96 / página impressa 97

## Estado

**Concluído e aprovado em 2026-09-09.**

Foi consultada apenas a página anterior necessária para confirmar a continuidade da seção `Permissões de arquivo`. W-RND p.558 permaneceu fechado.

## Inventário observado

W2 contém:

- running header e fólio;
- continuação de seção cross-page;
- referência textual à `tabela 2.1`;
- `Tabela 2.1 – Permissões para os arquivos no Linux`;
- três colunas e oito linhas de dados;
- valores binários como `011`, `010`, `001`;
- prosa explicativa com `chmod 700`;
- transcrição de terminal com comandos e saída;
- marcador editorial `❶` intercalado na saída monoespaçada e sua contraparte explicativa no parágrafo seguinte.

## Descobertas

### Tabela canônica não pode ser texto linear

O significado depende das relações entre linhas, colunas, cabeçalhos e células. A representação canônica deve preservar a topologia bidimensional. A verbalização futura pertence ao Narration Model.

### Lexema superficial e valor interpretado coexistem

`011` deve permanecer `011`; uma interpretação como valor binário 3/bit-width 3 é derivada e não substitui a forma da edição. O mesmo princípio vale para `700`, zeros à esquerda e outras notações.

### Callout editorial pode estar dentro de conteúdo literal visualmente

O `❶` usa fonte distinta e é anotação editorial, não saída produzida pelo terminal. Uma linha visual pode combinar spans com origens/funções diferentes.

### Fidelidade possui múltiplas granularidades

Uma tabela pode exigir constraints estruturais, enquanto células textuais usam `textual_exact` e células técnicas como `011` usam `literal_exact`. Isso deixa aberta a possibilidade de Fidelity Policy tornar-se um conjunto de constraints ortogonais em vez de um único enum.

## Invariantes aprovados em W2

**M1-I16 — Structural fidelity of structured data**  
Conteúdo cujo significado depende de relações estruturais preserva essas relações no CBM; linearização textual não substitui a estrutura original.

**M1-I17 — Surface representation ≠ interpreted value**  
A representação superficial de valores permanece preservada independentemente de parsing, normalização ou interpretação tipada posterior.

**M1-I18 — Visual adjacency ≠ common semantic origin**  
Elementos visualmente adjacentes/intercalados podem possuir origens e papéis semânticos diferentes e devem continuar distinguíveis quando isso for relevante.

## Estado acumulado após os quatro golden slices

Os invariantes **M1-I01 a M1-I18 estão aprovados**. F1/F2/W1/W2 estão concluídos. Nenhum holdout foi aberto.

## Próxima ação

1. consolidar as evidências dos quatro slices em **`CBM v0.1-alpha`**;
2. definir o schema conceitual mínimo do core, Source Evidence, SourceAnchor, fidelity, relationships e specializations;
3. executar validação cross-genre com romance(s), webnovel e outro material técnico quando disponível;
4. revisar o alpha e promover para `CBM v0.1 candidate` apenas se a validação cross-genre for satisfatória;
5. somente então abrir F-RND p.33 e W-RND p.558.

---

# M1.2 — Consolidação do CBM v0.1-alpha

## Estado histórico pré-freeze

**Seções 1–7 aprovadas e consolidadas em 2026-09-10.**

Contrato normativo:

`architecture/CBM-V0.1-ALPHA.md`

Estado do schema:

```text
CBM v0.1-alpha candidate
```

Este era o estado pré-freeze. O candidate congelado está preservado em `architecture/CBM-V0.1-CANDIDATE.md`; após holdouts e promotion review, a baseline corrente passou a `architecture/CBM-V0.1.md`.

## Decisões consolidadas

### Fronteira do CBM

O CBM contém estrutura/conteúdo canônicos e mecanismo para anexar conhecimento semântico qualificado. Inferências nunca sobrescrevem conteúdo canônico.

```text
Source Evidence
    ↓ SourceAnchor
CBM
    ↓
Narration / Performance / Audio
```

Source Evidence e Narration Model permanecem fora do CBM.

### Núcleo composicional

Direção escolhida:

```text
DocumentNode
+ ContentFragment
+ role namespaced
+ Entity
+ Annotation
+ Relation
+ optional StructuredPayload
+ SourceAnchor
+ FidelityConstraint
+ Provenance
```

`node_class` é pequeno/controlado; `role` é extensível.

### SpeakerCue

Decisão específica aprovada:

```text
Scene
├── SpeakerCue
└── Speech
```

`SpeakerCue` é sibling de `Speech`, ligado por `document.introduces`; Character/SpeakerCue/Speech permanecem distintos.

### SourceAnchor

Aprovado:

- SourceArtifact imutável/checksummed;
- `source_page_index` separado de `printed_page_label`;
- region canônica normalizada;
- ranges relativos a evidência identificada;
- múltiplos anchors;
- SourceAnchor localiza, mas não implica autoria/semântica.

### Fidelity

Aprovada modelagem por constraints ortogonais:

- `lexical`;
- `character`;
- `structure`;
- `symbolic`;
- `ordering`.

Requirement inicial: `preserve_exactly`.

`textual_exact`/`literal_exact` tornam-se perfis/aliases convenientes.

### Semântica

Aprovados:

- Entity fora da árvore;
- EntityMention como Annotation;
- Annotation e Relation namespaced;
- status epistemológicos `explicit`, `derived`, `inferred`, `human_asserted`;
- cross-reference = mention + relation resolvida;
- semantic events ficam como annotations no alpha;
- relations inversas são derivadas por padrão.

### Structured payloads

Regra:

1. usar node + fragments;
2. usar children quando necessário;
3. usar StructuredPayload apenas quando 1+2 não preservarem topologia.

`TablePayload` preserva topologia tabular. Após C3, `FormulaPayload` foi refinado e validado; figures multipainel foram validadas por `structured.figure_panel`.

### Provenance

Lineage consolidado:

```text
ProcessingActivity
        ↓
Derivation
```

O mesmo mecanismo cobre parser determinístico, OCR, LLM, humano e migração.

### Revisions

Aprovado:

```text
CanonicalDocument
└── CanonicalRevision*
```

- frozen é imutável;
- correção/reprocessamento cria nova revision;
- contrato permite DAG;
- implementação inicial será linear;
- objetos imutáveis podem ser reutilizados em várias revisions;
- active revision deve ser frozen;
- downstream deve registrar a revision consumida.

## Invariantes de schema

No alpha foram definidos **S01–S51**; o freeze review consolidou **S01–S56**, cobrindo:

- árvore/conteúdo;
- SourceAnchor;
- fidelity;
- provenance;
- semântica;
- payloads/extensões;
- revisions/lifecycle.

A lista normativa usada no freeze está em `architecture/CBM-V0.1-CANDIDATE.md` (S01–S56); a baseline promovida, com os mesmos invariantes, está em `architecture/CBM-V0.1.md`.

## Questões do alpha e resolução no freeze

Resolvidas no freeze: ownership de ContentFragment em StructuredPayload, `DocumentNode.status`, autoridade de `schema_version`, authority do SemanticRegistry e policy de validation report.

Permanecem deliberadamente adiadas: serialização física, algoritmo de digest/canonical serialization, governança física de Role Profiles, representação matemática estruturada concreta/AST e confidence calibration.

## Gate cross-genre — concluído

C1–C3 foram concluídos com `PASS_WITH_EXTENSION`, sem `MODEL_GAP`, `MODEL_FAILURE` ou mudança em primitivas universais. O freeze review subsequente passou; o próximo gate é blind holdout conformance.



---

## Validação cross-genre C1–C3 — concluída

- **C1 — Leandro Lima:** `PASS_WITH_EXTENSION`;
- **C2 — *Eternally Regressing Knight*:** `PASS_WITH_EXTENSION`;
- **C3 — James Stewart, *Calculus*:** `PASS_WITH_EXTENSION`.

Resultado agregado: novas primitivas universais = **0**; `MODEL_GAP` = **0**; `MODEL_FAILURE` = **0**.

C1 incorporou footnotes, listas e referências/citações externas. C2 incorporou vocabulário narrativo e confirmou speaker/thinker por Relation sem dependência de `SpeakerCue`. C3 refinou/validou `FormulaPayload`, `structured.figure_panel`, estruturas pedagógicas e mixed-content ordering (S51).

Registro detalhado: `M1-CROSS-GENRE-VALIDATION.md`.

### Próximo gate

O `CBM v0.1 candidate` foi congelado em 2026-09-11. F-RND p.33 e W-RND p.558 permaneceram fechados durante C1–C3 e o freeze review e agora podem ser abertos exclusivamente para blind conformance.


---

## M1.3 — Freeze review do CBM v0.1 candidate

**Data:** 2026-09-11  
**Resultado:** `PASS`  
**Contrato congelado:** `architecture/CBM-V0.1-CANDIDATE.md`  
**Review:** `planning/M1-CBM-FREEZE-REVIEW.md`

Blockers normativos resolvidos antes do freeze:

- ownership de fragments em StructuredPayload definido como não-owning para payload components;
- `DocumentNode.status` removido;
- `schema_version` concentrado em `CanonicalRevision`;
- `SemanticRegistry` definido como autoridade para membership semântico;
- lifecycle administrativo separado da imutabilidade do payload/digest;
- `ValidationReport` passa a referenciar explicitamente a ValidationPolicy.

Schema invariants: **S01–S56**.

F-RND p.33 e W-RND p.558 permaneceram fechados durante o review e agora estão liberados exclusivamente para blind conformance. O candidate congelado não pode ser alterado para acomodar o resultado; qualquer mudança normativa gera novo candidate/versionamento.

---

# M1.4 — Blind Holdout Conformance

## Estado

**Concluído em 2026-09-11.**

O `CBM v0.1 candidate` permaneceu congelado durante todo o teste. Foram abertas exclusivamente F-RND p.33 e W-RND p.558; nenhuma página adjacente foi consultada.

Resultados:

- F-RND — `PASS`;
- W-RND — `PASS_WITH_EXTENSION`;
- universal core changes — 0;
- schema invariant changes — 0;
- `MODEL_GAP` — 0;
- `MODEL_FAILURE` — 0.

W-RND observou duas extensões namespaced compatíveis com o contrato já congelado: `technical.terminal_input` e `editorial.omission_marker`.

Relatório detalhado: `M1-HOLDOUT-CONFORMANCE.md`.  
Manifest auditável: `../HOLDOUT-CONFORMANCE-MANIFEST.json`.

O SHA-256 de `architecture/CBM-V0.1-CANDIDATE.md` após os holdouts continua `22392650f6a63531bb7cb034c55c68e612970df13557747787050f84269aed58`, idêntico ao freeze.

## Próximo gate

Promotion review concluído com `PASS`; ver seção M1.5 abaixo.

---

# M1.5 — Promotion Review e encerramento

**Data:** 2026-09-11  
**Resultado:** `PASS`  
**Contrato promovido:** `architecture/CBM-V0.1.md` (`schema_version=0.1`)

Critérios concluídos:

- candidate permaneceu byte-for-byte igual ao freeze durante os holdouts;
- F1/F2/W1/W2 aprovados;
- C1/C2/C3 sem `MODEL_GAP`/`MODEL_FAILURE`;
- F-RND=`PASS`;
- W-RND=`PASS_WITH_EXTENSION`;
- zero mudanças em primitivas universais/invariantes após freeze;
- extensões de W-RND cabem no mecanismo de roles namespaced já congelado.

Extensões promovidas ao vocabulário comprovado:

- `technical.terminal_input`;
- `editorial.omission_marker`.

Invariantes finais do milestone: **M1-I01–M1-I18 + S01–S56**.

O M1 — Canonical Representation está **CONCLUÍDO**. Review detalhado: `M1-PROMOTION-REVIEW.md`. O próximo passo é definir formalmente o próximo milestone usando `CBM v0.1` como baseline.
