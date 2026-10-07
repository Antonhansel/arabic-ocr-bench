"""The committed page list (data/manifest.csv): every page names its source,
the source URL and the source license, as the code that builds it does."""
import csv
from pathlib import Path

from bench.dataset import SOURCES
from bench.realscans import MISRAJ_LICENSE, MISRAJ_PAGE, NOD_DOI, NOD_LICENSE

ROOT = Path(__file__).resolve().parent.parent


def test_every_page_carries_the_url_and_license_of_its_source():
    sources = {s["id"]: (s["url"], s["license"]) for s in SOURCES}
    sources["nod-yarmouk"] = (NOD_DOI, NOD_LICENSE)
    sources["misraj-dococr"] = (MISRAJ_PAGE, MISRAJ_LICENSE)
    with open(ROOT / "data" / "manifest.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    assert len({r["page_id"] for r in rows}) == len(rows)
    for r in rows:
        assert (r["source_url"], r["license"]) == sources[r["source_doc"]], r["page_id"]
