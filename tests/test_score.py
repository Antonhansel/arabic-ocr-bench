"""--common: a partial run is scored on the pages every engine finished."""
from bench.score import common_pages


def rows(engine, pages):
    return [{"engine": engine, "page_id": p} for p in pages]


def test_common_pages_is_the_intersection():
    rs = rows("tesseract", ["a", "b", "c"]) + rows("surya", ["a", "b"]) + rows("paddleocr", ["b", "a", "c"])
    assert common_pages(rs) == {"a", "b"}


def test_small_set_engine_does_not_shrink_the_set():
    # Gemini only runs on the small set: it must not cut the comparison down to its pages.
    rs = rows("tesseract", ["a", "b"]) + rows("surya", ["a", "b"]) + rows("gemini-3.5-flash", ["a"])
    assert common_pages(rs) == {"a", "b"}


def test_no_rows_no_pages():
    assert common_pages([]) == set()
