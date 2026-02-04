# 🌡️ Centered Temperature Model

## 📊 Model Enhancement: Temperature Centering

The temperature variable has been **centered** by subtracting the mean temperature from all observations. This makes the model coefficients much more interpretable!

---

## 🎯 What Changed

### Before (Uncentered):
```
Bowls_Sold = β₀ + β₁(Temp_High) + β₂(Precip) + β₃(Precip × Temp_High) + β₄(Weekend)
```

**Intercept (β₀):** Predicted bowls at 0°F ❄️🥶 (unrealistic!)

### After (Centered):
```
Bowls_Sold = β₀ + β₁(Temp_Centered) + β₂(Precip) + β₃(Precip × Temp_Centered) + β₄(Weekend)

where: Temp_Centered = Temp_High - Mean_Temperature
```

**Intercept (β₀):** Predicted bowls at **average temperature** 🌤️ (realistic!)

---

## 💡 Why Center Temperature?

### 1. **Interpretable Intercept**

**Before:**
- Intercept = Expected bowls when Temp = 0°F, no precip, midweek
- Problem: 0°F is outside the data range and not meaningful

**After:**
- Intercept = Expected bowls at **average temperature**, no precip, midweek
- Benefit: This is the "baseline" sales on a typical day!

### 2. **Better Interpretation of Precipitation Effect**

**Before:**
- β₂ = Precipitation effect at 0°F (not useful)

**After:**
- β₂ = Precipitation effect at **average temperature** (very useful!)

### 3. **Reduced Multicollinearity**

Centering reduces correlation between:
- Temperature and the interaction term
- Makes the model more stable
- Standard errors become smaller (more precise estimates)

---

## 📈 How It Works

### Example with Data:
```
Observed temperatures: 20°F, 30°F, 40°F, 50°F, 60°F
Mean temperature: 40°F
```

**Centered temperatures:**
```
20°F → -20 (20 degrees below average)
30°F → -10 (10 degrees below average)
40°F →   0 (exactly average)
50°F → +10 (10 degrees above average)
60°F → +20 (20 degrees above average)
```

---

## 🔍 Coefficient Interpretation After Centering

### Example Model Results:
```
β₀ (Intercept)           = 55.0 bowls
β₁ (Temp_Centered)       = -0.8 bowls/°F
β₂ (Precipitation)       = 8.0 bowls
β₃ (Precip × Temp_Cent)  = -0.3 bowls
β₄ (Weekend)             = 18.0 bowls

Mean Temperature = 42°F
```

### Interpretation:

**Intercept (55.0 bowls):**
- On an average temperature day (42°F), no precipitation, midweek
- **Expected sales = 55 bowls**
- This is your baseline!

**Temperature Effect (-0.8 bowls/°F):**
- For each degree **above average**, sales decrease by 0.8 bowls
- For each degree **below average**, sales increase by 0.8 bowls
- At 32°F (10° below avg): +8 bowls from temperature
- At 52°F (10° above avg): -8 bowls from temperature

**Precipitation (8.0 bowls):**
- At **average temperature** (42°F), precipitation adds 8 bowls
- This is the "base" precipitation effect

**Interaction Term (-0.3):**
- How precipitation's effect changes with temperature
- Negative means: Precipitation helps MORE when it's cold
- At 32°F (10° below avg): Precip adds 8 + (-0.3 × -10) = 11 bowls
- At 52°F (10° above avg): Precip adds 8 + (-0.3 × +10) = 5 bowls

**Weekend (18.0 bowls):**
- Friday/Saturday/Sunday adds 18 bowls vs Tuesday/Wednesday/Thursday

---

## 📊 Prediction Examples

### Scenario 1: Average Temp, No Precip, Midweek
```
Temp = 42°F → Temp_Centered = 0
Weekend = 0
Precip = 0

Bowls = 55 + (-0.8)(0) + 8(0) + (-0.3)(0) + 18(0)
      = 55 bowls
```

### Scenario 2: Cold Day, Snow, Weekend
```
Temp = 30°F → Temp_Centered = -12
Weekend = 1
Precip = 1

Bowls = 55 + (-0.8)(-12) + 8(1) + (-0.3)(1)(-12) + 18(1)
      = 55 + 9.6 + 8 + 3.6 + 18
      = 94.2 bowls
```

### Scenario 3: Warm Day, Rain, Midweek
```
Temp = 60°F → Temp_Centered = +18
Weekend = 0
Precip = 1

Bowls = 55 + (-0.8)(18) + 8(1) + (-0.3)(1)(18) + 18(0)
      = 55 - 14.4 + 8 - 5.4 + 0
      = 43.2 bowls
```

---

## 🎯 Dashboard Updates

### Prediction Section:
- Temperature input is **automatically centered** using the mean
- Mean temperature is shown in the help text
- Predictions use centered values internally

