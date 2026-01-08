# Deploying to Render.com - Step by Step Guide

Follow these steps to deploy your DESeq2 dashboard to Render.com.

## Step 1: Prepare Data Files

Run the preparation script to copy your data files:

```bash
cd deseq2_dashboard
chmod +x prepare_for_render.sh
./prepare_for_render.sh
```

This will:
- Create a `data/` directory in the dashboard folder
- Copy all DESeq2 TSV files from `../analysis_results/deseq2_results/`
- Create a `.renderignore` file

**Verify the files were copied:**
```bash
ls -la data/deseq2_results/primary/
ls -la data/deseq2_results/secondary/
```

## Step 2: Initialize Git Repository

If you don't already have a git repo:

```bash
cd deseq2_dashboard
git init
git add .
git commit -m "Initial commit - DESeq2 Dashboard"
```

## Step 3: Create GitHub Repository

1. Go to https://github.com and sign in
2. Click "New" repository
3. Name it (e.g., `deseq2-dashboard`)
4. **Don't** initialize with README (you already have files)
5. Click "Create repository"

## Step 4: Push to GitHub

```bash
# Add GitHub remote (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 5: Deploy on Render.com

1. **Sign up/Login:**
   - Go to https://render.com
   - Sign up with GitHub (easiest) or email

2. **Create New Web Service:**
   - Click "New +" button (top right)
   - Select "Web Service"

3. **Connect Repository:**
   - Click "Connect GitHub" (if not already connected)
   - Authorize Render to access your GitHub
   - Select your repository (`deseq2-dashboard`)

4. **Configure Settings:**
   
   **Basic Settings:**
   - **Name:** `deseq2-dashboard` (or your preferred name)
   - **Region:** Choose closest to your users
   - **Branch:** `main`
   - **Root Directory:** Leave empty (or `deseq2_dashboard` if repo is at root)
   
   **Build & Deploy:**
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py --host 0.0.0.0 --port $PORT`
   
   **Plan:**
   - **Free:** Good for testing (sleeps after 15 min inactivity)
   - **Starter ($7/month):** Always-on, better for production

5. **Environment Variables (Optional):**
   
   If you want to add authentication, click "Advanced" and add:
   - `DASH_USERNAME` = `your-username`
   - `DASH_PASSWORD` = `your-secure-password`
   
   Then modify `app.py` to use these (see `add_auth.py` for example)

6. **Click "Create Web Service"**
   - Render will start building (takes 5-10 minutes)
   - Watch the build logs for any errors

## Step 6: Access Your Dashboard

Once deployment completes:
- Your dashboard URL will be: `https://your-app-name.onrender.com`
- Render provides automatic HTTPS
- Share this URL with collaborators!

## Step 7: Update Data Files (When Needed)

When you have new DESeq2 results:

1. **On your cluster/local machine:**
   ```bash
   cd deseq2_dashboard
   ./prepare_for_render.sh  # Copy new files
   git add data/
   git commit -m "Update DESeq2 results"
   git push
   ```

2. **Render will automatically:**
   - Detect the new commit
   - Rebuild and redeploy
   - Update the dashboard (takes 5-10 min)

## Troubleshooting

### Build Fails - "Module not found"
- Check that `requirements.txt` includes all dependencies
- Verify Python version in `runtime.txt` matches Render's available versions

### Data Files Not Found
- Make sure `prepare_for_render.sh` ran successfully
- Check that `data/deseq2_results/` exists with `.tsv` files
- Verify file paths in build logs

### Dashboard Shows "No files found"
- Check build logs for file discovery
- Ensure TSV files are in `data/deseq2_results/primary/` and `secondary/`
- Verify file permissions (files should be readable)

### App Sleeps (Free Tier)
- Free tier apps sleep after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- Upgrade to Starter plan ($7/month) for always-on

### Custom Domain (Optional)
1. Go to your service settings on Render
2. Click "Custom Domains"
3. Add your domain
4. Follow DNS instructions

## Adding Authentication

To add password protection:

1. **Add environment variables on Render:**
   - `DASH_USERNAME` = `admin`
   - `DASH_PASSWORD` = `your-secure-password`

2. **Modify `app.py`** (add near top, after imports):
   ```python
   import dash_auth
   import os
   
   # After creating app = dash.Dash(...)
   USERNAME = os.environ.get('DASH_USERNAME', 'admin')
   PASSWORD = os.environ.get('DASH_PASSWORD', 'password')
   auth = dash_auth.BasicAuth(app, [(USERNAME, PASSWORD)])
   ```

3. **Redeploy:**
   - Commit the changes
   - Push to GitHub
   - Render auto-deploys

## Tips

- **Free Tier:** Good for testing and sharing with small teams
- **Starter Plan:** Recommended for production use (always-on, faster)
- **Auto-deploy:** Render automatically deploys on every git push to main branch
- **Build Logs:** Always check build logs if something goes wrong
- **Environment Variables:** Use them for secrets (passwords, API keys)

## Cost

- **Free Tier:** $0/month
  - Sleeps after 15 min inactivity
  - 750 hours/month compute time
  - Perfect for demos/testing
  
- **Starter Plan:** $7/month
  - Always-on
  - 100 GB bandwidth
  - Better for production

## Need Help?

- Render Docs: https://render.com/docs
- Render Status: https://status.render.com
- Check build logs for specific errors

---

**Your dashboard will be live at:** `https://your-app-name.onrender.com`

Happy deploying! 🚀

