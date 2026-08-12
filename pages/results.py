import streamlit as st
import pandas as pd

from src.client import get_room

st.title("Results")

if st.button("Back to home", type="secondary"):
    st.switch_page("pages/home.py")

room_id = st.session_state.results_room
room_state = get_room(room_id)
picks, pool = room_state["picks"], room_state["pool"]

picks = pd.DataFrame(picks)
pool = pd.DataFrame(pool)

# st.dataframe(picks)r
# st.dataframe(pool)

st.dataframe(picks.merge(pool, left_on="team", right_on="team_id", how="left")[
    ["pick_number", "round", "display_name_y", "display_name_x", "league_id"]
])