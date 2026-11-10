from copy import deepcopy

import pytest

from tools import TOOL_FUNCTIONS


deduplicate = TOOL_FUNCTIONS["deduplicate"]


def test_duplicate_url_keeps_first_item_and_order():
    items = [
        {"title": "First", "url": "https://example.com/a"},
        {"title": "Duplicate", "url": " https://example.com/a "},
        {"title": "Second", "url": "https://example.com/b"},
    ]
    original = deepcopy(items)

    result = deduplicate(items=items)

    assert result["items"] == [items[0], items[2]]
    assert result["input_count"] == 3
    assert result["item_count"] == 2
    assert result["removed_count"] == 1
    assert items == original


def test_missing_or_empty_urls_are_preserved():
    items = [
        {"title": "Missing URL"},
        {"title": "Null URL", "url": None},
        {"title": "Empty URL", "url": ""},
        {"title": "Whitespace URL", "url": "   "},
    ]

    result = deduplicate(items=items)

    assert result["items"] == items
    assert result["item_count"] == 4
    assert result["removed_count"] == 0


def test_empty_list_returns_empty_result():
    assert deduplicate(items=[]) == {
        "items": [],
        "input_count": 0,
        "item_count": 0,
        "removed_count": 0,
    }


@pytest.mark.parametrize(
    "bad_items",
    [
        None,
        "not a list",
        {},
        [123],
        [{"url": 123}],
    ],
)
def test_invalid_input_returns_error_dict(bad_items):
    result = deduplicate(items=bad_items)

    assert result["error"] == "invalid_input"
    assert isinstance(result["message"], str)
    assert result["message"]