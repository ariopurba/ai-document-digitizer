"""Generate small, labeled educational samples for local integration tests."""
from pathlib import Path

import pymupdf


def make_samples(directory: Path) -> dict[str, Path]:
    """Create a two-page text PDF, an image-only PDF, and photos of one page."""
    directory.mkdir(parents=True, exist_ok=True)
    paths = {kind: directory / name for kind, name in (
        ("text", "synthetic-lesson.pdf"),
        ("scan", "synthetic-scan.pdf"),
        ("png", "synthetic-page.png"),
        ("jpg", "synthetic-page.jpg"),
        ("jpeg", "synthetic-page.jpeg"),
    )}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError(f"Synthetic samples already exist in {directory}")
    with pymupdf.open() as doc:
        page = doc.new_page(width=520, height=420)
        page.insert_text((45, 50), "Synthetic lesson: Plant growth", fontsize=24)
        page.insert_text((45, 90), "Seedlings need light and water.", fontsize=16)
        for x in (45, 175, 305, 435):
            page.draw_line((x, 130), (x, 250))
        for index, row in enumerate([
            ("Plant", "Week", "Height"),
            ("Bean", "One", "12 cm"),
            ("Pea", "Two", "18 cm"),
        ]):
            y = 130 + index * 40
            page.draw_line((45, y), (435, y))
            for column, value in enumerate(row):
                page.insert_text((54 + column * 130, y + 26), value, fontsize=16)
        page.draw_line((45, 250), (435, 250))
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
        pixmap.save(paths["png"])
        for kind in ("jpg", "jpeg"):
            pixmap.save(paths[kind], output="jpeg")
        page = doc.new_page(width=520, height=420)
        page.insert_text((45, 70), "Observation journal", fontsize=22)
        page.insert_text((45, 110), "Measure each stem every week.", fontsize=16)
        doc.save(paths["text"])
    with pymupdf.open() as scan:
        page = scan.new_page(width=520, height=420)
        page.insert_image(page.rect, filename=str(paths["png"]))
        assert not page.get_text().strip()
        scan.save(paths["scan"], deflate=True)
    return paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    make_samples(parser.parse_args().directory)
