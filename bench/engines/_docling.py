"""Shared Docling setup: image input, standard PDF pipeline (layout model,
table model, reading order), OCR on the full page with the given backend,
everything else at Docling defaults (OCR at scale 3, i.e. the page is
resampled to 216 dpi whatever the input resolution).

Text export: export_to_text() with body AND furniture layers, because page
headers and footers are printed on the page and are in the ground truth
(Docling hides furniture by default). Two export artifacts are removed: the
"- " Docling puts in front of list items and the "|" table-cell separators.
"""
import re

import docling
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, ImageFormatOption
from docling_core.types.doc import ContentLayer

try:
    from importlib.metadata import version
    DOCLING_VERSION = version("docling")
except Exception:  # pragma: no cover
    DOCLING_VERSION = getattr(docling, "__version__", "unknown")


def build(ocr_options) -> DocumentConverter:
    opts = PdfPipelineOptions(do_ocr=True, ocr_options=ocr_options)
    conv = DocumentConverter(format_options={InputFormat.IMAGE: ImageFormatOption(pipeline_options=opts)})
    conv.initialize_pipeline(InputFormat.IMAGE)
    return conv


def to_text(conv: DocumentConverter, image_path: str) -> str:
    res = conv.convert(image_path)
    text = res.document.export_to_text(included_content_layers={ContentLayer.BODY, ContentLayer.FURNITURE})
    text = re.sub(r"(?m)^- ", "", text)
    return text.replace("|", " ")


def device(conv: DocumentConverter) -> str:
    try:
        import torch
        return "mps" if torch.backends.mps.is_available() else "cpu"
    except Exception:
        return "cpu"
