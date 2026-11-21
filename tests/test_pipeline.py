from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from docling_core.types.doc import DoclingDocument

from document_digitizer.config import DigitizerError
from document_digitizer.exporter import export_document
from document_digitizer.pipeline import process_file
from document_digitizer.validator import validate_source


def test_missing_input(tmp_path: Path) -> None:
    with pytest.raises(DigitizerError, match="Expected a local file"):
        validate_source(tmp_path / "missing.pdf")


def test_directory_input(tmp_path: Path) -> None:
    with pytest.raises(DigitizerError, match="Expected a local file"):
        validate_source(tmp_path)


def test_unsupported_input(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("text")
    with pytest.raises(DigitizerError, match="Unsupported file type"):
        validate_source(source)


def test_empty_input(tmp_path: Path) -> None:
    source = tmp_path / "scan.pdf"
    source.touch()
    with pytest.raises(DigitizerError, match="Empty input"):
        validate_source(source)


def test_accept_uppercase_extension(tmp_path: Path) -> None:
    source = tmp_path / "PHOTO.JPEG"
    source.write_bytes(b"x")
    assert validate_source(source) == source


def test_existing_result_is_preserved(tmp_path: Path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_bytes(b"x")
    destination = tmp_path / "output" / "sample"
    destination.mkdir(parents=True)
    previous = destination / "content.md"
    previous.write_text("first result")
    with patch("document_digitizer.pipeline.extract_document") as extract:
        with pytest.raises(DigitizerError, match="already exists"):
            process_file(source, destination.parent)
        extract.assert_not_called()
    assert previous.read_text() == "first result"


def test_export_failure_leaves_no_result(tmp_path: Path) -> None:
    doc = Mock(spec=DoclingDocument)
    doc.export_to_markdown.return_value = "lesson"
    doc.save_as_json.side_effect = OSError("disk full")
    with pytest.raises(OSError, match="disk full"):
        export_document(doc, tmp_path / "result")
    assert list(tmp_path.iterdir()) == []


def test_empty_export(tmp_path: Path) -> None:
    with pytest.raises(DigitizerError, match="empty Markdown"):
        export_document(DoclingDocument(name="empty"), tmp_path / "empty")
    assert list(tmp_path.iterdir()) == []
