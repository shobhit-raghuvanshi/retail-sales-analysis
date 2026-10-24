import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Superstore Data Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# DATABASE CONNECTION & DATA LOADING
# -----------------------------------------------------------------------------
DB_PATH = Path("superstore.db")


@st.cache_resource
def get_connection():
    """Establish and cache the SQLite database connection."""
    if not DB_PATH.exists():
        st.error(f"Database file '{DB_PATH}' not found in current directory.")
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


conn = get_connection()


@st.cache_data
def load_and_prepare_data():
    """Create database view if not exists and load cleaned DataFrame."""
    # Ensure view exists
    conn.execute("DROP VIEW IF EXISTS retail_analysis_view")
    conn.execute(
        """
        CREATE VIEW retail_analysis_view AS 
        SELECT 
            oi.row_id, o.order_id, o.order_date, o.ship_date, o.ship_mode, 
            c.customer_id, c.customer_name, c.segment, 
            p.product_id, p.product_name, p.category, p.sub_category, 
            l.country, l.city, l.state, l.postal_code, l.region, 
            oi.sales, oi.quantity, oi.discount, oi.profit 
        FROM order_items AS oi 
        JOIN orders AS o ON oi.order_id=o.order_id 
        JOIN customers AS c ON o.customer_id=c.customer_id 
        JOIN products AS p ON oi.product_id=p.product_id 
        LEFT JOIN locations AS l ON o.location_id=l.location_id
    """
    )
    conn.commit()

    df = pd.read_sql_query("SELECT * FROM retail_analysis_view", conn)

    # Date parsing & temporal feature extraction
    df["order_date"] = pd.to_datetime(
        df["order_date"], format="%Y-%m-%d", errors="coerce"
    )
    df["ship_date"] = pd.to_datetime(
        df["ship_date"], format="%Y-%m-%d", errors="coerce"
    )
    df["order_year"] = df["order_date"].dt.year
    df["order_month"] = df["order_date"].dt.month
    df["order_year_month"] = df["order_date"].dt.to_period("M").astype(str)

    return df


df_raw = load_and_prepare_data()

# -----------------------------------------------------------------------------
# SIDEBAR FILTERS
# -----------------------------------------------------------------------------
st.sidebar.title("Navigation & Filters")

