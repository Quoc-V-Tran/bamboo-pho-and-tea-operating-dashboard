# 🍜 Simple OLS Model with Interaction Term

## 📊 Model Specification

The model has been reverted to a **simple, interpretable** regression with an **interaction term**:

```
Bowls_Sold = β₀ + β₁(Temp_High) + β₂(Precip_Type) + β₃(Precip_Type × Temp_High) + β₄(Is_weekend)
```

---

## 🔍 Model Components

### 1. **Intercept (β₀)**
- **What:** Baseline bowls sold
- **Interpretation:** Expected bowls on a cold midweek clear day (at 0°F)

### 2. **Temperature (β₁)**
- **What:** Main temperature effect
- **Interpretation:** How bowls change per degree (on clear days)
- **Expected:** Negative (colder = more pho)

### 3. **Precipitation (β₂)**
- **What:** Precipitation main effect at 0°F
- **Interpretation:** Baseline difference between clear and precipitation days
- **Note:** This is modified by the interaction term!

### 4. **Precipitation × Temperature (β₃)** ⭐
- **What:** How precipitation's effect changes with temperature
- **Interpretation:** The "temperature slope" difference between clear and precipitation days
- **Key insight:** Precipitation might help sales more when it's cold vs warm

### 5. **Weekend (β₄)**
- **What:** Weekend boost
- **Interpretation:** Additional bowls sold on Fri/Sat/Sun vs Tue/Wed/Thu

---

## 🎯 Why the Interaction Term Matters

### The Problem Without Interaction:
```
Precipitation effect = constant (e.g., always +5 bowls)
```
But in reality:
- Cold + Rain → More comfort food appeal ☔❄️
- Warm + Rain → Less impact 🌧️☀️

### The Solution With Interaction:
```
Precipitation effect = β₂ + β₃ × Temperature
```

**Example:**
- At 20°F: Precip effect = β₂ + (β₃ × 20)
- At 60°F: Precip effect = β₂ + (β₃ × 60)

If β₃ is negative → Precipitation helps more when cold!

---

## 📈 Regression Lines in the Scatter Plot

The model now shows **4 regression lines**:

1. **Weekend + Clear** (Gold solid) 🟡
   - Fri/Sat/Sun with no precipitation
   - Formula: `β₀ + β₁(Temp) + β₄`

2. **Midweek + Clear** (Dark gray dashed) ⚫
   - Tue/Wed/Thu with no precipitation
   - Formula: `β₀ + β₁(Temp)`

3. **Weekend + Precipitation** (Blue solid) 🔵
   - Fri/Sat/Sun with rain/snow
   - Formula: `β₀ + β₁(Temp) + β₂ + β₃(Temp) + β₄`

4. **Midweek + Precipitation** (Dark blue dashed) 🔵
   - Tue/Wed/Thu with rain/snow
   - Formula: `β₀ + β₁(Temp) + β₂ + β₃(Temp)`

---

## 🧮 Coefficient Interpretation Guide

### Example Coefficients:
```
β₀ (Intercept)      = 80.0    → Baseline at 0°F
β₁ (Temp)           = -0.5    → -0.5 bowls per degree (on clear days)
β₂ (Precip)         = 15.0    → +15 bowls from precip at 0°F
β₃ (Precip×Temp)    = -0.2    → Interaction effect
β₄ (Weekend)        = 20.0    → +20 bowls on weekends
```

### Prediction Examples:

**Scenario 1: Tuesday, 30°F, Clear**
```
Bowls = 80 + (-0.5)(30) + 0 + 0 + 0
      = 80 - 15 + 0
      = 65 bowls
```

**Scenario 2: Saturday, 30°F, Clear**
```
Bowls = 80 + (-0.5)(30) + 0 + 0 + 20
      = 80 - 15 + 20
      = 85 bowls
```

**Scenario 3: Tuesday, 30°F, Snow**
```
Bowls = 80 + (-0.5)(30) + 15 + (-0.2)(30) + 0
      = 80 - 15 + 15 - 6 + 0
      = 74 bowls
```

**Scenario 4: Saturday, 30°F, Snow**
```
Bowls = 80 + (-0.5)(30) + 15 + (-0.2)(30) + 20
      = 80 - 15 + 15 - 6 + 20
      = 94 bowls
```

