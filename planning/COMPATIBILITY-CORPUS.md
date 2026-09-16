# Compatibility Corpus & Schema Evolution

## Estado

Estratégia aprovada em 2026-09-11 como requisito transversal a partir do M2.

O objetivo não é provar antecipadamente que o CBM representa todos os livros. É detectar, classificar e acumular evidência de compatibilidade à medida que o pipeline real passa a processar fontes mais diversas.

## Estrutura do corpus

### Regression Shortlist

- alvo: **8–12 materiais**;
- propósito: suíte pequena, estável e executada com frequência;
- seleção: maximizar diversidade de fenômenos estruturais e formatos.

Shortlist inicial:

1. Constituição Federal brasileira;
2. Platão — *A República*;
3. Heródoto — *Histórias*;
4. W. E. B. Du Bois — *The Souls of Black Folk*;
5. *The Rust Programming Language*;
6. Tutorial oficial do Python em PT-BR;
7. Bram Stoker — *Dracula*;
8. artigo científico moderno com equações, figuras e bibliografia.

### Discovery Corpus

- alvo inicial: **aproximadamente 30 materiais no total**, incluindo a shortlist;
- propósito: encontrar fenômenos novos, formatos problemáticos e casos extremos;
- não é gate para iniciar M2;
- materiais podem entrar/sair conforme deixem de acrescentar cobertura.

## Cobertura desejada

A seleção deve considerar pelo menos duas dimensões independentes.

### Conteúdo/estrutura

- história;
- cultura/ensaio;
- filosofia/diálogo;
- programação/documentação;
- direito/normas;
- ciência/artigos;
- matemática;
- poesia;
- narrativa epistolar/multidocumento;
- narrativa experimental;
- material procedural/cookbook;
- referência/dicionário/enciclopédia;
- documentos bilíngues;
- conteúdo fortemente visual quando relevante.

### Formato/container

- PDF textual bom;
- PDF textual degradado;
- PDF scanned/OCR-heavy;
- EPUB;
- HTML;
- Markdown;
- DOCX;
- TXT.

## Classificação de resultados

- `PASS`
- `PASS_WITH_EXTENSION`
- `PROCESSING_FAILURE`
- `MODEL_GAP`
- `MODEL_FAILURE`

### Distinção crítica

`PROCESSING_FAILURE` significa:

> o CBM vigente é capaz de representar corretamente o caso, mas o pipeline não conseguiu reconstruí-lo/materializá-lo.

`MODEL_GAP` significa:

> mesmo com reconstrução correta, falta capacidade estrutural no contrato vigente.

Não confundir esses resultados é um requisito de diagnóstico do M2.

## CorpusCase — conceito

Ainda sem schema físico congelado, cada caso deverá ser capaz de registrar conceitualmente:

```text
CorpusCase
├── source
├── format
├── language
├── structural_features[]
├── expected_capabilities[]
├── observed_extensions[]
├── incompatibilities[]
└── result
```

## Equivalência cross-format

Quando a mesma manifestação/edição estiver disponível em formatos diferentes, o corpus deve futuramente testar:

```text
PDF  ──┐
EPUB ──┼─→ estruturas canônicas semanticamente compatíveis?
HTML ──┘
```

A Source Evidence não precisa ser idêntica. O objetivo é detectar se diferenças de parser/container estão vazando indevidamente para a estrutura canônica.

## Política de evolução do CBM

`CBM v0.1` é baseline estável.

Novo caso não modifica automaticamente o core. O fluxo é:

```text
CorpusCase
   ↓
Observation
   ↓
PASS / EXTENSION / PROCESSING_FAILURE / GAP / FAILURE
   ↓
Schema Evolution Log
   ↓ se mudança normativa for justificada
novo candidate versionado
   ↓
regressão da shortlist/corpus relevante
   ↓
promoção explícita
```

## Schema Evolution Log — conteúdo mínimo

Uma observação de evolução deve registrar:

- ID;
- fonte/caso;
- fenômeno estrutural;
- evidência;
- representação atual;
- classificação;
- impacto;
- alternativa de extensão/mudança, se necessária;
- compatibilidade esperada;
- decisão/resultados de regressão quando aplicável.

## Relação com M1

F1/F2/W1/W2, C1/C2/C3 e F-RND/W-RND continuam sendo evidência histórica de construção/conformidade do `CBM v0.1`. O Compatibility Corpus amplia essa disciplina durante processamento real, mas não reabre retroativamente os gates do M1.

## Papéis executáveis aprovados no M2.6

O corpus passa a operar em quatro papéis distintos:

1. **Regression Core** — F1/F2/W1/W2, C1/C2/C3 e F-RND/W-RND, com assertions versionadas por camada;
2. **Compatibility Shortlist** — 8–12 casos adversariais para claims Tier 1/Tier 1.5;
3. **Discovery Corpus** — ~30 materiais usados como sensores de fenômenos novos;
4. **M2 Blind Holdouts** — casos novos, fechados até o freeze do candidate de implementação.

Golden tests devem validar Evidence, Reconstruction, CBM, Provenance e Validation por assertions estruturais/semânticas; snapshots completos/IDs não são o contrato do teste.

## Support tiers

- **Tier 1:** supported / exit-gated;
- **Tier 1.5:** best-effort com preservation obrigatória;
- **Experimental:** discovery only;
- **Deferred:** fora do escopo corrente.

M2 mantém PDF textual + Markdown em Tier 1 e PDF mixed em Tier 1.5.

## Evidence accountability

Evidence significativa deve ser classificada como `canonicalized`, `intentionally_noncanonical`, `unresolved` ou `suspected_loss`. Perda silenciosa conhecida de conteúdo significativo é blocker do M2.

## Holdouts do M2

Holdouts do M1 já foram revelados e agora fazem parte da regressão. O M2 exige novos holdouts selecionados/congelados antes da implementação. Como baseline de desenho, a suíte cega deve cobrir pelo menos PDF literário/prosa, PDF técnico, PDF matemático/estruturado e Markdown narrativa.

Após reveal, qualquer tuning sobre o mesmo holdout invalida seu papel como evidência cega para a nova claim; ele passa a ser regressão e um novo holdout é necessário.

## Exit criteria resumidos

- Regression Core verde em suas assertions;
- shortlist Tier 1 sem MODEL_GAP/MODEL_FAILURE não resolvido e sem significant silent loss;
- discovery findings classificados/registrados;
- provenance fim a fim demonstrada em objetos representativos;
- CanonicalRevisions principais frozen sob policy versionada;
- idempotência/cache/selective reprocessing demonstrados;
- novos blind holdouts executados somente após candidate freeze.



## Freeze protocol do M2

A shortlist não implica support claim; cada caso é avaliado por `support_tier`. Antes de tuning relevante, congelam-se assertions do Regression Core e seleção/hash/scope dos holdouts sem reveal. Antes do reveal, congela-se implementation candidate com identidade, baseline CBM, semantic config, processors/models/providers, reproducibility class, ValidationPolicy, versões das assertions e capability/support-tier claims. Mudança posterior de claim não reclassifica retroativamente um FAIL.

## Concrete Corpus v1 — 2026-09-14

A curadoria concreta foi fechada em 30 casos, com shortlist de 12. Registro operacional: `planning/COMPATIBILITY-CORPUS-V1.md`; registry machine-readable: `corpus/COMPATIBILITY-CORPUS-V1.json`. Em 2026-09-14 a shortlist está 12/12 adquirida e o corpus total **28/30** adquirido; permanecem pendentes apenas `CC-08` e `CC-15`. Novas aquisições vivem em `corpus/compatibility/`; `data/` histórico permanece separado.
