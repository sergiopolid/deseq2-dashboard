"""
Interactive DESeq2 Dashboard
A Dash/Plotly web application for exploring DESeq2 differential expression results
"""

import dash
from dash import dcc, html, Input, Output, State
from dash import dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from pathlib import Path
import base64
import io
from matplotlib_venn import venn2, venn3
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

from utils import (
    discover_deseq2_files,
    load_deseq2_file,
    merge_comparisons,
    get_file_display_name,
    extract_degs
)

# Initialize Dash app with Bootstrap theme
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)

app.title = "DESeq2 Interactive Dashboard"

# Get available files
available_files = discover_deseq2_files()

# Create file options for dropdowns with better formatting
file_options = []
for path, cat, name in available_files:
    # Create a shorter label: category abbreviation + cleaned name
    cat_abbrev = "P" if cat == "primary" else "S"
    # Truncate name if still too long
    short_name = name if len(name) <= 45 else name[:42] + "..."
    label = f"[{cat_abbrev}] {short_name}"
    file_options.append({"label": label, "value": path})

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("DESeq2 Interactive Dashboard", className="mb-4"),
            html.P(
                "Explore differential expression results with interactive volcano plots, "
                "scatter plot comparisons, and searchable data tables.",
                className="text-muted"
            )
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Volcano Plot", tab_id="volcano-tab"),
                dbc.Tab(label="Scatter Comparison", tab_id="scatter-tab"),
                dbc.Tab(label="Venn Diagram", tab_id="venn-tab"),
            ], id="main-tabs", active_tab="volcano-tab")
        ])
    ], className="mb-4"),
    
    # Content area
    html.Div(id="tab-content"),
    
    # Store for selected data
    dcc.Store(id="volcano-data-store"),
    dcc.Store(id="scatter-data-store"),
    dcc.Store(id="venn-data-store"),
    
], fluid=True)


# ============================================================================
# Volcano Plot Tab
# ============================================================================

def create_volcano_tab():
    """Create the volcano plot tab layout."""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Controls"),
                dbc.CardBody([
                    html.Label("Select Comparison:", className="fw-bold"),
                    dcc.Dropdown(
                        id="volcano-file-dropdown",
                        options=file_options,
                        value=file_options[0]["value"] if file_options else None,
                        placeholder="Select a comparison file...",
                        searchable=True,
                        clearable=False,
                        style={"fontSize": "12px"}
                    ),
                    html.Br(),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("FDR Threshold:", className="fw-bold"),
                            dcc.Slider(
                                id="volcano-fdr-slider",
                                min=0.001,
                                max=0.35,
                                step=0.001,
                                value=0.05,
                                marks={0.001: "0.001", 0.01: "0.01", 0.05: "0.05", 0.1: "0.1", 0.2: "0.2", 0.35: "0.35"},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ]),
                        dbc.Col([
                            html.Label("log2FC Threshold:", className="fw-bold"),
                            dcc.Slider(
                                id="volcano-lfc-slider",
                                min=0,
                                max=3,
                                step=0.1,
                                value=1.0,
                                marks={0: "0", 1: "1", 2: "2", 3: "3"},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ])
                    ]),
                    html.Br(),
                    
                    html.Label("Search Gene:", className="fw-bold"),
                    dbc.Input(
                        id="volcano-gene-search",
                        type="text",
                        placeholder="Enter gene symbol...",
                        debounce=True
                    ),
                    html.Br(),
                    
                    html.Label("Number of top genes to label:", className="fw-bold"),
                    dbc.Input(
                        id="volcano-n-labels",
                        type="number",
                        min=0,
                        max=100,
                        value=20,
                        step=5
                    ),
                    html.Br(),
                    html.Hr(),
                    
                    html.H6("Axis Limits (optional)", className="fw-bold mt-3"),
                    dbc.Checklist(
                        options=[{"label": "Use custom axis limits", "value": "custom-axes"}],
                        id="volcano-custom-axes",
                        switch=True
                    ),
                    html.Br(),
                    dbc.Row([
                        dbc.Col([
                            html.Label("X-axis min:", className="small"),
                            dbc.Input(
                                id="volcano-xmin",
                                type="number",
                                step=0.5,
                                placeholder="Auto"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("X-axis max:", className="small"),
                            dbc.Input(
                                id="volcano-xmax",
                                type="number",
                                step=0.5,
                                placeholder="Auto"
                            )
                        ], width=6)
                    ]),
                    html.Br(),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Y-axis min:", className="small"),
                            dbc.Input(
                                id="volcano-ymin",
                                type="number",
                                step=0.5,
                                placeholder="Auto"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Y-axis max:", className="small"),
                            dbc.Input(
                                id="volcano-ymax",
                                type="number",
                                step=0.5,
                                placeholder="Auto"
                            )
                        ], width=6)
                    ]),
                    html.Br(),
                    
                    dbc.Button(
                        "Export to CSV",
                        id="volcano-export-btn",
                        color="primary",
                        className="mt-2"
                    ),
                    dcc.Download(id="volcano-download")
                ])
            ], className="mb-4")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Volcano Plot"),
                dbc.CardBody([
                    dcc.Loading(
                        id="volcano-loading",
                        type="default",
                        children=dcc.Graph(id="volcano-plot")
                    )
                ])
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardHeader("Results Table"),
                dbc.CardBody([
                    html.Div(id="volcano-table-container")
                ])
            ])
        ], width=9)
    ])


# ============================================================================
# Scatter Plot Tab
# ============================================================================

