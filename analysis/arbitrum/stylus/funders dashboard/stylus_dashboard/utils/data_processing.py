import pandas as pd
from datetime import datetime, timedelta
from ..config import TIME_WINDOWS

def load_data(file_path):
    """Load and process data from CSV file."""
    df = pd.read_csv(file_path)
    if 'sample_date' in df.columns:
        df['sample_date'] = pd.to_datetime(df['sample_date'])
    return df

def filter_data_by_time_window(df, time_window):
    """Filter data based on selected time window."""
    if df.empty or 'sample_date' not in df.columns:
        return df
    
    latest_date = df['sample_date'].max()
    time_ago = latest_date - timedelta(days=TIME_WINDOWS[time_window])
    return df[df['sample_date'] >= time_ago]

def calculate_pct_change(df):
    """Calculate percentage change for a dataframe."""
    if df.empty:
        return df
    
    df = df.sort_values('sample_date')
    df['pct_change'] = df['amount'].pct_change() * 100
    return df

def calculate_project_metrics(df):
    """Calculate project metrics from the dataframe."""
    if df.empty:
        return None
    
    project_metrics = df.groupby('display_name').agg({
        'amount': ['mean', 'first', 'last']
    }).reset_index()
    
    project_metrics['pct_change'] = ((project_metrics[('amount', 'last')] - project_metrics[('amount', 'first')]) / 
                                   project_metrics[('amount', 'first')] * 100)
    
    project_metrics.columns = ['Project', 'Avg Devs/Month', 'First Month', 'Last Month', 'Monthly Growth %']
    project_metrics = project_metrics[['Project', 'Avg Devs/Month', 'Monthly Growth %']]
    
    return project_metrics.sort_values('Avg Devs/Month', ascending=False).head(30) 