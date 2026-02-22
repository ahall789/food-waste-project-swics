import re
import streamlit as st
from services import get_user_by_username, update_user_food_preferences
import os, streamlit as st
st.sidebar.write("MONGO_URI:", os.getenv("MONGO_URI"))
st.sidebar.write("DB_NAME:", os.getenv("DB_NAME"))
# ---------------- Login placeholder ----------------
def get_current_username() -> str:
    """
    Placeholder until real auth is wired in.
    Replace this with your actual login/session value.
    """
    return "amy_hall"

# ---------------- Options ----------------
DIETARY_OPTIONS = [
    "vegetarian", "vegan", "pescatarian",
    "gluten-free", "dairy-free", "nut-free",
    "halal", "kosher"
]

CUISINE_OPTIONS = [
    "Italian", "Indian", "Japanese", "Thai", "Mexican",
    "Mediterranean", "Chinese", "Korean", "French", "British"
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

    username = get_current_username()
    user = get_user_by_username(username)

    if not user:
        st.error("User profile not found.")
        return

    # Initialise tags once per session from DB
    init_tags_from_db("disliked_tags", user.get("disliked_ingredients", []))

    # Main form for dietary + cuisines (and Save)
    with st.form("food_prefs_form", clear_on_submit=False):
        dietary = st.multiselect(
            "Dietary restrictions",
            options=DIETARY_OPTIONS,
            default=user.get("dietary_restrictions", [])
        )

        cuisines = st.multiselect(
            "Favourite cuisines",
            options=CUISINE_OPTIONS,
            default=user.get("favorite_cuisines", [])
        )

        st.markdown("### Disliked ingredients (tags)")

        quick_pick = st.multiselect(
            "Quick add (common ingredients)",
            options=COMMON_INGREDIENTS,
            default=[],
            help="Select items to add them as tags."
        )

        # Add custom ingredient input (still inside the form)
        new_ing = st.text_input(
            "Add a custom ingredient",
            placeholder="e.g. aubergine",
            key="new_ing_input"
        )

        # Render current tags (chips)
        tags = st.session_state.get("disliked_tags", [])
        if tags:
            st.caption("Click a chip to remove it (it updates immediately).")
            cols = st.columns(4)
            for i, tag in enumerate(tags):
                col = cols[i % 4]
                if col.form_submit_button(f"✕ {tag}", use_container_width=True):
                    # Removing inside a form: update state and rerun after submit handling below
                    remove_tag("disliked_tags", tag)
                    st.session_state["_remove_rerun"] = True

        save = st.form_submit_button("Save changes")

    # Handle tag additions/removals outside the form submit logic
    # (Streamlit forms only run on submit, so we apply changes after.)
    if st.session_state.get("_remove_rerun"):
        st.session_state.pop("_remove_rerun", None)
        st.rerun()

    if quick_pick:
        for t in quick_pick:
            add_tag("disliked_tags", t)
        st.rerun()

    # Save changes
    if save:
        # Add anything typed but not explicitly “added”
        add_tag("disliked_tags", st.session_state.get("new_ing_input", ""))

        # Normalise + dedupe dietary/cuisines too
        dietary_clean = sorted(set([d.strip() for d in dietary if d.strip()]))
        cuisines_clean = sorted(set([c.strip() for c in cuisines if c.strip()]))

        disliked_clean = st.session_state.get("disliked_tags", [])

        ok = update_user_food_preferences(
            username=username,
            dietary_restrictions=dietary_clean,
            favorite_cuisines=cuisines_clean,
            disliked_ingredients=disliked_clean,
        )

        if not ok:
            st.error("Save failed (user not found).")
        else:
            st.success("Saved ✅")
            st.session_state.new_ing_input = ""
            st.rerun()

render_profile_page()