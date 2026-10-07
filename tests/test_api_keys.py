"""API engines read their key from the environment and fail loud without it."""
import pytest

from bench.engines import gemini, openrouter


@pytest.mark.parametrize("mod, var", [(gemini, "GEMINI_API_KEY"), (openrouter, "OPENROUTER_API_KEY")])
def test_key_comes_from_the_environment(monkeypatch, mod, var):
    monkeypatch.setattr(openrouter, "MODEL", "test/model")
    monkeypatch.setattr(mod, "_key", None)
    monkeypatch.delenv(var, raising=False)
    with pytest.raises(RuntimeError, match=var):
        mod.load()
    monkeypatch.setenv(var, " secret ")
    mod.load()
    assert mod._key == "secret"
