from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, USER_AGENT, clamp_int, err, pick_enum

SORTS = ("downloads", "likes")


def hf_models(query: str = "", task: str = "", sort: str = "downloads", limit: int = 5) -> dict[str, Any]:
    """Search models on the Hugging Face Hub (public API, no key)."""
    try:
        clean_query = " ".join(str(query or "").split())
        clean_task = str(task or "").strip().lower().replace(" ", "-").replace("_", "-")
        if not clean_query and not clean_task:
            raise ValueError("query and task are both empty - pass a model keyword and/or a task like 'text-to-speech'")
        sort = pick_enum(sort, SORTS, "downloads")
        limit = clamp_int(limit, 5, 1, 20)
        params: dict[str, Any] = {"sort": sort, "direction": -1, "limit": limit}
        if clean_query:
            params["search"] = clean_query
        if clean_task:
            params["pipeline_tag"] = clean_task
        response = requests.get("https://huggingface.co/api/models", params=params,
                                headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
        items = []
        for model in (response.json() or [])[:limit]:
            model_id = model.get("id") or model.get("modelId") or ""
            items.append({
                "title": model_id,
                "url": f"https://huggingface.co/{model_id}" if model_id else "",
                "source": "huggingface.co",
                "summary": f"task={model.get('pipeline_tag') or '?'}, downloads={model.get('downloads') or 0}, likes={model.get('likes') or 0}",
                "task": model.get("pipeline_tag"),
                "downloads": model.get("downloads"),
                "likes": model.get("likes"),
            })
        return {"tool": "hf_models", "query": clean_query, "task": clean_task or None, "sort": sort, "items": items}
    except Exception as exc:
        return err("hf_models", exc)
