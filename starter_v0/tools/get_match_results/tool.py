import os
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


def get_match_results(team_id: int, last: int = 5):
    """Get recent football matches for a team from API-Football."""

    api_key = os.getenv("API_FOOTBALL_KEY")
    base_url = os.getenv(
        "API_FOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    )

    if not api_key:
        return {"error": "Missing API_FOOTBALL_KEY in .env"}

    if team_id <= 0 or not 1 <= last <= 20:
        return {"error": "team_id must be positive and last must be 1-20"}

    params = urlencode({"team": team_id, "last": last, "timezone": "Asia/Ho_Chi_Minh"})
    url = f"{base_url}/fixtures?{params}"

    request = Request(url, headers={"x-apisports-key": api_key})

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("errors"):
            return {"error": data["errors"]}

        matches = []
        for item in data.get("response", []):
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})

            matches.append({
                "date": fixture.get("date"),
                "status": fixture.get("status", {}).get("long"),
                "home_team": teams.get("home", {}).get("name"),
                "away_team": teams.get("away", {}).get("name"),
                "home_goals": goals.get("home"),
                "away_goals": goals.get("away"),
                "league": item.get("league", {}).get("name")
            })

        return {"team_id": team_id, "matches": matches}

    except HTTPError as exc:
        return {"error": f"API HTTP error: {exc.code}"}
    except (URLError, TimeoutError) as exc:
        return {"error": f"Network error: {exc}"}
    except Exception as exc:
        return {"error": str(exc)}