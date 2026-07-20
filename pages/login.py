import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.title("The Field")
st.divider()

tab_login, tab_signup = st.tabs(["Sign in", "Create account"])

with tab_login:
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in", type="primary", use_container_width=True):
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = {"id": response.user.id, "email": response.user.email}
                st.session_state.access_token = response.session.access_token
                st.switch_page("pages/home.py")
            except Exception:
                st.error("Invalid email or password.")

with tab_signup:
    with st.form("signup_form"):
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        display_name = st.text_input("Display name")
        if st.form_submit_button("Create account", type="primary", use_container_width=True):
            try:
                response = supabase.auth.sign_up({"email": new_email, "password": new_password})
                st.session_state.user = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "display_name": display_name,
                }
                st.session_state.access_token = response.session.access_token
                st.switch_page("pages/home.py")
            except Exception as e:
                st.error(f"Could not create account: {e}")
