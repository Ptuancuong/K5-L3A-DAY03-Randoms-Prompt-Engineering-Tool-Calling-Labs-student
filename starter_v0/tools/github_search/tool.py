from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, USER_AGENT, clamp_int, err, pick_enum

SORTS = ("stars", "updated")


def github_search(query: str = "", language: str = "", sort: str = "stars", limit: int = 5) -> dict[str, Any]:
    """Search public GitHub repositories. GITHUB_TOKEN is optional (higher rate limit)."""
    try:
        clean_query = " ".join(str(query or "").split())
        if not clean_query:
            raise ValueError("query is empty - pass keywords describing the repository to find")
        clean_language = "".join(str(language or "").split())
        sort = pick_enum(sort, SORTS, "stars")
        limit = clamp_int(limit, 5, 1, 20)
        q = f"{clean_query} language:{clean_language}" if clean_language else clean_query
        headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": q, "sort": sort, "order": "desc", "per_page": limit},
            headers=headers,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = [{
            "title": repo.get("full_name") or "",
            "url": repo.get("html_url") or "",
            "source": "github.com",
            "summary": repo.get("description") or "",
            "stars": repo.get("stargazers_count"),
            "language": repo.get("language"),
            "updated_at": repo.get("updated_at"),
        } for repo in (response.json().get("items") or [])[:limit]]
        return {"tool": "github_search", "query": clean_query, "language": clean_language or None, "sort": sort, "items": items}
    except Exception as exc:
        return err("github_search", exc)