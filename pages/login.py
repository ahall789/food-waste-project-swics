"""
Dependencies:
    pip install streamlit pymongo bcrypt
"""

import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import bcrypt
import re

# ─── Page Config ──────────────────────────────────────────────────────────────
#st.set_page_config(
   # page_title="WasteLess — Login",
    #page_icon="🥦",
    #layout="centered",
    #initial_sidebar_state="collapsed",
#)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
from utils.style import load_css

load_css()
# ─── MongoDB Connection ────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    """Return a cached MongoDB database connection."""
    try:
        client = MongoClient("mongodb+srv://sakshikokane_db_user:xv2RDFTWbfZOAJQI@wastesless.mdemthv.mongodb.net/?appName=Wastesless", serverSelectionTimeoutMS=5000)
        client.server_info()          # triggers connection check
        return client["wasteless"]
    except Exception:
        return None


db = get_db()


# ─── Auth Helpers ─────────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def login_user(username: str, password: str):
    """Return user doc on success, error string on failure."""
    if db is None:
        return "Cannot connect to database. Is MongoDB running?"
    user = db.users.find_one({"username": username.strip().lower()})
    if not user:
        return "No account found with that username."
    if "password_hash" not in user:
        return "Account has no password set. Please re-register."
    if not verify_password(password, user["password_hash"]):
        return "Incorrect password."
    # update last_active
    db.users.update_one({"_id": user["_id"]}, {"$set": {"stats.last_active": datetime.utcnow()}})
    return user


def register_user(username: str, email: str, password: str,
                  dietary: list, cuisines: list, disliked: str):
    """Return user doc on success, error string on failure."""
    if db is None:
        return "⚠️ Cannot connect to database. Is MongoDB running?"

    username = username.strip().lower()

    # Validation
    if len(username) < 3:
        return "Username must be at least 3 characters."
    if not re.match(r"^[a-z0-9_]+$", username):
        return "Username may only contain letters, numbers, and underscores."
    if email and not is_valid_email(email):
        return "Please enter a valid email address."
    if len(password) < 6:
        return "Password must be at least 6 characters."

    if db.users.find_one({"username": username}):
        return f"Username '{username}' is already taken."

    disliked_list = [d.strip() for d in disliked.split(",") if d.strip()] if disliked else []

    new_user = {
        "username": username,
        "email": email.strip() if email else None,
        "password_hash": hash_password(password),
        "created_at": datetime.utcnow(),
        "dietary_restrictions": dietary,
        "favorite_cuisines": cuisines,
        "disliked_ingredients": disliked_list,
        "stats": {
            "total_meals_planned": 0,
            "total_waste_prevented_g": 0,
            "avg_rating": 0.0,
            "streak_days": 0,
            "last_active": datetime.utcnow(),
        },
        "preferences_learned": {
            "high_rated_cuisines": [],
            "frequently_used_ingredients": [],
            "preferred_cook_time": "medium",
        },
    }

    result = db.users.insert_one(new_user)
    new_user["_id"] = result.inserted_id
    return new_user


# ─── Session State Init ────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None

