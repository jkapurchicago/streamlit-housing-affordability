# Housing Affordability Streamlit App

A polished portfolio app comparing **housing costs** (Redfin), **incomes** (ACS), and **inflation** (BLS CPI).  
It ships with toy sample data so it runs offline immediately, but can connect to real sources via API keys and/or MySQL.

## Quickstart
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Secrets & Keys
Create `.streamlit/secrets.toml`:

```toml
[mysql]
host = "localhost"
port = 3306
user = "username"
password = "password"
database = "housing_dw"

BLS_KEY = "your_bls_key"
CENSUS_KEY = "your_census_key"
```
