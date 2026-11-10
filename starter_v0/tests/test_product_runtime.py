from pathlib import Path

import pytest

import product_runtime as runtime
from providers.base import ModelResponse, ToolCall
from tools import load_tool_declarations, to_openai_tools

ROOT = Path(__file__).resolve().parents[1]
TOOLS = to_openai_tools(load_tool_declarations(ROOT / "artifacts" / "tools.yaml"))


class FakeProvider:
    def __init__(self, *responses):
        self.responses = iter(responses)

    def complete(self, *args, **kwargs):
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def run(provider):
    return runtime.run_product_loop(provider=provider, messages=[{"role": "user", "content": "research"}], tools=TOOLS, model="fake")


def test_catalog_and_model_declarations_include_all_eleven_tools():
    names = {row["name"] for row in runtime.tool_catalog(ROOT)}
    assert names == {item["function"]["name"] for item in TOOLS}
    assert len(names) == 11


@pytest.mark.parametrize("name", sorted(set(runtime.TOOL_INFO) - {"send"}))
def test_each_read_tool_is_dispatched_through_product_loop(name, monkeypatch):
    for key in runtime.TOOL_INFO[name][2]:
        monkeypatch.setenv(key, "test-value")
    observed = []

    def tool(query):
        observed.append(query)
        return {"items": [{"title": "evidence"}]}

    monkeypatch.setitem(runtime.TOOL_FUNCTIONS, name, tool)
    result = run(FakeProvider(ModelResponse(text=None, tool_calls=[ToolCall(name=name, args={"query": "test"})]), ModelResponse(text="done")))
    assert observed == ["test"]
    assert result["status"] == "answered"
    assert result["tool_events"][0]["result"]["items"][0]["title"] == "evidence"


def test_missing_twitter_configuration_does_not_execute_tool(monkeypatch):
    def must_not_run(**kwargs):
        pytest.fail("Network tool must not run without configuration")

    monkeypatch.setitem(runtime.TOOL_FUNCTIONS, "timeline", must_not_run)
    result = runtime.execute_read_call("timeline", {"screenname": "sama"}, {"timeline"})
    assert result["error"] == "missing_configuration"
    assert "RAPIDAPI_KEY" in result["message"]


def test_error_after_tool_preserves_evidence_and_does_not_retry():
    result = run(FakeProvider(
        ModelResponse(text=None, tool_calls=[ToolCall(name="deduplicate", args={"items": [{"url": "a"}, {"url": "a"}]})]),
        ValueError("Failed to parse tool call arguments as JSON"),
    ))
    assert result["status"] == "provider_error"
    assert result["tool_events"][0]["result"]["removed_count"] == 1
    assert len(result["rounds"]) == 1
    assert any("TOOL_RESULTS_JSON" in msg["content"] for msg in result["messages"])


def test_clarify_pauses_before_other_calls(monkeypatch):
    result = run(FakeProvider(ModelResponse(text=None, tool_calls=[
        ToolCall(name="clarify", args={"question": "URL?"}),
        ToolCall(name="deduplicate", args={"items": []}),
    ])))
    assert result["status"] == "waiting_for_user"
    assert len(result["tool_events"]) == 1


def configure_telegram(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-telegram-secret")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@test-channel")


def test_model_confirmed_true_never_sends_until_ui_approval(monkeypatch):
    configure_telegram(monkeypatch)
    calls = []
    monkeypatch.setitem(runtime.TOOL_FUNCTIONS, "send", lambda **args: calls.append(args) or {"status": "sent"})
    result = run(FakeProvider(ModelResponse(text=None, tool_calls=[ToolCall(name="send", args={"text": "Exact draft", "confirmed": True})])))
    assert result["status"] == "awaiting_confirmation"
    assert calls == []
    pending = result["pending_send"]
    assert pending["destination"] == "@test-channel"
    assert runtime.approve_send(pending, pending["id"])["status"] == "sent"
    assert calls == [{"text": "Exact draft", "confirmed": True}]
    assert runtime.approve_send(pending, pending["id"])["error"] == "already_consumed"
    assert len(calls) == 1


def test_changed_destination_invalidates_approval(monkeypatch):
    configure_telegram(monkeypatch)
    pending = runtime.prepare_send({"text": "draft"})["pending_send"]
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@another-channel")
    assert runtime.approve_send(pending, pending["id"])["error"] == "destination_changed"


def test_failed_send_is_consumed_and_secret_is_redacted(monkeypatch):
    configure_telegram(monkeypatch)

    def fail(**kwargs):
        raise RuntimeError("https://api.telegram.org/bottest-telegram-secret/sendMessage")

    monkeypatch.setitem(runtime.TOOL_FUNCTIONS, "send", fail)
    pending = runtime.prepare_send({"text": "draft"})["pending_send"]
    result = runtime.approve_send(pending, pending["id"])
    assert "test-telegram-secret" not in str(result)
    assert runtime.approve_send(pending, pending["id"])["error"] == "already_consumed"


def test_unknown_tool_and_invalid_arguments_are_reported():
    result = runtime.execute_read_call("not-a-tool", {}, {"not-a-tool"})
    assert result["error"] == "unknown_tool"
    result = run(FakeProvider(
        ModelResponse(text=None, tool_calls=[ToolCall(name="fetch", args={"_invalid_json_arguments": "{"})]),
        ModelResponse(text="invalid input reported"),
    ))
    assert result["tool_events"][0]["result"]["error"] == "invalid_arguments"


def test_real_local_policy_search_has_evidence():
    result = runtime.execute_read_call("policy", {"query": "citation", "policy_area": "source_citation"}, {"policy"})
    assert "error" not in result
    assert result["results"]

