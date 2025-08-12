import streamlit as st
from lib.data_loader import load_data, compute_price_to_income
from lib.viz import choropleth_ratio

st.title("🗺️ Maps — Price-to-Income Ratio by County")

data = load_data("auto")
acs, redfin, cpi, counties = data["acs"], data["redfin"], data["cpi"], data["counties"]
ratio_df = compute_price_to_income(acs, redfin)

year = st.slider("Year",
                 int(ratio_df["year"].min()),
                 int(ratio_df["year"].max()),
                 int(ratio_df["year"].max()),
                 step=1)

fig = choropleth_ratio(ratio_df, counties, year)
st.plotly_chart(fig, use_container_width=True)
st.caption("Map uses Plotly county GeoJSON; only 5-digit numeric FIPS are plotted.")
