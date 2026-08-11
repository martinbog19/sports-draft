import streamlit as st
from archive.pages.draft import render_draft_page

st.title("Draft Room")


room = st.session_state.drafting_room


st.write(room)

# ── Intended draft flow (pseudo-code) ───────────────────────────────────────
#
# Guard:
#   if "drafting_room" not in st.session_state: switch_page("pages/home.py")
#   code = room["code"]
#
# 1. Fetch full room state every rerun (source of truth is Supabase, not
#    session_state — several browsers are looking at the same room):
#       state = get_room(code)
#       room, players, picks, pool = state["room"], state["players"], state["picks"], state["pool"]
#       players.sort(by="seat")
#       picks.sort(by="pick_number")
#
#   if room["status"] == "finished": render results/board only, stop here.
#
# 2. Work out whose turn it is (mirrors archive/pages/draft.py logic, but
#    driven by len(picks) instead of session_state counters, since state
#    now lives in the DB and any player's browser can compute this):
#       n = len(players)
#       pick_number = len(picks) + 1
#       round_num = (pick_number - 1) // n + 1
#       seat_in_round = (pick_number - 1) % n
#       if room["snake"] and round_num % 2 == 0: seat_in_round = n - 1 - seat_in_round
#       current_player = players[seat_in_round]
#       my_turn = current_player["user_id"] == st.session_state.user["id"]
#
# 3. Render the draft board (left/right split like the archived page):
#       left, right = st.columns([3, 1])
#       right: show picks so far, grouped "All picks" / "By player"
#       left: show pool + turn banner ("You're on the clock" / "waiting on X")
#
# 4. Render the available pool:
#       available = [p for p in pool if not p["is_drafted"]]
#       group/filter by league_id, search by display_name
#       if room["mode"] == "Easy": show prob, colored
#       elif room["mode"] == "Blurred": show prob, blurred
#       elif room["mode"] == "Expert": hide prob entirely
#       for each row: "Draft" button, disabled unless my_turn
#
# 5. On "Draft" click:
#       make_pick(code, team_id=row["team_id"], round=round_num, pick_number=pick_number)
#       -> backend: insert into picks, set pool.is_drafted=True for that team_id,
#          if picks_made >= rounds * n: set rooms.status = "finished"
#       st.rerun()
#
# 6. Live-ness across browsers: Streamlit only reruns on interaction, so a
#    non-active player's screen won't auto-update when someone else picks.
#    Need either st.autorefresh (poll get_room every few seconds) or a
#    manual "Refresh" button until something push-based is wired up.