import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go

# Data Loading & Preprocessing
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, 'dataset.csv')
df = pd.read_csv(dataset_path)

# Convert times
df['DepartureTime'] = pd.to_datetime(df['DepartureTime'])
df['ArrivalTime'] = pd.to_datetime(df['ArrivalTime'])
df['DepHour'] = df['DepartureTime'].dt.hour

# City coordinates
city_coords = {
    "New York": (40.7128, -74.0060),
    "Boston": (42.3601, -71.0589),
    "Seattle": (47.6062, -122.3321),
    "Chicago": (41.8781, -87.6298),
    "Miami": (25.7617, -80.1918),
    "San Francisco": (37.7749, -122.4194),
    "Los Angeles": (34.0522, -118.2437),
    "City 1": (34.0, -118.0),
    "City 2": (40.0, -74.0),
    "City 3": (42.0, -71.0),
    "City 4": (47.0, -122.0),
    "City 5": (41.0, -88.0),
    "City 6": (25.0, -80.0),
    "City 7": (37.0, -122.0),
    "City 8": (34.0, -118.0),
}
df['lat'] = df['Origin'].map(lambda x: city_coords.get(x, (0, 0))[0])
df['lon'] = df['Origin'].map(lambda x: city_coords.get(x, (0, 0))[1])

# App Setup
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUMEN])
app.title = "Fleet Performance & Revenue Insights"

# Layout
sidebar = dbc.Card(
    [
        html.H5("Filters", className="card-title text-center"),
        dbc.Label("Route", className="text-white"),
        dcc.Dropdown(
            id="route_selector",
            options=[{"label": r, "value": r} for r in sorted(df["Route"].unique())],
            value="All",
            clearable=False,
            placeholder="Select Route",
            className="text-black"
        ),
        dbc.Label("Origin City", className="text-white"),
        dcc.Dropdown(
            id="origin_selector",
            options=[{"label": c, "value": c} for c in sorted(df["Origin"].unique())],
            value="All",
            clearable=False,
            placeholder="Select Origin",
            className="text-black"
        ),
        dbc.Label("Destination City", className="text-white"),
        dcc.Dropdown(
            id="destination_selector",
            options=[{"label": c, "value": c} for c in sorted(df["Destination"].unique())],
            value="All",
            clearable=False,
            placeholder="Select Destination",
            className="text-black"
        ),
        dbc.Label("Departure Hour", className="text-white"),
        dcc.RangeSlider(
            id="time_slider",
            min=0,
            max=23,
            step=1,
            value=[0, 23],
            marks={i: str(i) for i in range(0, 24, 3)},
            className="text-white"
        ),
        html.Button(
            "Play ▶️", 
            id="play_pause", 
            n_clicks=0, 
            className="mt-2 btn btn-primary",
            style={"color": "white"}
        ),
        dcc.Store(id="play_state", data=False),
        dcc.Interval(id="interval", interval=1000, disabled=True),
    ],
    body=True,
    className="h-100",
    style={"background": "rgba(255,255,255,0.1)"},
)

content = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(html.H2("Fleet Performance & Revenue Insights", 
                               className="text-center text-white"), 
                        width=12)
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="choropleth_revenue", 
                                  figure=px.scatter_map(
                                      lat=[0], lon=[0], 
                                      color_continuous_scale=px.colors.sequential.Viridis
                                  ).update_layout(
                                      mapbox_style="carto-darkmatter",
                                      margin=dict(l=0, r=0, t=0, b=0),
                                      paper_bgcolor="rgba(0,0,0,0)",
                                      plot_bgcolor="rgba(0,0,0,0)"
                                  )), width=6),
                dbc.Col(dcc.Graph(id="time_series_revenue", 
                                  figure=px.line(x=[]).update_layout(
                                      paper_bgcolor="rgba(0,0,0,0)",
                                      plot_bgcolor="rgba(0,0,0,0)")
                                  ), width=6)
            ],
            className="mb-4"
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="scatter_3d", 
                                  figure=px.scatter_3d(x=[], y=[], z=[]).update_layout(
                                      paper_bgcolor="rgba(0,0,0,0)",
                                      plot_bgcolor="rgba(0,0,0,0)")
                                  ), width=6),
                dbc.Col(dcc.Graph(id="sankey_routes", 
                                  figure=go.Figure().update_layout(
                                      paper_bgcolor="rgba(0,0,0,0)",
                                      plot_bgcolor="rgba(0,0,0,0)")
                                  ), width=6)
            ],
            className="mb-4"
        ),
        dbc.Row(
            [
                dbc.Col(dash_table.DataTable(
                    id="data_table",
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_header={"backgroundColor": "#374151", "color": "white"},
                    style_cell={"backgroundColor": "#1f2937", "color": "white"},
                ), width=12)
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(id="insights_panel", 
                             className="text-white p-3 p-5"),
                    width=12
                )
            ]
        ),
        dcc.Store(id="filtered-data")
    ],
    style={"background": "rgba(255,255,255,0.1)", "padding": "20px"},
)

app.layout = dbc.Container(
    [
        dcc.Store(id="animation_range", data=[0, 23]),
        dbc.Row(
            [
                dbc.Col(sidebar, width=3, style={"minHeight": "100vh"}),
                dbc.Col(content, width=9),
            ],
            className="g-0",
        ),
    ],
    fluid=True,
)

# Callbacks
@callback(
    Output("play_state", "data"),
    Output("play_pause", "children"),
    Output("interval", "disabled"),
    Input("play_pause", "n_clicks"),
    State("play_state", "data"),
)
def toggle_play(n_clicks, playing):
    if n_clicks is None:
        raise PreventUpdate
    playing = not playing
    label = "Pause ⏸️" if playing else "Play ▶️"
    return playing, label, not playing

@callback(
    Output("time_slider", "value"),
    Input("interval", "n_intervals"),
    State("time_slider", "value"),
    State("play_state", "data"),
)
def advance_time(n_intervals, current_range, playing):
    if not playing:
        raise PreventUpdate
    start, end = current_range
    start = (start + 1) % 24
    end = (end + 1) % 24
    if start > end:
        return [start, 23] if start <= 23 else [0, end]
    return [start, end]

@callback(
    Output("filtered-data", "data"),
    Input("route_selector", "value"),
    Input("origin_selector", "value"),
    Input("destination_selector", "value"),
    Input("time_slider", "value"),
)
def filter_data(route, origin, destination, hour_range):
    d = df.copy()
    if route != "All":
        d = d[d["Route"] == route]
    if origin != "All":
        d = d[d["Origin"] == origin]
    if destination != "All":
        d = d[d["Destination"] == destination]
    d = d[(d["DepHour"] >= hour_range[0]) & (d["DepHour"] <= hour_range[1])]
    if d.empty:
        raise PreventUpdate
    return d.to_dict("records")

@callback(
    Output("choropleth_revenue", "figure"),
    Input("filtered-data", "data"),
)
def update_choropleth(data):
    if not data:
        raise PreventUpdate
    d = pd.DataFrame(data)
    rev = d.groupby("Origin")["Revenue_USD"].mean().reset_index()
    rev["lat"] = rev["Origin"].map(lambda x: city_coords.get(x, (0, 0))[0])
    rev["lon"] = rev["Origin"].map(lambda x: city_coords.get(x, (0, 0))[1])
    fig = px.scatter_map(
        rev,
        lat="lat",
        lon="lon",
        size="Revenue_USD",
        color="Revenue_USD",
        hover_name="Origin",
        color_continuous_scale=px.colors.sequential.Viridis,
        zoom=3,
        height=400,
    )
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

