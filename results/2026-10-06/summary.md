# Arabic OCR benchmark, run 2026-10-06

- Generated 2026-10-06T15:29 on Apple M5 Pro, 64 GB RAM, macOS 26.5.1.
- 56 page images scored. Ground truth: PDF text layer (born-digital) or the rendered text (synthetic).
- Normalization preset `standard`: nfkc=True, diacritics=True, tatweel=True, alef=True, alef_maqsura=True, persian=True, ta_marbuta=False, digits=True, punctuation=unify, symbols=True.
- CER and WER are means over pages; a failed page counts as empty output (CER = WER = 100%).
- Word recall (any order) = share of ground-truth words found in the output, ignoring order.
- s/page = median wall time per page once the model is loaded (load time listed separately).

## Engines

| Engine | Version | Device | Settings | Load s |
|---|---|---|---|---|
| apple-vision | macOS Version 26.5.1 (Build 25F80), VNRecognizeTextRequest revision 3 | Apple Neural Engine / GPU (system managed) | accurate, ar-SA, language correction on | 0.0 |
| docling-easyocr | docling 2.134.0 | mps | EasyOcrOptions(lang=[ar], mode=FULL_PAGE) | 8.2 |
| docling-rapidocr | docling 2.134.0 | mps | RapidOcrOptions(lang=[arabic], backend onnxruntime, mode=FULL_PAGE) | 4.1 |
| docling-tesseract | docling 2.134.0 | mps | TesseractCliOcrOptions(lang=[ara], mode=FULL_PAGE) | 3.9 |
| easyocr | easyocr 1.7.2, torch 2.14.1 | mps | lang ar, boxes -> rtl_lines | 4.6 |
| gemini-3.5-flash | gemini-3.5-flash | Google API | gemini-3.5-flash, default temperature, thinking low, max 8192 output tokens | 0.0 |
| paddleocr | paddleocr 3.7.0, paddlepaddle 3.3.1 | cpu | det PP-OCRv5_server_det, rec arabic_PP-OCRv5_mobile_rec | 3.3 |
| surya | surya-ocr 0.22.1 | llamacpp (Metal) | datalab-to/surya-ocr-2 GGUF, full_page=True | 3.0 |
| tesseract | tesseract 5.5.2 | cpu | tessdata ara, psm 3 | 0.0 |

## Main table (full set)

| Engine | Pages | Failures | CER born-digital | WER born-digital | CER synthetic | WER synthetic | CER all | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|---|---|---|
| apple-vision | 56 | 0 | 0.3% | 0.3% | 0.2% | 0.7% | 0.2% | 99.5% | 0.4 |
| surya | 56 | 0 | 1.6% | 2.9% | 0.1% | 0.3% | 1.0% | 99.7% | 11.9 |
| easyocr | 56 | 0 | 5.4% | 13.0% | 2.8% | 9.6% | 4.3% | 89.8% | 3.2 |
| paddleocr | 56 | 0 | 6.4% | 13.1% | 8.9% | 18.9% | 7.5% | 87.0% | 35.8 |
| tesseract | 56 | 0 | 10.6% | 16.2% | 9.7% | 12.4% | 10.2% | 88.9% | 0.7 |
| docling-tesseract | 56 | 0 | 11.9% | 16.8% | 8.1% | 11.6% | 10.3% | 89.8% | 1.1 |
| docling-rapidocr | 56 | 0 | 23.5% | 30.6% | 11.7% | 20.3% | 18.5% | 76.6% | 0.7 |
| docling-easyocr | 56 | 0 | 47.8% | 60.8% | 48.1% | 61.7% | 47.9% | 72.8% | 2.0 |

## Small set (same pages for every engine, includes API engines)

