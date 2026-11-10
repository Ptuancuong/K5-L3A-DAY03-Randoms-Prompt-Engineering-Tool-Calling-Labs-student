from typing import Any


def deduplicate_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Remove duplicate URLs, keeping the first item and input order."""
    if not isinstance(items, list):
        return {
            "error": "invalid_input",
            "message": "items must be a list of objects",
        }

    unique_items = []
    seen_urls = set()
    removed_count = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            return {
                "error": "invalid_input",
                "message": f"items[{index}] must be an object",
            }

        url = item.get("url")

        if url is not None and not isinstance(url, str):
            return {
                "error": "invalid_input",
                "message": f"items[{index}].url must be a string or null",
            }

        normalized_url = url.strip() if isinstance(url, str) else ""

        if normalized_url and normalized_url in seen_urls:
            removed_count += 1
            continue

        if normalized_url:
            seen_urls.add(normalized_url)

        unique_items.append(dict(item))

    return {
        "items": unique_items,
        "input_count": len(items),
        "item_count": len(unique_items),
        "removed_count": removed_count,
    }