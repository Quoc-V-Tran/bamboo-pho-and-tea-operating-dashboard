import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import statsmodels.api as sm
import pytz

st.set_page_config(page_title="Bamboo Pho Operations", layout="wide")

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

    st.title("🍜 Bamboo Pho Operations Dashboard")
    
    # Show data range
    date_min = merged['Date'].min()
    date_max = merged['Date'].max()
    total_days = len(model_df)
    total_closed = len(merged[merged['Bowls_Sold'] == 0])
    st.info(f"📊 Analyzing data from **{date_min}** to **{date_max}** • **{total_days}** operating days • **{total_closed}** closed days excluded (Mondays, holidays, weather closures)")

    # --- BUILD SIMPLE MODEL WITH INTERACTION ---
    # Bowls_Sold ~ Intercept + Temp_Centered + is_precipitation + (is_precipitation × Temp_Centered) + is_weekend
    # Note: Temperature is centered (mean subtracted) so intercept = predicted bowls at average temp
    X = model_df[['Temp_Centered', 'is_precipitation', 'precip_temp_interaction', 'is_weekend']]
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
        
        # Center tomorrow's temperature
        tomorrow_temp_centered = tomorrow_temp - mean_temp
        
        # Calculate interaction term with centered temperature
        tomorrow_interaction = (1 if tomorrow_has_precip else 0) * tomorrow_temp_centered
        
        # Calculate prediction
        tomorrow_pred = (ols_model.params['const'] + 
                        (ols_model.params['Temp_Centered'] * tomorrow_temp_centered) + 
                        (ols_model.params['is_precipitation'] * (1 if tomorrow_has_precip else 0)) +
                        (ols_model.params['precip_temp_interaction'] * tomorrow_interaction) +
                        (ols_model.params['is_weekend'] * (1 if tomorrow_is_weekend else 0)))
        
        st.metric("🔮 Predicted Bowls for Tomorrow", 
                 f"{int(max(0, tomorrow_pred))} Bowls",
                 help=f"OLS model with centered temperature (Mean temp: {mean_temp:.1f}°F)")
    
    with pred_col2:
        st.subheader("📊 Historical Stats & Model Coefficients")
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        
        with stat_col1:
            avg_bowls = model_df['Bowls_Sold'].mean()
            st.metric("Avg Daily Bowls", f"{avg_bowls:.1f}")
            st.metric("Total Bowls", f"{int(model_df['Bowls_Sold'].sum())}")
        
        with stat_col2:
            st.metric("Weekend Lift", f"+{ols_model.params['is_weekend']:.1f} Bowls")
            st.metric("Precip Impact", f"{ols_model.params['is_precipitation']:+.1f} Bowls",
                     help=f"At avg temp ({mean_temp:.1f}°F)")
        
        with stat_col3:
            st.metric("Temp Effect", f"{ols_model.params['Temp_Centered']:.2f} per °F")
            st.metric("Model R²", f"{ols_model.rsquared:.3f}")

    st.divider()
    
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
            (ols_model.params['is_precipitation'] * recent_df['is_precipitation']) +
            (ols_model.params['precip_temp_interaction'] * recent_df['precip_temp_interaction']) +
            (ols_model.params['is_weekend'] * recent_df['is_weekend'])
        )
        
        recent_df['Error'] = recent_df['Bowls_Sold'] - recent_df['Predicted']
        recent_df['Error_Pct'] = (recent_df['Error'] / recent_df['Bowls_Sold'] * 100)
        
        # Create comparison table
        comparison_data = recent_df[['Date', 'Day_of_Week', 'Temp_High', 'Precip_Type', 'Bowls_Sold', 'Predicted', 'Error', 'Error_Pct']].copy()
        comparison_data['Date'] = pd.to_datetime(comparison_data['Date']).dt.strftime('%Y-%m-%d')
        comparison_data['Predicted'] = comparison_data['Predicted'].round(1)
        comparison_data['Error'] = comparison_data['Error'].round(1)
        comparison_data['Error_Pct'] = comparison_data['Error_Pct'].round(1)
        
        comparison_data.columns = ['Date', 'Day', 'Temp (°F)', 'Weather', 'Actual', 'Predicted', 'Error', 'Error %']
        
        st.dataframe(comparison_data, use_container_width=True, hide_index=True)
        
        # Show metrics for most recent operating day (Sunday Feb 1)
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
        'const': f'Intercept (at {mean_temp:.1f}°F avg temp)',
        'Temp_Centered': 'Temperature (centered)',
        'is_precipitation': 'Precipitation',
        'precip_temp_interaction': 'Precip × Temp (interaction)',
        'is_weekend': 'Weekend'
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
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    with stats_col1:
        st.metric("R²", f"{ols_model.rsquared:.4f}")
    with stats_col2:
        st.metric("Adj. R²", f"{ols_model.rsquared_adj:.4f}")
    with stats_col3:
        st.metric("F-statistic", f"{ols_model.fvalue:.2f}")
    with stats_col4:
        st.metric("Prob(F)", f"{ols_model.f_pvalue:.4f}")
    
    st.caption("Significance codes: *** p<0.001, ** p<0.01, * p<0.05, . p<0.10")
    st.caption(f"Observations: {int(ols_model.nobs)} | Residual Std. Error: {np.sqrt(ols_model.mse_resid):.3f}")
    
    st.divider()

    # --- SCATTER PLOT WITH REGRESSION LINES ---
    st.subheader("🌡️ Temperature vs Bowls Sold (Operating Days Only)")
    
    fig = px.scatter(model_df, x='Temp_High', y='Bowls_Sold', color='Precip_Type',
                     color_discrete_map={
                         "Clear": "#D3D3D3", "Flurries": "#E0F2FE", "Snow": "#7DD3FC",
                         "Mixed": "#38BDF8", "Rain": "#1E3A8A", "Heavy Snow": "#FF0000"
                     },
                     hover_name='Day_of_Week',
                     labels={'Temp_High': 'Temperature (°F)', 'Bowls_Sold': 'Bowls Sold'})
    
    # Regression Lines with interaction term
    temp_range = np.linspace(model_df['Temp_High'].min(), model_df['Temp_High'].max(), 100)
    temp_range_centered = temp_range - mean_temp  # Center for model prediction
    
    # Weekend + Clear weather
    y_weekend_clear = (ols_model.params['const'] + 
                      (ols_model.params['Temp_Centered'] * temp_range_centered) + 
                      (ols_model.params['is_weekend'] * 1) +
                      (ols_model.params['is_precipitation'] * 0) +
                      (ols_model.params['precip_temp_interaction'] * 0))
    
    # Midweek + Clear weather
    y_midweek_clear = (ols_model.params['const'] + 
                      (ols_model.params['Temp_Centered'] * temp_range_centered) +
                      (ols_model.params['is_precipitation'] * 0) +
                      (ols_model.params['precip_temp_interaction'] * 0))
    
    # Weekend + Precipitation (interaction effect kicks in)
    y_weekend_precip = (ols_model.params['const'] + 
                       (ols_model.params['Temp_Centered'] * temp_range_centered) + 
                       (ols_model.params['is_weekend'] * 1) +
                       (ols_model.params['is_precipitation'] * 1) +
                       (ols_model.params['precip_temp_interaction'] * temp_range_centered))
    
    # Midweek + Precipitation (interaction effect kicks in)
    y_midweek_precip = (ols_model.params['const'] + 
                       (ols_model.params['Temp_Centered'] * temp_range_centered) +
                       (ols_model.params['is_precipitation'] * 1) +
                       (ols_model.params['precip_temp_interaction'] * temp_range_centered))

    # Plot regression lines
    fig.add_trace(go.Scatter(x=temp_range, y=y_weekend_clear, name='Weekend (Clear)', line=dict(color='#DAA520', width=3)))
    fig.add_trace(go.Scatter(x=temp_range, y=y_midweek_clear, name='Midweek (Clear)', line=dict(color='#DAA520', width=3, dash='dash')))
    fig.add_trace(go.Scatter(x=temp_range, y=y_weekend_precip, name='Weekend (Precip)', line=dict(color='#1E88E5', width=3)))
    fig.add_trace(go.Scatter(x=temp_range, y=y_midweek_precip, name='Midweek (Precip)', line=dict(color='#1E88E5', width=3, dash='dash')))
    
    fig.update_traces(marker=dict(size=12, line=dict(width=1, color='black')))
    fig.update_layout(template="simple_white", hovermode="closest")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- TOP 10 DISHES SOLD ---
    st.subheader("🍽️ Top 10 Dishes Sold")
    top_dishes = sales_df.groupby('Item')['Qty'].sum().reset_index()
    top_dishes.columns = ['Dish', 'Quantity Sold']
    top_dishes = top_dishes.sort_values(by='Quantity Sold', ascending=False).head(10)
    top_dishes['Quantity Sold'] = top_dishes['Quantity Sold'].astype(int)
    st.dataframe(top_dishes, use_container_width=True, hide_index=True)

    st.divider()

    # --- TOP 10 REGULARS ---
    st.subheader("👥 Top 10 Regulars (Most Visits)")
    loyalty_data = sales_df[sales_df['Customer Name'].notna()]
    if not loyalty_data.empty:
        top_loyalty = loyalty_data.groupby('Customer Name').agg({'Transaction ID': 'nunique', 'Gross Sales': 'sum'}).reset_index()
        top_loyalty.columns = ['Customer Name', 'Total Visits', 'Total Spend']
        top_loyalty = top_loyalty.sort_values(by=['Total Visits', 'Total Spend'], ascending=False).head(10)
        st.dataframe(top_loyalty.style.format({'Total Spend': '${:,.2f}'}), use_container_width=True)
    else:
        st.info("No customer data available.")

except Exception as e:
    st.error(f"Dashboard Error: {e}")