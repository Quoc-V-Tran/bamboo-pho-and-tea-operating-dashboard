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
    # Load and adjust timezone - combining 2025 and 2026 data
    pt_tz, et_tz = pytz.timezone('US/Pacific'), pytz.timezone('US/Eastern')
    
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
    df = pd.concat([df_2025, df_jan_2026, df_feb_2026], ignore_index=True)
    
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
    weather = pd.concat([weather_2025, weather_jan_2026, weather_feb_2026], ignore_index=True)
    
    return df, weather

try:
    sales_df, weather_df = load_all_data()
    
    # Process volume data specifically for Pho items
    pho_only = sales_df[sales_df['Item'].str.contains('Pho', case=False, na=False)].copy()
    daily_pho = pho_only.groupby('Date')['Qty'].sum().reset_index()
    daily_pho.columns = ['Date', 'Bowls_Sold']
    
    weather_df['Precip_Type'] = weather_df['Precip_Type'].replace('None', 'Clear').fillna('Clear')
    merged = pd.merge(weather_df, daily_pho, on='Date', how='left').fillna(0)
    merged['Day_of_Week'] = pd.to_datetime(merged['Date']).dt.day_name()
    
    # --- FEATURE ENGINEERING ---
    
    # Weekend binary (Saturday and Sunday ONLY - Friday is separate for base traffic)
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Saturday', 'Sunday']).astype(int)
    
    # Mixed precipitation dummy
    merged['is_mixed_precip'] = (merged['Precip_Type'] == 'Mixed').astype(int)
    
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
    
    # --- HOLIDAY PROXIMITY EFFECTS ---
    # Define all major holidays for 2025-2026
    major_holidays = [
        # 2025 Holidays
        pd.Timestamp('2025-01-01'),  # New Year's
        pd.Timestamp('2025-01-29'),  # Lunar New Year
        pd.Timestamp('2025-02-09'),  # Super Bowl Sunday
        pd.Timestamp('2025-02-14'),  # Valentine's Day
        pd.Timestamp('2025-04-20'),  # Easter
        pd.Timestamp('2025-05-26'),  # Memorial Day
        pd.Timestamp('2025-07-04'),  # July 4th
        pd.Timestamp('2025-09-01'),  # Labor Day
        pd.Timestamp('2025-11-27'),  # Thanksgiving
        pd.Timestamp('2025-12-25'),  # Christmas
        # 2026 Holidays
        pd.Timestamp('2026-01-01'),  # New Year's
        pd.Timestamp('2026-02-17'),  # Lunar New Year
        pd.Timestamp('2026-02-08'),  # Super Bowl Sunday
        pd.Timestamp('2026-02-14'),  # Valentine's Day
        pd.Timestamp('2026-04-05'),  # Easter
        pd.Timestamp('2026-05-25'),  # Memorial Day
        pd.Timestamp('2026-07-04'),  # July 4th
        pd.Timestamp('2026-09-07'),  # Labor Day
        pd.Timestamp('2026-11-26'),  # Thanksgiving
        pd.Timestamp('2026-12-25'),  # Christmas
    ]
    
    # Pre-Holiday: 1-2 days before major holidays
    merged['is_pre_holiday'] = 0
    for holiday in major_holidays:
        merged.loc[merged['Date_dt'].isin([holiday - pd.Timedelta(days=1), holiday - pd.Timedelta(days=2)]), 'is_pre_holiday'] = 1
    
    # Post-Holiday: 1-2 days after major holidays
    merged['is_post_holiday'] = 0
    for holiday in major_holidays:
        merged.loc[merged['Date_dt'].isin([holiday + pd.Timedelta(days=1), holiday + pd.Timedelta(days=2)]), 'is_post_holiday'] = 1
    
    # Valentine's Period: Feb 13-15 (massive pho window)
    merged['is_valentines_period'] = merged['Date_dt'].isin([
        pd.Timestamp('2025-02-13'), pd.Timestamp('2025-02-14'), pd.Timestamp('2025-02-15'),
        pd.Timestamp('2026-02-13'), pd.Timestamp('2026-02-14'), pd.Timestamp('2026-02-15')
    ]).astype(int)
    
    # Lunar New Year 3-day window: 2025 (Jan 29-31), 2026 (Feb 17-19)
    merged['is_lunar_new_year'] = merged['Date_dt'].isin([
        pd.Timestamp('2025-01-29'), pd.Timestamp('2025-01-30'), pd.Timestamp('2025-01-31'),
        pd.Timestamp('2026-02-17'), pd.Timestamp('2026-02-18'), pd.Timestamp('2026-02-19')
    ]).astype(int)
    
    # Interaction: Pre-Holiday × Friday ('I'm not cooking before the long weekend')
    merged['is_pre_holiday_friday'] = (merged['is_pre_holiday'] * merged['is_friday_base']).astype(int)
    
    # --- COMPETITOR CLOSURE EFFECTS (Overflow Demand) ---
    # Based on field research of Greater Harrisburg competitor schedules
    merged['little_saigon_closed'] = (merged['Day_of_Week'] == 'Tuesday').astype(int)
    merged['pho_kims_closed'] = (merged['Day_of_Week'] == 'Sunday').astype(int)
    merged['pho_la_vie_closed'] = (merged['Day_of_Week'] == 'Monday').astype(int)
    merged['la_squared_closed'] = (merged['Day_of_Week'] == 'Sunday').astype(int)
    
    # Aggregate Overflow Index: How many competitors are closed today?
    merged['competitor_overflow_index'] = (
        merged['little_saigon_closed'] + 
        merged['pho_kims_closed'] + 
        merged['pho_la_vie_closed'] + 
        merged['la_squared_closed']
    )
    
    # Interaction: Overflow × Weekend (Sundays have 2 major competitors closed)
    merged['overflow_weekend'] = (merged['competitor_overflow_index'] * merged['is_weekend']).astype(int)
    
    # Filter for active days only (Exclude Mondays AND any days with zero sales)
    model_df = merged[
        (merged['Day_of_Week'] != 'Monday') & 
        (merged['Bowls_Sold'] > 0)
    ].copy()
    
    # Center temperature variable (subtract mean)
    mean_temp = model_df['Temp_High'].mean()
    model_df['Temp_Centered'] = model_df['Temp_High'] - mean_temp

    st.title("🍜 Daily Insights")
    
    # Show data range
    date_min = merged['Date'].min()
    date_max = merged['Date'].max()
    total_days = len(model_df)
    total_closed = len(merged[merged['Bowls_Sold'] == 0])
    st.info(f"📊 Analyzing data from **{date_min}** to **{date_max}** • **{total_days}** operating days • **{total_closed}** closed days excluded (Mondays, holidays, weather closures)")

    # --- BUILD COMPREHENSIVE MODEL WITH BASE + HOLIDAY + COMPETITOR EFFECTS ---
    # Bowls_Sold ~ Temp + Weekend(Sat/Sun) + Mixed + Federal_Payday + Payday_Weekend + 
    #              Friday_Base + Pre_Holiday + Post_Holiday + Valentines + Lunar_NY + 
    #              Pre_Holiday×Friday + Competitor_Overflow + Overflow×Weekend
    X = model_df[['Temp_Centered', 'is_weekend', 'is_mixed_precip', 'is_federal_payday', 
                  'is_payday_weekend', 'is_friday_base', 'is_pre_holiday', 'is_post_holiday',
                  'is_valentines_period', 'is_lunar_new_year', 'is_pre_holiday_friday',
                  'competitor_overflow_index', 'overflow_weekend']]
    X = sm.add_constant(X) 
    y = model_df['Bowls_Sold']
    ols_model = sm.OLS(y, X).fit()
    
    # Calculate predictions for all historical data
    model_df['Predicted'] = ols_model.predict(X)
    model_df['Error'] = model_df['Bowls_Sold'] - model_df['Predicted']
    model_df['Error_Pct'] = (model_df['Error'] / model_df['Bowls_Sold'] * 100).abs()

    # --- TOMORROW'S PREDICTION (Top Section) ---
    st.header("📅 Tomorrow's Forecast")
    
    pred_col1, pred_col2 = st.columns([1, 2])
    
    with pred_col1:
        st.subheader("Enter Tomorrow's Forecast")
        tomorrow_temp = st.number_input("Temperature (°F)", min_value=0, max_value=100, value=35, step=1)
        
        col_a, col_b = st.columns(2)
        with col_a:
            tomorrow_is_weekend = st.checkbox("Weekend (Sat/Sun)", value=False)
            tomorrow_is_mixed = st.checkbox("Mixed Precip", value=False)
        with col_b:
            tomorrow_is_friday_base = st.checkbox("Friday", value=False, help="Base traffic")
            tomorrow_is_fed_payday = st.checkbox("Fed Payday Fri", value=False, help="Bi-weekly")
        
        st.markdown("**🎉 Holiday Effects**")
        col_c, col_d = st.columns(2)
        with col_c:
            tomorrow_is_pre_holiday = st.checkbox("Pre-Holiday (1-2 days before)", value=False)
            tomorrow_is_post_holiday = st.checkbox("Post-Holiday (1-2 days after)", value=False)
        with col_d:
            tomorrow_is_valentines = st.checkbox("Valentine's Period (Feb 13-15)", value=False)
            tomorrow_is_lunar_ny = st.checkbox("Lunar New Year (3-day window)", value=False)
        
        tomorrow_is_payday_wknd = st.checkbox("Payday Weekend (Sat/Sun after fed payday)", value=False)
        
        st.markdown("**🏪 Competitor Closures (Overflow Demand)**")
        col_e, col_f = st.columns(2)
        with col_e:
            tomorrow_little_saigon = st.checkbox("Little Saigon closed (Tue)", value=False)
            tomorrow_pho_kims = st.checkbox("Pho Kim's closed (Sun)", value=False)
        with col_f:
            tomorrow_pho_la_vie = st.checkbox("Pho La Vie closed (Mon)", value=False)
            tomorrow_la_squared = st.checkbox("The LA Squared closed (Sun)", value=False)
        
        # Calculate competitor overflow index
        tomorrow_overflow = (
            (1 if tomorrow_little_saigon else 0) +
            (1 if tomorrow_pho_kims else 0) +
            (1 if tomorrow_pho_la_vie else 0) +
            (1 if tomorrow_la_squared else 0)
        )
        
        # Center tomorrow's temperature
        tomorrow_temp_centered = tomorrow_temp - mean_temp
        
        # Interactions
        tomorrow_pre_hol_fri = (1 if tomorrow_is_pre_holiday else 0) * (1 if tomorrow_is_friday_base else 0)
        tomorrow_overflow_wknd = tomorrow_overflow * (1 if tomorrow_is_weekend else 0)
        
        tomorrow_pred = (ols_model.params['const'] + 
                        (ols_model.params['Temp_Centered'] * tomorrow_temp_centered) + 
                        (ols_model.params['is_weekend'] * (1 if tomorrow_is_weekend else 0)) +
                        (ols_model.params['is_mixed_precip'] * (1 if tomorrow_is_mixed else 0)) +
                        (ols_model.params['is_federal_payday'] * (1 if tomorrow_is_fed_payday else 0)) +
                        (ols_model.params['is_payday_weekend'] * (1 if tomorrow_is_payday_wknd else 0)) +
                        (ols_model.params['is_friday_base'] * (1 if tomorrow_is_friday_base else 0)) +
                        (ols_model.params['is_pre_holiday'] * (1 if tomorrow_is_pre_holiday else 0)) +
                        (ols_model.params['is_post_holiday'] * (1 if tomorrow_is_post_holiday else 0)) +
                        (ols_model.params['is_valentines_period'] * (1 if tomorrow_is_valentines else 0)) +
                        (ols_model.params['is_lunar_new_year'] * (1 if tomorrow_is_lunar_ny else 0)) +
                        (ols_model.params['is_pre_holiday_friday'] * tomorrow_pre_hol_fri) +
                        (ols_model.params['competitor_overflow_index'] * tomorrow_overflow) +
                        (ols_model.params['overflow_weekend'] * tomorrow_overflow_wknd))
        
        if tomorrow_overflow > 0:
            st.info(f"💡 {tomorrow_overflow} competitor(s) closed → Overflow demand expected!")
        
        st.metric("🔮 Predicted Bowls for Tomorrow", 
                 f"{int(max(0, tomorrow_pred))} Bowls",
                 help=f"Comprehensive model with 13 features (Mean temp: {mean_temp:.1f}°F)")
    
    with pred_col2:
        st.subheader("📊 Model Performance")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            avg_bowls = model_df['Bowls_Sold'].mean()
            st.metric("Avg Daily Bowls", f"{avg_bowls:.1f}")
            st.metric("Model R²", f"{ols_model.rsquared:.3f}",
                     help="Variance explained")
            st.metric("Adj. R²", f"{ols_model.rsquared_adj:.3f}")
            avg_error_pct = model_df['Error_Pct'].mean()
            st.metric("Avg Error %", f"{avg_error_pct:.1f}%")
        
        with stat_col2:
            st.markdown("**Core**")
            st.metric("🌡️ Temp", f"{ols_model.params['Temp_Centered']:.2f}/°F")
            st.metric("📅 Weekend", f"+{ols_model.params['is_weekend']:.1f}")
            st.metric("🏛️ Friday", f"+{ols_model.params['is_friday_base']:.1f}")
        
        with stat_col3:
            st.markdown("**Holidays**")
            st.metric("🎉 Pre-Hol", f"{ols_model.params['is_pre_holiday']:+.1f}")
            st.metric("💝 V-Day", f"{ols_model.params['is_valentines_period']:+.1f}")
            st.metric("🧧 Lunar", f"{ols_model.params['is_lunar_new_year']:+.1f}")
        
        with stat_col4:
            st.markdown("**Overflow**")
            st.metric("🏪 Index", f"+{ols_model.params['competitor_overflow_index']:.1f}",
                     help="Per competitor closed")
            st.metric("🏪×📅 Wknd", f"+{ols_model.params['overflow_weekend']:.1f}",
                     help="Overflow on weekends")
            
            # Calculate p-value significance
            p_overflow = ols_model.pvalues['competitor_overflow_index']
            sig = "***" if p_overflow < 0.001 else "**" if p_overflow < 0.01 else "*" if p_overflow < 0.05 else "ns"
            st.caption(f"Overflow p={p_overflow:.4f} {sig}")

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
        st.markdown("### Model Performance")
        
        # Error distribution
        within_5pct = (model_df['Error_Pct'] <= 5).sum()
        within_10pct = (model_df['Error_Pct'] <= 10).sum()
        within_20pct = (model_df['Error_Pct'] <= 20).sum()
        total = len(model_df)
        
        st.metric("Within 5% Error", f"{within_5pct} days ({100*within_5pct/total:.0f}%)")
        st.metric("Within 10% Error", f"{within_10pct} days ({100*within_10pct/total:.0f}%)")
        st.metric("Within 20% Error", f"{within_20pct} days ({100*within_20pct/total:.0f}%)")
        
        st.markdown("---")
        
        mae = model_df['Error'].abs().mean()
        st.metric("Mean Absolute Error", f"{mae:.1f} bowls")
        
        st.metric("RMSE", f"{np.sqrt(ols_model.mse_resid):.1f} bowls",
                 help="Root Mean Squared Error")
    
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