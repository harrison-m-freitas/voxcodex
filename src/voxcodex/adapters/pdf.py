from __future__ import annotations

from pathlib import Path

import pymupdf

from voxcodex.domain.source import SourceArtifact, SourceProfile


class PdfAdapter:
    adapter_version = "0.1.0"

    def inspect(self, source: SourceArtifact, bytes_path: Path) -> SourceProfile:
        text_page_count = 0
        image_only_page_count = 0
        mixed_content_page_count = 0
        total_images = 0
        rotations: set[int] = set()
        fonts: set[str] = set()

        with pymupdf.open(bytes_path) as document:
            page_count = document.page_count
            for page in document:
                text = page.get_text("text").strip()
                images = page.get_images(full=True)
                has_text = bool(text)
                has_images = bool(images)

                if has_text:
                    text_page_count += 1
                if has_images:
                    total_images += len(images)
                if has_images and not has_text:
                    image_only_page_count += 1
                if has_images and has_text:
                    mixed_content_page_count += 1

                rotations.add(int(page.rotation))
                for font in page.get_fonts(full=True):
                    if len(font) > 3 and font[3]:
                        fonts.add(str(font[3]))

        if text_page_count == 0:
            coverage_kind = "none"
        elif text_page_count == page_count:
            coverage_kind = "full"
        else:
            coverage_kind = "mixed"

        characteristics = {
            "page_count": page_count,
            "text_layer_present": text_page_count > 0,
            "text_page_count": text_page_count,
            "image_only_page_count": image_only_page_count,
            "mixed_content_page_count": mixed_content_page_count,
            "image_count": total_images,
            "coverage_kind": coverage_kind,
            "rotations": tuple(sorted(rotations)),
            "font_count": len(fonts),
        }

        recommended_routes = ["pdf_text"] if text_page_count else []
        if image_only_page_count or mixed_content_page_count:
            recommended_routes.append("pdf_visual_evidence")

        return SourceProfile(
            id=f"profile:{source.id}:pdf:{self.adapter_version}",
            source_artifact_ref=source.id,
            format_family="pdf",
            declared_media_type=source.media_type,
            detected_media_type="application/pdf",
            characteristics=characteristics,
            recommended_routes=tuple(recommended_routes),
            provenance_ref=f"derivation:inspect:{source.id}:pdf:{self.adapter_version}",
        )
