# Arabic OCR benchmark, run 2026-10-07-gemini-real

- Generated 2026-10-07T11:18 on Apple M5 Pro, 64 GB RAM, macOS 26.5.1.
- 10 page images scored. Ground truth: the dataset's human transcription (real scans).
- Normalization preset `standard`: nfkc=True, diacritics=True, tatweel=True, alef=True, alef_maqsura=True, persian=True, ta_marbuta=False, digits=True, punctuation=unify, symbols=True.
- CER and WER are means over pages; a failed page counts as empty output (CER = WER = 100%).
- Word recall (any order) = share of ground-truth words found in the output, ignoring order.
- s/page = median wall time per page once the model is loaded (load time listed separately).

## Engines

| Engine | Version | Device | Settings | Load s |
|---|---|---|---|---|
| gemini-3.5-flash | gemini-3.5-flash | Google API | gemini-3.5-flash, default temperature, thinking low, max 8192 output tokens | 0.0 |

## Main table (full set)

| Engine | Pages | Failures | CER real scans | WER real scans | CER all | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|---|

## Small set (same pages for every engine, includes API engines)

| Engine | Pages | Failures | CER | WER | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|
| gemini-3.5-flash | 10 | 0 | 1.6% | 2.9% | 97.3% | 9.2 |

## CER by condition

| Engine | Yarmouk scans (printed Wikipedia, 300 dpi) | Misraj scans | Misraj photos, one page |
|---|---|---|---|

## Effect of normalization (mean CER, all pages)

raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.

| Engine | CER raw | CER standard | CER aggressive |
|---|---|---|---|
| gemini-3.5-flash | 6.1% | 1.6% | 0.5% |

## Diagnostics

- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.
- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).
- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order.

| Engine | Pages with output | Reading-order suspects | Visual-order suspects | Number recall |
|---|---|---|---|---|
| gemini-3.5-flash | 10 | 0 | 0 | 95.1% |

## Failures

None.

## Three typical errors, side by side

Each example is the ground-truth line whose error rate is closest to the page CER, after normalization.
