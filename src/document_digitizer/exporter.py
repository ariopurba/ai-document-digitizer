from pathlib import Path
from tempfile import TemporaryDirectory

from docling_core.types.doc import DoclingDocument

from .config import DigitizerError


def export_document(document: DoclingDocument, destination: Path) -> None:
    """Write the Markdown and native JSON together in a new result directory."""
    markdown = document.export_to_markdown()
    if not markdown.strip():
        raise DigitizerError("Docling produced empty Markdown. Check the source pages.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent, prefix=".digitizer-") as temp:
        staging = Path(temp)
        (staging / "content.md").write_text(markdown, encoding="utf-8")
        document.save_as_json(staging / "content.json")
        # Claim the name exclusively before publishing either file.
        destination.mkdir()
        try:
            for filename in ("content.json", "content.md"):
                (staging / filename).rename(destination / filename)
        except OSError:
            for filename in ("content.json", "content.md"):
                (destination / filename).unlink(missing_ok=True)
            destination.rmdir()
            raise
