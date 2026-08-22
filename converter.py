import pymupdf as fitz
import os
from typing import Callable, Optional

DPI = 150
JPEG_QUALITY = 65


def convert_pdf(
    input_path: str,
    output_path: str,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> dict:
    """
    Re-render each page at DPI=150 as JPEG (quality=65%) into a new PDF.
    This approach handles all color spaces (CMYK, RGB, Grayscale) correctly
    because PyMuPDF renders the composited page — no manual image extraction.
    """
    src_doc = fitz.open(input_path)
    new_doc = fitz.open()

    original_size = os.path.getsize(input_path)
    total_pages = len(src_doc)
    mat = fitz.Matrix(DPI / 72, DPI / 72)  # 72 = PDF base DPI

    for page_num in range(total_pages):
        page = src_doc[page_num]

        # Render page to RGB pixmap (handles CMYK, indexed, etc. automatically)
        pix = page.get_pixmap(matrix=mat, alpha=False, colorspace=fitz.csRGB)

        # Encode as JPEG at quality=65
        img_bytes = pix.tobytes("jpeg", jpg_quality=JPEG_QUALITY)

        # Create new page matching rendered size
        new_page = new_doc.new_page(width=pix.width, height=pix.height)
        new_page.insert_image(new_page.rect, stream=img_bytes)

        if progress_callback:
            progress_callback((page_num + 1) / total_pages)

    new_doc.save(output_path, garbage=4, deflate=True, clean=True)
    new_doc.close()
    src_doc.close()

    new_size = os.path.getsize(output_path)
    reduction = original_size - new_size
    reduction_pct = round((reduction / original_size) * 100, 1) if original_size else 0

    return {
        "original_size_mb": round(original_size / (1024 * 1024), 2),
        "new_size_mb": round(new_size / (1024 * 1024), 2),
        "new_size_kb": round(new_size / 1024, 1),
        "size_reduction_mb": round(reduction / (1024 * 1024), 2),
        "size_reduction_pct": reduction_pct,
        "total_pages": total_pages,
    }
