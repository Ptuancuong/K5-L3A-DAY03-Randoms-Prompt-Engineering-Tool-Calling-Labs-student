import os
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


def get_league_standings(league_id: int, season: int):
    """Get standings for a football league and season."""

    api_key = os.getenv("API_FOOTBALL_KEY")
    base_url = os.getenv(
        "API_FOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    )

    if not api_key:
        return {"error": "Missing API_FOOTBALL_KEY in .env"}

    if league_id <= 0 or not 2000 <= season <= 2100:
        return {"error": "Invalid league_id or season"}

    params = urlencode({"league": league_id, "season": season})
    url = f"{base_url}/standings?{params}"

    request = Request(url, headers={"x-apisports-key": api_key})

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("errors"):
            return {"error": data["errors"]}

        response_data = data.get("response", [])
        if not response_data:
            return {
                "league_id": league_id,
                "season": season,
                "standings": [],
                "message": "No standings data available"
            }

        league = response_data[0].get("league", {})
        tables = league.get("standings", [])

        standings = []
        for table in tables:
            for team in table:
                standings.append({
                    "rank": team.get("rank"),
                    "team": team.get("team", {}).get("name"),
                    "points": team.get("points"),
                    "played": team.get("all", {}).get("played"),
                    "win": team.get("all", {}).get("win"),
                    "draw": team.get("all", {}).get("draw"),
                    "lose": team.get("all", {}).get("lose"),
                    "goal_difference": team.get("goalsDiff")
                })

        return {
            "league": league.get("name"),
            "season": season,
            "standings": standings
        }

    except HTTPError as exc:
        return {"error": f"API HTTP error: {exc.code}"}
    except (URLError, TimeoutError) as exc:
        return {"error": f"Network error: {exc}"}
    except Exception as exc:
        return {"error": str(exc)}