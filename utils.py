"""
Utility functions for DESeq2 Dashboard
Handles file discovery, data loading, and caching
"""

import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import functools

# Cache for loaded data
_data_cache: Dict[str, pd.DataFrame] = {}


def get_project_root() -> Path:
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    # Go up from deseq2_dashboard/ to Endothelial_LIFR_mouse/
    return current_file.parent.parent


def get_deseq2_results_dir() -> Path:
    """
    Get the DESeq2 results directory.
    Tries multiple locations:
    1. data/ subdirectory (for deployed apps)
    2. ../analysis_results/deseq2_results/ (for local development)
    """
    current_dir = Path(__file__).resolve().parent
    
    # Try data/ subdirectory first (for deployment)
    data_dir = current_dir / "data" / "deseq2_results"
    if data_dir.exists():
        return data_dir
    
    # Fall back to parent directory structure (for local development)
    project_root = get_project_root()
    results_dir = project_root / "analysis_results" / "deseq2_results"
    return results_dir


def discover_deseq2_files() -> List[Tuple[str, str, str]]:
    """
    Discover all DESeq2 TSV files in primary/ and secondary/ directories.
    
    Returns:
        List of tuples: (file_path, category, display_name)
        category: 'primary' or 'secondary'
        display_name: Human-readable name for the comparison
    """
    results_dir = get_deseq2_results_dir()
    files = []
    
    def clean_display_name(name: str) -> str:
        """Clean and shorten display name for better readability."""
        # Remove _results suffix
        if "_results" in name:
            name = name.replace("_results", "")
        
        # Extract and format date prefix (format: YYYYMMDD_)
        parts = name.split("_", 1)
        date_str = ""
        if len(parts) > 1 and parts[0].isdigit() and len(parts[0]) == 8:
            # Format date as YYYY-MM-DD for readability
            date_str = parts[0]
            date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            name = parts[1]
        else:
            # No date prefix found, use filename as-is
            pass
        
        # Replace common patterns with shorter versions
        name = name.replace("_vs_", " vs ")
        name = name.replace("_", " ")
        
        # Add date prefix if present (in parentheses)
        if date_str:
            name = f"{date_formatted}: {name}"
        
        # Truncate if too long (max 55 chars to account for date)
        if len(name) > 55:
            name = name[:52] + "..."
        
        return name
    
    # Scan primary directory
    primary_dir = results_dir / "primary"
    if primary_dir.exists():
        for file_path in sorted(primary_dir.glob("*.tsv")):
            name = file_path.stem
            display_name = clean_display_name(name)
            files.append((str(file_path), "primary", display_name))
    
    # Scan secondary directory
    secondary_dir = results_dir / "secondary"
    if secondary_dir.exists():
        for file_path in sorted(secondary_dir.glob("*.tsv")):
            name = file_path.stem
            display_name = clean_display_name(name)
            files.append((str(file_path), "secondary", display_name))
    
    return files


def load_deseq2_file(file_path: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Load a DESeq2 TSV file into a pandas DataFrame.
    
    Args:
        file_path: Path to the TSV file
        use_cache: Whether to use cached data if available
    
    Returns:
        DataFrame with columns: gene_symbol, baseMean, log2FoldChange, 
        lfcSE, stat, pvalue, padj
    """
    # Check cache first
    if use_cache and file_path in _data_cache:
        return _data_cache[file_path].copy()
    
    # Load file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    df = pd.read_csv(file_path, sep="\t")
    
    # Validate required columns
    required_cols = ["gene_symbol", "log2FoldChange"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Handle missing values
    # Replace inf with NaN
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numeric_cols:
        df[col] = df[col].replace([float('inf'), float('-inf')], pd.NA)
    
    # Ensure gene_symbol is string
    df['gene_symbol'] = df['gene_symbol'].astype(str)
    
    # Cache the data
    if use_cache:
        _data_cache[file_path] = df.copy()
    
    return df


def clear_cache():
    """Clear the data cache."""
    global _data_cache
    _data_cache.clear()


def merge_comparisons(file_path1: str, file_path2: str) -> pd.DataFrame:
    """
    Merge two DESeq2 comparison files by gene_symbol.
    
    Args:
        file_path1: Path to first comparison file
        file_path2: Path to second comparison file
    
    Returns:
        Merged DataFrame with columns from both comparisons
    """
    df1 = load_deseq2_file(file_path1)
    df2 = load_deseq2_file(file_path2)
    
    # Merge on gene_symbol
    merged = pd.merge(
        df1,
        df2,
        on="gene_symbol",
        how="inner",
        suffixes=("_1", "_2")
    )
    
    return merged


def get_file_display_name(file_path: str) -> str:
    """Extract a display name from a file path."""
    filename = os.path.basename(file_path)
    name = os.path.splitext(filename)[0]
    if "_results" in name:
        # Remove date prefix and _results suffix
        parts = name.split("_", 1)
        if len(parts) > 1:
            return parts[1].replace("_results", "")
    return name


def extract_degs(file_path: str, padj_threshold: float = 0.05, lfc_threshold: float = 1.0) -> set:
    """
    Extract differentially expressed genes (DEGs) from a DESeq2 results file.
    
    Args:
        file_path: Path to DESeq2 TSV file
        padj_threshold: Adjusted p-value threshold (default: 0.05)
        lfc_threshold: Log2 fold change threshold (default: 1.0)
    
    Returns:
        Set of gene symbols that are significantly differentially expressed
    """
    df = load_deseq2_file(file_path)
    
    # Filter for significant DEGs
    if 'padj' in df.columns:
        mask = (
            (df['padj'] < padj_threshold) & 
            (df['padj'].notna()) &
            (df['log2FoldChange'].abs() > lfc_threshold) &
            (df['log2FoldChange'].notna())
        )
        degs = df[mask]['gene_symbol'].tolist()
    elif 'pvalue' in df.columns:
        mask = (
            (df['pvalue'] < padj_threshold) & 
            (df['pvalue'].notna()) &
            (df['log2FoldChange'].abs() > lfc_threshold) &
            (df['log2FoldChange'].notna())
        )
        degs = df[mask]['gene_symbol'].tolist()
    else:
        degs = []
    
    # Convert to set and filter out any NaN values
    degs_set = set([str(g) for g in degs if pd.notna(g) and str(g) != 'nan'])
    
    return degs_set

