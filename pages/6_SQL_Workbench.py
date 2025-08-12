import streamlit as st
import sqlite3
import pandas as pd
import os
from lib.data_loader import load_data
from lib.sql_utils import load_sample_into_sqlite

st.title("🧪 SQL Workbench — Try Queries on the Sample Warehouse")

db_path = os.path.join("data", "sample_dw.sqlite")

# Load data and build SQLite (idempotent)
dfs = load_data("csv")
load_sample_into_sqlite(db_path, dfs["acs"], dfs["redfin"], dfs["cpi"], dfs["counties"])

st.info("Running against an embedded SQLite database created from the sample CSVs.")

q = st.text_area("SQL", "SELECT name FROM sqlite_master WHERE type='table';", height=150)
if st.button("Run"):
    try:
        with sqlite3.connect(db_path) as conn:
            out = pd.read_sql_query(q, conn)
        st.dataframe(out)
    except Exception as e:
        st.error(str(e))
