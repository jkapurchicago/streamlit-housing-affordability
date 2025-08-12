import streamlit as st

st.title("📚 Appendix — Code Chunks & Explanations")

st.markdown("### 1) Price-to-Income Ratio")
st.code("""
def compute_price_to_income(acs, redfin):
    redfin['year'] = redfin['period'].str.slice(0,4).astype(int)
    yearly = redfin.groupby(['county_fips','year'], as_index=False)['median_sale_price'].mean().rename(columns={'median_sale_price':'avg_price'})
    df = yearly.merge(acs[['county_fips','year','income_usd']], on=['county_fips','year'], how='left')
    df['price_to_income'] = (df['avg_price'] / df['income_usd']).round(2)
    return df
""", language="python")
st.write("We aggregate monthly prices into a yearly average per county, then divide by the ACS household income for that county-year.")

st.markdown("### 2) CPI Wide Pivot")
st.code("""
def cpi_pivot(cpi):
    return cpi.pivot_table(index='date', columns='series_id', values='value').reset_index()
""", language="python")
st.write("Pivoting enables multi-series line charts for CPI categories.")

st.markdown("### 3) Choropleth Map Setup")
st.code("""
px.choropleth(df,
              geojson='https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json',
              locations='fips', color='price_to_income', scope='usa')
""", language="python")
st.write("Plotly comes with a ready USA counties GeoJSON for choropleths.")
