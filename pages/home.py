import streamlit as st

from src.client import join_room, list_rooms

# ── Auth guard ─────────────────────────────────────────────────────────────────

if "user" not in st.session_state:
    st.switch_page("pages/login.py")


# ── Header ─────────────────────────────────────────────────────────────────────

col_title, col_user = st.columns([4, 1])
with col_title:
    st.title("The Field")
with col_user:
    st.caption(st.session_state.user["email"])
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.switch_page("pages/login.py")

st.divider()


# ── Actions ────────────────────────────────────────────────────────────────────

@st.dialog("Join a draft")
def join_draft_dialog():
    code = st.text_input("Room code", placeholder="e.g. XK92BF", max_chars=6)
    name = st.text_input("Your name")
    if st.button("Join", type="primary", use_container_width=True):
        if not code.strip() or not name.strip():
            st.error("Fill in both fields.")
        else:
            result = join_room(st.session_state.user["id"], code.upper(), name.strip())
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.room_code = code.upper()
                st.switch_page("pages/start.py")


c1, c2, _ = st.columns([1, 1, 3])
if c1.button("＋ Create new draft", type="primary", use_container_width=True):
    st.switch_page("pages/start.py")
if c2.button("Enter a code", use_container_width=True):
    join_draft_dialog()


# ── My Drafts ──────────────────────────────────────────────────────────────────

st.subheader("My drafts")

STATUS_ICON = {"lobby": "🔵", "drafting": "🟢", "finished": "⚫"}

try:
    data = list_rooms(st.session_state.user["id"])
    rooms = data.get("rooms", [])

    if not rooms:
        st.caption("No drafts yet. Create one or join with a code.")
    else:
        for room in rooms:
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.write(f"**{room.get('draft_name') or room['code']}**")
            c2.write(f"{STATUS_ICON.get(room['status'], '')} {room['status'].capitalize()}")
            c3.write(f"{room['rounds']} rounds")
            c4.write(room.get("mode", "—"))
            if c5.button("Open", key=f"open_{room['id']}", use_container_width=True):
                st.session_state.room_code = room["code"]
                st.switch_page("pages/start.py")

except Exception as e:
    st.warning(f"Could not load drafts — make sure the backend is running. [{e}]")
