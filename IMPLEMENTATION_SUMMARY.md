# Bamboo Pho Dashboard Implementation Summary

## ✅ Completed Features

### 1. Data Preparation
- **Filter Mondays**: Excluded Monday data (zero sales days) from the model
- **Weekend Dummy**: Created `is_weekend` binary variable (1 for Friday-Sunday, 0 otherwise)
- **Precipitation Dummy**: Created `is_precipitation` binary variable (1 for Rain/Snow/Heavy Snow/Mixed, 0 for Clear)
- **Timezone Conversion**: Sales timestamps converted from Pacific to East Coast time

### 2. OLS Regression Model
Built using `statsmodels` to predict Pho bowls sold based on:
- **Temperature** (Temp_High)
- **Weekend** (is_weekend)
- **Precipitation** (is_precipitation)

Model filters out Mondays and zero-sales days for training.

### 3. Tomorrow's Prediction
**Top section with side-by-side columns:**
- **Left column**: Interactive inputs for tomorrow's forecast
  - Temperature input (number slider)
  - Weekend checkbox
  - Precipitation checkbox
  - **Large metric card** showing "Predicted Bowls for Tomorrow"

- **Right column**: Current stats (3 sub-columns)
  - Average daily bowls
  - Total January bowls
  - Weekend lift coefficient
  - Precipitation impact coefficient
  - Temperature effect per °F
  - Model R² score

### 4. Loyalty Tracker
**Top 10 Regulars table** showing:
- Customer Name
- Total Visits (unique transactions)
- Total Spend
- Sorted by most visits, then by spend

### 5. Visualizations
- **Line chart**: Pho bowls sold vs daily high temperature (dual y-axis)
- **Scatter plot**: Temperature vs bowls with regression lines for weekends and midweek

### 6. UI Layout
- Uses `st.columns()` for side-by-side layouts
- Clean sectioned dashboard with dividers
- Metric cards for key statistics
- Interactive inputs for predictions

## How to Run
```bash
cd /Users/quoctran/Documents/moms-dashboard
source .venv/bin/activate
streamlit run app.py
```

## Model Coefficients (Expected)
Based on the January 2026 data:
- **Intercept**: Baseline bowls for midweek, clear day
- **Temp Effect**: Positive correlation with temperature
- **Weekend Lift**: Significant increase on Fri-Sun
- **Precipitation Impact**: Effect of rain/snow on sales
- **R² Score**: Model fit quality

## Data Sources
- `Jan_2026_Bamboo_Data.csv`: Sales transactions
- `jan_weather.csv`: Daily temperature and precipitation data
