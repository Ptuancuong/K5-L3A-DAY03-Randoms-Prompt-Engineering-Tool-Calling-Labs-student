---
name: hf_models
track: bonus
kind: live_api
provider: Hugging Face Hub API
requires_env: []
inputs: [query, task, sort, limit]
outputs: [items]
side_effect: false
---
# hf_models

Team-added tool. Searches models on the Hugging Face Hub (`/api/models`) by
keyword and/or task (`pipeline_tag`, e.g. `text-to-speech`), sorted by
`downloads` or `likes`.
