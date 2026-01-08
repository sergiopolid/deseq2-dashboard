#!/bin/bash
#==============================================================================
# Prepare Dashboard for Render.com Deployment
#==============================================================================
# 
# This script prepares the dashboard for deployment by:
# 1. Creating a data/ directory structure
# 2. Copying DESeq2 TSV files to the dashboard directory
# 3. Creating a .renderignore file
#
# Usage:
#   ./prepare_for_render.sh
#==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "Preparing Dashboard for Render.com Deployment"
echo "============================================================"
echo ""

# Create data directory structure
echo "Creating data directory structure..."
mkdir -p data/deseq2_results/primary
mkdir -p data/deseq2_results/secondary

# Find and copy DESeq2 files
SOURCE_DIR="../analysis_results/deseq2_results"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "⚠️  Warning: Source directory not found: $SOURCE_DIR"
    echo "   Make sure you're running this from the deseq2_dashboard directory"
    exit 1
fi

echo "Copying DESeq2 results files..."
echo "  From: $SOURCE_DIR"
echo "  To: data/deseq2_results/"

# Copy primary files
if [ -d "$SOURCE_DIR/primary" ]; then
    cp -v "$SOURCE_DIR"/primary/*.tsv data/deseq2_results/primary/ 2>/dev/null || echo "  No primary files found"
fi

# Copy secondary files
if [ -d "$SOURCE_DIR/secondary" ]; then
    cp -v "$SOURCE_DIR"/secondary/*.tsv data/deseq2_results/secondary/ 2>/dev/null || echo "  No secondary files found"
fi

# Create .renderignore file
echo ""
echo "Creating .renderignore file..."
cat > .renderignore <<EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Documentation (optional - uncomment if you don't want to deploy docs)
# *.md

# Scripts (not needed for deployment)
run_dashboard.sh
run_with_tunnel.sh
prepare_for_render.sh

# Environment
.env
.env.local

# Logs
*.log
EOF

echo "✓ Created .renderignore"

# Count files copied
PRIMARY_COUNT=$(find data/deseq2_results/primary -name "*.tsv" 2>/dev/null | wc -l)
SECONDARY_COUNT=$(find data/deseq2_results/secondary -name "*.tsv" 2>/dev/null | wc -l)

echo ""
echo "============================================================"
echo "✓ Preparation Complete!"
echo "============================================================"
echo "Files copied:"
echo "  Primary: $PRIMARY_COUNT files"
echo "  Secondary: $SECONDARY_COUNT files"
echo ""
echo "Next steps:"
echo "  1. Review the copied files in data/deseq2_results/"
echo "  2. Initialize git: git init"
echo "  3. Add files: git add ."
echo "  4. Commit: git commit -m 'Prepare for Render deployment'"
echo "  5. Push to GitHub"
echo "  6. Deploy on Render.com (see RENDER_DEPLOYMENT.md)"
echo "============================================================"

