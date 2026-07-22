import os

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(page_title="Login", page_icon="🏈", layout="centered")
st.title("The Field")
st.divider()

tab_login, tab_signup = st.tabs(["Sign in", "Create account"])

with tab_login:
    with st.form("login_form"):
        username = st.text_input("Username :red[*]")
        password = st.text_input("Password :red[*]", type="password")
        if st.form_submit_button("Sign in", type="primary", use_container_width=True):
            try:
                clean = username.strip().lower()
                result = supabase.table("profiles").select("email, display_name").eq("username", clean).execute()
                if not result.data:
                    st.error("Username not found.")
                else:
                    profile = result.data[0]
                    response = supabase.auth.sign_in_with_password(
                        {"email": profile["email"], "password": password}
                    )
                    st.session_state.user = {
                        "id": response.user.id,
                        "username": clean,
                        "display_name": profile["display_name"],
                        "email": profile["email"],
                    }
                    st.session_state.access_token = response.session.access_token
                    st.switch_page("pages/home.py")
            except Exception:
                st.error("Invalid username or password.")

with tab_signup:
    with st.form("signup_form"):
        new_username = st.text_input("Username :red[*]")
        new_name = st.text_input("Name", help="What should we call you?")
        new_email = st.text_input("Email :red[*]")
        new_password = st.text_input("Password :red[*]", type="password")
        new_password_confirm = st.text_input("Confirm password :red[*]", type="password")
        if st.form_submit_button("Create account", type="primary", use_container_width=True):
            if not new_username.strip():
                st.error("Username is required.")
            elif not new_email.strip():
                st.error("Email is required.")
            elif not new_password:
                st.error("Password is required.")
            elif new_password != new_password_confirm:
                st.error("Passwords don't match.")
            else:
                try:
                    clean = new_username.strip().lower()
                    email = new_email.strip().lower()
                    display_name = new_name.strip() or clean
                    response = supabase.auth.sign_up({"email": email, "password": new_password})
                    supabase.table("profiles").insert({
                        "user_id": response.user.id,
                        "username": clean,
                        "display_name": display_name,
                        "email": email,
                    }).execute()
                    st.session_state.user = {
                        "id": response.user.id,
                        "username": clean,
                        "display_name": display_name,
                        "email": email,
                    }
                    st.session_state.access_token = response.session.access_token
                    st.switch_page("pages/home.py")
                except Exception as e:
                    st.error(f"Could not create account: {e}")
