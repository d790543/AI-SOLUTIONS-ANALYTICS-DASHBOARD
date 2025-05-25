from dash import dcc, html, Input, Output, State, callback, no_update, dash_table
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from utils import get_country_dataframe, PLOTLY_COUNTRY_MAPPING
import logging

logger = logging.getLogger(__name__)

# Drilldown Modal Component
drilldown_modal = dbc.Modal([
    dbc.ModalHeader([
        dbc.ModalTitle(id='drilldown-title'),
        dbc.Button(
            "Export Country Data",
            id="export-drilldown-btn",
            color="success",
            outline=True,
            className="ms-2"
        )
    ]),
    dbc.ModalBody([
        dbc.Tabs([
            dbc.Tab(
                html.Div([
                    html.P("Shows the breakdown of different request types for the selected country.", 
                           className="text-muted mb-3"),
                    dcc.Graph(id='country-request-types')
                ]),
                label="Request Types",
                className="p-3"
            ),
            dbc.Tab(
                html.Div([
                    html.P("Displays the age distribution of users in this country.", 
                           className="text-muted mb-3"),
                    dcc.Graph(id='country-age-groups')
                ]),
                label="Age Groups",
                className="p-3"
            ),
            dbc.Tab(
                html.Div([
                    html.P("Illustrates how different user roles interact with the services.", 
                           className="text-muted mb-3"),
                    dcc.Graph(id='country-role-distribution')
                ]),
                label="User Roles",
                className="p-3"
            )
        ])
    ]),
    dbc.ModalFooter(
        dbc.Button("Close", id="close-drilldown", className="ml-auto")
    )
], id="drilldown-modal", size="xl", scrollable=True)

# Main Layout
layout = dbc.Container(
    id="page-container",
    style={'backgroundColor': 'var(--bg-color)', 'color': 'var(--text-color)'},
    children=[
        drilldown_modal,
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Global Request Distribution", className="d-inline"),
                        dbc.Button(
                            "Export All Data",
                            id="export-all-btn",
                            color="primary",
                            outline=True,
                            className="float-end"
                        )
                    ]),
                    dbc.CardBody([
                        html.P("This interactive world map visualizes request volumes across different countries.", 
                               className="text-muted mb-3"),
                        dcc.Graph(
                            id='world-map',
                            config={
                                'displayModeBar': True,
                                'scrollZoom': True,
                                'displaylogo': False
                            }
                        )
                    ])
                ], className="shadow-lg mb-4"),
                width=12
            )
        ]),
        dcc.Store(id='selected-country'),
        dcc.Download(id="download-all-data"),
        dcc.Download(id="download-country-data")
    ],
    fluid=True
)

# World Map Visualization
@callback(
    Output("world-map", "figure"),
    Input('data-store', 'data'),
    prevent_initial_call=False
)
def update_map(data):
    if not data:
        return px.choropleth(title="Data loading...")
    
    try:
        df = pd.DataFrame(data)
        
        if 'plotly_country' not in df.columns:
            df['plotly_country'] = df['country'].replace(PLOTLY_COUNTRY_MAPPING)
        
        if df['plotly_country'].isnull().all():
            return px.choropleth(title="No valid country data available")
        
        country_counts = df['plotly_country'].value_counts().reset_index()
        country_counts.columns = ['country', 'requests']
        
        fig = px.choropleth(
            country_counts,
            locations="country",
            locationmode="country names",
            color="requests",
            color_continuous_scale=px.colors.sequential.Plasma,
            range_color=[country_counts['requests'].min(), country_counts['requests'].max()],
            hover_name="country",
            hover_data={"requests": ":,", "country": False},
            title="<b>Live Request Heatmap</b>",
            height=700
        )
        
        fig.update_geos(
            projection_type="natural earth",
            showcountries=True,
            countrycolor="lightgray",
            showocean=True,
            oceancolor="lightblue"
        )
        
        fig.update_layout(
            margin={"r":0,"t":40,"l":0,"b":0},
            coloraxis_colorbar={
                "title": "Requests",
                "thickness": 20
            },
            geo=dict(
                bgcolor='rgba(0,0,0,0)',
                landcolor='lightgray'
            )
        )
        
        return fig
        
    except Exception as e:
        print(f"Map error: {str(e)}")
        return px.choropleth(title="Error visualizing data")

