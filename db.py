import streamlit as st
from pymongo import MongoClient
import os

@st.cache_resource
def get_db():
    try:
        client = MongoClient(
            "mongodb+srv://sakshikokane_db_user:xv2RDFTWbfZOAJQI@wastesless.mdemthv.mongodb.net/?appName=Wastesless",
            serverSelectionTimeoutMS=5000)
        client.server_info()  # triggers connection check
        return client["wasteless"]
    except Exception:
        return None

def get_collection(name: str):
    return get_db()[name]

#def get_collection():
    client = MongoClient('localhost', 27017)
    db = client['mydatabase']
    collection = db['users']
    return collection