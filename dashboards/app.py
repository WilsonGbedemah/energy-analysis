import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ─── Streamlit Config ───────────────────────────── #
st.set_page_config(page_title="Energy Demand Dashboard", layout="wide")
st.title("📈 US Energy Demand & Weather Dashboard")
st.caption("Tracking electricity trends and data quality across major US cities")
st.markdown(f"🕒 Last updated: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')}")

# ─── Load Data ─────────────────────────────────── #
@st.cache_data
def load_data():
    try:
        merged = pd.read_csv("data/processed/merged_data.csv", parse_dates=["date"])
        geo = pd.read_csv("data/processed/geographic_overview.csv")
        heatmap = pd.read_csv("data/processed/heatmap_matrix.csv", index_col=0)
        
        quality_reports = []
        for f in os.listdir("data/processed"):
            if f.endswith("_quality_report.csv"):
                df = pd.read_csv(os.path.join("data/processed", f))
                df["city"] = f.replace("_quality_report.csv", "").replace("_", " ").title()
                quality_reports.append(df)
        
        quality_df = pd.concat(quality_reports, ignore_index=True) if quality_reports else pd.DataFrame()
        return merged, geo, heatmap, quality_df
    except Exception as e:
        st.error(f"Data loading error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

merged_df, geo_df, heatmap_matrix, quality_df = load_data()
cities = merged_df["city"].unique().tolist() if not merged_df.empty else []

# ─── Sidebar ──────────────────────────────────── #
st.sidebar.header("🔍 Filter Options")

if not merged_df.empty:
    min_date = merged_df.date.min()
    max_date = merged_df.date.max()
    default_end = max_date
    default_start = max(min_date, max_date - pd.Timedelta(days=90))
else:
    min_date = datetime.today() - pd.Timedelta(days=365)
    max_date = datetime.today()
    default_end = max_date
    default_start = max_date - pd.Timedelta(days=90)

date_range = st.sidebar.date_input(
    "Date Range",
    value=[default_start.date(), default_end.date()],
    min_value=min_date.date(),
    max_value=max_date.date()
)

viz_mode = st.sidebar.radio("View Mode", ["Overview", "City Analysis"])

filtered_df = merged_df[
    (merged_df["date"] >= pd.to_datetime(date_range[0])) &
    (merged_df["date"] <= pd.to_datetime(date_range[1]))
] if not merged_df.empty else pd.DataFrame()

# ─── Overview Page ─────────────────────────────── #
if viz_mode == "Overview":
    st.header("📘 Dashboard Overview")
    
    # Introduction Section
    with st.expander("📌 Dashboard Guide", expanded=True):
        st.markdown("""
        ### Welcome to the Energy Demand Dashboard
        
        **Purpose**: Track electricity demand patterns across US cities and their relationship with weather data.
        
        **Key Features**:
        - 🏙️ **City Analysis**: Detailed energy and temperature trends for individual cities
        - 📅 **Temporal Patterns**: Daily, weekly, and seasonal demand variations
        - 🔗 **Correlation Analysis**: Relationship between temperature and energy demand
        - 🧪 **Data Quality**: Monitoring of missing values and anomalies
        
        **How to Use**:
        1. Select **City Analysis** in the sidebar to view specific city data
        2. Adjust the date range to focus on specific periods
        3. Explore the visualizations to understand patterns
        4. Check data quality metrics for reliability assessment
        """)
    
    # Key Metrics Section
    st.subheader("🔍 Quick Insights")
    if not merged_df.empty:
        # Calculate basic statistics
        total_days = (max_date - min_date).days
        total_energy = merged_df['energy_mwh'].sum()
        avg_daily = merged_df['energy_mwh'].mean()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Cities Tracked", len(cities))
        col2.metric("Total Days Analyzed", f"{total_days} days")
        col3.metric("Total Energy Recorded", f"{total_energy:,.0f} MWh")
        
        # Top/Bottom Cities Table
        st.subheader("🏆 Top Performing Cities")
        city_stats = merged_df.groupby('city').agg({
            'energy_mwh': ['mean', 'max', 'min'],
            'tmax_f': 'mean'
        }).sort_values(('energy_mwh', 'mean'), ascending=False)
        
        # Format column names
        city_stats.columns = [' '.join(col).strip() for col in city_stats.columns.values]
        st.dataframe(
            city_stats.head(5).style.format({
                'energy_mwh mean': '{:,.0f}',
                'energy_mwh max': '{:,.0f}',
                'energy_mwh min': '{:,.0f}',
                'tmax_f mean': '{:.1f}'
            }),
            use_container_width=True,
            height=210
        )
    
    # Data Summary Section
    st.subheader("📊 Data Summary")
    if not merged_df.empty:
        tab1, tab2 = st.tabs(["Sample Data", "Statistics"])
        
        with tab1:
            st.write("First 5 records of the dataset:")
            st.dataframe(
                merged_df.head(),
                column_config={
                    "date": st.column_config.DateColumn("Date"),
                    "tmax_f": st.column_config.NumberColumn("Max Temp (°F)"),
                    "energy_mwh": st.column_config.NumberColumn("Energy (MWh)")
                },
                use_container_width=True
            )
        
        with tab2:
            st.write("Descriptive statistics:")
            stats_df = merged_df[['tmax_f', 'energy_mwh']].describe()
            st.dataframe(
                stats_df.style.format('{:,.1f}'),
                use_container_width=True,
                height=350
            )
    
    # Data Quality Overview
    if not quality_df.empty:
        st.subheader("🧐 Data Quality Check")
        
        # Aggregate quality metrics
        quality_summary = quality_df.groupby('check')['count'].sum().reset_index()
        quality_summary.columns = ['Issue Type', 'Count']
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("Total Issues by Type:")
            st.dataframe(
                quality_summary,
                use_container_width=True,
                height=200
            )
        
        with col2:
            st.write("Most Recent Data Points:")
            latest_dates = merged_df.groupby('city')['date'].max().reset_index()
            st.dataframe(
                latest_dates.sort_values('date', ascending=False),
                column_config={
                    "date": st.column_config.DateColumn("Last Record")
                },
                use_container_width=True,
                height=200
            )
    
    # Quick Start Guide
    st.subheader("🚀 Quick Start Tips")
    st.markdown("""
    - **For trend analysis**: Go to City Analysis view and select a city
    - **For correlations**: Look at the scatter plots in City Analysis
    - **For data quality**: Check the quality metrics in both views
    - **To focus on specific periods**: Adjust the date range in the sidebar
    
    ℹ️ Hover over charts for detailed values and click legend items to toggle visibility.
    """)

# ─── City Analysis Page ────────────────────────── #
else:
    st.header("🏙️ City Energy Analysis")
    
    if not cities:
        st.warning("No city data available")
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
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=city_data["date"], y=city_data["tmax_f"], 
                name="Temperature", line=dict(color='firebrick')))
            fig.add_trace(go.Scatter(
                x=city_data["date"], y=city_data["energy_mwh"], 
                name="Energy", yaxis="y2", line=dict(color='navy')))
            fig.update_layout(
                yaxis=dict(title="Temperature (°F)"),
                yaxis2=dict(title="Energy (MWh)", overlaying="y", side="right"),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Correlation
            st.subheader("🔗 Temperature vs Energy Correlation")
            fig = px.scatter(
                city_data, x="tmax_f", y="energy_mwh",
                trendline="ols", hover_data=["date"],
                labels={"tmax_f": "Max Temperature (°F)", "energy_mwh": "Energy Demand (MWh)"}
            )
            r = city_data["tmax_f"].corr(city_data["energy_mwh"])
            fig.add_annotation(
                text=f"R = {r:.2f}, R² = {r**2:.2f}",
                x=0.95, y=0.95, xref="paper", yref="paper",
                showarrow=False, bgcolor="white"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Energy Usage Patterns
            st.subheader("🔥 Energy Usage Patterns")
            
            # Temperature distribution check
            st.caption("Temperature Distribution")
            temp_dist = px.histogram(city_data, x="tmax_f", nbins=15,
                                   labels={"tmax_f": "Max Temperature (°F)"})
            st.plotly_chart(temp_dist, use_container_width=True)
            
            # Heatmap with dynamic bands
            def temp_band(t):
                if t < 30: return "<30°F"
                elif t < 40: return "30-40°F" 
                elif t < 50: return "40-50°F"
                elif t < 60: return "50-60°F"
                elif t < 70: return "60-70°F"
                elif t < 80: return "70-80°F"
                elif t < 90: return "80-90°F"
                else: return ">90°F"
            
            heat_data = city_data.copy()
            heat_data["weekday"] = heat_data["date"].dt.day_name()
            heat_data["temp_range"] = heat_data["tmax_f"].apply(temp_band)
            
            temp_ranges = ["<30°F", "30-40°F", "40-50°F", "50-60°F", 
                         "60-70°F", "70-80°F", "80-90°F", ">90°F"]
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday",
                       "Friday", "Saturday", "Sunday"]
            
            pivot = heat_data.pivot_table(
                index="temp_range",
                columns="weekday",
                values="energy_mwh",
                aggfunc="mean"
            ).reindex(index=temp_ranges, columns=weekdays)
            
            fig = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale="RdBu_r",
                hoverinfo="text",
                text=[["{:.1f} MWh".format(val) if not pd.isna(val) else "No data" 
                      for val in row] for row in pivot.values],
                colorbar=dict(title="Avg Energy (MWh)")
            ))
            fig.update_layout(
                height=600,
                xaxis_title="Day of Week",
                yaxis_title="Temperature Range (°F)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
                        # Data Quality
            if not quality_df.empty:
                st.subheader("🧪 Data Quality")
                city_quality = quality_df[quality_df["city"] == geo_city]
                cols = st.columns(4)
                metrics = [
                    ("Missing Values", "missing_values"),
                    ("Temp Outliers", "temperature_outliers"),
                    ("Energy Issues", "energy_issues"),
                    ("Data Freshness", "data_freshness")
                ]
                for col, (name, check) in zip(cols, metrics):
                    with col:
                        val = city_quality[city_quality["check"] == check]["count"].sum()
                        st.metric(name, val)