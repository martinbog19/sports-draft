from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import httpx
import os, random, string, time

from src.api import get_polymarket_data

load_dotenv()
app = FastAPI()

FRONTEND_ORIGINS = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def _random_code(n=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def execute(query, retries: int = 2, backoff: float = 0.5):
    """Run a Supabase query, retrying on transient connection errors."""
    for attempt in range(retries + 1):
        try:
            return query.execute()
        except httpx.TransportError:
            if attempt == retries:
                raise
            time.sleep(backoff * (attempt + 1))


@app.get("/health")
def health():
      result = execute(db.table("rooms").select("id").limit(1))
      return {"supabase": "connected", "data": result.data}


class CreateRoomRequest(BaseModel):
    user_id: str
    host_name: str
    draft_name: str = "Unnamed draft"
    snake: bool = True
    rounds: int = 5
    mode: str = "Easy"
    odds_provider: Optional[str] = None
    leagues: list[str] = []


@app.post("/rooms")
def create_room(req: CreateRoomRequest):
    code = _random_code()
    room = execute(db.table("rooms").insert({
        "code": code,
        "draft_name": req.draft_name,
        "host_id": req.user_id,
        "snake": req.snake,
        "rounds": req.rounds,
        "mode": req.mode,
        "odds_provider": req.odds_provider,
        "leagues": req.leagues,
        "status": "lobby"
    })).data[0]

    execute(db.table("room_players").insert({
        "room_id": room["id"],
        "user_id": req.user_id,
        "display_name": req.host_name,
        "seat": 0
    }))

    return {"code": code, "room_id": room["id"]}


class JoinRoomRequest(BaseModel):
    user_id: str
    display_name: str


@app.post("/rooms/{code}/join")
def join_room(code: str, req: JoinRoomRequest):
    room = execute(db.table("rooms").select("*").eq("code", code).single()).data
    if not room:
        raise HTTPException(404, "Room not found")
    if room["status"] != "lobby":
        raise HTTPException(400, "Draft already started")

    players = execute(db.table("room_players").select("*").eq("room_id", room["id"])).data

    if any(p["user_id"] == req.user_id for p in players):
        raise HTTPException(400, "You're already in this draft")

    seat = len(players)

    execute(db.table("room_players").insert({
        "room_id": room["id"],
        "user_id": req.user_id,
        "display_name": req.display_name,
        "seat": seat
    }))

    return {"room_id": room["id"], "seat": seat}


class StartDraftRequest(BaseModel):
    user_id: str


def _fetch_odds(league_ids: list[str]) -> dict:
    """Fetch Polymarket odds for each league, keyed by (league_id, normalized team name).
    Best-effort: a league with no slug, or a failed fetch, is silently skipped rather than
    blocking the draft from starting.
    """
    league_rows = execute(
        db.table("leagues").select("id,polymarket_slug").in_("id", league_ids)
    ).data

    probs_by_team = {}
    for league in league_rows:
        slug = league.get("polymarket_slug")
        if not slug:
            continue
        try:
            df = get_polymarket_data(slug)
        except Exception:
            continue
        for _, row in df.iterrows():
            key = (league["id"], row["team"].strip().casefold())
            probs_by_team[key] = float(row["prob"])
    return probs_by_team


def _match_prob(team: dict, probs_by_team: dict) -> Optional[float]:
    for name in (team.get("display_name"), team.get("short_display_name"), team.get("location")):
        if not name:
            continue
        prob = probs_by_team.get((team["league_id"], name.strip().casefold()))
        if prob is not None:
            return prob
    return None


@app.post("/rooms/{code}/start")
def start_draft(code: str, req: StartDraftRequest):
    room = execute(db.table("rooms").select("*").eq("code", code).single()).data
    if not room:
        raise HTTPException(404, "Room not found")
    if room["host_id"] != req.user_id:
        raise HTTPException(403, "Only the host can start this draft")
    if room["status"] != "lobby":
        raise HTTPException(400, "Draft already started")

    leagues = room.get("leagues") or []
    if not leagues:
        raise HTTPException(400, "No leagues selected for this draft")

    teams = execute(
        db.table("teams").select("*")
        .eq("is_active", True)
        .in_("league_id", leagues)
    ).data
    if not teams:
        raise HTTPException(400, "No teams found for the selected leagues")

    probs_by_team = _fetch_odds(leagues)

    pool_rows = [
        {
            "room_id": room["id"],
            "team_id": team["id"],
            "display_name": team["display_name"],
            "league_id": team["league_id"],
            "logo_url": team.get("logo_url"),
            "prob": _match_prob(team, probs_by_team),
            "is_drafted": False,
        }
        for team in teams
    ]
    execute(db.table("pool").upsert(pool_rows, on_conflict="room_id,team_id"))

    execute(db.table("rooms").update({"status": "drafting"}).eq("id", room["id"]))
    return {"ok": True}


### Endpoint 4 — Get room state

@app.get("/rooms/{room_id}")
def get_room(room_id: str, hide_drafted: bool = False):
    room = execute(db.table("rooms").select("*").eq("id", room_id).single()).data
    players = execute(db.table("room_players").select("*").eq("room_id", room["id"]).order("seat")).data
    picks = execute(db.table("picks").select("*").eq("room_id", room["id"]).order("pick_number")).data
    pool_query = db.table("pool").select("*").eq("room_id", room["id"])
    if hide_drafted:
        pool_query = pool_query.eq("is_drafted", False)
    pool = execute(pool_query).data
    return {"room": room, "players": players, "picks": picks, "pool": pool}


@app.get("/rooms")
def list_rooms(user_id: str):
    memberships = execute(db.table("room_players").select("room_id").eq("user_id", user_id)).data
    room_ids = [m["room_id"] for m in memberships]
    if not room_ids:
        return {"rooms": []}
    rooms = execute(db.table("rooms").select("*").in_("id", room_ids)).data
    return {"rooms": rooms}


@app.get("/rooms/{code}/players")
def room_players(code: str):
    room = execute(db.table("rooms").select("*").eq("code", code).single()).data
    if not room:
        raise HTTPException(404, "Room not found")
    players = execute(db.table("room_players").select("*").eq("room_id", room["id"]).order("seat")).data
    return {"players": players}


class UpdateRoomRequest(BaseModel):
    user_id: str
    draft_name: Optional[str] = None
    snake: Optional[bool] = None
    rounds: Optional[int] = None
    mode: Optional[str] = None
    odds_provider: Optional[str] = None
    leagues: Optional[list[str]] = None


@app.put("/rooms/{code}")
def update_room(code: str, req: UpdateRoomRequest):
    room = execute(db.table("rooms").select("*").eq("code", code).single()).data
    if not room:
        raise HTTPException(404, "Room not found")
    if room["host_id"] != req.user_id:
        raise HTTPException(403, "Only the host can edit this draft")
    if room["status"] != "lobby":
        raise HTTPException(400, "Cannot edit a draft that has already started")

    updates = {k: v for k, v in {
        "draft_name": req.draft_name,
        "snake": req.snake,
        "rounds": req.rounds,
        "mode": req.mode,
        "odds_provider": req.odds_provider,
        "leagues": req.leagues,
    }.items() if v is not None}

    if updates:
        try:
            execute(db.table("rooms").update(updates).eq("id", room["id"]))
        except Exception as e:
            raise HTTPException(500, f"Database error: {e}")
    return {"ok": True}


@app.delete("/rooms/{code}")
def delete_room(code: str, user_id: str):
    room = execute(db.table("rooms").select("*").eq("code", code).single()).data
    if not room:
        raise HTTPException(404, "Room not found")
    if room["host_id"] != user_id:
        raise HTTPException(403, "Only the host can delete this draft")

    rid = room["id"]
    execute(db.table("picks").delete().eq("room_id", rid))
    execute(db.table("pool").delete().eq("room_id", rid))
    execute(db.table("room_players").delete().eq("room_id", rid))
    execute(db.table("rooms").delete().eq("id", rid))
    return {"ok": True}


class PickRequest(BaseModel):
    player_name: str
    user_id: str
    team: str
    league: str
    round: int
    pick_number: int

@app.post("/rooms/{room_id}/pick")
def make_pick(room_id: str, req: PickRequest):
    # room = execute(db.table("rooms").select("*").eq("id", room_id).single()).data
    # if room["status"] != "drafting":
    #     raise HTTPException(400, "Draft not in progress")

    # get prob at time of pick
    # pool_entry = execute(db.table("pool").select("prob").eq("room_id", room["id"]).eq("team", req.team).single()).data

    execute(db.table("picks").insert({
        "room_id": room_id,
        "user_id": req.user_id,
        "display_name": req.player_name,
        "team": req.team,
        "league": req.league,
        "prob_at_pick": None,
        "round": req.round,
        "pick_number": req.pick_number
    }))

    execute(db.table("pool").update({"is_drafted": True}).eq("room_id", room_id).eq("team_id", req.team))

    # # check if draft is finished
    # players = execute(db.table("room_players").select("*").eq("room_id", room["id"])).data
    # total_picks = room["rounds"] * len(players)
    # picks_made = execute(db.table("picks").select("id", count="exact").eq("room_id", room["id"])).count

    # if picks_made >= total_picks:
    #     execute(db.table("rooms").update({"status": "finished"}).eq("id", room["id"]))

    return {"ok": True, "round": req.round, "pick_number": req.pick_number}


@app.post("/rooms/{room_id}/terminate")
def terminate_draft(room_id: str):
    execute(db.table("rooms").update({"status": "finished"}).eq("id", room_id))
    return {"ok": True}


@app.get("/teams")
def get_teams(
    league_id: str | None = None,
    espn_sport: str | None = None,
    espn_league: str | None = None,
):
    query = db.table("teams").select("*").eq("is_active", True)

    if league_id:
        query = query.in_("league_id", league_id.split(","))
    if espn_sport:
        query = query.in_("espn_sport", espn_sport.split(","))
    if espn_league:
        query = query.in_("espn_league", espn_league.split(","))

    teams = execute(query).data
    return {"teams": teams}


@app.get("/leagues")
def get_leagues(id: str | None = None):
    query = db.table("leagues").select("*").eq("is_active", True)
    if id:
        query = query.in_("id", id.split(","))
    leagues = execute(query).data
    return {"leagues": leagues}


@app.get("/rooms/{room_id}/pool")
def get_room_pool(room_id: str):
    pool = execute(db.table("pool").select("*").eq("room_id", room_id)).data
    return {"pool": pool}
