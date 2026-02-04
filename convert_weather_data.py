#!/usr/bin/env python3
"""
Convert NOAA weather data to our dashboard format
"""
import csv
from datetime import datetime, timedelta

def determine_precip_type(prcp, snow, temp_f):
    """Determine precipitation type"""
    prcp = float(prcp) if prcp else 0.0
    snow = float(snow) if snow else 0.0
    
    if snow > 2.0:  # Heavy snow (>2 inches)
        return 'Heavy Snow'
    elif snow > 0.5:  # Significant snow
        return 'Snow'
    elif snow > 0.0:  # Light snow/flurries
        return 'Flurries'
    elif prcp > 0.0:
        if temp_f and temp_f <= 34:  # Near freezing with precip
            return 'Mixed'
        else:
            return 'Rain'
    else:
        return 'None'

def convert_weather_data():
    """Convert NOAA CSV to our format"""
    
    input_file = 'Jan 1 2025_ Jan 30 2026 Weather.csv'
    
    # Read NOAA data
    weather_dict = {}
    
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only use USC00363698 station (has TMAX data)
            if row['STATION'] == 'USC00363698':
                date = row['DATE']
                tmax = row['TMAX']
                prcp = row['PRCP']
                snow = row['SNOW']
                
                if tmax:  # Only include if we have temperature
                    temp_f = int(tmax)
                    precip_type = determine_precip_type(prcp, snow, temp_f)
                    weather_dict[date] = {
                        'temp': temp_f,
                        'precip': precip_type
                    }
    
    # Split into 2025 and 2026 files
    weather_2025 = []
    weather_2026 = []
    
    # Generate all dates
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 1, 31)
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        if date_str in weather_dict:
            temp = weather_dict[date_str]['temp']
            precip = weather_dict[date_str]['precip']
        else:
            # Missing data - use reasonable defaults
            temp = 'NA'
            precip = 'None'
        
        row = [date_str, temp, precip]
        
        if current_date.year == 2025:
            weather_2025.append(row)
        else:
            weather_2026.append(row)
        
        current_date += timedelta(days=1)
    
    # Write 2025 weather file
    with open('camp_hill_2025_weather.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Temp_High', 'Precip_Type'])
        writer.writerows(weather_2025)
    
    # Write 2026 January weather file
    with open('jan_weather.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Temp_High', 'Precip_Type'])
        writer.writerows(weather_2026[:31])  # Only January
    
    print("✅ Converted NOAA weather data successfully!")
    print(f"✅ Created camp_hill_2025_weather.csv ({len(weather_2025)} days)")
    print(f"✅ Updated jan_weather.csv ({len(weather_2026[:31])} days)")
    print(f"\n📊 Data coverage:")
    print(f"   2025: {len([r for r in weather_2025 if r[1] != 'NA'])}/{len(weather_2025)} days with data")
    print(f"   2026: {len([r for r in weather_2026[:31] if r[1] != 'NA'])}/{len(weather_2026[:31])} days with data")

if __name__ == '__main__':
    convert_weather_data()
