"""Arabic text normalization applied to both ground truth and OCR output
before scoring.

Every step is a named switch. Three presets:

- raw: only what no reader can see (invisible characters, Unicode NFC,
  whitespace). Use it to see how much the other steps hide.
- standard (default): raw + presentation forms decomposed (NFKC), harakat and
  other Arabic combining marks removed, tatweel removed, alef forms unified
  (أ إ آ ٱ -> ا), alef maqsura -> ya (ى -> ي), Persian look-alike letters
  mapped to Arabic (ی -> ي, ک -> ك, ە -> ه), digits mapped to 0-9, punctuation
  mapped to one form (، -> , and so on, list-separator dots · • -> .), symbols
  dropped (◄ ● ■).
- aggressive: standard + ta marbuta -> ha (ة -> ه) + all punctuation removed.

Change a single step with Norm.preset("standard").but(ta_marbuta=True).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, replace

# Invisible characters: zero-width (joiners, ZWSP, BOM), bidi marks,
# embeddings, overrides and isolates. Removed in every preset.
INVISIBLE = re.compile("[​-‏؜‪-‮⁦-⁩﻿­]")
WHITESPACE = re.compile(r"\s+")

ARABIC_RANGES = ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF),
                 (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))

ALEF_FORMS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ٲ": "ا", "ٳ": "ا"})
PERSIAN = str.maketrans({"ی": "ي", "ې": "ي", "ک": "ك", "ە": "ه", "ہ": "ه", "ۀ": "ه"})
DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
PUNCT = str.maketrans({
    "،": ",", "؛": ";", "؟": "?", "۔": ".", "٪": "%", "٫": ".", "٬": ",",
    "“": '"', "”": '"', "„": '"', "«": '"', "»": '"', "‹": "'", "›": "'",
    "‘": "'", "’": "'", "‚": "'", "–": "-", "—": "-", "‐": "-", "‑": "-",
    "−": "-", "…": "...", "٭": "*",
    # dots that separate list items (Wikipedia navigation lists use the middle
    # dot; engines return a period or a bullet for it)
    "·": ".", "•": ".", "∙": ".", "‧": ".", "・": ".",
    # ornate brackets around Quran verses; in logical order the verse opens
    # with U+FD3F and closes with U+FD3E
    "﴿": "(", "﴾": ")",
})


def _is_arabic(ch: str) -> bool:
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in ARABIC_RANGES)


@dataclass(frozen=True)
class Norm:
    nfkc: bool = True               # presentation forms (ﻻ ﷲ) -> base letters
    diacritics: bool = True         # remove harakat, tanween, shadda, sukun, dagger alef...
    tatweel: bool = True            # remove kashida (ـ)
    alef: bool = True               # أ إ آ ٱ -> ا
    alef_maqsura: bool = True       # ى -> ي
    persian: bool = True            # ی ک ە -> ي ك ه
    ta_marbuta: bool = False        # ة -> ه
    digits: bool = True             # ٠-٩ and ۰-۹ -> 0-9
    punctuation: str = "unify"      # "keep" | "unify" | "remove"
    symbols: bool = True            # remove Unicode "So" symbols (◄ ● ■ ©)

    @staticmethod
    def preset(name: str) -> "Norm":
        if name == "standard":
            return Norm()
        if name == "raw":
            return Norm(nfkc=False, diacritics=False, tatweel=False, alef=False,
                        alef_maqsura=False, persian=False, ta_marbuta=False,
                        digits=False, punctuation="keep", symbols=False)
        if name == "aggressive":
            return Norm(ta_marbuta=True, punctuation="remove")
        raise ValueError(f"unknown preset {name!r} (raw, standard, aggressive)")

    def but(self, **changes) -> "Norm":
        return replace(self, **changes)

    def describe(self) -> str:
        return ", ".join(f"{k}={v}" for k, v in asdict(self).items())


def normalize(text: str, norm: Norm | str = "standard") -> str:
    if isinstance(norm, str):
        norm = Norm.preset(norm)
    s = INVISIBLE.sub("", text)
    s = unicodedata.normalize("NFKC" if norm.nfkc else "NFC", s)
    if norm.diacritics:
        s = "".join(c for c in s if not (unicodedata.category(c) == "Mn" and _is_arabic(c)))
    if norm.tatweel:
        s = s.replace("ـ", "")
    if norm.alef:
        s = s.translate(ALEF_FORMS)
    if norm.persian:
        s = s.translate(PERSIAN)
    if norm.alef_maqsura:
        s = s.replace("ى", "ي")
    if norm.ta_marbuta:
        s = s.replace("ة", "ه")
    if norm.digits:
        s = s.translate(DIGITS)
    if norm.punctuation == "unify":
        s = s.translate(PUNCT)
    elif norm.punctuation == "remove":
        s = "".join(" " if unicodedata.category(c).startswith("P") else c for c in s)
    if norm.symbols:
        s = "".join(" " if unicodedata.category(c) == "So" else c for c in s)
    return WHITESPACE.sub(" ", s).strip()


def words(normalized: str) -> list[str]:
    """Word tokens for WER: punctuation and symbols act as separators, so
    "دبي." and "دبي ." both give ["دبي"]. Combining marks stay inside words."""
    return "".join(
        " " if unicodedata.category(c)[0] in "PS" else c for c in normalized
    ).split()
