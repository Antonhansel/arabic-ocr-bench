# Arabic OCR benchmark, run 2026-10-07-livetext

- Generated 2026-10-07T10:36 on Apple M5 Pro, 64 GB RAM, macOS 26.5.1.
- 152 page images scored. Ground truth: PDF text layer (born-digital) or the rendered text (synthetic) or the dataset's human transcription (real scans).
- Normalization preset `standard`: nfkc=True, diacritics=True, tatweel=True, alef=True, alef_maqsura=True, persian=True, ta_marbuta=False, digits=True, punctuation=unify, symbols=True.
- CER and WER are means over pages; a failed page counts as empty output (CER = WER = 100%).
- Word recall (any order) = share of ground-truth words found in the output, ignoring order.
- s/page = median wall time per page once the model is loaded (load time listed separately).

## Engines

| Engine | Version | Device | Settings | Load s |
|---|---|---|---|---|
| apple-livetext | macOS Version 26.5.1 (Build 25F80), VisionKit ImageAnalyzer | Apple Neural Engine / GPU (system managed) | text, locale ar-SA, Apple's reading order | 0.0 |

## Main table (full set)

| Engine | Pages | Failures | CER born-digital | WER born-digital | CER synthetic | WER synthetic | CER real scans | WER real scans | CER all | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| apple-livetext | 152 | 0 | 1.8% | 3.2% | 0.2% | 0.7% | 4.8% | 8.1% | 3.4% | 97.0% | 0.3 |

## Small set (same pages for every engine, includes API engines)

| Engine | Pages | Failures | CER | WER | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|
| apple-livetext | 20 | 0 | 2.6% | 4.2% | 96.8% | 0.3 |

## CER by condition

| Engine | Born-digital 300 dpi | Born-digital 150 dpi | Synthetic clean | Synthetic scan | Dubai law (Word) | MOHRE booklet (InDesign) | Yarmouk scans (printed Wikipedia, 300 dpi) | Misraj scans | Misraj photos, one page | Misraj photos, open book (two pages) |
|---|---|---|---|---|---|---|---|---|---|---|
| apple-livetext | 1.7% | 1.8% | 0.3% | 0.1% | 0.4% | 3.1% | 2.7% | 6.6% | 9.9% | 5.3% |

## CER by font (synthetic pages, clean and scan)

| Engine | noto-naskh | tahoma | times-new-roman |
|---|---|---|---|
| apple-livetext | 0.1% | 0.5% | 0.0% |

## Effect of normalization (mean CER, all pages)

raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.

| Engine | CER raw | CER standard | CER aggressive |
|---|---|---|---|
| apple-livetext | 7.6% | 3.4% | 3.0% |

## Diagnostics

- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.
- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).
- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order.

| Engine | Pages with output | Reading-order suspects | Visual-order suspects | Number recall |
|---|---|---|---|---|
| apple-livetext | 152 | 7 | 0 | 95.2% |

## Failures

None.

## Three typical errors, side by side

Removed from the published copy: this section quotes ground-truth and OCR text, which this repository does not redistribute. `bench.score` writes it again when you score your own run.
