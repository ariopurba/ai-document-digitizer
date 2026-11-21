"""Settings shared by the pipeline and its callers."""

OCR_LANGUAGE = "en"
SUPPORTED_SUFFIXES = frozenset({".pdf", ".jpg", ".jpeg", ".png"})


class DigitizerError(Exception):
    """A failure that a caller can report to the document owner."""
