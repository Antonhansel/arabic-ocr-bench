# Arabic OCR benchmark, run 2026-10-07-openrouter

- Generated 2026-10-07T12:07 on Apple M5 Pro, 64 GB RAM, macOS 26.5.1.
- 10 page images scored. Ground truth: the dataset's human transcription (real scans).
- Normalization preset `standard`: nfkc=True, diacritics=True, tatweel=True, alef=True, alef_maqsura=True, persian=True, ta_marbuta=False, digits=True, punctuation=unify, symbols=True.
- CER and WER are means over pages; a failed page counts as empty output (CER = WER = 100%).
- Word recall (any order) = share of ground-truth words found in the output, ignoring order.
- s/page = median wall time per page once the model is loaded (load time listed separately).

## Engines

| Engine | Version | Device | Settings | Load s |
|---|---|---|---|---|
| or-claude-opus-5.5 | anthropic/claude-opus-5.5 | OpenRouter API | anthropic/claude-opus-5.5, default temperature, reasoning low, max 16384 output tokens | 0.0 |
| or-gemini-3.1-pro | google/gemini-3.1-pro-preview | OpenRouter API | google/gemini-3.1-pro-preview, default temperature, reasoning low, max 16384 output tokens | 0.0 |
| or-gemini-3.8-flash | google/gemini-3.8-flash | OpenRouter API | google/gemini-3.8-flash, default temperature, reasoning low, max 16384 output tokens | 0.0 |
| or-gpt-6.1-sol | openai/gpt-6.1-sol | OpenRouter API | openai/gpt-6.1-sol, default temperature, reasoning low, max 16384 output tokens | 0.0 |
| or-mistral-medium-3.5 | mistralai/mistral-medium-3-5 | OpenRouter API | mistralai/mistral-medium-3-5, default temperature, reasoning low, max 16384 output tokens | 0.0 |
| or-qwen3.8-max | qwen/qwen3.8-max-prime | OpenRouter API | qwen/qwen3.8-max-prime, default temperature, reasoning low, max 16384 output tokens | 0.0 |

## Main table (full set)

| Engine | Pages | Failures | CER real scans | WER real scans | CER all | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|---|

## Small set (same pages for every engine, includes API engines)

| Engine | Pages | Failures | CER | WER | Word recall (any order) | s/page |
|---|---|---|---|---|---|---|
| or-gemini-3.8-flash | 10 | 0 | 1.9% | 3.0% | 97.6% | 7.9 |
| or-claude-opus-5.5 | 10 | 0 | 2.8% | 3.5% | 97.7% | 11.8 |
| or-gemini-3.1-pro | 10 | 0 | 3.1% | 4.3% | 97.7% | 7.2 |
| or-qwen3.8-max | 10 | 0 | 4.0% | 13.5% | 93.8% | 16.5 |
| or-gpt-6.1-sol | 10 | 0 | 4.3% | 10.4% | 91.0% | 17.7 |
| or-mistral-medium-3.5 | 10 | 0 | 41.6% | 58.1% | 47.3% | 57.7 |

## CER by condition

| Engine | Yarmouk scans (printed Wikipedia, 300 dpi) | Misraj scans | Misraj photos, one page |
|---|---|---|---|

## Effect of normalization (mean CER, all pages)

raw = invisible characters and whitespace only; standard = default; aggressive = standard + ta marbuta to ha + punctuation removed.

| Engine | CER raw | CER standard | CER aggressive |
|---|---|---|---|
| or-claude-opus-5.5 | 6.6% | 2.8% | 1.6% |
| or-gemini-3.1-pro | 7.0% | 3.1% | 1.9% |
| or-gemini-3.8-flash | 6.6% | 1.9% | 0.6% |
| or-gpt-6.1-sol | 6.5% | 4.3% | 3.2% |
| or-mistral-medium-3.5 | 45.0% | 41.6% | 39.7% |
| or-qwen3.8-max | 6.1% | 4.0% | 4.2% |

## Diagnostics

- Reading-order suspects: pages with word recall (any order) of 85% or more but WER of 30% or more.
- Visual-order suspects: pages where reversing each output line halves the CER (engine returned left-to-right order).
- Number recall: share of the ground-truth numbers (article numbers, years, amounts) found in the output, any order.

| Engine | Pages with output | Reading-order suspects | Visual-order suspects | Number recall |
|---|---|---|---|---|
| or-claude-opus-5.5 | 10 | 0 | 0 | 95.1% |
| or-gemini-3.1-pro | 10 | 0 | 0 | 96.0% |
| or-gemini-3.8-flash | 10 | 0 | 0 | 96.4% |
| or-gpt-6.1-sol | 10 | 0 | 0 | 94.5% |
| or-mistral-medium-3.5 | 10 | 0 | 0 | 74.5% |
| or-qwen3.8-max | 10 | 1 | 0 | 69.1% |

## Failures

None.

## Three typical errors, side by side

Each example is the ground-truth line whose error rate is closest to the page CER, after normalization.
