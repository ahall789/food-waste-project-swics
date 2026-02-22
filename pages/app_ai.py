import os
import re
import json
import pymongo #???
from pymongo import MongoClient #???
import google.generativeai as genai
import streamlit as st

st.set_page_config(page_title="Wasteless - Ai", layout="centered")

def get_db():
    try:
        # Use your Atlas connection string here
        client = MongoClient("mongodb+srv://sakshikokane_db_user:xv2RDFTWbfZOAJQI@wastesless.mdemthv.mongodb.net/?appName=Wastesless", serverSelectionTimeoutMS=5000)
        client.server_info() 
        return client["wasteless"]
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

db = get_db()
userCol = db.users
ingredientCol = db.ingredient_logs
mealCol = db.meal_history # unused
recipeHistCol = db.recipes_cache # unused


# set the API key
API_KEY = "AIzaSyBTnjj3Ss8hShXkJNYc_O4rvi-llGntuWI"
if not API_KEY:
    raise ValueError("Gemini API key not set.")

# config key
genai.configure(api_key = API_KEY)

# model version
model = genai.GenerativeModel("gemini-flash-latest")

def parse_ai_json(text):
    try:
        clean_text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL)
        return json.loads(clean_text.strip())
    except Exception as e:
        st.error(f"JSON Parsing Error: {e}")
        return None

# input to set prompt
def promptAi(model, username):
    # get user profile - saved as user
    user = userCol.find_one({"username": username})

    if not user:
        st.warning(f"Error: User not found")
        return None

    # user id saved as user_id - get users ingredients
    fridge = ingredientCol.find({"user_id": user["_id"]})
    diet = user.get("dietary_restrictions", [])

    ingredients = []
    expiring = []

    for i in fridge:
        for j in i.get["ingredients", []]:
            name = item.get("name")
            ingredients.append(name)
            if j.get("is_expiring", False):
                expiring.append(name)

    # prompt
    ingredients_str = ", ".join(ingredients) if ingredients else "none"
    expiring_str = ", ".join(expiring) if expiring else "none"
    dietary_str = ", ".join(diet) if diet else "none"

    prompt = f"""

You are a helpful meal planning assistant focused on reducing food waste.

Available ingredients: {ingredients_str}
Expiring soon: {expiring_str}
Dietary restrictions: {dietary_str}
{mode_note}

Rules:
- Use ONLY the available ingredients above, no extras.
- Prioritize expiring ingredients in every meal.
- Respect ALL dietary restrictions — this is critical for health and safety.
- Do not repeat recently made meals.

Generate exactly 3 different meal suggestions.
Return ONLY valid JSON — no explanation, no markdown, no extra text:
[
    {{
        "name": "Meal Name Here",
        "ingredients": ["ingredient1", "ingredient2"],
        "nutrition": {{"calories": x, "protein": y, "carbs": z, "fat": p}}
    }}
]
"""
    response = model.generate_content(prompt)
    return parse_ai_json(response.text)


def recipeAi(model, meal_name, ingredients, expiring=[]):
    expiring_str = ", ".join(expiring) if expiring else "none"

    # save in recipe_json
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
    return _parse_ai_json(response.text)

# get current user
current_user_data = st.session_state.get("user")

if not current_user_data:
    st.warning("User not found")
else:
    username = current_user_data.get("username")
    
    if st.button("Generate Meals"):
        mealsGen = promptAi(model, username)
        
        if mealsGen:
            st.subheader("Suggested Meals")
            st.write(mealsGen) 
            
            first_meal = mealsGen[0]
            st.info(f"Generating recipe for: {first_meal['name']}")
            
            full_recipe = recipeAi(model, first_meal['name'], first_meal['ingredients'])
            
            if full_recipe:
                st.subheader("Recipe Instructions")
                
                if isinstance(full_recipe, dict) and "steps" in full_recipe:
                    for step in full_recipe["steps"]:
                        st.write(f"- {step}")
                else:
                    st.write(full_recipe)




# ─── Example usage ─────
#if __name__ == "__main__":
 #   aiMeals = promptAi(model, "amy_hall")
  #  print (aiMeals)
   # st.text (aiMeals)

   # if aiMeals:
    #    meal = aiMeals[0]
     #   print(f"Generating recipe for: {meal["name"]}")
      #  full_recipe = recipeAi(model, meal["name"], meal["ingredients"])
        
       # print(full_recipe)
        #st.text(full_recipe)






## generate content
#try:
#    prompt = "Output a 2 sentence story."
#    response = model.generate_content(prompt)
#    print ("Response:\n", response.text)
#except Exception as e:
#    print ("Error: ", e)