# Global Date Filter
min_date = df_raw["order_date"].min().date()
max_date = df_raw["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Region & Category Filters
all_regions = sorted(df_raw["region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect(
    "Select Region(s)", options=all_regions, default=all_regions
)

all_categories = sorted(df_raw["category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Select Category(s)", options=all_categories, default=all_categories
)

all_segments = sorted(df_raw["segment"].dropna().unique().tolist())
selected_segments = st.sidebar.multiselect(
    "Select Segment(s)", options=all_segments, default=all_segments
)

# Filter Data
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df_raw[
        (df_raw["order_date"].dt.date >= start_date)
        & (df_raw["order_date"].dt.date <= end_date)
        & (df_raw["region"].isin(selected_regions))
        & (df_raw["category"].isin(selected_categories))
        & (df_raw["segment"].isin(selected_segments))
    ]
else:
    filtered_df = df_raw.copy()

# -----------------------------------------------------------------------------
# MAIN APP LAYOUT
# -----------------------------------------------------------------------------
st.title("Superstore Sales & Profitability EDA")
st.markdown(
    "An interactive dashboard based on the Superstore SQLite dataset analysis."
)

# Navigation Tabs
tab_overview, tab_categories, tab_geo, tab_temporal, tab_discount, tab_data = (
    st.tabs(
        [
            "Executive Summary",
            "Product Insights",
            "Geography & Segment",
            "Temporal Trends",
            "Discount vs Profitability",
            "Raw Data & Schema",
        ]
    )
)

# -----------------------------------------------------------------------------
# TAB 1: EXECUTIVE SUMMARY
# -----------------------------------------------------------------------------
with tab_overview:
    st.subheader("High-Level Business Metrics")

    tot_sales = filtered_df["sales"].sum()
    tot_profit = filtered_df["profit"].sum()
    profit_margin = (tot_profit / tot_sales * 100) if tot_sales > 0 else 0
    tot_qty = filtered_df["quantity"].sum()
    tot_orders = filtered_df["order_id"].nunique()
    tot_customers = filtered_df["customer_id"].nunique()

    # Average Order Value
    order_summary = filtered_df.groupby("order_id")["sales"].sum()
    avg_order_val = order_summary.mean() if not order_summary.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"${tot_sales:,.2f}")
    col2.metric(
        "Total Profit",
        f"${tot_profit:,.2f}",
        delta=f"{profit_margin:.2f}% Margin",
    )
    col3.metric("Avg Order Value (AOV)", f"${avg_order_val:,.2f}")
    col4.metric("Total Quantity Sold", f"{tot_qty:,} units")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Unique Orders", f"{tot_orders:,}")
    col6.metric("Unique Customers", f"{tot_customers:,}")
    col7.metric(
        "Avg Discount", f"{filtered_df['discount'].mean() * 100:.1f}%"
    )
    col8.metric("Total Line Items", f"{len(filtered_df):,}")

    st.markdown("---")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### Performance Overview by Category")
        cat_agg = (
            filtered_df.groupby("category")
            .agg(
                Sales=("sales", "sum"),
                Profit=("profit", "sum"),
                Quantity=("quantity", "sum"),
            )
            .reset_index()
        )

        fig_cat = px.bar(
            cat_agg,
            x="category",
            y=["Sales", "Profit"],
            barmode="group",
            title="Sales vs Profit by Category",
            labels={"value": "Amount ($)", "category": "Product Category"},
            color_discrete_sequence=["#2ca02c", "#1f77b4"],
        )
        st.plotly_chart(fig_cat, width='stretch')

    with col_b:
        st.markdown("### Profitability Distribution")
        fig_hist = px.histogram(
            filtered_df,
            x="profit",
            nbins=50,
            title="Transaction Profit Distribution",
            labels={"profit": "Profit ($)"},
            color_discrete_sequence=["#ff7f0e"],
        )
        fig_hist.update_layout(yaxis_title="Count")
        st.plotly_chart(fig_hist, width='stretch')

# -----------------------------------------------------------------------------
# TAB 2: CATEGORICAL & PRODUCT-LEVEL INSIGHTS
# -----------------------------------------------------------------------------
with tab_categories:
    st.subheader("Category & Product Performance")

    # Category Bar Charts (Matching Notebook Figures)
    cat_summary = (
        filtered_df.groupby("category")
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            total_quantity=("quantity", "sum"),
        )
        .reset_index()
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        fig1 = px.bar(
            cat_summary,
            x="category",
            y="total_sales",
            title="Sales by Category",
            color_discrete_sequence=["lightgreen"],
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, width='stretch')

    with c2:
        fig2 = px.bar(
            cat_summary,
            x="category",
            y="total_profit",
            title="Profit by Category",
            color_discrete_sequence=["lightblue"],
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, width='stretch')

    with c3:
        fig3 = px.bar(
            cat_summary,
            x="category",
            y="total_quantity",
            title="Quantity Sold by Category",
            color_discrete_sequence=["lightcoral"],
        )
        fig3.update_layout(showlegend=False)
        st.plotly_chart(fig3, width='stretch')

    st.markdown("---")
    st.markdown("### Top & Bottom Performers")

    product_analysis = (
        filtered_df.groupby("product_name")
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            quantity_sold=("quantity", "sum"),
        )
        .reset_index()
    )

    product_analysis["profit_margin_pct"] = (
        product_analysis["total_profit"] / product_analysis["total_sales"]
    ) * 100

    col_top, col_bot = st.columns(2)
    with col_top:
        st.markdown("**Top 10 Most Profitable Products**")
        top_10 = product_analysis.nlargest(10, "total_profit")
        st.dataframe(
            top_10.style.format(
                {
                    "total_sales": "${:,.2f}",
                    "total_profit": "${:,.2f}",
                    "profit_margin_pct": "{:.2f}%",
                }
            ),
            width='stretch',
        )

    with col_bot:
        st.markdown("**Top 10 Unprofitable Products (Loss Makers)**")
        bottom_10 = product_analysis.nsmallest(10, "total_profit")
        st.dataframe(
            bottom_10.style.format(
                {
                    "total_sales": "${:,.2f}",
                    "total_profit": "${:,.2f}",
                    "profit_margin_pct": "{:.2f}%",
                }
            ),
            width='stretch',
        )

    st.markdown("### High Sales, Negative Profit Outliers")
    median_sales = product_analysis["total_sales"].median()
    outlier_products = product_analysis[
        (product_analysis["total_sales"] > median_sales)
        & (product_analysis["total_profit"] < 0)
    ].sort_values(by="total_sales", ascending=False)

    st.write(
        f"Identified **{len(outlier_products)}** products generating above-median sales (>{median_sales:,.2f}) but operating at a net loss:"
    )
    st.dataframe(
        outlier_products.style.format(
            {
                "total_sales": "${:,.2f}",
                "total_profit": "${:,.2f}",
                "profit_margin_pct": "{:.2f}%",
            }
        ),
        width='stretch',
    )

# -----------------------------------------------------------------------------
# TAB 3: GEOGRAPHIC & SEGMENT PERFORMANCE
# -----------------------------------------------------------------------------
with tab_geo:
    st.subheader("Regional & Customer Segment Performance")

    region_analysis = (
        filtered_df.groupby("region")
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            orders=("order_id", "nunique"),
        )
        .reset_index()
    )

    r1, r2, r3 = st.columns(3)
    with r1:
        fig_r1 = px.bar(
            region_analysis,
            x="region",
            y="total_sales",
            title="Sales by Region",
            color_discrete_sequence=["lightgreen"],
        )
        st.plotly_chart(fig_r1, width='stretch')

    with r2:
        fig_r2 = px.bar(
            region_analysis,
            x="region",
            y="total_profit",
            title="Profit by Region",
            color_discrete_sequence=["lightblue"],
        )
        st.plotly_chart(fig_r2, width='stretch')

    with r3:
        fig_r3 = px.bar(
            region_analysis,
            x="region",
            y="orders",
            title="Orders by Region",
            color_discrete_sequence=["lightcoral"],
        )
        st.plotly_chart(fig_r3, width='stretch')

    st.markdown("---")
    col_seg1, col_seg2 = st.columns([1, 1])

    with col_seg1:
        st.markdown("### Customer Segment Breakdown")
        segment_analysis = (
            filtered_df.groupby("segment")
            .agg(
                total_sales=("sales", "sum"),
                total_profit=("profit", "sum"),
                customers=("customer_id", "nunique"),
                orders=("order_id", "nunique"),
            )
            .reset_index()
        )

        st.dataframe(
            segment_analysis.style.format(
                {"total_sales": "${:,.2f}", "total_profit": "${:,.2f}"}
            ),
            width='stretch',
        )

    with col_seg2:
        st.markdown("### State-Level Profitability Heatmap")
        state_df = (
            filtered_df.groupby("state")
            .agg(
                total_sales=("sales", "sum"), total_profit=("profit", "sum")
            )
            .reset_index()
        )

        fig_map = px.choropleth(
            state_df,
            locations="state",
            locationmode="USA-states",
            color="total_profit",
            scope="usa",
            hover_data=["total_sales", "total_profit"],
            color_continuous_scale="RdYlGn",
            title="Profitability by US State",
        )
        st.plotly_chart(fig_map, width='stretch')

