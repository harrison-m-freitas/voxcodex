# Proof of Concept

## Objetivo

Demonstrar a tese central:

```text
documento
→ estrutura
→ compreensão
→ roteiro narrável auditável
→ áudio coerente
```

## Corpus

### Fedra — Jean Racine

Testar:

- teatro;
- atos/cenas quando presentes;
- personagens;
- diálogo;
- speaker attribution;
- múltiplas vozes;
- continuidade de voz;
- distinção entre fala e indicação editorial;
- prosódia;
- confiança e revisão humana.

### Testes de Invasão — Georgia Weidman

Testar:

- estrutura técnica;
- capítulos/seções;
- prosa vs. código;
- comandos;
- URLs;
- IPs;
- termos ingleses;
- figuras;
- legendas;
- referências;
- cabeçalhos/rodapés;
- adaptação visual → áudio;
- preservação literal de conteúdo técnico.


## Corpus de conformidade do M1

- F1: *Fedra*, PDF p. 6 — analisado e aprovado.
- F2: *Fedra*, PDFs p. 10–11 — analisado e aprovado.
- F-RND: *Fedra*, PDF p. 33 — holdout revelado após freeze; **PASS**.
- W1: Weidman, PDF p. 112 — analisado e aprovado.
- W2: Weidman, PDF p. 96 — analisado e aprovado.
- W-RND: Weidman, PDF p. 558 — holdout revelado após freeze; **PASS_WITH_EXTENSION**.

As páginas holdout foram usadas somente após o freeze para testar surpresa intraobra. Nenhuma exigiu mudança de core; o candidate congelado permaneceu inalterado e foi posteriormente promovido para `CBM v0.1`.

### Validação cross-genre — concluída

- **C1:** Leandro Lima — *As Grandes Doutrinas da Graça*, Vols. 1–2 — `PASS_WITH_EXTENSION`;
- **C2:** *Eternally Regressing Knight* — `PASS_WITH_EXTENSION`;
- **C3:** James Stewart — *Calculus*, 8th ed. — `PASS_WITH_EXTENSION`.

Nenhum teste exigiu nova primitiva universal. Foram incorporados vocabulários de footnotes/citations, narrativa, matemática/pedagogia, figure panels e refinamento do `FormulaPayload`. Registro: `planning/M1-CROSS-GENRE-VALIDATION.md`.

## Regras de fidelidade confirmadas no M1

- `textual_exact`: padrão do modo Fiel para texto autoral/editorial narrável;
- `literal_exact`: conteúdo cujo significado depende de caracteres exatos, como comandos, código, URLs e IPs;
- `symbolic_exact`: direção prevista para fórmulas/matemática;
- a política pode ser refinada em spans/subunidades dentro de um bloco;
- estruturas como tabelas devem preservar topologia, não apenas texto linear;
- representação superficial e interpretação tipada coexistem, sem uma substituir a outra.

## Idioma

- Português: obrigatório.
- Inglês: oportunista.
- Tradução: fora do PoC.

## Produto-base

Audiobook **Fiel**.

Três operações conceituais:

1. PRESERVE
2. AUDIO_ADAPT
3. OMIT_FROM_AUDIO

Conteúdo enriquecido ou didático não pode ser inserido silenciosamente.

## Tipos de entrada sugeridos

- EPUB estruturado;
- PDF digital razoavelmente estruturado;
- opcionalmente poucas páginas escaneadas apenas para validar o conceito de reconstrução.

## Modelo canônico mínimo do PoC

O PoC seguirá o **`CBM v0.1` promovido** (`schema_version=0.1`), cuja especificação normativa está em `architecture/CBM-V0.1.md`. O candidate congelado permanece preservado apenas como evidência do gate.

Primitivas mínimas:

- CanonicalDocument;
- CanonicalRevision;
- DocumentNode;
- ContentFragment;
- SourceArtifact;
- SourceAnchor;
- FidelityConstraint;
- Entity;
- Annotation;
- Relation;
- ProcessingActivity;
- Derivation;
- ValidationReport.

`TablePayload` é obrigatório quando houver conteúdo tabular. `FormulaPayload` é a especialização validada para matemática quando a estrutura simbólica não puder ser preservada adequadamente por fragments/árvore simples.

Chapter, Scene, Speech, CodeBlock, TerminalTranscript etc. são roles/especializações, não primitivas universais.

O CBM não inclui NarrationSegment ou AudioSegment; esses pertencem a artefatos downstream.

## Critérios de sucesso

### Fedra

- atribuição de speaker confiável;
- mesma voz para o mesmo personagem;
- incerteza explicitada;
- revisão humana possível;
- preservação textual da edição.

### Weidman

- comandos preservados literalmente;
- código separado de prosa;
- URLs/IPs preservados;
- estrutura reconstruída;
- referências visuais tratadas;
- fonte rastreável a partir do áudio.

## Provenance obrigatório

Deve ser possível navegar:

```text
audio
→ narration segment
→ canonical block
→ source artifact/page
```

## Custo

Antes:
- estimativa X–Y.

Depois:
- custo real;
- erro da estimativa.

## Não construir no PoC

- dezenas de formatos;
- tradução completa;
- matemática avançada;
- diagramas científicos universais;
- centenas de vozes;
- vários provedores por categoria;
- vector DB dedicado sem necessidade demonstrada;
- microserviços;
- Kubernetes;
- app mobile;
- treinamento de modelos próprios.
