import os
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, dash_table, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate

# -------------------- Data Loading --------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, "dataset.csv")
df = pd.read_csv(dataset_path)

# -------------------- Pre‑processing --------------------
df["Year"] = df["Year"].astype(int)
year_min, year_max = df["Year"].min(), df["Year"].max()
countries = ["All"] + sorted(df["Country"].unique())
crops = ["All"] + sorted(df["Crop"].unique())

color_maps = {
    "Blue": "#1f77b4",
    "Orange": "#ff7f0e",
    "Green": "#2ca02c",
    "Red": "#d62728",
    "Purple": "#9467bd",
}

# -------------------- App Setup --------------------
external_stylesheets = [dbc.themes.DARKLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Agri‑Climate Nexus Dashboard"
# -------------------------------------------------

# -------------------- Layout --------------------
controls = dbc.Row(
    [
        dbc.Col(
            dcc.Dropdown(
                id="country_selector",
                options=[{"label": c, "value": c} for c in countries],
                value="All",
                clearable=False,
                style={"color": "black"},
            ),
            md=3,
        ),
        dbc.Col(
            dcc.Dropdown(
                id="crop_selector",
                options=[{"label": c, "value": c} for c in crops],
                value="All",
                clearable=False,
                style={"color": "black"},
            ),
            md=3,
        ),
        dbc.Col(
            dcc.Slider(
                id="year_slider",
                min=year_min,
                max=year_max,
                step=1,
                value=year_min,
                marks={y: str(y) for y in range(year_min, year_max + 1, 2)},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
            md=4,
        ),
        dbc.Col(
            html.Button("▶️", id="play_pause_button", n_clicks=0, style={"fontSize": "1.2rem"}),
            md=1,
        ),
        dbc.Col(
            dcc.Dropdown(
                id="color_scheme_selector",
                options=[{"label": k, "value": k} for k in color_maps.keys()],
                value="Blue",
                clearable=False,
                style={"color": "black"},
            ),
            md=2,
        ),
    ],
    className="g-2 mb-3",
)

insights_panel = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Dynamic Insights", className="card-title"),
            html.Div(id="insights_content", style={"whiteSpace": "pre-line", "color": "white"}),
        ]
    ),
    className="mb-3",
)

# Empty figures placeholders
empty_fig = go.Figure()
empty_fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=30, b=0),
)

layout = dbc.Container(
    [
        html.H2("Agri‑Climate Nexus Dashboard", className="text-center my-4", style={"color": "white"}),
        controls,
        insights_panel,
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="choropleth_export", figure=empty_fig), md=6),
                dbc.Col(dcc.Graph(id="time_series_yield", figure=empty_fig), md=6),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id="scatter_temp_rain", figure=empty_fig), md=6),
                dbc.Col(
                    dash_table.DataTable(
                        id="data_table",
                        page_size=10,
                        style_table={"overflowX": "auto"},
                        style_header={"backgroundColor": "#2c2f33", "color": "white"},
                        style_cell={"backgroundColor": "#1e2125", "color": "white"},
                    ),
                    md=6,
                ),
            ],
            className="mb-4",
        ),
        dcc.Store(id="filtered_data"),
        dcc.Store(id="animation_state", data=False),
        dcc.Interval(id="interval_component", interval=2000, n_intervals=0, disabled=True),
    ],
    fluid=True,
    style={"background": "linear-gradient(135deg, #0d1117, #1e1e1e)", "minHeight": "100vh", "color": "white"},
)

app.layout = layout

# -------------------- Callbacks --------------------
@callback(
    Output("animation_state", "data"),
    Output("interval_component", "disabled"),
    Input("play_pause_button", "n_clicks"),
    State("animation_state", "data"),
)
def toggle_animation(n_clicks, playing):
    if n_clicks is None:
        raise PreventUpdate
    playing = not playing
    return playing, not playing