def create_scatter_tab():
    """Create the scatter plot comparison tab layout."""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Controls"),
                dbc.CardBody([
                    html.Label("X-axis Comparison:", className="fw-bold"),
                    dcc.Dropdown(
                        id="scatter-x-dropdown",
                        options=file_options,
                        value=file_options[0]["value"] if len(file_options) > 0 else None,
                        placeholder="Select first comparison...",
                        searchable=True,
                        clearable=False,
                        style={"fontSize": "12px"}
                    ),
                    html.Br(),
                    
                    html.Label("Y-axis Comparison:", className="fw-bold"),
                    dcc.Dropdown(
                        id="scatter-y-dropdown",
                        options=file_options,
                        value=file_options[1]["value"] if len(file_options) > 1 else None,
                        placeholder="Select second comparison...",
                        searchable=True,
                        clearable=False,
                        style={"fontSize": "12px"}
                    ),
                    html.Br(),
                    
                    dbc.Checklist(
                        options=[{"label": "Show only significant genes (padj < 0.05 in either)", "value": "sig-only"}],
                        id="scatter-sig-filter",
                        switch=True
                    ),
                    html.Br(),
                    
                    html.Label("Number of top genes to label:", className="fw-bold"),
                    dbc.Input(
                        id="scatter-n-labels",
                        type="number",
                        min=0,
                        max=100,
                        value=40,
                        step=5
                    ),
                    html.Br(),
                    
                    html.Label("Search Gene:", className="fw-bold"),
                    dbc.Input(
                        id="scatter-gene-search",
                        type="text",
                        placeholder="Enter gene symbol...",
                        debounce=True
                    ),
                    html.Br(),
                    html.Hr(),
                    
                    html.H6("Axis Limits (optional)", className="fw-bold mt-3"),
                    dbc.Checklist(
                        options=[{"label": "Use custom axis limits", "value": "custom-axes"}],
                        id="scatter-custom-axes",
                        switch=True
                    ),
                    html.Br(),
                    dbc.Row([
                        dbc.Col([
                            html.Label("X-axis min:", className="small"),
                            dbc.Input(
                                id="scatter-xmin",
                                type="number",
                                step=0.5,
                                placeholder="Auto"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("X-axis max:", className="small"),
                            dbc.Input(
                                id="scatter-xmax",
                                type="number",
                                step=0.5,
                                placeholder="Auto"
                            )
                        ], width=6)
                    ]),
                    html.Br(),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Y-axis min:", className="small"),
                            dbc.Input(
                                id="scatter-ymin",
                                type="number",
                                step=0.5,
                                placeholder="Auto"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Y-axis max:", className="small"),
                            dbc.Input(
                                id="scatter-ymax",
                                type="number",
                                step=0.5,
                                placeholder="Auto"
                            )
                        ], width=6)
                    ]),
                    html.Br(),
                    
                    dbc.Button(
                        "Export to CSV",
                        id="scatter-export-btn",
                        color="primary",
                        className="mt-2"
                    ),
                    dcc.Download(id="scatter-download")
                ])
            ], className="mb-4")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Scatter Plot Comparison"),
                dbc.CardBody([
                    dcc.Loading(
                        id="scatter-loading",
                        type="default",
                        children=dcc.Graph(id="scatter-plot")
                    )
                ])
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardHeader("Merged Results Table"),
                dbc.CardBody([
                    html.Div(id="scatter-table-container")
                ])
            ])
        ], width=9)
    ])


# ============================================================================
# Venn Diagram Tab
# ============================================================================

def create_venn_tab():
    """Create the Venn diagram tab layout."""
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Controls"),
                dbc.CardBody([
                    html.Label("Number of Comparisons:", className="fw-bold"),
                    dcc.Dropdown(
                        id="venn-n-comparisons",
                        options=[
                            {"label": "2 Comparisons", "value": 2},
                            {"label": "3 Comparisons", "value": 3}
                        ],
                        value=2,
                        clearable=False
                    ),
                    html.Br(),
                    
                    html.Label("Comparison 1:", className="fw-bold"),
                    dcc.Dropdown(
                        id="venn-comp1-dropdown",
                        options=file_options,
                        value=file_options[0]["value"] if file_options else None,
                        placeholder="Select first comparison...",
                        searchable=True,
                        clearable=False,
                        style={"fontSize": "12px"}
                    ),
                    html.Br(),
                    
                    html.Label("Comparison 2:", className="fw-bold"),
                    dcc.Dropdown(
                        id="venn-comp2-dropdown",
                        options=file_options,
                        value=file_options[1]["value"] if len(file_options) > 1 else None,
                        placeholder="Select second comparison...",
                        searchable=True,
                        clearable=False,
                        style={"fontSize": "12px"}
                    ),
                    html.Div(id="venn-comp3-container"),
                    html.Br(),
                    
                    html.Hr(),
                    html.H6("DEG Thresholds", className="fw-bold mt-3"),
                    
                    html.Label("FDR Threshold:", className="fw-bold small"),
                    dcc.Slider(
                        id="venn-fdr-slider",
                        min=0.001,
                        max=0.35,
                        step=0.001,
                        value=0.05,
                        marks={0.001: "0.001", 0.01: "0.01", 0.05: "0.05", 0.1: "0.1", 0.2: "0.2", 0.35: "0.35"},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    
                    html.Label("log2FC Threshold:", className="fw-bold small mt-2"),
                    dcc.Slider(
                        id="venn-lfc-slider",
                        min=0,
                        max=3,
                        step=0.1,
                        value=1.0,
                        marks={0: "0", 1: "1", 2: "2", 3: "3"},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.Br(),
                    
                    dbc.Button(
                        "Export Overlap Genes",
                        id="venn-export-btn",
                        color="primary",
                        className="mt-2"
                    ),
                    dcc.Download(id="venn-download")
                ])
            ], className="mb-4")
        ], width=3),
        
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Venn Diagram"),
                dbc.CardBody([
                    dcc.Loading(
                        id="venn-loading",
                        type="default",
                        children=html.Div(id="venn-diagram-container")
                    )
                ])
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardHeader("Gene Lists"),
                dbc.CardBody([
                    html.Div(id="venn-gene-lists")
                ])
            ])
        ], width=9)
    ])


