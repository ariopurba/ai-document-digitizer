import hashlib
import json
from pathlib import Path

import pytest

from document_digitizer.config import DigitizerError
from document_digitizer.pipeline import process_file
from synthetic import make_samples

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def samples(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return make_samples(tmp_path_factory.mktemp("synthetic"))


@pytest.mark.parametrize("kind", ["text", "scan", "png", "jpg", "jpeg"])
def test_local_extraction(kind: str, samples: dict[str, Path], tmp_path: Path) -> None:
    source = samples[kind]
    digest = hashlib.sha256(source.read_bytes()).digest()
    result = process_file(source, tmp_path)
    markdown = (result / "content.md").read_text(encoding="utf-8")
    data = json.loads((result / "content.json").read_text(encoding="utf-8"))
    assert "seedlings need light and water" in markdown.lower()
    assert data["origin"]["filename"] == source.name
    assert data["texts"] and data["texts"][0]["prov"]
    assert len(data["pages"]) == (2 if kind == "text" else 1)
    if kind == "text":
        assert markdown.index("Plant growth") < markdown.index("Observation journal")
        table = data["tables"][0]["data"]
        assert (table["num_rows"], table["num_cols"]) == (3, 3)
        assert {"Bean", "Pea"} <= {cell["text"] for cell in table["table_cells"]}
        assert "| Bean" in markdown
    assert hashlib.sha256(source.read_bytes()).digest() == digest


def test_damaged_pdf(tmp_path: Path) -> None:
    source = tmp_path / "damaged.pdf"
    source.write_bytes(b"%PDF-1.4\ninvalid")
    with pytest.raises(DigitizerError, match="damaged.pdf"):
        process_file(source, tmp_path / "out")
    assert not (tmp_path / "out" / "damaged").exists()
