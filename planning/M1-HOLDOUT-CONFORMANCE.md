# M1 — Blind Holdout Conformance

## Estado

**Concluído em 2026-09-11 contra o `CBM v0.1 candidate` congelado.**

Contrato testado: `architecture/CBM-V0.1-CANDIDATE.md`  
SHA-256 congelado: `22392650f6a63531bb7cb034c55c68e612970df13557747787050f84269aed58`

Os únicos holdouts revelados foram os previamente reservados:

- **F-RND** — *Fedra*, PDF p.33;
- **W-RND** — Weidman, PDF p.558 / fólio impresso 559.

Nenhuma página adjacente foi aberta para resolver contexto. O teste foi executado contra o candidate congelado; `architecture/CBM-V0.1-CANDIDATE.md` não foi editado.

## Critérios

- `PASS` — representável naturalmente pelo candidate congelado;
- `PASS_WITH_EXTENSION` — exige apenas role/annotation/predicate namespaced ou especialização prevista, sem mudar primitivas/invariantes do core;
- `MODEL_GAP` — exige mudança normativa no CBM;
- `MODEL_FAILURE` — abstração fundamental não representa corretamente o material.

## Resultado executivo

| Holdout | Resultado | Core change | Model gap | Model failure |
|---|---|---:|---:|---:|
| F-RND — *Fedra* p.33 | **PASS** | 0 | 0 | 0 |
| W-RND — Weidman p.558 | **PASS_WITH_EXTENSION** | 0 | 0 | 0 |

**Resultado global:** blind conformance aprovado. O candidate congelado é elegível para promotion review de `CBM v0.1`.

---

# F-RND — *Fedra*, PDF p.33

## Inventário observado

A página contém, nesta ordem lógica:

1. continuação de uma fala em verso que começou antes da página;
2. `ENONE` como speaker cue explícito, seguido por três versos;
3. marcador estrutural `CENA VI`;
4. declaração explícita de participantes `HIPÓLITO, TERAMENE`;
5. `TERAMENE` como speaker cue, seguido por três versos;
6. `HIPÓLITO` como speaker cue, seguido por um verso no fim da página, com possibilidade de continuidade posterior.

A página contém também frases cujo significado pode sugerir movimentação cênica, mas elas continuam documentalmente sendo fala.

## Conformance

### Continuidade de fala sem speaker cue local

A página começa no meio de uma unidade lógica. O speaker cue não está presente no holdout revelado e não foi buscado em página adjacente.

Isso é representável pelo candidate porque:

- `PhysicalPage` não é parent lógico;
- `Speech` pode atravessar páginas e possuir múltiplos `SourceAnchor`s;
- estado estrutural aberto pode ser carregado/reconciliado entre chunks;
- ausência de evidência local não autoriza fabricar speaker.

**Valida:** M1-I01, M1-I08, S02, S13.

### SpeakerCue, Speech e Character permanecem distintos

`ENONE`, `TERAMENE` e `HIPÓLITO` são evidências de `drama.speaker_cue`; as falas correspondentes são `drama.speech`, e personagens continuam em `Entity`/relations.

A decisão congelada `SpeakerCue` sibling de `Speech` representa a página sem adaptação especial.

**Valida:** M1-I03, AD-048.

### Transição para Cena VI

`CENA VI` é `drama.scene`; `HIPÓLITO, TERAMENE` é `drama.participant_declaration`. Não é necessário fabricar eventos de entrada/saída para explicar a mudança.

**Valida:** M1-I09, M1-I11.

### Implicação semântica não altera papel documental

Falas como a de Enone sobre chegada de pessoas e a pergunta de Teramene sobre Fedra podem sustentar futuras inferências de eventos, mas permanecem `Speech`/`VerseLine` no canônico.

**Valida:** M1-I10, S09.

### VerseLine

A lineação poética continua sendo estrutural e endereçável independentemente de sentence segmentation.

**Valida:** M1-I05.

## Classificação

**F-RND = PASS.**

Nenhum role novo, payload novo, predicate novo ou mudança normativa é necessário.

---

# W-RND — Weidman, PDF p.558 / fólio 559

## Inventário observado

A página contém:

1. running header `Capítulo 20 ...` e fólio `559`;
2. continuação de parágrafo iniciado anteriormente;
3. referência textual à `listagem 20.15`;
4. caption `Listagem 20.15 – Configurando as opções`;
5. transcript/interação literal com prompts, valores digitados, valores ecoados e confirmação `y`;
6. marcador editorial `--trecho omitido--` dentro da listagem;
7. prosa técnica com termos/identificadores como APKTool, APK, Android SDK e Master Key;
8. `y` inline em estilo monoespaçado/negrito dentro de prosa;
9. `NOTA` editorial contendo URL externa.

