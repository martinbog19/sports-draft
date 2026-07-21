from fastapi import FastAPI, HTTPException
from supabase import create_client
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import os, random, string

load_dotenv()
app = FastAPI()
db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def random_code(n=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))

@app.get("/health")
def health():
      result = db.table("rooms").select("id").limit(1).execute()
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
    code = random_code()
    room = db.table("rooms").insert({
        "code": code,
        "draft_name": req.draft_name,
        "host_id": req.user_id,
        "snake": req.snake,
        "rounds": req.rounds,
        "mode": req.mode,
        "odds_provider": req.odds_provider,
        "leagues": req.leagues,
        "status": "lobby"
    }).execute().data[0]

    db.table("room_players").insert({
        "room_id": room["id"],
        "user_id": req.user_id,
        "display_name": req.host_name,
        "seat": 0
    }).execute()

    return {"code": code, "room_id": room["id"]}


class JoinRoomRequest(BaseModel):
    user_id: str
    display_name: str


@app.post("/rooms/{code}/join")
def join_room(code: str, req: JoinRoomRequest):
    room = db.table("rooms").select("*").eq("code", code).single().execute().data
    if not room:
        raise HTTPException(404, "Room not found")
    if room["status"] != "lobby":
        raise HTTPException(400, "Draft already started")

    players = db.table("room_players").select("*").eq("room_id", room["id"]).execute().data

    if any(p["user_id"] == req.user_id for p in players):
        raise HTTPException(400, "You're already in this draft")

    seat = len(players)

    db.table("room_players").insert({
        "room_id": room["id"],
        "user_id": req.user_id,
        "display_name": req.display_name,
        "seat": seat
    }).execute()

    return {"room_id": room["id"], "seat": seat}


# @app.post("/rooms/{code}/start")
# def start_draft(code: str):
#     room = db.table("rooms").select("*").eq("code", code).single().execute().data

#     # fetch odds and write to pool table
#     # (move your existing get_polymarket_data / get_kalshi_data logic here)
#     pool_rows = fetch_odds_for_room(room)
#     db.table("pool").insert(pool_rows).execute()

#     db.table("rooms").update({"status": "drafting"}).eq("id", room["id"]).execute()
#     return {"ok": True}


### Endpoint 4 — Get room state

@app.get("/rooms/{code}")
def get_room(code: str):
    room = db.table("rooms").select("*").eq("code", code).single().execute().data
    players = db.table("room_players").select("*").eq("room_id", room["id"]).order("seat").execute().data
    picks = db.table("picks").select("*").eq("room_id", room["id"]).order("pick_number").execute().data
    pool = db.table("pool").select("*").eq("room_id", room["id"]).execute().data
    return {"room": room, "players": players, "picks": picks, "pool": pool}


@app.get("/rooms")
def list_rooms(user_id: str):
    memberships = db.table("room_players").select("room_id").eq("user_id", user_id).execute().data
    room_ids = [m["room_id"] for m in memberships]
    if not room_ids:
        return {"rooms": []}
    rooms = db.table("rooms").select("*").in_("id", room_ids).execute().data
    return {"rooms": rooms}


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
    room = db.table("rooms").select("*").eq("code", code).single().execute().data
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
            db.table("rooms").update(updates).eq("id", room["id"]).execute()
        except Exception as e:
            raise HTTPException(500, f"Database error: {e}")
    return {"ok": True}


@app.delete("/rooms/{code}")
def delete_room(code: str, user_id: str):
    room = db.table("rooms").select("*").eq("code", code).single().execute().data
    if not room:
        raise HTTPException(404, "Room not found")
    if room["host_id"] != user_id:
        raise HTTPException(403, "Only the host can delete this draft")

    rid = room["id"]
    db.table("picks").delete().eq("room_id", rid).execute()
    db.table("pool").delete().eq("room_id", rid).execute()
    db.table("room_players").delete().eq("room_id", rid).execute()
    db.table("rooms").delete().eq("id", rid).execute()
    return {"ok": True}


### Endpoint 5 — Make a pick

class PickRequest(BaseModel):
    player_name: str
    team: str
    league: str
    round: int
    pick_number: int

@app.post("/rooms/{code}/pick")
def make_pick(code: str, req: PickRequest):
    room = db.table("rooms").select("*").eq("code", code).single().execute().data
    if room["status"] != "drafting":
        raise HTTPException(400, "Draft not in progress")

    # get prob at time of pick
    pool_entry = db.table("pool").select("prob").eq("room_id", room["id"]).eq("team", req.team).single().execute().data

    db.table("picks").insert({
        "room_id": room["id"],
        "display_name": req.player_name,
        "team": req.team,
        "league": req.league,
        "prob_at_pick": pool_entry["prob"] if pool_entry else None,
        "round": req.round,
        "pick_number": req.pick_number
    }).execute()

    # check if draft is finished
    players = db.table("room_players").select("*").eq("room_id", room["id"]).execute().data
    total_picks = room["rounds"] * len(players)
    picks_made = db.table("picks").select("id", count="exact").eq("room_id", room["id"]).execute().count

    if picks_made >= total_picks:
        db.table("rooms").update({"status": "finished"}).eq("id", room["id"]).execute()

    return {"ok": True}