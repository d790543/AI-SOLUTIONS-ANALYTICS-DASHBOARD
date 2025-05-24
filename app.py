# app.py

import dash
from dash import Dash, dcc, html, Input, Output, State, callback, no_update, dash_table
import dash_bootstrap_components as dbc
from pages import home, analytics
import os
import pandas as pd
from utils import process_logs

def ensure_data_loaded():
    """Ensure log data exists and is valid"""
    os.makedirs("data", exist_ok=True)
    
    # Check if data needs to be regenerated
    if not os.path.exists("data/server_logs.csv"):
        print("Generating fresh log data...")
        from log_generator import generate_logs
        generate_logs(num_entries=5000, output_file="data/server_logs.csv", refresh=True)
    else:
        print("Using existing log data")

ensure_data_loaded()

# Initialize the app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    assets_folder="assets",
    title="AI Solutions Analytics",
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}]
)

# Data store for sharing data across pages
data_store = dcc.Store(id='data-store')

# App Layout
app.layout = html.Div(
    id="main-container",
    style={'minHeight': '100vh'},
    children=[
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='selected-country'),
        data_store,
        dcc.Download(id="download-data"),
        html.Div(id='debug-output', style={'display': 'block'}),  # Changed to block for debugging

        # Navbar
        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand("AI Solutions Dashboard", className="ms-2"),
                dbc.Nav([
                    dbc.NavLink("Home", href="/", active="exact", key="home-link"),
                    dbc.NavLink("Analytics", href="/analytics", active="exact", key="analytics-link"),
                ], pills=True),
            ], fluid=True),
            color="primary",
            dark=True,
            className="mb-4"
        ),

        # Page Content
        html.Div(id='page-content', className="container-fluid")
    ]
)

# Load and store processed data
@app.callback(
    Output('data-store', 'data'),
    Input('url', 'pathname')
)
def load_data(pathname):
    df = process_logs()
    return df.to_dict('records')


# Page Routing
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/analytics':
        return analytics.layout
    elif pathname == '/':
        return home.layout
    else:
        return html.Div("404 Page Not Found", key="not-found")

# Run the app
if __name__ == '__main__':
    app.run(debug=True)