import re
import json
from pymongo import MongoClient
import google.generativeai as genai
import streamlit as st
from pymongo.errors import ServerSelectionTimeoutError
from utils.style import load_css

load_css()

MONGO_URI = "mongodb+srv://sakshikokane_db_user:xv2RDFTWbfZOAJQI@wastesless.mdemthv.mongodb.net/?appName=Wastesless"
DB_NAME = "wasteless"

API_KEY = ""

user = st.session_state.get("user")
if not user or not user.get("username"):
    st.warning("Please log in first.")
    st.switch_page("pages/login.py")
    st.stop()

username = user["username"]

@st.cache_resource
def get_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")  # fail fast if cannot connect
    return client[DB_NAME]

try:
    db = get_db()
except ServerSelectionTimeoutError as e:
    st.error(f"Database connection error:\n\n{e}")
    st.stop()

userCol = db.users
ingredientCol = db.ingredient_logs
mealCol = db.meal_history
recipeHistCol = db.recipes_cache

if not API_KEY:
    st.error("Gemini API key not set.")
    st.stop()

genai.configure(api_key=API_KEY)


# Pick a model that actually exists for this API key/project
def pick_model_name() -> str:
    preferred = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
        "gemini-1.0-pro",
    ]

    available = []
    for m in genai.list_models():
        # m.name looks like "models/gemini-pro"
        # Only keep models that support generateContent
        if "generateContent" in getattr(m, "supported_generation_methods", []):
            available.append(m.name.replace("models/", ""))

    # choose preferred if present
    for name in preferred:
        if name in available:
            return name

    # otherwise fall back to first available
    if available:
        return available[0]

    raise RuntimeError("No Gemini models available for generateContent with this API key.")

MODEL_NAME = pick_model_name()
st.info(f"Using Gemini model: {MODEL_NAME}")  # optional, for debugging
model = genai.GenerativeModel(MODEL_NAME)

# -------------------------------
# Helpers
# -------------------------------
def parse_ai_json(text: str):
    try:
        clean_text = re.sub(r"```(?:json)?\s*|\s*```", "", text, flags=re.IGNORECASE)
        return json.loads(clean_text.strip())
    except Exception as e:
        st.error(f"JSON Parsing Error: {e}")
        st.code(text)
        return None

# -------------------------------
# AI functions
# -------------------------------
def promptAi(model, username: str):
    user_doc = userCol.find_one({"username": username})
    if not user_doc:
        st.warning("Error: User not found")
        return None, [], []

    # Get latest ingredient log for this user
    latest_log = ingredientCol.find_one(
        {"user_id": user_doc["_id"]},
        sort=[("created_at", -1)]
    )

    diet = user_doc.get("dietary_restrictions", [])

    ingredients = []
    expiring = []

    if latest_log:
        for item in latest_log.get("ingredients", []):
            name = item.get("name")
            if not name:
                continue
            ingredients.append(name)
            if item.get("is_expiring", False):
                expiring.append(name)

    ingredients_str = ", ".join(ingredients) if ingredients else "none"
    expiring_str = ", ".join(expiring) if expiring else "none"
    dietary_str = ", ".join(diet) if diet else "none"

    prompt = f"""
You are a helpful meal planning assistant focused on reducing food waste.

Available ingredients: {ingredients_str}
Expiring soon: {expiring_str}
Dietary restrictions: {dietary_str}

Rules:
- Prefer using ONLY the available ingredients. If absolutely necessary, you may add at most 2 common pantry staples (salt, pepper, oil).
- Prioritize expiring ingredients in every meal.
- Respect ALL dietary restrictions — this is critical for health and safety.
- Generate exactly 3 different meal suggestions.

Return ONLY valid JSON — no explanation, no markdown, no extra text:
[
  {{
    "name": "Meal Name Here",
    "ingredients": ["ingredient1", "ingredient2"],
    "nutrition": {{"calories": 0, "protein": 0, "carbs": 0, "fat": 0}}
  }}
]
"""

    response = model.generate_content(prompt)
    meals = parse_ai_json(response.text)
    return meals, ingredients, expiring


def recipeAi(model, meal_name: str, ingredients: list, expiring: list = None):
    expiring = expiring or []
    expiring_str = ", ".join(expiring) if expiring else "none"

    prompt = f"""
Write a beginner-friendly step-by-step recipe for: {meal_name}
Available ingredients: {", ".join(ingredients)}
Key expiring ingredients to feature prominently: {expiring_str}

Rules:
- Write exactly 4-6 clear steps.
- Each step starts with a verb (Chop, Heat, Mix, etc.).
- Use simple language a first-time cook can follow.
- If there are expiring ingredients, use them early in the recipe.

Return ONLY valid JSON — no markdown, no extra text:
{{
  "steps": [
    "Step description here.",
    "Next step here."
  ]
}}
"""
    response = model.generate_content(prompt)
    return parse_ai_json(response.text)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("AI Meal Planner")
st.caption(f"Logged in as **{username}**")

if st.button("Generate meal ideas", type="primary"):
    meals, all_ings, expiring = promptAi(model, username)
    if meals:
        st.session_state["ai_meals"] = meals
        st.session_state["ai_expiring"] = expiring
    else:
        st.warning("No meals returned. Try again.")

meals = st.session_state.get("ai_meals")
expiring = st.session_state.get("ai_expiring", [])

if meals:
    st.subheader("Meal suggestions")
    for idx, meal in enumerate(meals, start=1):
        meal_name = meal.get("name", f"Meal {idx}")
        with st.expander(f"{idx}. {meal_name}"):
            st.write("Ingredients:", meal.get("ingredients", []))
            st.write("Nutrition:", meal.get("nutrition", {}))

            if st.button(f"Generate recipe for {meal_name}", key=f"gen_recipe_{idx}"):
                recipe = recipeAi(model, meal_name, meal.get("ingredients", []), expiring=expiring)
                if recipe and "steps" in recipe:
                    st.write("Recipe steps:")
                    for step_no, step in enumerate(recipe["steps"], start=1):
                        st.write(f"{step_no}. {step}")
                else:
                    st.warning("Recipe generation failed or returned invalid JSON.")