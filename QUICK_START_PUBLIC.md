# Quick Start: Make Dashboard Public

## Fastest Method (5 minutes)

### Option 1: Using localtunnel (No account needed)

1. **Install localtunnel:**
   ```bash
   npm install -g localtunnel
   # OR if you have pip:
   pip install localtunnel
   ```

2. **Start dashboard:**
   ```bash
   cd deseq2_dashboard
   ./run_dashboard.sh 8050
   ```

3. **In a new terminal, create tunnel:**
   ```bash
   lt --port 8050
   ```

4. **Share the URL** that appears (e.g., `https://random-name.loca.lt`)

**That's it!** Your collaborators can now access the dashboard.

---

### Option 2: Using ngrok (More reliable)

1. **Sign up at https://ngrok.com** (free)

2. **Install ngrok:**
   ```bash
   # Download from https://ngrok.com/download
   # Or: brew install ngrok/ngrok/ngrok  # macOS
   ```

3. **Authenticate:**
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

4. **Start dashboard:**
   ```bash
   cd deseq2_dashboard
   ./run_dashboard.sh 8050
   ```

5. **In a new terminal, create tunnel:**
   ```bash
   ngrok http 8050
   ```

6. **Share the URL** (e.g., `https://abc123.ngrok.io`)

---

### Option 3: Using the automated script

```bash
cd deseq2_dashboard
./run_with_tunnel.sh localtunnel
# OR
./run_with_tunnel.sh ngrok
```

The script will start the dashboard and tunnel automatically.

---

## Adding Password Protection (Recommended)

Before sharing publicly, add authentication:

1. **Install auth package:**
   ```bash
   pip install dash-auth
   ```

2. **Modify `app.py`** - Add at the top:
   ```python
   import dash_auth
   
   # After creating app = dash.Dash(...)
   USERNAME_PASSWORD_PAIRS = [
       ('username1', 'password1'),
       ('username2', 'password2'),
   ]
   auth = dash_auth.BasicAuth(app, USERNAME_PASSWORD_PAIRS)
   ```

3. **Restart dashboard** - Now users need to log in

---

## Important Notes

⚠️ **Security:**
- Always add password protection before sharing publicly
- Consider data privacy - ensure data can be shared
- Check institutional policies

⚠️ **Tunnel Limitations:**
- **localtunnel**: URLs change each time you restart
- **ngrok (free)**: URLs change each time, limited connections
- **ngrok (paid)**: Can get persistent URLs

⚠️ **Permanent Solution:**
For a permanent URL, see `DEPLOYMENT_GUIDE.md` for setting up a reverse proxy on your cluster.

---

## Troubleshooting

**"Command not found" errors:**
- Make sure you've installed the tunneling tool
- Check your PATH

**"Port already in use":**
- Use a different port: `./run_dashboard.sh 8051`
- Update tunnel command: `lt --port 8051`

**Dashboard not accessible:**
- Make sure dashboard is running (check terminal)
- Verify tunnel is connected (check tunnel terminal)
- Try the tunnel URL in an incognito window


