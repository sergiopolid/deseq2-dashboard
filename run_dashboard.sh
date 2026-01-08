#!/bin/bash
#==============================================================================
# DESeq2 Dashboard Startup Script
#==============================================================================
# 
# This script starts the interactive DESeq2 dashboard on a cluster node.
# The dashboard will be accessible via SSH port forwarding.
#
# Usage:
#   ./run_dashboard.sh [PORT]
#
# Default port: 8050
#
# To access from your local machine:
#   ssh -L 8050:localhost:8050 username@cluster-node
#   Then open: http://localhost:8050
#==============================================================================

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Set port (default: 8050)
PORT=${1:-8050}

echo "============================================================"
echo "DESeq2 Interactive Dashboard"
echo "============================================================"
echo "Starting dashboard on port $PORT"
echo ""
echo "To access from your local machine:"
echo "  1. Open a new terminal and run:"
echo "     ssh -L $PORT:localhost:$PORT $(whoami)@$(hostname)"
echo "  2. Open your browser and go to:"
echo "     http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please load Python module."
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import dash, plotly, pandas, numpy, dash_bootstrap_components" 2>/dev/null || {
    echo "Error: Required packages not installed."
    echo "Please install dependencies:"
    echo "  pip install -r requirements.txt"
    exit 1
}

echo "Dependencies OK"
echo ""

# Start the dashboard
python3 app.py --port $PORT --host 0.0.0.0 --debug

