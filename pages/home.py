import pandas as pd
import streamlit as st

from src.api import get_kalshi_data, get_polymarket_data
from src.client import join_room, list_rooms, update_room, delete_room
from src.config import KALSHI_LEAGUES, POLYMARKET_LEAGUES

# ── Auth guard ─────────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    st.switch_page("pages/login.py")


# ── Header ─────────────────────────────────────────────────────────────────────

col_title, col_user = st.columns([4, 1])
with col_title:
    _greeting = st.session_state.user.get("display_name") or st.session_state.user.get("username", "")
    st.subheader(f"Welcome to the field, {_greeting}!")
with col_user:
    st.caption(st.session_state.user.get("username") or st.session_state.user.get("email", ""))
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/login.py")

st.divider()


# ── Dialogs ────────────────────────────────────────────────────────────────────

@st.dialog("Join a draft")
def join_draft_dialog():
    code = st.text_input("Room code", placeholder="e.g. ABCDEF", max_chars=6)
    if st.button("Join", type="primary", use_container_width=True):
        if not code.strip():
            st.error("Enter a room code.")
        else:
            user = st.session_state.user
            display_name = user.get("display_name") or user["email"].split("@")[0]
            result = join_room(user["id"], code.upper(), display_name)
            if "detail" in result:
                st.error(result["detail"])
            else:
                st.rerun()


@st.dialog("Edit draft")
def edit_draft_dialog():
    room = st.session_state.editing_room
    current_leagues = room.get("leagues") or []

    c1, c2 = st.columns(2)
    with c1:
        snake = st.toggle("Snake draft", value=room.get("snake", True))
    with c2:
        rounds = st.number_input("Rounds", min_value=1, max_value=100, value=room.get("rounds", 25))

    mode = st.pills(
        "Game mode", ["Easy", "Blurred", "Expert"],
        default=room.get("mode"),
        help="Easy: shows % odds · Blurred: color only · Expert: no odds",
        width="stretch",
    )

    if mode is not None and mode != "Expert":
        odds_provider = st.pills(
            "Odds provider", ["Kalshi", "Polymarket"],
            default=room.get("odds_provider") or "Polymarket",
            width="stretch",
        )
    else:
        odds_provider = None

    league_options = KALSHI_LEAGUES if odds_provider == "Kalshi" else POLYMARKET_LEAGUES

    st.caption("Leagues:")
    with st.container(height=100):
        selected_leagues = [
            league for league in league_options
            if st.toggle(league, value=(league in current_leagues), key=f"edit_league_{league}")
        ]

    changed = (
        snake != room.get("snake", True)
        or rounds != room.get("rounds", 25)
        or mode != room.get("mode")
        or odds_provider != room.get("odds_provider")
        or sorted(selected_leagues) != sorted(current_leagues)
    )

    if st.button("Save", type="primary", use_container_width=True, disabled=not (changed and selected_leagues)):
        result = update_room(
            room["code"],
            st.session_state.user["id"],
            snake=snake,
            odds_provider=odds_provider,
            rounds=rounds,
            mode=mode,
            leagues=selected_leagues,
        )
        if "detail" in result:
            st.error(result["detail"])
        else:
            del st.session_state.editing_room
            st.rerun()


@st.dialog("Delete draft")
def delete_draft_dialog():
    room = st.session_state.deleting_room
    name = room.get("draft_name") or room["code"]
    st.warning(f"Delete **{name}**? This cannot be undone.")
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True):
        del st.session_state.deleting_room
        st.rerun()
    if c2.button("Delete", type="primary", use_container_width=True):
        result = delete_room(room["code"], st.session_state.user["id"])
        if "detail" in result:
            st.error(result["detail"])
        else:
            del st.session_state.deleting_room
            st.rerun()


# ── Actions ────────────────────────────────────────────────────────────────────

c1, c2, _ = st.columns([1, 1, 3])
if c1.button("＋ Create new draft", type="primary", use_container_width=True):
    st.switch_page("pages/start.py")
if c2.button("Enter a code", use_container_width=True):
    join_draft_dialog()

# ── Dev shortcut ───────────────────────────────────────────────────────────────

