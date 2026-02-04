# 📤 Dashboard Sharing Guide

## 🚀 Sharing Options

### Option 1: Streamlit Community Cloud (Free Public Hosting)

**Best for:** Sharing with anyone, anytime

**Steps:**
1. Push code to GitHub (public or private repo)
2. Deploy at [share.streamlit.io](https://share.streamlit.io)
3. Share the URL (e.g., `https://bamboo-pho-dashboard.streamlit.app`)

**Pros:**
- ✅ Free and easy
- ✅ Always accessible
- ✅ Auto-updates when you push to GitHub
- ✅ No server maintenance

**Cons:**
- ⚠️ Data is publicly visible (unless you add authentication)
- ⚠️ Free tier has resource limits

**Privacy Note:** Consider anonymizing customer names before deploying publicly.

---

### Option 2: Local Network Sharing

**Best for:** Sharing with someone on your Wi-Fi network

**Current Network URL:**
```
http://192.168.1.70:8501
```

**Steps:**
1. Keep Streamlit running on your computer
2. Share the network URL with your brother
3. He opens it in his browser (must be on same Wi-Fi)

**Pros:**
- ✅ Instant sharing
- ✅ Data stays private (local network only)
- ✅ No deployment needed

**Cons:**
- ❌ Only works on same network
- ❌ Your computer must stay on

---

### Option 3: Ngrok Tunneling (Temporary Public Link)

**Best for:** Quick temporary sharing outside your network

**Steps:**
1. Install ngrok: `brew install ngrok` (Mac) or download from [ngrok.com](https://ngrok.com)
2. Run: `ngrok http 8501`
3. Share the generated URL (e.g., `https://abc123.ngrok-free.app`)

**Pros:**
- ✅ Works from anywhere
- ✅ No GitHub/deployment needed
- ✅ Quick setup

**Cons:**
- ❌ Link expires when you close ngrok
- ❌ Free tier has session limits
- ❌ Your computer must stay on

---

### Option 4: Send Files (Private Local Run)

**Best for:** Maximum privacy, brother has Python

**Steps:**
1. Zip the project:
   ```bash
   cd /Users/quoctran/Documents
   zip -r moms-dashboard.zip moms-dashboard/ -x "*.git*" "*.venv*" "*__pycache__*"
   ```

2. Send via email/Google Drive/Dropbox

3. Include setup instructions (see below)

**Pros:**
- ✅ Complete privacy (data stays on his machine)
- ✅ He can experiment without affecting your version
- ✅ No ongoing internet connection needed

**Cons:**
- ❌ Requires Python installation
- ❌ Manual setup required
- ❌ Updates require resending files

---

## 📋 Setup Instructions (Option 4)

**For your brother to run locally:**

### Prerequisites:
- Python 3.9+ installed
- Terminal/command line access

### Setup Steps:

1. **Unzip the folder:**
   ```bash
   unzip moms-dashboard.zip
   cd moms-dashboard
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Mac/Linux
   # OR
   .venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install streamlit pandas plotly statsmodels pytz numpy
   ```

4. **Run the dashboard:**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser:**
   - Streamlit will automatically open, or go to: `http://localhost:8501`

---

## 🔒 Privacy Options

### If Sharing Publicly (Option 1 or 3):

Consider anonymizing sensitive data:

#### Option A: Remove Customer Names
In `app.py`, comment out the "Top 10 Regulars" section:

```python
# --- TOP 10 REGULARS ---
# st.subheader("👥 Top 10 Regulars (Most Visits)")
# ... (comment out entire section)
```

#### Option B: Anonymize Customer Names
Replace real names with generic labels:

```python
# In the Top 10 Regulars section:
top_loyalty['Customer_Name'] = [f"Customer {i+1}" for i in range(len(top_loyalty))]
```

#### Option C: Add Password Protection
Use `streamlit-authenticator`:

```bash
pip install streamlit-authenticator
```

Then add authentication to `app.py` (requires additional setup).

---

## 🌐 Streamlit Cloud Deployment Guide

### Detailed Steps:

1. **Prepare GitHub Repository:**
   ```bash
   # In your project folder
   cd /Users/quoctran/Documents/moms-dashboard
   
   # Initialize git (if not already)
   git init
   
   # Create .gitignore
   echo ".venv/
   __pycache__/
   *.pyc
   .DS_Store" > .gitignore
   
   # Add files
   git add .
   git commit -m "Initial commit: Bamboo Pho Operations Dashboard"
   ```

2. **Create GitHub Repository:**
   - Go to [github.com](https://github.com)
   - Click "New repository"
   - Name: `moms-dashboard` (or your choice)
   - Keep it **Public** (for free Streamlit hosting)
   - Don't initialize with README (you already have files)

3. **Push to GitHub:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/moms-dashboard.git
   git branch -M main
   git push -u origin main
   ```

4. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Fill in:
     - **Repository:** YOUR_USERNAME/moms-dashboard
     - **Branch:** main
     - **Main file path:** app.py
   - Click "Deploy"

5. **Share the URL:**
   - Your app will be at: `https://YOUR_USERNAME-moms-dashboard.streamlit.app`
   - Share this link with your brother!

---

## 📊 What Your Brother Will See

When accessing the dashboard, he'll see:

1. **📊 Data Range Info** - Operating days analyzed
2. **📅 Tomorrow's Forecast** - Prediction tool
3. **🎯 Actual vs Predicted** - Recent model performance
4. **📈 Line Chart** - Bowls sold vs temperature over time
5. **📊 OLS Regression Results** - Statistical table with p-values
6. **🌡️ Scatter Plot** - Temperature analysis with 4 regression lines
7. **🍽️ Top 10 Dishes** - Most popular items
8. **👥 Top 10 Regulars** - Most frequent customers (⚠️ includes real names)

---

## 🔄 Updating After Deployment

### If deployed on Streamlit Cloud:

**Method 1: Automatic (Recommended)**
- Just push changes to GitHub:
  ```bash
  git add .
  git commit -m "Update dashboard"
  git push
  ```
- Streamlit Cloud auto-updates within 1-2 minutes!

**Method 2: Manual**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Click "Reboot app"

---

## 💡 Recommendations

### For Family Review (Private):
→ **Use Option 2 (Local Network)** or **Option 4 (Send Files)**
- Keeps customer data private
- No setup hassle for you
- Brother can explore freely

### For Portfolio/Public Showcase:
→ **Use Option 1 (Streamlit Cloud)**
- Professional URL to share
- Always accessible
- But **anonymize customer names first!**

### For Quick Demo Outside Network:
→ **Use Option 3 (Ngrok)**
- Fast temporary access
- No GitHub needed
- Good for quick review session

---

## ⚠️ Important Notes

### Data Privacy:
- Your CSV files contain:
  - Real customer names
  - Transaction amounts
  - Sales quantities
  - Business metrics

### Before Public Deployment:
1. Review all data for sensitivity
2. Consider anonymizing customer information
3. Remove or redact any confidential details
4. Test with sample/fake data first

### Resource Usage:
- Dashboard uses ~306 operating days of data
- Loads fine on free Streamlit tier
- Should be fast for your brother to access

---

## 🎯 Recommended Approach for Your Brother

**My suggestion:** Use **Option 1 (Streamlit Cloud)** with customer names anonymized

**Why:**
- He can access anytime from anywhere
- No setup required on his end
- You can update easily
- Professional presentation
- Free forever

**Steps:**
1. Anonymize customer names (5 minutes)
2. Push to GitHub (5 minutes)
3. Deploy to Streamlit Cloud (5 minutes)
4. Share URL with brother ✅

**Total time:** ~15 minutes for permanent sharing solution!

---

## 📞 Need Help?

If you encounter issues:
- Streamlit docs: [docs.streamlit.io](https://docs.streamlit.io)
- GitHub guides: [guides.github.com](https://guides.github.com)
- Ngrok docs: [ngrok.com/docs](https://ngrok.com/docs)
