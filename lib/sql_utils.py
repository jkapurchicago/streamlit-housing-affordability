import sqlite3
import pandas as pd

def load_sample_into_sqlite(db_path: str, acs: pd.DataFrame, redfin: pd.DataFrame, cpi: pd.DataFrame, counties: pd.DataFrame):
    conn = sqlite3.connect(db_path)
    acs.to_sql("fact_income", conn, if_exists="replace", index=False)
    redfin.to_sql("fact_housing", conn, if_exists="replace", index=False)
    cpi.to_sql("fact_cpi", conn, if_exists="replace", index=False)
    counties.to_sql("dim_location", conn, if_exists="replace", index=False)
    # simple dim_date (YYYY-MM to first of month)
    dates = pd.DataFrame({"full_date": pd.to_datetime(cpi["date"]+"-01").drop_duplicates()})
    dates["date_id"] = dates["full_date"].dt.strftime("%Y%m%d").astype(int)
    dates["year"] = dates["full_date"].dt.year
    dates["month"] = dates["full_date"].dt.month
    dates["day_of_month"] = dates["full_date"].dt.day
    dates["quarter"] = ((dates["month"]-1)//3)+1
    dates["day_of_week"] = dates["full_date"].dt.dayofweek
    dates["is_weekend"] = dates["day_of_week"].isin([5,6])
    dates.to_sql("dim_date", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

MYSQL_DDL = {
"dim_date": """
CREATE TABLE IF NOT EXISTS dim_date(
  date_id         INT PRIMARY KEY,
  full_date       DATE NOT NULL,
  year            SMALLINT NOT NULL,
  quarter         TINYINT,
  month           TINYINT,
  day_of_month    TINYINT,
  day_of_week     TINYINT,
  is_weekend      BOOLEAN
);
""",
"dim_location": """
CREATE TABLE IF NOT EXISTS dim_location(
  location_id     INT AUTO_INCREMENT PRIMARY KEY,
  state_fips      CHAR(2) NOT NULL,
  state_name      VARCHAR(50),
  county_fips     CHAR(5),
  county_name     VARCHAR(60),
  metro_area      VARCHAR(60),
  census_region   VARCHAR(20)
);
""",
"fact_housing": """
CREATE TABLE IF NOT EXISTS fact_housing(
  county_fips       CHAR(5),
  county_name       VARCHAR(60),
  state             CHAR(2),
  period            CHAR(7),          -- YYYY-MM
  median_sale_price INT,
  KEY idx1 (county_fips, period)
);
""",
"fact_income": """
CREATE TABLE IF NOT EXISTS fact_income(
  county_fips  CHAR(5),
  county_name  VARCHAR(60),
  state        CHAR(2),
  year         INT,
  income_usd   INT,
  KEY idx1 (county_fips, year)
);
""",
"fact_cpi": """
CREATE TABLE IF NOT EXISTS fact_cpi(
  date_key    DATE,
  series_id   VARCHAR(20),
  value       DECIMAL(10,1),
  KEY idx1 (date_key, series_id)
);
"""
}
