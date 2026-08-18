import code
import os
import requests


BASE = os.getenv("BACKEND_URL", "http://localhost:8000")


def create_room(user_id, host_name, draft_name, snake, rounds, mode, odds_provider=None, leagues=None):
    return requests.post(
        f"{BASE}/rooms",
        json={
            "user_id": user_id,
            "host_name": host_name,
            "draft_name": draft_name,
            "snake": snake,
            "rounds": rounds,
            "mode": mode,
            "odds_provider": odds_provider,
            "leagues": leagues or [],
        }
    )


def join_room(user_id, code, display_name):
    return requests.post(
        f"{BASE}/rooms/{code}/join",
        json={"user_id": user_id, "display_name": display_name}
    ).json()


def get_room(room_id: str, hide_drafted: bool = False):
    params = {"hide_drafted": hide_drafted} if hide_drafted else {}
    return requests.get(f"{BASE}/rooms/{room_id}", params=params).json()


def get_room_players(code):
    return requests.get(f"{BASE}/rooms/{code}/players").json()


def list_rooms(user_id):
    return requests.get(f"{BASE}/rooms", params={"user_id": user_id}).json()


def update_room(code, user_id, draft_name=None, snake=None, rounds=None, mode=None, odds_provider=None, leagues=None):
    payload = {"user_id": user_id}
    if draft_name is not None:
        payload["draft_name"] = draft_name
    if snake is not None:
        payload["snake"] = snake
    if rounds is not None:
        payload["rounds"] = rounds
    if mode is not None:
        payload["mode"] = mode
    if odds_provider is not None:
        payload["odds_provider"] = odds_provider
    if leagues is not None:
        payload["leagues"] = leagues
    return requests.put(f"{BASE}/rooms/{code}", json=payload).json()


def delete_room(code, user_id):
    return requests.delete(f"{BASE}/rooms/{code}", params={"user_id": user_id}).json()


def start_draft(code, user_id):
    return requests.post(f"{BASE}/rooms/{code}/start", json={"user_id": user_id}).json()


def get_teams(
        league_id: list[str] | None = None,
        espn_sport: list[str] | None = None,
        espn_league: list[str] | None = None,
    ):
    params = {}
    if league_id:
        params["league_id"] = ",".join(league_id)
    if espn_sport:
        params["espn_sport"] = ",".join(espn_sport)
    if espn_league:
        params["espn_league"] = ",".join(espn_league)
    return requests.get(
        f"{BASE}/teams",
        params=params
    ).json()


def get_leagues(ids: list[str] | None = None):
    params = {"id": ",".join(ids)} if ids else {}
    return requests.get(f"{BASE}/leagues", params=params).json()


def get_room_pool(room_id):
    return requests.get(f"{BASE}/rooms/{room_id}/pool").json()


def make_pick(room_id, user_id, player_name, team, league, round_num, pick_number):
    return requests.post(
        f"{BASE}/rooms/{room_id}/pick",
        json={
            "user_id": user_id,
            "player_name": player_name,
            "team": team,
            "league": league,
            "round": round_num,
            "pick_number": pick_number
        }
    ).json()

def terminate_draft(room_id):
    return requests.post(f"{BASE}/rooms/{room_id}/terminate").json()