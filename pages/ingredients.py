from datetime import datetime
import streamlit as st
import services

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    user = st.session_state.user
else:
    st.switch_page("pages/login.py")

st.title('What is in your kitchen?')
st.write(f"You are logged in as {user['username']}"".")
st.subheader('Your Ingredients')

if 'ingredient_rows' not in st.session_state:
    st.session_state.ingredient_rows = [{
        'name': '',
        'is_expiring': False,
        'days_until_expiry': 365,
        'quantity': ''
    }]

for i, row in enumerate(st.session_state.ingredient_rows):
    col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
    with col1:
        st.session_state.ingredient_rows[i]['name'] = st.text_input(
            f'Name',
            value=row['name'],
            key=f'name_{i}',
            placeholder='e.g. eggs'
        )
    with col2:
        x = st.session_state.ingredient_rows[i]['is_expiring'] = st.checkbox(
            'Expiring soon',
            value=row['is_expiring'],
            key=f'exp_{i}'
        )
        if x:
            st.session_state.ingredient_rows[i]['days_until_expiry'] = st.number_input(
                f'Days until expiry',
                min_value = 0,
                max_value = 365,
                value=row['days_until_expiry'],
                key=f'days_until_expiry_{i}'
            )

    with col3:
        st.session_state.ingredient_rows[i]['quantity'] = st.text_input(
            f'Quantity',
            value=row['quantity'],
            key=f'q_{i}',
            placeholder='e.g. 1 cup, 500 grams, 3'
        )
    with col4:
        if i > 0:
            if st.button('✕', key=f'del_{i}'):
                st.session_state.ingredient_rows.pop(i)
                st.rerun()

col_left, col_right = st.columns(2)

with col_left:
    if st.button('+ Add Another Ingredient'):
        st.session_state.ingredient_rows = [{
            'name': '',
            'is_expiring': False,
            'days_until_expiry': None,
            'quantity': ''
        }]
        st.rerun()

with col_right:
    if st.button('Save to Pantry', type="primary"):
        user = db.users.find_one({"username": st.session_state.role})

        if user:
            formatted_ingredients = []
            for row in st.session_state.ingredient_rows:
                if row['name'].strip():
                    formatted_ingredients.append({
                        "name": row['name'].strip().lower(),
                        "is_expiring": row['expiring'],
                        "days_until_expiry": row['days_until_expiry'],
                        "quantity": row['quantity'].strip().lower()
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

                st.session_state.ingredient_rows = [{
                    'name': '',
                    'is_expiring': False,
                    'days_until_expiry': 365,
                    'quantity': ''
                }]
                st.rerun()
            else:
                st.warning("Please add at least one ingredient.")
        else:
            st.error("User not found in database.")