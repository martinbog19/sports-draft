import streamlit as st


def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "setup"
    if "player_inputs" not in st.session_state:
        st.session_state.player_inputs = ["Player 1", "Player 2"]
