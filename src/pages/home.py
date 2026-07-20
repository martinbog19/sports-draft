import streamlit as st
import pandas as pd

from src.client import list_rooms


st.set_page_config(page_title="The field", layout="wide", page_icon="🏈")

st.title("Home")


resp = list_rooms()
rooms = pd.DataFrame(resp["data"]).sort_values(by="created_at", ascending=False).reset_index(drop=True)

st.dataframe(rooms)


for room in rooms:
    c1, c2, c3, c4, _ = st.columns([1, 1, 1, 1, 1])
    c1.write(room["name"])
    c2.write(room["snake"])
    c3.write(room["rounds"])