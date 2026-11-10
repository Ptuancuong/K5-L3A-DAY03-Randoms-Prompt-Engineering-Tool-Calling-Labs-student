
import os
import json
from datetime import date
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


def get_player_stats(player_name: str, league_id: int = None):
    """Search player statistics in the automatically detected season."""

    api_key = os.getenv("API_FOOTBALL_KEY")
    base_url = os.getenv(
        "API_FOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    ).rstrip("/")

    if not api_key:
        return {"error": "Missing API_FOOTBALL_KEY in .env"}

    if not isinstance(player_name, str) or len(player_name.strip()) < 3:
        return {"error": "player_name must contain at least 3 characters"}

    if league_id is not None:
        if not isinstance(league_id, int) or league_id <= 0:
            return {"error": "league_id must be a positive integer"}

    today = date.today()
    # Most major European leagues start their season around August.
    season = today.year if today.month >= 8 else today.year - 1

    params_dict = {
        "search": player_name.strip(),
        "season": season
    }

    # Restrict the search only when the user specifies a league.
    if league_id is not None:
        params_dict["league"] = league_id

    params = urlencode(params_dict)
    url = f"{base_url}/players?{params}"
    request = Request(url, headers={"x-apisports-key": api_key})

    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        if data.get("errors"):
            return {
                "error": data["errors"],
                "player_name": player_name,
                "league_id": league_id,
                "season": season,
                "provider": "API-Football"
            }

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
            "league_id": league_id,
            "season": season,
            "player_count": len(players),
            "players": players,
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
