import streamlit as st
import pandas as pd
from datetime import datetime

from lib.data_loader import load_data, compute_price_to_income, cpi_pivot
from lib.viz import line_cpi, choropleth_ratio, choropleth_income

st.set_page_config(
    page_title="Housing Affordability — CPI vs Income vs Home Prices",
    layout="wide",
)

st.title("🏡 Housing Affordability — CPI vs Income vs Home Prices")
st.caption("A portfolio app comparing housing costs (Redfin), incomes (ACS), and inflation (BLS CPI).")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Data Source")
    source = st.radio("Use data from:", ["auto", "csv", "mysql"], index=0)
    st.markdown("---")
    st.write("If housing is only at ZIP level (no county mapping yet), the app will gracefully fall back.")
    st.markdown("---")
    st.write("Tip: add DB creds & API keys in `.streamlit/secrets.toml`.")

# --------------- Load & prep ---------------
data = load_data(source)
acs, redfin, cpi, counties = data["acs"], data["redfin"], data["cpi"], data["counties"]

ratio_df = compute_price_to_income(acs, redfin)  # may be EMPTY (no county mapping yet)
cpi_wide = cpi_pivot(cpi)

# --------------- KPIs (robust to missing ratio) ---------------
def _safe_median(series):
    s = pd.to_numeric(series, errors="coerce").dropna()
    return float(s.median()) if not s.empty else float("nan")

latest_income_year = pd.to_numeric(acs.get("year"), errors="coerce").max()
latest_price_year = pd.to_numeric(redfin["period"].str[:4], errors="coerce").max()

kpi_price = _safe_median(
    redfin.loc[
        redfin["period"].str.startswith(str(int(latest_price_year))) if pd.notna(latest_price_year) else [],
        "median_sale_price",
    ]
)
kpi_income = _safe_median(acs.loc[acs["year"] == latest_income_year, "income_usd"])

if ratio_df.empty:
    st.info(
        "County-level affordability requires a ZIP→county mapping. "
        "Until that’s in place, we’ll show CPI and headline KPIs (price & income)."
    )
    kpi_ratio = (kpi_price / kpi_income) if (pd.notna(kpi_price) and pd.notna(kpi_income) and kpi_income) else float("nan")
else:
    latest_year = int(ratio_df["year"].max())
    kpi_ratio = _safe_median(ratio_df.loc[ratio_df["year"] == latest_year, "price_to_income"])
    # align other KPIs to the same year
    kpi_price = _safe_median(redfin.loc[redfin["period"].str.startswith(str(latest_year)), "median_sale_price"])
    kpi_income = _safe_median(acs.loc[acs["year"] == latest_year, "income_usd"])

c1, c2, c3 = st.columns(3)
c1.metric("Avg Price-to-Income", "—" if pd.isna(kpi_ratio) else f"{kpi_ratio:.2f}")
c2.metric("Median Sale Price", "—" if pd.isna(kpi_price) else f"${int(kpi_price):,}")
c3.metric("Median Household Income", "—" if pd.isna(kpi_income) else f"${int(kpi_income):,}")

# --------------- CPI chart ---------------
st.subheader("Inflation Context — CPI Series")
st.plotly_chart(line_cpi(cpi_wide), use_container_width=True)

# --------------- Map (ratio if available; else income fallback) ---------------
st.subheader("Affordability Map")
if ratio_df.empty:
    if acs.empty:
        st.warning("No county metadata to map yet.")
    else:
        y_min = int(pd.to_numeric(acs["year"], errors="coerce").min())
        y_max = int(pd.to_numeric(acs["year"], errors="coerce").max())
        default_y = y_max if pd.notna(y_max) else y_min
        year = st.slider("Year (Income Map)", y_min, y_max, default_y, step=1)
        acs_year = (
            acs[acs["year"] == year]
            .merge(counties[["county_fips", "county_name", "state"]], on="county_fips", how="left")
        )
        st.plotly_chart(choropleth_income(acs_year), use_container_width=True)
        st.caption("Fallback: mapping county incomes while affordability is being wired.")
else:
    y_min = int(ratio_df["year"].min())
    y_max = int(ratio_df["year"].max())
    year = st.slider("Year (Affordability Map)", y_min, y_max, y_max, step=1)
    st.plotly_chart(choropleth_ratio(ratio_df, counties, year), use_container_width=True)
    st.caption("Plotly county GeoJSON requires 5-digit numeric FIPS; non-numeric IDs are ignored.")

# --------------- How we compute (code explainer) ---------------
st.markdown("---")
st.markdown("### How affordability is computed (once county mapping exists)")
st.code(
    """# 1) Aggregate ZIP → County or use county-level prices directly to build yearly averages
# redfin must have columns: county_fips, period (YYYY-MM), median_sale_price

redfin['year'] = redfin['period'].str.slice(0, 4).astype(int)
yearly = (redfin.groupby(['county_fips', 'year'], as_index=False)
          ['median_sale_price'].mean()
          .rename(columns={'median_sale_price': 'avg_price'}))

# 2) Join to ACS income by county/year
df = yearly.merge(acs[['county_fips','year','income_usd']], on=['county_fips','year'], how='left')

# 3) Ratio = avg_price / income_usd
df['price_to_income'] = (df['avg_price'] / df['income_usd']).round(2)""",
    language="python",
)
