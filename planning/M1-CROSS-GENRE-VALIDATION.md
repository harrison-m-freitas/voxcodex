# M1 — Validação Cross-Genre do CBM v0.1-alpha

## Estado

**Concluída em 2026-09-10.**

O `CBM v0.1-alpha candidate` foi submetido a três materiais que não participaram do desenho dos golden slices F1/F2/W1/W2. Os três testes resultaram em `PASS_WITH_EXTENSION` e **nenhum exigiu nova primitiva universal do core**.

Os holdouts cegos F-RND (*Fedra*, PDF p.33) e W-RND (Weidman, PDF p.558) permaneceram fechados durante toda esta etapa.

## Protocolo de classificação

Para cada construção encontrada:

1. verificar se as primitivas atuais representam corretamente o fenômeno;
2. se necessário, adicionar apenas `role`, `annotation_type`, `predicate`, Role Profile ou especialização de `StructuredPayload`;
3. classificar como `MODEL_GAP` apenas se o core não possuir capacidade fundamental suficiente;
4. classificar como `MODEL_FAILURE` apenas se uma abstração fundamental se mostrar incorreta.

Resultados possíveis:

- `PASS`;
- `PASS_WITH_EXTENSION`;
- `MODEL_GAP`;
- `MODEL_FAILURE`.

---

# C1 — Leandro Lima, *As Grandes Doutrinas da Graça*, Vols. 1–2

**Fonte:** `data/Leandro Lima - As Grandes Doutrinas da Graça, Vols. 1–2 (Agathos, 2017).pdf`

**Resultado:** `PASS_WITH_EXTENSION`

## Slices

- **C1-A:** PDF pp. 6–7 / páginas impressas 5–6;
- **C1-B:** PDF pp. 38–39 / páginas impressas 37–38.

## Fenômenos validados

- prosa expositiva;
- headings e subdivisões;
- layout em duas colunas;
- continuidade de um mesmo parágrafo entre colunas;
- continuidade entre páginas;
- notas de rodapé simples e complexas;
- referências bíblicas e bibliográficas externas;
- citações diretas;
- listas internas em nota;
- termos em idioma diferente dentro de texto português;
- hifenização causada por layout físico.

## Conclusões

O layout em colunas continua pertencendo à Source Evidence; a ordem lógica é reconstruída no CBM por `order_key` e múltiplos `SourceAnchor`. Uma nota de rodapé é estrutura documental relacionada ao seu marcador e não child de `PhysicalPage`.

A hifenização física pode ser reconstruída no conteúdo canônico desde que a forma física permaneça na Source Evidence e a transformação seja registrada como `Derivation(kind=reconstructed)`.

Referências externas não exigem nova primitiva: mentions permanecem `Annotation`, targets podem ser `Entity`/artefatos externos e a resolução usa `Relation`.

## Extensões incorporadas

Roles:

- `editorial.footnote`;
- `editorial.footnote_marker`;
- `text.list`;
- `text.list_item`.

Annotation types:

- `citation.scripture_reference`;
- `citation.bibliographic_reference`;
- `semantic.quotation`.

Predicate:

- `editorial.refers_to_note`.

Nenhuma primitiva universal foi alterada.

---

# C2 — *Eternally Regressing Knight*

**Fonte principal do teste:** `data/Eternally Regressing Knight - Novel/capitulo_1_ptbr.md`

**Fonte comparativa de apresentação:** `data/Eternally Regressing Knight - Novel/chapter_1_original_en.md`

Os dois arquivos foram tratados como manifestações/fontes distintas; o original inglês não foi usado como substituto silencioso da versão PT-BR.

**Resultado:** `PASS_WITH_EXTENSION`

## Slices conceituais

- **C2-A:** prólogo + início do capítulo, cobrindo narrativa, diálogo, lembrança/flashback e conteúdo citado em verso;
- **C2-B:** trecho posterior do capítulo, cobrindo diálogo alternado, pensamento, interioridade, onomatopeia e atribuição de fala por contexto.

## Fenômenos validados

- narrativa contínua;
- prólogo;
- diálogo sem `SpeakerCue` teatral;
- fala inline dentro de parágrafo;
- speaker inferido e speaker desconhecido;
- alternância de turnos;
- pensamento explicitamente atribuído;
- pensamento marcado apenas por apresentação;
- focalização/interioridade sem marcação explícita;
- flashback e ordem narrativa diferente de cronologia;
- personagens não nomeados e entity resolution contextual;
- separadores/scene breaks;
- canção/verso embutido;
- onomatopeia;
- diferenças editoriais entre manifestação EN e PT-BR.

## Conclusões

`SpeakerCue` é definitivamente uma especialização documental de certos formatos, não requisito para speaker attribution. A relação `narrative.speaker` pode ser inferida a partir de contexto e pode permanecer ausente quando o speaker não é resolvido.

Uma mesma função semântica pode coincidir com um bloco inteiro ou apenas com um span. Quando a fonte apresenta uma fala/pensamento como bloco autônomo, um `DocumentNode` com role especializado é apropriado; quando ocupa somente parte de um parágrafo, usa-se `Annotation` sobre o fragment/span correspondente.

POV, focalização e cronologia são interpretações semânticas e não campos estruturais obrigatórios do `DocumentNode`.

Traduções/manifestações em idiomas diferentes não são fundidas automaticamente num único CBM; alignment de tradução permanece fora do escopo do M1.

## Extensões incorporadas

Roles:

