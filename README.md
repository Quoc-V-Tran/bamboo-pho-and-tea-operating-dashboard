# 🍜 Bamboo Pho Operations Dashboard

A Streamlit dashboard for predicting daily pho bowl sales based on weather conditions and weekend patterns.

## Features

### ✨ Key Capabilities

1. **Tomorrow's Prediction**
   - Enter tomorrow's weather forecast
   - Get instant prediction for bowls sold
   - Based on OLS regression model

2. **Data-Driven Insights**
   - Weekend vs Midweek performance
   - Weather impact on sales
   - Temperature correlation analysis

3. **Loyalty Tracking**
   - Top 10 regular customers
   - Visit frequency and spending patterns

4. **Interactive Visualizations**
   - Time series: Bowls sold vs temperature
   - Scatter plot with regression lines
   - Color-coded weather conditions

## Quick Start

### Prerequisites
- Python 3.9+
- Virtual environment with required packages

### Installation & Running

```bash
# Navigate to project directory
cd /Users/quoctran/Documents/moms-dashboard

# Activate virtual environment
source .venv/bin/activate

# Run the dashboard
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Data Files

### Required Files
- `2025_Bamboo_Data.csv` - Sales transaction data for 2025 from Square POS
- `Jan_2026_Bamboo_Data.csv` - Sales transaction data for January 2026 from Square POS
- `camp_hill_2025_weather.csv` - Daily weather data for 2025 (temperature and precipitation)
- `jan_weather.csv` - Daily weather data for January 2026 (temperature and precipitation)

### Data Structure

**Sales Data Columns:**
- Date, Time, Time Zone
- Item, Qty, Gross Sales
- Customer Name, Transaction ID
- (Full schema in CSV)

**Weather Data Columns:**
- Date
- Temp_High (°F)
- Precip_Type (None/Clear/Rain/Snow/Mixed/Flurries/Heavy Snow)

## Model Details

### OLS Regression with Interaction Term
The dashboard uses Ordinary Least Squares regression to predict pho bowl sales:

**Model Equation:**
```
Bowls_Sold = β₀ + β₁(Temp_High) + β₂(is_precipitation) + 
             β₃(is_precipitation × Temp_High) + β₄(is_weekend)
```

**Independent Variables:**
- `Temp_High` - Daily high temperature in Fahrenheit
- `is_weekend` - Binary (1 for Fri-Sun, 0 for Tue-Thu)
- `is_precipitation` - Binary (1 for any precipitation, 0 for clear)
- `precip_temp_interaction` - Interaction term (is_precipitation × Temp_High)

**Dependent Variable:**
- `Bowls_Sold` - Total pho bowls sold per day

**Key Feature - Interaction Term:**
The interaction term captures how precipitation's effect on sales changes with temperature. For example, rain/snow might boost comfort food sales more when it's cold versus when it's warm.

**Data Filtering:**
- Mondays excluded (restaurant closed)
- Zero-sales days excluded
- East Coast timezone (converted from Pacific)

### Model Training
- Training set: Full year 2025 + January 2026 data
- All pho items aggregated by date
- Coefficients show:
  - Base temperature effect (on clear days)
  - Precipitation main effect
  - How precipitation's impact varies with temperature
  - Weekend sales lift
  
### Regression Lines
The scatter plot displays **4 regression lines**:
1. **Weekend + Clear** (Gold solid) - Friday-Sunday with no precipitation
2. **Midweek + Clear** (Gold dashed) - Tuesday-Thursday with no precipitation
3. **Weekend + Precipitation** (Blue solid) - Friday-Sunday with rain/snow
4. **Midweek + Precipitation** (Blue dashed) - Tuesday-Thursday with rain/snow

## Using the Dashboard

### 1. Predict Tomorrow's Sales

**Input Section (Top-Left):**
1. Enter tomorrow's forecasted temperature
2. Check "Weekend Day" if it's Friday, Saturday, or Sunday
3. Check "Precipitation Expected" if rain/snow is forecast
4. View the prediction instantly (includes automatic interaction calculation)

**Stats Section (Top-Right):**
- Review historical performance metrics (2025 + 2026)
- Compare model coefficients
- Check model quality (R²)
- See weekend lift and precipitation impact

### 2. Analyze Trends

**Time Series Chart:**
- Green line: Bowls sold
- Red line: Daily temperature
- Hover for details on specific dates

**Scatter Plot:**
- Each point: One day of sales
- Color: Weather condition
- Gold line: Weekend trend
- Gray dashed: Midweek trend

### 3. Review Top Customers

**Loyalty Table:**
- Customers sorted by visit frequency
- Shows total spend
- Helps identify VIP customers

## Customization

### Adjusting the Model

To modify model parameters, edit `app.py`:

```python
# Line 52-55: Model definition
X = model_df[['Temp_High', 'is_weekend', 'is_precipitation']]
X = sm.add_constant(X) 
y = model_df['Bowls_Sold']
ols_model = sm.OLS(y, X).fit()
```

### Adding Variables

To include additional predictors:
1. Add new column to `merged` dataframe
2. Include in `X` variable list
3. Update prediction formula

### Filtering Data

Modify line 47 to change filtering criteria:

```python
model_df = merged[(merged['Day_of_Week'] != 'Monday') & (merged['Bowls_Sold'] > 0)].copy()
```

## Troubleshooting

### Dashboard Won't Start
```bash
# Check if streamlit is installed
pip list | grep streamlit

