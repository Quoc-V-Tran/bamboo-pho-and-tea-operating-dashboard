#!/usr/bin/env python3
"""
Fetch 2025 weather data from NOAA for Harrisburg, PA (near Camp Hill)
Requires NOAA API token (free to register at https://www.ncdc.noaa.gov/cdo-web/token)
"""
import requests
import csv
from datetime import datetime, timedelta
import time

# NOAA API Configuration
# Register for free token at: https://www.ncdc.noaa.gov/cdo-web/token
NOAA_TOKEN = "YOUR_TOKEN_HERE"  # Replace with your token
BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"

# Harrisburg International Airport station
STATION_ID = "GHCND:USW00014751"  # KMDT - Harrisburg International

def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit"""
    return round(celsius * 9/5 + 32)

def determine_precip_type(prcp_mm, snow_mm, temp_f):
    """Determine precipitation type based on amount and temperature"""
    if snow_mm > 50:  # Heavy snow (>2 inches)
        return 'Heavy Snow'
    elif snow_mm > 10:  # Significant snow
        return 'Snow'
    elif snow_mm > 0:  # Light snow
        return 'Flurries'
    elif prcp_mm > 0:
        if temp_f < 34:  # Near freezing with rain
            return 'Mixed'
        else:
            return 'Rain'
    else:
        return 'None'

def fetch_noaa_data(start_date, end_date):
    """Fetch weather data from NOAA API"""
    
    if NOAA_TOKEN == "YOUR_TOKEN_HERE":
        print("❌ ERROR: You need to set your NOAA API token")
        print("1. Register at: https://www.ncdc.noaa.gov/cdo-web/token")
        print("2. Check your email for the token")
        print("3. Edit this file and replace YOUR_TOKEN_HERE with your token")
        return None
    
    headers = {'token': NOAA_TOKEN}
    
    params = {
        'datasetid': 'GHCND',
        'stationid': STATION_ID,
        'startdate': start_date,
        'enddate': end_date,
        'datatypeid': 'TMAX,PRCP,SNOW',  # Max temp, precipitation, snowfall
        'units': 'metric',
        'limit': 1000
    }
    
    print(f"Fetching data from {start_date} to {end_date}...")
    
    try:
        response = requests.get(BASE_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def process_weather_data():
    """Fetch and process full year of 2025 data"""
    
    weather_dict = {}
    
    # Fetch data in monthly chunks (API limits)
    for month in range(1, 13):
        start = f"2025-{month:02d}-01"
        if month == 12:
            end = "2025-12-31"
        else:
            next_month = month + 1
            end_date = datetime(2025, next_month, 1) - timedelta(days=1)
            end = end_date.strftime("%Y-%m-%d")
        
        data = fetch_noaa_data(start, end)
        
        if data and 'results' in data:
            for item in data['results']:
                date = item['date'][:10]  # Extract YYYY-MM-DD
                datatype = item['datatype']
                value = item['value']
                
                if date not in weather_dict:
                    weather_dict[date] = {'tmax': None, 'prcp': 0, 'snow': 0}
                
                if datatype == 'TMAX':
                    weather_dict[date]['tmax'] = value / 10  # Convert to Celsius
                elif datatype == 'PRCP':
                    weather_dict[date]['prcp'] = value  # mm
                elif datatype == 'SNOW':
                    weather_dict[date]['snow'] = value  # mm
        
        time.sleep(0.5)  # Be polite to API
    
    # Write to CSV
    output_file = 'camp_hill_2025_weather.csv'
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Temp_High', 'Precip_Type'])
        
        # Generate all dates in 2025
        current_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            if date_str in weather_dict and weather_dict[date_str]['tmax'] is not None:
                temp_c = weather_dict[date_str]['tmax']
                temp_f = celsius_to_fahrenheit(temp_c)
                prcp = weather_dict[date_str]['prcp']
                snow = weather_dict[date_str]['snow']
                
                precip_type = determine_precip_type(prcp, snow, temp_f)
                
                writer.writerow([date_str, temp_f, precip_type])
            else:
                # Missing data
                writer.writerow([date_str, 'NA', 'None'])
            
            current_date += timedelta(days=1)
    
    print(f"\n✓ Generated {output_file}")
    print(f"✓ Contains 365 days of 2025 weather data")

if __name__ == '__main__':
    print("=" * 60)
    print("NOAA Weather Data Fetcher for Camp Hill, PA (2025)")
    print("=" * 60)
    print("\nIMPORTANT:")
    print("1. You need a free NOAA API token")
    print("2. Register at: https://www.ncdc.noaa.gov/cdo-web/token")
    print("3. Check your email and copy the token")
    print("4. Edit this file and replace YOUR_TOKEN_HERE")
    print("\n" + "=" * 60)
    
    process_weather_data()
