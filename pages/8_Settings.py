import streamlit as st
import pandas as pd

st.title("⚙️ Settings — Source, Uploads & Cache")

st.markdown("Choose data source (sidebar), or upload real datasets to override samples.")

acs_file = st.file_uploader("Upload ACS income CSV", type=["csv"])
redfin_file = st.file_uploader("Upload Redfin housing CSV", type=["csv"])
cpi_file = st.file_uploader("Upload BLS CPI CSV", type=["csv"])

session_overrides = {}
if acs_file: session_overrides["acs"] = pd.read_csv(acs_file)
if redfin_file: session_overrides["redfin"] = pd.read_csv(redfin_file)
if cpi_file: session_overrides["cpi"] = pd.read_csv(cpi_file)

if session_overrides:
    st.session_state["overrides"] = session_overrides
    st.success("Uploads received. Navigate to other pages to use them.")

if st.button("Clear Streamlit cache"):
    st.cache_data.clear()
    st.success("Cache cleared.")
