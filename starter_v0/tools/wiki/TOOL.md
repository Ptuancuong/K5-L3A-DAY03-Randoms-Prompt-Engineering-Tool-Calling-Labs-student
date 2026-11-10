---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [title, lang]
outputs: [items, is_disambiguation]
side_effect: false
---
# wiki

Team-added tool. Returns the lead summary of one Wikipedia article
(`/api/rest_v1/page/summary/{title}`), in English (`en`) or Vietnamese (`vi`).
Use for background/definitions of a concept, person or organisation; not for
current news. A missing article returns `items: []` with a message (not an error).
