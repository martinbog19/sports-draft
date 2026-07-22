import streamlit as st
from src.pages.draft import render_draft_page

if "players" not in st.session_state:
    st.switch_page("pages/home.py")

render_draft_page()