# ============================================================================
# Callbacks
# ============================================================================

@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab")
)
def update_tab_content(active_tab):
    """Update content based on selected tab."""
    if active_tab == "volcano-tab":
        return create_volcano_tab()
    elif active_tab == "scatter-tab":
        return create_scatter_tab()
    elif active_tab == "venn-tab":
        return create_venn_tab()
    return html.Div("Select a tab")


@app.callback(
    [Output("volcano-plot", "figure"),
     Output("volcano-data-store", "data"),
     Output("volcano-table-container", "children")],
    [Input("volcano-file-dropdown", "value"),
     Input("volcano-fdr-slider", "value"),
     Input("volcano-lfc-slider", "value"),
     Input("volcano-gene-search", "value"),
     Input("volcano-n-labels", "value"),
     Input("volcano-custom-axes", "value"),
     Input("volcano-xmin", "value"),
     Input("volcano-xmax", "value"),
     Input("volcano-ymin", "value"),
     Input("volcano-ymax", "value")]
)
def update_volcano_plot(file_path, fdr_threshold, lfc_threshold, gene_search, n_labels,
                         custom_axes, xmin, xmax, ymin, ymax):
    """Update volcano plot and table based on controls."""
    if not file_path:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Please select a comparison file",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return empty_fig, None, html.Div("No data loaded")
    
    try:
        # Load data
        df = load_deseq2_file(file_path)
        
        # Apply gene search filter
        if gene_search:
            search_term = gene_search.upper()
            df = df[df['gene_symbol'].str.upper().str.contains(search_term, na=False)]
        
        # Calculate -log10(padj) or -log10(pvalue)
        if 'padj' in df.columns:
            df['neg_log10_p'] = -np.log10(df['padj'].replace(0, np.nan))
            p_col = 'padj'
        elif 'pvalue' in df.columns:
            df['neg_log10_p'] = -np.log10(df['pvalue'].replace(0, np.nan))
            p_col = 'pvalue'
        else:
            df['neg_log10_p'] = np.nan
            p_col = None
        
        # Determine significance
        if p_col:
            df['significant'] = (df[p_col] < fdr_threshold) & (np.abs(df['log2FoldChange']) > lfc_threshold)
            df['direction'] = 'Not significant'
            df.loc[(df['significant']) & (df['log2FoldChange'] > 0), 'direction'] = 'Up-regulated'
            df.loc[(df['significant']) & (df['log2FoldChange'] < 0), 'direction'] = 'Down-regulated'
        else:
            df['significant'] = False
            df['direction'] = 'Not significant'
        
        # Calculate ranking for top genes (combine significance and fold change)
        # Use regulation strength: -log10(p) * |log2FC|
        df['regulation_strength'] = df['neg_log10_p'] * df['log2FoldChange'].abs()
        df['regulation_strength'] = df['regulation_strength'].fillna(0)
        
        # Sort by regulation strength and select top N for labeling
        df_sorted = df.sort_values('regulation_strength', ascending=False)
        n_labels = n_labels if n_labels is not None and n_labels > 0 else 0
        top_genes = df_sorted.head(n_labels)['gene_symbol'].values if n_labels > 0 else []
        
        # Create volcano plot
        fig = go.Figure()
        
        # Not significant
        not_sig = df[~df['significant']]
        if len(not_sig) > 0:
            fig.add_trace(go.Scatter(
                x=not_sig['log2FoldChange'],
                y=not_sig['neg_log10_p'],
                mode='markers',
                marker=dict(color='gray', size=3, opacity=0.5),
                name='Not significant',
                text=not_sig['gene_symbol'],
                hovertemplate='<b>%{text}</b><br>' +
                              'log2FC: %{x:.3f}<br>' +
                              '-log10(p): %{y:.3f}<br>' +
                              '<extra></extra>'
            ))
        
        # Up-regulated
        up_sig = df[(df['significant']) & (df['log2FoldChange'] > 0)]
        if len(up_sig) > 0:
            fig.add_trace(go.Scatter(
                x=up_sig['log2FoldChange'],
                y=up_sig['neg_log10_p'],
                mode='markers',
                marker=dict(color='red', size=5, opacity=0.7),
                name='Up-regulated',
                text=up_sig['gene_symbol'],
                hovertemplate='<b>%{text}</b><br>' +
                              'log2FC: %{x:.3f}<br>' +
                              '-log10(p): %{y:.3f}<br>' +
                              '<extra></extra>'
            ))
        
        # Down-regulated
        down_sig = df[(df['significant']) & (df['log2FoldChange'] < 0)]
        if len(down_sig) > 0:
            fig.add_trace(go.Scatter(
                x=down_sig['log2FoldChange'],
                y=down_sig['neg_log10_p'],
                mode='markers',
                marker=dict(color='blue', size=5, opacity=0.7),
                name='Down-regulated',
                text=down_sig['gene_symbol'],
                hovertemplate='<b>%{text}</b><br>' +
                              'log2FC: %{x:.3f}<br>' +
                              '-log10(p): %{y:.3f}<br>' +
                              '<extra></extra>'
            ))
        
        # Label top genes (overlay on top)
        if len(top_genes) > 0:
            top_df = df[df['gene_symbol'].isin(top_genes)]
            # Split into up and down for better text positioning
            top_up = top_df[top_df['log2FoldChange'] > 0]
            top_down = top_df[top_df['log2FoldChange'] < 0]
            
            # Add up-regulated top genes
            if len(top_up) > 0:
                fig.add_trace(go.Scatter(
                    x=top_up['log2FoldChange'],
                    y=top_up['neg_log10_p'],
                    mode='markers+text',
                    marker=dict(color='darkred', size=8, opacity=0.9, line=dict(width=1, color='black')),
                    text=top_up['gene_symbol'],
                    textposition="top center",
                    textfont=dict(size=10, color='darkred'),
                    name=f'Top {n_labels} genes' if len(top_down) == 0 else f'Top {n_labels} genes (up)',
                    showlegend=True,
                    hovertemplate='<b>%{text}</b><br>' +
                                  'log2FC: %{x:.3f}<br>' +
                                  '-log10(p): %{y:.3f}<br>' +
                                  '<extra></extra>'
                ))
            
            # Add down-regulated top genes
            if len(top_down) > 0:
                fig.add_trace(go.Scatter(
                    x=top_down['log2FoldChange'],
                    y=top_down['neg_log10_p'],
                    mode='markers+text',
                    marker=dict(color='darkblue', size=8, opacity=0.9, line=dict(width=1, color='black')),
                    text=top_down['gene_symbol'],
                    textposition="bottom center",
                    textfont=dict(size=10, color='darkblue'),
                    name=f'Top {n_labels} genes' if len(top_up) == 0 else f'Top {n_labels} genes (down)',
                    showlegend=True,
                    hovertemplate='<b>%{text}</b><br>' +
                                  'log2FC: %{x:.3f}<br>' +
                                  '-log10(p): %{y:.3f}<br>' +
                                  '<extra></extra>'
                ))
        
        # Add reference lines
        fig.add_hline(
            y=-np.log10(fdr_threshold),
            line_dash="dash",
            line_color="orange",
            annotation_text=f"FDR = {fdr_threshold}"
        )
        fig.add_vline(
            x=lfc_threshold,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"log2FC = {lfc_threshold}"
        )
        fig.add_vline(
            x=-lfc_threshold,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"log2FC = -{lfc_threshold}"
        )
        
        # Update layout
        layout_dict = {
            "title": f"Volcano Plot: {get_file_display_name(file_path)}",
            "xaxis_title": "log2 Fold Change",
            "yaxis_title": "-log10(adjusted p-value)" if p_col == 'padj' else "-log10(p-value)",
            "hovermode": 'closest',
            "height": 600,
            "template": "plotly_white"
        }
        
        # Apply custom axis limits if enabled
        if custom_axes and "custom-axes" in custom_axes:
            # Only set range if at least one limit is specified
            if xmin is not None or xmax is not None:
                xaxis_range = [xmin, xmax]  # Plotly handles None values in range
                layout_dict["xaxis"] = {"range": xaxis_range}
            
            if ymin is not None or ymax is not None:
                yaxis_range = [ymin, ymax]  # Plotly handles None values in range
                layout_dict["yaxis"] = {"range": yaxis_range}
        
        fig.update_layout(**layout_dict)
        
        # Create sortable table using dash_table.DataTable
        table_df = df[['gene_symbol', 'log2FoldChange', 'baseMean', 'pvalue', 'padj']].copy()
        table_df = table_df.round(4)
        
        # Limit to first 2000 rows for performance
        display_df = table_df.head(2000)
        
        table = dash_table.DataTable(
            data=display_df.to_dict('records'),
            columns=[
                {"name": "Gene Symbol", "id": "gene_symbol", "type": "text"},
                {"name": "log2FC", "id": "log2FoldChange", "type": "numeric", "format": {"specifier": ".4f"}},
                {"name": "baseMean", "id": "baseMean", "type": "numeric", "format": {"specifier": ".2f"}},
                {"name": "p-value", "id": "pvalue", "type": "numeric", "format": {"specifier": ".2e"}},
                {"name": "padj", "id": "padj", "type": "numeric", "format": {"specifier": ".2e"}}
            ],
            sort_action="native",  # Enable sorting
            sort_mode="multi",  # Allow sorting by multiple columns
            filter_action="native",  # Enable filtering
            page_action="native",  # Enable pagination
            page_current=0,
            page_size=25,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'sans-serif',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{log2FoldChange} > 0 && {padj} < 0.05'},
                    'backgroundColor': '#ffe6e6',
                },
                {
                    'if': {'filter_query': '{log2FoldChange} < 0 && {padj} < 0.05'},
                    'backgroundColor': '#e6f3ff',
                }
            ],
            export_format="csv",
            export_headers="display"
        )
        
        table_info = html.P(
            f"Showing {min(2000, len(table_df))} of {len(table_df)} genes. "
            "Click column headers to sort. Use gene search to filter results.",
            className="text-muted small"
        )
        
        return fig, df.to_dict('records'), html.Div([table_info, table])
        
    except Exception as e:
        error_msg = html.Div([
            dbc.Alert(f"Error loading data: {str(e)}", color="danger")
        ])
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text=f"Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return empty_fig, None, error_msg


