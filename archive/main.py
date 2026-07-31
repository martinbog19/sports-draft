import streamlit as st

from src.state import init_state
from archive.pages.setup import render_setup_page
from archive.pages.draft import render_draft_page
from archive.pages.finished import render_finished_page

st.set_page_config(page_title="The field", layout="wide", page_icon="🏈")

init_state()

if st.session_state.page == "setup":
    render_setup_page()
elif st.session_state.page == "draft":
    render_draft_page()
elif st.session_state.page == "finished":
    render_finished_page()
