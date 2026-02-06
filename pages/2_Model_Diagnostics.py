import os
import streamlit as st
import pandas as pd

# Project root for data files (pages/ is subdir, so go up one level)
_script_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == 'pages' else _script_dir
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import pytz

st.title("📊 Model Diagnostics")

st.markdown("""
This page provides detailed diagnostics for the OLS regression model predicting Pho bowls sold.
The model uses temperature, precipitation, weekend effects, and interaction terms.
""")

@st.cache_data
def load_all_data():
    # Load and adjust timezone - combining 2024, 2025, and 2026 data
    pt_tz, et_tz = pytz.timezone('US/Pacific'), pytz.timezone('US/Eastern')

    def process_sales(df_raw):
        df_raw['Datetime_PT'] = pd.to_datetime(df_raw['Date'] + ' ' + df_raw['Time'])
        df_raw['Datetime_ET'] = df_raw['Datetime_PT'].dt.tz_localize(pt_tz).dt.tz_convert(et_tz)
        df_raw['Date'] = df_raw['Datetime_ET'].dt.date
        df_raw['Day_of_Week'] = df_raw['Datetime_ET'].dt.day_name()
        df_raw['Gross Sales'] = df_raw['Gross Sales'].replace(r'[\$,]', '', regex=True).astype(float)
        df_raw['Qty'] = pd.to_numeric(df_raw['Qty'], errors='coerce').fillna(0)
        return df_raw

    def _path(fname):
        """Try project folder, then Extreme SSD (project or root) if mounted."""
        p = os.path.join(BASE_DIR, fname)
        if os.path.exists(p):
            return p
        for vol in ['Extreme SSD', 'Extreme']:
            for sub in ['', 'moms-dashboard']:
                alt = os.path.join('/Volumes', vol, sub, fname) if sub else os.path.join('/Volumes', vol, fname)
                if os.path.exists(alt):
                    return alt
        return p

    sales_dfs = []
    # Load 2024 sales data (optional on Streamlit Cloud; required locally)
    try:
        df_2024 = process_sales(pd.read_csv(_path('2024_Bamboo_Data.csv')))
        sales_dfs.append(df_2024)
    except (FileNotFoundError, OSError):
        pass

    # Load 2025 sales data (optional on Streamlit Cloud; required locally)
    try:
        df_2025 = process_sales(pd.read_csv(_path('2025_Bamboo_Data.csv')))
        sales_dfs.append(df_2025)
    except (FileNotFoundError, OSError):
        pass

    # Load Jan 2026 sales data
    df_jan_2026 = process_sales(pd.read_csv(os.path.join(BASE_DIR, 'Jan_2026_Bamboo_Data.csv')))
    sales_dfs.append(df_jan_2026)

    # Load Feb 2026 sales data (Feb 1-4)
    df_feb_2026 = process_sales(pd.read_csv(os.path.join(BASE_DIR, 'Feb 3 and 4 sales.csv')))
    sales_dfs.append(df_feb_2026)

    # Combine sales data
    if not sales_dfs:
        raise FileNotFoundError("No sales data. Need Jan_2026_Bamboo_Data.csv and Feb 3 and 4 sales.csv.")
    df = pd.concat(sales_dfs, ignore_index=True)
    
    # Load 2024 weather data (preprocessed)
    weather_2024 = pd.read_csv(os.path.join(BASE_DIR, 'camp_hill_2024_weather_processed.csv'))
    weather_2024['Date'] = pd.to_datetime(weather_2024['Date']).dt.date
    
    # Load 2025 weather data
    weather_2025 = pd.read_csv(os.path.join(BASE_DIR, 'camp_hill_2025_weather.csv'))
    weather_2025['Date'] = pd.to_datetime(weather_2025['Date']).dt.date
    
    # Load Jan 2026 weather data
    weather_jan_2026 = pd.read_csv(os.path.join(BASE_DIR, 'jan_weather.csv'))
    weather_jan_2026['Date'] = pd.to_datetime(weather_jan_2026['Date']).dt.date
    
    # Load Feb 2026 weather data
    weather_feb_2026 = pd.read_csv(os.path.join(BASE_DIR, 'feb_weather.csv'))
    # Fix column names (handle spaces)
    weather_feb_2026.columns = weather_feb_2026.columns.str.replace(' ', '_')
    # Clean temperature values (remove °F suffix)
    weather_feb_2026['Temp_High'] = weather_feb_2026['Temp_High'].astype(str).str.replace('°F', '').astype(float)
    # Clean precipitation type (extract base type)
    weather_feb_2026['Precip_Type'] = weather_feb_2026['Precip_Type'].str.split(' ').str[0]
    weather_feb_2026['Date'] = pd.to_datetime(weather_feb_2026['Date']).dt.date
    
    # Combine weather data
    weather = pd.concat([weather_2024, weather_2025, weather_jan_2026, weather_feb_2026], ignore_index=True)
    
    # Aggregate pho bowls
    pho_items = df[df['Item'].str.contains('Pho', case=False, na=False)]
    daily_pho = pho_items.groupby('Date').agg({'Qty': 'sum'}).reset_index()
    daily_pho.columns = ['Date', 'Bowls_Sold']
    
    # Merge with weather
    merged = pd.merge(daily_pho, weather, on='Date', how='left')
    merged['Day_of_Week'] = pd.to_datetime(merged['Date']).dt.day_name()
    merged['Precip_Type'] = merged['Precip_Type'].fillna('Clear')
    
    return df, merged

