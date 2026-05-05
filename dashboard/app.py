import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# ----------------------------
# PAGE CONFIG (must be first)
# ----------------------------
st.set_page_config(page_title="Real Estate Dashboard", layout="wide")

# ----------------------------
# DB CONNECTION
# ----------------------------
DB_URL = "postgresql+psycopg2://airflow:airflow@127.0.0.1:5432/real_estate_db"
engine = create_engine(DB_URL)

# ----------------------------
# LOAD DATA
# ----------------------------
@st.cache_data
def load_data():
    try:
        query = "SELECT * FROM transformed_properties"
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

# ----------------------------
# LOAD DATA BEFORE USING IT
# ----------------------------
df = load_data()

# Safety check
if df.empty:
    st.error("No data found or database connection failed.")
    st.stop()

# ----------------------------
# MAIN TITLE
# ----------------------------
st.title("🏠 Real Estate Analytics Dashboard")

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filters")

locations = st.sidebar.multiselect(
    "Select Location",
    options=df['location'].dropna().unique(),
    default=df['location'].dropna().unique()
)

price_range = st.sidebar.slider(
    "Price Range",
    int(df['price'].min()),
    int(df['price'].max()),
    (int(df['price'].min()), int(df['price'].max()))
)

# ----------------------------
# FILTER DATA
# ----------------------------
filtered_df = df[
    (df['location'].isin(locations)) &
    (df['price'] >= price_range[0]) &
    (df['price'] <= price_range[1])
]

# ----------------------------
# KPIs
# ----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Properties", len(filtered_df))
col2.metric("Avg Price", f"₹ {int(filtered_df['price'].mean()):,}")
col3.metric("Avg Price/Sqft", f"₹ {int(filtered_df['price_per_sqft'].mean()):,}")

# ----------------------------
# CHARTS
# ----------------------------
st.subheader("📊 Price by Location")
price_by_location = filtered_df.groupby("location")["price"].mean().sort_values()
st.bar_chart(price_by_location)

st.subheader("📈 Price Distribution")
st.line_chart(filtered_df["price"].sort_values())

st.subheader("🏙 Top Locations")
top_locations = (
    filtered_df.groupby("location")["price"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
)
st.bar_chart(top_locations)

# ----------------------------
# DATA TABLE
# ----------------------------
st.subheader("📋 View Data")
st.dataframe(filtered_df)

# ----------------------------
# DOWNLOAD OPTION
# ----------------------------
st.download_button(
    "Download Data as CSV",
    filtered_df.to_csv(index=False),
    "real_estate_data.csv",
    "text/csv"
)