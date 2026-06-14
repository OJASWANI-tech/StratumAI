import os
import pandas as pd
import pycountry
import dash
import dash_bootstrap_components as dbc
import dash_table
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

# Data Loading
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, 'dataset.csv')
df = pd.read_csv(dataset_path)

# Add ISO-3 country codes for choropleth
def country_to_iso(name: str) -> str:
    try:
        return pycountry.countries.lookup(name).alpha_3
    except Exception:
        return None

df['iso_code'] = df['Country'].apply(country_to_iso)

# App Setup
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)

# Controls
controls = dbc.Row(
    [
        dbc.Col(
            dcc.Dropdown(
                id='country_selector',
                options=[{'label': 'All', 'value': 'All'}] + [
                    {'label': c, 'value': c} for c in sorted(df['Country'].unique())
                ],
                value='All',
                clearable=False,
                style={'color': 'black'},
            ),
            width=3,
        ),
        dbc.Col(
            dcc.Slider(
                id='year_slider',
                min=df['Year'].min(),
                max=df['Year'].max(),
                step=1,
                value=df['Year'].min(),
                marks={y: str(y) for y in range(df['Year'].min(), df['Year'].max() + 1, 5)},
                tooltip={"placement": "bottom", "always_visible": True},
            ),
            width=5,
        ),
        dbc.Col(
            dcc.Dropdown(
                id='metric_selector',
                options=[
                    {'label': 'GDP per Capita', 'value': 'GDP_per_capita'},
                    {'label': 'Life Expectancy', 'value': 'Life_Expectancy'},
                    {'label': 'Population', 'value': 'Population'},
                    {'label': 'CO₂ per Capita', 'value': 'CO2_per_capita'},
                ],
                value='GDP_per_capita',
                clearable=False,
                style={'color': 'black'},
            ),
            width=2,
        ),
        dbc.Col(
            html.Button(
                id='play_pause_button',
                children='Play',
                n_clicks=0,
                style={'backgroundColor': '#374151', 'color': 'white', 'border': 'none', 'padding': '6px 12px'}
            ),
            width=2,
        ),
    ],
    className='my-2',
)

# Layout
app.layout = dbc.Container(
    [
        html.H1(
            "Global Sustainability & Prosperity Dashboard",
            style={'textAlign': 'center', 'color': 'white', 'fontFamily': 'Inter, sans-serif', 'marginBottom': '2rem'}
        ),
        controls,
        dcc.Store(id='filtered-data', storage_type='memory'),
        dcc.Interval(id='interval', interval=1000, n_intervals=0, disabled=True),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='choropleth_co2'), width=4),
                dbc.Col(dcc.Graph(id='gdp_time_series'), width=4),
                dbc.Col(dcc.Graph(id='population_bubble'), width=4),
            ],
            className='my-2',
        ),
        dbc.Row(
            [
                dbc.Col(
                    dash_table.DataTable(
                        id='data_table',
                        columns=[{'name': c, 'id': c} for c in df.columns if c != 'iso_code'],
                        page_size=10,
                        style_table={'overflowX': 'auto'},
                        style_header={'backgroundColor': '#374151', 'color': 'white'},
                        style_cell={'backgroundColor': '#1f2937', 'color': 'white'},
                    ),
                    width=12,
                )
            ],
            className='my-2',
        ),
        dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Dynamic Insights", className='card-title', style={'color': 'white'}),
                    html.Div(id='insights_panel', style={'color': 'white'})
                ]
            ),
            className='my-2',
        ),
    ],
    fluid=True,
    style={'background': 'linear-gradient(180deg, #111827 0%, #1f2937 100%)', 'minHeight': '100vh', 'color': 'white'},
)

# Callbacks
@callback(
    Output('filtered-data', 'data'),
    Input('country_selector', 'value'),
    Input('year_slider', 'value')
)
def filter_data(selected_country: str, selected_year: int):
    if selected_country is None or selected_year is None:
        raise PreventUpdate
    dff = df.copy()
    if selected_country != 'All':
        dff = dff[dff['Country'] == selected_country]
    dff = dff[dff['Year'] == selected_year]
    return dff.to_dict('records')

