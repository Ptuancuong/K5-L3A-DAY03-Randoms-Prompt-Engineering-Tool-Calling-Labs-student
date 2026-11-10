---
name: get_match_results
track: bonus
kind: live_api
provider: API-Football
requires_env: [API_FOOTBALL_KEY]
inputs: [team_id, last]
outputs: [matches]
side_effect: false
---

# Get Match Results

Returns recent match results for a team.

- Requires a valid API-Football team ID.
- `last` defaults to 5.
- Does not modify external data.