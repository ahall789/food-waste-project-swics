import streamlit as st

st.set_page_config(page_title="WasteLess", page_icon="🥦", layout="centered")

login_page = st.Page("pages/login.py", title="Login", icon=":material/login:", default=True)
ingredients_page = st.Page("pages/ingredients.py", title="Ingredients", icon=":material/restaurant:")
profile_page = st.Page("pages/profile.py", title="Profile", icon=":material/person:")
app_ai = st.Page("app_ai_draft.py", title="App AI")

user = st.session_state.get("user")

if not user:
    nav = st.navigation([login_page])
else:
    nav = st.navigation([login_page, ingredients_page, profile_page, app_ai])

nav.run()