---
name: get_player_stats
track: bonus
kind: live_api
provider: API-Football
requires_env: [API_FOOTBALL_KEY]
inputs: [player_name, league_id, season]
outputs: [players]
side_effect: false
---

# Get Player Stats

Returns player statistics for a league and season.

- Requires a player name, league ID, and season.
- Multiple matching players may be returned.