| Engine | Pages | Failures | CER | WER | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|
| apple-vision | 10 | 0 | 0.2% | 0.6% | 99.4% | 0.4 |
| gemini-3.5-flash | 10 | 0 | 0.4% | 0.5% | 100.0% | 7.8 |
| surya | 10 | 0 | 0.9% | 1.2% | 100.0% | 12.1 |
| easyocr | 10 | 0 | 4.4% | 12.6% | 88.7% | 3.4 |
| paddleocr | 10 | 0 | 8.8% | 18.1% | 83.5% | 48.8 |
| tesseract | 10 | 0 | 10.5% | 13.3% | 87.0% | 0.8 |
| docling-tesseract | 10 | 0 | 13.9% | 18.2% | 86.4% | 1.2 |
| docling-rapidocr | 10 | 0 | 16.1% | 26.2% | 75.3% | 0.7 |
| docling-easyocr | 10 | 0 | 49.3% | 62.9% | 68.7% | 2.0 |

## CER by condition

| Engine | Born-digital 300 dpi | Born-digital 150 dpi | Synthetic clean | Synthetic scan | Dubai law (Word) | MOHRE booklet (InDesign) |
|---|---|---|---|---|---|---|
| apple-vision | 0.2% | 0.4% | 0.2% | 0.2% | 0.3% | 0.2% |
| surya | 1.0% | 2.3% | 0.1% | 0.1% | 2.9% | 0.4% |
| easyocr | 5.0% | 5.8% | 2.8% | 2.8% | 5.1% | 5.7% |
| paddleocr | 6.4% | 6.3% | 7.0% | 10.9% | 7.4% | 5.3% |
| tesseract | 11.9% | 9.3% | 9.5% | 10.0% | 7.2% | 14.1% |
| docling-tesseract | 12.0% | 11.8% | 10.2% | 6.0% | 9.9% | 14.0% |
| docling-rapidocr | 23.2% | 23.9% | 12.4% | 11.0% | 29.4% | 17.7% |
| docling-easyocr | 47.2% | 48.4% | 49.8% | 46.4% | 50.3% | 45.3% |

## CER by font (synthetic pages, clean and scan)

| Engine | noto-naskh | tahoma | times-new-roman |
|---|---|---|---|
| apple-vision | 0.1% | 0.3% | 0.1% |
| surya | 0.1% | 0.1% | 0.0% |
| easyocr | 3.1% | 2.5% | 2.9% |
| paddleocr | 10.0% | 11.0% | 5.8% |
| tesseract | 9.8% | 7.8% | 11.6% |
| docling-tesseract | 10.8% | 6.0% | 7.5% |
| docling-rapidocr | 6.2% | 11.8% | 17.1% |
| docling-easyocr | 50.2% | 46.8% | 47.3% |

## Effect of normalization (mean CER, all pages)

raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.

| Engine | CER raw | CER standard | CER aggressive |
|---|---|---|---|
| apple-vision | 4.8% | 0.2% | 0.2% |
| surya | 6.3% | 1.0% | 1.0% |
| easyocr | 10.9% | 4.3% | 1.9% |
| paddleocr | 12.3% | 7.5% | 5.7% |
| tesseract | 15.3% | 10.2% | 9.4% |
| docling-tesseract | 15.1% | 10.3% | 8.8% |
| docling-rapidocr | 22.9% | 18.5% | 16.4% |
| docling-easyocr | 51.8% | 47.9% | 45.8% |
| gemini-3.5-flash | 8.1% | 0.4% | 0.4% |

## Diagnostics

- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.
- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).
- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order.

| Engine | Pages with output | Reading-order suspects | Visual-order suspects | Number recall |
|---|---|---|---|---|
| apple-vision | 56 | 0 | 0 | 99.4% |
| surya | 56 | 0 | 0 | 99.9% |
| easyocr | 56 | 0 | 0 | 92.6% |
| paddleocr | 56 | 1 | 0 | 13.4% |
| tesseract | 56 | 2 | 0 | 73.3% |
| docling-tesseract | 56 | 1 | 0 | 72.1% |
| docling-rapidocr | 56 | 1 | 0 | 8.8% |
| docling-easyocr | 56 | 5 | 0 | 89.0% |
| gemini-3.5-flash | 10 | 0 | 0 | 100.0% |

## Failures

None.

## Three typical errors, side by side

Removed from the published copy: this section quotes ground-truth and OCR text, which this repository does not redistribute. `bench.score` writes it again when you score your own run.
