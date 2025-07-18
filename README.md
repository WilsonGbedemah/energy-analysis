# 🛰️ Project 1: US Weather + Energy Analysis Pipeline

### 📚 Pioneer AI Academy · Data Science Capstone

---

## 🚀 Overview

This project builds a **production-ready data pipeline** that combines **daily weather** and **electricity usage data** across 5 major US cities. The insights help **energy utilities**, **planners**, and **analysts** to forecast demand, reduce waste, and make informed data-driven decisions.

---

## 📍 Cities and Regions

| City     | State      | NOAA Station ID      | EIA Region Code |
|----------|------------|----------------------|------------------|
| New York | New York   | GHCND:USW00094728    | NYIS             |
| Chicago  | Illinois   | GHCND:USW00094846    | PJM              |
| Houston  | Texas      | GHCND:USW00012960    | ERCO             |
| Phoenix  | Arizona    | GHCND:USW00023183    | AZPS             |
| Seattle  | Washington | GHCND:USW00024233    | SCL              |

---

## 🧱 Project Structure

```
energy-analysis/
├── dashboards/
│   └── app.py                ← Streamlit dashboard
├── data/
│   ├── raw/                  ← Raw data from APIs
│   └── processed/            ← Cleaned, validated, and analyzed data
├── logs/                     ← Log files for pipeline steps
├── src/
│   ├── data_fetcher.py       ← Weather & energy data collection
│   ├── data_processor.py     ← Cleaning + quality checks
│   ├── analysis.py           ← Data aggregation + insights
│   └── pipeline.py           ← Full ETL runner
├── tests/                    ← Pytest-based unit tests
├── Makefile                  ← Workflow automation
├── .env                      ← Stores API keys (not versioned)
├── README.md                 ← 📘 This file
└── AI_USAGE.md               ← AI assistant audit (ChatGPT & Copilot)
```

---

## ⚙️ Pipeline Stages

### 1. 🔍 Data Fetching
- Uses NOAA and EIA APIs
- Pulls 90 days of:
  - Temperature (Max & Min)
  - Electricity Demand (daily)
- Automatically retries failed requests
- Output: `data/raw/`

### 2. 🧼 Data Processing
- Merges weather + energy data
- Performs **4 quality checks**:
  - Missing values
  - Temperature outliers (over 130°F / under -50°F)
  - Negative or missing energy demand
  - Data freshness (within 2 days)
- Logs issues to `logs/`
- Output: cleaned CSVs + `*_quality_report.csv`

### 3. 📊 Analysis & Insights
- Combines all city data into `merged_data.csv`
- Produces:
  - Correlation matrix
  - Seasonal patterns (monthly)
  - Weekday vs weekend usage
  - Heatmap matrix
  - Geographic summary

### 4. 🌐 Streamlit Dashboard
```bash
make run-dashboard
```

Visualizations:
1. **📍 US Map View**  
   - Shows current energy + temperature
   - % change from previous day
   - Color-coded by energy change

2. **📈 Time Series**  
   - 90-day chart: Max temperature (solid) vs Energy (dotted)
   - Weekends shaded
   - City selector dropdown

3. **🔬 Correlation Analysis**  
   - Temperature vs energy scatter plot
   - Trendline (regression) with R² and R
   - Hover shows date and values

4. **🔥 Heatmap by Temp & Weekday**  
   - Temp range on Y-axis
   - Weekday on X-axis
   - Color scale: low (blue) to high (red)

---

## ✅ How to Use

### Step 1: Install environment & dependencies
```bash
make install
```

### Step 2: Add your API keys
Create a `.env` file:
```dotenv
NOAA_API_KEY=your_noaa_token
EIA_API_KEY=your_eia_token
```

### Step 3: Run the full ETL pipeline
```bash
make pipeline
```

### Step 4: View results
```bash
make run-dashboard
```

---

## 📁 Output Files

| Path                                      | Description                                  |
|-------------------------------------------|----------------------------------------------|
| `data/raw/*.csv`                          | Raw NOAA and EIA data                        |
| `data/processed/*_cleaned.csv`            | Cleaned and merged per-city data             |
| `data/processed/merged_data.csv`          | All-city data for dashboard and insights     |
| `data/processed/*_quality_report.csv`     | Summary of missing, outliers, and freshness  |
| `data/processed/correlation_matrix.csv`   | Pairwise correlations (Temp vs Energy)       |
| `data/processed/geographic_overview.csv`  | Latest energy usage + % change               |
| `data/processed/heatmap_matrix.csv`       | Heatmap-ready usage matrix                   |

---

## 🧪 Testing

To run unit tests:

```bash
make test
```

Covers:
- Data fetching
- Data validation
- Analysis calculations
- Full ETL orchestration

---

## 🤖 AI Usage Summary

See [`AI_USAGE.md`](./AI_USAGE.md) for:

- Prompts used
- Specific AI contributions (ChatGPT / GitHub Copilot)
- Manual edits vs AI completions
- Impact on productivity and bug detection

---

## 💡 Insights Gained

- Energy usage increases as temperatures rise, especially >80°F
- Weekday demand consistently higher than weekends
- Seasonal patterns vary: colder cities peak in winter; hotter cities in summer
- R-squared values confirm **moderate to strong correlation** in most regions

---

## 🛠️ Tools Used

- Python 3.13+
- Streamlit
- Plotly
- Pandas, NumPy
- Scikit-learn
- NOAA / EIA APIs
- Pytest
- Makefile automation
- `uv` for dependency management

---

## 👤 Author & Attribution

**Project**: Pioneer AI Academy — Data Science Project 1  
**Maintainer**: Felix Wilson Gbedemah  
**Contact**: afrogbede09@gmail.com  
**License**: Apache License

---

## 🧠 Future Improvements

- Add ML model to forecast next-day demand
- Add error monitoring with Slack/email notifications
- Expand to all US states using FIPS codes
- Cache API responses to reduce load and retries

---
