#!/usr/bin/env python3
"""
Fetch 2025 weather data for Camp Hill, PA using Weather Underground or similar
Manual data entry template generator
"""
import csv
from datetime import datetime, timedelta

def create_weather_template():
    """Create a template CSV for manual data entry"""
    output_file = 'camp_hill_2025_weather_template.csv'
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Temp_High', 'Precip_Type'])
        writer.writerow(['# Instructions:', '', ''])
        writer.writerow(['# 1. Fill in Temp_High with daily high temperature in Fahrenheit', '', ''])
        writer.writerow(['# 2. Fill in Precip_Type with: None, Rain, Snow, Mixed, Flurries, or Heavy Snow', '', ''])
        writer.writerow(['# 3. Delete these instruction rows when done', '', ''])
        writer.writerow(['# 4. Save as: camp_hill_2025_weather.csv', '', ''])
        writer.writerow(['', '', ''])
        
        # Generate all dates in 2025
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            writer.writerow([date_str, '', 'None'])
            current_date += timedelta(days=1)
    
    print(f"✓ Created {output_file}")
    print(f"✓ Contains 365 days to fill in")
    print("\nTo get weather data:")
    print("1. Visit: https://www.wunderground.com/history/daily/us/pa/camp-hill")
    print("2. Select each month of 2025")
    print("3. Copy daily high temps and precipitation")
    print("4. Fill in the template")

if __name__ == '__main__':
    create_weather_template()
