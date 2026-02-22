from datetime import datetime
import streamlit as st
import services


if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    user = st.session_state.user
else:
    st.switch_page("pages/login.py")


st.set_page_config(page_title='Add Ingredients')

st.markdown(f"""
<div class="hero">
    <h1>Pantry</h1>
</div>
<div class="welcome-card">
    <h2>What is in your kitchen, {user['username']}? 👋</h2>
</div>
""", unsafe_allow_html=True)

st.subheader('Your Ingredients')

if 'ingredient_rows' not in st.session_state:
    db_ingredients = services.get_user_ingredients(user['username'])

    if db_ingredients:
        st.session_state.ingredient_rows = [
            {
                'name': ing.get('name', ''),
                'is_expiring': ing.get('is_expiring', False),
                'days_until_expiry': ing.get('days_until_expiry', None),
                'quantity': ing.get('quantity', '')
            }
            for ing in db_ingredients
        ]
    else:
        st.session_state.ingredient_rows = [{
            'name': '', 'is_expiring': False, 'days_until_expiry': None, 'quantity': ''
        }]


for i, row in enumerate(st.session_state.ingredient_rows):
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 1, 0.5])

        with col1:
            st.session_state.ingredient_rows[i]['name'] = st.text_input(
                "Name", value=row['name'], key=f"name_{i}"
            )

        with col2:
            st.session_state.ingredient_rows[i]['quantity'] = st.text_input(
                "Quantity", value=row['quantity'], key=f"qty_{i}"
            )

        with col3:
            is_exp = st.checkbox("Expiring?", value=row['is_expiring'], key=f"exp_{i}")
            st.session_state.ingredient_rows[i]['is_expiring'] = is_exp

            if is_exp:
                st.session_state.ingredient_rows[i]['days_until_expiry'] = st.number_input(
                    "Days", value=row['days_until_expiry'], min_value=0, key=f"days_{i}"
                )

        with col4:
            st.write("##")
            if st.button("✕", key=f"del_{i}"):
                st.session_state.ingredient_rows.pop(i)
                st.rerun()
    st.divider()

c1, c2 = st.columns(2)

with c1:
    if st.button("➕ Add Extra Ingredient"):
        # This adds a new empty dictionary to the list
        st.session_state.ingredient_rows.append({
            'name': '', 'is_expiring': False, 'days_until_expiry': 7, 'quantity': ''
        })
        st.rerun()

with c2:
    if st.button("💾 Save All to Database", type="primary"):
        # Filter out rows where the name is empty before saving
        to_save = [ing for ing in st.session_state.ingredient_rows if ing['name'].strip()]

        if to_save:
            with st.spinner("Saving to WasteLess DB..."):
                success = services.set_user_ingredients(user['username'], to_save)

                if success:
                    st.success("Pantry updated!")
                else:
                    st.error("Could not save to database.")
        else:
            st.warning("Please enter at least one ingredient name.")
