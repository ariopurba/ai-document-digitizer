from pathlib import Path

from .config import SUPPORTED_SUFFIXES, DigitizerError


def validate_source(file_path: Path | str) -> Path:
    """Accept only an existing, nonempty local file of a supported type."""
    source = Path(file_path).expanduser()
    if not source.is_file():
        raise DigitizerError(f"Expected a local file: {source}")
    if source.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise DigitizerError(f"Unsupported file type: {source.suffix or '(none)'}")
    if source.stat().st_size == 0:
        raise DigitizerError(f"Empty input file: {source}")
    return source
