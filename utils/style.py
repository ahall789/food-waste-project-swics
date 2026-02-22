import streamlit as st

def load_css(file_name="styles/styles.css"):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)