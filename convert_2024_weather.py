import pandas as pd

# Load raw 2024 NOAA weather data
df = pd.read_csv('camp_hill_2024_weather.csv')

# Rename and process columns
df_processed = pd.DataFrame()
df_processed['Date'] = pd.to_datetime(df['DATE']).dt.strftime('%Y-%m-%d')
df_processed['Temp_High'] = df['TMAX']

# Map precipitation types based on weather codes
# WT01=Fog, WT02=Heavy Fog, WT03=Thunder, WT08=Smoke/Haze
def get_precip_type(row):
    # Check for specific precipitation types first
    if pd.notna(row.get('WT16')):  # Rain
        return 'Rain'
    if pd.notna(row.get('WT18')):  # Snow
        return 'Snow'
    if pd.notna(row.get('WT11')):  # Heavy Snow
        return 'Heavy Snow'
    if pd.notna(row.get('WT14')):  # Drizzle/Light Rain
        return 'Rain'
    
    # Check precipitation amount
    if pd.notna(row['PRCP']) and float(row['PRCP']) > 0:
        # If there's precipitation but no specific type, guess based on temp
        if row['TMAX'] <= 35:
            return 'Snow'
        elif row['TMAX'] <= 40:
            return 'Mixed'
        else:
            return 'Rain'
    
    return 'None'

df_processed['Precip_Type'] = df.apply(get_precip_type, axis=1)

# Save processed file
df_processed.to_csv('camp_hill_2024_weather_processed.csv', index=False)
print(f"Processed {len(df_processed)} days of 2024 weather data")
print(df_processed.head(10))
