
import os
import json
from datetime import date, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError


def get_match_results(
    team_id: int,
    limit: int = 5,
    days_back: int = 365
):
    """
    Get recent completed football matches for a team.

    Automatically determines the football season.
    Does not require the user to provide a season.
    """

    api_key = os.getenv("API_FOOTBALL_KEY")
    base_url = os.getenv(
        "API_FOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    ).rstrip("/")

    if not api_key:
        return {"error": "Missing API_FOOTBALL_KEY"}

    if not isinstance(team_id, int) or team_id <= 0:
        return {"error": "team_id must be a positive integer"}

    if not isinstance(limit, int) or not 1 <= limit <= 20:
        return {"error": "limit must be between 1 and 20"}

    if not isinstance(days_back, int) or not 1 <= days_back <= 730:
        return {"error": "days_back must be between 1 and 730"}

    today = date.today()
    start_date = today - timedelta(days=days_back)

    # Most European football seasons start around August.
    # Before August, the current season started in the previous year.
    current_season = today.year if today.month >= 8 else today.year - 1

    headers = {
        "x-apisports-key": api_key
    }

    completed_statuses = {"FT", "AET", "PEN"}
    all_matches = []
    seasons_checked = []

    try:
        # Check the current season first, then the previous season.
        for season in [current_season, current_season - 1]:
            seasons_checked.append(season)

            params = urlencode({
                "team": team_id,
                "season": season,
                "from": start_date.isoformat(),
                "to": today.isoformat(),
                "timezone": "Asia/Ho_Chi_Minh"
            })

            url = f"{base_url}/fixtures?{params}"
            request = Request(url, headers=headers)

            with urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))

            if data.get("errors"):
                return {
                    "error": data["errors"],
                    "season": season,
                    "provider": "API-Football"
                }

            for item in data.get("response", []):
                fixture = item.get("fixture", {})
                status = fixture.get("status", {}).get("short")

                if status not in completed_statuses:
                    continue

                teams = item.get("teams", {})
                goals = item.get("goals", {})
                league = item.get("league", {})

                all_matches.append({
                    "date": fixture.get("date"),
                    "status": fixture.get("status", {}).get("long"),
                    "home_team": teams.get("home", {}).get("name"),
                    "away_team": teams.get("away", {}).get("name"),
                    "home_goals": goals.get("home"),
                    "away_goals": goals.get("away"),
                    "league": league.get("name"),
                    "season": league.get("season"),
                    "fixture_id": fixture.get("id")
                })

        # Remove duplicate fixtures, if any.
        unique_matches = {}
        for match in all_matches:
            fixture_id = match.get("fixture_id")
            if fixture_id is not None:
                unique_matches[fixture_id] = match

        matches = list(unique_matches.values())

        matches.sort(
            key=lambda match: match.get("date") or "",
            reverse=True
        )

        matches = matches[:limit]

        return {
            "team_id": team_id,
            "requested_limit": limit,
            "days_back": days_back,
            "seasons_checked": seasons_checked,
            "match_count": len(matches),
            "matches": matches,
            "provider": "API-Football"
        }

    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return {
            "error": f"API HTTP error: {exc.code}",
            "details": error_body,
            "provider": "API-Football"
        }

    except (URLError, TimeoutError) as exc:
        return {
            "error": f"Network error: {exc}",
            "provider": "API-Football"
        }

    except Exception as exc:
        return {
            "error": f"{type(exc).__name__}: {str(exc)}",
            "provider": "API-Football"
        }
