"""Glyph-aware ground-truth extraction for Arabic born-digital PDFs.

Why not pdftotext / PyMuPDF / pdfium? On Word and InDesign PDFs they reverse
right-to-left text character by character. A ligature glyph whose ToUnicode
entry is two letters ("لا", "لم") then comes out reversed ("ال", "مل"), so
"المقاولات" becomes "المقاوالت" and "المادة" becomes "املادة".

This module reads the glyphs with pdfminer, keeps every glyph's Unicode string
as one unit, and rebuilds logical order line by line:

1. group glyphs into visual lines by vertical position;
2. attach zero-width marks (harakat) to the base glyph under them;
3. sort base glyphs right to left;
4. put left-to-right islands (Latin words, numbers) back in left-to-right order.

Brackets are not mirrored: in both v0 sources (Word 2016 and InDesign) the
ToUnicode entry of a bracket glyph is already the logical character.

Every page also gets a list of warnings (unmapped glyphs, private-use
characters, rotated text) so that pages with an unreliable text layer can be
dropped before they become ground truth.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTContainer, LTPage

# Characters allowed inside a number island when they sit between two digits
# ("2025/7/15", "1.5", "10,000") or stick to it ("10%").
NUMBER_JOINERS = set("/.,:-٫٬")
NUMBER_SUFFIXES = set("%٪")


@dataclass
class Glyph:
    text: str
    x0: float
    x1: float
    y0: float
    y1: float
    size: float
    marks: list[str] = field(default_factory=list)

    @property
    def xc(self) -> float:
        return (self.x0 + self.x1) / 2

    @property
    def yc(self) -> float:
        return (self.y0 + self.y1) / 2


def _is_mark(text: str) -> bool:
    return bool(text) and all(unicodedata.category(c) == "Mn" for c in text)


def _kind(text: str) -> str:
    """R = right-to-left letter, L = left-to-right letter, D = digit, N = neutral."""
    kinds = {unicodedata.bidirectional(c) for c in text}
    if kinds & {"AL", "R"}:
        return "R"
    if "L" in kinds:
        return "L"
    if kinds & {"EN", "AN"}:
        return "D"
    return "N"


def _walk(obj, out: list[LTChar]) -> None:
    if isinstance(obj, LTChar):
        out.append(obj)
    elif isinstance(obj, LTContainer):
        for child in obj:
            _walk(child, out)


def _collect(page: LTPage, warnings: list[str]) -> list[Glyph]:
    chars: list[LTChar] = []
    _walk(page, chars)
    px0, py0, px1, py1 = page.bbox
    glyphs: list[Glyph] = []
    seen: set[tuple] = set()
    rotated = unmapped = pua = offpage = 0
    for c in chars:
        t = c.get_text()
        if not c.upright:
            rotated += 1
            continue
        if c.x1 < px0 or c.x0 > px1 or c.y1 < py0 or c.y0 > py1:
            offpage += 1
            continue
        if t.startswith("(cid:"):
            unmapped += 1
            continue
        if any(0xE000 <= ord(ch) <= 0xF8FF for ch in t):
            pua += 1
            continue
        # Fake bold draws the same glyph twice at (almost) the same spot.
        key = (t, round(c.x0, 0), round(c.y0, 0))
        if key in seen:
            continue
        seen.add(key)
        glyphs.append(Glyph(t, c.x0, c.x1, c.y0, c.y1, c.size))
    if rotated:
        warnings.append(f"{rotated} rotated glyphs skipped")
    if offpage:
        warnings.append(f"{offpage} off-page glyphs skipped")
    if unmapped:
        warnings.append(f"{unmapped} glyphs without Unicode mapping")
    if pua:
        warnings.append(f"{pua} private-use glyphs")
    return glyphs


def _group_lines(bases: list[Glyph]) -> list[list[Glyph]]:
    """Cluster glyphs whose vertical centres are close into visual lines."""
    lines: list[list[Glyph]] = []
    for g in sorted(bases, key=lambda g: -g.yc):
        for line in lines:
            ref = line[0]
            tol = 0.45 * max(min(ref.size, g.size), 1.0)
            if abs(ref.yc - g.yc) <= tol:
                line.append(g)
                break
        else:
            lines.append([g])
    lines.sort(key=lambda ln: -sum(g.yc for g in ln) / len(ln))
    return lines


def _attach_marks(marks: list[Glyph], bases: list[Glyph]) -> int:
    """Attach each zero-width mark to the base glyph under it. Returns orphans."""
    orphans = 0
    for m in marks:
        best, best_d = None, None
        for b in bases:
            if abs(b.yc - m.yc) > 1.2 * max(b.size, 1.0):
                continue
            if b.x0 - 0.5 <= m.x0 <= b.x1 + 0.5:
                d = abs(b.xc - m.x0) * 0.1 + abs(b.yc - m.yc)
            else:
                d = 1000 + min(abs(b.x0 - m.x0), abs(b.x1 - m.x0))
            if best_d is None or d < best_d:
                best, best_d = b, d
        if best is None or best_d >= 1000 + 3:
            orphans += 1
            continue
        best.marks.append(m.text)
    return orphans


def _island_end(seq: list[tuple[str, str]], i: int) -> int:
    """seq is in right-to-left visual order. Return the exclusive end of the
    left-to-right island that starts at i (an L or D token).

    Latin islands absorb the neutrals between two left-to-right tokens
    ("Dubai, UAE", "Law 5"). Number-only islands absorb a single joiner
    between two digits ("2025/7/15") and nothing else, so "15 2025" stays two
    islands, as the Unicode bidi algorithm displays them.
    """
    has_letter = seq[i][1] == "L"
    j = i + 1
    while j < len(seq):
        kind = seq[j][1]
        if kind in ("L", "D"):
            has_letter = has_letter or kind == "L"
            j += 1
            continue
        k = j
        while k < len(seq) and seq[k][1] == "N":
            k += 1
        if has_letter and k < len(seq) and seq[k][1] in ("L", "D"):
            j = k
            continue
        if (k == j + 1 and seq[j][0] in NUMBER_JOINERS and seq[j - 1][1] == "D"
                and k < len(seq) and seq[k][1] == "D"):
            j = k
            continue
        break
    return j


def _line_to_logical(line: list[Glyph]) -> str:
    line = sorted(line, key=lambda g: -g.xc)  # right to left
    tokens: list[tuple[str, str]] = []
    prev: Glyph | None = None
    for g in line:
        if prev is not None and g.text != " " and prev.text != " ":
            gap = prev.x0 - g.x1
            if gap > 0.2 * max(g.size, 1.0):
                tokens.append((" ", "N"))
        tokens.append((g.text + "".join(g.marks), _kind(g.text)))
        prev = g
    out: list[str] = []
    i = 0
    while i < len(tokens):
        text, kind = tokens[i]
        if kind in ("L", "D"):
            # A left-to-right island seen right to left: flip it back.
            j = _island_end(tokens, i)
            out.append("".join(reversed([t for t, _ in tokens[i:j]])))
            i = j
            continue
        if kind == "N" and text in NUMBER_SUFFIXES and i + 1 < len(tokens) and tokens[i + 1][1] == "D":
            # "10%" with Western digits is one left-to-right run, so "%" is
            # met first when reading right to left.
            j = _island_end(tokens, i + 1)
            out.append("".join(reversed([t for t, _ in tokens[i:j]])))
            i = j
            continue
        out.append(text)
        i += 1
    s = "".join(out)
    s = re.sub(r"[  ]+", " ", s).strip()
    return unicodedata.normalize("NFC", s)


def extract_page(pdf_path: str, page_index: int,
                 x_range: tuple[float, float] | None = None) -> tuple[str, list[str]]:
    """Return (text, warnings) for one page (0-based index).

    x_range keeps only glyphs whose centre lies in [x_min, x_max) (PDF points,
    origin at the left edge). Used to cut a two-page spread into two pages.
    """
    warnings: list[str] = []
    pages = list(extract_pages(pdf_path, page_numbers=[page_index], laparams=None))
    if not pages:
        return "", ["page not found"]
    glyphs = [g for g in _collect(pages[0], warnings) if g.text]
    if x_range is not None:
        glyphs = [g for g in glyphs if x_range[0] <= g.xc < x_range[1]]
    for g in glyphs:
        if g.text.strip() == "":
            g.text = " "
    marks = [g for g in glyphs if _is_mark(g.text)]
    bases = [g for g in glyphs if not _is_mark(g.text)]
    orphans = _attach_marks(marks, [b for b in bases if b.text != " "])
    if orphans:
        warnings.append(f"{orphans} orphan marks dropped")
    text_lines = [_line_to_logical(ln) for ln in _group_lines(bases)]
    return "\n".join(t for t in text_lines if t), warnings
