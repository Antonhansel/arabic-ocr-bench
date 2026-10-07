"""Visual-to-logical rebuild of one PDF text line (bench/pdf_gt.py).

Each test lists the glyphs as a PDF draws them, left to right, with the
ToUnicode string of each glyph, and checks the logical Arabic text.
"""
from bench.pdf_gt import Glyph, _line_to_logical


def line(visual_glyphs, size=10.0, gap_after=()):
    """Place glyphs left to right, 5pt wide each. gap_after: indexes after
    which a 5pt gap with no space glyph is left (as InDesign does)."""
    out, x = [], 0.0
    for i, t in enumerate(visual_glyphs):
        out.append(Glyph(t, x, x + 5, 0, size, size))
        x += 5 + (5 if i in gap_after else 0)
    return out


def test_ligature_glyph_stays_in_logical_order():
    # المقاولات drawn left to right: ت, لا (one ligature glyph), و, ا, ق, م, ل, ا
    assert _line_to_logical(line(["ت", "لا", "و", "ا", "ق", "م", "ل", "ا"])) == "المقاولات"


def test_number_and_brackets():
    # "رقم (7) لسنة 2025": brackets carry their logical code point in the PDF
    g = ["2", "0", "2", "5", " ", "ة", "ن", "س", "ل", " ", ")", "7", "(", " ", "م", "ق", "ر"]
    assert _line_to_logical(line(g)) == "رقم (7) لسنة 2025"


def test_list_number_with_period():
    # "1. على" : the period sits left of the digit on the page
    assert _line_to_logical(line(["ى", "ل", "ع", " ", ".", "1"])) == "1. على"


def test_date_stays_one_number():
    g = ["1", "5", "/", "7", "/", "2", "0", "2", "5", " ", "خ", "ي", "ر", "ا", "ت", "ب"]
    assert _line_to_logical(line(g)) == "بتاريخ 15/7/2025"


def test_percent_with_western_digits():
    assert _line_to_logical(line(["1", "0", "%", " ", "ة", "ب", "س", "ن"])) == "نسبة 10%"


def test_latin_phrase_keeps_its_order():
    g = ["ي", "م", "س", "ر", "ل", "ا", " ", "D", "u", "b", "a", "i", ",", " ", "U", "A", "E",
         " ", "ع", "ق", "و", "م"]
    assert _line_to_logical(line(g)) == "موقع Dubai, UAE الرسمي"


def test_gap_without_space_glyph_becomes_a_space():
    # "عقد العمل" with no space glyph, only a gap between the two words
    g = ["ل", "م", "ع", "ل", "ا", "د", "ق", "ع"]
    assert _line_to_logical(line(g, gap_after={4})) == "عقد العمل"


def test_marks_follow_their_base_letter():
    glyphs = line(["ل", "م", "ع"])
    glyphs[1].marks.append("َ")              # fatha on the mim
    assert _line_to_logical(glyphs) == "عمَل"
