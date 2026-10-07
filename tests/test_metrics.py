"""CER / WER / order-free recall on hand-counted Arabic examples."""
import pytest

from bench.metrics import bow_recall, cer, number_recall, rev_cer, score, wer
from bench.normalize import Norm, normalize


def test_identical_is_zero():
    s = "المادة الأولى من القانون"
    assert cer(s, s) == 0 and wer(s, s) == 0 and bow_recall(s, s) == 1


def test_cer_deletion():
    # كتاب = ك ت ا ب (4 chars); كتب drops the alef: 1 deletion
    assert cer("كتاب", "كتب") == pytest.approx(1 / 4)


def test_cer_substitution():
    # قلم -> فلم : qaf read as fa, 1 substitution over 3 chars
    assert cer("قلم", "فلم") == pytest.approx(1 / 3)


def test_cer_empty_output_is_one():
    assert cer("قانون العمل", "") == 1.0


def test_cer_can_exceed_one_on_invented_text():
    # ref "من" (2 chars), hyp "من من من" (8 chars): 6 insertions
    assert cer("من", "من من من") == pytest.approx(3.0)


def test_cer_counts_spaces():
    # missing space between two words: 1 deletion over 9 chars
    assert cer("عقد العمل", "عقدالعمل") == pytest.approx(1 / 9)


def test_wer_after_normalization():
    ref = normalize("ذهب الولد إلى المدرسة")      # -> ذهب الولد الي المدرسة
    hyp = normalize("ذهب الولد الى المدرسه")
    assert wer(ref, hyp) == pytest.approx(1 / 4)  # only المدرسة/المدرسه differs
    strict = Norm().but(ta_marbuta=True)
    assert wer(normalize("ذهب الولد إلى المدرسة", strict),
               normalize("ذهب الولد الى المدرسه", strict)) == 0


def test_wer_ignores_punctuation_spacing_cer_does_not():
    assert wer("دبي.", "دبي .") == 0
    assert cer("دبي.", "دبي .") == pytest.approx(1 / 4)


def test_order_free_recall_separates_reading_order_from_recognition():
    ref = "المادة الأولى من القانون"
    hyp = "القانون من الأولى المادة"           # every word read, order reversed
    assert bow_recall(ref, hyp) == 1.0
    assert wer(ref, hyp) == 1.0               # 4 edits over 4 words


def test_bow_recall_counts_duplicates_once_each():
    assert bow_recall("في في دبي", "في دبي") == pytest.approx(2 / 3)


def test_rev_cer_detects_visual_order_output():
    ref = normalize("المادة الأولى")
    visual = "ىلوألا ةداملا"                  # the same line typed left to right
    assert cer(ref, normalize(visual)) > 0.5    # most characters wrong
    assert rev_cer(ref, visual, Norm()) == 0


def test_score_treats_failure_as_empty_output():
    s = score("قانون العمل", None)
    assert s == {"cer": 1.0, "wer": 1.0, "bow_recall": 0.0}


def test_empty_reference_rejected():
    with pytest.raises(ValueError):
        cer("", "x")


def test_number_recall_counts_only_numbers():
    ref = normalize("المادة (٥) لسنة 2025")          # Arabic-Indic 5 -> 5
    assert number_recall(ref, normalize("المادة لسنة 2025")) == 0.5
    assert number_recall(ref, normalize("لسنة 2025 المادة (5)")) == 1.0
    assert number_recall(normalize("بدون أرقام"), "x") is None
