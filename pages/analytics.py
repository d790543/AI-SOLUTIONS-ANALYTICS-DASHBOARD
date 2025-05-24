from dash import dcc, html, Input, Output, callback, dash_table
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from utils import calculate_statistics, PLOTLY_COUNTRY_MAPPING

def calculate_percentages(dataframe):
    counts = dataframe['request_type'].value_counts().reset_index()
    counts.columns = ['request_type', 'count']
    total = counts['count'].sum()
    counts['percentage'] = (counts['count'] / total * 100).round(1)
    return counts

layout = dbc.Container(
    id="analytics-container",
    style={'backgroundColor': 'var(--bg-color)', 'color': 'var(--text-color)'},
    children=[
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Request & Demographic Analytics", className="d-inline"),
                        dbc.Button(
                            "Export Data", 
                            id="export-analytics-btn", 
                            outline=True, 
                            color="success", 
                            className="float-end"
                        )
                    ], id="analytics-card-header"),
                    dbc.CardBody([
                        dbc.Tabs(
                            id="analytics-tabs",
                            children=[
                                dbc.Tab(
                                    id="request-composition-tab",
                                    children=html.Div([
                                        html.P("This pie chart shows the proportional distribution of different request types across all users. Percentages are shown for each segment.", 
                                               className="text-muted mb-3"),
                                        dcc.Graph(id='request-pie')
                                    ]),
                                    label="Request Composition",
                                    tab_id="request-composition",
                                    tabClassName="py-2"
                                ),
                                dbc.Tab(
                                    id="request-trends-tab",
                                    children=html.Div([
                                        html.P("This stacked histogram reveals how request patterns change over time. Each colored segment represents a different request type.", 
                                               className="text-muted mb-3"),
                                        dcc.Graph(id='request-trends')
                                    ]),
                                    label="Request Trends",
                                    tab_id="request-trends",
                                    tabClassName="py-2"
                                ),
                                dbc.Tab(
                                    id="user-distribution-tab",
                                    children=html.Div([
                                        html.P("Analyze the distribution of the users by either age group (bar chart) or role (pie chart). Use the country filter to focus on specific regions.", 
                                               className="text-muted mb-3"),
                                        dbc.Row([
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='demographic-type',
                                                    options=[
                                                        {'label': 'Age Group', 'value': 'age_group'},
                                                        {'label': 'User Role', 'value': 'user_role'}
                                                    ],
                                                    value='age_group',
                                                    clearable=False,
                                                    className="mb-3"
                                                ),
                                                width=4
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='country-filter-demographic',
                                                    multi=True,
                                                    placeholder="All Countries",
                                                    className="mb-3"
                                                ),
                                                width=4
                                            )
                                        ]),
                                        dcc.Graph(id='demographic-chart')
                                    ]),
                                    label="User Distribution",
                                    tab_id="user-distribution",
                                    tabClassName="py-2"
                                ),
                                dbc.Tab(
                                    id="cross-analysis-tab",
                                    children=html.Div([
                                        html.P("This heatmap reveals relationships between different user attributes and their behavior. Darker cells indicate stronger correlations.", 
                                               className="text-muted mb-3"),
                                        dbc.Row([
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='crossfilter-x',
                                                    options=[
                                                        {'label': 'Age Group', 'value': 'age_group'},
                                                        {'label': 'User Role', 'value': 'user_role'},
                                                        {'label': 'Country', 'value': 'plotly_country'}
                                                    ],
                                                    value='age_group',
                                                    clearable=False,
                                                    className="mb-3"
                                                ),
                                                width=6
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='crossfilter-y',
                                                    options=[
                                                        {'label': 'Request Type', 'value': 'request_type'},
                                                        {'label': 'Status Code', 'value': 'status'}
                                                    ],
                                                    value='request_type',
                                                    clearable=False,
                                                    className="mb-3"
                                                ),
                                                width=6
                                            )
                                        ]),
                                        dcc.Graph(id='crossfilter-chart')
                                    ]),
                                    label="Cross Analysis",
                                    tab_id="cross-analysis",
                                    tabClassName="py-2"
                                ),
                                dbc.Tab(
                                    id="statistics-tab",
                                    children=html.Div([
                                        html.P("View key statistics about the user base. Choose whether to see overall metrics or statistics grouped by specific factors.", 
                                               className="text-muted mb-3"),
                                        dbc.Row([
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id='stats-groupby',
                                                    options=[
                                                        {'label': 'Overall Statistics', 'value': 'overall'},
                                                        {'label': 'By Country', 'value': 'plotly_country'},
                                                        {'label': 'By Age Group', 'value': 'age_group'},
                                                        {'label': 'By User Role', 'value': 'user_role'}
                                                    ],
                                                    value='overall',
                                                    clearable=False,
                                                    className="mb-3"
                                                ),
                                                width=6
                                            )
                                        ]),
                                        html.Div(id='stats-table-container')
                                    ]),
                                    label="Statistics",
                                    tab_id="statistics",
                                    tabClassName="py-2"
                                )
                            ],
                            active_tab="request-composition"
                        )
                    ], id="analytics-card-body")
                ], className="shadow-lg mb-4"),
                width=12
            )
        ]),
        dcc.Download(id="download-analytics")
    ],
    fluid=True
)

