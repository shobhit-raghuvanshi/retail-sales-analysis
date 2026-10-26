# 🛒 Retail Sales & Profitability Analysis Dashboard

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-Visualizations-blueviolet.svg)](https://plotly.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey.svg)](https://www.sqlite.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-orange.svg)](https://pandas.pydata.org/)

An end-to-end data analytics project featuring a normalized **SQLite relational database**, deep exploratory data analysis (EDA) via **Jupyter Notebook**, and a fully interactive **Streamlit & Plotly web application** to uncover actionable retail insights from the Superstore dataset.

---

## 🚀 Project Overview

The goal of this project is to transform raw transactional retail data into strategic business intelligence. The workflow covers relational database design, data cleaning, complex SQL querying, statistical analysis, and interactive frontend deployment.

### 📊 Key Performance Indicators (Global Metrics)
* **Total Revenue:** $2,297,200.86
* **Total Profit:** $286,397.02
* **Overall Profit Margin:** 12.47%
* **Total Quantities Sold:** 37,873 units
* **Unique Orders:** 5,009
* **Average Order Value (AOV):** $458.61
* **Unique Customers Served:** 793

---

## 🗂️ Repository Structure

```text
retail-sales-analysis/
│
├── app.py                     # Interactive Streamlit dashboard frontend
├── create_db_from_csv.py      # Script to parse CSV and build SQLite DB
├── superstore_schema.sql      # Database relational schema definition
├── retail_sales_analysis_using_sql.ipynb # Comprehensive EDA & SQL notebook
├── superstore.csv             # Raw dataset file
├── superstore.db              # SQLite database (auto-generated or pre-built)
└── README.md                  # Project documentation
```

---

## 🛠️ Installation & Quickstart

Follow these steps to set up and run the project locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/shobhit-raghuvanshi/retail-sales-analysis.git
cd retail-sales-analysis
```

### 2. Install Dependencies
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

*(Core dependencies: `pandas`, `numpy`, `matplotlib`, `plotly`, `streamlit`, `sqlite3`)*

### 3. Generate Database (Optional)
If you want to recreate the SQLite database from scratch using the SQL schema and raw CSV:
```bash
python create_db_from_csv.py
```

### 4. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```

---

## 💡 Key Business Insights & Findings

### 1. Category & Product Performance
* **Technology:** Generates the highest total profit ($145,454.95) and revenue, making it the most lucrative category despite selling fewer overall units.
* **Office Supplies:** Achieves the highest volume of units sold (22,906) and contributes a steady profit of $122,490.80.
* **Furniture:** Generates massive revenue ($741,999.80) but yields a remarkably low profit of only $18,451.27 due to tight margins and high logistics/shipping costs.
* **Product Outliers:** Identified **192 products** that generate above-median sales but operate at a net loss. Recommending price adjustments or discount caps on these SKUs.

### 2. Geographic & Segment Breakdown
* **Regional Performance:** The **West Region** leads all metrics ($725.5k sales, $108.4k profit, 1,611 orders). Conversely, the **Central Region** underperforms significantly in profitability ($39.7k profit) despite out-earning the South, pointing toward operational inefficiencies or aggressive discounting in the Midwest.
* **Customer Segments:** The **Consumer Segment** forms the core business backbone ($1.16M+ in sales), followed by Corporate and Home Office segments.

### 3. Temporal Trends & Seasonality
* **Year-over-Year Growth:** Consistent upward trajectory in both sales and profits from 2014 through 2017.
* **Seasonality:** Strong cyclical spikes occur consistently in **Q4 (November & December)** each year, reflecting holiday shopping surges.

### 4. Discount vs. Profitability Correlation
* **The Promotional Threshold:** Scatter analysis reveals a negative correlation (-0.219) between discount rates and profitability. Offering discounts **exceeding 20%** dramatically increases the risk of loss-making transactions.
* **Unprofitable Transactions:** 1,871 transactions (approx. 18.7% of total sales) were unprofitable, resulting in a cumulative loss of -$156,131.29.

---

## 🖥️ Streamlit Dashboard Features (`app.py`)

The application features a modern sidebar for global filtering (Date Range, Region, Category, and Segment) and is organized across 6 dedicated tabs:
1. **Executive Summary:** High-level KPI metric cards, category sales vs. profit comparisons, and profit distributions.
2. **Product Insights:** Deep dive into top-performing products, loss-makers, and high-sales negative margin outliers.
3. **Geography & Segment:** Regional performance breakdowns, customer segment metrics, and an interactive **US State Profitability Map**.
4. **Temporal Trends:** Multi-line monthly revenue/profit trends and annual category growth comparisons.
5. **Discount vs Profitability:** Discount rate distributions, average profit per discount level, and interactive scatter plots.
6. **Raw Data & Schema:** Database row counts, preview of `retail_analysis_view`, and custom CSV download buttons for filtered data.

---

## 📝 Database Architecture

The SQLite database is normalized into 5 primary tables linked via foreign keys:
* `customers`: Customer profiles and market segments (793 records).
* `locations`: Geographic data including city, state, region, and postal code (632 records).
* `products`: Product catalog, categories, and sub-categories (1,862 records).
* `orders`: Order metadata and customer mappings (5,009 records).
* `order_items`: Transactional line items containing sales, quantities, discounts, and profits (9,994 records).

---

## 👤 Author
Developed as a portfolio project showcasing full-stack data analysis, SQL database design, data visualization, and interactive web application deployment.