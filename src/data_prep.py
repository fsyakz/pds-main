import pandas as pd
from typing import Optional

def prep_inflasi_base(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare base inflation data with basic cleaning."""
    if df.empty:
        return df
    
    # Make a copy to avoid modifying original
    df_clean = df.copy()
    
    # Ensure data types
    df_clean['Provinsi'] = df_clean['Provinsi'].astype(str)
    df_clean['Tahun'] = pd.to_numeric(df_clean['Tahun'], errors='coerce')
    df_clean['Bulan'] = pd.to_numeric(df_clean['Bulan'], errors='coerce')
    df_clean['Inflasi (%)'] = pd.to_numeric(df_clean['Inflasi (%)'], errors='coerce')
    
    # Remove rows with invalid data
    df_clean = df_clean.dropna(subset=['Provinsi', 'Tahun', 'Bulan', 'Inflasi (%)'])
    
    return df_clean

def prep_inflasi_with_tanggal(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare inflation data with date column."""
    df_clean = prep_inflasi_base(df)
    
    if df_clean.empty:
        return df_clean
    
    # Create date column
    df_clean['Tanggal'] = pd.to_datetime(
        df_clean['Tahun'].astype(int).astype(str) + '-' + 
        df_clean['Bulan'].astype(int).astype(str) + '-01'
    )
    
    return df_clean

def latest_year(df: pd.DataFrame) -> Optional[int]:
    """Get the latest year from the data."""
    if df.empty:
        return None
    
    years = df['Tahun'].dropna().unique()
    if len(years) > 0:
        return int(max(years))
    return None

def latest_month_in_year(df: pd.DataFrame, year: int) -> Optional[int]:
    """Get the latest month for a given year."""
    if df.empty:
        return None
    
    year_data = df[df['Tahun'] == year]
    if year_data.empty:
        return None
    
    months = year_data['Bulan'].dropna().unique()
    if len(months) > 0:
        return int(max(months))
    return None
