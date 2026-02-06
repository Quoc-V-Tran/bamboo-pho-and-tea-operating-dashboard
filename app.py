import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import pytz

# --- 1. SET THE ANCHOR ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _path(fname):
    """Hunt for files in Project Folder, Mac Documents, or Extreme SSD."""
    local = os.path.join(BASE_DIR, fname)
    if os.path.exists(local): return local
    # SSD Fallback (searches for 'Extreme' in volume name)
    if os.path.exists('/Volumes'):
        for vol in os.listdir('/Volumes'):
            if 'Extreme' in vol:
                for sub in ['', 'moms-dashboard', 'bamboo_data']:
                    alt = os.path.join('/Volumes', vol, sub, fname) if sub else os.path.join('/Volumes', vol, fname)
                    if os.path.exists(alt): return alt
    return local

st.set_page_config(page_title="Bamboo Pho Daily Insights", layout="wide")

@st.cache_data
def load_all_data():
    pt_tz, et_tz = pytz.timezone('US/Pacific'), pytz.timezone('US/Eastern')
    
    def process_sales(df_raw):
        df_raw['Datetime_PT'] = pd.to_datetime(df_raw['Date'] + ' ' + df_raw['Time'])
        df_raw['Datetime_ET'] = df_raw['Datetime_PT'].dt.tz_localize(pt_tz).dt.tz_convert(et_tz)
        df_raw['Date'] = df_raw['Datetime_ET'].dt.date
        df_raw['Day_of_Week'] = df_raw['Datetime_ET'].dt.day_name()
        df_raw['Gross Sales'] = df_raw['Gross Sales'].replace(r'[\$,]', '', regex=True).astype(float)
        df_raw['Qty'] = pd.to_numeric(df_raw['Qty'], errors='coerce').fillna(0)
        return df_raw

    # Load All Sales
    sales_files = ['2024_Bamboo_Data.csv', '2025_Bamboo_Data.csv', 'Jan_2026_Bamboo_Data.csv', 'Feb 3 and 4 sales.csv']
    sales_dfs = []
    for f in sales_files:
        p = _path(f)
        if os.path.exists(p):
            sales_dfs.append(process_sales(pd.read_csv(p)))
        else:
            st.sidebar.warning(f"⚠️ Missing: {f}")
    
    if not sales_dfs:
        st.error("🚨 No sales data found. Check SSD connection or iCloud status.")
        st.stop()
        
    sales_df = pd.concat(sales_dfs, ignore_index=True)
    
    # Load All Weather
    weather_files = ['camp_hill_2024_weather_processed.csv', 'camp_hill_2025_weather.csv', 'jan_weather.csv', 'feb_weather.csv']
    weather_dfs = []
    for f in weather_files:
        p = _path(f)
        if os.path.exists(p):
            w = pd.read_csv(p)
            w['Date'] = pd.to_datetime(w['Date']).dt.date
            w.columns = w.columns.str.replace(' ', '_')
            if 'Temp_High' in w.columns and w['Temp_High'].dtype == object:
                w['Temp_High'] = w['Temp_High'].str.replace('°F', '').astype(float)
            if 'Precip_Type' in w.columns:
                w['Precip_Type'] = w['Precip_Type'].astype(str).str.split(' ').str[0]
            weather_dfs.append(w)
            
    weather_df = pd.concat(weather_dfs, ignore_index=True)
    return sales_df, weather_df

