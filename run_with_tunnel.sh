#!/bin/bash
#==============================================================================
# DESeq2 Dashboard with Tunneling Service
#==============================================================================
# 
# This script starts the dashboard and optionally sets up a tunnel for
# public access using ngrok, localtunnel, or cloudflared.
#
# Usage:
#   ./run_with_tunnel.sh [TUNNEL_TYPE] [PORT]
#
# TUNNEL_TYPE options:
#   ngrok      - Uses ngrok (requires account, most reliable)
#   localtunnel - Uses localtunnel (free, no account)
#   cloudflare - Uses Cloudflare Tunnel (free, persistent)
#   none       - No tunnel (default, local only)
#
# Examples:
#   ./run_with_tunnel.sh ngrok
#   ./run_with_tunnel.sh localtunnel 8050
#   ./run_with_tunnel.sh cloudflare
#==============================================================================

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
TUNNEL_TYPE=${1:-none}
PORT=${2:-8050}

echo "============================================================"
echo "DESeq2 Dashboard with Public Tunnel"
echo "============================================================"
echo "Tunnel type: $TUNNEL_TYPE"
echo "Port: $PORT"
echo "============================================================"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to start dashboard in background
start_dashboard() {
    echo "Starting dashboard on port $PORT..."
    python3 app.py --port $PORT --host 0.0.0.0 &
    DASHBOARD_PID=$!
    echo "Dashboard started (PID: $DASHBOARD_PID)"
    sleep 3  # Wait for dashboard to start
    echo ""
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    if [ ! -z "$DASHBOARD_PID" ]; then
        kill $DASHBOARD_PID 2>/dev/null || true
    fi
    if [ ! -z "$TUNNEL_PID" ]; then
        kill $TUNNEL_PID 2>/dev/null || true
    fi
    exit
}

trap cleanup SIGINT SIGTERM

# Check Python and dependencies
if ! command_exists python3; then
    echo "Error: python3 not found"
    exit 1
fi

python3 -c "import dash, plotly, pandas, numpy, dash_bootstrap_components" 2>/dev/null || {
    echo "Error: Required packages not installed."
    echo "Run: pip install -r requirements.txt"
    exit 1
}

# Start dashboard
start_dashboard

# Set up tunnel based on type
case $TUNNEL_TYPE in
    ngrok)
        if ! command_exists ngrok; then
            echo "Error: ngrok not found. Install from https://ngrok.com/download"
            echo "Or run: brew install ngrok/ngrok/ngrok  # macOS"
            exit 1
        fi
        echo "Creating ngrok tunnel..."
        echo "Public URL will be displayed below:"
        echo ""
        ngrok http $PORT
        ;;
    
    localtunnel)
        if ! command_exists lt; then
            echo "Installing localtunnel..."
            if command_exists npm; then
                npm install -g localtunnel
            elif command_exists pip3; then
                pip3 install localtunnel
            else
                echo "Error: Need npm or pip to install localtunnel"
                exit 1
            fi
        fi
        echo "Creating localtunnel..."
        echo "Public URL will be displayed below:"
        echo ""
        lt --port $PORT
        ;;
    
    cloudflare)
        if ! command_exists cloudflared; then
            echo "Error: cloudflared not found."
            echo "Install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
            exit 1
        fi
        echo "Creating Cloudflare tunnel..."
        echo "Public URL will be displayed below:"
        echo ""
        cloudflared tunnel --url http://localhost:$PORT
        ;;
    
    none)
        echo "Running without tunnel (local access only)"
        echo ""
        echo "To access from your local machine:"
        echo "  1. SSH port forward: ssh -L $PORT:localhost:$PORT $(whoami)@$(hostname)"
        echo "  2. Open: http://localhost:$PORT"
        echo ""
        echo "Press Ctrl+C to stop"
        wait $DASHBOARD_PID
        ;;
    
    *)
        echo "Error: Unknown tunnel type: $TUNNEL_TYPE"
        echo "Options: ngrok, localtunnel, cloudflare, none"
        kill $DASHBOARD_PID 2>/dev/null || true
        exit 1
        ;;
esac

cleanup