---

## 🔬 Understanding the Interaction Effect

### If β₃ < 0 (Negative):
```
Precipitation helps MORE when it's COLD
```

**Why?**
- Cold + Precipitation → Maximum comfort food appeal
- Warm + Precipitation → Less dramatic effect
- The slope difference grows as temperature decreases

**Visual:**
```
Bowls
  │
  │    ╱ (Clear - steep negative slope)
  │   ╱
  │  ╱   ╱ (Precip - less steep negative slope)
  │ ╱   ╱
  │╱___╱
  └─────────── Temperature
Cold        Warm
```

### If β₃ > 0 (Positive):
```
Precipitation helps MORE when it's WARM
```

---

## 🎯 Model Benefits

### Simplicity:
✅ Only 4 predictors (easy to explain)
✅ No lagged features (no data loss)
✅ No transformations (direct interpretation)

### Sophistication:
✅ Captures temperature-precipitation interaction
✅ Weekend effect included
✅ Multiple regression lines show different scenarios

### Interpretability:
✅ Clear coefficient meanings
✅ Easy to calculate by hand
✅ Direct business insights

---

## 📊 Binary Variable Encoding

### Precipitation (is_precipitation):
```
1 = Any precipitation (Mixed, Rain, Flurries, Snow, Heavy Snow)
0 = Clear weather
```

### Weekend (is_weekend):
```
1 = Friday, Saturday, Sunday
0 = Tuesday, Wednesday, Thursday
```

*Note: Mondays are excluded (restaurant closed)*

---

## 🎓 Statistical Insights

### Main Effects vs Interaction:
- **Main effect (β₁):** Temperature's effect when Precip = 0 (clear days)
- **Main effect (β₂):** Precipitation's effect when Temp = 0°F
- **Interaction (β₃):** How much the temperature slope changes with precipitation

### The Interaction Formula:
```
Total Temperature Effect = β₁ + β₃(Precip)
```

**On Clear Days:**
```
Temperature effect = β₁ + β₃(0) = β₁
```

**On Precipitation Days:**
```
Temperature effect = β₁ + β₃(1) = β₁ + β₃
```

So the slopes are **parallel when β₃ = 0**, but **different when β₃ ≠ 0**!

---

## 📈 Dashboard Features

### Tomorrow's Prediction:
- 🌡️ Temperature input
- ☔ Precipitation checkbox
- 📅 Weekend checkbox
- 🔮 Automatic calculation with interaction

### Model Stats Display:
- Average daily bowls
- Total bowls sold
- Weekend lift (β₄)
- Precipitation impact (β₂)
- Temperature effect (β₁)
- Model R²

### Scatter Plot:
- 4 regression lines (clear explanation of all scenarios)
- Color-coded by precipitation type
- Interactive hover details

---

## 🔄 To See the Simple Model

**Refresh your browser** (F5) or check the terminal - Streamlit may have auto-refreshed!

Look for:
- ✅ Simpler prediction inputs (no month selector)
- ✅ 4 regression lines in scatter plot
- ✅ Clear coefficient display
- ✅ Model R² showing goodness of fit

---

## 💡 Business Insights from the Model

### Key Questions This Model Answers:

1. **Does temperature affect pho sales?**
   - Look at β₁ (should be negative - colder = more pho)

2. **Do weekends boost sales?**
   - Look at β₄ (should be positive)

3. **Does precipitation help?**
   - Look at β₂ + β₃(Temp) for specific temperatures

4. **Does precipitation's effect depend on temperature?**
   - Look at β₃ (the interaction term!)
   - If significant → Yes! Cold rain/snow has different impact than warm rain

5. **How much can I predict?**
   - Look at R² (closer to 1 = better predictions)

---

## 🎯 Expected Model Performance

### Typical R² Range:
```
Simple Model (no interaction):  0.55-0.70
With Interaction Term:          0.60-0.75
```

The interaction term should add **+5-10 percentage points** to R² if the effect is real!

---

## ✅ Files Updated

- ✅ `app.py` - Reverted to simple model with interaction
- ✅ `SIMPLE_MODEL_EXPLANATION.md` - This documentation

---

**The model is now simple, interpretable, and includes the key interaction between temperature and precipitation!** 🎉📊
