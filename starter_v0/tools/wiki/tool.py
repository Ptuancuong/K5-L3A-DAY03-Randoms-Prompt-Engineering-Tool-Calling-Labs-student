from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, USER_AGENT, err, pick_enum

LANGS = ("en", "vi")


def wiki_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    """Fetch the lead summary of one Wikipedia article."""
    try:
        clean_title = " ".join(str(title or "").split())
        if not clean_title:
            raise ValueError("title is empty - pass the article/concept name, e.g. 'Transformer (machine learning)'")
        lang = pick_enum(lang, LANGS, "en")
        path_title = quote(clean_title.replace(" ", "_"), safe="")
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{path_title}"
        response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=TIMEOUT)
        if response.status_code == 404:
            return {"tool": "wiki", "title": clean_title, "lang": lang, "items": [],
                    "message": f"No Wikipedia ({lang}) article found for '{clean_title}'."}
        response.raise_for_status()
        data = response.json()
        page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page") or f"https://{lang}.wikipedia.org/wiki/{path_title}"
        item = {
            "title": data.get("title") or clean_title,
            "url": page_url,
            "source": f"{lang}.wikipedia.org",
            "summary": data.get("extract") or "",
            "description": data.get("description") or "",
        }
        return {"tool": "wiki", "title": clean_title, "lang": lang, "is_disambiguation": data.get("type") == "disambiguation", "items": [item]}
    except Exception as exc:
        return err("wiki", exc)
