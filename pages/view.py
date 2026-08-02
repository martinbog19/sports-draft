import streamlit as st
import pandas as pd

st.title("Live")


from src.client import get_teams, get_leagues


room = st.session_state.viewing_room


leagues = pd.DataFrame(get_leagues(room["leagues"])["leagues"]).sort_values(by="display_name").reset_index(drop=True)

st.subheader("Draft pool")
for _, league in leagues.iterrows():
    with st.expander(league["display_name"], type="compact"):
        pool = pd.DataFrame(get_teams(league["espn_sport"], league["espn_league"])["teams"]).sort_values(by="display_name")
        st.write(", ".join(pool["display_name"].to_list()))


if st.button("Launch draft!", type="primary"):
    # Write draft pool to database
    pass