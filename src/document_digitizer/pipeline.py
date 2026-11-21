from pathlib import Path

from .config import DigitizerError
from .exporter import export_document
from .extractor import extract_document
from .validator import validate_source


def process_file(file_path: Path | str, output_root: Path | str) -> Path:
    """Extract one file and return the directory containing both exports."""
    source = validate_source(file_path)
    destination = Path(output_root).expanduser() / source.stem
    if destination.exists():
        raise DigitizerError(
            f"Result already exists: {destination}. Choose another output root."
        )
    document = extract_document(source)
    try:
        export_document(document, destination)
    except DigitizerError:
        raise
    except Exception as exc:
        raise DigitizerError(
            f"Could not export {source.name} to {destination}: {exc}"
        ) from exc
    return destination
