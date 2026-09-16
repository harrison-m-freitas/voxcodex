from __future__ import annotations

import base64
from datetime import UTC, datetime
from pathlib import Path

from voxcodex.adapters.markdown import MarkdownAdapter
from voxcodex.adapters.pdf import PdfAdapter
from voxcodex.domain.source import SourceArtifact

import pymupdf


_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Zl1sAAAAASUVORK5CYII="
)


def make_source(path: Path, media_type: str) -> SourceArtifact:
    data = path.read_bytes()
    return SourceArtifact(
        id=f"source:{path.name}",
        media_type=media_type,
        original_filename=path.name,
        byte_size=len(data),
        checksum="a" * 64,
        acquisition_kind="synthetic_test",
        original_uri=None,
        created_at=datetime(2026, 9, 16, tzinfo=UTC),
    )


def test_pdf_profile_reports_text_and_image_only_pages(tmp_path: Path):
    path = tmp_path / "mixed.pdf"
    document = pymupdf.open()
    text_page = document.new_page()
    text_page.insert_text((72, 72), "Texto pesquisavel", fontsize=12)
    image_page = document.new_page()
    image_page.insert_image(pymupdf.Rect(72, 72, 144, 144), stream=_ONE_PIXEL_PNG)
    document.save(path)
    document.close()

    profile = PdfAdapter().inspect(make_source(path, "application/pdf"), path)

    assert profile.format_family == "pdf"
    assert profile.detected_media_type == "application/pdf"
    assert profile.characteristics["page_count"] == 2
    assert profile.characteristics["text_layer_present"] is True
    assert profile.characteristics["text_page_count"] == 1
    assert profile.characteristics["image_only_page_count"] == 1
    assert profile.characteristics["coverage_kind"] == "mixed"
    assert "pdf_text" in profile.recommended_routes


def test_markdown_profile_reports_encoding_and_syntax_hints(tmp_path: Path):
    path = tmp_path / "chapter.md"
    path.write_text(
        "# Titulo\n\nTexto.\n\n```python\nprint('x')\n```\n",
        encoding="utf-8",
        newline="\n",
    )

    profile = MarkdownAdapter().inspect(make_source(path, "text/markdown"), path)

    assert profile.format_family == "markdown"
    assert profile.detected_media_type == "text/markdown"
    assert profile.characteristics["encoding"] == "utf-8"
    assert profile.characteristics["line_endings"] == "lf"
    assert profile.characteristics["heading_syntax_present"] is True
    assert profile.characteristics["code_fence_present"] is True
    assert "markdown_syntax" in profile.recommended_routes
