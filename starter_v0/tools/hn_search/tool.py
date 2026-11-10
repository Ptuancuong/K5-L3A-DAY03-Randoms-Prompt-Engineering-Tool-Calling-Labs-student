from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, USER_AGENT, clamp_int, domain, err, pick_enum

SORTS = ("relevance", "date")
ENDPOINTS = {
    "relevance": "https://hn.algolia.com/api/v1/search",
    "date": "https://hn.algolia.com/api/v1/search_by_date",
}


def hn_search(query: str = "", sort: str = "relevance", limit: int = 5) -> dict[str, Any]:
    """Search Hacker News stories via the public Algolia API."""
    try:
        clean_query = " ".join(str(query or "").split())
        if not clean_query:
            raise ValueError("query is empty - pass the topic keyword to search on Hacker News")
        sort = pick_enum(sort, SORTS, "relevance")
        limit = clamp_int(limit, 5, 1, 20)
        response = requests.get(
            ENDPOINTS[sort],
            params={"query": clean_query, "tags": "story", "hitsPerPage": limit},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = []
        for hit in (response.json().get("hits") or [])[:limit]:
            object_id = hit.get("objectID") or ""
            discussion = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""
            link = hit.get("url") or discussion
            items.append({
                "title": hit.get("title") or hit.get("story_title") or "",
                "url": link,
                "source": domain(link) if hit.get("url") else "news.ycombinator.com",
                "summary": f"{hit.get('points') or 0} points, {hit.get('num_comments') or 0} comments on Hacker News",
                "discussion_url": discussion,
                "date": hit.get("created_at"),
            })
        return {"tool": "hn_search", "query": clean_query, "sort": sort, "items": items}
    except Exception as exc:
        return err("hn_search", exc)