@callback(
    Output("year_slider", "value"),
    Input("interval_component", "n_intervals"),
    State("year_slider", "value"),
    State("animation_state", "data"),
)
def animate_year(_n, current_year, playing):
    if not playing:
        raise PreventUpdate
    next_year = current_year + 1
    if next_year > year_max:
        next_year = year_min
    return next_year

@callback(
    Output("filtered_data", "data"),
    Input("country_selector", "value"),
    Input("crop_selector", "value"),
    Input("year_slider", "value"),
)
def filter_dataset(selected_country, selected_crop, selected_year):
    dff = df.copy()
    if selected_country != "All":
        dff = dff[dff["Country"] == selected_country]
    if selected_crop != "All":
        dff = dff[dff["Crop"] == selected_crop]
    dff = dff[dff["Year"] == selected_year]
    if dff.empty:
        raise PreventUpdate
    return dff.to_dict("records")

@callback(
    Output("choropleth_export", "figure"),
    Input("filtered_data", "data"),
    Input("color_scheme_selector", "value"),
)
def update_choropleth(data, scheme):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    fig = px.choropleth(
        dff,
        locations="Country",
        locationmode="country names",
        color="Export_Value_USD_million",
        hover_name="Country",
        color_continuous_scale=px.colors.sequential.Blues,
        title="Export Value by Country",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0),
        coloraxis_colorbar=dict(title=dict(text="USD million", side="top")),
    )
    fig.update_traces(
        marker_line_width=0.5,
        marker_line_color="white",
        selector=dict(type="choropleth"),
    )
    return fig

@callback(
    Output("time_series_yield", "figure"),
    Input("country_selector", "value"),
    Input("crop_selector", "value"),
    Input("color_scheme_selector", "value"),
)
def update_time_series(selected_country, selected_crop, scheme):
    dff = df.copy()
    if selected_country != "All":
        dff = dff[dff["Country"] == selected_country]
    if selected_crop != "All":
        dff = dff[dff["Crop"] == selected_crop]
    if dff.empty:
        raise PreventUpdate
    agg = dff.groupby("Year")["Yield_tons_per_hectare"].mean().reset_index()
    fig = px.line(
        agg,
        x="Year",
        y="Yield_tons_per_hectare",
        title="Crop Yield Over Time",
        color_discrete_sequence=[color_maps[scheme]],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Year",
        yaxis_title="Yield (tons/ha)",
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig

@callback(
    Output("scatter_temp_rain", "figure"),
    Input("filtered_data", "data"),
    Input("color_scheme_selector", "value"),
)
def update_scatter(data, scheme):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    fig = px.scatter(
        dff,
        x="Avg_Temperature_C",
        y="Rainfall_mm",
        size="Yield_tons_per_hectare",
        color="Yield_tons_per_hectare",
        color_continuous_scale=px.colors.sequential.Blues,
        title="Temperature vs Rainfall Impact",
        labels={
            "Avg_Temperature_C": "Average Temperature (°C)",
            "Rainfall_mm": "Rainfall (mm)",
            "Yield_tons_per_hectare": "Yield",
        },
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig

@callback(
    Output("data_table", "data"),
    Output("data_table", "columns"),
    Input("filtered_data", "data"),
)
def update_table(data):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    columns = [{"name": col, "id": col, "presentation": "markdown"} for col in dff.columns]
    return dff.to_dict("records"), columns

@callback(
    Output("insights_content", "children"),
    Input("filtered_data", "data"),
)
def update_insights(data):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    avg_temp = dff["Avg_Temperature_C"].mean()
    avg_rain = dff["Rainfall_mm"].mean()
    avg_yield = dff["Yield_tons_per_hectare"].mean()
    avg_export = dff["Export_Value_USD_million"].mean()
    insight = (
        f"🌡️ Average Temperature: {avg_temp:.2f}°C\n"
        f"☔ Average Rainfall: {avg_rain:.1f} mm\n"
        f"🚜 Average Yield: {avg_yield:.2f} tons/ha\n"
        f"💰 Average Export Value: {avg_export:,.0f} USD million"
    )
    return insight

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)