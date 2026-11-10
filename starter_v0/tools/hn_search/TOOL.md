---
name: hn_search
track: bonus
kind: live_api
provider: Hacker News (Algolia API)
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hn_search

Team-added tool. Searches Hacker News stories through the public Algolia API.
`sort=relevance` uses `/search`, `sort=date` uses `/search_by_date`. Each item
links to the story URL and keeps the HN discussion URL.
