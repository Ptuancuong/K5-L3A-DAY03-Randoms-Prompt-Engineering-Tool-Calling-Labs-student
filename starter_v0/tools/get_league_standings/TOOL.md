---
name: get_league_standings
track: bonus
kind: live_api
provider: API-Football
requires_env: [API_FOOTBALL_KEY]
inputs: [league_id, season]
outputs: [standings]
side_effect: false
---

# Get League Standings

Returns league standings for a specified season.

- Requires a valid league ID and season.
- Season is the starting year, such as 2025.