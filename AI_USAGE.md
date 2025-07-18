# 🤖 AI_USAGE.md
### Pioneer AI Academy · Data Science Capstone Project

## 📘 Overview

This file documents the use of AI-based models, algorithms, and techniques within the **US Weather + Energy Analysis Pipeline**. It outlines where and how AI/ML is applied to extract insights, along with potential future directions.

---

## ✅ Current Usage of AI/ML

### 1. **Statistical Correlation Analysis**
- **Method:** Pearson Correlation Coefficient
- **Used in:** `analysis.py`
- **Purpose:** Measures the linear relationship between temperature (TMAX/TMIN) and energy usage (`energy_mwh`).
- **Why it matters:** Helps detect how strongly temperature fluctuations drive electricity demand in each city.

### 2. **OLS Regression Trendline**
- **Method:** Ordinary Least Squares Linear Regression
- **Used in:** Streamlit Dashboard (`dashboards/app.py`) with Plotly’s `trendline="ols"`
- **Purpose:** Visualize and interpret the relationship between max temperature and energy usage across cities.
- **Output:** Regression line with R and R² displayed.
- **Dependency:** `statsmodels`

---

## 📈 Future AI Opportunities

This project is built with a modular architecture so advanced ML can be added later:

| AI Task                     | Algorithm/Tool Suggestions         | Goal |
|----------------------------|------------------------------------|------|
| Energy Demand Forecasting  | ARIMA, Prophet, XGBoost, LSTM      | Predict next-day or week’s energy usage |
| Anomaly Detection          | Isolation Forest, Z-score, AutoEncoders | Flag irregular consumption or sensor faults |
| Clustering Cities by Behavior | KMeans, DBSCAN                   | Group cities by similar weather/usage profiles |
| Feature Importance         | SHAP, Permutation Importance       | Understand what factors drive energy use |
| Time Series Segmentation   | Bayesian Change Point Detection    | Identify regime shifts or sudden usage patterns |

---

## 🔐 Ethical Considerations

- Data is sourced from public APIs (NOAA and EIA) and does not contain PII.
- Models and results are interpretable and auditable.
- The system is designed to enhance grid efficiency and environmental stewardship.

---

## 🔧 Key Dependencies for AI Modules

- `scikit-learn`: Regression, correlation, statistical models
- `statsmodels`: OLS regression for trendline analysis in visualizations
- `pandas`, `numpy`: Preprocessing and transformations
- `plotly`: Visualization of correlations and regression outputs

---

## 🧠 Conclusion

This project leverages basic AI tools like regression and correlation analysis to surface valuable relationships in city-level energy data. It is engineered for extensibility, so more sophisticated AI methods can be incorporated easily as part of future iterations.