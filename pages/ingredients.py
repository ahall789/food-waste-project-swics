from datetime import datetime
import streamlit as st
import json

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["wasteless"]

st.set_page_config(page_title='Add Ingredients', page_icon='🌱')

if 'role' not in st.session_state:
    st.session_state.role = "gorgia_betts"

st.title('What is in your kitchen?')
st.write(f"You are logged in as {st.session_state.role}.")
st.subheader('Your Ingredients')

if 'ingredient_rows' not in st.session_state:
    st.session_state.ingredient_rows = [{'name': '', 'expiring': False}]

st.subheader('Your Ingredients')

for i, row in enumerate(st.session_state.ingredient_rows):
    col1, col2, col3 = st.columns([4, 2, 1])

    with col1:
        st.session_state.ingredient_rows[i]['name'] = st.text_input(
            f'Ingredient {i + 1}',
            value=row['name'],
            key=f'ing_{i}',
            placeholder='e.g. eggs'
        )
    with col2:
        st.session_state.ingredient_rows[i]['expiring'] = st.checkbox(
            'Expiring soon',
            value=row['expiring'],
            key=f'exp_{i}'
        )
    with col3:
        if i > 0:
            if st.button('✕', key=f'del_{i}'):
                st.session_state.ingredient_rows.pop(i)
                st.rerun()

col_left, col_right = st.columns(2)

with col_left:
    if st.button('+ Add Another Ingredient'):
        st.session_state.ingredient_rows.append({'name': '', 'expiring': False})
        st.rerun()

with col_right:
    if st.button('✅ Save to Pantry', type="primary"):
        user = db.users.find_one({"username": st.session_state.role})

        if user:
            formatted_ingredients = []
            for row in st.session_state.ingredient_rows:
                if row['name'].strip():
                    formatted_ingredients.append({
                        "name": row['name'].strip().lower(),
                        "is_expiring": row['expiring'],
                        "quantity": "not specified"
                    })

            if formatted_ingredients:
                log_entry = {
                    "user_id": user["_id"],
                    "session_id": "session_" + datetime.now().strftime("%Y%m%d%H%M"),
                    "created_at": datetime.utcnow(),
                    "ingredients": formatted_ingredients
                }

                db.ingredient_logs.insert_one(log_entry)
                st.success("Ingredients saved to your log!")

                st.session_state.ingredient_rows = [{'name': '', 'expiring': False}]
                st.rerun()
            else:
                st.warning("Please add at least one ingredient.")
        else:
            st.error("User not found in database.")