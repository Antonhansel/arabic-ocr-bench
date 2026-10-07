# Arabic OCR benchmark, run 2026-10-07-real10-all

- Generated 2026-10-07T10:37 on Apple M5 Pro, 64 GB RAM, macOS 26.5.1.
- 9 page images scored. Ground truth: the dataset's human transcription (real scans).
- Normalization preset `standard`: nfkc=True, diacritics=True, tatweel=True, alef=True, alef_maqsura=True, persian=True, ta_marbuta=False, digits=True, punctuation=unify, symbols=True.
- CER and WER are means over pages; a failed page counts as empty output (CER = WER = 100%).
- Word recall (any order) = share of ground-truth words found in the output, ignoring order.
- s/page = median wall time per page once the model is loaded (load time listed separately).
- Scored with `--common`: only the pages that every engine finished, so all engines are compared on the same pages.

## Engines

| Engine | Version | Device | Settings | Load s |
|---|---|---|---|---|
| apple-livetext | macOS Version 26.5.1 (Build 25F80), VisionKit ImageAnalyzer | Apple Neural Engine / GPU (system managed) | text, locale ar-SA, Apple's reading order | 0.0 |
| apple-vision | macOS Version 26.5.1 (Build 25F80), VNRecognizeTextRequest revision 3 | Apple Neural Engine / GPU (system managed) | accurate, ar-SA, language correction on | 0.0 |
| docling-easyocr | docling 2.134.0 | mps | EasyOcrOptions(lang=[ar], mode=FULL_PAGE) | 7.4 |
| docling-rapidocr | docling 2.134.0 | mps | RapidOcrOptions(lang=[arabic], backend onnxruntime, mode=FULL_PAGE) | 4.4 |
| docling-tesseract | docling 2.134.0 | mps | TesseractCliOcrOptions(lang=[ara], mode=FULL_PAGE) | 4.0 |
| easyocr | easyocr 1.7.2, torch 2.14.1 | mps | lang ar, boxes -> rtl_lines | 3.5 |
| paddleocr | paddleocr 3.7.0, paddlepaddle 3.3.1 | cpu | det PP-OCRv5_server_det, rec arabic_PP-OCRv5_mobile_rec | 1.3 |
| surya | surya-ocr 0.22.1 | llamacpp (Metal) | datalab-to/surya-ocr-2 GGUF, full_page=True | 2.8 |
| tesseract | tesseract 5.5.2 | cpu | tessdata ara, psm 3 | 0.0 |

## Main table (full set)

| Engine | Pages | Failures | CER real scans | WER real scans | CER all | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|---|
| apple-vision | 9 | 0 | 3.5% | 5.5% | 3.5% | 96.1% | 0.4 |
| surya | 9 | 0 | 4.4% | 6.5% | 4.4% | 95.1% | 13.2 |
| apple-livetext | 9 | 0 | 5.0% | 7.8% | 5.0% | 93.8% | 0.3 |
| easyocr | 9 | 0 | 17.7% | 33.3% | 17.7% | 76.1% | 2.1 |
| tesseract | 9 | 0 | 22.1% | 52.5% | 22.1% | 71.6% | 0.6 |
| docling-tesseract | 9 | 0 | 23.4% | 53.6% | 23.4% | 71.2% | 1.8 |
| docling-rapidocr | 9 | 0 | 44.3% | 56.6% | 44.3% | 44.7% | 0.9 |
| paddleocr | 9 | 0 | 45.5% | 53.0% | 45.5% | 48.2% | 30.8 |
| docling-easyocr | 9 | 0 | 61.3% | 82.5% | 61.3% | 63.4% | 3.3 |

## Small set (same pages for every engine, includes API engines)

| Engine | Pages | Failures | CER | WER | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|
| apple-vision | 9 | 0 | 3.5% | 5.5% | 96.1% | 0.4 |
| surya | 9 | 0 | 4.4% | 6.5% | 95.1% | 13.2 |
| apple-livetext | 9 | 0 | 5.0% | 7.8% | 93.8% | 0.3 |
| easyocr | 9 | 0 | 17.7% | 33.3% | 76.1% | 2.1 |
| tesseract | 9 | 0 | 22.1% | 52.5% | 71.6% | 0.6 |
| docling-tesseract | 9 | 0 | 23.4% | 53.6% | 71.2% | 1.8 |
| docling-rapidocr | 9 | 0 | 44.3% | 56.6% | 44.7% | 0.9 |
| paddleocr | 9 | 0 | 45.5% | 53.0% | 48.2% | 30.8 |
| docling-easyocr | 9 | 0 | 61.3% | 82.5% | 63.4% | 3.3 |

## CER by condition

| Engine | Yarmouk scans (printed Wikipedia, 300 dpi) | Misraj scans | Misraj photos, one page |
|---|---|---|---|
| apple-vision | 1.3% | 3.9% | 7.4% |
| surya | 0.5% | 8.3% | 6.5% |
| apple-livetext | 4.4% | 4.0% | 7.7% |
| easyocr | 18.3% | 15.9% | 18.9% |
| tesseract | 20.2% | 16.6% | 34.2% |
| docling-tesseract | 17.9% | 25.0% | 32.2% |
| docling-rapidocr | 33.2% | 47.3% | 61.9% |
| paddleocr | 78.9% | 20.5% | 16.2% |
| docling-easyocr | 62.6% | 60.6% | 59.9% |

## Effect of normalization (mean CER, all pages)

raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.

| Engine | CER raw | CER standard | CER aggressive |
|---|---|---|---|
| apple-vision | 8.6% | 3.5% | 2.0% |
| surya | 7.6% | 4.4% | 3.0% |
| apple-livetext | 9.9% | 5.0% | 3.5% |
| easyocr | 20.5% | 17.7% | 7.9% |
| tesseract | 24.6% | 22.1% | 24.6% |
| docling-tesseract | 25.6% | 23.4% | 25.0% |
| docling-rapidocr | 45.7% | 44.3% | 36.4% |
| paddleocr | 47.9% | 45.5% | 41.1% |
| docling-easyocr | 62.8% | 61.3% | 59.7% |

## Diagnostics

- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.
- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).
- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order.
- Empty outputs: pages where the engine returned no text and no error; they score CER = WER = 100%.

| Engine | Pages with output | Reading-order suspects | Visual-order suspects | Number recall | Empty outputs |
|---|---|---|---|---|---|
| apple-vision | 9 | 0 | 0 | 96.0% | 0 |
| surya | 9 | 0 | 0 | 96.3% | 0 |
| apple-livetext | 9 | 0 | 0 | 94.6% | 0 |
| easyocr | 9 | 0 | 0 | 73.2% | 0 |
| tesseract | 9 | 2 | 0 | 30.9% | 0 |
| docling-tesseract | 9 | 2 | 0 | 43.9% | 0 |
| docling-rapidocr | 9 | 0 | 0 | 4.5% | 0 |
| paddleocr | 9 | 0 | 0 | 12.9% | 2 |
| docling-easyocr | 9 | 2 | 0 | 57.0% | 0 |

## Failures

None.

## Three typical errors, side by side

Removed from the published copy: this section quotes ground-truth and OCR text, which this repository does not redistribute. `bench.score` writes it again when you score your own run.
