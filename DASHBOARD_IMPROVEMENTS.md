# 🎯 Dashboard Improvements - February 2026

## ✅ Changes Made

### 1. **Updated Title** 
- **Old:** "Bamboo Pho Operations Dashboard"
- **New:** "Bamboo Pho and Tea Operations Dashboard"
- **Location:** Main dashboard title

---

### 2. **Error Flagging in Model Performance Table** 🚩
- **Added:** Flag column to highlight prediction errors > ±10%
- **Visual Indicator:** 🚩 emoji appears when error exceeds threshold
- **Location:** "Actual vs Predicted" table
- **Caption Added:** "🚩 = Error exceeds ±10%"

**How it works:**
```python
comparison_data['Flag'] = comparison_data['Error_Pct'].apply(
    lambda x: '🚩' if abs(x) > 10 else ''
)
```

**Example Output:**
| Date | Day | Actual | Predicted | Error | Error % | Flag |
|------|-----|--------|-----------|-------|---------|------|
| 2026-02-01 | Sun | 78 | 76 | +2 | +3.1% | |
| 2026-01-28 | Tue | 45 | 55 | -10 | -22.2% | 🚩 |

---

### 3. **Competitors Map** 🗺️

**New Section:** "Pho Competitors in Greater Harrisburg Area"

#### Features:
- **Interactive map** showing all 9 pho restaurants in the region
- **Normalized Rating:** Bubble size based on `(Rating × Reviews) / Max Reviews`
  - Weights ratings by popularity
  - Larger bubbles = better overall reputation
- **Average Pho Price:** Color scale from Green (cheap) to Red (expensive)
  - Calculated as: `(Pho Dac Biet L + Pho 2 Topping equivalent L) / 2`
- **Bamboo Pho highlight:** Gold star marker
- **Hover details:** Restaurant name, rating, reviews, normalized score, avg price, address

#### Metrics Displayed:
1. **Normalized Rating Calculation:**
   ```
   Normalized Score = (Google Rating × Number of Reviews) / Max Reviews in Dataset
   ```
   
   **Example:**
   - Bamboo: 4.7 × 330 / 715 = 2.17
   - LA Squared: 4.5 × 715 / 715 = 4.5 (highest)
   - Pho 99: 4.3 × 327 / 715 = 1.97

2. **Average Pho Price:**
   ```
   Avg Price = (Pho Dac Biet L + Pho 2 Topping L) / 2
   ```
   
   **Example:**
   - Bamboo: ($15.99 + $14.99) / 2 = $15.49
   - Little Saigon: ($14 + $13) / 2 = $13.50 (cheapest)
   - Pho La Vie: ($17.95 + $15.95) / 2 = $16.95 (most expensive)

#### Visual Elements:
- **Marker Size:** Proportional to normalized rating (larger = better reputation)
- **Marker Color:** Price gradient
  - 🟢 Green = Lower prices ($13.50-$14.50)
  - 🟡 Yellow = Mid-range ($14.50-$15.50)
  - 🔴 Red = Higher prices ($15.50-$16.95)
- **Gold Star:** Bamboo Pho and Tea (your location)

#### Map Configuration:
- **Center:** Harrisburg, PA area (40.26°N, 76.88°W)
- **Zoom:** 10.5 (shows greater Harrisburg region)
- **Style:** OpenStreetMap
- **Height:** 600px

#### Location Coordinates:
All 9 competitors geocoded with precise lat/long:
| Restaurant | Address | Coordinates |
|------------|---------|-------------|
| Bamboo Pho and Tea | Camp Hill | (40.2401, -76.9358) |
| Little Saigon | Harrisburg (Paxton St) | (40.2737, -76.8294) |
| Pho 7 Spice | Mechanicsburg | (40.2139, -77.0486) |
| Pho Kim's | Harrisburg (Derry St) | (40.2856, -76.7953) |
| Pho La Vie | Harrisburg (Allentown Blvd) | (40.3141, -76.7836) |
| Pho 99 | Harrisburg (S 13th St) | (40.2556, -76.8756) |
| Pho 3 Mien | Lemoyne | (40.2365, -76.8944) |
| Den Pho & Banh Mi | Harrisburg (Progress Ave) | (40.2661, -76.8458) |
| LA Squared | Harrisburg (Reily St) | (40.2638, -76.8867) |

---

## 📊 Data Source

**File:** `Pho Competitors.csv`

**Columns Used:**
- `Restaurants` - Restaurant name
- `Pho Dac Biet L` - Price of large Pho Dac Biet
- `Pho 2 Topping equivalent L` - Price of large 2-topping Pho
- `Address` - Full address (used for geocoding)
- `Google Reviews` - Number of reviews
- `Google Rating` - Average Google rating (1-5 stars)

---

## 🎯 Business Insights from Competitors Map

### **Market Position Analysis:**

