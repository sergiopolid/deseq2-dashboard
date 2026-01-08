"""
Interactive DESeq2 Dashboard
A Dash/Plotly web application for exploring DESeq2 differential expression results
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from pathlib import Path

from utils import (
    discover_deseq2_files,
    load_deseq2_file,
    merge_comparisons,
    get_file_display_name
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
            ], id="main-tabs", active_tab="volcano-tab")
        ])
    ], className="mb-4"),
    
    # Content area
    html.Div(id="tab-content"),
    
    # Store for selected data
    dcc.Store(id="volcano-data-store"),
    dcc.Store(id="scatter-data-store"),
    
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
    return html.Div("Select a tab")


@app.callback(
    [Output("volcano-plot", "figure"),
     Output("volcano-data-store", "data"),
     Output("volcano-table-container", "children")],
    [Input("volcano-file-dropdown", "value"),
     Input("volcano-fdr-slider", "value"),
     Input("volcano-lfc-slider", "value"),
     Input("volcano-gene-search", "value"),
     Input("volcano-custom-axes", "value"),
     Input("volcano-xmin", "value"),
     Input("volcano-xmax", "value"),
     Input("volcano-ymin", "value"),
     Input("volcano-ymax", "value")]
)
def update_volcano_plot(file_path, fdr_threshold, lfc_threshold, gene_search, 
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
        
        # Create table
        table_df = df[['gene_symbol', 'log2FoldChange', 'baseMean', 'pvalue', 'padj']].copy()
        table_df = table_df.round(4)
        
        table = dbc.Table.from_dataframe(
            table_df.head(1000),  # Limit to first 1000 rows for performance
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table-sm"
        )
        
        table_info = html.P(
            f"Showing {min(1000, len(table_df))} of {len(table_df)} genes. "
            "Use gene search to filter results.",
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
        
        table = dbc.Table.from_dataframe(
            table_df.head(1000),  # Limit to first 1000 rows
            striped=True,
            bordered=True,
            hover=True,
            responsive=True,
            className="table-sm"
        )
        
        table_info = html.P(
            f"Showing {min(1000, len(table_df))} of {len(table_df)} genes. "
            "Use gene search to filter results.",
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

