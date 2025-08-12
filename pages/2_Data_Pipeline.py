import streamlit as st
import pandas as pd
from lib.data_loader import load_data, compute_price_to_income, cpi_pivot

st.title("🧱 Data Pipeline — Extract • Transform • Load")

st.markdown("#### Extract")
st.code("""
# CSV (default)
acs = pd.read_csv("data/acs_income_sample.csv")
redfin = pd.read_csv("data/redfin_housing_sample.csv")
cpi = pd.read_csv("data/bls_cpi_sample.csv")

# Or from MySQL if secrets are set
from sqlalchemy import create_engine, text
engine = create_engine("mysql+pymysql://user:pwd@host:3306/housing_dw")
acs = pd.read_sql(text("SELECT * FROM fact_income"), engine)
redfin = pd.read_sql(text("SELECT * FROM fact_housing"), engine)
cpi = pd.read_sql(text("SELECT DATE_FORMAT(date_key,'%Y-%m') AS date, series_id, value FROM fact_cpi"), engine)
""", language="python")

st.markdown("#### Transform")
st.code("""
# Standardize keys
redfin['year'] = redfin['period'].str.slice(0,4).astype(int)
# Aggregate to yearly
yearly_prices = (redfin.groupby(['county_fips','year'], as_index=False)
                 ['median_sale_price'].mean().rename(columns={'median_sale_price':'avg_price'}))

# Combine with ACS
df = yearly_prices.merge(acs[['county_fips','year','income_usd']], on=['county_fips','year'], how='left')
df['price_to_income'] = (df['avg_price'] / df['income_usd']).round(2)

# CPI wide for multi-series plots
cpi_wide = cpi.pivot_table(index='date', columns='series_id', values='value').reset_index()
""", language="python")

st.markdown("#### Load")
st.code("""
# Option 1: Keep as pandas and cache in Streamlit
st.session_state['dfs'] = {'acs': acs, 'redfin': redfin, 'cpi': cpi}

# Option 2: Write to data warehouse (MySQL) via SQLAlchemy
yearly_prices.to_sql("fact_housing_yearly", engine, if_exists="replace", index=False)
""", language="python")

st.success("This page documents the pipeline logic with real code snippets for your portfolio.")
