# Arabic text layers: what common PDF extractors return

Born-digital pages of the benchmark (8 Dubai law pages, 8 MOHRE half spreads), scored like the OCR engines
(standard normalization). Ground truth: the glyph-by-glyph rebuild of bench/pdf_gt.py.

| Extractor | Document | Pages | CER | Word recall (any order) | Reversed-ligature signatures |
|---|---|---|---|---|---|
| pdftotext 26.04.0 | dubai-law-7-2025 | 8 | 15.0% | 69.9% | 55 |
| pdftotext 26.04.0 | mohre-labour-law-33-2021 | 8 | 21.2% | 58.9% | 112 |
| pdftotext 26.04.0 -layout | dubai-law-7-2025 | 8 | 18.7% | 69.9% | 55 |
| pdftotext 26.04.0 -layout | mohre-labour-law-33-2021 | 8 | 17.4% | 58.9% | 112 |
| PyMuPDF 1.28.2 get_text | dubai-law-7-2025 | 8 | 16.6% | 83.9% | 57 |
| PyMuPDF 1.28.2 get_text | mohre-labour-law-33-2021 | 8 | 18.5% | 72.6% | 147 |
| pdfplumber 0.11.10 extract_text | dubai-law-7-2025 | 8 | 78.8% | 9.2% | 76 |
| pdfplumber 0.11.10 extract_text | mohre-labour-law-33-2021 | 8 | 76.2% | 14.5% | 0 |
| pdfplumber 0.11.10 extract_text(char_dir_render='rtl') | dubai-law-7-2025 | 8 | 7.6% | 73.4% | 63 |
| pdfplumber 0.11.10 extract_text(char_dir_render='rtl') | mohre-labour-law-33-2021 | 8 | 10.4% | 71.5% | 146 |
| pypdf 6.19.0 extract_text | dubai-law-7-2025 | 8 | 10.7% | 96.4% | 0 |
| pypdf 6.19.0 extract_text | mohre-labour-law-33-2021 | 0 | n/a | n/a | n/a |
| pdfminer.six 20260107 extract_text | dubai-law-7-2025 | 8 | 78.1% | 9.2% | 77 |
| pdfminer.six 20260107 extract_text | mohre-labour-law-33-2021 | 0 | n/a | n/a | n/a |
