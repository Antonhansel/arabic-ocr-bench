"""Scoring: CER, WER, order-free word recall, and a visual-order check.

All functions take texts that are already normalized (see normalize.py).

- CER = character edit distance (insertions + deletions + substitutions)
  divided by the number of reference characters, spaces included. Not
  clipped: an engine that invents text can score above 1.0.
- WER = the same on word tokens (normalize.words), divided by the number of
  reference words.
- number_recall = the same, restricted to numbers (all-digit tokens).
- bow_recall = share of reference words found in the output, ignoring order
  (multiset intersection). High recall with high WER means the words were read
  but in the wrong order (columns, label/value rows, line order).
- rev_cer = CER after reversing the characters of every output line. If it
  is much lower than CER, the engine returned visual (left-to-right) order
  instead of logical Arabic order.
"""
from __future__ import annotations

from collections import Counter

from rapidfuzz.distance import Levenshtein

from .normalize import Norm, normalize, words


def cer(ref: str, hyp: str) -> float:
    if not ref:
        raise ValueError("empty reference")
    return Levenshtein.distance(ref, hyp) / len(ref)


def wer(ref: str, hyp: str) -> float:
    r, h = words(ref), words(hyp)
    if not r:
        raise ValueError("reference has no words")
    return Levenshtein.distance(r, h) / len(r)


def bow_recall(ref: str, hyp: str) -> float:
    r, h = Counter(words(ref)), Counter(words(hyp))
    total = sum(r.values())
    if not total:
        raise ValueError("reference has no words")
    return sum((r & h).values()) / total


def number_recall(ref: str, hyp: str) -> float | None:
    """Share of the reference's numbers (all-digit word tokens: article
    numbers, years, amounts) found in the output, ignoring order. None when
    the reference has no number."""
    r = Counter(w for w in words(ref) if w.isdigit())
    h = Counter(w for w in words(hyp) if w.isdigit())
    total = sum(r.values())
    return sum((r & h).values()) / total if total else None


def rev_cer(ref: str, raw_hyp: str, norm: Norm) -> float:
    """CER after reversing the characters of every line of the raw output.
    ref is already normalized; raw_hyp is the engine output as returned."""
    flipped = "\n".join(line[::-1] for line in raw_hyp.split("\n"))
    return cer(ref, normalize(flipped, norm))


def score(ref: str, hyp: str | None) -> dict:
    """All metrics for one page. hyp=None (engine error) scores as empty text."""
    hyp = hyp or ""
    return {
        "cer": cer(ref, hyp),
        "wer": wer(ref, hyp),
        "bow_recall": bow_recall(ref, hyp),
    }
