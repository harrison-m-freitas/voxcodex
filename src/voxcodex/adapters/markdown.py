from __future__ import annotations

from pathlib import Path

from markdown_it import MarkdownIt

from voxcodex.domain.source import SourceArtifact, SourceProfile


class MarkdownAdapter:
    adapter_version = "0.1.0"

    def inspect(self, source: SourceArtifact, bytes_path: Path) -> SourceProfile:
        raw = bytes_path.read_bytes()
        text = raw.decode("utf-8-sig")
        tokens = MarkdownIt().parse(text)

        crlf_count = raw.count(b"\r\n")
        lf_count = raw.count(b"\n")
        bare_lf_count = lf_count - crlf_count
        if crlf_count and bare_lf_count:
            line_endings = "mixed"
        elif crlf_count:
            line_endings = "crlf"
        elif bare_lf_count:
            line_endings = "lf"
        else:
            line_endings = "none"

        token_types = {token.type for token in tokens}
        characteristics = {
            "encoding": "utf-8",
            "line_endings": line_endings,
            "heading_syntax_present": "heading_open" in token_types,
            "code_fence_present": "fence" in token_types,
            "link_syntax_present": "link_open" in token_types,
            "embedded_html_present": bool({"html_block", "html_inline"} & token_types),
            "table_syntax_present": "table_open" in token_types,
        }

        return SourceProfile(
            id=f"profile:{source.id}:markdown:{self.adapter_version}",
            source_artifact_ref=source.id,
            format_family="markdown",
            declared_media_type=source.media_type,
            detected_media_type="text/markdown",
            characteristics=characteristics,
            recommended_routes=("markdown_syntax",),
            provenance_ref=f"derivation:inspect:{source.id}:markdown:{self.adapter_version}",
        )
