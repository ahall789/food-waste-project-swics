"""
WasteLess MongoDB Schema
============================================
Run this once to initialise the database.
Requirements: pip install pymongo
Usage: python mongo_setup.py
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime, timedelta
import random

# ─── Connection ───────────────────────────────────────────────────────────────
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "wasteless"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# ─── Schema Design ────────────────────────────────────────────────────────────

"""
COLLECTIONS:
  users            — user profile, dietary prefs, stats
  ingredient_logs  — ingredients added per session
  meal_history     — meals planned with ratings
  recipes_cache    — cached AI-generated recipes

DOCUMENT SCHEMAS:
───────────────────────────────────────────────────────
users:
{
  _id: ObjectId,
  username: str,
  email: str (optional),
  created_at: datetime,
  dietary_restrictions: [str],  
  favorite_cuisines: [str],
  disliked_ingredients: [str],
  stats: {
    total_meals_planned: int,
    total_waste_prevented_g: int,
    avg_rating: float,
    streak_days: int,
    last_active: datetime,
  },
  preferences_learned: {
    high_rated_cuisines: [str],
    frequently_used_ingredients: [str],
    preferred_cook_time: str,   # "quick" | "medium" | "long"
  }
}

ingredient_logs:
{
  _id: ObjectId,
  user_id: ObjectId,
  session_id: str,
  created_at: datetime,
  ingredients: [
    {
      name: str,
      is_expiring: bool,
      days_until_expiry: int (optional),
      quantity: str (optional),
    }
  ]
}

meal_history:
{
  _id: ObjectId,
  user_id: ObjectId,
  session_id: str,
  created_at: datetime,
  meal_name: str,
  cuisine: str,
  cook_time: str,
  difficulty: str,
  ingredients_used: [str],
  expiring_ingredients_used: [str],
  rating: int,              # 1-5
  user_notes: str,
  waste_prevented_g: int,   # estimated
  nutrition: {
    calories: int,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    fiber_g: float,
  },
  ai_prompt_hash: str,      # for deduplication
}

recipes_cache:
{
  _id: ObjectId,
  cache_key: str,           # hash of meal_name + ingredients + dietary
  meal_name: str,
  ingredients_input: [str],
  dietary_restrictions: [str],
  recipe_json: dict,        # full AI-generated recipe
  created_at: datetime,
  expires_at: datetime,     # TTL index (7 days)
  use_count: int,
}
"""

# ─── Create Collections & Indexes ─────────────────────────────────────────────
def setup_schema():
    print("Setting up WasteLess MongoDB schema...")

    # users
    db.create_collection("users") if "users" not in db.list_collection_names() else None
    db.users.create_index("username", unique=True)
    db.users.create_index("email", sparse=True)
    db.users.create_index("stats.last_active")

    # ingredient_logs
    db.create_collection("ingredient_logs") if "ingredient_logs" not in db.list_collection_names() else None
    db.ingredient_logs.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.ingredient_logs.create_index("session_id")

    # meal_history
    db.create_collection("meal_history") if "meal_history" not in db.list_collection_names() else None
    db.meal_history.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
    db.meal_history.create_index("rating")
    db.meal_history.create_index("meal_name")

    # recipes_cache with TTL
    db.create_collection("recipes_cache") if "recipes_cache" not in db.list_collection_names() else None
    db.recipes_cache.create_index("cache_key", unique=True)
    db.recipes_cache.create_index("expires_at", expireAfterSeconds=0)  # TTL index

    print("Schema and indexes created.")

# ─── Sample Data ──────────────────────────────────────────────────────────────
SAMPLE_USERS = [
    {
        "username": "amy_hall",
        "email": "amy@hall.com",
        "created_at": datetime.utcnow() - timedelta(days=45),
        "dietary_restrictions": ["vegetarian"],
        "favorite_cuisines": ["Italian", "Asian"],
        "disliked_ingredients": ["mushrooms"],
        "stats": {
            "total_meals_planned": 23,
            "total_waste_prevented_g": 4600,
            "avg_rating": 4.1,
            "streak_days": 7,
            "last_active": datetime.utcnow() - timedelta(hours=2),
        },
        "preferences_learned": {
            "high_rated_cuisines": ["Italian", "Mexican"],
            "frequently_used_ingredients": ["pasta", "eggs", "garlic", "onion"],
            "preferred_cook_time": "quick",
        }
    },
    {
        "username": "gorgia_betts",
        "email": "groga.betts.com",
        "created_at": datetime.utcnow() - timedelta(days=120),
        "dietary_restrictions": ["gluten-free"],
        "favorite_cuisines": ["American", "Mexican"],
        "disliked_ingredients": ["cilantro"],
        "stats": {
            "total_meals_planned": 67,
            "total_waste_prevented_g": 13400,
            "avg_rating": 4.4,
            "streak_days": 21,
            "last_active": datetime.utcnow() - timedelta(hours=18),
        },
        "preferences_learned": {
            "high_rated_cuisines": ["Mexican", "Asian"],
            "frequently_used_ingredients": ["chicken", "rice", "vegetables"],
            "preferred_cook_time": "medium",
        }
    },
    {
        "username": "alice_lean",
        "email": "alean@sheff.com",
        "created_at": datetime.utcnow() - timedelta(days=200),
        "dietary_restrictions": ["gluten-free"],
        "favorite_cuisines": ["Indian", "Mediterranean"],
        "disliked_ingredients": [],
        "stats": {
            "total_meals_planned": 156,
            "total_waste_prevented_g": 31200,
            "avg_rating": 4.7,
            "streak_days": 90,
            "last_active": datetime.utcnow() - timedelta(minutes=30),
        },
        "preferences_learned": {
            "high_rated_cuisines": ["Indian", "Thai", "Middle Eastern"],
            "frequently_used_ingredients": ["lentils", "chickpeas", "spinach", "tomatoes"],
            "preferred_cook_time": "medium",
        }
    }
]