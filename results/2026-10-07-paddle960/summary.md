# Arabic OCR benchmark, run 2026-10-07-paddle960

- Generated 2026-10-07T11:02 on Apple M5 Pro, 64 GB RAM, macOS 26.5.1.
- 96 page images scored. Ground truth: the dataset's human transcription (real scans).
- Normalization preset `standard`: nfkc=True, diacritics=True, tatweel=True, alef=True, alef_maqsura=True, persian=True, ta_marbuta=False, digits=True, punctuation=unify, symbols=True.
- CER and WER are means over pages; a failed page counts as empty output (CER = WER = 100%).
- Word recall (any order) = share of ground-truth words found in the output, ignoring order.
- s/page = median wall time per page once the model is loaded (load time listed separately).

## Engines

| Engine | Version | Device | Settings | Load s |
|---|---|---|---|---|
| paddleocr-max960 | paddleocr 3.7.0, paddlepaddle 3.3.1 | cpu | det PP-OCRv5_server_det, rec arabic_PP-OCRv5_mobile_rec, text_det_limit_type=max, text_det_limit_side_len=960 | 1.5 |

## Main table (full set)

| Engine | Pages | Failures | CER real scans | WER real scans | CER all | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|---|
| paddleocr-max960 | 96 | 0 | 22.1% | 36.2% | 22.1% | 67.1% | 10.7 |

## Small set (same pages for every engine, includes API engines)

| Engine | Pages | Failures | CER | WER | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|
| paddleocr-max960 | 10 | 0 | 19.7% | 33.8% | 67.2% | 6.9 |

## CER by condition

| Engine | Yarmouk scans (printed Wikipedia, 300 dpi) | Misraj scans | Misraj photos, one page | Misraj photos, open book (two pages) |
|---|---|---|---|---|
| paddleocr-max960 | 22.5% | 17.5% | 24.0% | 57.5% |

## Effect of normalization (mean CER, all pages)

raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.

| Engine | CER raw | CER standard | CER aggressive |
|---|---|---|---|
| paddleocr-max960 | 23.0% | 22.1% | 13.6% |

## Diagnostics

- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.
- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).
- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order.

| Engine | Pages with output | Reading-order suspects | Visual-order suspects | Number recall |
|---|---|---|---|---|
| paddleocr-max960 | 96 | 1 | 0 | 27.8% |

## Failures

None.

## Three typical errors, side by side

Removed from the published copy: this section quotes ground-truth and OCR text, which this repository does not redistribute. `bench.score` writes it again when you score your own run.
