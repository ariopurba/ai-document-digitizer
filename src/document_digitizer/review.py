"""Adapt the file-based pipeline to local browser uploads and page previews."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pymupdf
from docling_core.types.doc import DoclingDocument
from PIL import Image, ImageOps

from .config import SUPPORTED_SUFFIXES, DigitizerError
from .pipeline import process_file

_PREVIEW_SIZE = 1200


@dataclass(frozen=True)
class ReviewResult:
    """Both exports and the document model for page-by-page review."""

    markdown: bytes
    json: bytes
    document: DoclingDocument


def convert_upload(filename: str, contents: bytes) -> ReviewResult:
    """Run the existing pipeline in an isolated, short-lived directory."""
    name = Path(filename.replace("\\", "/")).name
    if Path(name).suffix.lower() not in SUPPORTED_SUFFIXES:
        raise DigitizerError("Choose a PDF, PNG, JPG, or JPEG file.")
    with TemporaryDirectory(prefix="digitizer-ui-") as temp:
        root = Path(temp)
        source = root / name
        source.write_bytes(contents)
        destination = process_file(source, root / "output")
        json_path = destination / "content.json"
        return ReviewResult(
            markdown=(destination / "content.md").read_bytes(),
            json=json_path.read_bytes(),
            document=DoclingDocument.load_from_json(json_path),
        )


def render_source_page(filename: str, contents: bytes, page_no: int) -> bytes:
    """Render one source page as a bounded PNG for the review panel."""
    if Path(filename).suffix.lower() == ".pdf":
        with pymupdf.open(stream=contents, filetype="pdf") as pdf:
            page = pdf[page_no - 1]
            scale = _PREVIEW_SIZE / max(page.rect.width, page.rect.height)
            return page.get_pixmap(
                matrix=pymupdf.Matrix(scale, scale), alpha=False
            ).tobytes("png")

    with Image.open(BytesIO(contents)) as source:
        source.seek(page_no - 1)
        frame = ImageOps.exif_transpose(source)
        frame.thumbnail((_PREVIEW_SIZE, _PREVIEW_SIZE))
        png = BytesIO()
        frame.save(png, format="PNG")
        return png.getvalue()
