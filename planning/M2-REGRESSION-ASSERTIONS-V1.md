# M2 — Regression Assertions v1 — FROZEN

**Data:** 2026-09-14  
**Status:** `FROZEN`

Estas assertions congelam o que os nove casos já conhecidos precisam demonstrar no pipeline M2. Elas testam semântica/estrutura por camada, não IDs ou serialização incidental. O JSON normativo é `corpus/manifests/M2-REGRESSION-ASSERTIONS-V1.json`.

## F1 — PDF p.6

- **F1-A01 [Reconstruction]** — Ato I and Cena I are reconstructed as distinct logical divisions rather than page artifacts.
- **F1-A02 [CBM]** — Participant declaration, SpeakerCue, Speech and Character remain distinct; SpeakerCue is sibling of Speech, not its child/field.
- **F1-A03 [CBM]** — VerseLine units are addressable and preserve source order/lineation.
- **F1-A04 [Reconstruction]** — Physical page end does not close an open speech merely because the page ends.
- **F1-A05 [Provenance]** — Source-derived units remain traceable to the source page/evidence.

## F2 — PDF pp.10-11

- **F2-A01 [Reconstruction]** — Open structural state survives page/chunk boundaries and reconciles cross-page speech continuity.
- **F2-A02 [CBM]** — Scene transitions are represented without fabricating entry/exit events not explicit in the edition.
- **F2-A03 [CBM]** — Declared participant state remains distinct from inferred semantic transitions.
- **F2-A04 [Reconstruction]** — Page boundary is not promoted to logical document boundary.

## W1 — PDF p.112

- **W1-A01 [Reconstruction]** — Running header/folio are identified as recurrent physical/editorial material, not duplicate logical chapters.
- **W1-A02 [CBM]** — Listing editorial container remains distinct from CodeBlock and TerminalTranscript content nature.
- **W1-A03 [Reconstruction]** — Terminal transcript and Bash source code are reconstructed as different structures.
- **W1-A04 [Evidence]** — Typography/layout remain available as evidence without a universal bold/monospace semantic shortcut.
- **W1-A05 [Fidelity]** — Local literal-sensitive content can carry stricter fidelity than surrounding textual prose.

## W2 — PDF p.96

- **W2-A01 [CBM]** — Table topology preserves rows, columns and cell membership rather than flattening to plain text.
- **W2-A02 [Fidelity]** — Surface lexeme such as 011 is preserved independently from typed/normalized interpretation.
- **W2-A03 [Reconstruction]** — Editorial callout marker interleaved with terminal-like content remains distinguishable from program output.
- **W2-A04 [Reconstruction]** — Cross-page section continuity is preserved.

## C1 — PDF pp.6-7 and 38-39

- **C1-A01 [Reconstruction]** — Multi-column physical layout is separated from logical reading order.
- **C1-A02 [Reconstruction]** — Paragraph continuity may cross columns/pages and remain one logical unit.
- **C1-A03 [CBM]** — Footnote marker and footnote body are separate units connected by explicit relation.
- **C1-A04 [Provenance]** — Layout-caused dehyphenation/reconstruction preserves source evidence and derivation.
- **C1-A05 [CBM]** — External scripture/bibliographic references remain external targets rather than copied canonical content.

## C2 — PT-BR chapter slices C2-A/C2-B

- **C2-A01 [CBM]** — Narrative utterance does not require theatrical SpeakerCue; speaker may be relation/inference or remain unknown.
- **C2-A02 [CBM]** — Semantic function spanning a whole block can be a DocumentNode role; inline occurrence can be Annotation/span without structural inflation.
- **C2-A03 [CBM]** — Narrative order remains document order; flashback/story chronology is not substituted for source order.
- **C2-A04 [CBM]** — Scene break, embedded song/verse and internal thought are representable without new universal primitives.
- **C2-A05 [Provenance]** — EN and PT-BR manifestations remain distinct sources; translation alignment is not silently merged.

## C3 — PDF pp.83,87,139,145

- **C3-A01 [Evidence]** — Mathematical visual/glyph/layout evidence is retained even when PDF text layer is plausible but semantically corrupt.
- **C3-A02 [CBM]** — FormulaPayload distinguishes source representation from reconstructed representation with provenance.
- **C3-A03 [CBM]** — Inline formula nodes and text fragments can participate in one shared logical order.
- **C3-A04 [CBM]** — Figure panels are individually addressable/anchorable.
- **C3-A05 [CBM]** — Pedagogical structures such as Definition/Example/Solution/Exercise use roles/relations without new universal core primitives.

## F-RND — PDF p.33

- **FR-A01 [Reconstruction]** — A page may begin mid-speech with open structural state and no fabricated local speaker.
- **FR-A02 [CBM]** — SpeakerCue and Speech remain sibling structures connected semantically.
- **FR-A03 [CBM]** — Scene VI and participant declaration are represented explicitly without inferred stage events.
- **FR-A04 [CBM]** — VerseLine ordering/identity survives the page boundary.

## W-RND — PDF p.558

- **WR-A01 [Reconstruction]** — Running header/folio do not duplicate logical chapter and paragraph continuation is preserved.
- **WR-A02 [CBM]** — Listing may contain terminal interaction plus editorial omission marker without flattening.
- **WR-A03 [Evidence]** — Typography can support input-vs-echo reconstruction without becoming a universal semantic rule.
- **WR-A04 [CBM]** — Roles technical.terminal_input and editorial.omission_marker are accepted extensions under CBM v0.1.
- **WR-A05 [CBM]** — Editorial note and external URL remain source editorial/reference content, distinct from generated assistance.

