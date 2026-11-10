
import os
import json
from datetime import date
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


def get_league_standings(league_id: int):
    """Get standings for a league in the automatically detected season."""

    api_key = os.getenv("API_FOOTBALL_KEY")
    base_url = os.getenv(
        "API_FOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    ).rstrip("/")

    if not api_key:
        return {"error": "Missing API_FOOTBALL_KEY in .env"}

    if not isinstance(league_id, int) or league_id <= 0:
        return {"error": "league_id must be a positive integer"}

    today = date.today()
    # Most major European leagues start their season around August.
    season = today.year if today.month >= 8 else today.year - 1

    params = urlencode({
        "league": league_id,
        "season": season
    })
    url = f"{base_url}/standings?{params}"
    request = Request(url, headers={"x-apisports-key": api_key})

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("errors"):
            return {
                "error": data["errors"],
                "league_id": league_id,
                "season": season,
                "provider": "API-Football"
            }

        response_data = data.get("response", [])
        if not response_data:
            return {
                "league_id": league_id,
                "season": season,
                "standings": [],
                "message": "No standings data available for this league and season",
                "provider": "API-Football"
            }

        league = response_data[0].get("league", {})
        tables = league.get("standings", [])

        standings = []
        for table in tables:
            for team in table:
                all_stats = team.get("all", {})
                standings.append({
                    "rank": team.get("rank"),
                    "team": team.get("team", {}).get("name"),
                    "points": team.get("points"),
                    "played": all_stats.get("played"),
                    "win": all_stats.get("win"),
                    "draw": all_stats.get("draw"),
                    "lose": all_stats.get("lose"),
                    "goal_difference": team.get("goalsDiff")
                })

        return {
            "league": league.get("name"),
            "league_id": league_id,
            "season": season,
            "standings": standings,
            "provider": "API-Football"
        }

    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        return {
            "error": f"API HTTP error: {exc.code}",
            "details": details,
            "provider": "API-Football"
        }
    except (URLError, TimeoutError) as exc:
        return {"error": f"Network error: {exc}", "provider": "API-Football"}
    except Exception as exc:
        return {
            "error": f"{type(exc).__name__}: {str(exc)}",
            "provider": "API-Football"
        }