### Statistics Display:
- Intercept shows it's "at avg temp" in the label
- Precipitation impact is shown "at avg temp"
- All calculations use centered temperature

### OLS Results Table:
- Intercept labeled as: `Intercept (at XX.X°F avg temp)`
- Temperature labeled as: `Temperature (centered)`
- Makes it clear the model uses centering

### Regression Lines:
- Still plotted against original temperature (for readability)
- But calculated using centered values
- Lines are identical to before, just different intercept interpretation!

---

## 📚 Statistical Benefits

### 1. **Numerical Stability**
- Centered data has better numerical properties
- Reduces rounding errors in computation

### 2. **Easier Hypothesis Testing**
- Can test "is there an effect at average conditions?"
- More relevant than testing "at 0°F"

### 3. **Better Model Diagnostics**
- Residual plots are easier to interpret
- Cook's distance and leverage are more meaningful

### 4. **Improved Convergence**
- Optimization algorithms converge faster
- More stable coefficient estimates

---

## ⚠️ Important Notes

### Predictions Are Identical!
```
Centered model predictions = Uncentered model predictions
```

The predictions don't change - only the **interpretation** of coefficients!

### Original Temperature Still Used for Display:
- Scatter plot x-axis shows actual temperature (20°F, 30°F, etc.)
- Input box asks for actual temperature
- Centering happens internally

### Mean Temperature:
- Calculated from **operating days only** (Mondays excluded)
- Based on full dataset (2025 + 2026)
- Displayed throughout the dashboard

---

## 🧮 Mathematical Proof

### Uncentered Model:
```
ŷ = β₀ + β₁(X)
```

### Centered Model:
```
ŷ = β₀* + β₁*(X - X̄)
  = β₀* + β₁*X - β₁*X̄
  = (β₀* - β₁*X̄) + β₁*X
```

**Result:**
- β₁* = β₁ (slope unchanged!)
- β₀ = β₀* - β₁*X̄ (intercept shifts)

**Since β₁ is the same:**
```
Uncentered: ŷ = β₀ + β₁X
Centered:   ŷ = (β₀* - β₁*X̄) + β₁*(X - X̄) 
              = β₀* - β₁*X̄ + β₁*X - β₁*X̄
              = β₀ + β₁X  ✓ (same!)
```

---

## 📖 Example Interpretation Guide

### Reading the Intercept:

**Before centering:**
> "The intercept is 120 bowls. This represents predicted sales at 0°F, no precipitation, on a midweek day. Obviously, this is extrapolation and not realistic."

**After centering:**
> "The intercept is 55 bowls. This represents predicted sales at the average temperature (42°F), no precipitation, on a midweek day. This is our baseline performance."

### Reading the Temperature Coefficient:

**Before centering:**
> "The temperature coefficient is -0.8. For every degree increase from 0°F, sales decrease by 0.8 bowls."

**After centering:**
> "The temperature coefficient is -0.8. For every degree above the average temperature (42°F), sales decrease by 0.8 bowls. For every degree below average, sales increase by 0.8 bowls."

### Reading the Precipitation Coefficient:

**Before centering:**
> "The precipitation coefficient is 8.0. This represents the effect of precipitation at 0°F (after accounting for the interaction term)."

**After centering:**
> "The precipitation coefficient is 8.0. This represents the effect of precipitation at the average temperature (42°F). On an average-temp day, precipitation adds about 8 bowls."

---

## 🔄 To See the Centered Model

**Refresh your browser (F5)** to see:

1. ✅ **Realistic intercept** (at average temperature)
2. ✅ **Mean temperature displayed** in stats
3. ✅ **Precipitation effect** interpreted at average temp
4. ✅ **Updated regression table** with clear labels
5. ✅ **Same predictions** (just better interpretation!)

---

## 🎓 When to Use Centering

### Always Center When:
- ✅ The intercept at X=0 is meaningless (like temperature in Fahrenheit)
- ✅ You have interaction terms (reduces multicollinearity)
- ✅ You want to interpret main effects at "typical" values

### Don't Need to Center When:
- ❌ X=0 is meaningful (e.g., years of experience, where 0 = entry-level)
- ❌ You only care about predictions, not interpretation
- ❌ Simple models without interactions

---

## ✅ Summary

**What we did:**
- Centered temperature by subtracting the mean
- Updated interaction term to use centered temperature
- Modified all predictions and visualizations

**Benefits:**
- ✅ Intercept now represents typical baseline sales
- ✅ Precipitation effect is at average temperature
- ✅ Coefficients are more interpretable
- ✅ Reduced multicollinearity
- ✅ Same predictions as before!

**The model is now statistically sound AND easy to explain to stakeholders!** 🎉📊