# Combined Drilldown Handler (fixes duplicate callback issue)
@callback(
    [Output('drilldown-modal', 'is_open'),
     Output('drilldown-title', 'children'),
     Output('selected-country', 'data')],
    [Input('world-map', 'clickData'),
     Input('close-drilldown', 'n_clicks')],
    [State('drilldown-modal', 'is_open'),
     State('selected-country', 'data')],
    prevent_initial_call=True
)
def handle_drilldown(click_data, close_clicks, is_open, current_country):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'world-map' and click_data:
        country = click_data['points'][0]['location']
        return True, f"Country Analysis: {country}", country
    elif trigger_id == 'close-drilldown':
        return False, dash.no_update, current_country
    
    return is_open, dash.no_update, current_country

# Drilldown Visualizations
@callback(
    [Output('country-request-types', 'figure'),
     Output('country-age-groups', 'figure'),
     Output('country-role-distribution', 'figure')],
    [Input('selected-country', 'data'),
     Input('data-store', 'data')]
)
def update_drilldown_visualizations(country, data):
    if not country or not data:
        return no_update, no_update, no_update
    
    try:
        df = pd.DataFrame(data)
        country_col = 'plotly_country' if 'plotly_country' in df.columns else 'country'
        country_df = df[df[country_col] == country]
        
        if country_df.empty:
            return no_update, no_update, no_update
        
        # Request Types Chart
        req_counts = country_df['request_type'].value_counts().reset_index()
        req_counts.columns = ['request_type', 'count']
        req_fig = px.bar(
            req_counts,
            x='request_type',
            y='count',
            title=f"Request Types in {country}",
            color='request_type',
            labels={'count': 'Number of Requests'},
            color_discrete_sequence=px.colors.qualitative.Pastel
        ).update_layout(
            paper_bgcolor='var(--card-bg)',
            plot_bgcolor='var(--card-bg)',
            font_color='var(--text-color)'
        )
        
        # Age Group Chart
        age_fig = px.pie(
            country_df,
            names='age_group',
            title=f"Age Groups in {country}",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Plasma
        ).update_layout(
            paper_bgcolor='var(--card-bg)',
            font_color='var(--text-color)'
        )
        
        # User Roles Chart
        role_counts = country_df.groupby(['user_role', 'request_type']).size().reset_index(name='count')
        role_fig = px.bar(
            role_counts,
            x='user_role',
            y='count',
            color='request_type',
            title=f"User Roles in {country}",
            labels={'count': 'Number of Requests', 'user_role': 'User Role'},
            barmode='stack',
            color_discrete_sequence=px.colors.qualitative.Set3
        ).update_layout(
            paper_bgcolor='var(--card-bg)',
            plot_bgcolor='var(--card-bg)',
            font_color='var(--text-color)',
            xaxis={'categoryorder': 'total descending'},
            legend_title_text='Request Type'
        )
        
        return req_fig, age_fig, role_fig
        
    except Exception as e:
        print(f"Error in drilldown visualizations: {e}")
        return no_update, no_update, no_update

# Data Export Callbacks
@callback(
    Output("download-all-data", "data"),
    [Input("export-all-btn", "n_clicks"),
     Input('data-store', 'data')],
    prevent_initial_call=True
)
def export_all_data(n_clicks, data):
    if n_clicks and data:
        df = pd.DataFrame(data)
        return dcc.send_data_frame(
            df.to_csv,
            "all_requests_data.csv",
            index=False
        )
    return no_update

@callback(
    Output("download-country-data", "data"),
    [Input("export-drilldown-btn", "n_clicks"),
     Input('selected-country', 'data'),
     Input('data-store', 'data')],
    prevent_initial_call=True
)
def export_country_data(n_clicks, country, data):
    if n_clicks and country and data:
        df = pd.DataFrame(data)
        country_col = 'plotly_country' if 'plotly_country' in df.columns else 'country'
        country_df = df[df[country_col] == country]
        return dcc.send_data_frame(
            country_df.to_csv,
            f"{country}_requests_data.csv",
            index=False
        )
    return no_update
