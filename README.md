# DESeq2 Interactive Dashboard

An interactive web application for exploring DESeq2 differential expression analysis results. Built with Python Dash and Plotly, providing R Shiny-like functionality for visualizing volcano plots, comparing fold changes across conditions, and browsing results in searchable tables.

## Features

- **Interactive Volcano Plots**: Explore differential expression with adjustable significance and fold change thresholds
- **Scatter Plot Comparisons**: Compare fold changes between two different comparisons side-by-side
- **Searchable Data Tables**: Browse and filter results by gene symbol
- **Auto-discovery**: Automatically finds all DESeq2 TSV files in primary/ and secondary/ directories
- **Export Functionality**: Download filtered results as CSV files
- **Responsive Design**: Clean, modern UI that works on different screen sizes

## Directory Structure

```
deseq2_dashboard/
├── app.py              # Main Dash application
├── utils.py            # Utility functions for file discovery and data loading
├── requirements.txt    # Python dependencies
├── run_dashboard.sh    # Cluster startup script
└── README.md          # This file
```

## Installation

### 1. Install Dependencies

```bash
cd deseq2_dashboard
pip install -r requirements.txt
```

Or if using a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Verify Data Files

The dashboard automatically discovers DESeq2 TSV files from:
- `../analysis_results/deseq2_results/primary/`
- `../analysis_results/deseq2_results/secondary/`

Make sure these directories contain your DESeq2 results files in TSV format with columns:
- `gene_symbol` (required)
- `log2FoldChange` (required)
- `baseMean`, `pvalue`, `padj` (optional but recommended)

## Sharing with Collaborators

**Want to make the dashboard publicly accessible?** See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

**Quick options:**
- **Temporary sharing (hours/days):** Use tunneling service (ngrok, localtunnel, Cloudflare)
- **Permanent sharing:** Set up reverse proxy on cluster or deploy to cloud
- **Secure sharing:** Add authentication (see `add_auth.py`)

**Quick start with tunnel:**
```bash
./run_with_tunnel.sh ngrok        # Requires ngrok account
./run_with_tunnel.sh localtunnel   # Free, no account needed
./run_with_tunnel.sh cloudflare    # Free, persistent URLs
```

## Usage

### Running on Cluster

1. **Start the dashboard server:**

```bash
cd deseq2_dashboard
chmod +x run_dashboard.sh
./run_dashboard.sh [PORT]
```

Default port is 8050. You can specify a different port:
```bash
./run_dashboard.sh 8051
```

2. **Set up SSH port forwarding** (from your local machine):

```bash
ssh -L 8050:localhost:8050 username@cluster-node
```

Replace `username` and `cluster-node` with your actual username and the cluster node where the dashboard is running.

3. **Open in browser:**

Navigate to: `http://localhost:8050`

### Running Locally

Simply run:

```bash
python3 app.py
```

Then open: `http://localhost:8050`

## Using the Dashboard

### Volcano Plot Tab

1. **Select Comparison**: Choose a DESeq2 results file from the dropdown
2. **Adjust Thresholds**: 
   - FDR threshold slider (default: 0.05)
   - log2FC threshold slider (default: 1.0)
3. **Search Genes**: Type a gene symbol to filter results
4. **Explore**: 
   - Hover over points to see gene details
   - Zoom and pan in the plot
   - View results in the table below
5. **Export**: Click "Export to CSV" to download filtered results

### Scatter Plot Comparison Tab

1. **Select Comparisons**: Choose two different DESeq2 files for X and Y axes
2. **Filter Options**:
   - Toggle to show only significant genes (padj < 0.05 in either comparison)
   - Set number of top genes to label (default: 40)
3. **Search Genes**: Filter by gene symbol
4. **Explore**:
   - View correlation between comparisons
   - Identify genes with different responses
   - See quadrant distribution
5. **Export**: Download merged comparison data

## Data Format

The dashboard expects DESeq2 TSV files with the following columns:

- **Required:**
  - `gene_symbol`: Gene identifier
  - `log2FoldChange`: Log2 fold change value

- **Optional (recommended):**
  - `baseMean`: Base mean expression
  - `pvalue`: P-value
  - `padj`: Adjusted p-value (FDR)
  - `lfcSE`: Standard error of log2FC
  - `stat`: Test statistic

## Troubleshooting

### Port Already in Use

If port 8050 is already in use, specify a different port:
```bash
./run_dashboard.sh 8051
```

### Module Not Found Errors

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### No Files Found

Check that DESeq2 results files exist in:
- `../analysis_results/deseq2_results/primary/`
- `../analysis_results/deseq2_results/secondary/`

Files should have `.tsv` extension.

### Connection Refused

If you can't connect via browser:
1. Verify the dashboard is running (check terminal output)
2. Ensure SSH port forwarding is set up correctly
3. Check firewall settings on the cluster

## Performance Notes

- Large datasets (30K+ genes) are handled efficiently with Plotly optimizations
- Data is cached after first load for faster subsequent interactions
- Tables are limited to 1000 rows for display (use search/filter to narrow down)
- Full data is available for export

## Technical Details

- **Framework**: Dash (Python web framework)
- **Visualization**: Plotly (interactive plots)
- **Styling**: Dash Bootstrap Components
- **Data Processing**: Pandas
- **Caching**: In-memory cache for loaded data files

## License

This dashboard is part of the Endothelial_LIFR_mouse project.

