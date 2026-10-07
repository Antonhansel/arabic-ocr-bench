"""Hand-checked Arabic examples for the normalization switches."""
import pytest

from bench.normalize import Norm, normalize, words


def test_diacritics_removed():
    # "مُحَمَّدٌ" = mim damma, ha fatha, mim fatha+shadda, dal tanween damm
    assert normalize("مُحَمَّدٌ") == "محمد"
    assert normalize("يُسمّى هذا القانون") == "يسمي هذا القانون"


def test_dagger_alef_and_tatweel_removed():
    assert normalize("هٰذا") == "هذا"            # superscript (dagger) alef U+0670
    assert normalize("العمـــــل") == "العمل"     # kashida justification


def test_alef_forms_unified():
    assert normalize("أحمد إبراهيم آمنة ٱلله") == "احمد ابراهيم امنة الله"


def test_alef_maqsura_to_ya():
    assert normalize("على مستوى") == "علي مستوي"


def test_ta_marbuta_is_optional():
    assert normalize("المادة") == "المادة"
    assert normalize("المادة", Norm().but(ta_marbuta=True)) == "الماده"
    assert normalize("المادة", "aggressive") == "الماده"


def test_digits_mapped_to_ascii():
    assert normalize("المادة (٣) لسنة ٢٠٢٥") == "المادة (3) لسنة 2025"
    assert normalize("۱۴۴۷هـ") == "1447ه"       # Persian digits; tatweel dropped


def test_spaces_and_invisible_characters():
    assert normalize("دبي‏  \n\t الإمارة‌") == "دبي الامارة"
    assert normalize("‫نص‬") == "نص"


def test_presentation_forms_decomposed():
    assert normalize("ﻻ") == "لا"           # ARABIC LIGATURE LAM WITH ALEF ISOLATED FORM
    assert normalize("ﷲ") == "الله"         # ARABIC LIGATURE ALLAH ISOLATED FORM
    assert normalize("ﺎﻠﻤ") == "الم"  # isolated/initial/medial forms


def test_persian_lookalikes_mapped():
    assert normalize("کتاب یک") == "كتاب يك"


def test_punctuation_unified_and_symbols_dropped():
    assert normalize("نعم، لا؛ لماذا؟") == "نعم, لا; لماذا?"
    assert normalize("◄ التعريفات") == "التعريفات"
    assert normalize("«دبي»") == '"دبي"'


def test_raw_preset_keeps_everything_visible():
    s = "مُحَمَّدٌ، أحمد على ٢٠٢٥"
    assert normalize(s, "raw") == s
    assert normalize("دبي‏   الإمارة", "raw") == "دبي الإمارة"


def test_unknown_preset():
    with pytest.raises(ValueError):
        normalize("x", "nope")


def test_words_split_on_punctuation_keep_marks():
    assert words("دبي. الإمارة،") == ["دبي", "الإمارة"]
    assert words("دبي .") == ["دبي"]
    assert words("2025/7/15") == ["2025", "7", "15"]
    # combining marks must not split a word (raw preset keeps them)
    assert words("المُقاولات") == ["المُقاولات"]


def test_list_separator_dots_unified_with_period():
    # Wikipedia navigation lists separate items with a middle dot; engines
    # return a period or a bullet for the same mark.
    assert normalize("الاغوال · البرايك") == normalize("الاغوال . البرايك") == normalize("الاغوال • البرايك")
    assert normalize("الاغوال · البرايك", "raw") == "الاغوال · البرايك"


def test_ornate_quran_brackets_unified_with_parentheses():
    # Misraj transcriptions open a verse with U+FD3F and close it with U+FD3E (logical order)
    assert normalize("فنزلت: ﴿ليس عليكم جناح﴾") == normalize("فنزلت: (ليس عليكم جناح)")
