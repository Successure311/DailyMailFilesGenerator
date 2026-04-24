# Deployment Guide: GitHub + Render + TiDB

## OVERVIEW
- **GitHub**: Code repository (source control)
- **Render**: Free web hosting (Python/Flask)
- **TiDB Cloud**: Database for dynamic data (AllStrategyDetails.xlsx data, margin data)
- **Fixed Data Files**: NF_ExpiryDate.csv, BNF_ExpiryDate.csv, SNX_ExpiryDate.csv (committed to repo, never change)

---

## PART 1: GITHUB SETUP

### Step 1.1: Create Required Files

Create `requirements.txt`:
```
flask>=2.0.0
pandas>=1.3.0
openpyxl>=3.0.0
pymysql>=1.0.0
```

Create `.gitignore`:
```
__pycache__/
*.pyc
.env
*.xlsx
MailFiles/
manual_lots.json
.vscode/
*.py.bak
```

### Step 1.2: Push to GitHub

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Flask app with TiDB integration"

# Add remote
git remote add origin https://github.com/Successure311/DailyMailFilesGenerator.git

# Push
git push -u origin main
```

### Step 1.3: Verify Files on GitHub
- NF_ExpiryDate.csv ✓ (committed)
- BNF_ExpiryDate.csv ✓ (committed)
- SNX_ExpiryDate.csv ✓ (committed)
- app.py ✓ (modified for TiDB)
- templates/index.html ✓
- static/app.js ✓
- static/styles.css ✓
- ClientWiseMargin.py ✓ (backup, can optionally remove)
- requirements.txt ✓ (new)
- .gitignore ✓ (new)

---

## PART 2: TiDB CLOUD SETUP

### Step 2.1: Access TiDB Cloud Console
1. Go to: https://tidbcloud.com
2. Login with your credentials
3. Navigate to your project

### Step 2.2: Get Connection Details
From your TiDB dashboard:
- Host: `gateway01.ap-southeast-1.prod.aws.tidbcloud.com`
- Port: `4000`
- User: `2hqkC7CYCyd33Y1.root`
- Password: `ED6Hesm31WIPzd8e`
- Database: `test`

### Step 2.3: Create Tables (Run in TiDB SQL Editor)

```sql
-- Drop existing tables if needed
DROP TABLE IF EXISTS strategies;
DROP TABLE IF EXISTS margin_data;
DROP TABLE IF EXISTS manual_lots;

-- Table for Strategies (replaces AllStrategyDetails.xlsx functionality)
CREATE TABLE strategies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    main_strategy VARCHAR(100),
    dte_wte INT,
    segment VARCHAR(50),
    strategy VARCHAR(100),
    exchange VARCHAR(50),
    symbol VARCHAR(50),
    entry_time VARCHAR(20),
    exit_time VARCHAR(20),
    strike VARCHAR(20),
    option_type VARCHAR(50),
    side VARCHAR(20),
    sl_percent VARCHAR(20),
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table for Margin Data (INDEX_MARGIN_DATA, STRATEGY_TRADE_COUNT, etc.)
CREATE TABLE margin_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_type VARCHAR(50),
    index_name VARCHAR(50),
    strategy_name VARCHAR(100),
    json_data JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table for Manual Lot Allocations
CREATE TABLE manual_lots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date VARCHAR(20),
    client_id VARCHAR(50),
    strategy VARCHAR(100),
    index_name VARCHAR(50),
    lot_count INT,
    margin_multiplier INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_allocation (date, client_id, strategy, index_name)
);
```

### Step 2.4: Download SSL Certificate
1. Download from: https://dl.academy.tisgrid.net/root/go根证书.pem
2. Or use the provided certificate path: `C:\Sagar\BackTestCode\TiDB\isrgrootx1.pem`
3. Upload this certificate to Render environment variables

---

## PART 3: RENDER DEPLOYMENT

### Step 3.1: Create Render Account
1. Go to: https://render.com
2. Sign up with GitHub account

### Step 3.2: Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `Successure311/DailyMailFilesGenerator`
3. Configure settings:

| Setting | Value |
|---------|-------|
| Name | `daily-mail-files-generator` |
| Region | Singapore (or closest) |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --host 0.0.0.0 --port $PORT` |