try:
    sales_df, weather_df = load_all_data()
    
    # Process volume for Pho items
    pho_only = sales_df[sales_df['Item'].str.contains('Pho', case=False, na=False)].copy()
    daily_pho = pho_only.groupby('Date')['Qty'].sum().reset_index().rename(columns={'Qty': 'Bowls_Sold'})
    
    # --- GLOBAL OPERATING FILTER ---
    merged = pd.merge(weather_df, daily_pho, on='Date', how='left').fillna(0)
    merged['Date_dt'] = pd.to_datetime(merged['Date'])
    merged['Day_of_Week'] = merged['Date_dt'].dt.day_name()
    
    # Exclude Mondays (Closed) and days with 0 sales (holidays/weather closures)
    merged = merged[(merged['Day_of_Week'] != 'Monday') & (merged['Bowls_Sold'] > 0)].copy()

    # Feature Engineering
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Friday', 'Saturday', 'Sunday']).astype(int)
    merged['is_rain'] = (merged['Precip_Type'].isin(['Rain', 'Mixed'])).astype(int)
    merged['is_snow'] = (merged['Precip_Type'].isin(['Snow', 'Flurries', 'Heavy Snow'])).astype(int)
    merged['month'] = merged['Date_dt'].dt.month
    merged['year'] = merged['Date_dt'].dt.year
    merged['is_2024'] = (merged['year'] == 2024).astype(int)
    merged['is_2025'] = (merged['year'] == 2025).astype(int)

    def get_season_impact(month):
        if month in [1, 2, 11, 12]: return 1
        elif month in [4, 5, 6, 7, 8]: return -1
        return 0
    merged['season_impact'] = merged['month'].apply(get_season_impact)

    # Federal Paydays
    payday_anchor = pd.Timestamp('2026-01-09')
    paydays = [payday_anchor + pd.Timedelta(days=i*14) for i in range(-52, 26)]
    merged['is_federal_payday'] = merged['Date_dt'].isin(paydays).astype(int)
    
    # Model Training
    KINK = 60
    merged['temp_cold'] = merged['Temp_High'].apply(lambda t: min(t, KINK))
    merged['temp_hot'] = merged['Temp_High'].apply(lambda t: max(0, t - KINK))

    X_vars = ['temp_cold', 'temp_hot', 'is_weekend', 'is_rain', 'is_snow', 
              'is_federal_payday', 'is_2024', 'is_2025', 'season_impact']
    X = sm.add_constant(merged[X_vars])
    ols_model = sm.OLS(merged['Bowls_Sold'], X).fit()

    # --- UI ---
    st.title("🍜 Bamboo Pho Daily Insights")
    
    with st.sidebar:
        st.header("📊 Model Overview")
        st.metric("Model R² Score", f"{ols_model.rsquared:.2f}")
        st.write(f"Total Observations: {int(ols_model.nobs)}")
        st.markdown("---")
        st.info("Predictions above 80 bowls indicate 'Shadow Demand' (Dine-in Capacity exceeded).")

    # Forecast Section
    st.header("📅 Tomorrow's Forecast")
    col_input, col_result = st.columns([2, 2])
    
    with col_input:
        tomorrow_temp = st.number_input("Forecasted High Temp (°F)", 0, 100, 35)
        tomorrow_is_weekend = st.checkbox("Weekend (Fri-Sun)")
        tomorrow_is_fed_payday = st.checkbox("Payday Friday")
        tomorrow_is_rain = st.checkbox("Expecting Rain")
        tomorrow_is_snow = st.checkbox("Expecting Snow")

    with col_result:
        # DYNAMIC PREDICTION ENGINE
        input_data = pd.DataFrame({
            'const': [1.0],
            'temp_cold': [min(tomorrow_temp, KINK)],
            'temp_hot': [max(0, tomorrow_temp - KINK)],
            'is_weekend': [1 if tomorrow_is_weekend else 0],
            'is_rain': [1 if tomorrow_is_rain else 0],
            'is_snow': [1 if tomorrow_is_snow else 0],
            'is_federal_payday': [1 if tomorrow_is_fed_payday else 0],
            'is_2024': [0],
            'is_2025': [0],
            'season_impact': [get_season_impact(pd.Timestamp.now().month)]
        })
        
        tomorrow_pred = ols_model.predict(input_data)[0]
        st.metric("🔮 Predicted Demand", f"{int(max(0, tomorrow_pred))} Bowls")
        
        if tomorrow_pred > 80:
            st.error("🚨 Capacity Alert: Expecting peak overflow!")
        elif tomorrow_pred > 65:
            st.warning("🟡 High Demand: Optimize table turnover.")

    st.divider()

    # Visuals
    st.subheader('📈 Historical Sales vs. Temperature')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=merged['Date'], y=merged['Bowls_Sold'], name='Bowls Sold', line=dict(color='#2E7D32')))
    fig.add_trace(go.Scatter(x=merged['Date'], y=merged['Temp_High'], name='High Temp (°F)', yaxis='y2', line=dict(color='#D84315')))
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'), template='simple_white', hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    # Leaderboard (January 2026)
    st.subheader("🏆 January 2026 Regulars Leaderboard")
    jan_2026_sales = sales_df[(pd.to_datetime(sales_df['Date']).dt.year == 2026) & (pd.to_datetime(sales_df['Date']).dt.month == 1)]
    top_cust = jan_2026_sales.groupby('Customer Name').size().sort_values(ascending=False).head(10)
    st.table(top_cust)

except Exception as e:
    st.error(f"Dashboard Error: {e}")