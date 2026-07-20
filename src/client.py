import requests

BASE = "http://localhost:8000"  # your FastAPI server

def create_room(user_id, host_name, draft_name, snake, rounds, mode):
    return requests.post(
        f"{BASE}/rooms",
        json={
            "user_id": user_id,
            "host_name": host_name,
            "draft_name": draft_name,
            "snake": snake,
            "rounds": rounds,
            "mode": mode,
        }
    )

def join_room(user_id, code, display_name):
    return requests.post(
        f"{BASE}/rooms/{code}/join",
        json={"user_id": user_id, "display_name": display_name}
    ).json()

def get_room(code):
    return requests.get(f"{BASE}/rooms/{code}").json()

def list_rooms(user_id):
    return requests.get(f"{BASE}/rooms", params={"user_id": user_id}).json()

# def make_pick(code, player_name, team, league, round, pick_number):
#     return requests.post(f"{BASE}/rooms/{code}/pick", json={
#         "player_name": player_name, "team": team, "league": league,
#         "round": round, "pick_number": pick_number
#     }).json()