#!/usr/bin/env python3
"""
Fetch 2025 weather data for Camp Hill, PA and generate CSV
"""
import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime, timedelta
import time

def celsius_to_fahrenheit(celsius):
    """Convert Celsius to Fahrenheit"""
    return round(celsius * 9/5 + 32)

def determine_precip_type(weather_desc):
    """Determine precipitation type from weather description"""
    weather_desc = weather_desc.lower()
    
    if 'heavy snow' in weather_desc or 'blizzard' in weather_desc:
        return 'Heavy Snow'
    elif 'snow' in weather_desc and 'flurr' not in weather_desc:
        return 'Snow'
    elif 'flurr' in weather_desc or 'snow shower' in weather_desc:
        return 'Flurries'
    elif 'rain' in weather_desc and 'snow' in weather_desc:
        return 'Mixed'
    elif 'sleet' in weather_desc or 'freezing rain' in weather_desc:
        return 'Mixed'
    elif 'rain' in weather_desc or 'drizzle' in weather_desc or 'shower' in weather_desc:
        return 'Rain'
    else:
        return 'None'

def fetch_month_data(month, year=2025):
    """Fetch weather data for a specific month"""
    url = f"https://www.timeanddate.com/weather/@5182928/historic?month={month}&year={year}"
    
    print(f"Fetching {year}-{month:02d}...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all day links
        day_links = soup.find_all('a', href=re.compile(r'historic\?hd=\d{8}'))
        
        month_data = {}
        
        for link in day_links:
            href = link.get('href')
            date_match = re.search(r'hd=(\d{4})(\d{2})(\d{2})', href)
            if date_match:
                year_str, month_str, day_str = date_match.groups()
                if int(year_str) == year and int(month_str) == month:
                    date_key = f"{year_str}-{month_str}-{day_str}"
                    month_data[date_key] = {'high_temp_c': None, 'weather': []}
        
        # Now fetch detailed data for each day
        for date_key in sorted(month_data.keys()):
            date_str = date_key.replace('-', '')
            day_url = f"https://www.timeanddate.com/weather/@5182928/historic?hd={date_str}"
            
            try:
                day_response = requests.get(day_url, timeout=30)
                day_response.raise_for_status()
                day_soup = BeautifulSoup(day_response.content, 'html.parser')
                
                # Find all temperature readings
                temp_cells = day_soup.find_all('td', string=re.compile(r'-?\d+\s*°C'))
                temps_c = []
                for cell in temp_cells:
                    temp_text = cell.get_text().strip()
                    temp_match = re.search(r'(-?\d+)\s*°C', temp_text)
                    if temp_match:
                        temps_c.append(int(temp_match.group(1)))
                
                # Find weather descriptions
                weather_cells = day_soup.find_all('td', string=re.compile(r'(rain|snow|clear|cloud|fog|sleet)', re.I))
                weather_descs = [cell.get_text().strip() for cell in weather_cells[:5]]  # Take first 5 to avoid duplicates
                
                if temps_c:
                    month_data[date_key]['high_temp_c'] = max(temps_c)
                    month_data[date_key]['weather'] = weather_descs
                
                # Be polite to the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  Warning: Could not fetch details for {date_key}: {e}")
                continue
        
        return month_data
        
    except Exception as e:
        print(f"  Error fetching month {month}: {e}")
        return {}

def generate_weather_csv():
    """Generate complete 2025 weather CSV"""
    
    all_data = {}
    
    # Fetch all 12 months
    for month in range(1, 13):
        month_data = fetch_month_data(month, 2025)
        all_data.update(month_data)
        time.sleep(1)  # Be polite between months
    
    # Generate CSV
    output_file = 'camp_hill_2025_weather.csv'
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Temp_High', 'Precip_Type'])
        
        # Generate all dates in 2025
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            if date_str in all_data and all_data[date_str]['high_temp_c'] is not None:
                high_temp_f = celsius_to_fahrenheit(all_data[date_str]['high_temp_c'])
                
                # Determine precipitation type from weather descriptions
                precip_type = 'None'
                for weather_desc in all_data[date_str]['weather']:
                    precip = determine_precip_type(weather_desc)
                    if precip != 'None':
                        precip_type = precip
                        break
                
                writer.writerow([date_str, high_temp_f, precip_type])
            else:
                # No data available, use placeholder
                writer.writerow([date_str, 'NA', 'None'])
            
            current_date += timedelta(days=1)
    
    print(f"\n✓ Generated {output_file}")
    print(f"✓ Contains {365} days of weather data")

if __name__ == '__main__':
    print("=" * 60)
    print("Fetching Camp Hill, PA Weather Data for 2025")
    print("=" * 60)
    generate_weather_csv()
