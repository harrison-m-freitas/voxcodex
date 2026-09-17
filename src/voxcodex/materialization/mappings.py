from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from voxcodex.digests import canonical_json_bytes, sha256_bytes
from voxcodex.domain.cbm.structured import FormulaPayload, TableCell, TablePayload
from voxcodex.domain.common import FrozenModel
from voxcodex.reconstruction.structured import FormulaCandidate, TableCandidate


NodeClass = Literal["root", "division", "block", "structured_block", "declaration", "asset"]


class RoleMapping(FrozenModel):
    reconstruction_role: str
    node_class: NodeClass
    cbm_role: str


class RoleMappingRegistry(FrozenModel):
    version: str
    mappings: tuple[RoleMapping, ...]

    @property
    def artifact_digest(self) -> str:
        return sha256_bytes(canonical_json_bytes(self.model_dump(mode="json")))

    def resolve(self, role: str) -> RoleMapping | None:
        for mapping in self.mappings:
            if mapping.reconstruction_role == role:
                return mapping
        return None

    @classmethod
    def v01_defaults(cls) -> "RoleMappingRegistry":
        division_roles = {
            "text.chapter",
            "text.section",
            "drama.act",
            "drama.scene",
            "narrative.prologue",
        }
        declaration_roles = {"drama.participant_declaration"}
        structured_roles = {"structured.table", "structured.formula"}
        asset_roles = {"structured.figure", "structured.figure_panel"}
        block_roles = {
            "text.paragraph",
            "text.heading",
            "text.caption",
            "text.list",
            "text.list_item",
            "drama.speech",
            "drama.speaker_cue",
            "poetry.verse_line",
            "technical.listing",
            "technical.code_block",
            "technical.code_line",
            "technical.terminal_transcript",
            "technical.terminal_command_line",
            "technical.terminal_output_line",
            "technical.terminal_control_line",
            "technical.terminal_input",
            "editorial.admonition",
            "editorial.callout_marker",
            "editorial.footnote",
            "editorial.footnote_marker",
            "editorial.omission_marker",
            "narrative.utterance",
            "narrative.internal_thought",
            "narrative.scene_break",
            "narrative.embedded_song",
            "math.expression",
            "math.derivation",
            "pedagogy.definition",
            "pedagogy.example",
            "pedagogy.problem_statement",
            "pedagogy.solution",
            "pedagogy.exercise_set",
            "pedagogy.exercise",
            "pedagogy.exercise_part",
            "pedagogy.shared_instruction",
            "pedagogy.tool_marker",
        }

        mappings: list[RoleMapping] = []
        for role in sorted(division_roles):
            mappings.append(RoleMapping(reconstruction_role=role, node_class="division", cbm_role=role))
        for role in sorted(declaration_roles):
            mappings.append(RoleMapping(reconstruction_role=role, node_class="declaration", cbm_role=role))
        for role in sorted(structured_roles):
            mappings.append(RoleMapping(reconstruction_role=role, node_class="structured_block", cbm_role=role))
        for role in sorted(asset_roles):
            mappings.append(RoleMapping(reconstruction_role=role, node_class="asset", cbm_role=role))
        for role in sorted(block_roles):
            mappings.append(RoleMapping(reconstruction_role=role, node_class="block", cbm_role=role))

        return cls(version="0.1", mappings=tuple(mappings))


class RoleProfileRegistry(RoleMappingRegistry):
    """Versioned materialization policy for namespaced CBM v0.1 roles."""

    @classmethod
    def v01_defaults(cls) -> "RoleProfileRegistry":
        base = RoleMappingRegistry.v01_defaults()
        return cls(version=base.version, mappings=base.mappings)


def materialize_table_payload(
    candidate: TableCandidate,
    *,
    content_refs_by_evidence: Mapping[str, str],
) -> TablePayload:
    cells: list[TableCell] = []
    for index, candidate_cell in enumerate(candidate.cells):
        content_refs = tuple(
            content_refs_by_evidence[ref.id]
            for ref in candidate_cell.evidence_refs
            if ref.id in content_refs_by_evidence
        )
        cells.append(
            TableCell(
                id=f"table-cell:{sha256_bytes(canonical_json_bytes({'candidate': candidate.id, 'index': index}))}",
                row=candidate_cell.row_index,
                column=candidate_cell.column_index,
                cell_role="body",
                content_refs=content_refs,
            )
        )
    return TablePayload(
        id=f"table-payload:{sha256_bytes(canonical_json_bytes({'candidate': candidate.id}))}",
        row_count=candidate.row_count,
        column_count=candidate.column_count,
        cells=tuple(cells),
    )


def materialize_formula_payload(
    candidate: FormulaCandidate,
    *,
    reconstructed_representation_ref: str | None = None,
) -> FormulaPayload:
    source_refs = tuple(ref.id for ref in candidate.evidence_refs)
    reconstructed_refs = (
        (reconstructed_representation_ref,)
        if reconstructed_representation_ref is not None
        else ()
    )
    return FormulaPayload(
        id=f"formula-payload:{sha256_bytes(canonical_json_bytes({'candidate': candidate.id}))}",
        source_representation_refs=source_refs,
        reconstructed_representation_refs=reconstructed_refs,
    )
