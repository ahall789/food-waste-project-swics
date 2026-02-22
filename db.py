import streamlit as st
from pymongo import MongoClient

@st.cache_resource
def get_db():
    """Return a cached MongoDB database connection."""
    try:
        client = MongoClient("mongodb+srv://sakshikokane_db_user:xv2RDFTWbfZOAJQI@wastesless.mdemthv.mongodb.net/?appName=Wastesless", serverSelectionTimeoutMS=5000)
        client.server_info()          # triggers connection check
        return client["wasteless"]
    except Exception:
        return "⚠️ Cannot connect to database. Is MongoDB running?"

def get_collection(name: str):
    return get_db()[name]