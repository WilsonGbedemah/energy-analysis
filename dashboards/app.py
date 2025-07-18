import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from sklearn.linear_model import LinearRegression

# Streamlit Config
st.set_page_config(page_title="US Weather + Energy Dashboard", layout="wide")
st.title("⚡ US Weather + Energy Usage Dashboard")
st.caption("Explore 90-day weather and electricity trends for 5 major US cities.")

# ─── Load Data ───────────────────────────────────────────── #
@st.cache_data
def load_data():
    merged = pd.read_csv("data/processed/merged_data.csv", parse_dates=["date"])
    geo = pd.read_csv("data/processed/geographic_overview.csv")
    heatmap = pd.read_csv("data/processed/heatmap_matrix.csv", index_col=0)
    return merged, geo, heatmap

merged_df, geo_df, heatmap_matrix = load_data()

cities = merged_df["city"].unique().tolist()

# ─── Sidebar Filters ─────────────────────────────────────── #
st.sidebar.header("🔍 Filter Options")
selected_cities = st.sidebar.multiselect("Select cities", options=cities, default=cities)
date_range = st.sidebar.date_input("Date range", [merged_df.date.min(), merged_df.date.max()])

# Apply filters
filtered = merged_df[
    (merged_df["city"].isin(selected_cities)) &
    (merged_df["date"] >= pd.to_datetime(date_range[0])) &
    (merged_df["date"] <= pd.to_datetime(date_range[1]))
]

# ─── 1. Geographic Overview ──────────────────────────────── #
st.header("1️⃣ Geographic Overview")
st.caption(f"🗓️ Data last updated: {geo_df['date'].max()}")

geo_data = geo_df.copy()
geo_data["energy_color"] = np.where(geo_data["energy_pct_change"] > 0, "red", "green")

# Hard-coded lat/lon (for 5 cities)
city_coords = {
    "new_york": {"lat": 40.7128, "lon": -74.0060},
    "chicago": {"lat": 41.8781, "lon": -87.6298},
    "houston": {"lat": 29.7604, "lon": -95.3698},
    "phoenix": {"lat": 33.4484, "lon": -112.0740},
    "seattle": {"lat": 47.6062, "lon": -122.3321}
}

map_fig = go.Figure()
for _, row in geo_data.iterrows():
    city = row["city"]
    lat, lon = city_coords[city]["lat"], city_coords[city]["lon"]
    hover_text = f"{city.title()}<br>Temp: {row.tmax_f}°F<br>Energy: {int(row.energy_mwh)} MWh<br>Change: {row.energy_pct_change:.1f}%"
    map_fig.add_trace(go.Scattergeo(
        lon=[lon], lat=[lat],
        text=hover_text,
        marker=dict(size=15, color=row.energy_color),
        name=city.title()
    ))
map_fig.update_layout(
    geo=dict(scope="usa", projection_type="albers usa"),
    title="📍 Current Energy + Temperature Snapshot",
    height=450
)
st.plotly_chart(map_fig, use_container_width=True)

# ─── 2. Time Series Analysis ─────────────────────────────── #
st.header("2️⃣ Temperature vs Energy Time Series")

city_option = st.selectbox("Select a city", ["All Cities"] + cities)
ts_df = filtered if city_option == "All Cities" else filtered[filtered.city == city_option]

fig = go.Figure()
fig.add_trace(go.Scatter(x=ts_df.date, y=ts_df.tmax_f, name="Max Temp (°F)", yaxis="y1"))
fig.add_trace(go.Scatter(x=ts_df.date, y=ts_df.energy_mwh, name="Energy Usage (MWh)", yaxis="y2", line=dict(dash="dot")))

# Highlight weekends
for date in ts_df.date:
    if date.weekday() >= 5:
        fig.add_vrect(x0=date, x1=date + pd.Timedelta(days=1), fillcolor="lightgrey", opacity=0.2, line_width=0)

fig.update_layout(
    title="Temperature and Energy Usage Over Time",
    xaxis_title="Date",
    yaxis=dict(title="Temperature (°F)"),
    yaxis2=dict(title="Energy (MWh)", overlaying="y", side="right"),
    height=450
)
st.plotly_chart(fig, use_container_width=True)

# ─── 3. Correlation Analysis ─────────────────────────────── #
st.header("3️⃣ Temperature vs Energy Correlation")

scatter_df = merged_df[merged_df.city.isin(selected_cities)]
fig = px.scatter(
    scatter_df, x="tmax_f", y="energy_mwh", color="city", trendline="ols",
    hover_data=["date"], title="Temperature vs Energy Consumption"
)

# Compute correlation
r = scatter_df["tmax_f"].corr(scatter_df["energy_mwh"])
r2 = r ** 2
fig.add_annotation(
    text=f"R = {r:.2f}, R² = {r2:.2f}",
    xref="paper", yref="paper",
    x=0.95, y=0.95, showarrow=False
)
st.plotly_chart(fig, use_container_width=True)

# ─── 4. Usage Patterns Heatmap ───────────────────────────── #
st.header("4️⃣ Energy Usage by Temperature & Weekday")

hm_city = st.selectbox("Select city for heatmap", cities)
city_df = merged_df[merged_df.city == hm_city].copy()
city_df["weekday"] = city_df.date.dt.day_name()

def temp_band(t):
    if t < 50: return "<50°F"
    elif t < 60: return "50-60°F"
    elif t < 70: return "60-70°F"
    elif t < 80: return "70-80°F"
    elif t < 90: return "80-90°F"
    return ">90°F"

city_df["temp_range"] = city_df["tmax_f"].apply(temp_band)
pivot = city_df.pivot_table(
    index="temp_range", columns="weekday", values="energy_mwh", aggfunc="mean"
).fillna(0).reindex([
    "<50°F", "50-60°F", "60-70°F", "70-80°F", "80-90°F", ">90°F"
])

fig = go.Figure(data=go.Heatmap(
    z=pivot.values,
    x=pivot.columns,
    y=pivot.index,
    text=np.round(pivot.values, 1).astype(str),
    hoverinfo="text",
    colorscale="RdBu_r",
    colorbar_title="Avg MWh"
))
fig.update_layout(
    title=f"Avg Energy Usage by Temperature and Day ({hm_city.title()})",
    height=450
)
st.plotly_chart(fig, use_container_width=True)
