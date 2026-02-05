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
    
    # Load Feb 2026 sales data (Feb 1-4)
    df_feb_2026 = pd.read_csv('Feb 3 and 4 sales.csv')
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
    
    # Calculate Total Orders (transaction count) per day for ALL items
    daily_orders = df.groupby('Date')['Transaction ID'].nunique().reset_index()
    daily_orders.columns = ['Date', 'Total_Orders']
    
    # Merge with weather
    merged = pd.merge(daily_pho, weather, on='Date', how='left')
    merged = pd.merge(merged, daily_orders, on='Date', how='left').fillna(0)
    merged['Day_of_Week'] = pd.to_datetime(merged['Date']).dt.day_name()
    merged['Precip_Type'] = merged['Precip_Type'].fillna('Clear')
    
    return df, merged

try:
    sales_df, merged = load_all_data()
    
    # --- FEATURE ENGINEERING ---
    
    # Weekend binary (Saturday and Sunday only)
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Saturday', 'Sunday']).astype(int)
    
    # Precipitation type binaries (3 categories)
    merged['is_clear'] = (merged['Precip_Type'].isin(['None', 'Clear'])).astype(int)
    merged['is_rain'] = (merged['Precip_Type'].isin(['Rain', 'Mixed'])).astype(int)
    merged['is_snow'] = (merged['Precip_Type'].isin(['Snow', 'Flurries', 'Heavy Snow'])).astype(int)
    
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
    
    # Year Dummies (Capture Model Drift)
    merged['year'] = merged['Date_dt'].dt.year
    merged['is_2024'] = (merged['year'] == 2024).astype(int)
    merged['is_2025'] = (merged['year'] == 2025).astype(int)
    merged['is_2026'] = (merged['year'] == 2026).astype(int)
    
    # Interaction: 2026 × Friday (Test if Navy base effect strengthened in 2026)
    merged['is_2026_friday'] = (merged['is_2026'] * merged['is_weekly_friday']).astype(int)
    
    # --- SCHOOL HOLIDAY EFFECT ---
    # Define school holiday ranges (when families have time off)
    school_holidays = [
        # Winter Break
        ('2023-12-22', '2024-01-01'),
        ('2024-12-23', '2025-01-01'),
        ('2025-12-24', '2026-01-02'),
        # Spring Break
        ('2024-03-28', '2024-04-01'),
        ('2025-04-14', '2025-04-21'),
        ('2026-03-20', '2026-03-24'),
        # Thanksgiving Break
        ('2023-11-23', '2023-11-27'),
        ('2024-11-28', '2024-12-02'),
        ('2025-11-27', '2025-11-28'),
    ]
    
    # Single day holidays
    single_day_holidays = [
        # MLK Day
        '2024-01-15', '2025-01-20', '2026-01-19',
        # Presidents' Day
        '2024-02-19', '2025-02-17', '2026-02-16',
        # Memorial Day
        '2024-05-27', '2025-05-26', '2026-05-25',
        # Labor Day
        '2024-09-02', '2025-09-01', '2026-09-07',
    ]
    
    # Initialize column
    merged['is_school_holiday'] = 0
    
    # Mark date ranges
    for start, end in school_holidays:
        date_range = pd.date_range(start=start, end=end, freq='D')
        merged.loc[merged['Date_dt'].isin(date_range), 'is_school_holiday'] = 1
    
    # Mark single days
    for date_str in single_day_holidays:
        date_obj = pd.to_datetime(date_str).date()
        merged.loc[merged['Date'] == date_obj, 'is_school_holiday'] = 1
    
    # Prepare model data (exclude Mondays and zero sales)
    model_df = merged[
        (merged['Day_of_Week'] != 'Monday') & 
        (merged['Bowls_Sold'] > 0)
    ].copy()
    
    # Center temperature
    mean_temp = model_df['Temp_High'].mean()
    model_df['Temp_Centered'] = model_df['Temp_High'] - mean_temp
    
    # --- MODEL A: BOWL COUNT ---
    X = model_df[['Temp_Centered', 'is_weekend', 'is_rain', 'is_snow', 'is_federal_payday', 
                  'is_payday_weekend', 'is_weekly_friday', 'is_semi_monthly', 'is_semi_monthly_weekend',
                  'is_2024', 'is_2025', 'is_2026_friday', 'is_school_holiday']]
    y_bowls = model_df['Bowls_Sold']
    X = sm.add_constant(X)
    ols_model_bowls = sm.OLS(y_bowls, X).fit()
    
    # Calculate MAE and predictions for Model A
    mae_bowls = (y_bowls - ols_model_bowls.predict(X)).abs().mean()
    model_df['Predicted_Bowls'] = ols_model_bowls.predict(X)
    model_df['Error_Bowls'] = model_df['Bowls_Sold'] - model_df['Predicted_Bowls']
    model_df['Error_Pct_Bowls'] = (model_df['Error_Bowls'] / model_df['Bowls_Sold'] * 100).abs()
    mape_bowls = model_df['Error_Pct_Bowls'].mean()
    
    # --- MODEL B: ORDER COUNT ---
    y_orders = model_df['Total_Orders']
    ols_model_orders = sm.OLS(y_orders, X).fit()
    
    # Calculate MAE and predictions for Model B
    mae_orders = (y_orders - ols_model_orders.predict(X)).abs().mean()
    model_df['Predicted_Orders'] = ols_model_orders.predict(X)
    model_df['Error_Orders'] = model_df['Total_Orders'] - model_df['Predicted_Orders']
    model_df['Error_Pct_Orders'] = (model_df['Error_Orders'] / model_df['Total_Orders'] * 100).abs()
    mape_orders = model_df['Error_Pct_Orders'].mean()
    
    # Use Model A for display (backwards compatibility)
    ols_model = ols_model_bowls
    mae = mae_bowls
    model_df['Predicted'] = model_df['Predicted_Bowls']
    model_df['Error'] = model_df['Error_Bowls']
    model_df['Error_Pct'] = model_df['Error_Pct_Bowls']
    
    # --- MODEL COMPARISON SECTION ---
    st.header("🔬 Model Comparison: Bowl Count vs Order Count")
    st.markdown("""
    **Research Question:** Does transaction count (Total Orders) show more stable relationships 
    with our Navy Base and economic variables than bowl count?
    
    Both models use identical features but predict different outcomes:
    - **Model A**: Total Pho bowls sold (affected by party size)
    - **Model B**: Total transactions/orders (pure customer visit count)
    """)
    
    comp_col1, comp_col2, comp_col3 = st.columns(3)
    
    with comp_col1:
        st.markdown("**📊 Model Fit**")
        r2_comp = pd.DataFrame({
            'Metric': ['R²', 'Adj. R²'],
            'Bowl Count': [f"{ols_model_bowls.rsquared:.4f}", f"{ols_model_bowls.rsquared_adj:.4f}"],
            'Order Count': [f"{ols_model_orders.rsquared:.4f}", f"{ols_model_orders.rsquared_adj:.4f}"]
        })
        st.dataframe(r2_comp, hide_index=True, use_container_width=True)
    
    with comp_col2:
        st.markdown("**📉 Prediction Error**")
        error_comp = pd.DataFrame({
            'Metric': ['MAE', 'MAPE'],
            'Bowl Count': [f"{mae_bowls:.2f} bowls", f"{mape_bowls:.2f}%"],
            'Order Count': [f"{mae_orders:.2f} orders", f"{mape_orders:.2f}%"]
        })
        st.dataframe(error_comp, hide_index=True, use_container_width=True)
    
    with comp_col3:
        st.markdown("**🏆 Winner**")
        if ols_model_orders.rsquared > ols_model_bowls.rsquared:
            st.success("Order Count")
            diff = ((ols_model_orders.rsquared - ols_model_bowls.rsquared) / ols_model_bowls.rsquared * 100)
            st.caption(f"+{diff:.1f}% R² improvement")
        else:
            st.success("Bowl Count")
            diff = ((ols_model_bowls.rsquared - ols_model_orders.rsquared) / ols_model_orders.rsquared * 100)
            st.caption(f"+{diff:.1f}% R² improvement")
    
    # Key insights
    st.markdown("**💡 Key Insights:**")
    if ols_model_orders.rsquared > ols_model_bowls.rsquared:
        st.info("""
        ✅ **Order Count shows stronger predictive power**, suggesting that:
        - Customer visit patterns are more predictable than bowl quantities
        - Navy Base paydays and school holidays primarily drive **foot traffic**, not party size
        - Transaction count is less noisy (not affected by large family orders)
        """)
    else:
        st.info("""
        ✅ **Bowl Count shows stronger predictive power**, suggesting that:
        - Quantity per order varies systematically with our features
        - Paydays and holidays affect both visit frequency AND party size
        - Families order more bowls during favorable conditions
        """)
    
    st.divider()
    
    # --- MODEL PERFORMANCE SUMMARY (Bowl Count Details) ---
    st.subheader("📊 Model A Performance: Bowl Count (Detailed View)")
    
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
        st.metric("🌡️ Temp", f"{ols_model.params['Temp_Centered']:.2f}/°F")
        st.metric("📅 Weekend", f"+{ols_model.params['is_weekend']:.1f}")
        st.metric("🌧️ Rain", f"{ols_model.params['is_rain']:+.1f}")
        st.metric("❄️ Snow", f"{ols_model.params['is_snow']:+.1f}")
    
    with stat_col3:
        st.markdown("**Payday Effects**")
        st.metric("📆 Fri", f"+{ols_model.params['is_weekly_friday']:.1f}",
                 help="General Friday payday")
        st.metric("💰 15th/Last", f"+{ols_model.params['is_semi_monthly']:.1f}",
                 help="Semi-monthly paydays")
        st.metric("💰×📅", f"+{ols_model.params['is_semi_monthly_weekend']:.1f}",
                 help="Semi-monthly × Weekend")
    
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
            (ols_model.params['Temp_Centered'] * recent_df['Temp_Centered']) +
            (ols_model.params['is_weekend'] * recent_df['is_weekend']) +
            (ols_model.params['is_rain'] * recent_df['is_rain']) +
            (ols_model.params['is_snow'] * recent_df['is_snow']) +
            (ols_model.params['is_federal_payday'] * recent_df['is_federal_payday']) +
            (ols_model.params['is_payday_weekend'] * recent_df['is_payday_weekend']) +
            (ols_model.params['is_weekly_friday'] * recent_df['is_weekly_friday']) +
            (ols_model.params['is_semi_monthly'] * recent_df['is_semi_monthly']) +
            (ols_model.params['is_semi_monthly_weekend'] * recent_df['is_semi_monthly_weekend']) +
            (ols_model.params['is_2024'] * recent_df['is_2024']) +
            (ols_model.params['is_2025'] * recent_df['is_2025']) +
            (ols_model.params['is_2026_friday'] * recent_df['is_2026_friday']) +
            (ols_model.params['is_school_holiday'] * recent_df['is_school_holiday'])
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
        'const': f'Intercept (Baseline: 2026, Tue-Thu, Clear, {mean_temp:.1f}°F, Regular school day)',
        'Temp_Centered': 'Temperature (centered)',
        'is_weekend': 'Weekend (Sat/Sun only)',
        'is_rain': 'Rain/Mixed (vs Clear)',
        'is_snow': 'Snow/Flurries/Heavy (vs Clear)',
        'is_federal_payday': 'Federal Payday Friday (bi-weekly, NSA)',
        'is_payday_weekend': 'Payday Weekend (Sat/Sun after federal payday)',
        'is_weekly_friday': 'Weekly Friday (General Payday)',
        'is_semi_monthly': 'Semi-Monthly Payday (15th & Last Day)',
        'is_semi_monthly_weekend': 'Semi-Monthly × Weekend (interaction)',
        'is_2024': 'Year 2024 (vs 2026 baseline)',
        'is_2025': 'Year 2025 (vs 2026 baseline)',
        'is_2026_friday': '2026 × Friday (Navy base effect strengthening)',
        'is_school_holiday': 'School Holiday / Break (families have time off)'
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
    
    st.caption("📊 Baseline relationships shown. Model with year controls includes 12 features: Temp, Weekend(Sat/Sun), Rain (vs Clear), Snow (vs Clear), Federal Payday, Payday Weekend, Weekly Friday, Semi-Monthly (15th/Last), Semi-Monthly×Weekend, Year 2024, Year 2025, and 2026×Friday (Navy base strengthening).")

except Exception as e:
    st.error(f"Model Diagnostics Error: {e}")
