import os
import requests
from supabase import create_client
import time
from dotenv import load_dotenv



SLEEP_SECONDS = 2
TIMEOUT_SECONDS = 10


load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
leagues = supabase.table("leagues").select("id", "espn_sport, espn_league").eq("is_active", True).execute().data

def _get_espn_team_urls(espn_sport: str, espn_league: str) -> list[str]:

    team_urls = []
    page = 1
    while True:
        url = f"http://sports.core.api.espn.com/v2/sports/{espn_sport}/leagues/{espn_league}/teams?page={page}"
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        team_urls.extend([x["$ref"] for x in data["items"]])
        if data["pageIndex"] >= data["pageCount"]:
            break
        page += 1
    return team_urls

def _transform_team_payload(data: dict, espn_sport: str, espn_league: str) -> dict:
    logos = data.get("logos") or []
    return {
        "id": data["uid"],
        "espn_id": data["id"],
        "espn_sport": espn_sport,
        "espn_league": espn_league,
        "display_name": data["displayName"],
        "short_display_name": data["shortDisplayName"],
        "location": data["location"],
        "espn_slug": data["slug"],
        "abbreviation": data["abbreviation"],
        "logo_url": logos[0].get("href") if logos else None,
        "is_active": data["isActive"],
    }

failed = False
for league in leagues:
    league_id = league["id"]
    sport = league["espn_sport"]
    league_name = league["espn_league"]
    try:
        print(f"Updating teams for {sport} - {league_name}")
        team_urls = _get_espn_team_urls(sport, league_name)
        assert team_urls, f"No teams found for `{league_id}`"
    except Exception as e:
        failed = True
        print(f"Failed to update teams for `{league_id}`: {e}")
        continue

    transformed_teams = []
    for url in team_urls:
        try:
            print(f"    Fetching team data from {url}")
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            transformed_team = _transform_team_payload(data, sport, league_name)
            transformed_teams.append(transformed_team)
        except Exception as e:
            failed = True
            print(f"    Failed to fetch team data from `{url}`: {e}")
            continue
        time.sleep(SLEEP_SECONDS)

    if transformed_teams:
        supabase.table("teams").upsert(
            transformed_teams,
            on_conflict="id"
        ).execute()

if failed:
    raise Exception("One or more leagues failed to update. Check the logs for details.")