# Making DESeq2 Dashboard Publicly Accessible

This guide covers several options for sharing your dashboard with collaborators over the internet.

## Option 1: Tunneling Services (Easiest - Temporary Access)

### A. Using ngrok (Recommended for Quick Sharing)

**Pros:**
- Very easy to set up
- Free tier available
- Works immediately
- HTTPS included

**Cons:**
- Free tier: URLs change each time you restart
- Free tier: Limited connections
- Requires ngrok account

**Setup:**

1. **Install ngrok:**
   ```bash
   # Download from https://ngrok.com/download
   # Or use package manager
   ```

2. **Get auth token** (sign up at https://dashboard.ngrok.com)

3. **Start dashboard:**
   ```bash
   cd deseq2_dashboard
   ./run_dashboard.sh 8050
   ```

4. **In another terminal, create tunnel:**
   ```bash
   ngrok http 8050
   ```

5. **Share the URL** (e.g., `https://abc123.ngrok.io`) with collaborators

**For persistent URL (paid plan):**
```bash
ngrok http 8050 --domain=your-custom-name.ngrok.io
```

### B. Using localtunnel (Free, No Account Needed)

**Pros:**
- Completely free
- No account required
- Easy to use

**Cons:**
- URLs change each time
- Less reliable than ngrok
- No custom domains

**Setup:**

1. **Install localtunnel:**
   ```bash
   npm install -g localtunnel
   # Or: pip install localtunnel
   ```

2. **Start dashboard:**
   ```bash
   cd deseq2_dashboard
   ./run_dashboard.sh 8050
   ```

3. **In another terminal, create tunnel:**
   ```bash
   lt --port 8050
   ```

4. **Share the URL** provided (e.g., `https://random-name.loca.lt`)

### C. Using Cloudflare Tunnel (Free, Persistent)

**Pros:**
- Free and unlimited
- Persistent URLs
- Good performance
- HTTPS included

**Cons:**
- Requires Cloudflare account
- More setup steps

**Setup:**

1. **Install cloudflared:**
   ```bash
   # Download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
   ```

2. **Start dashboard:**
   ```bash
   cd deseq2_dashboard
   ./run_dashboard.sh 8050
   ```

3. **Create tunnel:**
   ```bash
   cloudflared tunnel --url http://localhost:8050
   ```

4. **Share the URL** provided

## Option 2: Cloud Deployment (Permanent Solution)

### A. Deploy to Heroku

**Pros:**
- Free tier available
- Persistent URL
- Easy deployment
- Automatic HTTPS

**Cons:**
- Free tier has limitations (sleeps after inactivity)
- Requires moving code (data can stay on cluster)

**Setup:**

1. **Create `Procfile`:**
   ```
   web: python app.py --host 0.0.0.0 --port $PORT
   ```

2. **Create `runtime.txt`:**
   ```
   python-3.9.0
   ```

3. **Deploy:**
   ```bash
   heroku create your-dashboard-name
   git push heroku main
   heroku open
   ```

**Note:** You'll need to either:
- Copy data files to Heroku, OR
- Modify app to fetch data from cluster via API

### B. Deploy to Render.com (Free Alternative)

Similar to Heroku but with better free tier.

### C. Deploy to AWS/GCP/Azure

More complex but full control. Good for production use.

## Option 3: Cluster Web Server (Best for Long-term)

### A. Set up Nginx Reverse Proxy

**Pros:**
- Permanent URL
- Full control
- Best performance
- Can add authentication

**Cons:**
- Requires IT/admin access
- More complex setup
- May need SSL certificate

**Setup (requires IT support):**

1. **Configure Nginx:**
   ```nginx
   server {
       listen 80;
       server_name your-dashboard.your-domain.edu;
       
       location / {
           proxy_pass http://localhost:8050;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Set up SSL (Let's Encrypt):**
   ```bash
   certbot --nginx -d your-dashboard.your-domain.edu
   ```

3. **Add authentication (optional):**
   - Use HTTP Basic Auth
   - Or integrate with institutional SSO

### B. Use Existing Cluster Web Portal

Many clusters have JupyterHub or similar. Check if you can:
- Deploy Dash apps through JupyterHub
- Use cluster's existing web proxy

## Option 4: Hybrid Approach (Recommended)

**Best Practice:** Keep data on cluster, expose dashboard via tunnel or proxy.

1. **Dashboard runs on cluster** (data stays local)
2. **Use tunneling service** for external access
3. **Add authentication** for security

## Security Considerations

⚠️ **IMPORTANT:** Before making dashboard public:

1. **Add Authentication:**
   - Use Dash's built-in auth
   - Or add HTTP Basic Auth via reverse proxy
   - Or use institutional SSO

2. **Limit Access:**
   - Whitelist IP addresses if possible
   - Use password protection
   - Consider VPN requirement

3. **Data Privacy:**
   - Ensure data can be shared publicly
   - Consider anonymization if needed
   - Check institutional policies

## Quick Start Scripts

See `run_with_tunnel.sh` for automated tunneling setup.

## Recommendation

**For quick sharing (days/weeks):**
- Use **ngrok** or **Cloudflare Tunnel** (Option 1)

**For permanent sharing:**
- Set up **Nginx reverse proxy** on cluster (Option 3A)
- Or deploy to **Render.com** (Option 2B)

**For maximum security:**
- Use **cluster web server** with authentication (Option 3A)


