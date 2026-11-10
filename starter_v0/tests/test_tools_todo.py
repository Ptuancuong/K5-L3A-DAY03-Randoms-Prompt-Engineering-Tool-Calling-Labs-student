"""TODO(student): Tool Unit Test Challenge.

Each test below is implemented to test the tools offline.
Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401
from tools import TOOL_FUNCTIONS  # noqa: F401


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    clarify_tool = TOOL_FUNCTIONS["clarify"]
    result = clarify_tool(question="Bạn chọn phương án nào?", response_type="choice", options=["A", "B"])
    assert result["options"] == ["A", "B"]
    assert result["awaiting_user"] is True
    assert result["response_type"] == "choice"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    items = [
        {"title": "Tin 1", "section": "A"},
        {"title": "Tin 2", "section": "B"},
        {"title": "Tin 3", "section": "A"},
    ]
    result = format_tool(items=items, template="sections")
    md = result["markdown"]
    assert md.count("## A") == 1
    assert md.count("## B") == 1


def test_format_thread_numbers_items() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    items = [{"title": "Item 1"}, {"title": "Item 2"}]
    result = format_tool(items=items, template="thread")
    lines = result["markdown"].split("\n\n")
    assert lines[0].startswith("1/ ")
    assert lines[1].startswith("2/ ")


def test_format_empty_items_does_not_crash() -> None:
    format_tool = TOOL_FUNCTIONS["format"]
    res1 = format_tool(items=None)
    res2 = format_tool(items=[])
    assert res1["item_count"] == 0
    assert res2["item_count"] == 0


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_bot_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
    calls = fake_http(FakeResponse({"ok": True}))
    send_tool = TOOL_FUNCTIONS["send"]
    result = send_tool(text="Hello", confirmed=True)
    assert len(calls) == 1
    assert "fake_bot_token" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "123456"
    assert calls[0]["json"]["text"] == "Hello"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    send_tool = TOOL_FUNCTIONS["send"]
    result = send_tool(text="Hello", confirmed=True)
    assert "error" in result
    assert len(calls) == 0


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))
    lookup_tool = TOOL_FUNCTIONS["lookup"]
    lookup_tool(query="test", timeframe=None)
    assert len(calls) == 1
    assert "time_range" not in calls[0]["json"]


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({
        "data": {
            "markdown": "Content body",
            "metadata": {"title": "T", "sourceURL": "https://example.com/source"},
        }
    }))
    fetch_tool = TOOL_FUNCTIONS["fetch"]
    result = fetch_tool(url="https://example.com/source")
    item = result["items"][0]
    assert item["title"] == "T"
    assert item["url"] == "https://example.com/source"
    assert item["summary"] == "Content body"
    assert item["source"] == "example.com"


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")
    fake_http(FakeResponse({"data": {"markdown": "a" * 5000, "metadata": {}}}))
    fetch_tool = TOOL_FUNCTIONS["fetch"]
    result = fetch_tool(url="https://example.com")
    assert len(result["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    raw_items = [{"id": f"{i}", "text": f"Tweet {i}", "screen_name": "user"} for i in range(6)]
    raw_items.insert(2, {"text": "No ID tweet", "screen_name": "user"})
    fake_http(FakeResponse({"timeline": raw_items}))
    timeline_tool = TOOL_FUNCTIONS["timeline"]
    result = timeline_tool(screenname="user", limit=3)
    assert len(result["items"]) == 3
    for item in result["items"]:
        assert item["url"].startswith("https://x.com/user/status/")


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "test-key")
    calls = fake_http(FakeResponse({"tweets": []}))
    social_tool = TOOL_FUNCTIONS["social_search"]
    social_tool(query="OpenAI", search_type="Top")
    assert len(calls) == 1
    assert calls[0]["params"]["query"] == "OpenAI"
    assert calls[0]["params"]["search_type"] == "Top"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="privacy policy", policy_area="data_privacy")
    assert len(result["results"]) > 0
    for item in result["results"]:
        assert item["policy_area"] == "data_privacy"


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    policy_tool = TOOL_FUNCTIONS["policy"]
    result = policy_tool(query="injection probe", policy_area="source_citation")
    found_untrusted = False
    for hit in result["results"]:
        for line in hit.get("untrusted_text", []):
            if "ignore the citation policy" in line:
                found_untrusted = True
                break
        assert "ignore the citation policy" not in hit["facts"]
    assert found_untrusted is True


# ---------------- YOUR NEW TOOL(S) ----------------

def test_my_new_tool_happy_path() -> None:
    calc = TOOL_FUNCTIONS["calculator"]
    res = calc(expression="10 + 20 * 3")
    assert res.get("error") is None
    assert res["result"] == 70


def test_my_new_tool_bad_input_from_model() -> None:
    calc = TOOL_FUNCTIONS["calculator"]
    res = calc(expression="")
    assert res["error"] == "ValueError"


def test_my_new_tool_failure_returns_error_dict() -> None:
    calc = TOOL_FUNCTIONS["calculator"]
    res = calc(expression="10 / 0")
    assert res["error"] == "ZeroDivisionError"
    assert "division by zero" in res["message"]


# ---------------- sentiment_analyzer ----------------

def test_sentiment_analyzer_positive() -> None:
    fn = TOOL_FUNCTIONS["sentiment_analyzer"]
    res = fn(text="This AI model is an amazing and successful breakthrough!")
    assert res["tool"] == "sentiment_analyzer"
    assert res["sentiment"] == "positive"
    assert res["polarity_score"] > 0
    assert "breakthrough" in res["positive_signals"]


def test_sentiment_analyzer_negative_and_negation() -> None:
    fn = TOOL_FUNCTIONS["sentiment_analyzer"]
    res = fn(text="This product is terrible and dangerous, not good at all.")
    assert res["sentiment"] == "negative"
    assert res["polarity_score"] < 0


def test_sentiment_analyzer_empty_input() -> None:
    fn = TOOL_FUNCTIONS["sentiment_analyzer"]
    res = fn(text="")
    assert res["error"] == "ValueError"


# ---------------- crypto_lookup ----------------

def test_crypto_lookup_known_symbol(fake_http) -> None:
    fake_http(FakeResponse({
        "bitcoin": {
            "usd": 89500.0,
            "usd_24h_change": 2.34,
            "usd_market_cap": 1770000000000,
        }
    }))
    fn = TOOL_FUNCTIONS["crypto_lookup"]
    res = fn(symbol="BTC")
    assert res["tool"] == "crypto_lookup"
    assert res["symbol"] == "BTC"
    assert res["coin_id"] == "bitcoin"
    assert res["price"] == 89500.0


def test_crypto_lookup_empty_or_invalid_symbol(fake_http) -> None:
    fn = TOOL_FUNCTIONS["crypto_lookup"]
    res_empty = fn(symbol="")
    assert res_empty["error"] == "ValueError"

    fake_http(FakeResponse({}))
    res_unknown = fn(symbol="UNKNOWN_COIN_XYZ_123")
    assert res_unknown["error"] == "NotFoundError"


def test_crypto_lookup_vs_currency_vnd(fake_http) -> None:
    fake_http(FakeResponse({
        "ethereum": {
            "vnd": 80000000.0,
            "vnd_24h_change": 1.5,
            "vnd_market_cap": 9600000000000,
        }
    }))
    fn = TOOL_FUNCTIONS["crypto_lookup"]
    res = fn(symbol="ETH", vs_currency="vnd")
    assert res["currency"] == "VND"
    assert res["price"] == 80000000.0

