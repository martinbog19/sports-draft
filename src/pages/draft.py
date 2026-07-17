import streamlit as st

from src.utils import prob_color_continuous


@st.dialog("Confirm custom pick")
def _confirm_custom_pick_dialog(pending, current_player, pick_number, n_players):
    st.write(
        f"Draft **{pending['team']}** ({pending['league']}) "
        f"as pick {pick_number} for **{current_player}**?"
    )
    col_yes, col_no = st.columns(2)
    if col_yes.button("Confirm", type="primary", use_container_width=True):
        st.session_state.drafts[current_player].append(pending["team"])
        st.session_state.pending_toast = f"Pick {pick_number}: **{current_player}** chose **{pending['team']}**."
        del st.session_state.pending_custom_pick
        _advance_pick(n_players)
    if col_no.button("Cancel", use_container_width=True):
        del st.session_state.pending_custom_pick
        st.rerun()


def render_draft_page():
    if "pending_toast" in st.session_state:
        st.toast(st.session_state.pending_toast, duration=10)
        del st.session_state.pending_toast

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

    if st.button("Back to Setup"):
        for i, player in enumerate(st.session_state.players):
            st.session_state[f"player_{i}"] = player
        st.session_state.player_inputs = list(st.session_state.players)
        st.session_state.page = "setup"
        st.rerun()

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

    exp1, exp2 = st.columns([1, 1])
    with exp1:
        with st.expander("Make a custom pick", type="compact"):
            with st.form("custom_pick_form", clear_on_submit=True):
                custom_team = st.text_input("Team name")
                custom_league = st.selectbox(
                    "League",
                    options=st.session_state.get("leagues", [])
                )
                if st.form_submit_button("Draft", type="primary"):
                    if custom_team.strip():
                        st.session_state.pending_custom_pick = {
                            "team": custom_team.strip(),
                            "league": custom_league,
                        }
                        st.rerun()
                    else:
                        st.error("Enter a team name.")

    if pending := st.session_state.get("pending_custom_pick"):
        _confirm_custom_pick_dialog(pending, current_player, pick_number, n_players)

    with exp2:
        with st.expander("Advanced filters", type="compact"):
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

    mode = st.session_state.get("mode", "Easy")
    max_prob = pool["prob"].max() if not pool.empty else 1.0

    pool_cols = [3, 1, 1, 1, 0.5]
    
    h1, h2, h3, _, _ = st.columns(pool_cols)
    h1.markdown("**Team**")
    h2.markdown("**League**")
    if mode != "Expert":
        h3.markdown("**Win Probability**")

    for idx, row in pool.iterrows():
        c1, c2, c3, c4, _ = st.columns(pool_cols)
        c1.write(row["team"])
        c2.write(row["league"])
        if mode == "Easy":
            color = prob_color_continuous(row["prob"], max_prob)
            c3.markdown(
                f'<span style="color:{color};font-weight:bold">'
                f'{row["prob"]:.1f}%</span>',
                unsafe_allow_html=True
            )
        elif mode == "Blurred":
            color = prob_color_continuous(row["prob"], max_prob)
            c3.markdown(
                f'<span style="color:{color};font-weight:bold;filter:blur(4px);'
                f'user-select:none;display:inline-block;">'
                f'{row["prob"]:.1f}%</span>',
                unsafe_allow_html=True
            )
        if c4.button("Draft", key=f"draft_{idx}", type="primary", width="stretch"):
            st.session_state.pending_toast = f"Pick {pick_number}: **{current_player}** chose **{row['team']}**."
            st.session_state.drafts[current_player].append(row["team"])
            st.session_state.data = st.session_state.data.drop(idx)
            _advance_pick(n_players)


def _advance_pick(n_players):
    st.session_state.pick += 1
    if st.session_state.pick >= n_players:
        st.session_state.pick = 0
        st.session_state.round += 1
    if st.session_state.round > st.session_state.rounds:
        st.session_state.page = "finished"
    st.rerun()


def _render_board(players):
    st.header("Draft Board")

    tab_order, tab_players = st.tabs(["All Picks", "By Player"])

    with tab_order:
        n = len(players)
        all_picks = []
        for r in range(1, st.session_state.rounds + 1):
            for pos in range(n):
                if st.session_state.snake and r % 2 == 0:
                    player_idx = n - 1 - pos
                else:
                    player_idx = pos
                player = players[player_idx]
                if r - 1 < len(st.session_state.drafts[player]):
                    global_pick = (r - 1) * n + pos + 1
                    all_picks.append((global_pick, player, st.session_state.drafts[player][r - 1]))

        if all_picks:
            for num, player, team in all_picks:
                st.write(f"**{num}.** {team} — *{player}*")
        else:
            st.caption("No picks yet")

    with tab_players:
        for player in players:
            st.markdown(f"**{player}**")
            picks = st.session_state.drafts[player]
            if picks:
                for i, team in enumerate(picks, start=1):
                    st.write(f"{i}. {team}")
            else:
                st.caption("No picks yet")
            st.divider()