- `narrative.prologue`;
- `narrative.utterance`;
- `narrative.internal_thought`;
- `narrative.scene_break`;
- `narrative.embedded_song`.

Annotation types:

- `narrative.utterance`;
- `narrative.internal_thought`;
- `narrative.point_of_view`;
- `narrative.focalization`;
- `narrative.sound_effect`.

Predicates:

- `narrative.speaker`;
- `narrative.thinker`;
- `semantic.attributed_to`.

Nenhuma primitiva universal foi alterada.

---

# C3 — James Stewart, *Calculus*, 8th ed.

**Fonte:** `data/Calculus 8Ed James Stewart.pdf`

**Resultado:** `PASS_WITH_EXTENSION`

## Slices

- **C3-A:** PDF p.83 / impressa p.51 — texto + fórmulas + definição + figuras/subfiguras;
- **C3-B:** PDF p.87 / impressa p.55 — função definida por casos + limites laterais + gráfico;
- **C3-C1:** PDF p.139 / impressa p.107 — derivação multilinha + equação numerada + Example/Solution + gráficos;
- **C3-C2:** PDF p.145 / impressa p.113 — exercícios, subitens, shared instructions, fórmulas, gráficos e marcadores pedagógicos.

## Fenômenos validados

- matemática inline e display;
- limites, frações, superscripts/subscripts;
- função definida por casos;
- derivação matemática multilinha;
- labels editoriais de equações e referências cruzadas;
- figuras e figuras multipainel;
- gráficos como figures com interpretação derivada separada;
- Definition/Example/Solution;
- exercise sets, exercises e subparts recursivas;
- instrução compartilhada aplicável a múltiplos exercícios;
- marcadores pedagógicos visuais.

## Conclusões

O text layer de PDF matemático não pode ser presumido como representação canônica autoritativa: ele pode perder operadores, scripts, relações bidimensionais ou trocar símbolos enquanto continua aparentemente legível. A reconstrução de matemática deve combinar evidência visual/layout/glifos, possuir provenance explícita e preservar a região fonte.

`FormulaPayload`, antes apenas fronteira mínima, passa a ser uma especialização validada. Ainda não se escolhe uma AST matemática universal; o payload preserva representações da fonte e pode referenciar representações reconstruídas qualificadas por provenance/confidence.

Conteúdo matemático inline confirmou que `ContentFragment` e child `DocumentNode` embutido precisam participar do mesmo espaço lógico de ordenação dentro do parent. Essa regra foi incorporada como S51.

Figuras multipainel são representáveis como `structured.figure` com children `structured.figure_panel`, cada qual endereçável e ancorável. Interpretação de gráfico continua derivada, não caption nem conteúdo autoral.

Estruturas pedagógicas usam roles e relações; não criam primitivas universais.

## Extensões incorporadas

Roles:

- `math.expression`;
- `math.derivation`;
- `structured.figure_panel`;
- `pedagogy.definition`;
- `pedagogy.example`;
- `pedagogy.problem_statement`;
- `pedagogy.solution`;
- `pedagogy.exercise_set`;
- `pedagogy.exercise`;
- `pedagogy.exercise_part`;
- `pedagogy.shared_instruction`;
- `pedagogy.tool_marker`.

Predicates:

- `pedagogy.applies_to`;
- `math.transforms_to` — disponível somente quando a transformação matemática for efetivamente analisada/derivada; não é presumida pela simples proximidade visual.

Labels editoriais como número de equação/figura permanecem distintos da identidade canônica e usam o mecanismo geral de referência (`semantic.reference_mention` + `document.refers_to`).

## FormulaPayload refinado

```yaml
FormulaPayload:
  id:
  source_representation_refs: []
  reconstructed_representation_refs: []
  fidelity_constraints: []
```

Regras:

- representação efetivamente presente na fonte pode ser preservada em `source_representation_refs`;
- representação reconstruída exige provenance explícita e, quando aplicável, confidence;
- reconstrução nunca é promovida silenciosamente a representação original;
- tecnologia/AST matemática concreta permanece decisão posterior.

Nenhuma primitiva universal foi alterada.

---

# Resultado consolidado

| Slice/corpus | Resultado | Mudança no core universal |
|---|---|---|
| C1 — teologia/prosa expositiva | `PASS_WITH_EXTENSION` | nenhuma |
| C2 — webnovel/narrativa | `PASS_WITH_EXTENSION` | nenhuma |
| C3 — matemática/textbook | `PASS_WITH_EXTENSION` | nenhuma |

A validação cross-genre confirmou o padrão arquitetural:

```text
core estável
+
roles / Role Profiles
+
annotations / relations
+
StructuredPayload especializado quando topologia exige
```

## Gate resultante

O `CBM v0.1-alpha candidate` está **cross-genre validated** após incorporação das extensões acima.

O próximo gate é uma revisão curta de freeze/promoção para `CBM v0.1 candidate`. Somente após esse freeze os holdouts cegos F-RND e W-RND podem ser abertos.

## Holdouts

Continuam fechados e não foram consultados nesta validação:

- F-RND — *Fedra*, PDF p.33;
- W-RND — Weidman, PDF p.558.


---

## Pós-validação: freeze

Em 2026-09-11 o contrato cross-genre validated passou por review final e foi congelado como `CBM v0.1 candidate` (`schema_version=0.1-candidate`). Esse candidate foi posteriormente aprovado nos holdouts e promovido; a baseline normativa corrente está em `architecture/CBM-V0.1.md`. Este relatório preserva a evidência cross-genre que sustentou o freeze e a promoção.
