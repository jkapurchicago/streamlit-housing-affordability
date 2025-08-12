import streamlit as st

st.title("📌 Project Overview")
st.markdown("""
**Question:** _Has housing become less affordable over time when compared to income growth and inflation trends?_

**Data**  
- **Redfin**: county-level median sale prices (monthly)  
- **ACS (U.S. Census)**: household income by county (yearly)  
- **BLS CPI**: inflation indexes by category (monthly)

**Approach**  
1. Ingest the three datasets (CSV, API, or MySQL).  
2. Clean and standardize time keys (YYYY-MM and YYYY) and geographic keys (county FIPS).  
3. Aggregate prices to yearly averages; compute **price-to-income**.  
4. Compare with CPI trends to contextualize affordability.  
5. Visualize trends and a county-level map, and enable an ad-hoc SQL workbench.
""")
st.info("Tip: Use the **Settings** page to choose your data source or upload files.")
