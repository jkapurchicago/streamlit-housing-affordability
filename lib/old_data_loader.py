import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

@st.cache_data(show_spinner=False)
def read_csv(name: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, name)
    return pd.read_csv(path)

def secrets_has_mysql() -> bool:
    try:
        s = st.secrets["mysql"]
        return all(k in s for k in ("host","user","password","database"))
    except Exception:
        return False

def get_mysql_engine():
    s = st.secrets["mysql"]
    # Support Unix socket connections if provided in secrets as `socket`.
    # Example secrets:
    # [mysql]
    # user = "root"
    # password = "..."
    # database = "inflation_affordability_three"
    # socket = "/tmp/mysql.sock"  # optional; if set, TCP host/port are ignored
    if "socket" in s and s["socket"]:
        # SQLAlchemy/PyMySQL supports unix_socket as a query param
        url = (
            f"mysql+pymysql://{s['user']}:{s['password']}@localhost/"
            f"{s['database']}?unix_socket={s['socket']}"
        )
    else:
        url = (
            f"mysql+pymysql://{s['user']}:{s['password']}@{s['host']}:{s.get('port',3306)}/"
            f"{s['database']}"
        )
    return create_engine(url, pool_pre_ping=True)

def _pad_fips(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    is_num = s.str.fullmatch(r"\d+")
    return s.where(~is_num, s.str.zfill(5))

@st.cache_data(show_spinner=True, ttl=300)
def load_data(source: str = "auto"):
    """
    Returns dict: {acs, redfin, cpi, counties}

    MySQL:
      - Prices from fact_housing(_v2) at ZIP level, aggregated monthly (period=YYYY-MM).
      - Income from fact_income joined with dim_location (county_geo_id).
      - CPI from fact_cpi joined with dim_date.
      - Counties from dim_location (county_geo_id).  (Used for labels/maps if mappable.)
    """
    if source == "auto":
        source = "mysql" if secrets_has_mysql() else "csv"

    if source == "mysql":
        try:
            engine = get_mysql_engine()
            with engine.begin() as conn:
                # ---- Income by county/year ----
                acs = pd.read_sql(text("""
                    SELECT
                        dl.county_geo_id AS county_fips,
                        dl.county_name,
                        dl.state_fips    AS state,
                        fi.year,
                        fi.income_usd
                    FROM fact_income fi
                    JOIN dim_location dl
                      ON dl.county_geo_id = fi.county_geo_id
                """), conn)

                # ---- Housing monthly from fact_housing_v2 if exists, else fact_housing (ZIP level) ----
                tbl = "fact_housing_v2"
                exists = pd.read_sql(text("""
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE() AND table_name = 'fact_housing_v2'
                    LIMIT 1
                """), conn).shape[0] == 1
                if not exists:
                    tbl = "fact_housing"

                redfin = pd.read_sql(text(f"""
                    SELECT
                        fh.zip_code,
                        CONCAT(dd.year,'-', LPAD(dd.month,2,'0')) AS period,
                        fh.median_sale_price
                    FROM {tbl} fh
                    JOIN dim_date dd
                      ON dd.date_id = fh.date_id
                    WHERE fh.median_sale_price IS NOT NULL
                """), conn)

                # ---- CPI monthly ----
                cpi = pd.read_sql(text("""
                    SELECT
                        CONCAT(dd.year,'-', LPAD(dd.month,2,'0')) AS date,
                        fc.series_id,
                        fc.cpi_value AS value
                    FROM fact_cpi fc
                    JOIN dim_date dd
                      ON dd.date_id = fc.date_id
                """), conn)

                # ---- County labels (for income/map) ----
                counties = pd.read_sql(text("""
                    SELECT
                        dl.county_geo_id AS county_fips,
                        dl.county_name,
                        dl.state_fips    AS state,
                        dl.state_fips    AS state_fips
                    FROM dim_location dl
                    WHERE dl.county_geo_id IS NOT NULL
                """), conn)

            # normalize
            if "county_fips" in acs.columns:
                acs["county_fips"] = _pad_fips(acs["county_fips"])
            if "county_fips" in counties.columns:
                counties["county_fips"] = _pad_fips(counties["county_fips"])
            redfin["period"] = redfin["period"].astype(str).str.slice(0,7)
            cpi["date"] = cpi["date"].astype(str).str.slice(0,7)

            return {"acs": acs, "redfin": redfin, "cpi": cpi, "counties": counties}
        except Exception as e:
            st.warning(f"MySQL load failed ({e}). Falling back to CSV samples.")

    # ---- CSV fallback (shipped with the project) ----
    acs = read_csv("acs_income_sample.csv")
    redfin = read_csv("redfin_housing_sample.csv")
    cpi = read_csv("bls_cpi_sample.csv")
    counties = read_csv("county_fips_sample.csv")

    for df in (acs, counties):
        if "county_fips" in df.columns:
            df["county_fips"] = _pad_fips(df["county_fips"])
    redfin["period"] = redfin["period"].astype(str).str.slice(0,7)
    cpi["date"] = cpi["date"].astype(str).str.slice(0,7)

    return {"acs": acs, "redfin": redfin, "cpi": cpi, "counties": counties}

def compute_price_to_income(acs: pd.DataFrame, redfin: pd.DataFrame) -> pd.DataFrame:
    """
    County-level: requires redfin to have county_fips.
    Since your housing is ZIP-level (no county mapping yet), we return an EMPTY df with expected columns.
    The app/pages will detect this and fall back gracefully.
    """
    expected_cols = ["county_fips","year","avg_price","income_usd","price_to_income"]
    if "county_fips" not in redfin.columns:
        return pd.DataFrame(columns=expected_cols)

    rf = redfin.copy()
    rf["year"] = rf["period"].str.slice(0,4).astype(int)
    yearly = (rf.groupby(["county_fips","year"], as_index=False)["median_sale_price"]
                .mean().rename(columns={"median_sale_price":"avg_price"}))
    out = yearly.merge(acs[["county_fips","year","income_usd"]], on=["county_fips","year"], how="left")
    out["price_to_income"] = (out["avg_price"] / out["income_usd"]).round(2)
    return out[expected_cols]

def cpi_pivot(cpi: pd.DataFrame) -> pd.DataFrame:
    return cpi.pivot_table(index="date", columns="series_id", values="value").reset_index()
