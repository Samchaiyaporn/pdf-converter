import pymupdf as fitz
import filetype
import os


def analyze_pdf(file_path: str) -> dict:
    issues = []
    info = {}

    # File size
    file_size = os.path.getsize(file_path)
    info["file_size_bytes"] = file_size
    info["file_size_mb"] = round(file_size / (1024 * 1024), 2)

    if file_size > 20 * 1024 * 1024:
        issues.append(f"ไฟล์ขนาดใหญ่เกิน: {info['file_size_mb']} MB (เกิน 20 MB)")

    # Content-type check
    kind = filetype.guess(file_path)
    info["detected_type"] = kind.mime if kind else "unknown"
    if kind is None or kind.mime != "application/pdf":
        issues.append(
            f"Content-type ไม่ถูกต้อง: ตรวจพบ '{info['detected_type']}' "
            f"แทนที่จะเป็น 'application/pdf'"
        )

    # PDF internal analysis
    try:
        doc = fitz.open(file_path)
        info["page_count"] = len(doc)

        large_images = []
        total_images = 0
        seen_xrefs = set()

        for page_num in range(len(doc)):
            page = doc[page_num]
            images = page.get_images(full=True)

            for img in images:
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                total_images += 1

                try:
                    base_image = doc.extract_image(xref)
                    img_size = len(base_image["image"])
                    img_size_mb = round(img_size / (1024 * 1024), 2)

                    if img_size > 300 * 1024:  # > 300KB
                        large_images.append(
                            {
                                "page": page_num + 1,
                                "size_mb": img_size_mb,
                                "width": base_image.get("width", 0),
                                "height": base_image.get("height", 0),
                            }
                        )
                except Exception:
                    pass

        info["total_images"] = total_images
        info["large_images"] = large_images
        info["large_images_count"] = len(large_images)

        if large_images:
            total_mb = round(sum(i["size_mb"] for i in large_images), 2)
            issues.append(
                f"พบรูปขนาดใหญ่ {len(large_images)} ภาพ (รวม {total_mb} MB)"
            )

        doc.close()

    except Exception as e:
        issues.append(f"ไม่สามารถอ่าน PDF ได้: {e}")
        info.setdefault("page_count", 0)
        info.setdefault("total_images", 0)
        info.setdefault("large_images", [])
        info.setdefault("large_images_count", 0)

    info["issues"] = issues
    info["has_issues"] = len(issues) > 0

    return info
