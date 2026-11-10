import os
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


def get_player_stats(player_name: str, league_id: int, season: int):
    """Search player statistics for a league and season."""

    api_key = os.getenv("API_FOOTBALL_KEY")
    base_url = os.getenv(
        "API_FOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    )

    if not api_key:
        return {"error": "Missing API_FOOTBALL_KEY in .env"}

    if not player_name or len(player_name.strip()) < 3:
        return {"error": "player_name must contain at least 3 characters"}

    if league_id <= 0 or not 2000 <= season <= 2100:
        return {"error": "Invalid league_id or season"}

    params = urlencode({
        "search": player_name.strip(),
        "league": league_id,
        "season": season
    })
    url = f"{base_url}/players?{params}"

    request = Request(url, headers={"x-apisports-key": api_key})

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("errors"):
            return {"error": data["errors"]}

        players = []
        for item in data.get("response", []):
            player = item.get("player", {})

            for stat in item.get("statistics", []):
                games = stat.get("games", {})
                goals = stat.get("goals", {})

                players.append({
                    "player_id": player.get("id"),
                    "name": player.get("name"),
                    "age": player.get("age"),
                    "team": stat.get("team", {}).get("name"),
                    "league": stat.get("league", {}).get("name"),
                    "appearances": games.get("appearences"),
                    "minutes": games.get("minutes"),
                    "goals": goals.get("total"),
                    "assists": goals.get("assists"),
                    "yellow_cards": stat.get("cards", {}).get("yellow"),
                    "red_cards": stat.get("cards", {}).get("red")
                })

        return {
            "search_name": player_name,
            "season": season,
            "players": players
        }

    except HTTPError as exc:
        return {"error": f"API HTTP error: {exc.code}"}
    except (URLError, TimeoutError) as exc:
        return {"error": f"Network error: {exc}"}
    except Exception as exc:
        return {"error": str(exc)}