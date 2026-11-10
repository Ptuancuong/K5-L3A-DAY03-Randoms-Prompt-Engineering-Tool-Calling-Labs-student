
---
name: get_league_standings
track: bonus
kind: live_api
provider: API-Football
requires_env: [API_FOOTBALL_KEY]
inputs: [league_id]
outputs: [standings]
side_effect: false
---

# Get League Standings

Returns standings for a football league in the automatically detected current season.

## Inputs

- league_id: Required positive integer. API-Football league ID.

## Season handling

- Determines the season internally.
- Does not require the user to provide a season.
- Uses the season start year.

## Behavior

- Uses the API-Football standings endpoint.
- Returns rank, team, points, played, wins, draws, losses, and goal difference.
- Returns structured errors when the API request fails.
- Does not invent standings.

