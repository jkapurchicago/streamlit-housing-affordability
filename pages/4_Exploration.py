import streamlit as st
import pandas as pd
from lib.data_loader import load_data, compute_price_to_income, cpi_pivot
from lib.viz import line_prices, line_ratio

st.title("🔎 Exploration — County Drilldown")

data = load_data("auto")
acs, redfin, cpi, counties = data["acs"], data["redfin"], data["cpi"], data["counties"]
ratio_df = compute_price_to_income(acs, redfin)

display_names = (counties["county_name"] + ", " + counties["state"] + " — " + counties["county_fips"])
choice = st.selectbox("Choose a county", display_names)
selected_fips = choice.split("—")[-1].strip()

# Yearly prices
redfin_yearly = (redfin.assign(year=redfin['period'].str.slice(0,4).astype(int))
                 .groupby(['county_fips','year'], as_index=False)['median_sale_price'].mean()
                 .rename(columns={'median_sale_price':'avg_price'}))

c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(line_prices(redfin_yearly, counties, selected_fips), use_container_width=True)
with c2:
    st.plotly_chart(line_ratio(ratio_df, counties, selected_fips), use_container_width=True)

st.markdown("---")
st.write("Raw yearly table:")
st.dataframe(ratio_df[ratio_df["county_fips"]==selected_fips].sort_values("year"))
