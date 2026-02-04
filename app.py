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
    
    # Binary features
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Friday', 'Saturday', 'Sunday']).astype(int)
    merged['is_precipitation'] = (merged['Precip_Type'] != 'Clear').astype(int)
    
    # Payday Effect: Flag days within 4 days after 15th and 30th/last day of month
    merged['day_of_month'] = pd.to_datetime(merged['Date']).dt.day
    merged['days_in_month'] = pd.to_datetime(merged['Date']).dt.days_in_month
    merged['is_payday_effect'] = (
        # 4 days after 15th (days 16-19)
        ((merged['day_of_month'] >= 16) & (merged['day_of_month'] <= 19)) |
        # 4 days after month end (days 1-4 of month OR last 4 days wrapping to next month)
        ((merged['day_of_month'] >= 1) & (merged['day_of_month'] <= 4)) |
        # Handle last day payday for months with 30/31 days (days 31, 1-4)
        (merged['day_of_month'] >= merged['days_in_month'])
    ).astype(int)
    
    # Holiday Effect: Flag 2 days before major holidays
    # Define major holidays for 2025-2026
    major_holidays = {
        # 2025 Holidays
        pd.Timestamp('2025-05-26'): 'Memorial Day',       # Last Monday in May
        pd.Timestamp('2025-07-04'): 'July 4th',
        pd.Timestamp('2025-09-01'): 'Labor Day',          # First Monday in Sept
        pd.Timestamp('2025-11-27'): 'Thanksgiving',       # 4th Thursday in Nov
        pd.Timestamp('2025-12-25'): 'Christmas',
        pd.Timestamp('2025-04-20'): 'Easter',             # 2025 Easter
        pd.Timestamp('2025-02-09'): 'Super Bowl',         # 2025 Super Bowl
        # 2026 Holidays
        pd.Timestamp('2026-05-25'): 'Memorial Day',
        pd.Timestamp('2026-07-04'): 'July 4th',
        pd.Timestamp('2026-09-07'): 'Labor Day',
        pd.Timestamp('2026-11-26'): 'Thanksgiving',
        pd.Timestamp('2026-12-25'): 'Christmas',
        pd.Timestamp('2026-04-05'): 'Easter',             # 2026 Easter
        pd.Timestamp('2026-02-08'): 'Super Bowl',         # 2026 Super Bowl
    }
    
    merged['is_pre_holiday'] = 0
    for holiday_date in major_holidays.keys():
        # Flag BOTH 1 day before AND 2 days before holiday (within 2 days)
        merged.loc[
            pd.to_datetime(merged['Date']).isin([holiday_date - pd.Timedelta(days=1), holiday_date - pd.Timedelta(days=2)]),
            'is_pre_holiday'
        ] = 1
    
    # Filter for active days only (Exclude Mondays/zeros)
    model_df = merged[
        (merged['Day_of_Week'] != 'Monday') & 
        (merged['Bowls_Sold'] > 0)
    ].copy()
    
    # Center temperature variable (subtract mean)
    mean_temp = model_df['Temp_High'].mean()
    model_df['Temp_Centered'] = model_df['Temp_High'] - mean_temp
    
    # Interaction term: Precipitation × Centered Temperature
    model_df['precip_temp_interaction'] = model_df['is_precipitation'] * model_df['Temp_Centered']

    st.title("🍜 Daily Insights")
    
    # Show data range
    date_min = merged['Date'].min()
    date_max = merged['Date'].max()
    total_days = len(model_df)
    total_closed = len(merged[merged['Bowls_Sold'] == 0])
    st.info(f"📊 Analyzing data from **{date_min}** to **{date_max}** • **{total_days}** operating days • **{total_closed}** closed days excluded (Mondays, holidays, weather closures)")

    # --- BUILD ENHANCED MODEL WITH INTERACTION + PAYDAY + HOLIDAY EFFECTS ---
    # Bowls_Sold ~ Intercept + Temp_Centered + is_precipitation + (is_precipitation × Temp_Centered) + is_weekend + is_payday_effect + is_pre_holiday
    # Note: Temperature is centered (mean subtracted) so intercept = predicted bowls at average temp
    X = model_df[['Temp_Centered', 'is_precipitation', 'precip_temp_interaction', 'is_weekend', 'is_payday_effect', 'is_pre_holiday']]
    X = sm.add_constant(X) 
    y = model_df['Bowls_Sold']
    ols_model = sm.OLS(y, X).fit()

    # --- TOMORROW'S PREDICTION (Top Section) ---
    st.header("📅 Tomorrow's Forecast")
    
    pred_col1, pred_col2 = st.columns([1, 2])
    
    with pred_col1:
        st.subheader("Enter Tomorrow's Forecast")
        tomorrow_temp = st.number_input("Temperature (°F)", min_value=0, max_value=100, value=35, step=1)
        tomorrow_is_weekend = st.checkbox("Weekend Day (Fri-Sun)", value=False)
        tomorrow_has_precip = st.checkbox("Precipitation Expected", value=False)
        tomorrow_is_payday = st.checkbox("Payday Effect (4 days after 15th or month-end)", value=False)
        tomorrow_is_pre_holiday = st.checkbox("Pre-Holiday (2 days before major holiday)", value=False)
        
        # Center tomorrow's temperature
        tomorrow_temp_centered = tomorrow_temp - mean_temp
        
        # Calculate interaction term with centered temperature
        tomorrow_interaction = (1 if tomorrow_has_precip else 0) * tomorrow_temp_centered
        
        # Calculate prediction
        tomorrow_pred = (ols_model.params['const'] + 
                        (ols_model.params['Temp_Centered'] * tomorrow_temp_centered) + 
                        (ols_model.params['is_precipitation'] * (1 if tomorrow_has_precip else 0)) +
                        (ols_model.params['precip_temp_interaction'] * tomorrow_interaction) +
                        (ols_model.params['is_weekend'] * (1 if tomorrow_is_weekend else 0)) +
                        (ols_model.params['is_payday_effect'] * (1 if tomorrow_is_payday else 0)) +
                        (ols_model.params['is_pre_holiday'] * (1 if tomorrow_is_pre_holiday else 0)))
        
        st.metric("🔮 Predicted Bowls for Tomorrow", 
                 f"{int(max(0, tomorrow_pred))} Bowls",
                 help=f"Enhanced OLS model with 7 features (Mean temp: {mean_temp:.1f}°F)")
    
    with pred_col2:
        st.subheader("📊 Historical Stats & Model Coefficients")
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            avg_bowls = model_df['Bowls_Sold'].mean()
            st.metric("Avg Daily Bowls", f"{avg_bowls:.1f}")
            st.metric("Weekend Lift", f"+{ols_model.params['is_weekend']:.1f}")
        
        with stat_col2:
            st.metric("Temp Effect", f"{ols_model.params['Temp_Centered']:.2f}/°F")
            st.metric("Precip Impact", f"{ols_model.params['is_precipitation']:+.1f}",
                     help=f"At avg temp ({mean_temp:.1f}°F)")
        
        with stat_col3:
            st.metric("💰 Payday Boost", f"+{ols_model.params['is_payday_effect']:.1f}",
                     help="4 days after 15th or month-end")
            st.metric("🎉 Holiday Boost", f"+{ols_model.params['is_pre_holiday']:.1f}",
                     help="2 days before major holiday")
        
        with stat_col4:
            st.metric("Model R²", f"{ols_model.rsquared:.3f}")
            st.metric("Total Bowls", f"{int(model_df['Bowls_Sold'].sum())}")

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