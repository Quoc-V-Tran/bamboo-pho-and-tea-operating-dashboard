# 🚀 Quick Start Guide

## Run the Dashboard

```bash
cd /Users/quoctran/Documents/moms-dashboard
source .venv/bin/activate
streamlit run app.py
```

Dashboard opens at: `http://localhost:8501`

---

## What's Implemented ✅

### 1. Data Preparation
- ✅ **Filter Mondays** - Excluded from model (zero sales)
- ✅ **Weekend Dummy** - Binary variable for Fri-Sun
- ✅ **Precipitation Dummy** - Binary for Rain/Snow/Mixed vs Clear
- ✅ **Timezone Conversion** - Pacific → East Coast time

### 2. OLS Regression Model
- ✅ **Statsmodels OLS** - Predicts bowls based on:
  - Temperature (Temp_High)
  - Weekend (is_weekend)
  - Precipitation (is_precipitation)

### 3. Tomorrow's Prediction
- ✅ **Interactive Inputs** - Temperature, Weekend, Precipitation
- ✅ **Large Metric Card** - "Predicted Bowls for Tomorrow"
- ✅ **Side-by-side Layout** - Prediction + Stats using `st.columns()`

### 4. Current Stats (Right Column)
- ✅ **6 Metric Cards** in 3 columns:
  - Average daily bowls
  - Total January bowls
  - Weekend lift coefficient
  - Precipitation impact
  - Temperature effect per °F
  - Model R² score

### 5. Loyalty Tracker
- ✅ **Top 10 Regulars Table**
  - Customer name
  - Total visits (unique transactions)
  - Total spend
  - Sorted by visits → spend

### 6. Visualizations
- ✅ **Line Chart** - Bowls sold vs temperature over time
- ✅ **Scatter Plot** - Temperature vs bowls with regression lines

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────┐
│         🍜 Bamboo Pho Operations Dashboard       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│           📅 Tomorrow's Forecast                 │
├──────────────────┬──────────────────────────────┤
│ Enter Forecast   │  📊 January Stats (6 metrics)│
│ • Temp           │  ┌─────┬─────┬─────┐        │
│ • Weekend □      │  │ Avg │ Week│ Temp│        │
│ • Precip □       │  │ Bowl│ Lift│ Eff │        │
│                  │  ├─────┼─────┼─────┤        │
│ 🔮 Predicted:    │  │ Tot │ Prec│ R²  │        │
│    XX Bowls     │  │ Bowl│ Imp │     │        │
│                  │  └─────┴─────┴─────┘        │
└──────────────────┴──────────────────────────────┘

────────────────────────────────────────────────────

📈 Line Chart: Bowls vs Temperature (time series)

────────────────────────────────────────────────────

🌡️ Scatter Plot: Temp vs Bowls (with regression)

────────────────────────────────────────────────────

👥 Top 10 Regulars Table
```

---

## Key Model Insights

After running, you'll see coefficients like:

- **Intercept**: ~40 bowls (midweek baseline)
- **Temperature**: +0.3 to +0.5 bowls per °F
- **Weekend Lift**: +15 to +20 bowls
- **Precipitation**: -5 to +5 bowls (varies)
- **R²**: ~0.6-0.8 (model fit)

---

## Example Usage

### Scenario: Predict Thursday's Sales

**Forecast:**
- Temperature: 42°F
- Day: Thursday (not weekend)
- Weather: Rain expected

**Inputs:**
1. Enter `42` for temperature
2. Leave "Weekend Day" unchecked
3. Check "Precipitation Expected"

**Result:**
Dashboard shows: "🔮 Predicted Bowls for Tomorrow: 52 Bowls"

---

## Files Structure

```
📁 moms-dashboard/
├── 📄 app.py                    ← Main dashboard
├── 📊 Jan_2026_Bamboo_Data.csv  ← Sales data
├── 🌤️ jan_weather.csv           ← Weather data
├── 📖 README.md                 ← Full documentation
├── 📋 IMPLEMENTATION_SUMMARY.md ← Technical details
├── 🎨 DASHBOARD_LAYOUT.md       ← UI diagram
└── 🚀 QUICK_START.md            ← This file
```

---

## Troubleshooting

**Dashboard won't start?**
```bash
pip install streamlit pandas plotly statsmodels pytz
```

**Import errors?**
```bash
source .venv/bin/activate  # Make sure venv is active
```

**Data not loading?**
- Check CSV files are in same folder as app.py
- Verify file names match exactly

---

## Next Steps

1. **Run the dashboard** (command at top)
2. **Enter tomorrow's forecast** in the top-left section
3. **Review stats** in the top-right section
4. **Analyze trends** using the charts
5. **Check top customers** in the table

---

## Support Docs

- `README.md` - Full documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation
- `DASHBOARD_LAYOUT.md` - Visual layout guide

---

**Ready to go! 🎉**

Just run: `streamlit run app.py`
