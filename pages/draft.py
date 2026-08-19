import streamlit as st
# from archive.pages.draft import render_draft_page

from src.client import get_room, get_room_players, get_room_pool, make_pick, terminate_draft

st.title("Draft Room")

room = st.session_state.drafting_room

room_state = get_room(room["id"])
room, players, picks, pool = room_state["room"], room_state["players"], room_state["picks"], room_state["pool"]

players.sort(key=lambda x: x["seat"])

n = len(players)
pick_number = len(picks) + 1
round_num = (pick_number - 1) // n + 1

seat_in_round = (pick_number - 1) % n
if room["snake"] and round_num % 2 == 0:
    seat_in_round = n - 1 - seat_in_round

current_player = players[seat_in_round]

st.write(f"Round {round_num} • Pick {pick_number} of {n * room['rounds']} • {current_player['display_name']} is on the clock")

my_turn = current_player["user_id"] == st.session_state.user["id"]


settings = st.columns([1, 1, 1, 2])
with settings[0]:
    sort_by = st.selectbox(
        "Sort by",
        options=["Probability", "Team name"],
        index=0,
    )
with settings[1]:
    league_list = sorted(set(team["league_id"] for team in pool))
    selected_leagues = st.pills(
        "Filter by league",
        options=league_list,
        selection_mode="multi",
    )
    selected_leagues = league_list if not selected_leagues else selected_leagues

if sort_by == "Probability":
    pool.sort(key=lambda x: (x["prob"] is None, -(x["prob"] or 0), x["display_name"]))
elif sort_by == "Team name":
    pool.sort(key=lambda x: x["display_name"])

cols = st.columns([3, 2])
for team in pool:
    if team["is_drafted"]:
        continue
    if team["league_id"] not in selected_leagues:
        continue
    with cols[0]:
        with st.container(horizontal=True, vertical_alignment="top", border=True, gap="xxsmall", height=60):

            st.space()
            st.image(team["logo_url"], width=25)
            st.space("xxsmall")
            st.write(team["display_name"])
            st.caption(team["league_id"].upper())
            
            st.write(f"{team['prob']:.1f}%" if team["prob"] is not None else "—")
            st.space("large")

            if st.button("Draft", key=f"draft_{team['team_id']}", type="primary", disabled=not my_turn):
                make_pick(
                    room_id=room["id"],
                    user_id=st.session_state.user["id"],
                    player_name=st.session_state.user["display_name"],
                    team=team["team_id"],
                    league=team["league_id"],
                    round_num=round_num,
                    pick_number=pick_number,
                )

                if pick_number >= n * room["rounds"]:
                    terminate_draft(room["id"])
                    st.session_state.results_room = room["id"]
                    st.switch_page("pages/results.py")

                st.rerun()

with cols[1]:
    tab_all, tab_by_player, tab_my = st.tabs(["All picks", "By player", "My picks"])

    with tab_all:
        if not picks:
            st.caption("No picks yet.")
        for pick in picks:
            team = next((t for t in pool if t["team_id"] == pick["team"]), None)
            if team is None:
                continue
            pick_str = f"**#{pick['pick_number']}** "
            pick_str += pick["display_name"] + "  •  " + team["display_name"]

            # with st.container(horizontal=True, vertical_alignment="center"):
            st.write(pick_str)


    with tab_by_player:
        for player in players:
            st.write(f"**{player['display_name']}**")
            player_picks = [pick for pick in picks if pick["user_id"] == player["user_id"]]
            if not player_picks:
                st.caption("No picks yet.")
                continue
            for pick in player_picks:
                team = next((t for t in pool if t["team_id"] == pick["team"]), None)
                if team is None:
                    continue
                # with st.container(horizontal=True, vertical_alignment="center", border=True, gap="xxsmall"):
                pick_str = f"**#{pick['pick_number']}** "
                pick_str += pick["display_name"] + "  •  " + team["display_name"]
                st.write(pick_str)
            st.divider()
        

    with tab_my:
        if not picks:
            st.caption("No picks yet.")
        for pick in picks:
            if pick["user_id"] != st.session_state.user["id"]:
                continue
            team = next((t for t in pool if t["team_id"] == pick["team"]), None)
            if team is None:
                continue
            with st.container(horizontal=True, vertical_alignment="center", border=True, gap="xxsmall"):
                st.space()
                st.image(team["logo_url"], width=40)
                st.space("xxsmall")
                st.write(f"You drafted {team['display_name']} ({team['league_id'].upper()})")
                st.caption(f"Round {pick['round']} • Pick {pick['pick_number']}")