A Source Evidence mostra contraste tipográfico relevante: os primeiros valores fornecidos pelo usuário e a resposta final `y` aparecem em negrito monoespaçado, enquanto valores posteriormente ecoados aparecem em monoespaçado regular; `trecho omitido` aparece em itálico.

## Conformance

### Running header e fólio

São recorrência física/editorial, não nova instância lógica de Chapter. O fólio impresso é distinto do índice físico da fonte.

**Valida:** M1-I13, S12.

### Continuação cross-page

O primeiro parágrafo começa antes da página. O candidate suporta continuidade estrutural sem usar a página como parent ou boundary semântico.

**Valida:** M1-I01, M1-I08.

### Listing permanece função editorial

`technical.listing` contém uma interação de terminal/aplicação, mas Listing não é sinônimo de CodeBlock nem de uma string literal opaca.

A estrutura pode ser:

```text
technical.listing
├── text.caption
└── technical.terminal_transcript
    ├── prompt/input fragments
    ├── output fragments
    └── editorial omission marker
```

**Valida:** M1-I15, AD-049 e especialização `technical.listing`.

### Tipografia como evidência, não semântica automática

O contraste bold/regular oferece evidência forte para separar valores digitados de valores ecoados. A semântica continua derivada; `bold => input` não vira regra universal.

**Valida:** M1-I12, M1-I18.

### Extensão 1 — input interativo

O candidate já permite `role` namespaced/extensível. Para preservar o papel dos valores digitados sem chamá-los incorretamente de `technical.command`, o holdout requer uma extensão de vocabulário do tipo:

```text
technical.terminal_input
```

Essa extensão não altera `DocumentNode`, `ContentFragment`, `StructuredPayload`, invariantes ou core.

### Extensão 2 — marcador editorial de omissão

`--trecho omitido--` é visualmente intercalado no transcript, porém não deve ser promovido a program output. Pode ser preservado como `ContentFragment` `marker` com role namespaced do tipo:

```text
editorial.omission_marker
```

A origem fina da omissão não é inferida; no nível canônico seguro, permanece evidência da edição ingerida.

Isso aplica diretamente a regra `visual adjacency ≠ common semantic origin`.

### Prosa e hifenização física

Quebras editoriais como `usa-` / `mos` e `aplicati-` / `vos` podem ser reconstruídas no CBM como texto lógico contínuo, desde que a Source Evidence permaneça ancorada e a reconstrução tenha provenance.

C1 já havia validado essa capacidade; W-RND confirma que ela também aparece no corpus-base técnico.

### Inline literal `y`

O `y` dentro da prosa pode ser um `ContentFragment` literal com fidelidade de caracteres mais estrita que o parágrafo pai, sem quebrar o modelo textual.

**Valida:** M1-I14, S08.

### NOTA + URL externa

A nota é `editorial.admonition`; a URL permanece literal e pode receber annotation/relation de referência externa sem tornar conteúdo gerado parte da fonte.

Nenhuma nova primitiva é necessária.

## Classificação

**W-RND = PASS_WITH_EXTENSION.**

Extensões observadas:

- `technical.terminal_input` — role de fragment para input interativo;
- `editorial.omission_marker` — role de fragment para omissão editorial explícita.

Essas extensões são legais sob o mecanismo de roles namespaced/extensíveis já congelado. Portanto:

- universal core changes: **0**;
- schema invariant changes: **0**;
- `MODEL_GAP`: **0**;
- `MODEL_FAILURE`: **0**.

---

# Conclusão do gate

O blind holdout conformance não encontrou evidência que invalide as abstrações congeladas.

```text
Golden slices F1/F2/W1/W2
        ↓
Cross-genre C1/C2/C3
        ↓
CBM v0.1 candidate FROZEN
        ↓
F-RND  PASS
W-RND  PASS_WITH_EXTENSION
        ↓
zero MODEL_GAP
zero MODEL_FAILURE
        ↓
eligível para CBM v0.1 promotion review
```

A especificação congelada `architecture/CBM-V0.1-CANDIDATE.md` permanece byte-for-byte inalterada em relação ao freeze manifest.

## Próximo gate recomendado

Executar **promotion review** curto para decidir a promoção formal de `0.1-candidate` para `CBM v0.1`. Esse review deve:

1. confirmar o resultado dos dois holdouts;
2. decidir se os dois roles observados em W-RND entram no registry/perfil de extensões da versão estável;
3. não reabrir o desenho do core sem nova evidência;
4. marcar M1 como concluído se a promoção for aprovada.
