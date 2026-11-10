# get_match_results

## Purpose
Get the most recent completed football match for a team.

## Parameters
- team_id: Required integer. API-Football team ID.
- days_back: Optional integer. Number of past days to search.
  Default: 365. Allowed range: 1 to 730.

## Behavior
- Uses the API-Football fixtures endpoint.
- Uses from and to date filters.
- Does not use the API-restricted last parameter.
- Returns the latest completed match.
- Completed statuses include FT, AET, and PEN.

## Error handling
Returns a structured error when the API request fails.
Does not invent match scores.