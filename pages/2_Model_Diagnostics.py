import streamlit as st
import pandas as pd
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
    
    # Load 2024 sales data
    df_2024 = pd.read_csv('2024_Bamboo_Data.csv')
    df_2024['Datetime_PT'] = pd.to_datetime(df_2024['Date'] + ' ' + df_2024['Time'])
    df_2024['Datetime_ET'] = df_2024['Datetime_PT'].dt.tz_localize(pt_tz).dt.tz_convert(et_tz)
    df_2024['Date'] = df_2024['Datetime_ET'].dt.date
    df_2024['Day_of_Week'] = df_2024['Datetime_ET'].dt.day_name()
    df_2024['Gross Sales'] = df_2024['Gross Sales'].replace(r'[\$,]', '', regex=True).astype(float)
    df_2024['Qty'] = pd.to_numeric(df_2024['Qty'], errors='coerce').fillna(0)
    
    # Load 2025 sales data
    df_2025 = pd.read_csv('2025_Bamboo_Data.csv')
    df_2025['Datetime_PT'] = pd.to_datetime(df_2025['Date'] + ' ' + df_2025['Time'])
    df_2025['Datetime_ET'] = df_2025['Datetime_PT'].dt.tz_localize(pt_tz).dt.tz_convert(et_tz)
    df_2025['Date'] = df_2025['Datetime_ET'].dt.date
    df_2025['Day_of_Week'] = df_2025['Datetime_ET'].dt.day_name()
    df_2025['Gross Sales'] = df_2025['Gross Sales'].replace(r'[\$,]', '', regex=True).astype(float)
    df_2025['Qty'] = pd.to_numeric(df_2025['Qty'], errors='coerce').fillna(0)
    
    # Load Jan 2026 sales data
    df_jan_2026 = pd.read_csv('Jan_2026_Bamboo_Data.csv')
    df_jan_2026['Datetime_PT'] = pd.to_datetime(df_jan_2026['Date'] + ' ' + df_jan_2026['Time'])
    df_jan_2026['Datetime_ET'] = df_jan_2026['Datetime_PT'].dt.tz_localize(pt_tz).dt.tz_convert(et_tz)
    df_jan_2026['Date'] = df_jan_2026['Datetime_ET'].dt.date
    df_jan_2026['Day_of_Week'] = df_jan_2026['Datetime_ET'].dt.day_name()
    df_jan_2026['Gross Sales'] = df_jan_2026['Gross Sales'].replace(r'[\$,]', '', regex=True).astype(float)
    df_jan_2026['Qty'] = pd.to_numeric(df_jan_2026['Qty'], errors='coerce').fillna(0)
    
    # Load Feb 2026 sales data (up to Feb 2)
    df_feb_2026 = pd.read_csv('feb_2026_uptofeb2_summary.csv')
    df_feb_2026['Datetime_PT'] = pd.to_datetime(df_feb_2026['Date'] + ' ' + df_feb_2026['Time'])
    df_feb_2026['Datetime_ET'] = df_feb_2026['Datetime_PT'].dt.tz_localize(pt_tz).dt.tz_convert(et_tz)
    df_feb_2026['Date'] = df_feb_2026['Datetime_ET'].dt.date
    df_feb_2026['Day_of_Week'] = df_feb_2026['Datetime_ET'].dt.day_name()
    df_feb_2026['Gross Sales'] = df_feb_2026['Gross Sales'].replace(r'[\$,]', '', regex=True).astype(float)
    df_feb_2026['Qty'] = pd.to_numeric(df_feb_2026['Qty'], errors='coerce').fillna(0)
    
    # Combine sales data
    df = pd.concat([df_2024, df_2025, df_jan_2026, df_feb_2026], ignore_index=True)
    
    # Load 2024 weather data (preprocessed)
    weather_2024 = pd.read_csv('camp_hill_2024_weather_processed.csv')
    weather_2024['Date'] = pd.to_datetime(weather_2024['Date']).dt.date
    
    # Load 2025 weather data
    weather_2025 = pd.read_csv('camp_hill_2025_weather.csv')
    weather_2025['Date'] = pd.to_datetime(weather_2025['Date']).dt.date
    
    # Load Jan 2026 weather data
    weather_jan_2026 = pd.read_csv('jan_weather.csv')
    weather_jan_2026['Date'] = pd.to_datetime(weather_jan_2026['Date']).dt.date
    
    # Load Feb 2026 weather data
    weather_feb_2026 = pd.read_csv('feb_weather.csv')
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
    
    # Weekend binary (Saturday and Sunday only)
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Saturday', 'Sunday']).astype(int)
    
    # Mixed precipitation
    merged['is_mixed_precip'] = (merged['Precip_Type'] == 'Mixed').astype(int)
    
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
    
    # Private Sector Payday Effects
    merged['is_weekly_friday'] = (merged['Day_of_Week'] == 'Friday').astype(int)
    merged['is_semi_monthly'] = 0
    merged.loc[merged['Date_dt'].dt.day == 15, 'is_semi_monthly'] = 1
    merged.loc[merged['Date_dt'].dt.day == merged['Date_dt'].dt.days_in_month, 'is_semi_monthly'] = 1
    merged['is_semi_monthly_weekend'] = (merged['is_semi_monthly'] * merged['is_weekend']).astype(int)
    
    # Prepare model data (exclude Mondays and zero sales)
    model_df = merged[
        (merged['Day_of_Week'] != 'Monday') & 
        (merged['Bowls_Sold'] > 0)
    ].copy()
    
    # Center temperature
    mean_temp = model_df['Temp_High'].mean()
    model_df['Temp_Centered'] = model_df['Temp_High'] - mean_temp
    
    # Run simplified payday-focused OLS regression
    X = model_df[['Temp_Centered', 'is_weekend', 'is_mixed_precip', 'is_federal_payday', 
                  'is_payday_weekend', 'is_weekly_friday', 'is_semi_monthly', 'is_semi_monthly_weekend']]
    y = model_df['Bowls_Sold']
    X = sm.add_constant(X)
    ols_model = sm.OLS(y, X).fit()
    
    # Calculate MAE
    mae = (y - ols_model.predict(X)).abs().mean()
    
    # --- ACTUAL VS PREDICTED (Recent Days) ---
    st.subheader("🎯 Model Performance: Actual vs Predicted")
    
    # Get recent operating days (last 7 days with sales, excluding Mondays)
    recent_df = model_df.tail(14).copy()  # Get more to ensure we have enough after filtering
    recent_df = recent_df[recent_df['Day_of_Week'] != 'Monday'].tail(7)  # Get last 7 operating days
    
    if len(recent_df) > 0:
        # Calculate predictions for recent days
        recent_df['Predicted'] = (
            ols_model.params['const'] + 
            (ols_model.params['Temp_Centered'] * recent_df['Temp_Centered']) +
            (ols_model.params['is_weekend'] * recent_df['is_weekend']) +
            (ols_model.params['is_mixed_precip'] * recent_df['is_mixed_precip']) +
            (ols_model.params['is_federal_payday'] * recent_df['is_federal_payday']) +
            (ols_model.params['is_payday_weekend'] * recent_df['is_payday_weekend']) +
            (ols_model.params['is_weekly_friday'] * recent_df['is_weekly_friday']) +
            (ols_model.params['is_semi_monthly'] * recent_df['is_semi_monthly']) +
            (ols_model.params['is_semi_monthly_weekend'] * recent_df['is_semi_monthly_weekend'])
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
        'const': f'Intercept (Baseline: Tue-Thu, Clear, {mean_temp:.1f}°F)',
        'Temp_Centered': 'Temperature (centered)',
        'is_weekend': 'Weekend (Sat/Sun only)',
        'is_mixed_precip': 'Mixed Precipitation',
        'is_federal_payday': 'Federal Payday Friday (bi-weekly, NSA)',
        'is_payday_weekend': 'Payday Weekend (Sat/Sun after federal payday)',
        'is_weekly_friday': 'Weekly Friday (General Payday)',
        'is_semi_monthly': 'Semi-Monthly Payday (15th & Last Day)',
        'is_semi_monthly_weekend': 'Semi-Monthly × Weekend (interaction)'
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

    # --- SCATTER PLOT WITH REGRESSION LINES ---
    st.subheader("🌡️ Temperature vs Bowls Sold")
    
    # Create scatter plot colored by weekend vs midweek
    model_df['Day_Type'] = model_df['is_weekend'].apply(lambda x: 'Weekend (Sat/Sun)' if x == 1 else 'Midweek (Tue-Thu)')
    
    fig = px.scatter(model_df, x='Temp_High', y='Bowls_Sold', color='Day_Type',
                     color_discrete_map={'Weekend (Sat/Sun)': '#DAA520', 'Midweek (Tue-Thu)': '#1E88E5'},
                     hover_data=['Date', 'Day_of_Week', 'Precip_Type'],
                     labels={'Temp_High': 'Temperature (°F)', 'Bowls_Sold': 'Bowls Sold'})
    
    # Regression Lines (showing baseline relationships without special events)
    temp_range = np.linspace(model_df['Temp_High'].min(), model_df['Temp_High'].max(), 100)
    temp_range_centered = temp_range - mean_temp
    
    # Weekend line (Sat/Sun, no special events)
    y_weekend = ols_model.params['const'] + (ols_model.params['Temp_Centered'] * temp_range_centered) + ols_model.params['is_weekend']
    # Midweek line (Tue-Thu, no special events)
    y_midweek = ols_model.params['const'] + (ols_model.params['Temp_Centered'] * temp_range_centered)
    
    fig.add_trace(go.Scatter(x=temp_range, y=y_weekend, name='Weekend Baseline',
                            line=dict(color='#DAA520', width=4), mode='lines'))
    fig.add_trace(go.Scatter(x=temp_range, y=y_midweek, name='Midweek Baseline',
                            line=dict(color='#1E88E5', width=4, dash='dash'), mode='lines'))
    
    fig.update_traces(marker=dict(size=10, opacity=0.6))
    fig.update_layout(template="simple_white", hovermode="closest",
                     legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("📊 Baseline relationships shown. Simplified payday-focused model includes 8 features: Temp, Weekend(Sat/Sun), Mixed Precip, Federal Payday (bi-weekly), Payday Weekend, Weekly Friday, Semi-Monthly (15th/Last), and Semi-Monthly×Weekend interaction.")

except Exception as e:
    st.error(f"Model Diagnostics Error: {e}")
