import uuid
from datetime import datetime
from typing import Any, Optional, Dict, List
from db import get_collection

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    users = get_collection("users")
    return users.find_one({"username": username})

def update_user_food_preferences(
    username: str,
    dietary_restrictions: List[str],
    favorite_cuisines: List[str],
    disliked_ingredients: List[str],
) -> bool:
    users = get_collection("users")

    update_doc = {
        "dietary_restrictions": dietary_restrictions,
        "favorite_cuisines": favorite_cuisines,
        "disliked_ingredients": disliked_ingredients,
        "stats.last_active": datetime.utcnow(),
    }

    result = users.update_one({"username": username}, {"$set": update_doc})
    return result.matched_count == 1

def get_user_ingredients(username: str) -> List[Dict[str, Any]]:
    logs = get_collection("ingredient_logs")

    user = get_user_by_username(username)
    if not user:
        return []

    ingredient_log = logs.find_one(
        {"user_id": user["_id"]},
        sort=[("created_at", -1)]
    )

    return ingredient_log.get("ingredients", []) if ingredient_log else []

def set_user_ingredients(username: str, ingredients: List[Dict[str, Any]]) -> bool:
    logs = get_collection("ingredient_logs")
    user = get_user_by_username(username)

    if not user:
        print(f"User {username} not found.")
        return False
    if not ingredients:
        print(f"Ingredients not found.")
        return False

    new_log = {
        "user_id": user["_id"],
        "session_id": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "ingredients": ingredients
    }

    result = logs.insert_one(new_log)
    if result.acknowledged and result.inserted_id:
        return True

    return False