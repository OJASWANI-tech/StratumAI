import os
import pandas as pd
import numpy as np
import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, dash_table, Input, Output, State, callback
from dash.exceptions import PreventUpdate

# --------------------------- Data Loading ---------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, 'dataset.csv')
df = pd.read_csv(dataset_path)

# --------------------------- App Setup ---------------------------
base_path = os.getenv('BASE_PATH', '/')
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    requests_pathname_prefix=base_path,
    routes_pathname_prefix=base_path,
)
app.title = "Patient Health Insights Dashboard"

# --------------------------- Controls ---------------------------
gender_options = ["All", "Male", "Female"]
smoking_options = ["All", "Current Smoker", "Former Smoker", "Non-smoker"]
exercise_options = ["All", "Daily", "1-2 times/week", "3-5 times/week", "Never"]
diagnosis_options = ["All", "Healthy", "Obesity", "Hypertension", "Heart Disease", "Diabetes"]

controls = dbc.Card(
    [
        dbc.CardHeader(html.H5("Filters")),
        dbc.CardBody(
            [
                dbc.Label("Gender"),
                dcc.Dropdown(
                    id="ctrl_gender",
                    options=[{"label": i, "value": i} for i in gender_options],
                    value="All",
                    clearable=False,
                ),
                dbc.Label("Age Range", className="mt-3"),
                dcc.RangeSlider(
                    id="ctrl_age_range",
                    min=int(df["Age"].min()),
                    max=int(df["Age"].max()),
                    step=1,
                    value=[int(df["Age"].min()), int(df["Age"].max())],
                    marks={i: str(i) for i in range(int(df["Age"].min()), int(df["Age"].max()) + 1, 10)},
                ),
                dbc.Label("Smoking Status", className="mt-3"),
                dcc.Dropdown(
                    id="ctrl_smoking",
                    options=[{"label": i, "value": i} for i in smoking_options],
                    value="All",
                    clearable=False,
                ),
                dbc.Label("Exercise Frequency", className="mt-3"),
                dcc.Dropdown(
                    id="ctrl_exercise",
                    options=[{"label": i, "value": i} for i in exercise_options],
                    value="All",
                    clearable=False,
                ),
                dbc.Label("Primary Diagnosis", className="mt-3"),
                dcc.Dropdown(
                    id="ctrl_diagnosis",
                    options=[{"label": i, "value": i} for i in diagnosis_options],
                    value="All",
                    clearable=False,
                ),
                dbc.Label("Medication Count", className="mt-3"),
                dcc.RangeSlider(
                    id="ctrl_med_count",
                    min=int(df["Medication_Count"].min()),
                    max=int(df["Medication_Count"].max()),
                    step=1,
                    value=[int(df["Medication_Count"].min()), int(df["Medication_Count"].max())],
                    marks={i: str(i) for i in range(int(df["Medication_Count"].min()), int(df["Medication_Count"].max()) + 1)},
                ),
                dbc.Button("Play/Pause", id="ctrl_play_pause", color="secondary", className="mt-3"),
            ]
        ),
    ],
    className="mb-4",
)

# --------------------------- Layout ---------------------------
app.layout = dbc.Container(
    [
        dcc.Store(id="filtered-data"),
        html.H2("Patient Health Insights Dashboard", className="text-center my-4"),
        dbc.Row(
            [
                dbc.Col(controls, width=3),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(id="plot_cholesterol_bar"), width=6),
                                dbc.Col(dcc.Graph(id="plot_bmi_hist"), width=6),
                            ],
                            className="mb-4",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(id="plot_bp_scatter"), width=6),
                                dbc.Col(dcc.Graph(id="plot_diagnosis_sankey"), width=6),
                            ],
                            className="mb-4",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dash_table.DataTable(
                                        id="plot_patient_table",
                                        columns=[{"name": c, "id": c} for c in df.columns],
                                        page_size=10,
                                        style_table={"overflowX": "auto"},
                                        style_header={"backgroundColor": "#2c3e50"},
                                        style_cell={"backgroundColor": "#34495e", "color": "#ecf0f1"},
                                        filter_action="native",
                                        sort_action="native",
                                        row_selectable="single",
                                    ),
                                    width=12,
                                )
                            ],
                            className="mb-4",
                        ),
                        dbc.Card(
                            [
                                dbc.CardHeader(html.H5("Dynamic Insights")),
                                dbc.CardBody(html.Div(id="insights_panel")),
                            ],
                            className="mt-3",
                        ),
                    ],
                    width=9,
                ),
            ]
        ),
    ],
    fluid=True,
    className="p-4",
    style={"background": "linear-gradient(135deg, #111 0%, #222 100%)"},
)

# --------------------------- Callbacks ---------------------------

