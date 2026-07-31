import pandas as pd
import streamlit as st

from src.api import get_kalshi_data, get_polymarket_data
from src.config import KALSHI_LEAGUES, POLYMARKET_LEAGUES
from src.client import create_room


def render_setup_page():
    st.title("Fantasy Draft Setup")

    st.subheader("Players")

    if st.button("Add player"):
        st.session_state.player_inputs.append(
            f"Player {len(st.session_state.player_inputs) + 1}"
        )
        st.rerun()

    players = []
    for i in range(len(st.session_state.player_inputs)):
        players.append(
            st.text_input(
                f"Player {i + 1}",
                placeholder="Enter player name",
                key=f"player_{i}"
            )
        )


    st.subheader("Draft settings")

    c1, c2, c3, _ = st.columns([1, 2, 2, 4])

    with c1:
        snake = st.toggle("Snake draft", value=True)

    with c2:
        rounds = st.number_input(
            "Number of rounds",
            min_value=1,
            max_value=100,
            value=5,
        )

    with c3:
        mode = st.pills(
            "Game mode", ["Easy", "Blurred", "Expert"],
            default="Easy",
            help="Easy: shows % odds · Blurred: color only · Expert: no odds",
            width="stretch"
        )
        if mode != "Expert":
            odds_provider = st.pills(
                "Odds provider", ["Kalshi", "Polymarket"],
                default="Polymarket",
                width="stretch"
            )
        else:
            odds_provider = None

    if odds_provider == "Kalshi":
        leagues = KALSHI_LEAGUES
        fetch_league_fn = get_kalshi_data
    else:
        leagues = POLYMARKET_LEAGUES
        fetch_league_fn = get_polymarket_data


    st.subheader("Draft pool")
    st.caption("Select leagues available in the draft:")

    selected_leagues = st.multiselect(
        "Leagues",
        options=sorted(leagues.keys()),
        default=sorted(leagues.keys()),
        key=f"league_multiselect_{odds_provider}"
    )

    st.divider()

    if st.button("Start Draft!", type="primary"):
        players = [p.strip() for p in players if p.strip()]

        if len(players) < 2:
            st.error("Need at least 2 drafters!")
            st.stop()

        if len(set(players)) < len(players):
            st.error("Player names must be unique.")
            st.stop()
        
        host_name = "Martin_test"
        result = create_room(host_name, snake, rounds, mode)
        st.session_state.room_code = result["code"]
        st.session_state.page = "lobby"  # new waiting screen

        with st.spinner(f"Fetching odds data from {odds_provider}..."):
            data = pd.DataFrame()
            for league_name in selected_leagues:
                league_events = fetch_league_fn(leagues[league_name])
                league_events["league"] = league_name
                data = pd.concat([data, league_events], ignore_index=True)

        draft_pool = data.sort_values("prob", ascending=False)

        st.session_state.players = players
        st.session_state.snake = snake
        st.session_state.rounds = rounds
        st.session_state.mode = mode
        st.session_state.leagues = sorted(draft_pool["league"].unique().tolist())
        st.session_state.data = draft_pool
        st.session_state.drafts = {p: [] for p in players}
        st.session_state.round = 1
        st.session_state.pick = 0
        # st.session_state.page = "draft"

        # st.rerun()
