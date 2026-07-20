import pandas as pd
import streamlit as st

# from src.api import get_kalshi_data, get_polymarket_data
from src.config import KALSHI_LEAGUES, POLYMARKET_LEAGUES
from src.client import create_room



st.title("Fantasy draft setup")

draft_name = st.text_input("Draft name", placeholder="Choose your draft name!")

st.subheader("Draft settings")

c1, c2, c3, c4, c5 = st.columns([1, 2, 2, 2, 1])

with c1:
    snake = st.toggle("Snake draft", value=True)

with c2:
    rounds = st.number_input(
        "Number of rounds",
        min_value=1,
        max_value=100,
        value=25,
    )

with c3:
    mode = st.pills(
        "Game mode", ["Easy", "Blurred", "Expert"],
        # default="Easy",
        help="Easy: shows % odds · Blurred: color only · Expert: no odds",
        width="stretch"
    )
with c4:
    if mode is not None and mode != "Expert":
        odds_provider = st.pills(
            "Odds provider", ["Kalshi", "Polymarket"],
            default="Polymarket",
            width="stretch"
        )
    else:
        odds_provider = None

leagues = KALSHI_LEAGUES if odds_provider == "Kalshi" else POLYMARKET_LEAGUES

st.subheader("Draft pool")
st.caption("Select leagues available in the draft:")

# selected_leagues = st.multiselect(
#     "Leagues",
#     options=sorted(leagues.keys()),
#     default=sorted(leagues.keys()),
#     key=f"league_multiselect_{odds_provider}"
# )

with st.container(height=100):
    selected_leagues = [
        league for league in leagues
        if st.toggle(league, value=True, key=f"league_{league}")
    ]

st.divider()

@st.dialog("Draft created!")
def show_room_code(code, name):
    st.markdown(f"### `{code}`")
    st.caption(f"Share this code with your friends to join **{name}**.")
    st.code(code, language=None)
    if st.button("Done", type="primary", use_container_width=True):
        st.switch_page("pages/home.py")


ready = (
    bool(draft_name.strip())
    and mode is not None
    and (mode == "Expert" or odds_provider is not None)
    and len(selected_leagues) > 0
)

if st.button("Create draft!", type="primary", disabled=not ready):

    user = st.session_state.get("user", {})
    result = create_room(user.get("id"), user.get("display_name", "Host"), draft_name, snake, rounds, mode)

    if result.status_code == 200:
        st.session_state.room_code = result.json()["code"]
        show_room_code(result.json()["code"], draft_name)