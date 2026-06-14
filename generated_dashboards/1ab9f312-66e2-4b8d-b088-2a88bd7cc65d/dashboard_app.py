import os
import pandas as pd
import datetime as dt
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
import plotly.express as px
import plotly.graph_objects as go

# -------------------- Data Loading & Pre‑processing --------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, "dataset.csv")
df = pd.read_csv(dataset_path)

# Convert datetime columns
df["DepartureTime"] = pd.to_datetime(df["DepartureTime"])
df["ArrivalTime"] = pd.to_datetime(df["ArrivalTime"])
df["Year"] = df["DepartureTime"].dt.year

# Calculate additional features
df["FlightDuration"] = df["ArrivalTime"] - df["DepartureTime"]
df["FlightDuration"] = df["FlightDuration"].dt.total_seconds() / 3600  # Hours

# Get unique years for slider
year_options = sorted(df["Year"].unique())
year_min, year_max = min(year_options), max(year_options)

# -------------------- App Setup --------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)
app.title = "Flight Operations Dashboard"

# -------------------- Controls Panel --------------------
controls = dbc.Card(
    dbc.CardBody(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Origin", htmlFor="origin_selector", className="text-white"),
                            dcc.Dropdown(
                                id="origin_selector",
                                options=[{"label": "All", "value": "All"}] +
                                        [{"label": c, "value": c} for c in sorted(df["Origin"].unique())],
                                value="All",
                                clearable=False,
                                style={"color": "black"}
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Label("Metric", htmlFor="metric_selector", className="text-white"),
                            dcc.Dropdown(
                                id="metric_selector",
                                options=[
                                    {"label": "Passengers", "value": "Passengers"},
                                    {"label": "Distance (km)", "value": "Distance_km"},
                                    {"label": "Flight Duration (hours)", "value": "FlightDuration"},
                                    {"label": "Fuel Usage (L)", "value": "FuelUsed_Liters"},
                                    {"label": "Revenue (USD)", "value": "Revenue_USD"},
                                ],
                                value="Passengers",
                                clearable=False,
                                style={"color": "black"}
                            ),
                        ],
                        width=6,
                    ),
                ],
                className="g-2",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Year Range", htmlFor="year_slider", className="text-white"),
                            dcc.RangeSlider(
                                id="year_slider",
                                min=year_min,
                                max=year_max,
                                value=[year_min, year_max],
                                step=1,
                                marks={y: str(y) for y in year_options},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="g-2 mt-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Animation", className="text-white"),
                            dcc.Checklist(
                                id="play_pause_button",
                                options=[{"label": "Play", "value": "play"}],
                                value=[],
                                style={"margin-top": "10px"},
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
        ]
    ),
    className="mb-4",
)

# -------------------- Layout --------------------
app.layout = dbc.Container(
    [
        html.H1(
            "Flight Operations Dashboard",
            style={"color": "#fff", "fontFamily": "Roboto, sans-serif", "fontSize": 24},
            className="my-4 text-center",
        ),
        dcc.Store(id="filtered-data", storage_type="memory"),
        controls,
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="route_map"), width=6),
                dbc.Col(dcc.Graph(id="time_series"), width=6),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4("Route Information", className="text-white"),
                        html.Div(id="route_info_panel", className="text-white p-2 bg-dark rounded"),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        html.H4("Dynamic Insights", className="text-white"),
                        html.Div(id="insights_panel", className="text-white p-2 bg-dark rounded"),
                    ],
                    width=6,
                ),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Loading(
                        dcc.DataTable(
                            id="data_table",
                            columns=[{"name": c, "id": c} for c in df.columns],
                            page_size=10,
                            filter_action="native",
                            sort_action="native",
                            style_table={"overflowX": "auto", "height": "300px"},
                            style_header={"backgroundColor": "#2c2c2c", "color": "white"},
                            style_cell={"backgroundColor": "#1e1e1e", "color": "white"},
                        ),
                        type="circle",
                    ),
                    width=12,
                )
            ],
        ),
        html.Div(id="animation-state", style={"display": "none"}),
    ],
    fluid=True,
    style={"background": "#1e1e1e"},
)

# -------------------- Callbacks --------------------
@callback(
    Output("filtered-data", "data"),
    Input("origin_selector", "value"),
    Input("year_slider", "value"),
)
def filter_data(selected_origin: str, selected_years: list) -> list[dict]:
    dff = df.copy()
    if selected_origin != "All":
        dff = dff[dff["Origin"] == selected_origin]
    dff = dff[(dff["Year"] >= selected_years[0]) & (dff["Year"] <= selected_years[1])]
    if dff.empty:
        raise PreventUpdate
    return dff.to_dict("records")

