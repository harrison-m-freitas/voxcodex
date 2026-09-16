# VoxCodex Compatibility Corpus

This directory contains the concrete Compatibility Corpus v1 acquisitions. It is separate from the historical `data/` directory so M1/M2 frozen evidence is not rewritten or mixed with later compatibility acquisitions.

- Registry: `COMPATIBILITY-CORPUS-V1.json`
- Per-case metadata: `compatibility/CC-xx/metadata.json`
- Acquisition manifests: `manifests/`
- Compatibility Corpus v1: **FROZEN 30/30**; shortlist **12/12**; no acquisition cases remain pending.
- M2 Blind Holdouts v1 are **FROZEN / UNREVEALED**; `CC-05`, `CC-07`, `CC-14`, `CC-18` remain quarantined.

Raw acquired bytes are copied unchanged from the user-provided acquisition ZIP. Stable `CC-xx` IDs identify cases; acquired filenames are preserved inside each case. Acquisition URLs/rights are not inferred from filenames and remain pending when not embedded in the uploaded artifact.

The v1 corpus membership and acquired manifestations are frozen by `COMPATIBILITY-CORPUS-V1-FREEZE-MANIFEST.json`. Future replacements or manifestation changes require an explicit new corpus version; they do not mutate v1.
