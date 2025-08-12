import streamlit as st
from lib.sql_utils import MYSQL_DDL

st.title("🧬 Schemas & Tables")

st.markdown("Below are MySQL DDLs for a small data warehouse used in this project.")
for name, ddl in MYSQL_DDL.items():
    st.markdown(f"**{name}**")
    st.code(ddl, language="sql")
