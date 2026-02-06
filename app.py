import os
import streamlit as st
import pandas as pd

# Project root for data files (works when run from project dir or Streamlit Cloud)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
    
    # Naval Base (NSA Mechanicsburg) Traffic Effects
    
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
    
    # --- YEAR DUMMIES (Capture Model Drift) ---
    merged['year'] = merged['Date_dt'].dt.year
    merged['is_2024'] = (merged['year'] == 2024).astype(int)
    merged['is_2025'] = (merged['year'] == 2025).astype(int)
    
    # Filter for active days only (Exclude Mondays and zero sales)
    model_df = merged[
        (merged['Day_of_Week'] != 'Monday') & 
        (merged['Bowls_Sold'] > 0)
    ].copy()

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

    # --- FIND OPTIMAL TEMPERATURE KINK POINT ---
    # Test piecewise temperature models with different kink points
    kink_points = [50, 55, 60, 65, 70]
    best_r2 = 0
    best_kink = 60  # Default
    kink_results = []
    
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
        
        kink_results.append({
            'kink': kink,
            'r2': model_temp.rsquared,
            'cold_coef': model_temp.params[f'temp_cold_{kink}'],
            'hot_coef': model_temp.params[f'temp_hot_{kink}'],
            'cold_pval': model_temp.pvalues[f'temp_cold_{kink}'],
            'hot_pval': model_temp.pvalues[f'temp_hot_{kink}']
        })
        
        if model_temp.rsquared > best_r2:
            best_r2 = model_temp.rsquared
            best_kink = kink
    
    # Use optimal kink point
    model_df['temp_cold'] = model_df['Temp_High'].apply(lambda t: min(t, best_kink))
    model_df['temp_hot'] = model_df['Temp_High'].apply(lambda t: max(0, t - best_kink))

    # --- BUILD SIMPLIFIED PIECEWISE TEMPERATURE MODEL ---
    # Bowls_Sold ~ Temp_Cold + Temp_Hot + Weekend(Fri/Sat/Sun) + Rain + Snow + Federal_Payday + 
    #              Payday_Weekend + Year_2024 + Year_2025 + Season_Impact
    # Note: is_clear is baseline for precipitation, 2026 is baseline for year
    # Weekend now includes Friday (combined payday/weekend effect)
    # Season_Impact: High (+1) = Jan/Feb/Nov/Dec, Low (-1) = Apr-Aug, Neutral (0) = Mar/Sep/Oct
    # Temperature: Piecewise at optimal kink point
    X = model_df[['temp_cold', 'temp_hot', 'is_weekend', 'is_rain', 'is_snow', 'is_federal_payday', 
                  'is_payday_weekend',
                  'is_2024', 'is_2025', 'season_impact']]
    X = sm.add_constant(X) 
    y = model_df['Bowls_Sold']
    ols_model = sm.OLS(y, X).fit()
    
    # Store kink point info for display
    optimal_kink = best_kink
    kink_cold_coef = ols_model.params['temp_cold']
    kink_hot_coef = ols_model.params['temp_hot']
    
    # Calculate predictions and errors
    model_df['Predicted'] = ols_model.predict(X)
    model_df['Error'] = model_df['Bowls_Sold'] - model_df['Predicted']
    model_df['Error_Pct'] = (model_df['Error'] / model_df['Bowls_Sold'] * 100).abs()
    
    # Calculate MAE (Mean Absolute Error)
    mae = model_df['Error'].abs().mean()

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
            tomorrow_is_weekend = st.checkbox("Weekend (Fri/Sat/Sun)", value=False,
                                              help="Combined Friday payday + weekend effect")
            tomorrow_is_rain = st.checkbox("Rain/Mixed", value=False)
        with col_b:
            tomorrow_is_snow = st.checkbox("Snow/Flurries", value=False)
        
        st.markdown("**💰 Payday**")
        col_c, col_d = st.columns(2)
        with col_c:
            tomorrow_is_fed_payday = st.checkbox("Payday Friday", value=False)
        with col_d:
            tomorrow_is_payday_wknd = st.checkbox("Payday Weekend (Sat/Sun after)", value=False)
        
        st.markdown("**🌦️ Seasonality**")
        tomorrow_season_impact = st.selectbox(
            "Season Impact", 
            options=[1, 0, -1],
            format_func=lambda x: {
                1: "High Demand (Jan, Feb, Nov, Dec - Winter Peak)",
                0: "Neutral (Mar, Sep, Oct - Shoulder Seasons)",
                -1: "Low Demand (Apr-Aug - Warm Season Slump)"
            }[x],
            index=0,  # Default to High Demand (it's February)
            help="Consolidated seasonal demand pattern"
        )
        
        # Piecewise temperature transformation
        tomorrow_temp_cold = min(tomorrow_temp, optimal_kink)
        tomorrow_temp_hot = max(0, tomorrow_temp - optimal_kink)
        
        # Tomorrow is assumed to be 2026 (is_2024=0, is_2025=0)
        tomorrow_pred = (ols_model.params['const'] + 
                        (ols_model.params['temp_cold'] * tomorrow_temp_cold) + 
                        (ols_model.params['temp_hot'] * tomorrow_temp_hot) + 
                        (ols_model.params['is_weekend'] * (1 if tomorrow_is_weekend else 0)) +
                        (ols_model.params['is_rain'] * (1 if tomorrow_is_rain else 0)) +
                        (ols_model.params['is_snow'] * (1 if tomorrow_is_snow else 0)) +
                        (ols_model.params['is_federal_payday'] * (1 if tomorrow_is_fed_payday else 0)) +
                        (ols_model.params['is_payday_weekend'] * (1 if tomorrow_is_payday_wknd else 0)) +
                        (ols_model.params['is_2024'] * 0) +  # Tomorrow is 2026, not 2024
                        (ols_model.params['is_2025'] * 0) +  # Tomorrow is 2026, not 2025
                        (ols_model.params['season_impact'] * tomorrow_season_impact))
        
        st.metric("🔮 Predicted Bowls for Tomorrow", 
                 f"{int(max(0, tomorrow_pred))} Bowls",
                 help=f"Parsimonious model (10 features, Kink: {optimal_kink}°F)")
        
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