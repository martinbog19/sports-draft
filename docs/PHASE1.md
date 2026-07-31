# Phase 1 — Actionable Steps

Goal: two people on different laptops completing a draft together, using the existing Streamlit UI.

---

## Step 1 — Supabase project (1 hour)

1. Go to supabase.com, create a free account, create a new project
2. Once created, go to **Settings → General** and copy the Project URL (`https://<ref>.supabase.co`).
   Then go to **Settings → API** and copy the **Secret key** (`sb_secret_...`).
   - Publishable key (`sb_publishable_...`) = safe for browsers, use later in the React frontend
   - Secret key (`sb_secret_...`) = privileged, use in FastAPI only, never expose publicly
3. Create a `.env` file at the root of this repo:
```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=sb_secret_...
```
4. Add `.env` to `.gitignore` immediately

---

## Step 2 — Create the database tables (1–2 hours)

In Supabase, go to **SQL Editor** and run:

```sql
-- Users are handled by Supabase Auth automatically

create table rooms (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,         -- 6-char invite code, e.g. "XK92BF"
  host_id uuid references auth.users,
  snake boolean default true,
  rounds int default 5,
  mode text default 'Easy',
  status text default 'lobby',       -- lobby | drafting | finished
  created_at timestamp default now()
);

create table room_players (
  id uuid primary key default gen_random_uuid(),
  room_id uuid references rooms on delete cascade,
  user_id uuid references auth.users,
  display_name text not null,
  seat int not null                  -- draft order position
);

create table pool (
  id uuid primary key default gen_random_uuid(),
  room_id uuid references rooms on delete cascade,
  team text not null,
  league text not null,
  prob float not null
);

create table picks (
  id uuid primary key default gen_random_uuid(),
  room_id uuid references rooms on delete cascade,
  user_id uuid references auth.users,
  display_name text not null,
  team text not null,
  league text not null,
  prob_at_pick float,
  round int not null,
  pick_number int not null,
  created_at timestamp default now()
);
```

Enable **Realtime** on the `picks` table: go to **Database → Replication**, toggle on the `picks` table.

```sql
alter publication supabase_realtime add table picks
```

---

## Step 3 — FastAPI backend (3–5 days)

### Setup

```bash
mkdir backend && cd backend
pip install fastapi uvicorn supabase python-dotenv
```

Create `backend/main.py`:

```python
from fastapi import FastAPI, HTTPException
from supabase import create_client
from pydantic import BaseModel
from dotenv import load_dotenv
import os, random, string

load_dotenv()
app = FastAPI()
db = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def random_code(n=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))
```

### Endpoint 1 — Create a room

```python
class CreateRoomRequest(BaseModel):
    host_name: str
    snake: bool = True
    rounds: int = 5
    mode: str = "Easy"
    leagues: list[str] = []

@app.post("/rooms")
def create_room(req: CreateRoomRequest):
    code = random_code()
    room = db.table("rooms").insert({
        "code": code,
        "snake": req.snake,
        "rounds": req.rounds,
        "mode": req.mode,
        "status": "lobby"
    }).execute().data[0]

    db.table("room_players").insert({
        "room_id": room["id"],
        "display_name": req.host_name,
        "seat": 0
    }).execute()

    return {"code": code, "room_id": room["id"]}
```

### Endpoint 2 — Join a room

```python
class JoinRoomRequest(BaseModel):
    display_name: str

@app.post("/rooms/{code}/join")
def join_room(code: str, req: JoinRoomRequest):
    room = db.table("rooms").select("*").eq("code", code).single().execute().data
    if not room:
        raise HTTPException(404, "Room not found")
    if room["status"] != "lobby":
        raise HTTPException(400, "Draft already started")

    players = db.table("room_players").select("*").eq("room_id", room["id"]).execute().data
    seat = len(players)

    db.table("room_players").insert({
        "room_id": room["id"],
        "display_name": req.display_name,
        "seat": seat
    }).execute()

    return {"room_id": room["id"], "seat": seat}
```

### Endpoint 3 — Start the draft (fetches odds, populates pool)

```python
@app.post("/rooms/{code}/start")
def start_draft(code: str):
    room = db.table("rooms").select("*").eq("code", code).single().execute().data

    # fetch odds and write to pool table
    # (move your existing get_polymarket_data / get_kalshi_data logic here)
    pool_rows = fetch_odds_for_room(room)
    db.table("pool").insert(pool_rows).execute()

    db.table("rooms").update({"status": "drafting"}).eq("id", room["id"]).execute()
    return {"ok": True}
```

### Endpoint 4 — Get room state

```python
@app.get("/rooms/{code}")
def get_room(code: str):
    room = db.table("rooms").select("*").eq("code", code).single().execute().data
    players = db.table("room_players").select("*").eq("room_id", room["id"]).order("seat").execute().data
    picks = db.table("picks").select("*").eq("room_id", room["id"]).order("pick_number").execute().data
    pool = db.table("pool").select("*").eq("room_id", room["id"]).execute().data
    return {"room": room, "players": players, "picks": picks, "pool": pool}
```

### Endpoint 5 — Make a pick

```python
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
```

Run it with:
```bash
uvicorn backend.main:app --reload
```

---

## Step 4 — Wire Streamlit to the backend (2–3 days)

Replace `st.session_state` logic with calls to your FastAPI server. Add a `src/client.py`:

```python
import requests

BASE = "http://localhost:8000"  # your FastAPI server

def create_room(host_name, snake, rounds, mode):
    return requests.post(f"{BASE}/rooms", json={
        "host_name": host_name, "snake": snake, "rounds": rounds, "mode": mode
    }).json()

def join_room(code, display_name):
    return requests.post(f"{BASE}/rooms/{code}/join", json={"display_name": display_name}).json()

def get_room(code):
    return requests.get(f"{BASE}/rooms/{code}").json()

def make_pick(code, player_name, team, league, round, pick_number):
    return requests.post(f"{BASE}/rooms/{code}/pick", json={
        "player_name": player_name, "team": team, "league": league,
        "round": round, "pick_number": pick_number
    }).json()
```

Then in the setup page, instead of wiring state locally:
```python
if st.button("Start Draft!"):
    result = create_room(host_name, snake, rounds, mode)
    st.session_state.room_code = result["code"]
    st.session_state.page = "lobby"  # new waiting screen
```

---

## Step 5 — Handle real-time with polling (1 day)

Supabase Realtime works natively in React — in Streamlit, the simplest approach is polling: check the DB every few seconds and rerun if something changed.

```python
# at the top of the draft page render
import time

room_state = get_room(st.session_state.room_code)
last_pick_count = len(room_state["picks"])

if last_pick_count != st.session_state.get("last_pick_count", 0):
    st.session_state.last_pick_count = last_pick_count
    st.rerun()

# auto-refresh every 3 seconds while waiting for other players
time.sleep(3)
st.rerun()
```

This is a workaround — it's not elegant and will feel slightly laggy, but it works for validating the backend. You'll replace it with true WebSocket push when you build the React frontend in Phase 2.

---

## Milestone check

You're done with Phase 1 when:
- [ ] Player A creates a room and gets a code
- [ ] Player B enters the code and joins
- [ ] Both see the same draft pool
- [ ] When A makes a pick, B's screen updates within a few seconds
- [ ] The finished page shows the same results for both players
- [ ] Closing and reopening the browser doesn't lose the draft state
