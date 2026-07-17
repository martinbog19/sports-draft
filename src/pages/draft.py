import streamlit as st

from src.utils import prob_color


def render_draft_page():
    players = st.session_state.players
    n_players = len(players)

    if st.session_state.snake:
        if st.session_state.round % 2 == 1:
            player_idx = st.session_state.pick
        else:
            player_idx = n_players - 1 - st.session_state.pick
    else:
        player_idx = st.session_state.pick

    current_player = players[player_idx]
    pick_number = (
        (st.session_state.round - 1) * n_players
        + st.session_state.pick
        + 1
    )

    st.title("Draft Room")
    st.subheader(
        f"Round {st.session_state.round}/{st.session_state.rounds} "
        f"• Pick {pick_number} "
        f"• {current_player} is on the clock"
    )

    left, right = st.columns([3, 1])

    with left:
        _render_pool(current_player, pick_number, n_players)

    with right:
        _render_board(players)


def _render_pool(current_player, pick_number, n_players):
    st.header("Available Draft Pool")

    with st.expander("🔍 Advanced Filters"):
        c1, c2 = st.columns(2)
        with c1:
            league_filter = st.multiselect(
                "League",
                sorted(st.session_state.data["league"].unique())
            )
        with c2:
            search = st.text_input("Search team")
        hide_zero_odds = st.toggle("Hide 0% odds", value=True)

    pool = st.session_state.data.copy()

    if league_filter:
        pool = pool[pool["league"].isin(league_filter)]
    if search:
        pool = pool[pool["team"].str.contains(search, case=False, na=False)]
    if hide_zero_odds:
        pool = pool[pool["prob"] > 0]

    h1, h2, h3, h4 = st.columns([3, 1, 1, 1])
    h1.markdown("**Team**")
    h2.markdown("**League**")
    h3.markdown("**Win Probability**")

    for idx, row in pool.iterrows():
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        c1.write(row["team"])
        c2.write(row["league"])
        c3.markdown(
            f'<span style="color:{prob_color(row["prob"])};font-weight:bold">'
            f'{row["prob"]:.1f}%</span>',
            unsafe_allow_html=True
        )
        if c4.button("Draft", key=f"draft_{idx}"):
            st.toast(
                f"Pick {pick_number}: **{current_player}** chose **{row['team']}**.",
                duration=10
            )
            st.session_state.drafts[current_player].append(row["team"])
            st.session_state.data = st.session_state.data.drop(idx)
            st.session_state.pick += 1

            if st.session_state.pick >= n_players:
                st.session_state.pick = 0
                st.session_state.round += 1

            if st.session_state.round > st.session_state.rounds:
                st.session_state.page = "finished"

            st.rerun()


def _render_board(players):
    st.header("Draft Board")
    for player in players:
        st.markdown(f"**{player}**")
        picks = st.session_state.drafts[player]
        if picks:
            for i, team in enumerate(picks, start=1):
                st.write(f"{i}. {team}")
        else:
            st.caption("No picks yet")
        st.divider()
