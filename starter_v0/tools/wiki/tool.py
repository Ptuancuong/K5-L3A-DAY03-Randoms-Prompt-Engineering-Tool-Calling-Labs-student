from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, USER_AGENT, err, pick_enum

LANGS = ("en", "vi")
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _summary(lang: str, title: str) -> dict[str, Any] | None:
    """Return the page summary JSON, or None when the article does not exist (404)."""
    path_title = quote(title.replace(" ", "_"), safe="")
    response = requests.get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{path_title}", headers=HEADERS, timeout=TIMEOUT)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def _search_title(lang: str, query: str) -> str | None:
    """Best matching article title for a free-text query, or None."""
    response = requests.get(
        f"https://{lang}.wikipedia.org/w/rest.php/v1/search/title",
        params={"q": query, "limit": 1},
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    if response.status_code != 200:
        return None
    pages = (response.json() or {}).get("pages") or []
    return pages[0].get("title") if pages else None


def _lookup(lang: str, title: str) -> tuple[dict[str, Any] | None, str]:
    """Exact title first, then Wikipedia title search. Returns (summary, matched_title)."""
    data = _summary(lang, title)
    if data is not None:
        return data, title
    found = _search_title(lang, title)
    if found and found != title:
        data = _summary(lang, found)
        if data is not None:
            return data, found
    return None, title


def wiki_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    """Fetch the lead summary of one Wikipedia article.

    Fallbacks: exact title -> title search -> (if lang=vi) the same on English Wikipedia.
    """
    try:
        clean_title = " ".join(str(title or "").split())
        if not clean_title:
            raise ValueError("title is empty - pass the article/concept name, e.g. 'Transformer (deep learning)'")
        requested_lang = pick_enum(lang, LANGS, "en")

        used_lang = requested_lang
        data, matched = _lookup(requested_lang, clean_title)
        if data is None and requested_lang != "en":
            used_lang = "en"
            data, matched = _lookup("en", clean_title)

        result: dict[str, Any] = {"tool": "wiki", "title": clean_title, "lang": used_lang, "requested_lang": requested_lang}
        if data is None:
            return {**result, "items": [], "message": f"No Wikipedia article found for '{clean_title}'."}
        if used_lang != requested_lang:
            result["note"] = f"No {requested_lang} article found; returned the {used_lang} article instead."

        page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page") \
            or f"https://{used_lang}.wikipedia.org/wiki/{quote(matched.replace(' ', '_'), safe='')}"
        item = {
            "title": data.get("title") or matched,
            "url": page_url,
            "source": f"{used_lang}.wikipedia.org",
            "summary": data.get("extract") or "",
            "description": data.get("description") or "",
        }
        return {**result, "is_disambiguation": data.get("type") == "disambiguation", "items": [item]}
    except Exception as exc:
        return err("wiki", exc)