import re
from typing import Optional

import streamlit as st
from services import get_user_by_username, update_user_food_preferences


# ---------------- Auth ----------------
def get_current_username() -> Optional[str]:
    """Gets the logged-in user from session state."""
    user = st.session_state.get("user")
    if not user:
        return None
    return user.get("username")

# ---------------- Options ----------------
DIETARY_OPTIONS = [
    "vegetarian", "vegan", "pescatarian",
    "gluten-free", "dairy-free", "nut-free",
    "halal", "kosher"
]

CUISINE_OPTIONS = [
    "Italian", "Indian", "Japanese", "Thai", "Mexican",
    "Mediterranean", "Middle Eastern", "Chinese", "Korean",
    "French", "British", "American", "Asian"
]

COMMON_INGREDIENTS = [
    "mushrooms", "cilantro", "olives", "garlic", "onion", "tomato", "pepper",
    "egg", "milk", "cheese", "butter", "yoghurt", "nuts", "peanuts", "soy",
    "wheat", "gluten", "shellfish", "fish"
]

# ---------------- Tag helpers ----------------
def normalise_tag(tag: str, *, lowercase: bool = True) -> str:
    if not tag:
        return ""
    tag = tag.strip()
    tag = re.sub(r"\s+", " ", tag)
    return tag.lower() if lowercase else tag

def init_tags_from_db(state_key: str, existing: list[str]):
    if state_key not in st.session_state:
        cleaned = [normalise_tag(x) for x in (existing or []) if x]
        st.session_state[state_key] = sorted(set([x for x in cleaned if x]))

def add_tag(state_key: str, new_tag: str, *, lowercase: bool = True, max_len: int = 40):
    tag = normalise_tag(new_tag, lowercase=lowercase)
    if not tag:
        return
    if len(tag) > max_len:
        st.toast(f"Tag too long (max {max_len} chars).", icon="⚠️")
        return
    tags = st.session_state.get(state_key, [])
    if tag not in tags:
        tags.append(tag)
        st.session_state[state_key] = sorted(tags)

def remove_tag(state_key: str, tag: str):
    tags = st.session_state.get(state_key, [])
    if tag in tags:
        tags.remove(tag)
        st.session_state[state_key] = tags

# ---------------- Page UI ----------------
def render_profile_page():
    st.title("Profile")
    st.caption("Update your dietary requirements and food preferences.")

    # ── Guard: must be logged in ──────────────────────────────────────────
    username = get_current_username()
    if not username:
        st.warning("Please log in to view your profile.")
        if st.button("Go to Login"):
            st.switch_page("login.py")
        return

    user = get_user_by_username(username)
    if not user:
        st.error("User profile not found in database.")
        return

    # Initialise disliked tags once per session from DB
    init_tags_from_db("disliked_tags", user.get("disliked_ingredients", []))

    # ── Disliked ingredient tags (outside form so removal works instantly) ─
    st.markdown("### Disliked ingredients")

    quick_pick = st.multiselect(
        "Quick add (common ingredients)",
        options=COMMON_INGREDIENTS,
        default=[],
        help="Select items to add them as tags."
    )
    if quick_pick:
        for t in quick_pick:
            add_tag("disliked_tags", t)
        st.rerun()

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        new_ing = st.text_input(
            "Add a custom ingredient",
            placeholder="e.g. aubergine",
            key="new_ing_input",
            label_visibility="collapsed"
        )
    with col_btn:
        if st.button("Add", use_container_width=True):
            if new_ing.strip():
                add_tag("disliked_tags", new_ing)
                st.session_state["new_ing_input"] = ""
                st.rerun()
            else:
                st.toast("Please type an ingredient first.", icon="⚠️")

    # Render tag chips — each button removes that tag instantly
    tags = st.session_state.get("disliked_tags", [])
    if tags:
        st.caption("Click a tag to remove it.")
        cols = st.columns(4)
        for i, tag in enumerate(tags):
            if cols[i % 4].button(f"✕ {tag}", key=f"remove_{tag}", use_container_width=True):
                remove_tag("disliked_tags", tag)
                st.rerun()
    else:
        st.caption("No disliked ingredients added yet.")

    st.divider()

    # ── Main preferences form ─────────────────────────────────────────────
    # Filter defaults to only values in options — prevents crashes from old DB data
    saved_dietary  = [d for d in user.get("dietary_restrictions", []) if d in DIETARY_OPTIONS]
    saved_cuisines = [c for c in user.get("favorite_cuisines", [])    if c in CUISINE_OPTIONS]

    with st.form("food_prefs_form", clear_on_submit=False):
        dietary = st.multiselect(
            "Dietary restrictions",
            options=DIETARY_OPTIONS,
            default=saved_dietary,
        )

        cuisines = st.multiselect(
            "Favourite cuisines",
            options=CUISINE_OPTIONS,
            default=saved_cuisines,
        )

        save = st.form_submit_button("💾 Save changes", use_container_width=True)

    if save:
        dietary_clean  = sorted(set([d.strip() for d in dietary if d.strip()]))
        cuisines_clean = sorted(set([c.strip() for c in cuisines if c.strip()]))
        disliked_clean = st.session_state.get("disliked_tags", [])

        ok = update_user_food_preferences(
            username=username,
            dietary_restrictions=dietary_clean,
            favorite_cuisines=cuisines_clean,
            disliked_ingredients=disliked_clean,
        )

        if not ok:
            st.error("Save failed — user not found.")
        else:
            # Keep session state in sync
            st.session_state["user"]["dietary_restrictions"] = dietary_clean
            st.session_state["user"]["favorite_cuisines"]    = cuisines_clean
            st.session_state["user"]["disliked_ingredients"] = disliked_clean
            st.success("Profile saved ✅")
            st.rerun()

render_profile_page()