@callback(
    Output("route_map", "figure"),
    Input("filtered-data", "data"),
    Input("metric_selector", "value"),
)
def update_route_map(data: list[dict], metric: str):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    
    # Create mapbox figure
    fig = go.Figure()
    fig.update_layout(
        mapbox_style="mapbox://styles/mapbox/dark-v10",
        mapbox_center_lat=40,
        mapbox_center_lon=-100,
        mapbox_zoom=3,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    
    # Add origin-destination lines
    origins = dff["Origin"].unique()
    for origin in origins:
        origin_df = dff[dff["Origin"] == origin]
        destinations = origin_df["Destination"].unique()
        for dest in destinations:
            route_df = origin_df[origin_df["Destination"] == dest]
            fig.add_trace(
                go.Scattermapbox(
                    lat=[route_df["DepartureTime"].iloc[0].city or 0, 
                        route_df["ArrivalTime"].iloc[0].city or 0],
                    lon=[route_df["DepartureTime"].iloc[0].city or 0, 
                        route_df["ArrivalTime"].iloc[0].city or 0],
                    mode="lines",
                    line=dict(color="#1f77b4", width=1),
                    showlegend=False,
                    hoverinfo="none"
                )
            )
    
    return fig

@callback(
    Output("time_series", "figure"),
    Input("filtered-data", "data"),
    Input("metric_selector", "value"),
)
def update_time_series(data: list[dict], metric: str):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    
    if dff.empty:
        return go.Figure()
    
    # Group by year and month
    dff["YearMonth"] = dff["DepartureTime"].dt.to_period("M")
    df_plot = dff.groupby("YearMonth")[metric].mean().reset_index()
    
    fig = px.line(
        df_plot,
        x="YearMonth",
        y=metric,
        title=f"{metric} Over Time",
        markers=True,
    )
    fig.update_traces(line=dict(color="#1f77b4"))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Date",
        yaxis_title=metric,
        transition={"duration": 500},
    )
    return fig

@callback(
    Output("insights_panel", "children"),
    Input("filtered-data", "data"),
    Input("metric_selector", "value"),
)
def update_insights(data: list[dict], metric: str):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    
    # Calculate key metrics
    total = dff[metric].sum()
    avg = dff[metric].mean()
    max_val = dff[metric].max()
    min_val = dff[metric].min()
    
    return html.Div(
        [
            html.P(f"Total {metric}: {total:.2f}", className="mb-2"),
            html.P(f"Average {metric}: {avg:.2f}", className="mb-2"),
            html.P(f"Maximum {metric}: {max_val:.2f}", className="mb-2"),
            html.P(f"Minimum {metric}: {min_val:.2f}"),
        ],
        className="text-white"
    )

@callback(
    Output("data_table", "data"),
    Input("filtered-data", "data"),
)
def update_table(data: list[dict]):
    if not data:
        raise PreventUpdate
    return data

@callback(
    Output("route_info_panel", "children"),
    Input("route_map", "clickData"),
    Input("filtered-data", "data"),
)
def update_route_info(clickData, data):
    if not data or not clickData:
        return ""
    
    dff = pd.DataFrame(data)
    point = clickData["points"][0]
    lat = point["lat"]
    lon = point["lon"]
    
    # Find nearest route
    route_info = dff.iloc[dff.submissions.index(closest to (lat, lon))]
    
    return html.Div(
        [
            html.P(f"Route: {route_info['Route']}"),
            html.P(f"Origin: {route_info['Origin']}"),
            html.P(f"Destination: {route_info['Destination']}"),
            html.P(f"Passengers: {route_info['Passengers']}"),
            html.P(f"Distance: {route_info['Distance_km']} km"),
        ]
    )

# -------------------- Animation --------------------
@callback(
    Output("year_slider", "value"),
    Input("play_pause_button", "value"),
    State("year_slider", "value"),
    State("animation-state", "children"),
    prevent_initial_call=True,
)
def animate_year(play_state: list, current_value: list, animation_state: str):
    if not play_state:
        return current_value
    
    # Get current state
    current_start, current_end = current_value
    year_options = sorted(df["Year"].unique())
    
    # Animate by moving the window
    window_size = 5
    new_start = current_start
    new_end = current_end
    
    if current_end < year_max:
        new_start = current_start + 1
        new_end = current_end + 1
    elif current_end == year_max:
        new_start = year_min
        new_end = year_min + window_size
    
    return [new_start, new_end]

# -------------------- Main --------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8050"))
    app.run(host="0.0.0.0", port=port, debug=True)