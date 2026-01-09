# Deploying to Web Server / Cloud Hosting

This guide covers deploying the DESeq2 dashboard to various web hosting platforms.

## Option 1: Render.com (Recommended - Free Tier Available)

**Pros:**
- Free tier available
- Persistent URL (yourname.onrender.com)
- Automatic HTTPS
- Easy deployment from Git
- Can handle data files

**Cons:**
- Free tier sleeps after 15 min inactivity (wakes on request)
- Paid tier needed for always-on

### Setup Steps:

1. **Create account** at https://render.com

2. **Prepare deployment files:**

   Create `Procfile` in `deseq2_dashboard/`:
   ```
   web: python app.py --host 0.0.0.0 --port $PORT
   ```

   Create `runtime.txt`:
   ```
   python-3.11.0
   ```

   Update `app.py` to read PORT from environment:
   ```python
   import os
   # At the bottom, replace app.run() with:
   if __name__ == "__main__":
       port = int(os.environ.get("PORT", 8050))
       app.run(debug=False, host="0.0.0.0", port=port)
   ```

3. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

4. **Deploy on Render:**
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Settings:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python app.py --host 0.0.0.0 --port $PORT`
     - Environment: Python 3
   - Click "Create Web Service"
   - Wait for deployment (5-10 min)

5. **Set environment variables** (if needed):
   - DASH_USERNAME, DASH_PASSWORD (for auth)
   - Any other config

6. **Access your dashboard:**
   - URL: `https://your-app-name.onrender.com`

---

## Option 2: Heroku (Classic Platform)

**Pros:**
- Well-established platform
- Free tier (limited)
- Easy Git-based deployment
- Add-ons available

**Cons:**
- Free tier discontinued (but Eco dyno is $5/month)
- Requires credit card for verification

### Setup Steps:

1. **Install Heroku CLI:**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Linux
   wget https://cli-assets.heroku.com/install.sh && sh install.sh
   ```

2. **Create deployment files:**

   `Procfile`:
   ```
   web: python app.py --host 0.0.0.0 --port $PORT
   ```

   `runtime.txt`:
   ```
   python-3.11.0
   ```

3. **Login and create app:**
   ```bash
   heroku login
   cd deseq2_dashboard
   heroku create your-dashboard-name
   ```

4. **Deploy:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```

5. **Open:**
   ```bash
   heroku open
   ```

---

## Option 3: PythonAnywhere (Free Tier Available)

**Pros:**
- Free tier for Python web apps
- Good for data-heavy apps
- Can upload files directly
- Persistent storage

**Cons:**
- Free tier has limitations (1 web app, limited CPU)
- Interface can be clunky

### Setup Steps:

1. **Create account** at https://www.pythonanywhere.com

2. **Upload files:**
   - Go to Files tab
   - Upload your `deseq2_dashboard` folder

3. **Install dependencies:**
   - Go to Bash console
   ```bash
   cd deseq2_dashboard
   pip3.10 install --user -r requirements.txt
   ```

4. **Create web app:**
   - Go to Web tab
   - Click "Add a new web app"
   - Choose "Flask" (we'll modify it)
   - Python 3.10

5. **Configure WSGI file:**
   - Edit the WSGI file:
   ```python
   import sys
   path = '/home/YOUR_USERNAME/deseq2_dashboard'
   if path not in sys.path:
       sys.path.insert(0, path)
   
   from app import app as application
   ```

6. **Configure web app:**
   - Source code: `/home/YOUR_USERNAME/deseq2_dashboard`
   - Working directory: `/home/YOUR_USERNAME/deseq2_dashboard`
   - WSGI file: (point to modified file above)

7. **Reload web app** - Your dashboard should be live!

---

## Option 4: Railway.app (Modern Alternative)

**Pros:**
- Very easy setup
- Good free tier
- Modern platform
- Automatic HTTPS

**Cons:**
- Newer platform (less established)
- Free tier has usage limits

### Setup Steps:

1. **Sign up** at https://railway.app

2. **Deploy from GitHub:**
   - Click "New Project"
   - "Deploy from GitHub repo"
   - Select your repo

3. **Configure:**
   - Root Directory: `deseq2_dashboard`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py --host 0.0.0.0 --port $PORT`

4. **Add environment variable:**
   - PORT (Railway sets this automatically)

5. **Deploy** - Done!

---

## Option 5: Fly.io (Good for Always-On)

**Pros:**
- Free tier with 3 VMs
- Always-on option
- Good performance
- Global deployment

**Cons:**
- More complex setup
- Requires Docker knowledge

### Setup Steps:

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Create `Dockerfile`:**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8080
   CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "8080"]
   ```

3. **Create `fly.toml`:**
   ```toml
   app = "your-dashboard-name"
   primary_region = "iad"
   
   [build]
   
   [http_service]
     internal_port = 8080
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
   ```

4. **Deploy:**
   ```bash
   fly launch
   fly deploy
   ```

---

## Option 6: Your Own Server/VPS

If you have access to a server (AWS EC2, DigitalOcean, etc.):

### Setup with Gunicorn (Recommended):

1. **Install dependencies:**
   ```bash
   pip install gunicorn
   ```

2. **Create `gunicorn_config.py`:**
   ```python
   bind = "0.0.0.0:8050"
   workers = 2
   timeout = 120
   ```

3. **Run with Gunicorn:**
   ```bash
   gunicorn app:server --config gunicorn_config.py
   ```

4. **Set up Nginx reverse proxy:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8050;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

5. **Add SSL with Let's Encrypt:**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

---

## Important: Data Files

### Option A: Include data in deployment (simpler)
- Copy data files to repo
- Works for small-medium datasets
- Data is bundled with app

### Option B: Remote data access (better for large data)
- Modify `utils.py` to fetch data from:
  - S3/Cloud storage
  - Your cluster via API
  - Shared network drive
  - Database

Example modification:
```python
def load_deseq2_file(file_path: str, use_cache: bool = True) -> pd.DataFrame:
    # If file_path is URL, download it
    if file_path.startswith('http'):
        import requests
        response = requests.get(file_path)
        # Parse from memory or temp file
    else:
        # Original file loading code
        ...
```

---

## Recommendations

**For Quick Setup (Best for Most Users):**
- **Render.com** - Easiest, free tier, persistent URL

**For Always-On Free:**
- **PythonAnywhere** or **Railway.app**

**For Production:**
- **Fly.io** or **Your own VPS** with Nginx

**For Maximum Control:**
- **AWS/GCP/Azure** with your own server setup

---

## Quick Comparison

| Platform | Free Tier | Always-On | Ease | Best For |
|----------|-----------|-----------|------|----------|
| Render | ✅ | ❌ (sleeps) | ⭐⭐⭐⭐⭐ | Quick deployment |
| Heroku | ❌ | ✅ (paid) | ⭐⭐⭐⭐ | Established projects |
| PythonAnywhere | ✅ | ✅ | ⭐⭐⭐ | Data-heavy apps |
| Railway | ✅ | Limited | ⭐⭐⭐⭐⭐ | Modern projects |
| Fly.io | ✅ | ✅ | ⭐⭐⭐ | Always-on needs |
| Own Server | Varies | ✅ | ⭐⭐ | Maximum control |

---

## Next Steps

1. Choose a platform from above
2. Follow the setup steps
3. Add authentication (see `add_auth.py`)
4. Configure data access (Option A or B above)
5. Deploy and share the URL!

Need help with a specific platform? The steps above should get you started!


