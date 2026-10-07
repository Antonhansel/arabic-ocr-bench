"""Misraj Markdown/HTML to plain text, the real-scan small set, and the
--kind filter of the runner."""
from bench.dataset import Row, gt_problems, mark_small_set
from bench.engines import ENGINES
from bench.realscans import interleave, md_to_text
from bench.run import select_rows


def test_page_number_is_kept_watermark_and_image_are_dropped():
    md = ("<page_number>١٥٨</page_number>\n\nالنص الأول\n"
          "<watermark>This file was downloaded from example.com</watermark>\n"
          "<image> image here</image>\n<img src='x.png'>\nالنص الثاني")
    assert md_to_text(md) == "١٥٨\nالنص الأول\nالنص الثاني"


def test_html_table_is_read_row_by_row_in_cell_order():
    md = ("<table><thead><tr><th>القطاع</th><th>الرأسمال</th></tr></thead>"
          "<tbody><tr><td>مصرف 1</td><td></td><td>100</td></tr>"
          "<tr><td>مصرف\n  2</td><td><b>132</b></td></tr></tbody></table>")
    assert md_to_text(md) == "القطاع الرأسمال\nمصرف 1 100\nمصرف 2 132"


def test_markdown_table_separator_is_dropped_and_cells_joined():
    md = "| الاسم | العدد |\n|---|:---:|\n| فعالة | ١٩ |"
    assert md_to_text(md) == "الاسم العدد\nفعالة ١٩"


def test_emphasis_headings_bullets_and_rules_are_removed():
    md = ("# الفصل الأول\n**<ins>الأدلة</ins> :**\n- بند أول\n* بند ثان\n\n***\n---\n"
          "(١) المرجع السابق .")
    assert md_to_text(md) == "الفصل الأول\nالأدلة :\nبند أول\nبند ثان\n(١) المرجع السابق ."


def test_numbered_list_numbers_are_printed_so_they_stay():
    assert md_to_text("1. الأول\n2. الثاني") == "1. الأول\n2. الثاني"


def test_italic_markup_is_unwrapped_but_a_printed_asterisk_stays():
    assert md_to_text("*Chronique de Michel le Syrien*, tome II") == "Chronique de Michel le Syrien, tome II"
    assert md_to_text("(*) كتبت في ١٩٩١") == "(*) كتبت في ١٩٩١"


def test_entities_and_escapes_are_decoded():
    assert md_to_text("محمد &amp; علي \\*نص\\*") == "محمد & علي *نص*"


def test_interleave_alternates_sources():
    assert interleave([1, 2, 3], ["a"]) == [1, "a", 2, 3]


def rs_row(pid, source, capture):
    return Row(pid, f"{pid}.png", f"{pid}.txt", "real-scan", capture, 300, "", source, "", "")


def test_small_set_takes_4_yarmouk_4_misraj_scans_2_misraj_photos():
    rows = ([rs_row(f"y{i}", "nod-yarmouk", "scanned") for i in range(6)] +
            [rs_row(f"m{i}", "misraj-dococr", "scanned") for i in range(6)] +
            [rs_row(f"p{i}", "misraj-dococr", "photo") for i in range(4)])
    mark_small_set(rows)
    picked = [r.page_id for r in rows if r.small_set]
    assert picked == ["y0", "y1", "y2", "y3", "m0", "m1", "m2", "m3", "p0", "p1"]


def test_kind_filter_applies_before_limit():
    rows = [{"page_id": "a", "kind": "born-digital", "small_set": "1"},
            {"page_id": "b", "kind": "real-scan", "small_set": "0"},
            {"page_id": "c", "kind": "real-scan", "small_set": "1"},
            {"page_id": "d", "kind": "real-scan", "small_set": "1"}]
    tess = ENGINES["tesseract"]
    assert [r["page_id"] for r in select_rows(rows, tess, 2, False, "real-scan")] == ["b", "c"]
    assert [r["page_id"] for r in select_rows(rows, tess, None, True, "real-scan")] == ["c", "d"]
    gemini = ENGINES["gemini-3.5-flash"]                       # small set only, whatever the flags
    assert [r["page_id"] for r in select_rows(rows, gemini, None, False, "real-scan")] == ["c", "d"]


def test_pdf_checks_do_not_drop_printed_ligatures_from_human_transcriptions():
    text = " ".join(["قال رسول الله ﷺ في الحديث ﴿ليس عليكم جناح﴾"] * 6) + " املوص الشعيب املصبة املوص"
    assert gt_problems(text, [], pdf_text=False) == []
    assert "presentation-form characters in text layer" in gt_problems(text, [])


def test_misraj_selection_file_is_consistent():
    # The page list is committed and drives the download: one row per page,
    # known capture and layout values, and a uuid to check the dataset row.
    import csv
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / "data" / "realscans_misraj.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len({r["row"] for r in rows}) == len(rows) == len({r["uuid"] for r in rows})
    assert {r["capture"] for r in rows} <= {"scanned", "photo"}
    assert {r["layout"] for r in rows} <= {"single", "multi"}
    assert all(0 <= int(r["row"]) < 400 for r in rows)
    # every two-page item is a photo of an open book: that is how they were picked
    assert all(r["capture"] == "photo" for r in rows if r["layout"] == "multi")
