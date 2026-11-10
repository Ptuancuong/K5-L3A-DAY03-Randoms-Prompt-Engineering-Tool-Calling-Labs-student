---
name: github_search
track: bonus
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [query, language, sort, limit]
outputs: [items]
side_effect: false
---
# github_search

Team-added tool. Searches public GitHub repositories
(`/search/repositories`), optional `language` filter, sorted by `stars` or
`updated`. `GITHUB_TOKEN` is optional and only raises the rate limit
(unauthenticated: 10 searches/minute).
