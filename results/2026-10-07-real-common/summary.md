# Arabic OCR benchmark, run 2026-10-07-real-common

- Generated 2026-10-07T10:36 on Apple M5 Pro, 64 GB RAM, macOS 26.5.1.
- 44 page images scored. Ground truth: the dataset's human transcription (real scans).
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
| easyocr | easyocr 1.7.2, torch 2.14.1 | mps | lang ar, boxes -> rtl_lines | 3.0 |
| paddleocr | paddleocr 3.7.0, paddlepaddle 3.3.1 | cpu | det PP-OCRv5_server_det, rec arabic_PP-OCRv5_mobile_rec | 2.1 |
| surya | surya-ocr 0.22.1 | llamacpp (Metal) | datalab-to/surya-ocr-2 GGUF, full_page=True | 3.1 |
| tesseract | tesseract 5.5.2 | cpu | tessdata ara, psm 3 | 0.0 |

## Main table (full set)

| Engine | Pages | Failures | CER real scans | WER real scans | CER all | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|---|
| surya | 44 | 0 | 3.9% | 6.5% | 3.9% | 96.1% | 14.7 |
| apple-livetext | 44 | 0 | 5.0% | 8.4% | 5.0% | 95.2% | 0.3 |
| apple-vision | 44 | 0 | 8.1% | 12.1% | 8.1% | 96.4% | 0.5 |
| easyocr | 44 | 0 | 18.7% | 31.1% | 18.7% | 80.9% | 3.6 |
| tesseract | 44 | 0 | 19.7% | 43.0% | 19.7% | 76.5% | 0.8 |
| paddleocr | 44 | 0 | 33.5% | 44.3% | 33.5% | 61.7% | 16.0 |

## Small set (same pages for every engine, includes API engines)

| Engine | Pages | Failures | CER | WER | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|
| apple-vision | 10 | 0 | 3.5% | 5.5% | 96.2% | 0.4 |
| surya | 10 | 0 | 4.3% | 6.4% | 95.4% | 11.7 |
| apple-livetext | 10 | 0 | 4.9% | 7.7% | 94.2% | 0.3 |
| easyocr | 10 | 0 | 17.3% | 34.1% | 75.0% | 2.4 |
| tesseract | 10 | 0 | 20.7% | 49.3% | 72.5% | 0.6 |
| paddleocr | 10 | 0 | 42.9% | 51.1% | 50.4% | 21.4 |

## CER by condition

| Engine | Yarmouk scans (printed Wikipedia, 300 dpi) | Misraj scans | Misraj photos, one page | Misraj photos, open book (two pages) |
|---|---|---|---|---|
| surya | 0.6% | 3.3% | 15.7% | 2.0% |
| apple-livetext | 3.9% | 4.2% | 9.9% | 5.3% |
| apple-vision | 1.9% | 3.6% | 8.5% | 52.5% |
| easyocr | 15.9% | 12.4% | 19.8% | 55.2% |
| tesseract | 18.5% | 11.8% | 38.1% | 30.9% |
| paddleocr | 51.1% | 13.5% | 26.1% | 55.0% |

## Effect of normalization (mean CER, all pages)

raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.

| Engine | CER raw | CER standard | CER aggressive |
|---|---|---|---|
| surya | 6.5% | 3.9% | 3.2% |
| apple-livetext | 8.2% | 5.0% | 4.2% |
| apple-vision | 11.3% | 8.1% | 7.4% |
| easyocr | 20.2% | 18.7% | 11.6% |
| tesseract | 21.1% | 19.7% | 21.2% |
| paddleocr | 34.6% | 33.5% | 29.0% |

## Diagnostics

- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.
- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).
- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order.
- Empty outputs: pages where the engine returned no text and no error; they score CER = WER = 100%.

| Engine | Pages with output | Reading-order suspects | Visual-order suspects | Number recall | Empty outputs |
|---|---|---|---|---|---|
| surya | 44 | 0 | 0 | 97.2% | 0 |
| apple-livetext | 44 | 2 | 0 | 92.8% | 0 |
| apple-vision | 44 | 3 | 0 | 94.3% | 0 |
| easyocr | 44 | 1 | 0 | 73.9% | 0 |
| tesseract | 44 | 6 | 0 | 32.1% | 0 |
| paddleocr | 44 | 1 | 0 | 28.9% | 4 |

## Failures

None.

## Three typical errors, side by side

Removed from the published copy: this section quotes ground-truth and OCR text, which this repository does not redistribute. `bench.score` writes it again when you score your own run.