@callback(
    Output("filtered-data", "data"),
    Input("ctrl_gender", "value"),
    Input("ctrl_age_range", "value"),
    Input("ctrl_smoking", "value"),
    Input("ctrl_exercise", "value"),
    Input("ctrl_diagnosis", "value"),
    Input("ctrl_med_count", "value"),
)
def filter_dataset(gender, age_range, smoking, exercise, diagnosis, med_range):
    dff = df.copy()
    if gender != "All":
        dff = dff[dff["Gender"] == gender]
    dff = dff[(dff["Age"] >= age_range[0]) & (dff["Age"] <= age_range[1])]
    if smoking != "All":
        dff = dff[dff["Smoking_Status"] == smoking]
    if exercise != "All":
        dff = dff[dff["Exercise_Frequency"] == exercise]
    if diagnosis != "All":
        dff = dff[dff["Primary_Diagnosis"] == diagnosis]
    dff = dff[(dff["Medication_Count"] >= med_range[0]) & (dff["Medication_Count"] <= med_range[1])]
    return dff.to_dict("records")


def get_filtered_df(data):
    if not data:
        raise PreventUpdate
    return pd.DataFrame(data)


@callback(
    Output("plot_bmi_hist", "figure"),
    Input("filtered-data", "data"),
)
def update_bmi_hist(data):
    dff = get_filtered_df(data)
    fig = px.histogram(
        dff,
        x="BMI",
        nbins=30,
        title="BMI Distribution",
        color_discrete_sequence=["#1f77b4"],
        template="plotly_dark",
    )
    fig.update_layout(transition_duration=500)
    return fig


@callback(
    Output("plot_cholesterol_bar", "figure"),
    Input("filtered-data", "data"),
)
def update_chol_bar(data):
    dff = get_filtered_df(data)
    agg = (
        dff.groupby(["Primary_Diagnosis", "Cholesterol"])
        .size()
        .reset_index(name="Count")
    )
    fig = px.bar(
        agg,
        x="Primary_Diagnosis",
        y="Count",
        color="Cholesterol",
        barmode="group",
        title="Cholesterol Levels by Diagnosis",
        color_discrete_sequence=px.colors.qualitative.Dark24,
        template="plotly_dark",
    )
    fig.update_layout(transition_duration=500)
    return fig


@callback(
    Output("plot_bp_scatter", "figure"),
    Input("filtered-data", "data"),
)
def update_bp_scatter(data):
    dff = get_filtered_df(data)
    fig = px.scatter_3d(
        dff,
        x="Age",
        y="BMI",
        z="Blood_Pressure_Systolic",
        color="Primary_Diagnosis",
        size="Blood_Pressure_Diastolic",
        title="Blood Pressure vs Age vs BMI",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Dark2,
    )
    fig.update_layout(transition_duration=500)
    return fig


@callback(
    Output("plot_diagnosis_sankey", "figure"),
    Input("filtered-data", "data"),
)
def update_sankey(data):
    dff = get_filtered_df(data)
    if dff.empty:
        raise PreventUpdate
    src = dff["Primary_Diagnosis"]
    tgt = dff["Medication_Count"].astype(str)
    all_nodes = pd.concat([src, tgt]).unique()
    node_map = {k: i for i, k in enumerate(all_nodes)}
    links = (
        dff.groupby([src, tgt])
        .size()
        .reset_index(name="value")
        .assign(
            source=lambda x: x[src.name].map(node_map),
            target=lambda x: x[tgt.name].map(node_map),
        )
    )
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=all_nodes,
                    color=px.colors.qualitative.Dark24[: len(all_nodes)],
                ),
                link=dict(
                    source=links["source"],
                    target=links["target"],
                    value=links["value"],
                ),
            )
        ]
    )
    fig.update_layout(
        title_text="Diagnosis Flow to Medication Count",
        font=dict(size=10),
        template="plotly_dark",
        transition_duration=500,
    )
    return fig


@callback(
    Output("plot_patient_table", "data"),
    Input("filtered-data", "data"),
)
def update_table(data):
    dff = get_filtered_df(data)
    return dff.to_dict("records")


@callback(
    Output("insights_panel", "children"),
    Input("filtered-data", "data"),
)
def update_insights(data):
    dff = get_filtered_df(data)
    total = len(dff)
    if total == 0:
        return html.P("No records match the current filters.", className="text-warning")
    avg_bmi = dff["BMI"].mean()
    high_bp = (dff["Blood_Pressure_Systolic"] > 140).mean() * 100
    smoking_rate = (dff["Smoking_Status"] == "Current Smoker").mean() * 100
    insights = [
        html.P(f"Total patients displayed: {total}"),
        html.P(f"Average BMI: {avg_bmi:.2f}"),
        html.P(f"Percentage with high systolic BP (>140): {high_bp:.1f}%"),
        html.P(f"Current smokers in view: {smoking_rate:.1f}%"),
    ]
    return insights


@callback(
    Output("ctrl_play_pause", "children"),
    Input("ctrl_play_pause", "n_clicks"),
    State("ctrl_play_pause", "children"),
)
def toggle_play_pause(n, current):
    if not n:
        raise PreventUpdate
    return "Pause" if current == "Play" else "Play"


# --------------------------- Main ---------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8050"))
    app.run(host="0.0.0.0", port=port, debug=False)