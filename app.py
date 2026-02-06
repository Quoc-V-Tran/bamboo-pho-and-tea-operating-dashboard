import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import pytz

# --- 1. GLOBAL SETTINGS & PATHING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _path(fname):
    local = os.path.join(BASE_DIR, fname)
    if os.path.exists(local): return local
    if os.path.exists('/Volumes'):
        for vol in os.listdir('/Volumes'):
            if 'Extreme' in vol:
                for sub in ['', 'moms-dashboard', 'bamboo_data']:
                    alt = os.path.join('/Volumes', vol, sub, fname) if sub else os.path.join('/Volumes', vol, fname)
                    if os.path.exists(alt): return alt
    return local

st.set_page_config(page_title="Bamboo Pho Daily Insights", layout="wide", page_icon="🍜")

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

    # Sales files
    sales_files = ['2024_Bamboo_Data.csv', '2025_Bamboo_Data.csv', 'Jan_2026_Bamboo_Data.csv', 'Feb 3 and 4 sales.csv']
    sales_dfs = []
    for f in sales_files:
        p = _path(f)
        if os.path.exists(p):
            sales_dfs.append(process_sales(pd.read_csv(p)))
    
    # Weather files
    weather_files = ['camp_hill_2024_weather_processed.csv', 'camp_hill_2025_weather.csv', 'jan_weather.csv', 'feb_weather.csv']
    weather_dfs = []
    for f in weather_files:
        p = _path(f)
        if os.path.exists(p):
            w = pd.read_csv(p)
            w['Date'] = pd.to_datetime(w['Date']).dt.date
            w.columns = w.columns.str.replace(' ', '_')
            if 'Temp_High' in w.columns:
                w['Temp_High'] = w['Temp_High'].astype(str).str.replace('°F', '').astype(float)
            if 'Precip_Type' in w.columns:
                w['Precip_Type'] = w['Precip_Type'].astype(str).str.split(' ').str[0]
            weather_dfs.append(w)
            
    return pd.concat(sales_dfs, ignore_index=True), pd.concat(weather_dfs, ignore_index=True)

