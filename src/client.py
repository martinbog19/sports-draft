import requests

BASE = "http://localhost:8000"


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


def get_room(code):
    return requests.get(f"{BASE}/rooms/{code}").json()


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
