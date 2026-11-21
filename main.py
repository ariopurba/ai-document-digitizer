"""Command-line entry point for single-document extraction."""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from document_digitizer.config import DigitizerError


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Digitize one PDF, JPG, JPEG or PNG locally."
    )
    parser.add_argument(
        "--input", required=True, type=Path, help="Source document path"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("output"), help="Output root"
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s"
    )
    log = logging.getLogger("document_digitizer")
    log.setLevel(logging.INFO)
    try:
        from document_digitizer.pipeline import process_file

        log.info("Processing %s", args.input)
        destination = process_file(args.input, args.output)
    except (DigitizerError, OSError, ImportError) as exc:
        log.error("%s", exc)
        return 1
    log.info("Saved Markdown and JSON in %s", destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
