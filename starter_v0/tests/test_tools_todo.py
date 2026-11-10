"""TODO(student): Tool Unit Test Challenge.

Each test below is a stub. Replace `pytest.skip(...)` with a real test.
Patterns to copy are in test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest

from conftest import FakeResponse  # noqa: F401  (you will need it)
from tools import TOOL_FUNCTIONS  # noqa: F401

TODO = "TODO(student): implement this test"


# ---------------- clarify ----------------

import re  # noqa: E402
from pathlib import Path  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = TOOL_FUNCTIONS["clarify"](question="Nguồn nào?", response_type="choice", options=["web", "twitter"])
    assert result["options"] == ["web", "twitter"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    markdown = TOOL_FUNCTIONS["format"](items=items, template="sections")["markdown"]
    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    # both A items sit under the single A heading, before B
    assert markdown.index("a1") < markdown.index("a2") < markdown.index("## B")


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"tin {i}", "url": f"https://x.com/{i}"} for i in range(3)]
    markdown = TOOL_FUNCTIONS["format"](items=items, template="thread")["markdown"]
    lines = [line for line in markdown.split("\n") if line.strip()]
    assert [line.split(" ", 1)[0] for line in lines] == ["1/", "2/", "3/"]


def test_format_empty_items_does_not_crash() -> None:
    for empty in (None, []):
        result = TOOL_FUNCTIONS["format"](items=empty, template="sections")
        assert result["item_count"] == 0
        assert result["markdown"] == ""


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001")
    calls = fake_http(FakeResponse({"ok": True}))

    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert calls[0]["url"] == "https://api.telegram.org/bot123:abc/sendMessage"
    assert calls[0]["json"]["chat_id"] == "-1001"
    assert calls[0]["json"]["text"] == "Bản tin"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = TOOL_FUNCTIONS["send"](text="Bản tin", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    calls = fake_http(FakeResponse({"results": []}))
    TOOL_FUNCTIONS["lookup"](query="AI", timeframe=None)
    assert "time_range" not in calls[0]["json"]
    assert calls[0]["json"]["query"] == "AI"


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nBody",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/post"},
    }}))

    result = TOOL_FUNCTIONS["fetch"](url="https://www.example.com/post")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"] == {"url": "https://www.example.com/post", "formats": ["markdown"]}
    assert calls[0]["headers"]["Authorization"] == "Bearer fc-test"
    assert result["items"][0] == {
        "title": "T", "url": "https://www.example.com/post", "source": "example.com", "summary": "# Hello\nBody",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc-test")
    fake_http(FakeResponse({"data": {"markdown": "x" * 5000, "metadata": {}}}))
    summary = TOOL_FUNCTIONS["fetch"](url="https://example.com")["items"][0]["summary"]
    assert len(summary) == 4000


# ---------------- timeline / social_search ----------------

def _raw_tweets() -> list[dict]:
    no_id = {"text": "missing id", "screen_name": "sama"}
    valid = [{"tweet_id": str(100 + i), "text": f"tweet {i}", "screen_name": "sama"} for i in range(6)]
    return [no_id, *valid]


def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    calls = fake_http(FakeResponse({"timeline": _raw_tweets()}))

    result = TOOL_FUNCTIONS["timeline"](screenname="sama", limit=3)

    assert calls[0]["params"] == {"screenname": "sama"}
    assert len(result["items"]) == 3
    assert all(re.fullmatch(r"https://x\.com/sama/status/\d+", item["url"]) for item in result["items"])
    assert "missing id" not in [item["summary"] for item in result["items"]]


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    calls = fake_http(FakeResponse({"timeline": []}))
    TOOL_FUNCTIONS["social_search"](query="OpenAI", search_type="Top")
    assert calls[0]["url"].endswith("/search.php")
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}


# Regression (Challenge+): a negative limit from the model used to slice items[:-1]
# and silently return "all but the last" posts instead of the default amount.
def test_timeline_negative_limit_falls_back_to_default(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    fake_http(FakeResponse({"timeline": _raw_tweets()}))
    # 6 valid tweets: buggy code returned items[:-3] -> 3 items; expected the default 5
    assert len(TOOL_FUNCTIONS["timeline"](screenname="sama", limit=-3)["items"]) == 5


# Regression (Challenge+): limit="three" used to raise ValueError inside int() and fail the whole call.
def test_social_search_non_numeric_limit_does_not_fail_the_call(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    fake_http(FakeResponse({"timeline": _raw_tweets()}))
    result = TOOL_FUNCTIONS["social_search"](query="OpenAI", limit="three")
    assert "error" not in result
    assert len(result["items"]) == 5


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    for empty in ("", "   ", "là gì"):  # only stopwords -> no search terms
        assert TOOL_FUNCTIONS["policy"](query=empty)["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    results = TOOL_FUNCTIONS["policy"](query="API key customer data", policy_area="data_privacy", top_k=5)["results"]
    assert results
    assert {item["policy_area"] for item in results} == {"data_privacy"}


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    # Read the planted quoted line from the policy file instead of hard-coding it here.
    raw = (ROOT / "company_policy" / "source-citation-policy.md").read_text(encoding="utf-8")
    probe_section = raw.split("## Injection probe", 1)[1]
    planted = next(line.lstrip("> ").strip() for line in probe_section.splitlines() if line.startswith(">"))

    results = TOOL_FUNCTIONS["policy"](query="injection probe citation", policy_area="source_citation", top_k=10)["results"]
    probe = next(item for item in results if item["section"] == "Injection probe")

    assert planted in probe["untrusted_text"]
    assert planted not in probe["facts"]


# ---------------- YOUR NEW TOOL(S) ----------------
# Write at least 3 tests per tool your team adds:
#   1. happy path (mocked if it calls an API)
#   2. bad / missing input from the model (empty string, wrong type, out-of-enum value)
#   3. failure path (missing key, HTTP error, timeout) -> returns error dict, does not raise

import requests  # noqa: E402

wiki = TOOL_FUNCTIONS["wiki"]
hn = TOOL_FUNCTIONS["hn_search"]
github = TOOL_FUNCTIONS["github_search"]
hf = TOOL_FUNCTIONS["hf_models"]


# ---- wiki ----

def test_wiki_requests_summary_endpoint_and_maps_article(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Transformer (deep learning)",
        "extract": "A transformer is a neural network architecture.",
        "description": "Machine learning model",
        "type": "standard",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Transformer_(deep_learning)"}},
    }))

    result = wiki(title="Transformer (deep learning)")

    assert len(calls) == 1
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/Transformer_%28deep_learning%29"
    assert result["items"] == [{
        "title": "Transformer (deep learning)",
        "url": "https://en.wikipedia.org/wiki/Transformer_(deep_learning)",
        "source": "en.wikipedia.org",
        "summary": "A transformer is a neural network architecture.",
        "description": "Machine learning model",
    }]
    assert result["is_disambiguation"] is False


def test_wiki_unknown_lang_falls_back_to_english(fake_http) -> None:
    calls = fake_http(FakeResponse({"title": "AI", "extract": "x"}))
    result = wiki(title="AI", lang="fr")
    assert calls[0]["url"].startswith("https://en.wikipedia.org/")
    assert result["lang"] == "en"


def test_wiki_vietnamese_title_is_url_encoded(fake_http) -> None:
    calls = fake_http(FakeResponse({"title": "Trí tuệ nhân tạo", "extract": "x"}))
    wiki(title="Trí tuệ nhân tạo", lang="vi")
    assert calls[0]["url"].startswith("https://vi.wikipedia.org/api/rest_v1/page/summary/Tr%C3%AD_tu")
    assert " " not in calls[0]["url"]


def test_wiki_empty_title_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    result = wiki(title="   ")
    assert result["error"] == "ValueError"
    assert calls == []


def test_wiki_missing_article_returns_empty_items_not_error(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    result = wiki(title="Zzqqxx")
    assert "error" not in result
    assert result["items"] == []
    assert "No Wikipedia" in result["message"]


def test_wiki_server_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    assert wiki(title="AI")["error"] == "HTTPError"


def _route_http(monkeypatch, routes: dict[str, FakeResponse]) -> list[str]:
    """Fake requests.get that answers by URL prefix (fake_http only returns one response)."""
    seen: list[str] = []

    def _get(url, **kwargs):
        seen.append(url)
        for prefix, response in routes.items():
            if url.startswith(prefix):
                return response
        return FakeResponse(status_code=404)

    monkeypatch.setattr(requests, "get", _get)
    return seen


def test_wiki_uses_title_search_when_exact_title_missing(monkeypatch) -> None:
    seen = _route_http(monkeypatch, {
        "https://en.wikipedia.org/w/rest.php/v1/search/title": FakeResponse({"pages": [{"title": "Transformer (deep learning)"}]}),
        "https://en.wikipedia.org/api/rest_v1/page/summary/Transformer_%28deep_learning%29": FakeResponse({"title": "Transformer (deep learning)", "extract": "x"}),
    })

    result = wiki(title="Transformer AI")

    assert result["items"][0]["title"] == "Transformer (deep learning)"
    assert seen[0].endswith("/summary/Transformer_AI")       # exact title tried first
    assert "/search/title" in seen[1]                         # then search
    assert "note" not in result                               # same language, no fallback note


def test_wiki_vietnamese_miss_falls_back_to_english(monkeypatch) -> None:
    seen = _route_http(monkeypatch, {
        "https://vi.wikipedia.org/w/rest.php/v1/search/title": FakeResponse({"pages": []}),
        "https://en.wikipedia.org/api/rest_v1/page/summary/Andrej_Karpathy": FakeResponse({"title": "Andrej Karpathy", "extract": "AI researcher"}),
    })

    result = wiki(title="Andrej Karpathy", lang="vi")

    assert result["lang"] == "en"
    assert result["requested_lang"] == "vi"
    assert "returned the en article" in result["note"]
    assert result["items"][0]["source"] == "en.wikipedia.org"
    assert any(url.startswith("https://vi.wikipedia.org") for url in seen)  # vi really was tried first


# ---- hn_search ----

def test_hn_search_sends_story_query_and_maps_hits(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [
        {"objectID": "1", "title": "Rust 2.0", "url": "https://www.rust-lang.org/news", "points": 10, "num_comments": 3, "created_at": "2026-01-01"},
        {"objectID": "2", "title": "Ask HN: Rust?", "url": None, "points": 1, "num_comments": 0},
    ]}))

    result = hn(query="Rust", limit=2)

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search"
    assert calls[0]["params"] == {"query": "Rust", "tags": "story", "hitsPerPage": 2}
    first, second = result["items"]
    assert first["url"] == "https://www.rust-lang.org/news"
    assert first["source"] == "rust-lang.org"
    assert first["discussion_url"] == "https://news.ycombinator.com/item?id=1"
    assert "10 points" in first["summary"]
    # Ask HN posts have no external url -> fall back to the HN discussion page
    assert second["url"] == "https://news.ycombinator.com/item?id=2"
    assert second["source"] == "news.ycombinator.com"


def test_hn_search_date_sort_uses_search_by_date_endpoint(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hn(query="LLM", sort="date")
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"


def test_hn_search_coerces_bad_limit_and_sort_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hn(query="AI", sort="popular", limit="3")
    hn(query="AI", limit=0)
    hn(query="AI", limit=999)
    assert calls[0]["url"].endswith("/search")          # unknown sort -> relevance
    assert calls[0]["params"]["hitsPerPage"] == 3        # "3" -> 3
    assert calls[1]["params"]["hitsPerPage"] == 1        # 0 -> at least 1
    assert calls[2]["params"]["hitsPerPage"] == 20       # capped


def test_hn_search_empty_query_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    assert hn(query="")["error"] == "ValueError"
    assert calls == []


def test_hn_search_timeout_returns_error_dict(fake_http) -> None:
    fake_http(requests.Timeout("read timed out"))
    result = hn(query="AI")
    assert result["error"] == "Timeout"
    assert result["tool"] == "hn_search"


# ---- github_search ----

def test_github_search_builds_language_qualifier_and_maps_repos(monkeypatch, fake_http) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = fake_http(FakeResponse({"items": [{
        "full_name": "org/agent", "html_url": "https://github.com/org/agent", "description": "An agent",
        "stargazers_count": 1234, "language": "Python", "updated_at": "2026-11-01T00:00:00Z",
    }]}))

    result = github(query="llm agent", language="Python", limit=1)

    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"] == {"q": "llm agent language:Python", "sort": "stars", "order": "desc", "per_page": 1}
    assert "Authorization" not in calls[0]["headers"]
    assert result["items"][0] == {
        "title": "org/agent", "url": "https://github.com/org/agent", "source": "github.com",
        "summary": "An agent", "stars": 1234, "language": "Python", "updated_at": "2026-11-01T00:00:00Z",
    }


def test_github_search_ignores_blank_language_and_bad_sort(monkeypatch, fake_http) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    calls = fake_http(FakeResponse({"items": []}))
    github(query="vector db", language="  ", sort="popularity", limit="abc")
    assert calls[0]["params"]["q"] == "vector db"
    assert calls[0]["params"]["sort"] == "stars"
    assert calls[0]["params"]["per_page"] == 5


def test_github_search_sends_token_when_configured(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "gh-test")
    calls = fake_http(FakeResponse({"items": []}))
    github(query="rag")
    assert calls[0]["headers"]["Authorization"] == "Bearer gh-test"


def test_github_search_rate_limit_returns_error_dict(monkeypatch, fake_http) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    fake_http(FakeResponse(status_code=403))
    result = github(query="rag")
    assert result["error"] == "HTTPError"
    assert result["tool"] == "github_search"


# ---- hf_models ----

def test_hf_models_sends_search_and_normalised_task(fake_http) -> None:
    calls = fake_http(FakeResponse([
        {"id": "hexgrad/Kokoro-82M", "pipeline_tag": "text-to-speech", "downloads": 100, "likes": 7},
    ]))

    result = hf(query="kokoro", task="Text To Speech", limit=1)

    assert calls[0]["url"] == "https://huggingface.co/api/models"
    assert calls[0]["params"] == {"sort": "downloads", "direction": -1, "limit": 1,
                                  "search": "kokoro", "pipeline_tag": "text-to-speech"}
    item = result["items"][0]
    assert item["title"] == "hexgrad/Kokoro-82M"
    assert item["url"] == "https://huggingface.co/hexgrad/Kokoro-82M"
    assert item["downloads"] == 100


def test_hf_models_task_only_search_omits_search_param(fake_http) -> None:
    calls = fake_http(FakeResponse([]))
    hf(task="text-to-speech", sort="likes")
    assert "search" not in calls[0]["params"]
    assert calls[0]["params"]["sort"] == "likes"


def test_hf_models_without_query_or_task_returns_error_without_request(fake_http) -> None:
    calls = fake_http(FakeResponse([]))
    assert hf(query="", task="")["error"] == "ValueError"
    assert calls == []


def test_hf_models_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=429))
    assert hf(query="qwen")["error"] == "HTTPError"
