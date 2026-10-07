"""Engine registry: every adapter module exists, and paid engines stay opt-in."""
import importlib.util

from bench.engines import DEFAULT_ENGINES, ENGINES


def test_every_engine_module_exists():
    # find_spec does not import the module, so engines from other venvs are checked too.
    for e in ENGINES.values():
        assert importlib.util.find_spec(e.module) is not None, e.module


def test_paid_engines_are_not_run_by_default():
    assert all(not ENGINES[n].small_set_only for n in DEFAULT_ENGINES)
    assert "gemini-3.5-flash" not in DEFAULT_ENGINES


def test_openrouter_engines_stay_on_the_small_set():
    names = [n for n in ENGINES if n.startswith("or-")]
    assert names and all(ENGINES[n].small_set_only for n in names)
