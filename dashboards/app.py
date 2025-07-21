import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ─── Streamlit Config ───────────────────────────── #
st.set_page_config(page_title="Energy Demand & Quality Dashboard", layout="wide")
st.title("📈 US Energy Demand & Weather Data Quality Dashboard")
st.caption("Tracking electricity trends and data quality across major US cities")
st.markdown(f"🕒 **Last updated:** {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}")

# ─── Load Data ─────────────────────────────────── #
@st.cache_data
def load_data():
    try:
        merged = pd.read_csv("data/processed/merged_data.csv", parse_dates=["date"])
        geo = pd.read_csv("data/processed/geographic_overview.csv")
        heatmap = pd.read_csv("data/processed/heatmap_matrix.csv", index_col=0)
        
        # Load quality reports
        quality_reports = []
        for f in os.listdir("data/processed"):
            if f.endswith("_quality_report.csv"):
                df = pd.read_csv(os.path.join("data/processed", f))
                df["city"] = f.replace("_quality_report.csv", "").replace("_", " ").title()
                quality_reports.append(df)
        
        quality_df = pd.concat(quality_reports, ignore_index=True) if quality_reports else pd.DataFrame()
        return merged, geo, heatmap, quality_df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

merged_df, geo_df, heatmap_matrix, quality_df = load_data()
cities = merged_df["city"].unique().tolist() if not merged_df.empty else []

# ─── Sidebar ──────────────────────────────────── #
st.sidebar.header("🔍 Filter Options")
date_range = st.sidebar.date_input("Date Range", 
    value=[merged_df.date.min(), merged_df.date.max()] if not merged_df.empty else [datetime.today(), datetime.today()],
    min_value=merged_df.date.min() if not merged_df.empty else datetime.today(),
    max_value=merged_df.date.max() if not merged_df.empty else datetime.today()
)

# Visualization mode selection
viz_mode = st.sidebar.radio("Visualization Mode", 
    options=["Overview", "Single City Analysis", "City Comparison"],
    index=0
)

# Filter data based on date range
filtered_df = merged_df[
    (merged_df["date"] >= pd.to_datetime(date_range[0])) &
    (merged_df["date"] <= pd.to_datetime(date_range[1]))
] if not merged_df.empty else pd.DataFrame()

# ─── Overview Page ─────────────────────────────── #
if viz_mode == "Overview":
    st.header("📘 Dashboard Overview")
    
    st.markdown("""
    ## Welcome to the Energy Demand & Weather Dashboard
    
    This dashboard provides insights into:
    - Electricity demand patterns across US cities
    - Relationship between weather and energy consumption
    - Data quality metrics for our datasets
    
    ### How to Use This Dashboard
    
    1. **Select Visualization Mode** in the sidebar:
       - *Overview*: This introduction page
       - *Single City Analysis*: Detailed charts for one city at a time
       - *City Comparison*: Compare metrics between two cities
    
    2. **Adjust Date Range** to focus on specific time periods
    
    ### Chart Explanations
    
    **📉 Time Series Analysis**
    - Shows daily maximum temperature and energy consumption over time
    - Weekend days are shaded gray for easy identification
    - Helps identify seasonal patterns and anomalies
    
    **🔗 Correlation Analysis**
    - Scatter plot showing relationship between temperature and energy use
    - Includes trendline and R² value
    - Positive correlation suggests increased cooling demand in hotter weather
    
    **🔥 Usage Heatmap**
    - Visualizes energy consumption by temperature range and weekday
    - Colors indicate consumption levels (red = higher, blue = lower)
    - Helps identify usage patterns under different weather conditions
    """)
    
    # Display the complete merged data table
    st.header("📊 Complete Energy and Weather Data")
    st.markdown("This table shows all processed data across all cities")
    
    if not merged_df.empty:
        st.dataframe(
            merged_df,
            column_config={
                "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "city": "City",
                "tmax_f": st.column_config.NumberColumn("Max Temp (°F)", format="%.1f"),
                "tmin_f": st.column_config.NumberColumn("Min Temp (°F)", format="%.1f"),
                "energy_mwh": st.column_config.NumberColumn("Energy (MWh)", format=",.0f"),
                "weekday": "Day of Week",
                "month": "Month",
                "day_type": "Day Type"
            },
            use_container_width=True,
            height=600
        )
    else:
        st.warning("No data available to display")