### Step 3.3: Environment Variables
Add these in Render dashboard:

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.11` | |
| `TIDB_HOST` | `gateway01.ap-southeast-1.prod.aws.tidbcloud.com` | |
| `TIDB_USER` | `2hqkC7CYCyd33Y1.root` | |
| `TIDB_PASSWORD` | `ED6Hesm31WIPzd8e` | |
| `TIDB_DATABASE` | `test` | |
| `TIDB_PORT` | `4000` | |

### Step 3.4: Free Tier Limitations
- Web service sleeps after 15 minutes of inactivity
- First deployment may take 2-3 minutes
- Free tier: 512MB RAM, 0.5 CPU

---

## PART 4: UPDATE APP.PY FOR RENDER

Modify `app.py` to use environment variables:

```python
import os

TIDB_CONFIG = {
    'host': os.environ.get('TIDB_HOST', 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'),
    'user': os.environ.get('TIDB_USER', '2hqkC7CYCyd33Y1.root'),
    'password': os.environ.get('TIDB_PASSWORD', 'ED6Hesm31WIPzd8e'),
    'database': os.environ.get('TIDB_DATABASE', 'test'),
    'port': int(os.environ.get('TIDB_PORT', '4000')),
    'charset': 'utf8mb4'
}
```

---

## PART 5: WORKFLOW

### When you need to update strategies (AllStrategyDetails.xlsx):

1. **Local Development:**
   - Update your local `AllStrategyDetails.xlsx`
   - Run `python app.py`
   - Test locally
   - Upload file through web UI OR update locally

2. **Commit & Deploy:**
   ```bash
   git add AllStrategyDetails.xlsx
   git commit -m "Update strategies"
   git push origin main
   ```
   - Render auto-deploys from main branch

3. **Strategy Data Sync:**
   - When file is uploaded via web UI, it's saved locally AND synced to TiDB
   - On app startup, data loads from TiDB (with local file as fallback)

### Fixed Data Files (CSV):
- These are committed to GitHub
- When you need to add new dates, edit locally and push to GitHub:
  ```bash
  # Edit NF_ExpiryDate.csv, BNF_ExpiryDate.csv, SNX_ExpiryDate.csv
  git add .
  git commit -m "Add new expiry dates"
  git push
  ```
- Render will pull latest on next deployment OR you can add a sync endpoint

---

## PART 6: MONITORING & TROUBLESHOOTING

### Check Deployment Status
1. Render Dashboard → Your Service → Logs

### Common Issues:

**"Connection refused" error:**
- Check TiDB firewall whitelist includes Render's IP
- Verify port 4000 is correct

**"Module not found" error:**
- Ensure `requirements.txt` is correct
- Check build logs on Render

**"TiDB SSL Certificate error":**
- Add certificate path to environment variables
- Or disable SSL verification (not recommended for production)

### Useful Render Commands:
- View logs: `render logs <service-name>`
- Redeploy: Push to GitHub main branch

---

## PART 7: SECURITY NOTES

1. **Never commit these to GitHub:**
   - Passwords
   - API keys
   - SSL certificates
   - Generated xlsx files

2. **Use Render Environment Variables:**
   - All TiDB credentials stored in Render dashboard
   - Not in code

3. **SSL Required:**
   - TiDB Cloud requires SSL connection
   - Certificate: `isrgrootx1.pem`

---

## QUICK REFERENCE

### URLs:
- App URL: `https://daily-mail-files-generator.onrender.com` (after deployment)
- GitHub Repo: `https://github.com/Successure311/DailyMailFilesGenerator`
- TiDB Console: `https://tidbcloud.com`

### Key Files:
| File | Purpose | Deployment |
|------|---------|------------|
| app.py | Main Flask app | GitHub → Render |
| AllStrategyDetails.xlsx | Dynamic strategy data | Local upload OR TiDB |
| NF_ExpiryDate.csv | Nifty expiry dates | GitHub (fixed) |
| BNF_ExpiryDate.csv | BankNifty expiry dates | GitHub (fixed) |
| SNX_ExpiryDate.csv | Sensex expiry dates | GitHub (fixed) |
| ClientWiseMargin.py | Margin data backup | GitHub (optional) |

### Database Tables:
| Table | Purpose |
|-------|---------|
| strategies | Store strategy details from AllStrategyDetails.xlsx |
| margin_data | Store INDEX_MARGIN_DATA, STRATEGY_TRADE_COUNT, etc. |
| manual_lots | Store lot allocations per date/client |