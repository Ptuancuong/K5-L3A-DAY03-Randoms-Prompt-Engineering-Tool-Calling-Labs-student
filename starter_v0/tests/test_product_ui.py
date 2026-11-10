"""Streamlit UI tests: no live model calls, no network or real Telegram messages."""
import shutil
from pathlib import Path

from streamlit.testing.v1 import AppTest

import env_loader
import product_runtime
import providers
from providers.base import ModelResponse, ToolCall

ROOT = Path(__file__).resolve().parents[1]


def app_test(tmp_path, monkeypatch):
    monkeypatch.setattr(env_loader, "load_lab_env", lambda root: None)
    (tmp_path / "artifacts").mkdir()
    for name in ("system_prompt.md", "tools.yaml"):
        shutil.copyfile(ROOT / "artifacts" / name, tmp_path / "artifacts" / name)
    for name in ("app.py", "product_runtime.py"):
        shutil.copyfile(ROOT / name, tmp_path / name)
    shutil.copytree(ROOT / "company_policy", tmp_path / "company_policy")
    source = (ROOT / "app.py").read_text(encoding="utf-8-sig")
    source = source.replace("ROOT = Path(__file__).resolve().parent", f"ROOT = Path({str(tmp_path)!r})")
    return AppTest.from_string(source, default_timeout=20).run()


def test_startup_shows_all_tools_without_credentials(tmp_path, monkeypatch):
    app = app_test(tmp_path, monkeypatch)
    assert not app.exception
    assert len(app.session_state["session"]["tool_declarations"]) == 11
    labels = [expander.label for expander in app.sidebar.expander]
    assert len(labels) == 11
    for name in product_runtime.TOOL_INFO:
        assert any(f"{name} ·" in label for label in labels)
    assert any("RAPIDAPI_KEY" in caption.value for caption in app.sidebar.caption)


def test_chat_executes_new_tool_and_saves_transcript(tmp_path, monkeypatch):
    responses = iter([
        ModelResponse(text=None, tool_calls=[ToolCall(name="deduplicate", args={"items": [{"url": "a"}, {"url": "a"}]})]),
        ModelResponse(text="Đã loại 1 tin trùng."),
    ])

    class FakeProvider:
        def complete(self, *args, **kwargs):
            return next(responses)

    monkeypatch.setattr(providers, "make_provider", lambda name: FakeProvider())
    app = app_test(tmp_path, monkeypatch)
    app.chat_input[0].set_value("Loại trùng").run()
    assert not app.exception
    turn = app.session_state["session"]["turns"][0]
    assert turn["tool_events"][0]["result"]["removed_count"] == 1
    assert len(list((tmp_path / "transcripts").glob("*.ui.transcript.json"))) == 1


def test_pending_send_can_be_cancelled_without_network(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-secret")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@fake-channel")
    calls = []
    monkeypatch.setitem(product_runtime.TOOL_FUNCTIONS, "send", lambda **args: calls.append(args) or {"status": "sent"})

    class FakeProvider:
        def complete(self, *args, **kwargs):
            return ModelResponse(text=None, tool_calls=[ToolCall(name="send", args={"text": "Draft for review", "confirmed": True})])

    monkeypatch.setattr(providers, "make_provider", lambda name: FakeProvider())
    app = app_test(tmp_path, monkeypatch)
    app.chat_input[0].set_value("Tạo bản nháp").run()
    assert not app.exception
    assert app.chat_input[0].disabled
    assert calls == []
    next(button for button in app.button if button.label == "Hủy gửi").click().run()
    assert not app.exception
    assert calls == []
    assert app.session_state["session"]["actions"][0]["result"]["status"] == "cancelled"
    assert not app.chat_input[0].disabled


def test_explicit_ui_approval_sends_exactly_once(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-secret")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@fake-channel")
    calls = []
    monkeypatch.setitem(product_runtime.TOOL_FUNCTIONS, "send", lambda **args: calls.append(args) or {"status": "sent"})

    class FakeProvider:
        def complete(self, *args, **kwargs):
            return ModelResponse(text=None, tool_calls=[ToolCall(name="send", args={"text": "Exact approved text", "confirmed": True})])

    monkeypatch.setattr(providers, "make_provider", lambda name: FakeProvider())
    app = app_test(tmp_path, monkeypatch)
    app.chat_input[0].set_value("Đề xuất bản nháp").run()
    assert calls == []
    next(button for button in app.button if button.label == "Xác nhận gửi bản nháp này").click().run()
    assert not app.exception
    assert calls == [{"text": "Exact approved text", "confirmed": True}]
    app.run()
    assert len(calls) == 1
    assert app.session_state["session"]["actions"][0]["result"]["status"] == "sent"


def test_provider_error_keeps_partial_results_in_saved_transcript(tmp_path, monkeypatch):
    responses = iter([
        ModelResponse(text=None, tool_calls=[ToolCall(name="deduplicate", args={"items": [{"url": "a"}, {"url": "a"}]})]),
        ValueError("Failed to parse tool call arguments as JSON"),
    ])

    class FakeProvider:
        def complete(self, *args, **kwargs):
            value = next(responses)
            if isinstance(value, Exception):
                raise value
            return value

    monkeypatch.setattr(providers, "make_provider", lambda name: FakeProvider())
    app = app_test(tmp_path, monkeypatch)
    app.chat_input[0].set_value("Loại trùng và tóm tắt").run()
    assert not app.exception
    turn = app.session_state["session"]["turns"][0]
    assert turn["status"] == "provider_error"
    assert turn["tool_events"][0]["result"]["removed_count"] == 1
    assert list((tmp_path / "transcripts").glob("*.ui.transcript.json"))
