import streamlit as st

st.set_page_config(page_title="WasteLess", page_icon="🥦", layout="centered")

# ---------- Define pages ----------
login_page = st.Page(
    "pages/login.py",
    title="Login",
    icon=":material/login:",
    default=True,   # ⭐ this makes it the starting page
)

ingredients_page = st.Page(
    "pages/ingredients.py",
    title="Ingredients",
    icon=":material/restaurant:",
)

profile_page = st.Page(
    "pages/profile.py",
    title="Profile",
    icon=":material/person:",
)

# ---------- Navigation ----------
nav = st.navigation([
    login_page,
    ingredients_page,
    profile_page,
])

nav.run()