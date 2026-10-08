# arabic-ocr-bench

A small evaluation harness that measures OCR engines on Arabic pages from public UAE
documents and from real scans and photos of printed pages, with a ground truth you can
check.

It backs the write-up [Arabic OCR in 2026: 14 engines on UAE laws and real
scans](https://arelion.dev/arabic-ocr/). This repository holds the code, the list of
pages and the scores. It holds no page image, no PDF and no transcription:
`scripts/download_data.py` fetches them from their publishers (see
[Data sources and licenses](#data-sources-and-licenses)).

## Results (2026-10-07)

Not every engine read every page: Surya read 44 of the 96 real pages, Docling 9, and
the paid models 10. Nothing is extrapolated: each table below only uses pages that
every engine in it read (`bench.score --common`). Per-page numbers are in the
`results.csv` next to each summary.

| Results folder | Pages | Engines | What it answers |
|---|---|---|---|
| [`2026-10-07-real-common`](results/2026-10-07-real-common/summary.md) | 44 real scans and photos (all 10 photos) | Tesseract, Apple Vision, Apple Live Text, EasyOCR, PaddleOCR, Surya | The main comparison on real pages |
| [`2026-10-07-real96`](results/2026-10-07-real96/summary.md) | 96 real scans and photos | Tesseract, Apple Vision, Apple Live Text, EasyOCR, PaddleOCR (Surya: 44 pages only) | The five engines that finished every real page. Compare Surya in `real-common`. |
| [`2026-10-07-v0-livetext`](results/2026-10-07-v0-livetext/summary.md) | 56 law and synthetic pages | the 9 local engines, Gemini on the 10-page small set | Born-digital UAE law pages and synthetic pages |
| [`2026-10-07-real10-all`](results/2026-10-07-real10-all/summary.md) | 9 real pages | the 9 local engines | The only real pages Docling read (from the `dev-real-10` run) |
| [`2026-10-07-real-api`](results/2026-10-07-real-api/summary.md) | 44 real pages, API engines on the 10-page real small set | the 6 engines above, Gemini 3.5 Flash, 6 OpenRouter models | The paid AI models against the others on the same 10 real pages ("Small set" table) |
| [`2026-10-07-openrouter`](results/2026-10-07-openrouter/summary.md) | 10 real pages | Gemini 3.8 Flash, Gemini 3.1 Pro, GPT-6.1 Sol, Claude Opus 5.5, Qwen3.8 Max, Mistral Medium 3.5 | The OpenRouter run (the cost of every call went to the engine logs, which are not published) |
| [`2026-10-07-gemini-real`](results/2026-10-07-gemini-real/summary.md) | 10 real pages | Gemini 3.5 Flash | Gemini's run on the real small set (token counts went to its log, not published) |
| [`2026-10-07-paddle960`](results/2026-10-07-paddle960/summary.md) | 96 real pages | PaddleOCR with each page shrunk to 960 px | The fix for PaddleOCR's blank pages |
| [`paddle-diag`](results/paddle-diag/report.json) | 3 Yarmouk scans | PaddleOCR text detector, 4 settings | Why PaddleOCR returns blank pages |
| [`pdf-text-layers`](results/pdf-text-layers/summary.md) | 16 law pages | 7 PDF text extractors | Copy-paste versus OCR on born-digital PDFs |
| [`2026-10-06`](results/2026-10-06/summary.md) | 56 law and synthetic pages | 8 engines, Gemini on the small set | The first run, before Live Text existed in the bench |

Mean CER on the 44 real pages (lower is better): Surya 3.9%, Apple Live Text 5.0%,
Apple Vision 8.1%, EasyOCR 18.7%, Tesseract 19.7%, PaddleOCR 33.5%.

Not measured: Surya on 52 of the 96 real pages, Docling on
real pages (except the 9 above). Gemini 3.5 Flash read the 10-page real small set in a
separate run: 1.6% CER, against 3.5% for Apple Vision and 4.3% for Surya on the same pages.
Six OpenRouter models read the same 10 pages: Gemini 3.8 Flash 1.9% (0.3 cents a page),
Claude Opus 5.5 2.8%, Gemini 3.1 Pro 3.1%, Qwen3.8 Max 4.0%, GPT-6.1 Sol 4.3%, Mistral
Medium 3.5 41.6% (it often stops after a few lines). Mistral Large 4 returned no text on
the one test page (16,384 tokens spent, nothing written) and was left out of the run.

Each results folder holds `results.csv` (one row per page and engine: scores, seconds,
error) and `summary.md`. The last section of a summary quotes ground-truth and OCR
lines, so it is removed from the published copies. OCR outputs, raw records and engine
logs are not published.

Related write-ups: [Arabic OCR in 2026](https://arelion.dev/arabic-ocr/),
[PaddleOCR on Arabic scans](https://arelion.dev/guides/paddleocr-arabic/),
[Surya OCR on Arabic](https://arelion.dev/guides/surya-ocr-arabic/),
[Arabic PDF to text](https://arelion.dev/guides/arabic-pdf-to-text/).

## What it measures

For every engine and every page image:

- **CER**: character edit distance (insertions + deletions + substitutions) divided by the
  number of ground-truth characters, spaces and punctuation included. Not clipped: an
  engine that invents text can score above 100%.
- **WER**: the same on words. Words are split on spaces and punctuation, so `دبي.` and
  `دبي .` are the same word.
- **Word recall (any order)**: share of ground-truth words found in the output, ignoring
  order. High recall with a high WER means the words were read but put in the wrong order
  (columns, label and value rows, line order). This is the reading-order check.
- **Number recall**: share of the ground-truth numbers (article numbers, years, amounts)
  found in the output, any order. A model can read every word and drop every number.
- **Visual-order check**: CER after reversing every output line. If that halves the CER,
  the engine returned left-to-right (visual) order instead of Arabic logical order.
- **Time**: wall time per page once the model is loaded, and the load time.
- **Failures**: an engine that fails to install, fails to load, crashes on a page or
  exceeds its page timeout is recorded with the error. A failed page scores as empty
  output (CER = WER = 100%) in the means.

Scores are computed after Arabic normalization. Three presets
([`bench/normalize.py`](bench/normalize.py)); every step is a switch:

| Step | raw | standard (default) | aggressive |
|---|---|---|---|
| Remove invisible characters (ZWJ, ZWNJ, bidi marks), collapse whitespace | yes | yes | yes |
| Presentation forms to base letters (NFKC: `ﻻ` to `لا`) | no (NFC) | yes | yes |
| Remove harakat, tanween, shadda, sukun, dagger alef | no | yes | yes |
| Remove tatweel (kashida) `ـ` | no | yes | yes |
| Alef forms `أ إ آ ٱ` to `ا` | no | yes | yes |
| Alef maqsura `ى` to ya `ي` | no | yes | yes |
| Persian look-alikes `ی ک ە` to `ي ك ه` | no | yes | yes |
| Arabic-Indic and Persian digits to `0-9` | no | yes | yes |
| Punctuation: `،` to `,`, `؛` to `;`, `؟` to `?`, quotes and dashes unified | no | yes | removed |
| List-separator dots `·` `•` to `.` (Wikipedia lists use `·`; engines return `.` or `•`) | no | yes | removed |
| Ornate brackets around Quran verses `﴿ ﴾` to `( )` | no | yes | removed |
| Symbols (`◄ ● ■`) removed | no | yes | yes |
| Ta marbuta `ة` to ha `ه` | no | no | yes |

The report shows CER under all three presets per engine, so the effect of normalization is
visible. To rescore a run with another preset: `.venv/bin/python -m bench.score results/<run> --norm raw`.
Rescoring reads the run's OCR outputs, so it works on runs you made yourself, not on the
published folders.

## What it does not measure

- Handwriting, stamps, signatures, ID cards, invoices or forms: none. I found no public
  dataset with a permissive license and page-level text for invoices, forms or stamped
  government documents.
- Tables as structures (no TEDS), layout detection, or key-value extraction.
- In v0, the "scan" pages are synthetic degradations (rotation, blur, grey paper, noise,
  JPEG). Real scans and photos of printed pages come with dataset v1, from other documents than the
  UAE laws (see [Dataset v1](#dataset-v1-real-scans)).
- Speed on other hardware: all timings come from one Apple M5 Pro (64 GB). Engines run on
  different units (CPU, Apple GPU through MPS or Metal, the Neural Engine for Apple
  Vision, a remote API for Gemini), so speed is "this machine, default settings".
- Tuned settings: every engine runs with its documented defaults for Arabic, see
  [Engines](#engines). A tuned engine can do better.

## Dataset v0

56 page images, built by [`bench/dataset.py`](bench/dataset.py), listed in
[`data/manifest.csv`](data/manifest.csv) (page id, image and ground-truth paths, kind,
degradation, dpi, font, source document, source URL, page in the source, small-set flag,
notes, license). The PDFs, the page images and the ground-truth texts are not in the
repository: `scripts/download_data.py` downloads the two PDFs, and
`scripts/build_dataset.sh` renders the pages and writes the ground truth to `data/gt/`.

| Kind | Source | Pages | Images |
|---|---|---|---|
| born-digital | Dubai Law No. (7) of 2025 on contracting activities, Dubai Legislation Portal (Word 2016 PDF, Times New Roman, harakat on many words) | 8 | 16 (150 and 300 dpi) |
| born-digital | Federal Decree-Law No. (33) of 2021 on labour relations, MOHRE booklet (InDesign PDF, A5 pages laid out as two-page spreads, cut in two; kashida justification) | 8 | 16 (150 and 300 dpi) |
| synthetic | 4 passages taken from other pages of the same two laws, rendered on A4 at 300 dpi with Noto Naskh Arabic (OFL), Tahoma and Times New Roman (macOS), clean and with a light scan degradation | 4 texts x 3 fonts x 2 | 24 |

A subset of 10 images (`small_set=1` in the manifest: both documents, both resolutions, all
three fonts) is used for paid or slow engines; the report has a separate table where every
engine is scored on these same 10 images.

### Ground truth for synthetic pages

The rendered text is the ground truth. Rendering uses Pillow with HarfBuzz shaping
(raqm), which does no font fallback: a character missing from the font is drawn as an
empty box while the ground truth keeps it. Geeza Pro, the macOS Arabic system font, has
no glyph for `0-9`, brackets, quotes or the colon, and was replaced by Tahoma after the
10-page run showed every engine "missing" those numbers. `check_coverage` in
`bench/dataset.py` now refuses to render a passage with any character the font lacks.
The "scan" degradation: rotation of 0.5 to 1.5 degrees, Gaussian blur 0.9 px, grey
levels 25-230, Gaussian noise sigma 10, JPEG quality 70 (parameters per page in the
manifest `notes` column).

### Ground truth for born-digital pages

The PDF text layer is the ground truth, but common extractors (pdftotext, PyMuPDF,
pdfium) break Arabic from these PDFs: they reverse right-to-left text character by
character, so a ligature glyph mapped to two letters comes out reversed. `المقاولات`
becomes `المقاوالت`, `المادة` becomes `املادة`, `في` becomes `يف`.
[`bench/pdf_gt.py`](bench/pdf_gt.py) reads glyphs with pdfminer, keeps each glyph's
Unicode string as one unit, rebuilds each visual line right to left and flips Latin and
number islands back (unit tests in `tests/test_pdf_gt.py`).

Checks before a page is kept (`gt_problems` in `bench/dataset.py`): no unmapped or
private-use glyphs, no rotated text, at least 60% Arabic letters, no presentation-form
characters, at most two reversed-ligature signatures (`اإل`, `األ`, standalone `يف`...),
at least 40 words. Dropped pages are listed in `data/dropped_pages.txt` (none in v0).
I also compared six test pages line by line with the rendered image (Dubai pages 1, 2
and 14; MOHRE 8R, 12R and 38L).

Known defects of this ground truth:

- Harakat are sometimes attached to the neighbouring letter (`حيثمُا` for `حيثُما`). The
  standard preset removes harakat, so this only affects the `raw` scores.
- Line order follows the page top to bottom; on the Dubai definition pages a label and
  its definition share a line, as they do visually.
- Page headers, footers and page numbers are in the ground truth because they are printed
  on the page.

## Dataset v1: real scans

v1 adds pages that went through a scanner or a camera, with a transcription made by
people, from two public datasets ([`bench/realscans.py`](bench/realscans.py)). They are
listed in the same manifest with `kind=real-scan`, `degradation` = `scanned` or
`photo` (phone or overhead book camera), and `layout` = `single`, or `multi` for a photo of
an open book (two pages), where the transcription reads the right page, then the left one.

| Source | License | Pages | What they are |
|---|---|---|---|
| [NOD](https://doi.org/10.5281/zenodo.5068735), Yarmouk collection (Hegghammer 2021), seeded from the Yarmouk Arabic OCR Dataset (Abu Doush et al. 2018) | CC BY 4.0 | 50 | Arabic Wikipedia articles printed on paper and scanned in colour at 300 dpi. NOD's clean colour scans (`yarmouk_01_col`) only, not its 42 versions with synthetic noise. Every second article of the 100, in ID order. |
| [Misraj-DocOCR](https://huggingface.co/datasets/Misraj/Misraj-DocOCR), revision `7177bf7` | Apache-2.0 | 47 selected of 400 | Scans of printed books, journals and magazines (37) and photos of printed pages (10: 6 of one page, 4 of an open book). |

The Misraj card says its 400 pages are "real + synthetic". I classified every page by
eye: 147 pages share eight fixed image sizes and are all synthetic renders (tilted
pages, stacked-paper effects, vignettes, highlighter strokes); the other 253 were
checked on thumbnails, then every kept page again at three times its native resolution.
Kept: pages with clear scan or camera evidence (irregular ink and broken strokes from
print, paper tone, scanner borders, blur, perspective). Left out: born-digital renders,
pages that are mostly pictures, tables of contents and indexes, and one page whose
transcription is LaTeX. Background statistics (share of pure white, noise) did not
separate a cleaned scan from a Word export, so the glyph check decided; it removed two
pages I had first kept. A third one went while I cut images for an article: a novel page
I had taken for a phone photo is a digital e-book page laid over a blurred cover picture,
saved as a low-quality JPEG. The 47 rows, with their uuid and capture type, are in
[`data/realscans_misraj.csv`](data/realscans_misraj.csv).

Ground truth:

- NOD: the dataset's plain-text file, one article per page, in logical order. Empty lines
  are removed.
- Misraj: the dataset's Markdown, turned into plain text by `md_to_text`: page numbers
  kept, tables read row by row in the order of the HTML cells, emphasis, headings,
  bullets and rules removed, watermarks (site names stamped on the scan) and image
  placeholders dropped. Unit tests in `tests/test_realscans.py`.
- Pages with less than 60% Arabic letters or fewer than 40 words are dropped and listed
  in `data/dropped_pages.txt` (one NOD article in v1). The two v0 checks aimed at broken
  PDF text layers (presentation forms, reversed ligatures) are not applied: these
  transcriptions rightly contain `ﷺ`, the ornate brackets `﴿ ﴾` around Quran verses, and
  village names such as `املوص`.
- 96 pages in the end: 49 NOD scans, 37 Misraj scans, 10 Misraj photos.

Images and transcriptions are downloaded by `scripts/download_data.py` (or by
`scripts/build_dataset.sh`, for any file still missing), checked against the published
checksums, and never committed (`data/external/`, `data/realscans/`): the transcriptions
belong to the datasets.

Known defects of this ground truth:

- Misraj transcriptions carry light edits: printed `لايلزمه` is transcribed `لا يلزمه`,
  printed `الشيء` becomes `الشي`. An engine that reads the print exactly loses a little.
- On the photos of open books the transcription reads the right page, then the left one.
  The report scores these 4 pages in their own column; word recall (any order) is the
  fair number there.
- On one photo (Misraj row 136) a strip of the facing page shows on the left edge and is
  not transcribed: an engine that reads it gets extra words.
- Misraj images are distributed without a resolution. Docling then assumes 72 dpi and
  enlarges each page three times before OCR (its default `scale=3`); the other engines
  ignore the missing value or estimate it. The NOD scans carry their 300 dpi.

## Data sources and licenses

The repository redistributes none of these files. `scripts/download_data.py` fetches
them from their publishers and checks them; `--dry-run` lists every file, its URL, its
license and its checksum without downloading anything.

| Source | Used for | License | Download |
|---|---|---|---|
| Dubai Law No. (7) of 2025 on contracting activities, [Dubai Legislation Portal](https://dlp.dubai.gov.ae) | 8 born-digital pages, 2 synthetic passages | None stated in the PDF (official UAE legislation) | 0.6 MB |
| Federal Decree-Law No. (33) of 2021 on labour relations, booklet of the Ministry of Human Resources and Emiratisation ([MOHRE](https://mohre.gov.ae)) | 8 born-digital pages, 2 synthetic passages | None stated in the PDF (official UAE legislation) | 0.6 MB |
| NOD, Noisy OCR Dataset, Yarmouk collection: Thomas Hegghammer (2021), Zenodo, [doi:10.5281/zenodo.5068735](https://doi.org/10.5281/zenodo.5068735). Seeded from the Yarmouk Arabic OCR Dataset (Abu Doush, AlKhateeb and Gharibeh 2018). | 49 real scans | CC BY 4.0 | 42 MB (2 files of the record) |
| Misraj-DocOCR, [Misraj/Misraj-DocOCR](https://huggingface.co/datasets/Misraj/Misraj-DocOCR) at revision `7177bf7`. Cite: Hennara et al. (2025), "Baseer: A Vision-Language Model for Arabic Document-to-Markdown OCR", [arXiv:2509.18174](https://arxiv.org/abs/2509.18174). | 37 real scans, 10 photos | Apache-2.0 | 537 MB |
| Noto Naskh Arabic, The Noto Project Authors ([google/fonts](https://github.com/google/fonts/tree/main/ofl/notonaskharabic)), downloaded by `scripts/build_dataset.sh` | synthetic pages | SIL Open Font License 1.1 | 0.3 MB |

Licenses as checked on 2026-10-07: NOD on its Zenodo record, Misraj-DocOCR on its
dataset card at the pinned revision, Noto Naskh Arabic in the license file that comes
with the font. Neither law PDF states a license. Tahoma and Times New Roman ship with
macOS and are not downloaded. Every page in `data/manifest.csv` carries the license of
its source in the `license` column.

The law publishers give no checksum, so `bench/dataset.py` records the SHA-256 of the
copies behind the published results, and the download script warns when a file
differs. On 2026-10-07, a rebuild from law PDFs downloaded that day and from NOD and
Misraj files that match their published checksums gave the same manifest, ground truth
and page images as the published runs, byte for byte.

The OCR engines and model weights come with their own licenses (Surya's weights, for
example); check them before you use an engine in a product.

## Engines

| Engine | Adapter | Env | Settings |
|---|---|---|---|
| Tesseract 5 | [`tesseract.py`](bench/engines/tesseract.py) | core | CLI, `-l ara`, `--psm 3` |
| Apple Vision | [`apple_vision.py`](bench/engines/apple_vision.py) + [`tools/vision_ocr.swift`](tools/vision_ocr.swift) | core | `VNRecognizeTextRequest`, accurate, `ar-SA`, language correction on. `ar-SA` is listed as supported on macOS 26.5 (checked, not assumed). |
| Apple Live Text (added 2026-10-07) | [`apple_livetext.py`](bench/engines/apple_livetext.py) + [`tools/livetext_ocr.swift`](tools/livetext_ocr.swift) | core | VisionKit `ImageAnalyzer`, text only, locale `ar-SA`: the API behind Live Text in Preview, Photos and Safari. Text and reading order are Apple's own, no box sorting. `ar-SA` and `ars-SA` are listed on macOS 26.5. |
| EasyOCR | [`easyocr_engine.py`](bench/engines/easyocr_engine.py) | docling | `Reader(["ar"])`, MPS |
| PaddleOCR 3 | [`paddleocr_engine.py`](bench/engines/paddleocr_engine.py) | paddle | `PaddleOCR(lang="ar")`: PP-OCRv5 server detection + Arabic PP-OCRv5 mobile recognition, CPU |
| PaddleOCR 3, page shrunk (added 2026-10-07) | [`paddleocr_max960.py`](bench/engines/paddleocr_max960.py) | paddle | Same, plus `text_det_limit_type="max"`, `text_det_limit_side_len=960`: the long side of the page is 960 px for text detection. Fix for the blank pages, see [`tools/paddle_diag.py`](tools/paddle_diag.py). |
| Surya 0.22 | [`surya_engine.py`](bench/engines/surya_engine.py) | surya | surya-ocr-2 VLM, full-page mode, served by llama.cpp (Metal) |
| Docling + EasyOCR | [`docling_easyocr.py`](bench/engines/docling_easyocr.py) | docling | `EasyOcrOptions(lang=["ar"])`, full-page OCR |
| Docling + Tesseract | [`docling_tesseract.py`](bench/engines/docling_tesseract.py) | docling | `TesseractCliOcrOptions(lang=["ara"])`, full-page OCR |
| Docling + RapidOCR | [`docling_rapidocr.py`](bench/engines/docling_rapidocr.py) | docling | `RapidOcrOptions(lang=["arabic"])`, onnxruntime, full-page OCR |
| OpenRouter vision models (added 2026-10-07) | [`openrouter.py`](bench/engines/openrouter.py) + one `or_*.py` per model | core | Same prompt as Gemini, reasoning effort low, 16384 output tokens max, small set only, one call at a time. Models: Gemini 3.8 Flash, Gemini 3.1 Pro, GPT-6.1 Sol, Claude Opus 5.5, Qwen3.8 Max, Mistral Medium 3.5 (Mistral Large 4 is registered but returned no text on its test page). An empty answer cut by the token budget or an error counts as a failure. Key in the `OPENROUTER_API_KEY` environment variable. |
| Gemini 3.5 Flash (API) | [`gemini.py`](bench/engines/gemini.py) | core | REST, plain-text transcription prompt, default temperature, thinking level low, 8192 output tokens max; small set only, one call at a time. At temperature 0 one page ran past 240 s and timed out, so the run uses Google's default. Key in the `GEMINI_API_KEY` environment variable. |

Glue decisions that affect scores, applied the same way wherever they apply:

- Engines that return boxes without page order (EasyOCR, PaddleOCR, Apple Vision) go
  through one shared rule, [`bench/engines/_boxes.py`](bench/engines/_boxes.py): boxes
  that overlap vertically form a line, lines top to bottom, boxes right to left. No column
  detection. EasyOCR's own `paragraph=True` was tried on the first page and scored worse
  (CER 8.7% against 4.2%).
- Docling: text is exported with body and furniture layers (headers and footers are on
  the page); the `- ` list prefix and `|` table separators added by the export are
  removed. Docling resamples every page to 216 dpi before OCR (its default `scale=3`),
  using the DPI stored in the PNG (all dataset images carry it). Its EasyOCR backend
  drops words under confidence 0.5 (default `confidence_threshold`); standalone EasyOCR
  keeps every box.
- Surya: block HTML is stripped of tags.

## How to run

Tested on macOS 26.5 on Apple silicon only. The Apple engines need macOS, and the
scripts assume Homebrew in `/opt/homebrew` and a macOS arm64 build of llama.cpp.
Prerequisites (Homebrew): `tesseract tesseract-lang poppler fribidi`, `uv`, Xcode command
line tools (for `swiftc`). Everything else lands inside this folder.

```bash
git clone https://github.com/Antonhansel/arabic-ocr-bench.git
cd arabic-ocr-bench
scripts/setup_envs.sh              # .venv (core) + .venvs/{docling,paddle,surya}; "core" alone for a first look
scripts/fetch_surya.sh             # llama-server binary + Surya GGUF weights (~1.5 GB)
.venv/bin/python scripts/download_data.py --dry-run   # every input file: URL, license, checksum
.venv/bin/python scripts/download_data.py             # law PDFs, NOD and Misraj files (about 580 MB)
scripts/build_dataset.sh --limit 1 # 1 page, then --limit 10, then no flag for the full v0
scripts/build_dataset.sh --real 1  # full v0 + 1 real scan; no flag = full v0 + all real scans
.venv/bin/python -m pytest -q tests

# subset first: one page, then ten, then everything
.venv/bin/python -m bench.run --engines tesseract,apple-vision --limit 1 --out results/dev-1page
.venv/bin/python -m bench.run --limit 10 --out results/dev-10pages

# full run, detached, with a macOS notification when the DONE marker appears
OUT=results/$(date +%F); mkdir -p $OUT
OUT=$OUT WITH_GEMINI=1 nohup scripts/run_full.sh > $OUT/run.log 2>&1 & disown
nohup scripts/notify_on_done.sh $OUT/DONE > /dev/null 2>&1 & disown

# rescore without running OCR again
.venv/bin/python -m bench.score $OUT --norm standard
```

`setup_envs.sh` installs the newest versions listed in `envs/<env>.txt`, then overwrites
`envs/<env>.lock.txt` with what it installed (`git diff envs/` shows the drift). The
committed lock files hold the versions of the published runs. To install exactly those,
skip `setup_envs.sh` for that env:
`uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r envs/core.lock.txt`
(or `.venvs/<env>` with `envs/<env>.lock.txt`).

API engines are opt-in: they send the page images to a provider and cost money. They
read their key from the environment: `export GEMINI_API_KEY=...` for `gemini-3.5-flash`
(and `WITH_GEMINI=1`), `export OPENROUTER_API_KEY=...` for the `or-*` engines. Without
the key, the engine fails to load and every page is recorded as a failure.

`bench.run` options: `--engines a,b`, `--limit N` (the manifest is stratified, so the
first rows mix conditions), `--kind born-digital|synthetic|real-scan` (applied before
`--limit`), `--small` (small set only), `--resume` (skip pages already done), `--out`. Model caches go to `models/` (engine workers run with `HOME`,
`HF_HOME`, `EASYOCR_MODULE_PATH`, `PADDLE_PDX_CACHE_HOME` pointed there).

Outputs in `results/<run>/`: `results.csv` (page, engine, CER, WER, word recall,
reversed-line CER, CER and WER under the raw preset, CER under the aggressive preset,
seconds, error), `summary.md`, `engines.json` (versions, devices, load times),
`raw.jsonl`, `outputs/<engine>/<page>.txt` and `logs/`. `.gitignore` keeps all but
`results.csv` and `summary.md` out of git: the outputs hold OCR text, the logs hold
local paths, token counts and costs. The last section of `summary.md` quotes
ground-truth and OCR lines; remove it before you publish a summary.

`bench.score` options: `--norm raw|standard|aggressive`, and `--common` to keep only the
pages that every engine finished (engines limited to the small set, such as Gemini, do
not shrink that set). Use `--common` on any run that was stopped or merged from runs of
different sizes, otherwise the means compare engines on different pages.

### Re-run everything

The OCR outputs are not published, so a re-run starts from the engines. Every step
below can be stopped and resumed: `bench.run --resume` skips pages already in `raw.jsonl`.

```bash
cd arabic-ocr-bench
# 1. environments, Surya weights, inputs and dataset v0 + v1 (checked against checksums), tests
scripts/setup_envs.sh
scripts/fetch_surya.sh
.venv/bin/python scripts/download_data.py
scripts/build_dataset.sh
.venv/bin/python -m pytest -q tests

# 2. every default engine on all 152 images, then Gemini on the 20-image small set
#    (Gemini needs GEMINI_API_KEY; drop WITH_GEMINI=1 to skip it)
OUT=results/$(date +%F)-full; mkdir -p $OUT
OUT=$OUT WITH_GEMINI=1 nohup scripts/run_full.sh > $OUT/run.log 2>&1 & disown
nohup scripts/notify_on_done.sh $OUT/DONE > /dev/null 2>&1 & disown

# 3. score (run_full.sh scores at the end; rescore with --common if you stopped it early)
.venv/bin/python -m bench.score $OUT --common

# 4. copy-paste versus OCR on the law PDFs (its own throwaway env, see the tool's docstring)
uv venv /tmp/pdfx --python 3.12
uv pip install --python /tmp/pdfx/bin/python pymupdf pypdf pdfplumber pdfminer.six rapidfuzz
PYTHONPATH=. /tmp/pdfx/bin/python tools/pdf_text_layers.py results/pdf-text-layers
```

### Reproduce the 2026-10-07 tables

These are the exact commands behind the folders in [Results](#results-2026-10-07). They
write into the published folders, so `git diff` shows what changed on your machine.

```bash
# the real-scan run (no Gemini step): Surya read 44 of its 96 pages
mkdir -p results/2026-10-07-realscans
OUT=results/2026-10-07-realscans nohup scripts/run_full.sh --kind real-scan > results/2026-10-07-realscans/run.log 2>&1 & disown

# the 10-page dev run that holds Docling's only real pages (misraj-058 was later
# dropped from the manifest, so 9 pages are scored)
.venv/bin/python -m bench.run --kind real-scan --limit 10 --out results/dev-real-10

# Apple Live Text on all 152 images (46 s in total)
.venv/bin/python -m bench.run --out results/2026-10-07-livetext --engines apple-livetext

# merged views; combine_runs.sh copies outputs and records (nothing is re-run), then scores
scripts/combine_runs.sh results/2026-10-07-real-common results/2026-10-07-realscans results/2026-10-07-livetext
.venv/bin/python -m bench.score results/2026-10-07-real-common --common
scripts/combine_runs.sh results/2026-10-07-v0-livetext results/2026-10-06 results/2026-10-07-livetext
.venv/bin/python -m bench.score results/2026-10-07-v0-livetext --common
scripts/combine_runs.sh results/2026-10-07-real10-all results/dev-real-10 results/2026-10-07-livetext
.venv/bin/python -m bench.score results/2026-10-07-real10-all --common
scripts/combine_runs.sh results/2026-10-07-real96 results/2026-10-07-realscans results/2026-10-07-livetext

# Gemini 3.5 Flash on the 10-page real small set (needs GEMINI_API_KEY), then merged with the real pages
.venv/bin/python -m bench.run --out results/2026-10-07-gemini-real --engines gemini-3.5-flash --kind real-scan
# the six OpenRouter models on the same 10 pages (needs OPENROUTER_API_KEY)
.venv/bin/python -m bench.run --out results/2026-10-07-openrouter --kind real-scan \
  --engines or-gemini-3.8-flash,or-gemini-3.1-pro,or-gpt-6.1-sol,or-claude-opus-5.5,or-qwen3.8-max,or-mistral-medium-3.5
scripts/combine_runs.sh results/2026-10-07-real-api results/2026-10-07-realscans results/2026-10-07-livetext results/2026-10-07-gemini-real results/2026-10-07-openrouter
.venv/bin/python -m bench.score results/2026-10-07-real-api --common

# PaddleOCR blank pages: what the detector saw on two blank pages and one good page,
# then the 960 px fix on the 96 real pages
HOME=$PWD/models/home PADDLE_PDX_CACHE_HOME=$PWD/models/paddlex .venvs/paddle/bin/python \
  tools/paddle_diag.py results/paddle-diag data/realscans/yarmouk-1189.png \
  data/realscans/yarmouk-12866.png data/realscans/yarmouk-1569.png
.venv/bin/python -m bench.run --out results/2026-10-07-paddle960 --engines paddleocr-max960 --kind real-scan
```

`combine_runs.sh` takes the folders in order and later records win, so put the newer run
last. The `dev-*` folders are not committed.

## Code map

Every file starts with a docstring or comment that says what it does and how to call it.

| File | Role |
|---|---|
| [`bench/dataset.py`](bench/dataset.py) | Builds dataset v0 (renders the law PDFs at 150 and 300 dpi, synthetic pages), checks every ground truth, writes `data/manifest.csv`. `SOURCES` holds the law URLs, checksums and licenses. |
| [`bench/pdf_gt.py`](bench/pdf_gt.py) | Ground truth of born-digital PDF pages, rebuilt glyph by glyph in Arabic reading order |
| [`bench/realscans.py`](bench/realscans.py) | Dataset v1: downloads and checks NOD and Misraj, turns their transcriptions into plain text, adds the rows to the manifest |
| [`bench/run.py`](bench/run.py) | Runs engines on the manifest (one worker process per engine), writes `raw.jsonl` and `outputs/`, then scores |
| [`bench/worker.py`](bench/worker.py) | The worker: loads one engine in its own venv and answers page requests over stdin/stdout |
| [`bench/score.py`](bench/score.py) | Scores a results folder from saved outputs: `results.csv` and `summary.md` |
| [`bench/metrics.py`](bench/metrics.py) | CER, WER, word recall in any order, number recall, reversed-line CER |
| [`bench/normalize.py`](bench/normalize.py) | The three normalization presets, every step a switch |
| [`bench/engines/__init__.py`](bench/engines/__init__.py) | Engine registry: name, adapter module, venv, small-set flag, timeouts |
| `bench/engines/*.py` | One adapter per engine (see [Engines](#engines)); `_boxes.py` orders boxes right to left, `_docling.py` is the shared Docling setup |
| [`tools/vision_ocr.swift`](tools/vision_ocr.swift), [`tools/livetext_ocr.swift`](tools/livetext_ocr.swift) | Small Swift servers for Apple Vision and Apple Live Text, compiled on first use |
| [`tools/pdf_text_layers.py`](tools/pdf_text_layers.py) | Scores 7 PDF text extractors against the same ground truth as the OCR engines |
| [`tools/paddle_diag.py`](tools/paddle_diag.py) | Records what PaddleOCR's text detector sees under several settings, and saves its probability maps |
| [`scripts/setup_envs.sh`](scripts/setup_envs.sh) | Creates `.venv` and `.venvs/{docling,paddle,surya}` from `envs/*.txt` |
| [`scripts/fetch_surya.sh`](scripts/fetch_surya.sh) | Downloads the llama.cpp server and the Surya weights |
| [`scripts/download_data.py`](scripts/download_data.py) | Downloads the law PDFs and the NOD and Misraj files from their publishers and checks them; `--dry-run` lists them, `--only laws\|nod\|misraj` picks a group |
| [`scripts/build_dataset.sh`](scripts/build_dataset.sh) | Builds dataset v0 and v1 (`--limit N`, `--real N` for subsets) |
| [`scripts/run_full.sh`](scripts/run_full.sh) | Detached full run, resumable, writes a `DONE` marker; `WITH_GEMINI=1` adds Gemini |
| [`scripts/notify_on_done.sh`](scripts/notify_on_done.sh) | Waits for a `DONE` marker, then notifies (macOS notification, sound, voice) |
| [`scripts/combine_runs.sh`](scripts/combine_runs.sh) | Merges results folders into one and scores it, without re-running anything |
| `tests/*.py` | Unit tests, see [Tests](#tests) |

## How to add an engine

1. Write `bench/engines/<name>.py` with `ocr(image_path: str) -> str` and, optionally,
   `load() -> dict` (load models once; return `version`, `device`, `model` for the report).
2. Register it in `bench/engines/__init__.py`: `Engine("<name>", "bench.engines.<name>", "<env>")`.
3. If it needs its own dependencies, add `envs/<env>.txt` and run `scripts/setup_envs.sh <env>`.
4. Run it on one page: `.venv/bin/python -m bench.run --engines <name> --limit 1 --out results/dev-1page`.

The worker protocol is in [`bench/worker.py`](bench/worker.py); a crash or a hang costs one
page and is recorded.

## How to add a document

1. Add an entry to `SOURCES` in `bench/dataset.py`: `url`, `sha256` of the copy you
   tested, `license`, local `file`, `layout` (`single`, or `spread-rtl` for two-page
   spreads), `pages` to test (`"5"`, or `"12R"` / `"12L"` for spread halves),
   `synthetic_from` pages for the synthetic set, `fonts`.
2. `scripts/build_dataset.sh`. Pages that fail the ground-truth checks are listed in
   `data/dropped_pages.txt` and left out.
3. Open a few `data/pages/*.png` next to `data/gt/*.txt` and compare line by line before
   trusting them.

## Known limits

- Ground truth quality: the text layer is what the PDF says, after the glyph rebuild above.
  Six of the sixteen pages were compared by eye.
- Fonts: born-digital pages use Times New Roman (Word) and Muna / TheSansArabic
  (InDesign); synthetic pages use Noto Naskh Arabic, Tahoma and Times New Roman.
  Calligraphic styles (Diwani, Thuluth), Nastaliq and decorative headings are not covered.
- One test page is a table of contents (MOHRE 32R: article, title, page number in three
  columns). The ground truth reads it row by row, as printed; an engine that reads it
  column by column is not wrong but loses on CER and WER. Word recall (any order) is the
  fair number for that page.
- Size: 16 law pages, 4 synthetic texts, 96 real pages, of which 44 were read by every
  engine. Treat differences of a few CER points between close engines as noise.
- One machine, one run, default settings (plus the one PaddleOCR variant). Times include
  Python overhead.
- Gemini ran on 10 v0 images and on the 10-page real small set (separate run). Its numbers
  move with the model version. The v0 run did not log token counts; the real small set
  did: about 1.8 cents a page at Google's list price (11,385 tokens in, 18,003 out).
- No handwriting, no ID cards, no invoices or forms, no personal data. v0 uses public UAE
  laws; the v1 real scans are printed Wikipedia articles, books, journals and magazines,
  not UAE documents.
- v1 pages were selected by one person, by eye; another reader could classify a few
  borderline Misraj pages differently.
- The law PDFs are not pinned by their publishers. If a publisher replaces a file, the
  download script warns and the ground truth built from it may differ.

## Tests

```bash
.venv/bin/python -m pytest -q tests
```

Normalization switches, CER/WER/recall on hand-counted Arabic examples, the PDF line
rebuild (ligatures, numbers, brackets, dates, Latin islands, gaps without space glyphs),
the Misraj Markdown to text conversion and the real-scan small set, the `--common` page
set of the scorer, the engine registry (every adapter module exists, paid engines stay
out of the default run), API keys read from the environment, the download script (dry
run, checksum checks) and the source and license of every page in the manifest. The
tests need the core env, not the data.

## License

The code and the result files in this repository are under the MIT license, see
[`LICENSE`](LICENSE). The inputs are not in the repository and keep their own licenses,
see [Data sources and licenses](#data-sources-and-licenses).
