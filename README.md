# HomeGraph: Housing Affordability Data Engineering Project

## Project Summary

This project is a **Housing Affordability Streamlit App** designed to answer a core question: **Have housing costs become less affordable over time when compared to household income growth and general inflation trends?**

The application integrates data from three major sources to calculate an **Aggregate Affordability Index**, which highlights areas where the median home sale price is outpacing income growth and the Consumer Price Index (CPI).

---

## Presentation

Watch the project presentation for a detailed walkthrough of the goal, data, and data engineering methodology:

[![HomeGraph Presentation](https://img.youtube.com/vi/DcoCmjygeE8/0.jpg)](https://www.youtube.com/watch?v=DcoCmjygeE8)

---

## Technology Stack & Data Engineering

This project involved building a robust ETL (Extract, Transform, Load) pipeline to process large, multi-source datasets and load them into a relational Data Warehouse.

### Key Technologies
* **Application:** **Streamlit** (`app.py`) for the interactive web interface.
* **Big Data Processing:** **PySpark** (Spark Jobs) was essential for handling the large Redfin dataset (approximately 9 million records, 5GB+ uncompressed) using parallel processing.
* **Data Storage:** MySQL (Data Warehouse) and SQLite (for local sample data).
* **Data Stack:** Python, Pandas, Plotly, SQLAlchemy.

### Data Sources
| Source | Data Type | Key Information |
| :--- | :--- | :--- |
| **Redfin** | Compressed File | Median home sale price, number of homes sold, and days on market by ZIP code/County. |
| **US Census Bureau (ACS)** | REST API | Median-level household income per county. |
| **Bureau of Labor Statistics (BLS) CPI** | REST API | Consumer Price Index (CPI) to track inflation of essential goods and services over time. |

---

## Quickstart

The app ships with a toy sample dataset so it runs offline immediately.

```bash
pip install -r requirements.txt
streamlit run app.py