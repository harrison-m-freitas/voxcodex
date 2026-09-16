from __future__ import annotations

from pathlib import Path

import pymupdf


_ONE_PIXEL_PPM = b"P6\n1 1\n255\n\xff\x00\x00"


def build_inspectable_pdf(path: Path) -> Path:
    document = pymupdf.open()
    page = document.new_page(width=612, height=792)

    page.insert_text((72, 72), "Bold title", fontname="hebo", fontsize=18)
    page.insert_text((72, 110), "Normal left column", fontname="helv", fontsize=11)
    page.insert_text((330, 110), "Normal right column", fontname="helv", fontsize=11)
    page.insert_text((72, 150), "E = mc", fontname="helv", fontsize=12)
    page.insert_text((112, 143), "2", fontname="helv", fontsize=7)
    page.insert_image(pymupdf.Rect(72, 190, 122, 240), stream=_ONE_PIXEL_PPM)

    document.save(path)
    document.close()
    return path
