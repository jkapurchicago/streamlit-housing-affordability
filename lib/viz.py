import plotly.express as px
import pandas as pd

# ---------- helpers ----------
def _fips_series(series: pd.Series) -> pd.Series:
    """
    Convert a county identifier to Plotly-friendly 5-digit FIPS when possible.
    Non-numeric IDs are kept as-is but will be filtered out from the map.
    """
    s = series.astype(str).str.strip()
    is_num = s.str.fullmatch(r"\d+")
    return s.where(~is_num, s.str.zfill(5))

# ---------- CPI ----------
def line_cpi(cpi_wide: pd.DataFrame):
    """
    Multi-series CPI line chart. Expects a pivoted dataframe with:
      columns: ['date', SERIES_1, SERIES_2, ...]
    """
    cols = [c for c in cpi_wide.columns if c != "date"]
    fig = px.line(
        cpi_wide,
        x="date",
        y=cols,
        title="CPI Series Over Time",
    )
    fig.update_layout(legend_title_text="Series ID", hovermode="x unified")
    return fig

# ---------- County drilldown (kept for compatibility with the Exploration page) ----------
def line_prices(redfin_yearly: pd.DataFrame, county_meta: pd.DataFrame, county_fips: str):
    """
    Yearly average price trend for a county.
    Expects redfin_yearly with columns: ['county_fips','year','avg_price']
    """
    sub = redfin_yearly[redfin_yearly["county_fips"] == county_fips]
    if sub.empty:
        return px.scatter(title="No price data for selected county")
    name = county_meta.loc[county_meta["county_fips"] == county_fips, "county_name"]
    name = name.iloc[0] if not name.empty else county_fips
    fig = px.line(
        sub,
        x="year",
        y="avg_price",
        markers=True,
        title=f"Average Median Sale Price per Year — {name}",
    )
    return fig

def line_ratio(ratio_df: pd.DataFrame, county_meta: pd.DataFrame, county_fips: str):
    """
    Price-to-income ratio trend for a county.
    Expects ratio_df with columns: ['county_fips','year','price_to_income']
    """
    sub = ratio_df[ratio_df["county_fips"] == county_fips]
    if sub.empty:
        return px.scatter(title="No affordability ratio for selected county")
    name = county_meta.loc[county_meta["county_fips"] == county_fips, "county_name"]
    name = name.iloc[0] if not name.empty else county_fips
    fig = px.line(
        sub,
        x="year",
        y="price_to_income",
        markers=True,
        title=f"Price-to-Income Ratio — {name}",
    )
    return fig

# ---------- Maps ----------
def choropleth_ratio(ratio_df: pd.DataFrame, counties: pd.DataFrame, year: int):
    """
    County choropleth of price-to-income ratio for a given year.
    Requires ratio_df with ['county_fips','year','price_to_income'] and
    counties with ['county_fips','county_name','state'].
    """
    if ratio_df.empty:
        return px.scatter(title="No county-level affordability yet")

    df = ratio_df[ratio_df["year"] == year].merge(
        counties[["county_fips", "county_name", "state"]],
        on="county_fips",
        how="left",
    )
    if df.empty:
        return px.scatter(title=f"No data for {year}")

    df["fips"] = _fips_series(df["county_fips"])
    df = df[df["fips"].str.fullmatch(r"\d{5}") == True]
    if df.empty:
        return px.scatter(title="No mappable counties (need numeric 5-digit FIPS)")

    fig = px.choropleth(
        df,
        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
        locations="fips",
        color="price_to_income",
        hover_name="county_name",
        hover_data={"fips": False, "state": True, "price_to_income": ":.2f"},
        scope="usa",
        title=f"Price-to-Income Ratio by County — {year}",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    return fig

def choropleth_income(acs_year: pd.DataFrame):
    """
    Fallback county choropleth by income when ratio isn't available.
    Expects acs_year with ['county_fips','income_usd'] (optionally county_name).
    """
    if acs_year.empty:
        return px.scatter(title="No county income to map")

    df = acs_year.copy()
    df["fips"] = _fips_series(df["county_fips"])
    df = df[df["fips"].str.fullmatch(r"\d{5}") == True]
    if df.empty:
        return px.scatter(title="No mappable counties (need numeric 5-digit FIPS)")

    fig = px.choropleth(
        df,
        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
        locations="fips",
        color="income_usd",
        hover_name="county_name" if "county_name" in df.columns else None,
        hover_data={"fips": False, "income_usd": ":,.0f"},
        scope="usa",
        title="Median Household Income by County",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    return fig
