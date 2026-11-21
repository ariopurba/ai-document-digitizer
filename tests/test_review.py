from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from document_digitizer.review import render_source_page

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "demo" / "synthetic-plant-growth.pdf"


def test_source_preview_tracks_selected_page() -> None:
    contents = SAMPLE.read_bytes()
    first = render_source_page(SAMPLE.name, contents, 1)
    second = render_source_page(SAMPLE.name, contents, 2)
    assert first != second
    with Image.open(BytesIO(first)) as image:
        assert max(image.size) == 1200


@pytest.mark.integration
def test_sample_conversion_stays_in_sync_with_review() -> None:
    streamlit = pytest.importorskip("streamlit.testing.v1")
    app = streamlit.AppTest.from_file(str(ROOT / "app.py"), default_timeout=90)
    app.run()
    assert app.button[0].proto.disabled

    app.radio[0].set_value("Try sample").run()
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert "2 pages" in app.success[0].value
    assert any("| Bean" in item.value for item in app.markdown)
    assert len(app.get("download_button")) == 2

    app.selectbox[0].set_value(2).run()
    assert not app.exception and not app.error
    assert any("Observation journal" in item.value for item in app.markdown)
    assert all("Seedlings need" not in item.value for item in app.markdown)

    app.radio[0].set_value("Upload a file").run()
    assert not app.selectbox and not app.get("download_button")
