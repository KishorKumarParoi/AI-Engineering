import os
import logfire
from pypdf import PdfReader
from app.config import settings


def _parse_with_doc_ai(file_path: str) -> str:
    """Attempt extraction using Google Cloud Document AI."""
    from google.cloud import documentai
    from google.api_core.client_options import ClientOptions

    location = settings.GCP_DOC_AI_LOCATION or "us"
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    name = client.processor_path(
        settings.PROJECT_ID,
        location,
        settings.GCP_DOC_AI_PROCESSOR_ID,
    )

    with open(file_path, "rb") as image:
        image_content = image.read()

    raw_document = documentai.RawDocument(
        content=image_content, mime_type="application/pdf"
    )
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)

    document = result.document
    return document.text or ""


def parse_pdf(file_path: str) -> str:
    """
    Extract text from a PDF.
    First tries Google Cloud Document AI if processor is configured.
    Falls back to pypdf + pdfplumber locally.
    """
    with logfire.span("PDF Parsing", filename=file_path):
        # 1. Try Document AI if configured
        if settings.PROJECT_ID and settings.GCP_DOC_AI_PROCESSOR_ID:
            try:
                with logfire.span("Google Document AI Extraction", processor=settings.GCP_DOC_AI_PROCESSOR_ID):
                    text = _parse_with_doc_ai(file_path)
                    if text and text.strip():
                        logfire.info(f"Document AI extracted {len(text)} characters from {file_path}.")
                        return text
            except Exception as e:
                logfire.warning(f"Document AI extraction failed: {e}. Falling back to local PDF parser.")

        # 2. Local parser fallback (pypdf + pdfplumber)
        try:
            reader = PdfReader(file_path)
            total_pages = len(reader.pages)
            logfire.info(f"PDF has {total_pages} pages (local parsing).")

            text_parts: list[str] = []
            blank_pages: list[int] = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    text_parts.append(text)
                else:
                    blank_pages.append(i + 1)

            # Fallback: use pdfplumber for any pages pypdf returned blank
            if blank_pages:
                logfire.info(f"pypdf returned blank on pages {blank_pages} — retrying with pdfplumber.")
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        for page_num in blank_pages:
                            page = pdf.pages[page_num - 1]
                            fallback_text = page.extract_text() or ""
                            if fallback_text.strip():
                                text_parts.append(fallback_text)
                except Exception as plumber_err:
                    logfire.warning(f"pdfplumber fallback failed: {plumber_err}")

            full_text = "\n".join(text_parts)

            if not full_text.strip():
                logfire.warning(f"No text extracted from {file_path}. File may be fully image-based.")
            else:
                logfire.info(f"Extracted {len(full_text)} characters from {file_path}.")

            return full_text

        except Exception as e:
            logfire.error(f"PDF Parse Failed for {file_path}: {e}")
            raise