# ─── Already Logged In ─────────────────────────────────────────────────────────
if st.session_state.user:
    user = st.session_state.user
    dietary_tags = " ".join(
        [f'<span class="welcome-tag">🥗 {d}</span>' for d in (user.get("dietary_restrictions") or [])]
    )
    cuisines_tags = " ".join(
        [f'<span class="welcome-tag">🍽️ {c}</span>' for c in (user.get("favorite_cuisines") or [])]
    )

    st.markdown(f"""
    <div class="hero">
        <div class="hero-icon">🥦</div>
        <h1>WasteLess</h1>
    </div>
    <div class="welcome-card">
        <h2>Welcome back, {user['username']}! 👋</h2>
        <p>Ready to cook something amazing?</p>
        <div class="welcome-meta">
            {dietary_tags}
            {cuisines_tags}
        </div>
    </div>
    """, unsafe_allow_html=True)

    stats = user.get("stats", {})
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🍳 Meals Planned", stats.get("total_meals_planned", 0))
    with col2:
        waste_kg = round(stats.get("total_waste_prevented_g", 0) / 1000, 1)
        st.metric("♻️ Waste Saved", f"{waste_kg} kg")
    with col3:
        st.metric("🔥 Streak", f"{stats.get('streak_days', 0)} days")

    st.divider()
    col_go, col_out = st.columns(2)
    with col_go:
        if st.button("🥗 Start Meal Planning →", use_container_width=True):
            st.switch_page("app.py")   # update to your main app page
    with col_out:
        if st.button("🚪 Log out", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    st.markdown('<p class="footer-note">WasteLess · Fighting food waste, one meal at a time 🌍</p>',
                unsafe_allow_html=True)
    st.stop()


# ─── Landing Hero ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-icon">🥦</div>
    <h1>WasteLess</h1>
    <p>
    </p>
    <p>AI-powered meals from what you already have</p>
    <div class="stat-row">
        <div class="stat-pill">🌍 Reduce food waste</div>
        <div class="stat-pill">🤖 AI meal ideas</div>
        <div class="stat-pill">🥗 Dietary-friendly</div>
    </div>
</div>
""", unsafe_allow_html=True)

if db is None:
    st.warning("⚠️ MongoDB is not reachable. Start MongoDB locally or update the connection URI in `login.py`.", icon="⚠️")

# authetnication
tab_login, tab_register = st.tabs(["🔑  Log In", "✨  Create Account"])

# login
with tab_login:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("login_form"):
        username_in = st.text_input("Username", placeholder="your_username")
        password_in = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Log in", use_container_width=True)

    if submitted:
        if not username_in or not password_in:
            st.error("Please fill in both fields.")
        else:
            result = login_user(username_in, password_in)
            if isinstance(result, str):
                st.error(result)
            else:
                st.session_state.user = result
                st.success(f"Welcome back, **{result['username']}**! 🎉")
                st.rerun()

    st.markdown('<p class="divider">Demo accounts: amy_hall / georgia_betts / alice_lean<br>(set passwords via mongo_setup.py)</p>',
                unsafe_allow_html=True)

# register
with tab_register:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form("register_form"):
        col_u, col_e = st.columns(2)
        with col_u:
            reg_username = st.text_input("Username *", placeholder="gorga")
        with col_e:
            reg_email = st.text_input("Email", placeholder="georgia@example.com")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            reg_pass = st.text_input("Password *", type="password", placeholder="min. 6 chars")
        with col_p2:
            reg_pass2 = st.text_input("Confirm password *", type="password", placeholder="repeat")

        reg_dietary = st.multiselect(
            "Dietary restrictions",
            ["vegetarian", "vegan", "gluten-free", "halal", "kosher",
             "dairy-free", "nut-free", "low-carb", "keto", "pescatarian"],
            placeholder="Select any that apply",
        )

        reg_cuisines = st.multiselect(
            "Favourite cuisines",
            ["Italian", "Asian", "Mexican", "Indian", "Mediterranean",
             "American", "Middle Eastern", "Thai", "Japanese", "French"],
            placeholder="Pick your favourites",
        )

        reg_disliked = st.text_input(
            "Ingredients you dislike (comma-separated)",
            placeholder="e.g. mushrooms, olives, anchovies",
        )

        reg_submitted = st.form_submit_button("Create my account 🌱", use_container_width=True)

    if reg_submitted:
        if not reg_username or not reg_pass or not reg_pass2:
            st.error("Username and password fields are required.")
        elif reg_pass != reg_pass2:
            st.error("Passwords don't match.")
        else:
            result = register_user(reg_username, reg_email, reg_pass,
                                   reg_dietary, reg_cuisines, reg_disliked)
            if isinstance(result, str):
                st.error(result)
            else:
                st.session_state.user = result
                st.success(f"Account created! Welcome to WasteLess, **{result['username']}** 🎉")
                st.balloons()
                st.rerun()

# footer
st.markdown(
    '<p class="footer-note">WasteLess · Fighting food waste, one meal at a time 🌍</p>',
    unsafe_allow_html=True,
)