# -----------------------------------------------------------------------------
# TAB 4: TEMPORAL SALES & PROFIT TRENDS
# -----------------------------------------------------------------------------
with tab_temporal:
    st.subheader("Temporal Trends & Seasonality Analysis")

    monthly_df = (
        filtered_df.groupby("order_year_month")
        .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
        .reset_index()
    )

    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=monthly_df["order_year_month"],
            y=monthly_df["total_sales"],
            mode="lines+markers",
            name="Sales ($)",
            line=dict(color="#1f77b4", width=2),
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=monthly_df["order_year_month"],
            y=monthly_df["total_profit"],
            mode="lines+markers",
            name="Profit ($)",
            line=dict(color="#2ca02c", width=2),
        )
    )

    fig_trend.update_layout(
        title="Monthly Sales and Profit Over Time",
        xaxis_title="Year-Month",
        yaxis_title="Amount ($)",
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, width='stretch')

    # YoY Comparison
    yearly_df = (
        filtered_df.groupby(["order_year", "category"])
        .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
        .reset_index()
    )

    fig_yearly = px.bar(
        yearly_df,
        x="order_year",
        y="total_sales",
        color="category",
        barmode="group",
        title="Annual Revenue Growth by Category",
        labels={"order_year": "Year", "total_sales": "Sales ($)"},
    )
    st.plotly_chart(fig_yearly, width='stretch')