@callback(
    Output("time_series_revenue", "figure"),
    Input("filtered-data", "data"),
)
def update_time_series(data):
    if not data:
        raise PreventUpdate
    d = pd.DataFrame(data)
    hourly = d.groupby("DepHour")["Revenue_USD"].sum().reset_index()
    fig = px.line(hourly, x="DepHour", y="Revenue_USD", markers=True, height=400)
    fig.update_traces(line_color="#f59e0b")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Departure Hour",
        yaxis_title="Revenue (USD)",
        font_color="white"
    )
    return fig

@callback(
    Output("scatter_3d", "figure"),
    Input("filtered-data", "data"),
)
def update_scatter3d(data):
    if not data:
        raise PreventUpdate
    d = pd.DataFrame(data)
    fig = px.scatter_3d(
        d,
        x="Distance_km",
        y="FuelUsed_Liters",
        z="Revenue_USD",
        color="Route",
        size="Passengers",
        height=400,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white"
    )
    return fig

@callback(
    Output("sankey_routes", "figure"),
    Input("filtered-data", "data"),
)
def update_sankey(data):
    if not data:
        raise PreventUpdate
    d = pd.DataFrame(data)
    nodes = list(pd.concat([d["Origin"], d["Destination"]]).unique())
    node_idx = {node: i for i, node in enumerate(nodes)}
    source = d["Origin"].map(node_idx)
    target = d["Destination"].map(node_idx)
    value = d["Passengers"]
    fig = go.Figure(
        data=[go.Sankey(
            node=dict(pad=15, thickness=20,
                      line=dict(color="black", width=0.5),
                      label=nodes,
                      color="#10b981"),
            link=dict(source=source, target=target, value=value)
        )]
    )
    fig.update_layout(
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white"
    )
    return fig

@callback(
    Output("data_table", "data"),
    Input("filtered-data", "data"),
)
def update_table(data):
    if not data:
        raise PreventUpdate
    return data

@callback(
    Output("insights_panel", "children"),
    Input("filtered-data", "data"),
)
def update_insights(data):
    if not data:
        raise PreventUpdate
    d = pd.DataFrame(data)

    top_routes = d.groupby("Route")["Revenue_USD"].sum().nlargest(3).reset_index()
    top_routes_md = html.Ul(
        [html.Li(f"Route {row.Route}: ${row.Revenue_USD:,.0f}") 
         for _, row in top_routes.iterrows()],
        className="text-white"
    )

    peak_hours = d.groupby("DepHour")["Revenue_USD"].sum().nlargest(3).reset_index()
    peak_hours_md = html.Ul(
        [html.Li(f"{int(row.DepHour)}:00 – ${row.Revenue_USD:,.0f}") 
         for _, row in peak_hours.iterrows()],
        className="text-white"
    )

    d["Rev_per_L"] = d["Revenue_USD"] / d["FuelUsed_Liters"]
    fuel_eff = d["Rev_per_L"].mean()
    fuel_md = html.P(
        f"Average revenue per liter of fuel: ${fuel_eff:,.2f}", 
        className="text-white"
    )

    delay_rev = d.groupby("Delay_min")["Revenue_USD"].mean().reset_index()
    delay_fig = px.bar(
        delay_rev, 
        x="Delay_min", 
        y="Revenue_USD", 
        height=200,
        color_discrete_sequence=["#10b981"]
    )
    delay_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        xaxis_title="Delay (minutes)",
        yaxis_title="Average Revenue (USD)"
    )

    return html.Div(
        [
            html.H5("Key Insights", className="text-white mb-3"),
            html.H6("Top Routes by Revenue:", className="text-white"),
            top_routes_md,
            html.H6("Peak Departure Hours:", className="text-white mt-3"),
            peak_hours_md,
            html.H6("Fuel Efficiency:", className="text-white mt-3"),
            fuel_md,
            html.H6("Delay Impact on Revenue:", className="text-white mt-3"),
            dcc.Graph(figure=delay_fig)
        ],
        className="p-3"
    )

if __name__ == "__main__":
    app.run(debug=True)