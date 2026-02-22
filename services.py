from bson import ObjectId
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