# ─── Single City Analysis ──────────────────────── #
elif viz_mode == "Single City Analysis":
    st.header("📊 Single City Analysis")
    
    if not cities:
        st.warning("No city data available for selected date range")
    else:
        # Geographic Overview
        st.subheader("📍 Current Snapshot")
        geo_city = st.selectbox("Select City for Geographic Overview", cities, key="geo_city")
        city_data = filtered_df[filtered_df["city"] == geo_city]
        
        if city_data.empty:
            st.warning(f"No data available for {geo_city} in selected date range")
        else:
            city_coords = {
                "new_york": {"lat": 40.7128, "lon": -74.0060},
                "chicago": {"lat": 41.8781, "lon": -87.6298},
                "houston": {"lat": 29.7604, "lon": -95.3698},
                "phoenix": {"lat": 33.4484, "lon": -112.0740},
                "seattle": {"lat": 47.6062, "lon": -122.3321}
            }
            
            latest_data = geo_df[geo_df["city"] == geo_city.lower()].iloc[-1] if not geo_df.empty else None
            
            if latest_data is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Max Temperature", f"{latest_data['tmax_f']}°F")
                with col2:
                    st.metric("Energy Demand", f"{latest_data['energy_mwh']:,.0f} MWh")
                with col3:
                    change = latest_data['energy_pct_change']
                    st.metric("Daily Change", f"{change:.1f}%", 
                             delta_color="inverse" if change > 0 else "normal")
                
                # Map visualization
                fig = go.Figure(go.Scattergeo(
                    lon = [city_coords[geo_city.lower()]["lon"]],
                    lat = [city_coords[geo_city.lower()]["lat"]],
                    text = f"{geo_city.title()}<br>Temp: {latest_data['tmax_f']}°F<br>Energy: {latest_data['energy_mwh']:,.0f} MWh",
                    marker = dict(
                        size = 20,
                        color = "red" if latest_data['energy_pct_change'] > 0 else "green",
                        opacity = 0.8
                    )
                ))
                fig.update_layout(
                    geo = dict(
                        scope = 'usa',
                        projection_type = 'albers usa',
                        showland = True,
                        landcolor = "rgb(250, 250, 250)",
                        subunitcolor = "rgb(217, 217, 217)",
                        countrycolor = "rgb(217, 217, 217)",
                        countrywidth = 0.5,
                        subunitwidth = 0.5
                    ),
                    height = 400,
                    margin = {"r":0,"t":0,"l":0,"b":0}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Time Series
        st.subheader("📉 Temperature & Energy Trend")
        ts_city = st.selectbox("Select City for Time Series", cities, key="ts_city")
        ts_data = filtered_df[filtered_df["city"] == ts_city]
        
        if not ts_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ts_data["date"], 
                y=ts_data["tmax_f"], 
                name="Max Temp (°F)",
                line=dict(color='firebrick')
            ))
            fig.add_trace(go.Scatter(
                x=ts_data["date"], 
                y=ts_data["energy_mwh"], 
                name="Energy (MWh)",
                yaxis="y2",
                line=dict(color='navy', dash='dot')
            ))
            
            # Highlight weekends
            for date in ts_data["date"]:
                if date.weekday() >= 5:  # Saturday or Sunday
                    fig.add_vrect(
                        x0=date, x1=date + pd.Timedelta(days=1),
                        fillcolor="lightgray", opacity=0.2,
                        line_width=0
                    )
            
            fig.update_layout(
                yaxis=dict(title="Temperature (°F)"),
                yaxis2=dict(title="Energy (MWh)", overlaying="y", side="right"),
                height=450,
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Correlation
        st.subheader("🔗 Temperature vs. Energy Correlation")
        corr_city = st.selectbox("Select City for Correlation", cities, key="corr_city")
        corr_data = filtered_df[filtered_df["city"] == corr_city]
        
        if not corr_data.empty:
            fig = px.scatter(
                corr_data, 
                x="tmax_f", 
                y="energy_mwh",
                trendline="ols",
                hover_data=["date"],
                labels={"tmax_f": "Max Temperature (°F)", "energy_mwh": "Energy (MWh)"}
            )
            r = corr_data["tmax_f"].corr(corr_data["energy_mwh"])
            fig.add_annotation(
                text=f"R = {r:.2f}, R² = {r**2:.2f}",
                xref="paper", yref="paper",
                x=0.95, y=0.95,
                showarrow=False,
                bgcolor="white"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap
        st.subheader("🔥 Energy Usage Patterns")
        hm_city = st.selectbox("Select City for Heatmap", cities, key="hm_city")
        hm_data = filtered_df[filtered_df["city"] == hm_city]
        
        if not hm_data.empty:
            def temp_band(t):
                if t < 50: return "<50°F"
                elif t < 60: return "50-60°F"
                elif t < 70: return "60-70°F"
                elif t < 80: return "70-80°F"
                elif t < 90: return "80-90°F"
                return ">90°F"
            
            heat_data = hm_data.copy()
            heat_data["weekday"] = heat_data["date"].dt.day_name()
            heat_data["temp_range"] = heat_data["tmax_f"].apply(temp_band)
            
            # Ensure all temperature ranges exist
            temp_ranges = ["<50°F", "50-60°F", "60-70°F", "70-80°F", "80-90°F", ">90°F"]
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            pivot = heat_data.pivot_table(
                index="temp_range",
                columns="weekday",
                values="energy_mwh",
                aggfunc="mean"
            ).reindex(index=temp_ranges, columns=weekdays).fillna(0)
            
            fig = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale="RdBu_r",
                hoverinfo="text",
                text=[["{:.1f} MWh".format(val) for val in row] for row in pivot.values],
                colorbar=dict(title="Avg Energy (MWh)")
            ))
            fig.update_layout(
                height=500,
                xaxis_title="Day of Week",
                yaxis_title="Temperature Range"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Data Quality Metrics
        if not quality_df.empty:
            st.header("🧪 Data Quality Metrics")
            q_city = st.selectbox("Select City for Quality Report", cities, key="quality_city")
            city_quality = quality_df[quality_df["city"] == q_city]
            
            # Create columns for metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                missing = city_quality[city_quality["check"] == "missing_values"]["count"].sum()
                st.metric("Missing Values", missing, 
                         help="Count of null values in critical columns")
            
            with col2:
                outliers = city_quality[city_quality["check"] == "temperature_outliers"]["count"].sum()
                st.metric("Temperature Outliers", outliers,
                         help="Readings outside -50°F to 130°F range")
            
            with col3:
                energy_issues = city_quality[city_quality["check"] == "energy_issues"]["count"].sum()
                st.metric("Energy Data Issues", energy_issues,
                         help="Negative or missing energy values")
            
            with col4:
                freshness = city_quality[city_quality["check"] == "data_freshness"]
                if not freshness.empty:
                    days_old = freshness["count"].values[0]
                    is_fresh = freshness["is_fresh"].values[0]
                    st.metric("Data Freshness", 
                            f"{days_old} days",
                            "Fresh" if is_fresh else "Stale",
                            help="How current the data is (fresh = ≤2 days old)",
                            delta_color="normal")
                else:
                    st.metric("Data Freshness", "N/A")

# ─── City Comparison ───────────────────────────── #
elif viz_mode == "City Comparison":
    st.header("📊 City Comparison")
    
    if len(cities) < 2:
        st.warning("Need at least 2 cities for comparison")
    else:
        col1, col2 = st.columns(2)
        with col1:
            city1 = st.selectbox("Select First City", cities, key="city1")
        with col2:
            city2 = st.selectbox("Select Second City", [c for c in cities if c != city1], key="city2")
        
        compare_data = filtered_df[filtered_df["city"].isin([city1, city2])]
        
        if len(compare_data["city"].unique()) < 2:
            st.warning("Not enough data for selected cities in date range")
        else:
            # Time Series Comparison
            st.subheader("📉 Temperature & Energy Trend Comparison")
            
            fig = go.Figure()
            for city, color in zip([city1, city2], ["#1f77b4", "#ff7f0e"]):
                city_df = compare_data[compare_data["city"] == city]
                fig.add_trace(go.Scatter(
                    x=city_df["date"],
                    y=city_df["tmax_f"],
                    name=f"{city} Temp",
                    line=dict(color=color),
                    yaxis="y1"
                ))
                fig.add_trace(go.Scatter(
                    x=city_df["date"],
                    y=city_df["energy_mwh"],
                    name=f"{city} Energy",
                    line=dict(color=color, dash="dot"),
                    yaxis="y2"
                ))
            
            fig.update_layout(
                yaxis=dict(title="Temperature (°F)"),
                yaxis2=dict(title="Energy (MWh)", overlaying="y", side="right"),
                height=450,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Correlation Comparison
            st.subheader("🔗 Correlation Comparison")
            
            fig = px.scatter(
                compare_data,
                x="tmax_f",
                y="energy_mwh",
                color="city",
                trendline="ols",
                hover_data=["date"],
                labels={"tmax_f": "Max Temperature (°F)", "energy_mwh": "Energy (MWh)"},
                color_discrete_sequence=["#1f77b4", "#ff7f0e"]
            )
            
            # Add R values for each city
            for i, city in enumerate([city1, city2]):
                city_df = compare_data[compare_data["city"] == city]
                r = city_df["tmax_f"].corr(city_df["energy_mwh"])
                fig.add_annotation(
                    text=f"{city}: R = {r:.2f}",
                    xref="paper",
                    yref="paper",
                    x=0.95,
                    y=0.90 - (i * 0.05),
                    showarrow=False,
                    bgcolor="white"
                )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Heatmap Comparison
            st.subheader("🔥 Usage Pattern Comparison")
            
            def temp_band(t):
                if t < 50: return "<50°F"
                elif t < 60: return "50-60°F"
                elif t < 70: return "60-70°F"
                elif t < 80: return "70-80°F"
                elif t < 90: return "80-90°F"
                return ">90°F"
            
            temp_ranges = ["<50°F", "50-60°F", "60-70°F", "70-80°F", "80-90°F", ">90°F"]
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            
            col1, col2 = st.columns(2)
            for i, city in enumerate([city1, city2]):
                with col1 if i == 0 else col2:
                    st.markdown(f"**{city}**")
                    city_data = compare_data[compare_data["city"] == city].copy()
                    city_data["weekday"] = city_data["date"].dt.day_name()
                    city_data["temp_range"] = city_data["tmax_f"].apply(temp_band)
                    
                    pivot = city_data.pivot_table(
                        index="temp_range",
                        columns="weekday",
                        values="energy_mwh",
                        aggfunc="mean"
                    ).reindex(index=temp_ranges, columns=weekdays).fillna(0)
                    
                    fig = go.Figure(go.Heatmap(
                        z=pivot.values,
                        x=pivot.columns,
                        y=pivot.index,
                        colorscale="RdBu_r",
                        hoverinfo="text",
                        text=[["{:.1f} MWh".format(val) for val in row] for row in pivot.values],
                        colorbar=dict(title="Avg Energy (MWh)")
                    ))
                    fig.update_layout(
                        height=500,
                        xaxis_title="Day of Week",
                        yaxis_title="Temperature Range"
                    )
                    st.plotly_chart(fig, use_container_width=True)