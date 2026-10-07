"""OpenRouter adapter: request shape and answer cleanup, without calling the API."""
from bench.engines import openrouter as o
from bench.engines.gemini import PROMPT


def test_payload_sends_the_image_and_the_shared_prompt():
    o.MODEL = "test/model"
    p = o.payload("page.jpg", "QUJD")
    parts = p["messages"][0]["content"]
    assert p["model"] == "test/model" and p["usage"] == {"include": True}
    assert parts[0]["image_url"]["url"] == "data:image/jpeg;base64,QUJD"
    assert parts[1]["text"] == PROMPT


def test_whole_answer_code_fence_is_removed():
    assert o.strip_fence("```text\nسطر أول\nسطر ثان\n```") == "سطر أول\nسطر ثان"
    assert o.strip_fence("```\nسطر\n```") == "سطر"


def test_text_without_fence_is_kept_as_is():
    assert o.strip_fence("سطر أول\n```ليس سياجا```") == "سطر أول\n```ليس سياجا```"


def test_text_of_reads_string_and_list_contents():
    assert o.text_of({"choices": [{"message": {"content": "نص"}}]}) == "نص"
    assert o.text_of({"choices": [{"message": {"content": [{"type": "text", "text": "نص"}]}}]}) == "نص"


def test_empty_answer_cut_by_the_budget_is_a_failure(monkeypatch):
    import io, json, pytest
    o.MODEL = "test/model"
    o._key = "k"
    out = {"choices": [{"finish_reason": "length", "message": {"content": ""}}], "usage": {}}
    monkeypatch.setattr(o.urllib.request, "urlopen", lambda req, timeout: io.BytesIO(json.dumps(out).encode()))
    monkeypatch.setattr("builtins.open", lambda *a, **k: io.BytesIO(b"png"))
    with pytest.raises(RuntimeError, match="no text"):
        o.ocr("page.png")
