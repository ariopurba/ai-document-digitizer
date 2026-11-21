from pathlib import Path

from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import (
    DocumentConverter,
    ImageFormatOption,
    PdfFormatOption,
)
from docling_core.types.doc import DoclingDocument

from .config import OCR_LANGUAGE, DigitizerError
from .validator import validate_source


def extract_document(file_path: Path | str) -> DoclingDocument:
    """Convert one local PDF or photo into Docling's ordered document tree."""
    source = validate_source(file_path)
    options = PdfPipelineOptions(
        do_ocr=True,
        do_table_structure=True,
        enable_remote_services=False,
        ocr_options=RapidOcrOptions(backend="onnxruntime", lang=[OCR_LANGUAGE]),
    )
    try:
        converter = DocumentConverter(
            allowed_formats=[InputFormat.PDF, InputFormat.IMAGE],
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=options),
                InputFormat.IMAGE: ImageFormatOption(pipeline_options=options),
            },
        )
        result = converter.convert(source)
    except Exception as exc:
        raise DigitizerError(f"Docling could not process {source.name}: {exc}") from exc

    try:
        if result.status != ConversionStatus.SUCCESS:
            errors = "; ".join(error.error_message for error in result.errors)
            raise DigitizerError(f"{source.name}: {result.status.value}. {errors}")
        return result.document
    finally:
        result.input.release()
