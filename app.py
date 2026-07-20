import streamlit as st

st.set_page_config(page_title="The Field", page_icon="🏈", layout="wide")

pg = st.navigation(
    [
        st.Page("pages/login.py", title="Login", default=True),
        st.Page("pages/home.py", title="Home"),
        st.Page("pages/start.py", title="Setup"),
    ],
    position="hidden",
)

pg.run()