@callback(
    Output('country-filter-demographic', 'options'),
    Input('data-store', 'data')
)
def update_country_filter(data):
    if not data:
        return []
    df = pd.DataFrame(data)
    # Use plotly_country if available, otherwise fall back to country
    country_col = 'plotly_country' if 'plotly_country' in df.columns else 'country'
    return [{'label': c, 'value': c} for c in df[country_col].unique()]

@callback(
    Output('request-pie', 'figure'),
    Input('data-store', 'data')
)
def update_pie_chart(data):
    if not data:
        return px.pie(title="No data available")
    
    try:
        df = pd.DataFrame(data)
        percent_df = calculate_percentages(df)
        
        return px.pie(
            percent_df,
            names='request_type',
            values='percentage',
            hole=0.3,
            title="Global Request Distribution (%)",
            hover_data=['count'],
            labels={'percentage': 'Percentage', 'count': 'Total Count'}
        ).update_layout(
            paper_bgcolor='var(--card-bg)',
            font_color='var(--text-color)',
            uniformtext_minsize=12,
            uniformtext_mode='hide'
        )
    except Exception as e:
        print(f"Error updating pie chart: {e}")
        return px.pie(title="Error loading data")

@callback(
    Output('request-trends', 'figure'),
    Input('data-store', 'data')
)
def update_trends_chart(data):
    if not data:
        return px.histogram(title="No data available")
    
    try:
        df = pd.DataFrame(data)
        
        # Ensure datetime is properly formatted
        if 'datetime' not in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['datetime'])
        
        # Calculate appropriate number of bins
        unique_dates = len(df['datetime'].unique())
        nbins = min(20, unique_dates) if unique_dates > 0 else 1
        
        fig = px.histogram(
            df,
            x='datetime',
            color='request_type',
            title="Requests by Type Over Time",
            nbins=nbins,
            barmode='stack'
        )
        
        return fig.update_layout(
            paper_bgcolor='var(--card-bg)',
            plot_bgcolor='var(--card-bg)',
            font_color='var(--text-color)',
            yaxis_title="Number of Requests",
            xaxis_title="Date"
        )
        
    except Exception as e:
        print(f"Error updating trends chart: {e}")
        return px.histogram(title="Error loading data")
    
