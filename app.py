import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import pytz

# --- CONFIGURATION & PATHING ---
st.set_page_config(page_title="Bamboo Pho & Tea Insights", layout="wide", page_icon="🍜")

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _path(fname):
    """
    Priority Search:
    1. Local Project Folder (same as app.py)
    2. Mac Documents Folder
    3. External SSD (Extreme SSD)
    """
    # 1. Local Project Folder
    local_path = os.path.join(BASE_DIR, fname)
    if os.path.exists(local_path):
        return local_path
        
    # 2. Local Mac Documents Fallback
    home = os.path.expanduser("~")
    doc_path = os.path.join(home, "Documents", fname)
    if os.path.exists(doc_path):
        return doc_path

    # 3. External SSD Volumes
    for vol in ['Extreme SSD', 'Extreme']:
        for sub in ['', 'moms-dashboard']:
            alt = os.path.join('/Volumes', vol, sub, fname) if sub else os.path.join('/Volumes', vol, fname)
            if os.path.exists(alt):
                return alt
    
    return local_path # Fallback to local path string

# --- DATA LOADING ---
@st.cache_data
def load_all_data():
    pt_tz, et_tz = pytz.timezone('US/Pacific'), pytz.timezone('US/Eastern')

    def process_sales(df_raw):
        # Handle Date/Time conversion
        df_raw['Datetime_PT'] = pd.to_datetime(df_raw['Date'] + ' ' + df_raw['Time'])
        df_raw['Datetime_ET'] = df_raw['Datetime_PT'].dt.tz_localize(pt_tz).dt.tz_convert(et_tz)
        df_raw['Date'] = df_raw['Datetime_ET'].dt.date
        df_raw['Day_of_Week'] = df_raw['Datetime_ET'].dt.day_name()
        
        # Numeric cleanup
        if 'Gross Sales' in df_raw.columns:
            df_raw['Gross Sales'] = df_raw['Gross Sales'].replace(r'[\$,]', '', regex=True).astype(float)
        df_raw['Qty'] = pd.to_numeric(df_raw['Qty'], errors='coerce').fillna(0)
        return df_raw

    sales_dfs = []
    missing_optional = []

    # File lists
    required_sales = ['Jan_2026_Bamboo_Data.csv', 'Feb 3 and 4 sales.csv']
    optional_sales = ['2024_Bamboo_Data.csv', '2025_Bamboo_Data.csv']
    
    # Load Sales
    for fname in required_sales + optional_sales:
        target = _path(fname)
        if os.path.exists(target):
            try:
                sales_dfs.append(process_sales(pd.read_csv(target)))
            except Exception as e:
                st.sidebar.error(f"Error reading {fname}: {e}")
        elif fname in optional_sales:
            missing_optional.append(fname)

    if not sales_dfs:
        st.error("🚨 Critical Error: No sales data found. Ensure 2026 CSVs are in the project folder.")
        st.stop()

    df = pd.concat(sales_dfs, ignore_index=True)

    # Load & Standardize Weather
    weather_files = ['camp_hill_2024_weather_processed.csv', 'camp_hill_2025_weather.csv', 'jan_weather.csv', 'feb_weather.csv']
    weather_dfs = []
    
    for wf in weather_files:
        path = _path(wf)
        if os.path.exists(path):
            w_df = pd.read_csv(path)
            w_df['Date'] = pd.to_datetime(w_df['Date']).dt.date
            # Cleanup headers for consistency
            w_df.columns = w_df.columns.str.replace(' ', '_')
            if 'Temp_High' in w_df.columns and w_df['Temp_High'].dtype == object:
                w_df['Temp_High'] = w_df['Temp_High'].str.replace('°F', '').astype(float)
            weather_dfs.append(w_df)
            
    weather = pd.concat(weather_dfs, ignore_index=True)
    
    if missing_optional:
        st.sidebar.warning(f"⚠️ Historical data missing: {', '.join(missing_optional)}")

    return df, weather

