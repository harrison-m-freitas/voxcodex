from __future__ import annotations

from typing import Literal

from voxcodex.domain.common import FrozenModel


NodeClass = Literal["root", "division", "block", "structured_block", "declaration", "asset"]


class RoleMapping(FrozenModel):
    reconstruction_role: str
    node_class: NodeClass
    cbm_role: str


class RoleMappingRegistry(FrozenModel):
    version: str
    mappings: tuple[RoleMapping, ...]

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