@callback(
    Output('choropleth_co2', 'figure'),
    Input('filtered-data', 'data')
)
def update_choropleth(data):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    fig = px.choropleth(
        dff,
        locations='iso_code',
        color='CO2_per_capita',
        hover_name='Country',
        color_continuous_scale='Viridis',
        labels={'CO2_per_capita': 'CO₂ per Capita'},
        projection='natural earth',
    )
    fig.update_layout(
        title='CO₂ per Capita by Country',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig

@callback(
    Output('gdp_time_series', 'figure'),
    Input('country_selector', 'value')
)
def update_gdp_series(selected_country: str):
    if selected_country is None:
        raise PreventUpdate
    dff = df.copy()
    if selected_country != 'All':
        dff = dff[dff['Country'] == selected_country]
    fig = px.line(
        dff,
        x='Year',
        y='GDP_per_capita',
        color='Country' if selected_country == 'All' else None,
        labels={'GDP_per_capita': 'GDP per Capita'},
    )
    fig.update_layout(
        title='GDP per Capita Over Time',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_title_text='Country',
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig

@callback(
    Output('population_bubble', 'figure'),
    Input('filtered-data', 'data'),
    Input('metric_selector', 'value')
)
def update_population_bubble(data, metric):
    if not data or not metric:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    fig = px.scatter(
        dff,
        x=metric,
        y='Life_Expectancy',
        size='Population',
        color='Country',
        labels={metric: metric.replace('_', ' '), 'Life_Expectancy': 'Life Expectancy'},
    )
    fig.update_layout(
        title=f'{metric.replace("_", " ")} vs Life Expectancy with Population Size',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig

@callback(
    Output('data_table', 'data'),
    Input('filtered-data', 'data')
)
def update_table(data):
    if not data:
        raise PreventUpdate
    return data

@callback(
    Output('insights_panel', 'children'),
    Input('country_selector', 'value'),
    Input('year_slider', 'value'),
    Input('metric_selector', 'value')
)
def update_insights(country, year, metric):
    if country is None or year is None or metric is None:
        raise PreventUpdate
    base = [
        "Economic Growth: GDP per capita has risen steadily across most countries, with the fastest growth in emerging economies.",
        "Health Outcomes: Life expectancy improvements correlate strongly with GDP per capita.",
        "Environmental Impact: CO₂ per capita peaks in high‑income countries but is trending downward globally.",
        "Population Dynamics: Rapid population growth in developing nations drives future demand."
    ]
    if country != 'All':
        base.insert(0, f"Selected Country: {country}")
    base.append(f"Year: {year} – Metric for analysis: {metric.replace('_', ' ')}")
    return html.Ul([html.Li(txt) for txt in base])

# Animation Controls
@callback(
    Output('interval', 'disabled'),
    Input('play_pause_button', 'n_clicks'),
    State('interval', 'disabled')
)
def toggle_animation(n_clicks, disabled):
    if n_clicks is None:
        raise PreventUpdate
    return not disabled

@callback(
    Output('play_pause_button', 'children'),
    Input('interval', 'disabled')
)
def update_button_label(disabled):
    return 'Pause' if not disabled else 'Play'

@callback(
    Output('year_slider', 'value'),
    Input('interval', 'n_intervals'),
    State('year_slider', 'value')
)
def animate_year(n_intervals, current_year):
    if ctx.triggered_id != 'interval':
        raise PreventUpdate
    max_year = df['Year'].max()
    next_year = current_year + 1 if current_year < max_year else df['Year'].min()
    return next_year

# Run Server
if __name__ == '__main__':
    port = int(os.getenv('PORT', '8050'))
    app.run(host='0.0.0.0', port=port, debug=True)