try:
    sales_df, merged = load_all_data()
    
    # --- FEATURE ENGINEERING ---
    
    # Weekend binary (Friday, Saturday, Sunday - combined payday/weekend effect)
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Friday', 'Saturday', 'Sunday']).astype(int)
    
    # Precipitation type binaries (3 categories)
    merged['is_clear'] = (merged['Precip_Type'].isin(['None', 'Clear'])).astype(int)
    merged['is_rain'] = (merged['Precip_Type'].isin(['Rain', 'Mixed'])).astype(int)
    merged['is_snow'] = (merged['Precip_Type'].isin(['Snow', 'Flurries', 'Heavy Snow'])).astype(int)
    
    # Seasonality: Consolidated season impact variable
    merged['Date_dt'] = pd.to_datetime(merged['Date'])
    merged['month'] = merged['Date_dt'].dt.month
    
    # High Demand (+1): Jan, Feb, Nov, Dec (The Winter Peak)
    # Low Demand (-1): Apr, May, Jun, Jul, Aug (The Transitions & Heat Slump)
    # Neutral (0): March, September, October
    def get_season_impact(month):
        if month in [1, 2, 11, 12]:  # High demand (winter peak)
            return 1
        elif month in [4, 5, 6, 7, 8]:  # Low demand (warm season slump)
            return -1
        else:  # Neutral (Mar, Sep, Oct - shoulder seasons)
            return 0
    
    merged['season_impact'] = merged['month'].apply(get_season_impact)
    
    # Naval Base Traffic Effects
    merged['Date_dt'] = pd.to_datetime(merged['Date'])
    
    # Federal Payday: Bi-weekly Fridays (2025 + 2026)
    federal_payday_anchor = pd.Timestamp('2026-01-09')
    federal_paydays = []
    current_date = federal_payday_anchor
    
    # Go backwards to cover 2025
    while current_date >= pd.Timestamp('2025-01-01'):
        federal_paydays.append(current_date)
        current_date = current_date - pd.Timedelta(days=14)
    
    # Go forwards to cover rest of 2026
    current_date = federal_payday_anchor + pd.Timedelta(days=14)
    while current_date <= pd.Timestamp('2026-12-31'):
        federal_paydays.append(current_date)
        current_date = current_date + pd.Timedelta(days=14)
    
    merged['is_federal_payday'] = merged['Date_dt'].isin(federal_paydays).astype(int)
    
    # Payday Weekend
    merged['is_payday_weekend'] = 0
    payday_dates = merged[merged['is_federal_payday'] == 1]['Date_dt']
    for payday_date in payday_dates:
        merged.loc[merged['Date_dt'] == payday_date + pd.Timedelta(days=1), 'is_payday_weekend'] = 1
        merged.loc[merged['Date_dt'] == payday_date + pd.Timedelta(days=2), 'is_payday_weekend'] = 1
    
    # Friday Base Traffic
    merged['is_friday_base'] = (merged['Day_of_Week'] == 'Friday').astype(int)
    
    # Holiday Proximity Effects
    major_holidays = [
        pd.Timestamp('2025-01-01'), pd.Timestamp('2025-01-29'), pd.Timestamp('2025-02-09'),
        pd.Timestamp('2025-02-14'), pd.Timestamp('2025-04-20'), pd.Timestamp('2025-05-26'),
        pd.Timestamp('2025-07-04'), pd.Timestamp('2025-09-01'), pd.Timestamp('2025-11-27'),
        pd.Timestamp('2025-12-25'), pd.Timestamp('2026-01-01'), pd.Timestamp('2026-02-17'),
        pd.Timestamp('2026-02-08'), pd.Timestamp('2026-02-14'), pd.Timestamp('2026-04-05'),
        pd.Timestamp('2026-05-25'), pd.Timestamp('2026-07-04'), pd.Timestamp('2026-09-07'),
        pd.Timestamp('2026-11-26'), pd.Timestamp('2026-12-25')
    ]
    
    merged['is_pre_holiday'] = 0
    for holiday in major_holidays:
        merged.loc[merged['Date_dt'].isin([holiday - pd.Timedelta(days=1), holiday - pd.Timedelta(days=2)]), 'is_pre_holiday'] = 1
    
    merged['is_post_holiday'] = 0
    for holiday in major_holidays:
        merged.loc[merged['Date_dt'].isin([holiday + pd.Timedelta(days=1), holiday + pd.Timedelta(days=2)]), 'is_post_holiday'] = 1
    
    merged['is_valentines_period'] = merged['Date_dt'].isin([
        pd.Timestamp('2025-02-13'), pd.Timestamp('2025-02-14'), pd.Timestamp('2025-02-15'),
        pd.Timestamp('2026-02-13'), pd.Timestamp('2026-02-14'), pd.Timestamp('2026-02-15')
    ]).astype(int)
    
    merged['is_lunar_new_year'] = merged['Date_dt'].isin([
        pd.Timestamp('2025-01-29'), pd.Timestamp('2025-01-30'), pd.Timestamp('2025-01-31'),
        pd.Timestamp('2026-02-17'), pd.Timestamp('2026-02-18'), pd.Timestamp('2026-02-19')
    ]).astype(int)
    
    merged['is_pre_holiday_friday'] = (merged['is_pre_holiday'] * merged['is_friday_base']).astype(int)
    
    # Year Dummies (Capture Model Drift)
    merged['year'] = merged['Date_dt'].dt.year
    merged['is_2024'] = (merged['year'] == 2024).astype(int)
    merged['is_2025'] = (merged['year'] == 2025).astype(int)
    
    # Prepare model data (exclude Mondays and zero sales)
    model_df = merged[
        (merged['Day_of_Week'] != 'Monday') & 
        (merged['Bowls_Sold'] > 0)
    ].copy()
    
    # --- FIND OPTIMAL TEMPERATURE KINK POINT ---
    # Test piecewise temperature models with different kink points
    kink_points = [50, 55, 60, 65, 70]
    best_r2 = 0
    best_kink = 60  # Default
    
    for kink in kink_points:
        # Create piecewise temperature variables
        model_df[f'temp_cold_{kink}'] = model_df['Temp_High'].apply(lambda t: min(t, kink))
        model_df[f'temp_hot_{kink}'] = model_df['Temp_High'].apply(lambda t: max(0, t - kink))
        
        # Build temporary model with this kink
        X_temp = model_df[[f'temp_cold_{kink}', f'temp_hot_{kink}', 
                          'is_weekend', 'is_rain', 'is_snow', 'is_federal_payday', 
                          'is_payday_weekend',
                          'is_2024', 'is_2025', 'season_impact']]
        X_temp = sm.add_constant(X_temp)
        y_temp = model_df['Bowls_Sold']
        
        model_temp = sm.OLS(y_temp, X_temp).fit()
        
        if model_temp.rsquared > best_r2:
            best_r2 = model_temp.rsquared
            best_kink = kink
    
    # Use optimal kink point
    model_df['temp_cold'] = model_df['Temp_High'].apply(lambda t: min(t, best_kink))
    model_df['temp_hot'] = model_df['Temp_High'].apply(lambda t: max(0, t - best_kink))
    
    # --- BUILD SIMPLIFIED PIECEWISE TEMPERATURE MODEL ---
    # Season_Impact: High (+1) = Jan/Feb/Nov/Dec, Low (-1) = Apr-Aug, Neutral (0) = Mar/Sep/Oct
    # Weekend now includes Friday (combined payday/weekend effect)
    # Temperature: Piecewise at optimal kink point
    X = model_df[['temp_cold', 'temp_hot', 'is_weekend', 'is_rain', 'is_snow', 'is_federal_payday', 
                  'is_payday_weekend',
                  'is_2024', 'is_2025', 'season_impact']]
    y = model_df['Bowls_Sold']
    X = sm.add_constant(X)
    ols_model = sm.OLS(y, X).fit()
    
    # Calculate MAE and predictions
    mae = (y - ols_model.predict(X)).abs().mean()
    model_df['Predicted'] = ols_model.predict(X)
    model_df['Error'] = model_df['Bowls_Sold'] - model_df['Predicted']
    model_df['Error_Pct'] = (model_df['Error'] / model_df['Bowls_Sold'] * 100).abs()
    
    # --- MODEL PERFORMANCE SUMMARY ---
    st.subheader("📊 Model Performance Summary")
    
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.markdown("**Fit Metrics**")
        st.metric("R²", f"{ols_model.rsquared:.3f}",
                 help="Variance explained")
        st.metric("Adj. R²", f"{ols_model.rsquared_adj:.3f}")
        st.metric("MAE", f"{mae:.2f} bowls",
                 help="Mean Absolute Error")
        st.metric("F-stat", f"{ols_model.fvalue:.1f}",
                 help="Model significance")
    
    with stat_col2:
        st.markdown("**Core Effects**")
        st.metric("🌡️ Cold", f"{ols_model.params['temp_cold']:.3f}/°F",
                 help=f"Below {best_kink}°F")
        st.metric("🌡️ Hot", f"{ols_model.params['temp_hot']:.3f}/°F",
                 help=f"Above {best_kink}°F")
        st.metric("📅 Weekend", f"+{ols_model.params['is_weekend']:.1f}")
        st.metric("🌧️ Rain", f"{ols_model.params['is_rain']:+.1f}")
        st.metric("❄️ Snow", f"{ols_model.params['is_snow']:+.1f}")
    
    with stat_col3:
        st.markdown("**Key Effects**")
        st.metric("🌦️ Season", f"{ols_model.params['season_impact']:+.1f}",
                 help="Winter peak vs warm slump")
        st.metric("🏛️ Fed Pay", f"+{ols_model.params['is_federal_payday']:.1f}",
                 help="NSA bi-weekly payday")
        st.metric("🏛️ Pay Wknd", f"+{ols_model.params['is_payday_weekend']:.1f}",
                 help="Sat/Sun after federal payday")
    
    st.divider()
    
    # --- ACTUAL VS PREDICTED (ALL HISTORICAL DATA) ---
    st.subheader("📈 Model Fit: Actual vs Predicted Bowls")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Scatter plot: Actual vs Predicted
        fig_scatter = go.Figure()
        
        # Add scatter points colored by error percentage
        fig_scatter.add_trace(go.Scatter(
            x=model_df['Predicted'],
            y=model_df['Bowls_Sold'],
            mode='markers',
            marker=dict(
                size=8,
                color=model_df['Error_Pct'],
                colorscale='RdYlGn_r',  # Red = high error, Green = low error
                showscale=True,
                colorbar=dict(title="Error %"),
                line=dict(width=0.5, color='white')
            ),
            text=[f"Date: {d}<br>Actual: {a:.0f}<br>Predicted: {p:.0f}<br>Error: {e:.1f}%" 
                  for d, a, p, e in zip(model_df['Date'], model_df['Bowls_Sold'], 
                                       model_df['Predicted'], model_df['Error_Pct'])],
            hovertemplate='%{text}<extra></extra>',
            name='Data Points'
        ))
        
        # Add perfect prediction line (y = x)
        min_val = min(model_df['Predicted'].min(), model_df['Bowls_Sold'].min())
        max_val = max(model_df['Predicted'].max(), model_df['Bowls_Sold'].max())
        fig_scatter.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            line=dict(color='black', width=2, dash='dash'),
            name='Perfect Fit (y=x)'
        ))
        
        fig_scatter.update_layout(
            xaxis_title='Predicted Bowls',
            yaxis_title='Actual Bowls',
            template='simple_white',
            hovermode='closest',
            height=500
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("📊 Points on the diagonal line = perfect predictions. Color shows error magnitude.")
    
    with col2:
        st.markdown("### Error Distribution")
        
        # Error distribution
        within_5pct = (model_df['Error_Pct'] <= 5).sum()
        within_10pct = (model_df['Error_Pct'] <= 10).sum()
        within_20pct = (model_df['Error_Pct'] <= 20).sum()
        total = len(model_df)
        
        st.metric("Within 5% Error", f"{within_5pct} days ({100*within_5pct/total:.0f}%)")
        st.metric("Within 10% Error", f"{within_10pct} days ({100*within_10pct/total:.0f}%)")
        st.metric("Within 20% Error", f"{within_20pct} days ({100*within_20pct/total:.0f}%)")
        
        st.markdown("---")
        
        st.metric("Mean Absolute Error", f"{mae:.1f} bowls")
        
        st.metric("RMSE", f"{np.sqrt(ols_model.mse_resid):.1f} bowls",
                 help="Root Mean Squared Error")
    
    st.divider()
    
    # --- ACTUAL VS PREDICTED (Recent Days) ---
    st.subheader("🎯 Recent Days: Actual vs Predicted")
    
    # Get recent operating days (last 7 days with sales, excluding Mondays)
    recent_df = model_df.tail(14).copy()  # Get more to ensure we have enough after filtering
    recent_df = recent_df[recent_df['Day_of_Week'] != 'Monday'].tail(7)  # Get last 7 operating days
    
    if len(recent_df) > 0:
        # Calculate predictions for recent days
        recent_df['Predicted'] = (
            ols_model.params['const'] + 
            (ols_model.params['temp_cold'] * recent_df['temp_cold']) +
            (ols_model.params['temp_hot'] * recent_df['temp_hot']) +
            (ols_model.params['is_weekend'] * recent_df['is_weekend']) +
            (ols_model.params['is_rain'] * recent_df['is_rain']) +
            (ols_model.params['is_snow'] * recent_df['is_snow']) +
            (ols_model.params['is_federal_payday'] * recent_df['is_federal_payday']) +
            (ols_model.params['is_payday_weekend'] * recent_df['is_payday_weekend']) +
            (ols_model.params['is_2024'] * recent_df['is_2024']) +
            (ols_model.params['is_2025'] * recent_df['is_2025']) +
            (ols_model.params['season_impact'] * recent_df['season_impact'])
        )
        
        recent_df['Error'] = recent_df['Bowls_Sold'] - recent_df['Predicted']
        recent_df['Error_Pct'] = (recent_df['Error'] / recent_df['Bowls_Sold'] * 100)
        
        # Create comparison table
        comparison_data = recent_df[['Date', 'Day_of_Week', 'Temp_High', 'Precip_Type', 'Bowls_Sold', 'Predicted', 'Error', 'Error_Pct']].copy()
        comparison_data['Date'] = pd.to_datetime(comparison_data['Date']).dt.strftime('%Y-%m-%d')
        comparison_data['Predicted'] = comparison_data['Predicted'].round(1)
        comparison_data['Error'] = comparison_data['Error'].round(1)
        comparison_data['Error_Pct'] = comparison_data['Error_Pct'].round(1)
        
        # Flag errors > ±10%
        comparison_data['Flag'] = comparison_data['Error_Pct'].apply(lambda x: '🚩' if abs(x) > 10 else '')
        
        comparison_data.columns = ['Date', 'Day', 'Temp (°F)', 'Weather', 'Actual', 'Predicted', 'Error', 'Error %', 'Flag']
        
        st.dataframe(comparison_data, use_container_width=True, hide_index=True)
        st.caption("🚩 = Error exceeds ±10%")
        
        # Show metrics for most recent operating day
        most_recent = recent_df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(f"📅 {most_recent['Day_of_Week']} {pd.to_datetime(most_recent['Date']).strftime('%b %d')}", 
                     "Most Recent Day")
        with col2:
            st.metric("Actual Bowls", f"{int(most_recent['Bowls_Sold'])}")
        with col3:
            st.metric("Predicted Bowls", f"{int(most_recent['Predicted'])}")
        with col4:
            error_val = int(most_recent['Error'])
            st.metric("Prediction Error", f"{error_val:+d} bowls", 
                     delta=f"{most_recent['Error_Pct']:.1f}%",
                     delta_color="inverse")
    
    st.divider()
    
    # --- MODEL STATISTICS (STARGAZER-STYLE) ---
    st.subheader("📊 OLS Regression Results")
    
    # Create a clean summary table
    summary_data = {
        'Variable': [],
        'Coefficient': [],
        'Std Error': [],
        't-statistic': [],
        'P-value': [],
        'Significance': []
    }
    
    # Get model parameters
    params = ols_model.params
    std_err = ols_model.bse
    t_stats = ols_model.tvalues
    p_values = ols_model.pvalues
    
    # Format variable names
    var_names = {
        'const': f'Intercept (Baseline: 2026, Neutral season, Tue-Thu, Clear, Temp at kink)',
        'temp_cold': f'Temperature ≤ {best_kink}°F (below kink, should be ~0)',
        'temp_hot': f'Temperature > {best_kink}°F (above kink, should be negative)',
        'is_weekend': 'Weekend (Fri/Sat/Sun - combined payday/weekend)',
        'is_rain': 'Rain/Mixed (vs Clear)',
        'is_snow': 'Snow/Flurries/Heavy (vs Clear)',
        'is_federal_payday': 'Federal Payday Friday (bi-weekly, NSA)',
        'is_payday_weekend': 'Payday Weekend (Sat/Sun after federal payday)',
        'is_2024': 'Year 2024 (vs 2026 baseline)',
        'is_2025': 'Year 2025 (vs 2026 baseline)',
        'season_impact': 'Season Impact (+1: Jan/Feb/Nov/Dec, -1: Apr-Aug, 0: Mar/Sep/Oct)'
    }
    
    for var in params.index:
        summary_data['Variable'].append(var_names.get(var, var))
        summary_data['Coefficient'].append(f"{params[var]:.4f}")
        summary_data['Std Error'].append(f"{std_err[var]:.4f}")
        summary_data['t-statistic'].append(f"{t_stats[var]:.3f}")
        summary_data['P-value'].append(f"{p_values[var]:.4f}")
        
        # Add significance stars
        if p_values[var] < 0.001:
            sig = '***'
        elif p_values[var] < 0.01:
            sig = '**'
        elif p_values[var] < 0.05:
            sig = '*'
        elif p_values[var] < 0.10:
            sig = '.'
        else:
            sig = ''
        summary_data['Significance'].append(sig)
    
    summary_df = pd.DataFrame(summary_data)
    
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    # Model statistics
    stats_col1, stats_col2, stats_col3, stats_col4, stats_col5 = st.columns(5)
    with stats_col1:
        st.metric("R²", f"{ols_model.rsquared:.4f}")
    with stats_col2:
        st.metric("Adj. R²", f"{ols_model.rsquared_adj:.4f}")
    with stats_col3:
        st.metric("MAE", f"{mae:.2f}")
    with stats_col4:
        st.metric("F-statistic", f"{ols_model.fvalue:.2f}")
    with stats_col5:
        st.metric("Prob(F)", f"{ols_model.f_pvalue:.4f}")
    
    st.caption("Significance codes: *** p<0.001, ** p<0.01, * p<0.05, . p<0.10")
    st.caption(f"Observations: {int(ols_model.nobs)} | Residual Std. Error: {np.sqrt(ols_model.mse_resid):.3f} | MAE: Mean Absolute Error")
    
    st.divider()
    
    # --- TEMPERATURE KINK POINT ANALYSIS ---
    st.subheader("🌡️ Temperature Kink Point Analysis")
    
    st.markdown(f"""
    **Piecewise Temperature Model**: Tests whether temperature affects demand **non-linearly** with a threshold (kink).
    
    - **Below {best_kink}°F**: Cold enough for pho (coefficient: {ols_model.params['temp_cold']:.4f})
    - **Above {best_kink}°F**: Each degree warmer reduces demand (coefficient: {ols_model.params['temp_hot']:.4f})
    
    This "hockey stick" pattern captures that pho demand is strong in cold weather, but as temperatures rise,
    customers shift to other options like banh mi or fresh salads.
    """)
    
    # Display kink point comparison table
    kink_results_for_display = []
    for kink_val in [50, 55, 60, 65, 70]:
        # Recreate the kink analysis for display
        model_df[f'temp_cold_{kink_val}'] = model_df['Temp_High'].apply(lambda t: min(t, kink_val))
        model_df[f'temp_hot_{kink_val}'] = model_df['Temp_High'].apply(lambda t: max(0, t - kink_val))
        
        X_display = model_df[[f'temp_cold_{kink_val}', f'temp_hot_{kink_val}', 
                             'is_weekend', 'is_rain', 'is_snow', 'is_federal_payday', 
                             'is_payday_weekend',
                             'is_2024', 'is_2025', 'season_impact']]
        X_display = sm.add_constant(X_display)
        y_display = model_df['Bowls_Sold']
        model_display = sm.OLS(y_display, X_display).fit()
        
        kink_results_for_display.append({
            'Kink (°F)': kink_val,
            'R²': model_display.rsquared,
            'Cold Coef': model_display.params[f'temp_cold_{kink_val}'],
            'Hot Coef': model_display.params[f'temp_hot_{kink_val}'],
            'Cold p-value': model_display.pvalues[f'temp_cold_{kink_val}'],
            'Hot p-value': model_display.pvalues[f'temp_hot_{kink_val}']
        })
    
    kink_display_df = pd.DataFrame(kink_results_for_display)
    kink_display_df['Cold Coef'] = kink_display_df['Cold Coef'].apply(lambda x: f"{x:.4f}")
    kink_display_df['Hot Coef'] = kink_display_df['Hot Coef'].apply(lambda x: f"{x:.4f}")
    kink_display_df['Cold p-value'] = kink_display_df['Cold p-value'].apply(lambda x: f"{x:.4f}")
    kink_display_df['Hot p-value'] = kink_display_df['Hot p-value'].apply(lambda x: f"{x:.4f}")
    kink_display_df['R²'] = kink_display_df['R²'].apply(lambda x: f"{x:.4f}")
    
    st.dataframe(kink_display_df, hide_index=True, use_container_width=True)
    
    st.caption(f"✅ **Optimal Kink: {best_kink}°F** (highest R²)")
    
    st.divider()

    # --- SCATTER PLOT WITH REGRESSION LINES ---
    st.subheader("🌡️ Temperature vs Bowls Sold")
    
    # Create scatter plot colored by weekend vs midweek
    model_df['Day_Type'] = model_df['is_weekend'].apply(lambda x: 'Weekend (Fri/Sat/Sun)' if x == 1 else 'Midweek (Tue-Thu)')
    
    fig = px.scatter(model_df, x='Temp_High', y='Bowls_Sold', color='Day_Type',
                     color_discrete_map={'Weekend (Fri/Sat/Sun)': '#DAA520', 'Midweek (Tue-Thu)': '#1E88E5'},
                     hover_data=['Date', 'Day_of_Week', 'Precip_Type'],
                     labels={'Temp_High': 'Temperature (°F)', 'Bowls_Sold': 'Bowls Sold'})
    
    # Regression Lines (showing baseline relationships without special events)
    temp_range = np.linspace(model_df['Temp_High'].min(), model_df['Temp_High'].max(), 100)
    temp_range_cold = np.minimum(temp_range, best_kink)
    temp_range_hot = np.maximum(0, temp_range - best_kink)
    
    # Weekend line (Fri/Sat/Sun, no special events)
    y_weekend = (ols_model.params['const'] + 
                 (ols_model.params['temp_cold'] * temp_range_cold) + 
                 (ols_model.params['temp_hot'] * temp_range_hot) + 
                 ols_model.params['is_weekend'])
    # Midweek line (Tue-Thu, no special events)
    y_midweek = (ols_model.params['const'] + 
                 (ols_model.params['temp_cold'] * temp_range_cold) + 
                 (ols_model.params['temp_hot'] * temp_range_hot))
    
    fig.add_trace(go.Scatter(x=temp_range, y=y_weekend, name='Weekend Baseline',
                            line=dict(color='#DAA520', width=4), mode='lines'))
    fig.add_trace(go.Scatter(x=temp_range, y=y_midweek, name='Midweek Baseline',
                            line=dict(color='#1E88E5', width=4, dash='dash'), mode='lines'))
    
    fig.update_traces(marker=dict(size=10, opacity=0.6))
    fig.update_layout(template="simple_white", hovermode="closest",
                     legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(f"📊 Baseline relationships shown. Piecewise temperature model with kink at {best_kink}°F. Lines show 'hockey stick' pattern: flat below kink, steep decline above. Weekend (Fri/Sat/Sun) vs Midweek (Tue-Thu). Model includes 10 features.")

except Exception as e:
    st.error(f"Model Diagnostics Error: {e}")