# --- APP LOGIC ---
try:
    sales_df, weather_df = load_all_data()

    # Filter for Pho only items
    pho_only = sales_df[sales_df['Item'].str.contains('Pho', case=False, na=False)].copy()
    daily_pho = pho_only.groupby('Date')['Qty'].sum().reset_index()
    daily_pho.columns = ['Date', 'Bowls_Sold']
    
    weather_df['Precip_Type'] = weather_df['Precip_Type'].replace('None', 'Clear').fillna('Clear')
    merged = pd.merge(weather_df, daily_pho, on='Date', how='left').fillna(0)
    merged['Date_dt'] = pd.to_datetime(merged['Date'])
    merged['Day_of_Week'] = merged['Date_dt'].dt.day_name()
    
    # --- FEATURE ENGINEERING ---
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Friday', 'Saturday', 'Sunday']).astype(int)
    merged['is_rain'] = (merged['Precip_Type'].isin(['Rain', 'Mixed'])).astype(int)
    merged['is_snow'] = (merged['Precip_Type'].isin(['Snow', 'Flurries', 'Heavy Snow'])).astype(int)
    merged['month'] = merged['Date_dt'].dt.month

    # Seasonality
    def get_season_impact(month):
        return 1 if month in [1, 2, 11, 12] else (-1 if month in [4, 5, 6, 7, 8] else 0)
    merged['season_impact'] = merged['month'].apply(get_season_impact)

    # Federal Payday Fridays Logic (2025-2026)
    federal_payday_anchor = pd.Timestamp('2026-01-09')
    all_paydays = []
    # Gen 2 years of paydays
    for i in range(-30, 30):
        all_paydays.append(federal_payday_anchor + pd.Timedelta(days=i*14))
    merged['is_federal_payday'] = merged['Date_dt'].isin(all_paydays).astype(int)

    # --- MODELING (OLS) ---
    model_df = merged[(merged['Day_of_Week'] != 'Monday') & (merged['Bowls_Sold'] > 0)].copy()
    
    # Piecewise Temperature at 60F Kink
    KINK = 60
    model_df['temp_cold'] = model_df['Temp_High'].apply(lambda t: min(t, KINK))
    model_df['temp_hot'] = model_df['Temp_High'].apply(lambda t: max(0, t - KINK))

    features = ['temp_cold', 'temp_hot', 'is_weekend', 'is_rain', 'is_snow', 'is_federal_payday', 'season_impact']
    X = sm.add_constant(model_df[features])
    ols_model = sm.OLS(model_df['Bowls_Sold'], X).fit()

    # --- DASHBOARD UI ---
    st.title("🍜 Bamboo Pho Operating Insights")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔮 Predictive Forecasting")
        tomorrow_temp = st.slider("Forecasted High Temp (°F)", 0, 100, 45)
        
        # Pred Logic
        t_cold = min(tomorrow_temp, KINK)
        t_hot = max(0, tomorrow_temp - KINK)
        
        # Simplified prediction for today (2026 baseline)
        pred = (ols_model.params['const'] + 
                (ols_model.params['temp_cold'] * t_cold) + 
                (ols_model.params['temp_hot'] * t_hot) + 
                (ols_model.params['season_impact'] * get_season_impact(2))) # Fixed to Feb for now
        
        st.metric("Predicted Bowls", f"{int(max(0, pred))} Bowls", delta_color="normal")
        
        # Capacity Alert
        if pred > 80:
            st.error("🚨 Capacity Warning: Expecting overflow. Prioritize takeout prep!")
        elif pred > 65:
            st.warning("🟡 High Demand: Seating will be near capacity.")

    with col2:
        st.markdown("### 📊 Stats Summary")
        st.write(f"**R² Score:** {ols_model.rsquared:.2f}")
        st.write(f"**Model Obs:** {int(ols_model.nobs)} days")
        st.write(f"**Optimal Kink:** {KINK}°F")

    st.divider()
    
    # Visual Chart
    st.subheader("History: Sales vs Temperature")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=model_df['Date'], y=model_df['Bowls_Sold'], name="Bowls", line=dict(color="#2E7D32")))
    fig.add_trace(go.Scatter(x=model_df['Date'], y=model_df['Temp_High'], name="Temp", yaxis="y2", line=dict(color="#D84315")))
    fig.update_layout(yaxis2=dict(overlaying='y', side='right'), hovermode="x unified", template="simple_white")
    st.plotly_chart(fig, use_container_width=True)

    # Leaderboard
    st.subheader("🏆 January 2026 Regulars")
    jan_sales = sales_df[(pd.to_datetime(sales_df['Date']).dt.month == 1) & (pd.to_datetime(sales_df['Date']).dt.year == 2026)]
    top_cust = jan_sales.groupby('Customer Name').size().sort_values(ascending=False).head(5)
    st.table(top_cust)

except Exception as e:
    st.error(f"Application Error: {e}")
    st.info("Ensure CSV files are in the project folder or Documents.")