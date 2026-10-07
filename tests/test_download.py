"""scripts/download_data.py: the dry run lists every input with its license and
downloads nothing; downloaded files are checked."""
import hashlib
import importlib.util
import urllib.request
from pathlib import Path

import pytest

from bench import realscans
from bench.dataset import SOURCES

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("download_data", ROOT / "scripts" / "download_data.py")
dl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dl)

LAW_URLS = [s["url"] for s in SOURCES]
NOD_URLS = [realscans.NOD_URL.format(name=n) for n in realscans.NOD_FILES]
MISRAJ_URLS = [realscans.MISRAJ_URL.format(rev=realscans.MISRAJ_REV, name=n) for n in realscans.MISRAJ_FILES]


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a dry run must not download anything")
    monkeypatch.setattr(urllib.request, "urlopen", refuse)


def test_dry_run_lists_every_source_with_its_license(no_network, capsys):
    dl.main(["--dry-run"])
    out = capsys.readouterr().out
    assert len(LAW_URLS + NOD_URLS + MISRAJ_URLS) == 6
    assert all(u in out for u in LAW_URLS + NOD_URLS + MISRAJ_URLS)
    for license in (SOURCES[0]["license"], realscans.NOD_LICENSE, realscans.MISRAJ_LICENSE):
        assert f"license: {license}" in out


def test_only_keeps_the_chosen_group(no_network, capsys):
    dl.main(["--dry-run", "--only", "nod"])
    out = capsys.readouterr().out
    assert all(u in out for u in NOD_URLS)
    assert not any(u in out for u in LAW_URLS + MISRAJ_URLS)


def test_law_pdf_that_differs_from_the_published_copy_is_flagged(tmp_path, monkeypatch):
    pdf = tmp_path / "law.pdf"
    pdf.write_bytes(b"%PDF-1.7 another edition")
    monkeypatch.setattr(dl, "download", lambda src: pdf)
    law = next(f for f in dl.files() if f["group"] == "laws")
    ok, status = dl.get(law)
    assert not ok and "differs" in status
    ok, _ = dl.get(dict(law, digest=hashlib.sha256(pdf.read_bytes()).hexdigest()))
    assert ok


def test_dataset_file_with_a_wrong_checksum_stops_the_download(tmp_path):
    shard = tmp_path / "train-00000-of-00002.parquet"
    shard.write_bytes(b"not the published file")
    misraj = next(f for f in dl.files() if f["group"] == "misraj")
    with pytest.raises(RuntimeError, match="does not match"):
        dl.get(dict(misraj, path=shard))