@callback(
    Output('demographic-chart', 'figure'),
    [Input('demographic-type', 'value'),
     Input('country-filter-demographic', 'value'),
     Input('data-store', 'data')]
)
def update_demographic_chart(demographic_type, countries, data):
    if not data:
        return px.bar()
    
    df = pd.DataFrame(data)
    
    # Filter by selected countries if any
    if countries and len(countries) > 0:
        # Use plotly_country if available, otherwise fall back to country
        country_col = 'plotly_country' if 'plotly_country' in df.columns else 'country'
        filtered_df = df[df[country_col].isin(countries)]
    else:
        filtered_df = df
    
    if filtered_df.empty:
        return px.bar()
    
    if demographic_type == 'age_group':
        demo_data = filtered_df['age_group'].value_counts().reset_index()
        demo_data.columns = ['age_group', 'count']
        fig = px.bar(
            demo_data,
            x='age_group',
            y='count',
            title="Age Group Distribution",
            color='age_group',
            color_discrete_sequence=px.colors.sequential.Plasma,
            labels={'count': 'Number of Users'},
            text='count'
        )
    else:
        demo_data = filtered_df['user_role'].value_counts().reset_index()
        demo_data.columns = ['user_role', 'count']
        fig = px.pie(
            demo_data,
            names='user_role',
            values='count',
            title="User Role Distribution",
            hole=0.3,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
    
    return fig.update_layout(
        paper_bgcolor='var(--card-bg)',
        plot_bgcolor='var(--card-bg)',
        font_color='var(--text-color)',
        margin={'t': 40, 'b': 20}
    )

@callback(
    Output('crossfilter-chart', 'figure'),
    [Input('crossfilter-x', 'value'),
     Input('crossfilter-y', 'value'),
     Input('data-store', 'data')]
)
def update_crossfilter_chart(x_col, y_col, data):
    if not data:
        return px.density_heatmap()
    
    df = pd.DataFrame(data)
    
    # Ensure we have data for the selected columns
    if x_col not in df.columns or y_col not in df.columns:
        return px.density_heatmap()
    
    cross_data = df.groupby([x_col, y_col]).size().reset_index(name='count')
    
    if cross_data.empty:
        return px.density_heatmap()
    
    # For categorical data, use histogram2d
    if df[x_col].dtype == 'object' and df[y_col].dtype == 'object':
        fig = px.density_heatmap(
            cross_data,
            x=x_col,
            y=y_col,
            z='count',
            histfunc="sum",
            title=f"{x_col.title()} vs {y_col.title()} Distribution",
            color_continuous_scale='Viridis'
        )
    else:
        # For mixed or numerical data
        fig = px.scatter(
            cross_data,
            x=x_col,
            y=y_col,
            size='count',
            color='count',
            title=f"{x_col.title()} vs {y_col.title()} Distribution",
            color_continuous_scale='Viridis'
        )
    
    return fig.update_layout(
        paper_bgcolor='var(--card-bg)',
        plot_bgcolor='var(--card-bg)',
        font_color='var(--text-color)',
        xaxis_title=x_col.title(),
        yaxis_title=y_col.title(),
        margin={'t': 40, 'b': 20}
    )

@callback(
    Output('stats-table-container', 'children'),
    [Input('stats-groupby', 'value'),
     Input('data-store', 'data')]
)
def update_stats_table(groupby_col, data):
    if not data:
        return dash.no_update
    
    df = pd.DataFrame(data)
    stats_df = calculate_statistics(df, groupby_col)
    stats_df = stats_df.astype(str)
    
    if groupby_col == 'overall':
        columns = [{"name": "Metric", "id": "Metric"}, {"name": "Value", "id": "Value"}]
    else:
        columns = [{"name": col, "id": col} for col in stats_df.columns]
    
    return dash_table.DataTable(
        id='stats-table',
        columns=columns,
        data=stats_df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'minWidth': '100px', 'width': '150px', 'maxWidth': '300px',
            'whiteSpace': 'normal',
            'backgroundColor': 'var(--card-bg)',
            'color': 'var(--text-color)'
        },
        style_header={
            'backgroundColor': 'var(--card-bg)',
            'color': 'var(--text-color)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'var(--bg-color)'
            }
        ],
        filter_action="native",
        sort_action="native",
        page_size=10
    )

@callback(
    Output("download-analytics", "data"),
    [Input("export-analytics-btn", "n_clicks"),
     Input('data-store', 'data')],
    prevent_initial_call=True
)
def export_analytics(n_clicks, data):
    if n_clicks and data:
        df = pd.DataFrame(data)
        return dcc.send_data_frame(
            df.to_csv,
            "analytics_data.csv",
            index=False
        )
    return dash.no_update