# -----------------------------------------------------------------------------
# TAB 5: DISCOUNT VS PROFITABILITY CORRELATION
# -----------------------------------------------------------------------------
with tab_discount:
    st.subheader("Discount Analysis & Impact on Profitability")

    st.markdown(
        """
    A critical insight discovered during EDA is the strong impact higher discounts have on profit margins. 
    Excessive discounting often leads to deeply negative profit line items.
    """
    )

    col_d1, col_d2 = st.columns([1, 2])

    with col_d1:
        st.markdown("### Discount Rate Distribution")
        discount_dist = (
            filtered_df["discount"]
            .value_counts(normalize=True)
            .sort_index()
            .mul(100)
            .round(2)
            .reset_index()
        )
        discount_dist.columns = ["Discount Rate", "Percentage (%)"]
        st.dataframe(discount_dist, width='stretch')

    with col_d2:
        st.markdown("### Profitability vs Discount Level")
        disc_profit = (
            filtered_df.groupby("discount")
            .agg(
                avg_profit=("profit", "mean"),
                total_profit=("profit", "sum"),
                item_count=("row_id", "count"),
            )
            .reset_index()
        )

        fig_disc = px.bar(
            disc_profit,
            x="discount",
            y="avg_profit",
            title="Average Profit per Item by Discount Rate",
            labels={
                "discount": "Discount Rate (0.1 = 10%)",
                "avg_profit": "Average Profit ($)",
            },
            color="avg_profit",
            color_continuous_scale="RdBu",
        )
        st.plotly_chart(fig_disc, width='stretch')

    st.markdown("### Scatter Plot: Sales vs Profit by Discount")
    fig_scatter = px.scatter(
        filtered_df,
        x="sales",
        y="profit",
        color="discount",
        size="quantity",
        hover_data=["product_name", "category", "sub_category"],
        title="Sales vs Profit colored by Discount Rate",
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig_scatter, width='stretch')

# -----------------------------------------------------------------------------
# TAB 6: RAW DATA & SCHEMA
# -----------------------------------------------------------------------------
with tab_data:
    st.subheader("Database Schema Verification & Raw Tables")

    # Table Row Counts
    row_counts = pd.read_sql_query(
        """
        SELECT 'customers' as table_name, COUNT(*) as rows FROM customers 
        UNION ALL SELECT 'locations', COUNT(*) FROM locations 
        UNION ALL SELECT 'orders', COUNT(*) FROM orders 
        UNION ALL SELECT 'products', COUNT(*) FROM products 
        UNION ALL SELECT 'order_items', COUNT(*) FROM order_items 
        ORDER BY table_name
    """,
        conn,
    )

    st.markdown("### Database Table Summary")
    st.table(row_counts)

    st.markdown("### Filtered Transactional Dataset (`retail_analysis_view`)")
    st.write(f"Displaying {len(filtered_df):,} records:")
    st.dataframe(filtered_df, width='stretch')

    st.download_button(
        label="Download Filtered Data as CSV",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name="superstore_filtered_data.csv",
        mime="text/csv",
    )