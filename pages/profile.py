import streamlit as st
from pymongo import MongoClient

st.title("Profile")

def get_collection():
    client = MongoClient('localhost', 27017)
    db = client['mydatabase']
    collection = db['users']
    return collection
