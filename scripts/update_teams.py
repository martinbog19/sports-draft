import os
import requests
from supabase import create_client
import time


db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


sport = "hockey"
league = "nhl"


team_urls = []
page = 1
while True:
    url = f"http://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/teams?page={page}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    team_urls.extend([x["$ref"] for x in data["items"]])
    if data["pageIndex"] >= data["pageCount"]:
        break
    page += 1


transformed_teams = []
for url in team_urls:

    print(url, end="\r")

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    time.sleep(5)

    transformed_team = {
        "id": data["uid"],
        "espn_id": data["id"],
        "sport": sport,
        "league": league,
        "display_name": data["displayName"],
        "short_display_name": data["shortDisplayName"],
        "location": data["location"],
        "espn_slug": data["slug"],
        "abbreviation": data["abbreviation"],
        "logo_url": data.get("logos", [{}])[0].get("href"),
        "is_active": data["isActive"],
    }
    transformed_teams.append(transformed_team)

db.table("teams").upsert(
    transformed_teams,
    on_conflict="id"
).execute()