#### Price Positioning:
- **Bamboo Average:** $15.49
- **Market Range:** $13.50 - $16.95
- **Position:** Mid-to-upper range (ranked 6th of 9)
- **Insight:** Bamboo is priced competitively but not the cheapest

#### Reputation Score:
- **Bamboo Normalized Score:** 2.17
- **Best Score:** LA Squared (4.5)
- **Bamboo Rank:** ~5th of 9
- **Insight:** Good rating (4.7) but fewer reviews than top competitors

#### Geographic Distribution:
- **Cluster:** 6 restaurants in Harrisburg proper
- **Suburban:** 3 restaurants (including Bamboo in Camp Hill)
- **Insight:** Less direct competition in Camp Hill area

### **Competitive Advantages:**
1. ✅ **Location:** Less saturated suburb market
2. ✅ **Rating:** 4.7 (above average)
3. ⚠️ **Reviews:** 330 (mid-tier - could grow with marketing)
4. ⚠️ **Price:** Higher than some competitors

### **Opportunities:**
1. **Increase Reviews:** Target 500+ reviews to boost normalized score
2. **Price Strategy:** Consider promotional pricing to compete with $13.50-$14.50 range
3. **Geographic Advantage:** Market to Camp Hill/West Shore customers (less competition)

---

## 🔄 Dashboard Layout (Updated)

```
🍜 Bamboo Pho and Tea Operations Dashboard
├── 📊 Data Range Info Banner
│
├── 📅 Tomorrow's Forecast
│   ├── Prediction Inputs (Left)
│   └── Historical Stats (Right)
│
├── 🎯 Model Performance: Actual vs Predicted  [WITH ERROR FLAGS 🚩]
│   ├── Last 7 Operating Days Table
│   └── Most Recent Day Metrics
│
├── 🗺️ Pho Competitors Map  [NEW SECTION]
│   ├── Interactive map with 9 restaurants
│   ├── Normalized ratings (bubble size)
│   ├── Average prices (color scale)
│   └── Legend and metrics
│
├── 📈 Pho Bowls Sold vs Temperature (Line Chart)
│
├── 📊 OLS Regression Results (Statistical Table)
│
├── 🌡️ Temperature vs Bowls (Scatter + 4 Regression Lines)
│
├── 🍽️ Top 10 Dishes Sold
│
└── 👥 Top 10 Regulars (Most Visits)
```

---

## 📦 Files Modified

- ✅ `app.py` - Added all three improvements
- ✅ `DASHBOARD_IMPROVEMENTS.md` - This documentation
- 📄 `Pho Competitors.csv` - Used as data source (no changes)

---

## 🚀 To Deploy Updates

**Push to GitHub:**
```bash
cd /Users/quoctran/Documents/moms-dashboard
git add .
git commit -m "Add competitors map, error flagging, and title update"
git push
```

**Streamlit Cloud will auto-update in ~1-2 minutes!**

---

## 🎨 Visual Examples

### Error Flagging:
```
🎯 Model Performance: Actual vs Predicted
─────────────────────────────────────────────────
Date       | Day | Actual | Predicted | Error % | Flag
2026-02-01 | Sun | 78     | 76        | +3.1%   |     
2026-01-31 | Fri | 71     | 73        | -2.8%   |     
2026-01-30 | Thu | 68     | 65        | +4.4%   |     
2026-01-29 | Wed | 48     | 51        | -5.6%   |     
2026-01-28 | Tue | 45     | 55        | -22.2%  | 🚩  
2026-01-26 | Sun | 85     | 82        | +3.5%   |     

🚩 = Error exceeds ±10%
```

### Competitors Map Legend:
```
🔵 Marker Size: Normalized Rating (Rating × Reviews / Max Reviews)
⭐ Gold Star: Bamboo Pho and Tea location
🎨 Color Scale: Average Pho Price (Red = Higher, Green = Lower)
💰 Price Range: $13.50 - $16.95
```

---

## ✅ Testing Checklist

Before sharing with your brother:

- [x] Title updated to "Bamboo Pho and Tea"
- [x] Error flags appear for predictions > ±10%
- [x] Competitors map loads with all 9 restaurants
- [x] Bamboo Pho marked with gold star
- [x] Bubble sizes reflect normalized ratings
- [x] Colors reflect average prices
- [x] Hover tooltips show all details
- [x] Map centered on Harrisburg area
- [x] Legend explains all visual elements

---

## 💡 Future Enhancement Ideas

Based on the competitors map:

1. **Track Competitor Ratings Over Time**
   - Monitor changes in ratings/reviews
   - Alert if competitors gain significant reviews

2. **Dynamic Pricing Insights**
   - Show how your prices compare to market average
   - Suggest optimal pricing based on rating/location

3. **Market Share Analysis**
   - Estimate market share based on reviews volume
   - Track growth relative to competitors

4. **Drive Time Analysis**
   - Add isochrones showing 5/10/15 min drive times
   - Identify overlap in service areas

---

**All improvements complete and ready to deploy!** 🎉