# Reinstall if needed
pip install streamlit
```

### Data Loading Errors
- Verify CSV files are in the same directory as `app.py`
- Check file names match exactly (case-sensitive)
- Ensure CSV encoding is UTF-8

### Model Errors
- Verify statsmodels is installed: `pip install statsmodels`
- Check for sufficient data points (need at least 3-4 days)
- Ensure no all-zero columns in model data

### Timezone Issues
The app converts Pacific Time to Eastern Time. To change:

```python
# Line 16: Modify timezone conversion
pt_tz, et_tz = pytz.timezone('US/Pacific'), pytz.timezone('US/Eastern')
```

## Technical Stack

- **Streamlit** - Web dashboard framework
- **Pandas** - Data manipulation
- **Plotly** - Interactive visualizations
- **Statsmodels** - OLS regression
- **NumPy** - Numerical operations
- **Pytz** - Timezone handling

## File Structure

```
moms-dashboard/
├── app.py                          # Main dashboard application
├── 2025_Bamboo_Data.csv            # 2025 sales data
├── Jan_2026_Bamboo_Data.csv        # January 2026 sales data
├── camp_hill_2025_weather.csv      # 2025 weather data
├── jan_weather.csv                 # January 2026 weather data
├── README.md                       # This file (overview)
├── SIMPLE_MODEL_EXPLANATION.md     # Detailed model documentation
├── IMPLEMENTATION_SUMMARY.md       # Technical implementation details
├── DASHBOARD_LAYOUT.md             # UI layout diagram
└── .venv/                          # Virtual environment
```

## Additional Documentation

For detailed information about the current model:
- **`SIMPLE_MODEL_EXPLANATION.md`** - Complete guide to the interaction term model, coefficient interpretation, and prediction examples

## Future Enhancements

Potential additions:
- [x] Multi-year data (2025 + 2026) ✅
- [x] Interaction term for temperature-precipitation effects ✅
- [ ] Hourly sales breakdown
- [ ] Menu item popularity analysis
- [ ] Automated weather API integration
- [ ] Sales forecasting (7-day outlook)
- [ ] Customer segmentation analysis
- [ ] Profit margin tracking

## Support

For questions or issues:
1. Check the troubleshooting section above
2. Review the implementation summary
3. Verify data file formats
4. Check Python/package versions

## License

Internal use only - Bamboo Pho & Tea operations.
