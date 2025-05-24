# utils.py

import pandas as pd
import ipaddress
from datetime import datetime
from log_generator import countries as country_ip_ranges, USER_ROLES

# Age groups for random assignment
AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55+"]

# utils.py - Update PLOTLY_COUNTRY_MAPPING
PLOTLY_COUNTRY_MAPPING = {
    'United States': 'United States of America',
    'United Kingdom': 'United Kingdom',
    'Germany': 'Germany',
    'France': 'France',
    'Japan': 'Japan',
    'India': 'India',
    'Brazil': 'Brazil',
    'Australia': 'Australia',
    'Canada': 'Canada',
    'China': 'China',
    'South Africa': 'South Africa',
    'Mexico': 'Mexico',
    'Russia': 'Russian Federation',
    'South Korea': 'South Korea',
    'Singapore': 'Singapore',
    'Italy': 'Italy',
    'Spain': 'Spain',
    'Netherlands': 'Netherlands',
    'Sweden': 'Sweden',
    'Switzerland': 'Switzerland'
}

# Reverse mapping for validation
PLOTLY_TO_OUR_COUNTRY = {v: k for k, v in PLOTLY_COUNTRY_MAPPING.items()}

def validate_dataframe(df):
    """Validate essential columns and country values."""
    required_columns = ['timestamp', 'ip', 'method', 'endpoint', 'status', 
                       'country', 'user_role', 'age_group']
    
    if not all(col in df.columns for col in required_columns):
        print("Missing required columns in dataframe")
        return False
    
    # Check for at least some valid data
    if df.empty or df['country'].isnull().all():
        print("Empty dataframe or no valid countries")
        return False
    
    return True

def categorize_endpoint(endpoint):
    """Categorize endpoints into business request types."""
    endpoint = str(endpoint).lower()
    if "scheduledemo" in endpoint:
        return "Scheduled Demo"
    elif "event" in endpoint:
        return "Promotional Event"
    elif "prototype" in endpoint or "jobs" in endpoint:
        return "Job Request"
    elif "ai-assistant" in endpoint:
        return "AI Assistant"
    else:
        print(f"Uncategorized endpoint: {endpoint}")
        return "Other"

def get_country_from_ip(ip):
    """Estimate country from IP address based on known ranges."""
    try:
        ip_obj = ipaddress.ip_address(ip)
        ip_int = int(ip_obj)
        for country, ranges in country_ip_ranges.items():
            for ip_range in ranges:
                network = ipaddress.ip_network(ip_range)
                if int(network.network_address) <= ip_int <= int(network.broadcast_address):
                    return country
        return "Unknown"
    except Exception:
        return "Unknown"

def process_logs(log_file="data/server_logs.csv"):
    try:
        df = pd.read_csv(log_file)

        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['datetime'])

        # Ensure country column exists and is valid
        if 'country' not in df.columns:
            df['country'] = df['ip'].apply(get_country_from_ip)
        
        # Create a dedicated column for Plotly-compatible country names
        df['plotly_country'] = df['country'].replace(PLOTLY_COUNTRY_MAPPING)
        
        # Remove any rows with null countries
        df = df.dropna(subset=['plotly_country'])
        
        # Categorize endpoints
        df['request_type'] = df['endpoint'].apply(categorize_endpoint)
        
        # Ensure numeric values
        df['status'] = pd.to_numeric(df['status'], errors='coerce')
        
        print("Processed data sample:", df[['country', 'plotly_country']].head())
        print("Unique plotly countries:", df['plotly_country'].unique())
        
        return df

    except Exception as e:
        print(f"Error processing logs: {e}")
        # Generate fresh logs if there's an error
        from log_generator import generate_logs
        generate_logs(5000, refresh=True)
        return process_logs(log_file)

def get_country_data(df, country):
    """Subset dataframe for a specific country."""
    # Convert back from Plotly country name to our name if needed
    original_country = PLOTLY_TO_OUR_COUNTRY.get(country, country)
    return df[df["country"] == original_country]

def get_request_type_counts(df, country=None):
    """Count request types, globally or by country."""
    if country:
        # Convert back from Plotly country name if needed
        original_country = PLOTLY_TO_OUR_COUNTRY.get(country, country)
        df = df[df["country"] == original_country]
    return df["request_type"].value_counts().reset_index()

def get_country_dataframe(df=None):
    """Prepare country summary dataframe with Plotly-compatible names."""
    if df is None:
        df = process_logs()

    if df.empty or 'plotly_country' not in df.columns:
        return pd.DataFrame({'country': [], 'count': []})

    counts = df['plotly_country'].value_counts().reset_index()
    counts.columns = ['country', 'count']
    return counts

def get_demographic_data(df, demographic_type='age_group', countries=None):
    """Return demographic stats."""
    if countries:
        # Convert Plotly country names back to our names if needed
        original_countries = [PLOTLY_TO_OUR_COUNTRY.get(c, c) for c in countries]
        df = df[df['country'].isin(original_countries)]

    if demographic_type == 'age_group':
        return df['age_group'].value_counts().reset_index()
    else:
        return df['user_role'].value_counts().reset_index()

def get_crossfilter_data(df, x_col, y_col):
    """Cross-tabulate x and y columns."""
    # Handle case where x_col or y_col is country (need to use plotly_country)
    if x_col == 'country':
        x_col = 'plotly_country'
    if y_col == 'country':
        y_col = 'plotly_country'
        
    return df.groupby([x_col, y_col]).size().reset_index(name='count')

def calculate_statistics(df, groupby_col=None):
    """Calculate general or grouped statistics."""
    if groupby_col and groupby_col != 'overall':
        # Handle country case specially
        if groupby_col == 'country':
            groupby_col = 'plotly_country'
            
        stats = df.groupby(groupby_col).agg({
            'age_group': lambda x: x.mode()[0] if not x.mode().empty else 'N/A',
            'user_role': lambda x: x.mode()[0] if not x.mode().empty else 'N/A',
            'request_type': lambda x: x.mode()[0] if not x.mode().empty else 'N/A',
            'country': 'count'
        }).rename(columns={
            'age_group': 'age_group_mode',
            'user_role': 'user_role_mode',
            'request_type': 'request_type_mode',
            'country': 'count'
        }).reset_index()
        
        # Convert back country names if needed
        if groupby_col == 'plotly_country':
            stats = stats.rename(columns={'plotly_country': 'country'})
    else:
        stats = pd.DataFrame({
            'Metric': ['Total Users', 'Unique Countries', 'Most Common Age Group',
                       'Most Common Role', 'Most Common Request Type'],
            'Value': [
                len(df),
                df['plotly_country'].nunique(),
                df['age_group'].mode()[0] if not df['age_group'].mode().empty else 'N/A',
                df['user_role'].mode()[0] if not df['user_role'].mode().empty else 'N/A',
                df['request_type'].mode()[0] if not df['request_type'].mode().empty else 'N/A'
            ]
        })

    return stats