"""Streamlit entry point for local document conversion and review."""

import hashlib
import logging
import sys
from pathlib import Path
from time import perf_counter

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from document_digitizer.config import SUPPORTED_SUFFIXES, DigitizerError

log = logging.getLogger("document_digitizer.ui")
SAMPLE = ROOT / "demo" / "synthetic-plant-growth.pdf"

STYLE = """
<style>
.stMainBlockContainer {max-width: 1240px; padding-top: 4rem;}
.st-key-intro {
    background: #173f36;
    border: 1px solid #173f36;
    border-radius: 22px;
    padding: clamp(1.4rem, 4vw, 2.6rem);
}
.st-key-intro h1, .st-key-intro p {color: #fffdf3;}
.st-key-intro h1 {
    font-size: clamp(2rem, 4.7vw, 4rem);
    line-height: 1.06;
    letter-spacing: -.045em;
    padding: 0;
}
.st-key-intro p {max-width: 56ch; margin: .15rem 0;}
.st-key-source-page, .st-key-extracted-page {
    background: #fffdf8;
    border: 1px solid #dbe2d7;
    border-radius: 16px;
    padding: 1rem 1.2rem;
}
.st-key-source-page img {border: 1px solid #dbe2d7; border-radius: 5px;}
.st-key-extracted-page [data-testid="stMarkdownContainer"] {overflow-x: auto;}
[data-testid="stFileUploaderDropzone"] {border: 1px dashed #a7b8a7;}
@media (max-width: 700px) {
    .st-key-page-pair [data-testid="stHorizontalBlock"] {flex-wrap: wrap;}
    .st-key-page-pair [data-testid="stColumn"] {min-width: 100%;}
}
</style>
"""


def main() -> None:
    st.set_page_config(page_title="AI Document Digitizer", layout="wide")
    st.html(STYLE)

    with st.container(key="intro"):
        st.title("AI Document Digitizer", anchor=False)
        st.markdown(
            "Turn scanned pages into editable text and tables. "
            "Review both side by side, right on your Mac."
        )

    st.subheader("Choose a document", anchor=False)
    mode = st.radio(
        "Document source", ("Upload a file", "Try sample"), horizontal=True
    )
    if mode == "Try sample":
        name, contents = SAMPLE.name, SAMPLE.read_bytes()
        st.caption("Synthetic plant-growth worksheet · 2 scanned pages")
    else:
        upload = st.file_uploader(
            "PDF or image",
            type=sorted(suffix[1:] for suffix in SUPPORTED_SUFFIXES),
        )
        name, contents = (upload.name, upload.getvalue()) if upload else ("", b"")

    source_key = (mode, name, hashlib.sha256(contents).hexdigest())
    if st.session_state.get("document_source") != source_key:
        st.session_state["document_source"] = source_key
        st.session_state.pop("review_result", None)
        st.session_state.pop("review_page", None)

    if st.button("Convert document", type="primary", disabled=not name) and name:
        st.session_state.pop("review_result", None)
        st.session_state.pop("review_page", None)
        started = perf_counter()
        with st.spinner("Extracting text and tables locally…", show_time=True):
            try:
                from document_digitizer.review import convert_upload

                result = convert_upload(name, contents)
            except (DigitizerError, OSError) as exc:
                log.warning("Conversion failed for %r: %s", name, exc)
                st.error("Couldn’t convert the document. Check the file and try again.")
                with st.expander("Error details"):
                    st.code(str(exc), language=None)
            except Exception:
                log.exception("Could not prepare document for review")
                st.error("Couldn’t prepare the result. See the terminal for details.")
            else:
                st.session_state["review_result"] = (
                    result, perf_counter() - started
                )

    saved = st.session_state.get("review_result")
    if saved is None:
        return

    from document_digitizer.review import render_source_page

    result, elapsed = saved
    pages = sorted(result.document.pages)
    page_label = "page" if len(pages) == 1 else "pages"
    st.success(f"Conversion complete · {len(pages)} {page_label} · {elapsed:.1f} s")
    st.text(name)

    stem = Path(name).stem
    download_md, download_json = st.columns(2)
    download_md.download_button(
        "Download Markdown",
        result.markdown,
        file_name=f"{stem}.md",
        mime="text/markdown",
        on_click="ignore",
        width="stretch",
    )
    download_json.download_button(
        "Download JSON",
        result.json,
        file_name=f"{stem}.json",
        mime="application/json",
        on_click="ignore",
        width="stretch",
    )
    if not pages:
        st.info("This result has no page information. Use the full downloads.")
        return

    st.subheader("Review by page", anchor=False)
    page = st.selectbox(
        "Page", pages, key="review_page", format_func=lambda number: f"Page {number}",
        width=220,
    )

    with st.container(key="page-pair"):
        left, right = st.columns(2, gap="medium")
        with left, st.container(key="source-page"):
            st.markdown("#### Source page")
            try:
                preview = render_source_page(name, contents, page)
            except (OSError, ValueError, RuntimeError):
                log.exception("Could not render source page %s", page)
                st.error("Couldn’t display this source page.")
            else:
                st.image(preview, width="stretch", caption=f"Source page {page}")
        with right, st.container(key="extracted-page"):
            st.markdown("#### Extracted content")
            markdown = result.document.export_to_markdown(page_no=page).strip()
            if markdown:
                st.markdown(markdown)
            else:
                st.info("No text or tables were extracted on this page.")


if __name__ == "__main__":
    main()
