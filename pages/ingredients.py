from datetime import datetime, date
import streamlit as st
import pandas as pd
import numpy as np

import json

@st.cache_data
def load_data():
    df = pd.DataFrame(ingredients)
    return df

df = load_data()
config = {
    "_index": st.column_config.DateColumn("Month", format="MMM YYYY"),
    "Total": st.column_config.NumberColumn("Total ($)"),
}

st.dataframe(df, column_config=config)