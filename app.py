import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import pytz

st.set_page_config(page_title="Daily Insights", layout="wide")

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
    
    return df, weather

try:
    sales_df, weather_df = load_all_data()
    
    # Process volume data specifically for Pho items
    pho_only = sales_df[sales_df['Item'].str.contains('Pho', case=False, na=False)].copy()
    daily_pho = pho_only.groupby('Date')['Qty'].sum().reset_index()
    daily_pho.columns = ['Date', 'Bowls_Sold']
    
    # Calculate Total Orders (transaction count) per day for ALL items
    daily_orders = sales_df.groupby('Date')['Transaction ID'].nunique().reset_index()
    daily_orders.columns = ['Date', 'Total_Orders']
    
    weather_df['Precip_Type'] = weather_df['Precip_Type'].replace('None', 'Clear').fillna('Clear')
    merged = pd.merge(weather_df, daily_pho, on='Date', how='left').fillna(0)
    merged = pd.merge(merged, daily_orders, on='Date', how='left').fillna(0)
    merged['Day_of_Week'] = pd.to_datetime(merged['Date']).dt.day_name()
    
    # --- FEATURE ENGINEERING ---
    
    # Weekend binary (Saturday and Sunday ONLY - Friday is separate for base traffic)
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Saturday', 'Sunday']).astype(int)
    
    # Precipitation type binaries (3 categories)
    merged['is_clear'] = (merged['Precip_Type'].isin(['None', 'Clear'])).astype(int)
    merged['is_rain'] = (merged['Precip_Type'].isin(['Rain', 'Mixed'])).astype(int)
    merged['is_snow'] = (merged['Precip_Type'].isin(['Snow', 'Flurries', 'Heavy Snow'])).astype(int)
    
    # Naval Base (NSA Mechanicsburg) Traffic Effects
    merged['Date_dt'] = pd.to_datetime(merged['Date'])
    
    # 1. Federal Payday: Bi-weekly Fridays (2025 + 2026)
    # Generate all federal payday Fridays for 2025-2026
    # Start from a known payday (Jan 9, 2026) and go backwards/forwards
    federal_payday_anchor = pd.Timestamp('2026-01-09')
    
    # Generate payday dates going backwards to cover 2025
    federal_paydays = []
    current_date = federal_payday_anchor
    
    # Go backwards to start of 2025
    while current_date >= pd.Timestamp('2025-01-01'):
        federal_paydays.append(current_date)
        current_date = current_date - pd.Timedelta(days=14)
    
    # Go forwards to end of 2026
    current_date = federal_payday_anchor + pd.Timedelta(days=14)
    while current_date <= pd.Timestamp('2026-12-31'):
        federal_paydays.append(current_date)
        current_date = current_date + pd.Timedelta(days=14)
    
    merged['is_federal_payday'] = merged['Date_dt'].isin(federal_paydays).astype(int)
    
    # 2. Payday Weekend: Saturday/Sunday after federal payday Friday
    # Shift federal payday forward by 1 and 2 days to capture weekend effect
    merged['is_payday_weekend'] = 0
    payday_dates = merged[merged['is_federal_payday'] == 1]['Date_dt']
    for payday_date in payday_dates:
        # Mark the Saturday (day after payday Friday)
        merged.loc[merged['Date_dt'] == payday_date + pd.Timedelta(days=1), 'is_payday_weekend'] = 1
        # Mark the Sunday (2 days after payday Friday)
        merged.loc[merged['Date_dt'] == payday_date + pd.Timedelta(days=2), 'is_payday_weekend'] = 1
    
    # 3. Friday Base Traffic (NSA Mechanicsburg lunch rush)
    merged['is_friday_base'] = (merged['Day_of_Week'] == 'Friday').astype(int)
    
    # --- PRIVATE SECTOR PAYDAY EFFECTS ---
    # Every Friday = General payday for many local workers
    merged['is_weekly_friday'] = (merged['Day_of_Week'] == 'Friday').astype(int)
    
    # Semi-monthly paydays: 15th and last day of each month
    merged['is_semi_monthly'] = 0
    merged.loc[merged['Date_dt'].dt.day == 15, 'is_semi_monthly'] = 1
    merged.loc[merged['Date_dt'].dt.day == merged['Date_dt'].dt.days_in_month, 'is_semi_monthly'] = 1
    
    # Interaction: Semi-monthly payday × Weekend (15th/month-end on Fri-Sun = massive weekend)
    merged['is_semi_monthly_weekend'] = (merged['is_semi_monthly'] * merged['is_weekend']).astype(int)
    
    # --- YEAR DUMMIES (Capture Model Drift) ---
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
    
    # Filter for active days only (Exclude Mondays and zero sales)
    model_df = merged[
        (merged['Day_of_Week'] != 'Monday') & 
        (merged['Bowls_Sold'] > 0)
    ].copy()
    
    # Center temperature variable (subtract mean)
    mean_temp = model_df['Temp_High'].mean()
    model_df['Temp_Centered'] = model_df['Temp_High'] - mean_temp

    st.title("🍜 Daily Insights")
    
    # Sidebar: Shadow Demand Explanation
    with st.sidebar:
        st.markdown("### 📊 About Capacity Planning")
        st.markdown("""
        **What is "Shadow Demand"?**
        
        Our model predicts customer *intent* to visit, not just realized sales. 
        
        With **10 tables** and typical turnover, dine-in capacity is ~**80 bowls/day**.
        
        When predictions exceed this:
        - 🚨 You're hitting physical constraints
        - 💰 Lost revenue opportunity without takeout
        - 📈 High demand = optimize for speed & takeout
        
        **Capacity Alert Zones:**
        - 🟢 < 68 bowls: Comfortable capacity
        - 🟡 68-80 bowls: High demand, manageable
        - 🔴 > 80 bowls: Peak alert - prioritize takeout
        """)
    
    # Show data range
    date_min = merged['Date'].min()
    date_max = merged['Date'].max()
    total_days = len(model_df)
    total_closed = len(merged[merged['Bowls_Sold'] == 0])
    st.info(f"📊 Analyzing data from **{date_min}** to **{date_max}** • **{total_days}** operating days • **{total_closed}** closed days excluded (Mondays, holidays, weather closures)")

    # --- MODEL A: BOWL COUNT (Current Model) ---
    # Bowls_Sold ~ Temp + Weekend + Rain + Snow + Federal_Payday + Payday_Weekend + 
    #              Weekly_Friday + Semi_Monthly + Semi_Monthly×Weekend + Year_2024 + Year_2025 + 
    #              2026×Friday + School_Holiday
    # Note: is_clear is baseline for precipitation, 2026 is baseline for year
    X = model_df[['Temp_Centered', 'is_weekend', 'is_rain', 'is_snow', 'is_federal_payday', 
                  'is_payday_weekend', 'is_weekly_friday', 'is_semi_monthly', 'is_semi_monthly_weekend',
                  'is_2024', 'is_2025', 'is_2026_friday', 'is_school_holiday']]
    X = sm.add_constant(X) 
    y_bowls = model_df['Bowls_Sold']
    ols_model_bowls = sm.OLS(y_bowls, X).fit()
    
    # Calculate predictions and errors for Model A
    model_df['Predicted_Bowls'] = ols_model_bowls.predict(X)
    model_df['Error_Bowls'] = model_df['Bowls_Sold'] - model_df['Predicted_Bowls']
    model_df['Error_Pct_Bowls'] = (model_df['Error_Bowls'] / model_df['Bowls_Sold'] * 100).abs()
    mae_bowls = model_df['Error_Bowls'].abs().mean()
    mape_bowls = model_df['Error_Pct_Bowls'].mean()
    
    # --- MODEL B: ORDER COUNT (Transaction Count) ---
    # Total_Orders ~ Same features as Model A
    y_orders = model_df['Total_Orders']
    ols_model_orders = sm.OLS(y_orders, X).fit()
    
    # Calculate predictions and errors for Model B
    model_df['Predicted_Orders'] = ols_model_orders.predict(X)
    model_df['Error_Orders'] = model_df['Total_Orders'] - model_df['Predicted_Orders']
    model_df['Error_Pct_Orders'] = (model_df['Error_Orders'] / model_df['Total_Orders'] * 100).abs()
    mae_orders = model_df['Error_Orders'].abs().mean()
    mape_orders = model_df['Error_Pct_Orders'].mean()
    
    # Use Model A (bowls) for predictions (keeping existing functionality)
    ols_model = ols_model_bowls
    mae = mae_bowls
    
    # --- MODEL COMPARISON: BOWLS VS ORDERS ---
    st.header("📊 Model Comparison: Bowl Count vs Order Count")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🍜 Model A: Bowl Count")
        st.metric("R²", f"{ols_model_bowls.rsquared:.4f}")
        st.metric("Adjusted R²", f"{ols_model_bowls.rsquared_adj:.4f}")
        st.metric("MAE", f"{mae_bowls:.2f} bowls")
        st.metric("MAPE", f"{mape_bowls:.2f}%")
        st.caption("Predicts total Pho bowls sold per day")
    
    with col2:
        st.subheader("📋 Model B: Order Count")
        st.metric("R²", f"{ols_model_orders.rsquared:.4f}")
        st.metric("Adjusted R²", f"{ols_model_orders.rsquared_adj:.4f}")
        st.metric("MAE", f"{mae_orders:.2f} orders")
        st.metric("MAPE", f"{mape_orders:.2f}%")
        st.caption("Predicts total transactions per day")
    
    # Comparison insights
    if ols_model_orders.rsquared > ols_model_bowls.rsquared:
        winner = "Order Count"
        diff = ((ols_model_orders.rsquared - ols_model_bowls.rsquared) / ols_model_bowls.rsquared * 100)
        st.success(f"✅ **{winner}** shows stronger predictive power ({diff:.1f}% higher R²)")
    else:
        winner = "Bowl Count"
        diff = ((ols_model_bowls.rsquared - ols_model_orders.rsquared) / ols_model_orders.rsquared * 100)
        st.success(f"✅ **{winner}** shows stronger predictive power ({diff:.1f}% higher R²)")
    
    if mape_orders < mape_bowls:
        st.info(f"📉 Order Count has {((mape_bowls - mape_orders) / mape_bowls * 100):.1f}% lower prediction error (MAPE)")
    else:
        st.info(f"📉 Bowl Count has {((mape_orders - mape_bowls) / mape_orders * 100):.1f}% lower prediction error (MAPE)")
    
    st.divider()

    # --- TOMORROW'S PREDICTION (Top Section) ---
    st.header("📅 Tomorrow's Forecast")
    
    # Center the forecast section
    left_pad, forecast_col, right_pad = st.columns([1, 3, 1])
    
    with forecast_col:
        st.subheader("Enter Tomorrow's Forecast")
        tomorrow_temp = st.number_input("Temperature (°F)", min_value=0, max_value=100, value=35, step=1)
        
        st.markdown("**🌤️ Weather & Day Type**")
        col_a, col_b = st.columns(2)
        with col_a:
            tomorrow_is_weekend = st.checkbox("Weekend (Sat/Sun)", value=False)
            tomorrow_is_rain = st.checkbox("Rain/Mixed", value=False)
        with col_b:
            tomorrow_is_snow = st.checkbox("Snow/Flurries", value=False)
        
        st.markdown("**💰 Payday Events**")
        col_c, col_d = st.columns(2)
        with col_c:
            tomorrow_is_weekly_friday = st.checkbox("Friday (General Payday)", value=False)
            tomorrow_is_semi_monthly = st.checkbox("Semi-Monthly (15th or Last Day)", value=False)
        with col_d:
            tomorrow_is_fed_payday = st.checkbox("Federal Payday Friday", value=False, help="Bi-weekly NSA")
            tomorrow_is_payday_wknd = st.checkbox("Payday Weekend (Sat/Sun after)", value=False)
        
        st.markdown("**🎓 School Holiday**")
        tomorrow_is_school_holiday = st.checkbox("School Holiday / Break", value=False,
                                                  help="Winter/Spring/Thanksgiving breaks, MLK, Presidents' Day, Memorial Day, Labor Day")
        
        # Center tomorrow's temperature
        tomorrow_temp_centered = tomorrow_temp - mean_temp
        
        # Interactions
        tomorrow_semi_wknd = (1 if tomorrow_is_semi_monthly else 0) * (1 if tomorrow_is_weekend else 0)
        # Tomorrow is assumed to be 2026 (is_2024=0, is_2025=0)
        tomorrow_2026_friday = 1 if tomorrow_is_weekly_friday else 0
        
        tomorrow_pred = (ols_model.params['const'] + 
                        (ols_model.params['Temp_Centered'] * tomorrow_temp_centered) + 
                        (ols_model.params['is_weekend'] * (1 if tomorrow_is_weekend else 0)) +
                        (ols_model.params['is_rain'] * (1 if tomorrow_is_rain else 0)) +
                        (ols_model.params['is_snow'] * (1 if tomorrow_is_snow else 0)) +
                        (ols_model.params['is_federal_payday'] * (1 if tomorrow_is_fed_payday else 0)) +
                        (ols_model.params['is_payday_weekend'] * (1 if tomorrow_is_payday_wknd else 0)) +
                        (ols_model.params['is_weekly_friday'] * (1 if tomorrow_is_weekly_friday else 0)) +
                        (ols_model.params['is_semi_monthly'] * (1 if tomorrow_is_semi_monthly else 0)) +
                        (ols_model.params['is_semi_monthly_weekend'] * tomorrow_semi_wknd) +
                        (ols_model.params['is_2024'] * 0) +  # Tomorrow is 2026, not 2024
                        (ols_model.params['is_2025'] * 0) +  # Tomorrow is 2026, not 2025
                        (ols_model.params['is_2026_friday'] * tomorrow_2026_friday) +
                        (ols_model.params['is_school_holiday'] * (1 if tomorrow_is_school_holiday else 0)))
        
        st.metric("🔮 Predicted Bowls for Tomorrow", 
                 f"{int(max(0, tomorrow_pred))} Bowls",
                 help=f"Model with school holiday effect (13 features, Mean temp: {mean_temp:.1f}°F)")
        
        # --- CAPACITY CONSTRAINT ANALYSIS ---
        MAX_DINE_IN_CAPACITY = 80  # Based on 10 tables, ~3 turns/day, 2.5 bowls/table avg
        predicted_bowls = int(max(0, tomorrow_pred))
        
        if predicted_bowls > MAX_DINE_IN_CAPACITY:
            capacity_diff = predicted_bowls - MAX_DINE_IN_CAPACITY
            st.warning(f"""
            ⚠️ **Peak Demand Alert!**
            
            Predicted demand is **{capacity_diff} bowls above seating capacity** ({MAX_DINE_IN_CAPACITY} bowls).
            
            **Operational Recommendations:**
            - Prioritize takeout orders to capture overflow demand
            - Pre-pack garnish kits (herbs, lime, jalapeños, bean sprouts)
            - Consider prep staff scheduling for high-volume service
            - Ensure adequate to-go containers in stock
            
            💡 *This represents "Shadow Demand" - potential sales lost without takeout optimization.*
            """)
        elif predicted_bowls > MAX_DINE_IN_CAPACITY * 0.85:
            # 85-100% capacity - high but manageable
            st.info(f"""
            📊 **High Demand Expected**
            
            Predicted demand is **{predicted_bowls} bowls** (~{100*predicted_bowls/MAX_DINE_IN_CAPACITY:.0f}% of capacity).
            
            Operating near capacity. Takeout orders will help maximize revenue.
            """)
        else:
            # Comfortable capacity
            st.success(f"""
            ✅ **Demand Within Capacity**
            
            Predicted demand is **{predicted_bowls} bowls** (~{100*predicted_bowls/MAX_DINE_IN_CAPACITY:.0f}% of capacity).
            
            Comfortable service level for 10-table dine-in capacity.
            """)
        
        st.info("💡 For detailed model performance metrics and diagnostics, see the **Model Diagnostics** page in the sidebar.")

    st.divider()
    
    # --- LINE CHART: Pho Bowls vs Daily High Temperature ---
    st.subheader('📈 Pho Bowls Sold vs Daily High Temperature (Excluding Closed Days)')
    chart_df = merged.sort_values('Date').copy()
    chart_df['Date'] = pd.to_datetime(chart_df['Date'])
    
    # Filter out closed days (Mondays and any days with zero sales)
    chart_df = chart_df[
        (chart_df['Day_of_Week'] != 'Monday') & 
        (chart_df['Bowls_Sold'] > 0)
    ]
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=chart_df['Date'], y=chart_df['Bowls_Sold'], name='Pho Bowls Sold', line=dict(color='#2E7D32', width=2), mode='lines+markers'))
    fig_line.add_trace(go.Scatter(x=chart_df['Date'], y=chart_df['Temp_High'], name='Daily High (°F)', line=dict(color='#D84315', width=2), mode='lines+markers', yaxis='y2'))
    fig_line.update_layout(
        xaxis_title='Date',
        yaxis=dict(title='Pho Bowls Sold', side='left'),
        yaxis2=dict(title='Temperature (°F)', side='right', overlaying='y', range=[0, max(chart_df['Temp_High']) * 1.1] if len(chart_df) > 0 else [0, 100]),
        template='simple_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig_line, use_container_width=True)
    
    st.divider()
    # --- TOP 10 DISHES SOLD ---
    st.subheader("🍽️ Top 10 Dishes Sold")
    top_dishes = sales_df.groupby('Item')['Qty'].sum().reset_index()
    top_dishes.columns = ['Dish', 'Quantity Sold']
    top_dishes = top_dishes.sort_values(by='Quantity Sold', ascending=False).head(10)
    top_dishes['Quantity Sold'] = top_dishes['Quantity Sold'].astype(int)
    st.dataframe(top_dishes, use_container_width=True, hide_index=True)

    st.divider()

    # --- TOP 10 REGULARS (LAST MONTH ONLY) ---
    st.subheader("👥 Top 10 Regulars - January 2026 Leaderboard")
    
    # Filter for January 2026 only
    jan_2026_sales = sales_df[
        (pd.to_datetime(sales_df['Date']).dt.year == 2026) & 
        (pd.to_datetime(sales_df['Date']).dt.month == 1)
    ]
    
    loyalty_data = jan_2026_sales[jan_2026_sales['Customer Name'].notna()]
    if not loyalty_data.empty:
        top_loyalty = loyalty_data.groupby('Customer Name').agg({'Transaction ID': 'nunique', 'Gross Sales': 'sum'}).reset_index()
        top_loyalty.columns = ['Customer Name', 'Total Visits', 'Total Spend']
        top_loyalty = top_loyalty.sort_values(by=['Total Visits', 'Total Spend'], ascending=False).head(10)
        
        # Anonymize names to initials (except names with commas - already anonymous)
        def anonymize_name(name):
            if ',' in name:
                return name  # Keep names with commas as-is (already anonymous)
            parts = str(name).split()
            if len(parts) >= 2:
                return f"{parts[0][0]}.{parts[-1][0]}."  # First Initial + Last Initial
            elif len(parts) == 1:
                return f"{parts[0][0]}."  # Just first initial
            else:
                return name
        
        top_loyalty['Customer Name'] = top_loyalty['Customer Name'].apply(anonymize_name)
        
        st.dataframe(top_loyalty.style.format({'Total Spend': '${:,.2f}'}), use_container_width=True)
        st.caption("🔒 Names anonymized for privacy (initials only)")
    else:
        st.info("No customer data available for January 2026.")

except Exception as e:
    st.error(f"Dashboard Error: {e}")