try:
    # --- 2. DATA PIPELINE ---
    sales_df, weather_df = load_all_data()
    pho_only = sales_df[sales_df['Item'].str.contains('Pho', case=False, na=False)].copy()
    daily_pho = pho_only.groupby('Date')['Qty'].sum().reset_index().rename(columns={'Qty': 'Bowls_Sold'})
    
    merged = pd.merge(weather_df, daily_pho, on='Date', how='left').fillna(0)
    merged['Date_dt'] = pd.to_datetime(merged['Date'])
    merged['Day_of_Week'] = merged['Date_dt'].dt.day_name()
    
    # Global Filter: Closed on Mondays and zero-sales days
    merged = merged[(merged['Day_of_Week'] != 'Monday') & (merged['Bowls_Sold'] > 0)].copy()

    # Feature Engineering
    KINK = 60
    merged['is_weekend'] = merged['Day_of_Week'].isin(['Friday', 'Saturday', 'Sunday']).astype(int)
    merged['is_rain'] = (merged['Precip_Type'].isin(['Rain', 'Mixed', 'Rainy'])).astype(int)
    merged['is_snow'] = (merged['Precip_Type'].isin(['Snow', 'Flurries', 'Heavy Snow'])).astype(int)
    merged['temp_cold'] = merged['Temp_High'].apply(lambda t: min(t, KINK))
    merged['temp_hot'] = merged['Temp_High'].apply(lambda t: max(0, t - KINK))
    merged['month'] = merged['Date_dt'].dt.month
    merged['year'] = merged['Date_dt'].dt.year
    merged['is_2024'] = (merged['year'] == 2024).astype(int)
    merged['is_2025'] = (merged['year'] == 2025).astype(int)
    
    def get_season(m): return 1 if m in [1, 2, 11, 12] else (-1 if m in [4, 5, 6, 7, 8] else 0)
    merged['season_impact'] = merged['month'].apply(get_season)
    
    anchor = pd.Timestamp('2026-01-09')
    paydays = [anchor + pd.Timedelta(days=i*14) for i in range(-52, 26)]
    merged['is_federal_payday'] = merged['Date_dt'].isin(paydays).astype(int)

    # --- 3. MODELING & BACKTESTING ---
    merged = merged.sort_values('Date_dt')
    X_vars = ['temp_cold', 'temp_hot', 'is_weekend', 'is_rain', 'is_snow', 'is_federal_payday', 'is_2024', 'is_2025', 'season_impact']
    
    # Split for Backtest
    train_df = merged.iloc[:-14]
    test_df = merged.iloc[-14:]
    
    X_train = sm.add_constant(train_df[X_vars])
    model = sm.OLS(train_df['Bowls_Sold'], X_train).fit()
    
    # Run Backtest
    X_test = sm.add_constant(test_df[X_vars], has_constant='add')
    test_df['Predicted'] = model.predict(X_test)
    mae = np.mean(np.abs(test_df['Bowls_Sold'] - test_df['Predicted']))

    # --- 4. NAVIGATION ---
    with st.sidebar:
        st.title("🍜 App Navigation")
        page = st.radio("Go to:", ["Home & Forecast", "Model Diagnostics"])
        st.markdown("---")
        st.metric("Model R² Score", f"{model.rsquared:.2f}")
        st.metric("Forecast Accuracy", f"{100 - (mae/test_df['Bowls_Sold'].mean()*100):.1f}%")

    # --- PAGE: HOME & FORECAST ---
    if page == "Home & Forecast":
        st.title("🍜 Bamboo Pho Daily Insights")
        st.header("📅 Tomorrow's Forecast")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Operational Inputs")
            t_temp = st.slider("Forecasted High Temp (°F)", 0, 100, 35)
            c1, c2 = st.columns(2)
            with c1:
                t_wknd = st.checkbox("Weekend (Fri-Sun)")
                t_rain = st.checkbox("Rain")
            with c2:
                t_snow = st.checkbox("Snow")
                t_pay = st.checkbox("Payday Friday")
            t_season = st.selectbox("Seasonality", [1, 0, -1], format_func=lambda x: {1: "Winter Peak", 0: "Shoulder", -1: "Summer Slump"}[x])

        with col2:
            input_data = pd.DataFrame({'const':[1.0], 'temp_cold':[min(t_temp, KINK)], 'temp_hot':[max(0, t_temp-KINK)], 'is_weekend':[1 if t_wknd else 0], 'is_rain':[1 if t_rain else 0], 'is_snow':[1 if t_snow else 0], 'is_federal_payday':[1 if t_pay else 0], 'is_2024':[0], 'is_2025':[0], 'season_impact':[t_season]})
            pred = model.predict(input_data)[0]
            st.metric("🔮 Predicted Demand", f"{int(max(0, pred))} Bowls")
            if pred > 80: st.error(f"🚨 Capacity Alert! {int(pred-80)} bowls over seating limit.")
            elif pred > 68: st.warning("🟡 High Demand Expected.")

        st.divider()
        st.subheader("📈 Historical Sales vs. Temperature")
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(x=merged['Date'], y=merged['Bowls_Sold'], name='Bowls', line=dict(color='#2E7D32')))
        fig_hist.add_trace(go.Scatter(x=merged['Date'], y=merged['Temp_High'], name='Temp', yaxis='y2', line=dict(color='#D84315')))
        fig_hist.update_layout(yaxis2=dict(overlaying='y', side='right'), template='simple_white', hovermode='x unified')
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- PAGE: MODEL DIAGNOSTICS ---
    else:
        st.title("🧪 Model Diagnostics")
        st.markdown("""
        Use this page to validate the model's accuracy and understand the underlying drivers of soup demand.
        """)
        
        # 14-Day Backtest
        st.subheader("🧪 14-Day Backtest Accuracy")
        st.markdown("_Showing model performance on the last 14 operating days (unseen by training data)._")
        fig_back = go.Figure()
        fig_back.add_trace(go.Scatter(x=test_df['Date'], y=test_df['Bowls_Sold'], name='Actual Sales', mode='lines+markers', line=dict(color='#2E7D32')))
        fig_back.add_trace(go.Scatter(x=test_df['Date'], y=test_df['Predicted'], name='Model Prediction', mode='lines+markers', line=dict(color='#FFA000', dash='dash')))
        fig_back.update_layout(template='simple_white', height=400, hovermode='x unified')
        st.plotly_chart(fig_back, use_container_width=True)
        
        # Coefficients Table
        st.subheader("📊 Regression Coefficients")
        st.markdown("This table shows how many **additional bowls** are sold for every 1-unit increase in each variable.")
        coef_df = model.params.to_frame('Coefficient').join(model.pvalues.to_frame('P-Value'))
        st.dataframe(coef_df.style.format({'Coefficient': '{:.2f}', 'P-Value': '{:.4f}'}), use_container_width=True)
        st.caption("P-values < 0.05 are considered statistically significant.")

except Exception as e:
    st.error(f"Dashboard Error: {e}")