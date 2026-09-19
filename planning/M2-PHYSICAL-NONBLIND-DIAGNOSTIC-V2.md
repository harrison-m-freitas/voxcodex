# M2 Physical Non-Blind Diagnostic — Candidate V2

Status: **KNOWN NON-BLIND BLOCKERS FOUND / HOLDOUTS STILL UNREVEALED**

This diagnostic used the five known Tier 1 non-holdout SourceArtifacts whose frozen SHA-256 values matched exactly. It is **not formal Candidate V2 conformance**, because the local runtime was Python 3.13.5 rather than the candidate-bound Python 3.14.7 and diagnostic-only compatibility shims were required for `uuid.uuid7` and `rfc8785`.

No content from `CC-05`, `CC-07`, `CC-14`, or `CC-18` was opened or processed.

## Findings

| Case | Scope | Result | Known blocker |
|---|---|---|---|
| CC-04 | full 628-page PDF | MODEL_FAILURE | 63 whitespace-only text spans treated as significant suspected loss |
| CC-12 | full 770-page PDF | MODEL_FAILURE | 7 whitespace-only text spans treated as significant suspected loss |
| CC-19 | full source text | MODEL_FAILURE | 74 nested emphasis units + 3 indented code blocks + 1 HTML comment not fully accounted |
| CC-22 | full 228-page PDF | MODEL_FAILURE | 36 whitespace-only text spans treated as significant suspected loss |
| CC-25 | full 297-page PDF | MODEL_FAILURE | 1 whitespace-only text span treated as significant suspected loss |

## V3 correction boundary

The V3 correction is intentionally narrow and uses only known, non-blind evidence:

- whitespace-only `text_span` becomes non-significant when otherwise unrepresented;
- nested Markdown syntax fully contained by a canonicalized block range becomes redundant non-significant evidence;
- Markdown `code_block` and `html_block` are mapped to the existing `technical.code_block` role;
- CBM v0.1, frozen assertions, blind selection, holdout scopes, and ValidationPolicy remain unchanged.

Candidate V2 remains immutable historical pre-reveal evidence. The four blind holdouts remain **FROZEN / UNREVEALED**.