@app.callback(
    Output("volcano-download", "data"),
    Input("volcano-export-btn", "n_clicks"),
    State("volcano-data-store", "data"),
    prevent_initial_call=True
)
def export_volcano_data(n_clicks, data):
    """Export volcano plot data to CSV."""
    if data:
        df = pd.DataFrame(data)
        return dcc.send_data_frame(df.to_csv, "deseq2_volcano_export.csv", index=False)
    return None


@app.callback(
    [Output("scatter-plot", "figure"),
     Output("scatter-data-store", "data"),
     Output("scatter-table-container", "children")],
    [Input("scatter-x-dropdown", "value"),
     Input("scatter-y-dropdown", "value"),
     Input("scatter-sig-filter", "value"),
     Input("scatter-n-labels", "value"),
     Input("scatter-gene-search", "value"),
     Input("scatter-custom-axes", "value"),
     Input("scatter-xmin", "value"),
     Input("scatter-xmax", "value"),
     Input("scatter-ymin", "value"),
     Input("scatter-ymax", "value")]
)
def update_scatter_plot(file_path1, file_path2, sig_filter, n_labels, gene_search,
                        custom_axes, xmin, xmax, ymin, ymax):
    """Update scatter plot and table based on controls."""
    if not file_path1 or not file_path2:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Please select both comparison files",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return empty_fig, None, html.Div("No data loaded")
    
    if file_path1 == file_path2:
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text="Please select two different comparison files",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return empty_fig, None, html.Div("Please select two different comparisons")
    
    try:
        # Merge data
        merged = merge_comparisons(file_path1, file_path2)
        
        # Apply significance filter
        if sig_filter and "sig-only" in sig_filter:
            if 'padj_1' in merged.columns and 'padj_2' in merged.columns:
                merged = merged[
                    (merged['padj_1'] < 0.05) | (merged['padj_2'] < 0.05)
                ]
        
        # Apply gene search filter
        if gene_search:
            search_term = gene_search.upper()
            merged = merged[merged['gene_symbol'].str.upper().str.contains(search_term, na=False)]
        
        # Calculate max absolute log2FC for labeling
        merged['max_abs_lfc'] = merged[
            ['log2FoldChange_1', 'log2FoldChange_2']
        ].abs().max(axis=1)
        
        # Sort by max_abs_lfc and select top N for labeling
        merged_sorted = merged.sort_values('max_abs_lfc', ascending=False)
        top_genes = merged_sorted.head(n_labels)['gene_symbol'].values if n_labels > 0 else []
        
        # Create scatter plot
        fig = go.Figure()
        
        # All points
        fig.add_trace(go.Scatter(
            x=merged['log2FoldChange_1'],
            y=merged['log2FoldChange_2'],
            mode='markers',
            marker=dict(color='gray', size=3, opacity=0.5),
            name='All genes',
            text=merged['gene_symbol'],
            hovertemplate='<b>%{text}</b><br>' +
                          'X (log2FC): %{x:.3f}<br>' +
                          'Y (log2FC): %{y:.3f}<br>' +
                          '<extra></extra>'
        ))
        
        # Label top genes
        if len(top_genes) > 0:
            top_df = merged[merged['gene_symbol'].isin(top_genes)]
            fig.add_trace(go.Scatter(
                x=top_df['log2FoldChange_1'],
                y=top_df['log2FoldChange_2'],
                mode='markers+text',
                marker=dict(color='red', size=8, opacity=0.8),
                text=top_df['gene_symbol'],
                textposition="top center",
                name='Top genes',
                hovertemplate='<b>%{text}</b><br>' +
                              'X (log2FC): %{x:.3f}<br>' +
                              'Y (log2FC): %{y:.3f}<br>' +
                              '<extra></extra>'
            ))
        
        # Add reference lines
        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.3)
        fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.3)
        
        # Add diagonal line (y = x)
        x_range = [
            merged['log2FoldChange_1'].min(),
            merged['log2FoldChange_1'].max()
        ]
        fig.add_trace(go.Scatter(
            x=x_range,
            y=x_range,
            mode='lines',
            line=dict(color='blue', dash='dot', width=1),
            name='y = x',
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Calculate correlation
        corr = merged['log2FoldChange_1'].corr(merged['log2FoldChange_2'])
        
        # Update layout
        x_name = get_file_display_name(file_path1)
        y_name = get_file_display_name(file_path2)
        
        layout_dict = {
            "title": f"Fold Change Comparison<br><sub>Correlation: {corr:.3f}</sub>",
            "xaxis_title": f"log2FC: {x_name}",
            "yaxis_title": f"log2FC: {y_name}",
            "hovermode": 'closest',
            "height": 600,
            "template": "plotly_white"
        }
        
        # Apply custom axis limits if enabled
        if custom_axes and "custom-axes" in custom_axes:
            # Only set range if at least one limit is specified
            if xmin is not None or xmax is not None:
                xaxis_range = [xmin, xmax]  # Plotly handles None values in range
                layout_dict["xaxis"] = {"range": xaxis_range}
            
            if ymin is not None or ymax is not None:
                yaxis_range = [ymin, ymax]  # Plotly handles None values in range
                layout_dict["yaxis"] = {"range": yaxis_range}
        
        fig.update_layout(**layout_dict)
        
        # Create table
        table_cols = ['gene_symbol', 'log2FoldChange_1', 'log2FoldChange_2']
        if 'padj_1' in merged.columns:
            table_cols.extend(['padj_1', 'padj_2'])
        if 'pvalue_1' in merged.columns:
            table_cols.extend(['pvalue_1', 'pvalue_2'])
        
        table_df = merged[table_cols].copy()
        table_df = table_df.round(4)
        
        # Create sortable table using dash_table.DataTable
        display_df = table_df.head(2000)
        
        table = dash_table.DataTable(
            data=display_df.to_dict('records'),
            columns=[
                {"name": "Gene Symbol", "id": "gene_symbol", "type": "text"},
                {"name": "log2FC (1)", "id": "log2FoldChange_1", "type": "numeric", "format": {"specifier": ".4f"}},
                {"name": "log2FC (2)", "id": "log2FoldChange_2", "type": "numeric", "format": {"specifier": ".4f"}},
            ] + ([
                {"name": "padj (1)", "id": "padj_1", "type": "numeric", "format": {"specifier": ".2e"}},
                {"name": "padj (2)", "id": "padj_2", "type": "numeric", "format": {"specifier": ".2e"}}
            ] if 'padj_1' in table_df.columns else []) + ([
                {"name": "pvalue (1)", "id": "pvalue_1", "type": "numeric", "format": {"specifier": ".2e"}},
                {"name": "pvalue (2)", "id": "pvalue_2", "type": "numeric", "format": {"specifier": ".2e"}}
            ] if 'pvalue_1' in table_df.columns else []),
            sort_action="native",
            sort_mode="multi",
            filter_action="native",
            page_action="native",
            page_current=0,
            page_size=25,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'sans-serif',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            export_format="csv",
            export_headers="display"
        )
        
        table_info = html.P(
            f"Showing {min(2000, len(table_df))} of {len(table_df)} genes. "
            "Click column headers to sort. Use gene search to filter results.",
            className="text-muted small"
        )
        
        return fig, merged.to_dict('records'), html.Div([table_info, table])
        
    except Exception as e:
        error_msg = html.Div([
            dbc.Alert(f"Error loading data: {str(e)}", color="danger")
        ])
        empty_fig = go.Figure()
        empty_fig.add_annotation(
            text=f"Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return empty_fig, None, error_msg


@app.callback(
    Output("scatter-download", "data"),
    Input("scatter-export-btn", "n_clicks"),
    State("scatter-data-store", "data"),
    prevent_initial_call=True
)
def export_scatter_data(n_clicks, data):
    """Export scatter plot data to CSV."""
    if data:
        df = pd.DataFrame(data)
        return dcc.send_data_frame(df.to_csv, "deseq2_scatter_export.csv", index=False)
    return None


@app.callback(
    Output("venn-comp3-container", "children"),
    Input("venn-n-comparisons", "value")
)
def update_venn_comp3_container(n_comparisons):
    """Show/hide third comparison dropdown based on number of comparisons."""
    if n_comparisons == 3:
        return [
            html.Br(),
            html.Label("Comparison 3:", className="fw-bold"),
            dcc.Dropdown(
                id="venn-comp3-dropdown",
                options=file_options,
                value=file_options[2]["value"] if len(file_options) > 2 else None,
                placeholder="Select third comparison...",
                searchable=True,
                clearable=False,
                style={"fontSize": "12px"}
            )
        ]
    return []


@app.callback(
    [Output("venn-diagram-container", "children"),
     Output("venn-gene-lists", "children"),
     Output("venn-data-store", "data")],
    [Input("venn-n-comparisons", "value"),
     Input("venn-comp1-dropdown", "value"),
     Input("venn-comp2-dropdown", "value"),
     Input("venn-fdr-slider", "value"),
     Input("venn-lfc-slider", "value")],
    [State("venn-comp3-dropdown", "value"),
     State("venn-data-store", "data")]
)
def update_venn_diagram(n_comparisons, file_path1, file_path2, fdr_threshold, lfc_threshold, file_path3, stored_data):
    """Update Venn diagram based on selected comparisons."""
    
    # Validate inputs
    if not file_path1 or not file_path2:
        return html.Div([
            dbc.Alert("Please select at least two comparisons", color="warning")
        ]), html.Div(), None
    
    if n_comparisons == 3 and not file_path3:
        return html.Div([
            dbc.Alert("Please select all three comparisons", color="warning")
        ]), html.Div(), None
    
    # Check for duplicate selections
    paths = [file_path1, file_path2]
    if n_comparisons == 3:
        paths.append(file_path3)
        if len(set(paths)) != 3:
            return html.Div([
                dbc.Alert("Please select three different comparisons", color="warning")
            ]), html.Div(), None
    else:
        if file_path1 == file_path2:
            return html.Div([
                dbc.Alert("Please select two different comparisons", color="warning")
            ]), html.Div(), None
    
    # Ensure thresholds are numbers
    if fdr_threshold is None:
        fdr_threshold = 0.05
    if lfc_threshold is None:
        lfc_threshold = 1.0
    
    try:
        # Extract DEGs from each comparison
        degs1 = extract_degs(file_path1, fdr_threshold, lfc_threshold)
        degs2 = extract_degs(file_path2, fdr_threshold, lfc_threshold)
        names = [get_file_display_name(file_path1), get_file_display_name(file_path2)]
        
        # Debug info
        deg_counts_info = html.P(
            f"DEG counts - {names[0]}: {len(degs1)}, {names[1]}: {len(degs2)}",
            className="text-muted small mb-2"
        )
        
        if n_comparisons == 3:
            if not file_path3:
                return html.Div([
                    dbc.Alert("Please select all three comparisons", color="warning")
                ]), html.Div(), None
            degs3 = extract_degs(file_path3, fdr_threshold, lfc_threshold)
            names.append(get_file_display_name(file_path3))
            deg_counts_info = html.P(
                f"DEG counts - {names[0]}: {len(degs1)}, {names[1]}: {len(degs2)}, {names[2]}: {len(degs3)}",
                className="text-muted small mb-2"
            )
        
        # Calculate overlaps first
        if n_comparisons == 2:
            only1 = degs1 - degs2
            only2 = degs2 - degs1
            overlap = degs1 & degs2
            
            overlaps_data = {
                'only_1': list(only1),
                'only_2': list(only2),
                'overlap': list(overlap)
            }
            
        else:  # n_comparisons == 3
            only1 = degs1 - degs2 - degs3
            only2 = degs2 - degs1 - degs3
            only3 = degs3 - degs1 - degs2
            overlap12 = (degs1 & degs2) - degs3
            overlap13 = (degs1 & degs3) - degs2
            overlap23 = (degs2 & degs3) - degs1
            overlap_all = degs1 & degs2 & degs3
            
            overlaps_data = {
                'only_1': list(only1),
                'only_2': list(only2),
                'only_3': list(only3),
                'overlap_12': list(overlap12),
                'overlap_13': list(overlap13),
                'overlap_23': list(overlap23),
                'overlap_all': list(overlap_all)
            }
        
        # Create Venn diagram
        fig, ax = plt.subplots(figsize=(10, 8))
        
        if n_comparisons == 2:
            # Convert sets to lists for venn2
            degs1_list = list(degs1)
            degs2_list = list(degs2)
            
            # Create venn2 diagram
            v = venn2([degs1_list, degs2_list], set_labels=names, ax=ax)
            
            # Customize colors and labels for venn2
            if v:
                # Get patches and customize
                patches = [v.get_patch_by_id('10'), v.get_patch_by_id('01'), v.get_patch_by_id('11')]
                colors = ['#3498db', '#e74c3c', '#2ecc71']
                
                for i, patch in enumerate(patches):
                    if patch:
                        patch.set_facecolor(colors[i % 3])
                        patch.set_alpha(0.6)
                        patch.set_edgecolor('black')
                        patch.set_linewidth(2)
                
                # Update labels with counts
                label_ids = ['10', '01', '11']
                label_texts = [
                    f'{len(only1)}',
                    f'{len(only2)}',
                    f'{len(overlap)}'
                ]
                
                for label_id, label_text in zip(label_ids, label_texts):
                    label = v.get_label_by_id(label_id)
                    if label:
                        label.set_text(label_text)
                        label.set_fontsize(12)
                        label.set_fontweight('bold')
            
        else:  # n_comparisons == 3
            # Convert sets to lists for venn3
            degs1_list = list(degs1)
            degs2_list = list(degs2)
            degs3_list = list(degs3)
            
            # Create venn3 diagram
            v = venn3([degs1_list, degs2_list, degs3_list], set_labels=names, ax=ax)
            
            # Customize colors for venn3
            if v:
                colors = ['#3498db', '#e74c3c', '#2ecc71']
                
                # venn3 has different patch IDs
                for i, patch_id in enumerate(['100', '010', '001', '110', '101', '011', '111']):
                    patch = v.get_patch_by_id(patch_id)
                    if patch:
                        # Determine color based on which sets are involved
                        if patch_id == '111':  # All three
                            patch.set_facecolor('#f39c12')  # Orange for all overlap
                        elif patch_id in ['110', '101', '011']:  # Two-way overlaps
                            patch.set_facecolor('#95a5a6')  # Gray for two-way
                        else:  # Single sets
                            patch.set_facecolor(colors[i % 3])
                        patch.set_alpha(0.6)
                        patch.set_edgecolor('black')
                        patch.set_linewidth(2)
                
                # Update labels with counts
                label_map = {
                    '100': len(only1),
                    '010': len(only2),
                    '001': len(only3),
                    '110': len(overlap12),
                    '101': len(overlap13),
                    '011': len(overlap23),
                    '111': len(overlap_all)
                }
                
                for label_id, count in label_map.items():
                    label = v.get_label_by_id(label_id)
                    if label:
                        label.set_text(str(count))
                        label.set_fontsize(11)
                        label.set_fontweight('bold')
        
        ax.set_title(f"Venn Diagram of DEGs\n(FDR < {fdr_threshold}, |log2FC| > {lfc_threshold})", 
                     fontsize=14, fontweight='bold', pad=20)
        
        # Convert matplotlib figure to base64 string for display
        buf = io.BytesIO()
        try:
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode()
            img_src = f'data:image/png;base64,{img_str}'
            venn_img = html.Img(src=img_src, style={'width': '100%', 'height': 'auto'})
        except Exception as img_error:
            venn_img = html.Div([
                dbc.Alert(f"Error generating image: {str(img_error)}", color="danger"),
                html.Pre(str(img_error), style={'fontSize': '10px'})
            ])
        finally:
            plt.close(fig)
            buf.close()
        
        # Create gene lists display
        if n_comparisons == 2:
            gene_lists_html = dbc.Row([
                dbc.Col([
                    html.H6(f"Only {names[0]}", className="fw-bold"),
                    html.P(f"{len(only1)} genes", className="text-muted small"),
                    html.Div([
                        html.Span(gene, className="badge bg-primary me-1 mb-1") 
                        for gene in sorted(list(only1))[:50]
                    ] if only1 else [html.P("No genes", className="text-muted")])
                ], width=4),
                dbc.Col([
                    html.H6("Overlap", className="fw-bold"),
                    html.P(f"{len(overlap)} genes", className="text-muted small"),
                    html.Div([
                        html.Span(gene, className="badge bg-success me-1 mb-1") 
                        for gene in sorted(list(overlap))[:50]
                    ] if overlap else [html.P("No genes", className="text-muted")])
                ], width=4),
                dbc.Col([
                    html.H6(f"Only {names[1]}", className="fw-bold"),
                    html.P(f"{len(only2)} genes", className="text-muted small"),
                    html.Div([
                        html.Span(gene, className="badge bg-danger me-1 mb-1") 
                        for gene in sorted(list(only2))[:50]
                    ] if only2 else [html.P("No genes", className="text-muted")])
                ], width=4)
            ])
        else:
            gene_lists_html = dbc.Row([
                dbc.Col([
                    html.H6(f"Only {names[0]}", className="fw-bold"),
                    html.P(f"{len(only1)} genes", className="text-muted small"),
                    html.Div([
                        html.Span(gene, className="badge bg-primary me-1 mb-1") 
                        for gene in sorted(list(only1))[:30]
                    ] if only1 else [html.P("No genes", className="text-muted")])
                ], width=3),
                dbc.Col([
                    html.H6(f"Only {names[1]}", className="fw-bold"),
                    html.P(f"{len(only2)} genes", className="text-muted small"),
                    html.Div([
                        html.Span(gene, className="badge bg-danger me-1 mb-1") 
                        for gene in sorted(list(only2))[:30]
                    ] if only2 else [html.P("No genes", className="text-muted")])
                ], width=3),
                dbc.Col([
                    html.H6(f"Only {names[2]}", className="fw-bold"),
                    html.P(f"{len(only3)} genes", className="text-muted small"),
                    html.Div([
                        html.Span(gene, className="badge bg-success me-1 mb-1") 
                        for gene in sorted(list(only3))[:30]
                    ] if only3 else [html.P("No genes", className="text-muted")])
                ], width=3),
                dbc.Col([
                    html.H6("All Overlap", className="fw-bold"),
                    html.P(f"{len(overlap_all)} genes", className="text-muted small"),
                    html.Div([
                        html.Span(gene, className="badge bg-warning me-1 mb-1") 
                        for gene in sorted(list(overlap_all))[:30]
                    ] if overlap_all else [html.P("No genes", className="text-muted")])
                ], width=3)
            ])
        
        # Combine diagram and info
        venn_container = html.Div([
            deg_counts_info,
            venn_img
        ])
        
        return venn_container, gene_lists_html, overlaps_data
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = html.Div([
            dbc.Alert(f"Error creating Venn diagram: {str(e)}", color="danger"),
            html.Pre(error_details, style={'fontSize': '10px', 'overflow': 'auto', 'maxHeight': '200px'})
        ])
        return error_msg, html.Div(), None


@app.callback(
    Output("venn-download", "data"),
    Input("venn-export-btn", "n_clicks"),
    State("venn-data-store", "data"),
    State("venn-n-comparisons", "value"),
    State("venn-comp1-dropdown", "value"),
    State("venn-comp2-dropdown", "value"),
    State("venn-comp3-dropdown", "value"),
    prevent_initial_call=True
)
def export_venn_overlaps(n_clicks, overlaps_data, n_comparisons, file_path1, file_path2, file_path3):
    """Export overlap gene lists to CSV."""
    if not overlaps_data:
        return None
    
    try:
        # Create a DataFrame with all overlaps
        export_data = []
        
        if n_comparisons == 2:
            names = [get_file_display_name(file_path1), get_file_display_name(file_path2)]
            export_data.append({
                'Category': f'Only {names[0]}',
                'Gene_Count': len(overlaps_data['only_1']),
                'Genes': ', '.join(sorted(overlaps_data['only_1']))
            })
            export_data.append({
                'Category': f'Overlap ({names[0]} & {names[1]})',
                'Gene_Count': len(overlaps_data['overlap']),
                'Genes': ', '.join(sorted(overlaps_data['overlap']))
            })
            export_data.append({
                'Category': f'Only {names[1]}',
                'Gene_Count': len(overlaps_data['only_2']),
                'Genes': ', '.join(sorted(overlaps_data['only_2']))
            })
        else:
            names = [get_file_display_name(file_path1), get_file_display_name(file_path2), get_file_display_name(file_path3)]
            export_data.append({
                'Category': f'Only {names[0]}',
                'Gene_Count': len(overlaps_data['only_1']),
                'Genes': ', '.join(sorted(overlaps_data['only_1']))
            })
            export_data.append({
                'Category': f'Only {names[1]}',
                'Gene_Count': len(overlaps_data['only_2']),
                'Genes': ', '.join(sorted(overlaps_data['only_2']))
            })
            export_data.append({
                'Category': f'Only {names[2]}',
                'Gene_Count': len(overlaps_data['only_3']),
                'Genes': ', '.join(sorted(overlaps_data['only_3']))
            })
            export_data.append({
                'Category': f'Overlap {names[0]} & {names[1]}',
                'Gene_Count': len(overlaps_data['overlap_12']),
                'Genes': ', '.join(sorted(overlaps_data['overlap_12']))
            })
            export_data.append({
                'Category': f'Overlap {names[0]} & {names[2]}',
                'Gene_Count': len(overlaps_data['overlap_13']),
                'Genes': ', '.join(sorted(overlaps_data['overlap_13']))
            })
            export_data.append({
                'Category': f'Overlap {names[1]} & {names[2]}',
                'Gene_Count': len(overlaps_data['overlap_23']),
                'Genes': ', '.join(sorted(overlaps_data['overlap_23']))
            })
            export_data.append({
                'Category': f'Overlap All Three',
                'Gene_Count': len(overlaps_data['overlap_all']),
                'Genes': ', '.join(sorted(overlaps_data['overlap_all']))
            })
        
        df = pd.DataFrame(export_data)
        return dcc.send_data_frame(df.to_csv, "venn_diagram_overlaps.csv", index=False)
        
    except Exception as e:
        return None


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="DESeq2 Interactive Dashboard")
    # Check for PORT environment variable (used by cloud platforms)
    default_port = int(os.environ.get("PORT", 8050))
    parser.add_argument("--port", type=int, default=default_port, help="Port to run the server on (default: 8050 or $PORT)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    # Disable debug mode in production (when PORT is set by cloud platform)
    debug_mode = args.debug if os.environ.get("PORT") is None else False
    
    app.run(debug=debug_mode, host=args.host, port=args.port)

