
---
name: get_player_stats
track: bonus
kind: live_api
provider: API-Football
requires_env: [API_FOOTBALL_KEY]
inputs: [player_name, league_id]
outputs: [players]
side_effect: false
---

# Get Player Stats

Returns player statistics for the automatically detected current season.

## Inputs

- player_name: Required string, at least 3 characters.
- league_id: Optional positive integer. Use it to restrict the search to a specific league.

## Season handling

- Determines the season internally.
- Does not require the user to provide a season.

## Behavior

- Uses the API-Football players endpoint.
- Searches by player name.
- Optionally restricts results to a league.
- Returns appearances, minutes, goals, assists, and cards.
- May return multiple matching players.
- Returns structured errors when the API request fails.
- Does not invent player statistics.