with st.expander("🚧 Dev tools"):
    dev_provider = st.pills("Provider", ["Polymarket", "Kalshi"], default="Polymarket", key="dev_provider")
    if st.button("Launch draft with live odds", use_container_width=True):
        leagues = KALSHI_LEAGUES if dev_provider == "Kalshi" else POLYMARKET_LEAGUES
        fetch_fn = get_kalshi_data if dev_provider == "Kalshi" else get_polymarket_data
        with st.spinner(f"Fetching odds from {dev_provider}..."):
            data = pd.DataFrame()
            for league_name, slug in leagues.items():
                try:
                    df = fetch_fn(slug)
                    df["league"] = league_name
                    data = pd.concat([data, df], ignore_index=True)
                except Exception:
                    pass
        data = data.sort_values("prob", ascending=False)
        players = ["Alice", "Bob", "Charlie"]
        st.session_state.players = players
        st.session_state.snake = True
        st.session_state.round = 1
        st.session_state.pick = 0
        st.session_state.rounds = 5
        st.session_state.drafts = {p: [] for p in players}
        st.session_state.mode = "Easy"
        st.session_state.leagues = sorted(data["league"].unique().tolist())
        st.session_state.data = data
        st.switch_page("pages/draft.py")


# ── My Drafts ──────────────────────────────────────────────────────────────────

from datetime import datetime, timezone

STATUS_ORDER = {"lobby": 0, "drafting": 1, "finished": 2}

st.subheader("My drafts")

try:
    data = list_rooms(st.session_state.user["id"])
    rooms = data.get("rooms", [])

    if not rooms:
        st.caption("No drafts yet. Create one or join with a code.")
    else:
        # ── Controls
        fc, sc = st.columns([3, 2])
        status_filter = fc.pills(
            "Status", ["Lobby", "Drafting", "Finished"],
            selection_mode="multi",
            default=None,
            label_visibility="collapsed",
        )
        sort_by = sc.selectbox(
            "Sort", ["Newest first", "Oldest first", "Name A→Z", "Name Z→A"],
            label_visibility="collapsed",
        )

        # ── Filter
        if status_filter:
            active = [s.lower() for s in status_filter]
            rooms = [r for r in rooms if r["status"] in active]

        # ── Sort
        def sort_key(r):
            if sort_by in ("Name A→Z", "Name Z→A"):
                return (r.get("draft_name") or r["code"]).lower()
            return r.get("created_at") or ""

        rooms.sort(
            key=sort_key,
            reverse=sort_by in ("Newest first", "Name Z→A"),
        )

        # ── Rows
        user_id = st.session_state.user["id"]
        for room in rooms:
            is_host = room.get("host_id") == user_id
            name = room.get("draft_name") or room["code"]
            status = room["status"]

            snake_str = "Snake" if room.get("snake", True) else "Linear"
            rounds_str = f"{room.get('rounds', '?')} rounds"
            mode_str = room.get("mode") or "—"
            provider = room.get("odds_provider")
            provider_str = provider if provider else ("" if mode_str == "Expert" else "—")
            n_leagues = len(room.get("leagues") or [])
            leagues_str = f"{n_leagues} league{'s' if n_leagues != 1 else ''}"

            created_str = ""
            raw_ts = room.get("created_at")
            if raw_ts:
                dt = datetime.fromisoformat(raw_ts).astimezone(timezone.utc)
                created_str = dt.strftime("%b %d, %Y")

            c_info, c_status, c_launch, c_edit, c_delete = st.columns([4, 2, 1, 1, 1])

            c_info.write(f"**{name}**  `{room['code']}`")
            detail_parts = [mode_str]
            if provider_str:
                detail_parts.append(provider_str)
            detail_parts += [rounds_str, snake_str, leagues_str]
            if created_str:
                detail_parts.append(f"Created {created_str}")
            c_info.caption(" · ".join(detail_parts))

            c_status.write(status.capitalize())

            c_launch.button("Launch", key=f"launch_{room['id']}", disabled=True, use_container_width=True)
            if is_host:
                if c_edit.button("Edit", key=f"edit_{room['id']}", use_container_width=True):
                    st.session_state.editing_room = room
                if c_delete.button("Delete", key=f"delete_{room['id']}", use_container_width=True):
                    st.session_state.deleting_room = room

except Exception as e:
    st.warning(f"Could not load drafts — make sure the backend is running. [{e}]")

# Open dialogs if triggered from the list above
if "editing_room" in st.session_state:
    edit_draft_dialog()
if "deleting_room" in st.session_state:
    delete_draft_dialog()



# if st.button("First pick lol"):

#     import numpy as np
#     import time
#     names = ["Alice", "Bob", "Charlie"]
#     pick = np.random.randint(0, len(names))
#     sleeps = np.exp(np.linspace(-20, 0, 200 + pick))
#     container = st.empty()
#     for i, sleep_time in enumerate(sleeps):
#         container.write(names[i % len(names)])
#         time.sleep(sleep_time)
