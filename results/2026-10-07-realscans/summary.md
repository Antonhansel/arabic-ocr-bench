# Arabic OCR benchmark, run 2026-10-07-realscans

- Generated 2026-10-07T10:38 on Apple M5 Pro, 64 GB RAM, macOS 26.5.1.
- 96 page images scored. Ground truth: the dataset's human transcription (real scans).
- Normalization preset `standard`: nfkc=True, diacritics=True, tatweel=True, alef=True, alef_maqsura=True, persian=True, ta_marbuta=False, digits=True, punctuation=unify, symbols=True.
- CER and WER are means over pages; a failed page counts as empty output (CER = WER = 100%).
- Word recall (any order) = share of ground-truth words found in the output, ignoring order.
- s/page = median wall time per page once the model is loaded (load time listed separately).

## Engines

| Engine | Version | Device | Settings | Load s |
|---|---|---|---|---|
| apple-vision | macOS Version 26.5.1 (Build 25F80), VNRecognizeTextRequest revision 3 | Apple Neural Engine / GPU (system managed) | accurate, ar-SA, language correction on | 0.0 |
| easyocr | easyocr 1.7.2, torch 2.14.1 | mps | lang ar, boxes -> rtl_lines | 3.0 |
| paddleocr | paddleocr 3.7.0, paddlepaddle 3.3.1 | cpu | det PP-OCRv5_server_det, rec arabic_PP-OCRv5_mobile_rec | 2.1 |
| surya | surya-ocr 0.22.1 | llamacpp (Metal) | datalab-to/surya-ocr-2 GGUF, full_page=True | 3.1 |
| tesseract | tesseract 5.5.2 | cpu | tessdata ara, psm 3 | 0.0 |

## Main table (full set)

| Engine | Pages | Failures | CER real scans | WER real scans | CER all | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|---|
| surya | 44 | 0 | 3.9% | 6.5% | 3.9% | 96.1% | 14.7 |
| apple-vision | 96 | 0 | 5.9% | 9.3% | 5.9% | 96.1% | 0.5 |
| tesseract | 96 | 0 | 19.8% | 48.2% | 19.8% | 77.8% | 0.8 |
| easyocr | 96 | 0 | 20.0% | 32.2% | 20.0% | 80.4% | 3.7 |
| paddleocr | 96 | 0 | 36.8% | 48.0% | 36.8% | 55.6% | 34.3 |

## Small set (same pages for every engine, includes API engines)

| Engine | Pages | Failures | CER | WER | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|
| apple-vision | 10 | 0 | 3.5% | 5.5% | 96.2% | 0.4 |
| surya | 10 | 0 | 4.3% | 6.4% | 95.4% | 11.7 |
| easyocr | 10 | 0 | 17.3% | 34.1% | 75.0% | 2.4 |
| tesseract | 10 | 0 | 20.7% | 49.3% | 72.5% | 0.6 |
| paddleocr | 10 | 0 | 42.9% | 51.1% | 50.4% | 21.4 |

## CER by condition

| Engine | Yarmouk scans (printed Wikipedia, 300 dpi) | Misraj scans | Misraj photos, one page | Misraj photos, open book (two pages) |
|---|---|---|---|---|
| surya | 0.6% | 3.3% | 15.7% | 2.0% |
| apple-vision | 2.7% | 4.5% | 8.5% | 52.5% |
| tesseract | 19.6% | 15.9% | 38.1% | 30.9% |
| easyocr | 20.1% | 16.2% | 19.8% | 55.2% |
| paddleocr | 52.2% | 16.2% | 26.1% | 55.0% |

## Effect of normalization (mean CER, all pages)

raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.

| Engine | CER raw | CER standard | CER aggressive |
|---|---|---|---|
| surya | 6.5% | 3.9% | 3.2% |
| apple-vision | 9.8% | 5.9% | 5.4% |
| tesseract | 20.8% | 19.8% | 22.7% |
| easyocr | 21.2% | 20.0% | 12.1% |
| paddleocr | 37.7% | 36.8% | 31.3% |

## Diagnostics

- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.
- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).
- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order.
- Empty outputs: pages where the engine returned no text and no error; they score CER = WER = 100%.

| Engine | Pages with output | Reading-order suspects | Visual-order suspects | Number recall | Empty outputs |
|---|---|---|---|---|---|
| surya | 44 | 0 | 0 | 97.2% | 0 |
| apple-vision | 96 | 4 | 0 | 94.2% | 0 |
| tesseract | 96 | 23 | 0 | 43.5% | 0 |
| easyocr | 96 | 4 | 0 | 78.8% | 0 |
| paddleocr | 96 | 1 | 0 | 26.3% | 14 |

## Failures

None.

## Three typical errors, side by side

Removed from the published copy: this section quotes ground-truth and OCR text, which this repository does not redistribute. `bench.score` writes it again when you score your own run.
