import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import pytz

# --- GLOBAL PATH HELPER ---
# This ensures the app looks in the script folder, Documents, and SSD automatically.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _path(fname):
    """Search project folder, Mac Documents, then External SSD."""
    # 1. Local Project Folder
    local = os.path.join(BASE_DIR, fname)
    if os.path.exists(local): return local
    
    # 2. SSD Search (Matches 'Extreme SSD', 'Extreme', etc.)
    if os.path.exists('/Volumes'):
        for vol in os.listdir('/Volumes'):
            if 'Extreme' in vol:
                for sub in ['', 'moms-dashboard', 'bamboo_data']:
                    alt = os.path.join('/Volumes', vol, sub, fname) if sub else os.path.join('/Volumes', vol, fname)
                    if os.path.exists(alt): return alt
                    
    # 3. Documents Fallback
    doc_path = os.path.join(os.path.expanduser("~"), "Documents", "moms-dashboard", fname)
    return doc_path if os.path.exists(doc_path) else local

st.set_page_config(page_title="Daily Insights", layout="wide")

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

    # --- LOAD SALES DATA (all required) ---
    sales_files = ['2024_Bamboo_Data.csv', '2025_Bamboo_Data.csv', 
                   'Jan_2026_Bamboo_Data.csv', 'Feb 3 and 4 sales.csv']
    sales_dfs = []
    
    for f in sales_files:
        p = _path(f)
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required sales file missing: {f}")
        sales_dfs.append(process_sales(pd.read_csv(p)))
    
    df = pd.concat(sales_dfs, ignore_index=True)
    
    # --- LOAD WEATHER DATA ---
    weather_files = [
        'camp_hill_2024_weather_processed.csv',
        'camp_hill_2025_weather.csv',
        'jan_weather.csv',
        'feb_weather.csv'
    ]
    
    weather_dfs = []
    for f in weather_files:
        p = _path(f)
        if not os.path.exists(p):
            raise FileNotFoundError(f"Required weather file missing: {f}")
        w_df = pd.read_csv(p)
        w_df['Date'] = pd.to_datetime(w_df['Date']).dt.date
        w_df.columns = w_df.columns.str.replace(' ', '_')
        if 'Temp_High' in w_df.columns:
            w_df['Temp_High'] = w_df['Temp_High'].astype(str).str.replace('°F', '').astype(float)
        if 'Precip_Type' in w_df.columns:
            w_df['Precip_Type'] = w_df['Precip_Type'].astype(str).str.split(' ').str[0]
        weather_dfs.append(w_df)
            
    weather = pd.concat(weather_dfs, ignore_index=True)
    return df, weather

try:
    sales_df, weather_df = load_all_data()
    
    # --- DATA PROCESSING ---
    pho_only = sales_df[sales_df['Item'].str.contains('Pho', case=False, na=False)].copy()
    daily_pho = pho_only.groupby('Date')['Qty'].sum().reset_index()
    daily_pho.columns = ['Date', 'Bowls_Sold']
    
    weather_df['Precip_Type'] = weather_df['Precip_Type'].replace('nan', 'Clear').replace('None', 'Clear').fillna('Clear')
    merged = pd.merge(weather_df, daily_pho, on='Date', how='left').fillna(0)
    merged['Date_dt'] = pd.to_datetime(merged['Date'])
    merged['Day_of_Week'] = merged['Date_dt'].dt.day_name()
    
    # --- FEATURE ENGINEERING ---
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Friday', 'Saturday', 'Sunday']).astype(int)
    merged['is_rain'] = (merged['Precip_Type'].isin(['Rain', 'Mixed'])).astype(int)
    merged['is_snow'] = (merged['Precip_Type'].isin(['Snow', 'Flurries', 'Heavy Snow'])).astype(int)
    merged['month'] = merged['Date_dt'].dt.month
    
    def get_season_impact(month):
        if month in [1, 2, 11, 12]: return 1
        elif month in [4, 5, 6, 7, 8]: return -1
        return 0
    
    merged['season_impact'] = merged['month'].apply(get_season_impact)
    
    # Paydays (Bi-weekly)
    federal_payday_anchor = pd.Timestamp('2026-01-09')
    paydays = [federal_payday_anchor + pd.Timedelta(days=i*14) for i in range(-52, 26)]
    merged['is_federal_payday'] = merged['Date_dt'].isin(paydays).astype(int)
    
    # Year Dummies
    merged['year'] = merged['Date_dt'].dt.year
    merged['is_2024'] = (merged['year'] == 2024).astype(int)
    merged['is_2025'] = (merged['year'] == 2025).astype(int)
    
    model_df = merged[(merged['Day_of_Week'] != 'Monday') & (merged['Bowls_Sold'] > 0)].copy()

    # --- MODELING ---
    KINK = 60
    model_df['temp_cold'] = model_df['Temp_High'].apply(lambda t: min(t, KINK))
    model_df['temp_hot'] = model_df['Temp_High'].apply(lambda t: max(0, t - KINK))

    X_vars = ['temp_cold', 'temp_hot', 'is_weekend', 'is_rain', 'is_snow', 
              'is_federal_payday', 'is_2024', 'is_2025', 'season_impact']
    X = sm.add_constant(model_df[X_vars])
    ols_model = sm.OLS(model_df['Bowls_Sold'], X).fit()

    # --- UI ---
    st.title("🍜 Bamboo Pho Daily Insights")
    
    st.header("📅 Tomorrow's Forecast")
    tomorrow_temp = st.number_input("Temperature (°F)", 0, 100, 35)
    
    t_cold = min(tomorrow_temp, KINK)
    t_hot = max(0, tomorrow_temp - KINK)
    
    # Simple prediction (Assuming 2026 baseline)
    tomorrow_pred = (ols_model.params['const'] + 
                    (ols_model.params['temp_cold'] * t_cold) + 
                    (ols_model.params['temp_hot'] * t_hot))
    
    st.metric("🔮 Predicted Bowls", f"{int(max(0, tomorrow_pred))} Bowls")
    
    st.divider()
    st.subheader('📈 Sales vs Temperature')
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=model_df['Date'], y=model_df['Bowls_Sold'], name='Bowls', line=dict(color='#2E7D32')))
    fig.add_trace(go.Scatter(x=model_df['Date'], y=model_df['Temp_High'], name='Temp', yaxis='y2', line=dict(color='#D84315')))
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'), template='simple_white')
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Dashboard Error: {e}")