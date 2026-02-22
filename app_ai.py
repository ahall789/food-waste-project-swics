import os
import pymongo #???
import google.generativeai as genai

# connect to db
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "wasteless"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

userCol = db.users
ingredientCol = db.ingredient_logs
mealCol = db.meal_history
recipeHistCol = db.recipes_cache


# set the API key
API_KEY = "AIzaSyBTnjj3Ss8hShXkJNYc_O4rvi-llGntuWI"
if not API_KEY:
    raise ValueError("Gemini API key not set.")

# config key
genai.configure(api_key = API_KEY)

# model version
model = genai.GenerativeModel("gemini-flash-latest")

# input to set prompt
def promptAi(model, username):
    # get user profile - saved as user
    user = userCol.find_one({"username": username})
    # user id saved as user_id - get users ingredients
    fridge = ingredientCol.find({"user_id": user["_id"]})
    diet = userCol.find("dietary_restrictions", [])

    ingredients = []
    expiring = []

    for i in fridge:
        for j in i["ingredients"]:
            ingredients.append(j["name"])
            if j.get("is_expiring", True): # must add
                expiring.append(j["name"])

    # prompt
    ingredients_str = ", ".join(ingredients) if ingredients else "none"
    expiring_str = ", ".join(expiring) if expiring else "none"
    dietary_str = ", ".join(diet) if diet else "none"
    mode_note = f"CRITICAL: Every meal MUST feature at least one of these expiring ingredients: {expiring_str}." \
        if expiring else ""

    prompt = f """

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
    print (response.text)

    # save to db cache
    #recipeHistCol.update_one(---)


## generate content
#try:
#    prompt = "Output a 2 sentence story."
#    response = model.generate_content(prompt)
#    print ("Response:\n", response.text)
#except Exception as e:
#    print ("Error: ", e)
