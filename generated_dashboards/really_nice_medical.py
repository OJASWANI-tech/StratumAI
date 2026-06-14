import os
import json
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, callback, ctx
import plotly.express as px
from dash.exceptions import PreventUpdate

# --------------------------- Data Loading ---------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, "dataset.csv")
df = pd.read_csv(dataset_path)

# Ensure proper dtypes
df["Age"] = df["Age"].astype(int)
df["BMI"] = df["BMI"].astype(float)
df["Blood_Pressure_Systolic"] = df["Blood_Pressure_Systolic"].astype(int)
df["Blood_Pressure_Diastolic"] = df["Blood_Pressure_Diastolic"].astype(int)
df["Blood_Sugar_Level"] = df["Blood_Sugar_Level"].astype(float)
df["Heart_Rate"] = df["Heart_Rate"].astype(int)
df["Hospital_Visits_Last_Year"] = df["Hospital_Visits_Last_Year"].astype(int)
df["Medication_Count"] = df["Medication_Count"].astype(int)

# --------------------------- App Setup ---------------------------
external_stylesheets = [dbc.themes.DARKLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Patient Health Insights Dashboard"

# --------------------------- Controls ---------------------------
primary_diag_options = ["All", "Healthy", "Obesity", "Hypertension", "Heart Disease", "Diabetes"]
gender_options = ["All", "Male", "Female"]
smoking_options = ["All", "Current Smoker", "Former Smoker", "Non-smoker"]
exercise_options = ["All", "Daily", "1-2 times/week", "3-5 times/week", "Never"]

age_min, age_max = df["Age"].min(), df["Age"].max()
bmi_min, bmi_max = df["BMI"].min(), df["BMI"].max()

controls = dbc.Card(
    [
        dbc.CardHeader(html.H5("Filters")),
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Dropdown(
                                id="primary_diag_dropdown",
                                options=[{"label": v, "value": v} for v in primary_diag_options],
                                value="All",
                                clearable=False,
                            ),
                            width=12,
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="gender_dropdown",
                                options=[{"label": v, "value": v} for v in gender_options],
                                value="All",
                                clearable=False,
                            ),
                            width=12,
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="smoking_status_dropdown",
                                options=[{"label": v, "value": v} for v in smoking_options],
                                value="All",
                                clearable=False,
                            ),
                            width=12,
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="exercise_freq_dropdown",
                                options=[{"label": v, "value": v} for v in exercise_options],
                                value="All",
                                clearable=False,
                            ),
                            width=12,
                        ),
                        dbc.Col(
                            dcc.RangeSlider(
                                id="age_range_slider",
                                min=age_min,
                                max=age_max,
                                step=1,
                                value=[age_min, age_max],
                                marks={int(age_min): str(age_min), int(age_max): str(age_max)},
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                            width=12,
                            className="mt-3",
                        ),
                        dbc.Col(
                            dcc.RangeSlider(
                                id="bmi_range_slider",
                                min=bmi_min,
                                max=bmi_max,
                                step=0.1,
                                value=[bmi_min, bmi_max],
                                marks={float(bmi_min): f"{bmi_min:.1f}", float(bmi_max): f"{bmi_max:.1f}"},
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                            width=12,
                            className="mt-3",
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Play",
                                id="play_pause_button",
                                color="primary",
                                className="mt-3",
                                n_clicks=0,
                            ),
                            width=12,
                        ),
                    ]
                )
            ]
        ),
    ],
    className="h-100",
)

# --------------------------- Plots ---------------------------
def empty_fig():
    return {"layout": {"paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)"}}

bmi_hist = dcc.Graph(id="bmi_hist", config={"displayModeBar": False})
bp_scatter = dcc.Graph(id="bp_scatter", config={"displayModeBar": False})
smoking_box = dcc.Graph(id="smoking_bmi_box", config={"displayModeBar": False})
med_visits_scatter = dcc.Graph(id="med_visits_scatter", config={"displayModeBar": False})

# --------------------------- Data Table ---------------------------
patient_table = dash_table.DataTable(
    id="patient_table",
    columns=[{"name": c.replace("_", " "), "id": c} for c in df.columns],
    page_size=10,
    style_table={"overflowX": "auto"},
    style_header={"backgroundColor": "#2c3e50"},
    style_cell={"backgroundColor": "#34495e", "color": "#ecf0f1"},
    sort_action="native",
    filter_action="native",
    row_selectable="single",
)

# --------------------------- Insights Panel ---------------------------
insights_panel = dbc.Card(
    [
        dbc.CardHeader(html.H5("Dynamic Insights")),
        dbc.CardBody(html.Div(id="insights_content")),
    ],
    className="mt-3",
)

# --------------------------- Layout ---------------------------
app.layout = dbc.Container(
    [
        dcc.Store(id="filtered-data"),
        dcc.Interval(id="animation-interval", interval=1500, n_intervals=0, disabled=True),
        dbc.Row(
            [
                dbc.Col(controls, width=3, style={"background": "linear-gradient(135deg, #111 0%, #222 100%)"}),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(bmi_hist, width=12),
                                dbc.Col(bp_scatter, width=12),
                            ],
                            className="g-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(smoking_box, width=12),
                                dbc.Col(med_visits_scatter, width=12),
                            ],
                            className="g-3 mt-3",
                        ),
                    ],
                    width=6,
                ),
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(patient_table, width=12),
                            ],
                            className="g-3 mt-3",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(insights_panel, width=12),
                            ],
                            className="g-3 mt-3",
                        ),
                    ],
                    width=3,
                ),
            ],
            className="g-0",
        ),
    ],
    fluid=True,
    className="bg-dark text-light",
)

# --------------------------- Callbacks ---------------------------
@callback(
    Output("filtered-data", "data"),
    Input("primary_diag_dropdown", "value"),
    Input("gender_dropdown", "value"),
    Input("smoking_status_dropdown", "value"),
    Input("exercise_freq_dropdown", "value"),
    Input("age_range_slider", "value"),
    Input("bmi_range_slider", "value"),
    Input("animation-interval", "n_intervals"),
    State("play_pause_button", "children"),
)
def filter_dataset(
    primary_diag,
    gender,
    smoking,
    exercise,
    age_range,
    bmi_range,
    n_intervals,
    play_state,
):
    dff = df.copy()
    if primary_diag != "All":
        dff = dff[dff["Primary_Diagnosis"] == primary_diag]
    if gender != "All":
        dff = dff[dff["Gender"] == gender]
    if smoking != "All":
        dff = dff[dff["Smoking_Status"] == smoking]
    if exercise != "All":
        dff = dff[dff["Exercise_Frequency"] == exercise]
    dff = dff[(dff["Age"] >= age_range[0]) & (dff["Age"] <= age_range[1])]
    dff = dff[(dff["BMI"] >= bmi_range[0]) & (dff["BMI"] <= bmi_range[1])]

    # Animation: cycle through patient IDs when playing
    if play_state == "Pause":
        return dff.to_dict("records")
    if not dff.empty:
        patient_ids = dff["Patient_ID"].tolist()
        idx = n_intervals % len(patient_ids)
        dff = dff[dff["Patient_ID"] == patient_ids[idx]]
    return dff.to_dict("records")


@callback(Output("bmi_hist", "figure"), Input("filtered-data", "data"))
def update_bmi_hist(data):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    fig = px.violin(
        dff,
        y="BMI",
        color="Primary_Diagnosis",
        box=True,
        points="all",
        title="BMI Distribution by Diagnosis",
        color_discrete_sequence=app.colors if hasattr(app, "colors") else None,
    )
    fig.update_layout(transition_duration=500, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


@callback(Output("bp_scatter", "figure"), Input("filtered-data", "data"))
def update_bp_scatter(data):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    fig = px.scatter(
        dff,
        x="Blood_Pressure_Systolic",
        y="Blood_Pressure_Diastolic",
        size="BMI",
        color="Primary_Diagnosis",
        title="Blood Pressure (Systolic vs Diastolic)",
        hover_data=["Patient_ID"],
        color_discrete_sequence=app.colors if hasattr(app, "colors") else None,
    )
    fig.update_layout(transition_duration=500, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


@callback(Output("smoking_bmi_box", "figure"), Input("filtered-data", "data"))
def update_smoking_box(data):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    fig = px.box(
        dff,
        x="Smoking_Status",
        y="BMI",
        color="Smoking_Status",
        title="BMI by Smoking Status",
        color_discrete_sequence=app.colors if hasattr(app, "colors") else None,
    )
    fig.update_layout(transition_duration=500, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


@callback(Output("med_visits_scatter", "figure"), Input("filtered-data", "data"))
def update_med_visits_scatter(data):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    fig = px.scatter(
        dff,
        x="Hospital_Visits_Last_Year",
        y="Medication_Count",
        color="Primary_Diagnosis",
        title="Medication Count vs Hospital Visits",
        hover_data=["Patient_ID"],
        color_discrete_sequence=app.colors if hasattr(app, "colors") else None,
    )
    fig.update_layout(transition_duration=500, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    return fig


@callback(Output("patient_table", "data"), Input("filtered-data", "data"))
def update_table(data):
    if not data:
        raise PreventUpdate
    return data


@callback(Output("insights_content", "children"), Input("filtered-data", "data"))
def update_insights(data):
    if not data:
        raise PreventUpdate
    dff = pd.DataFrame(data)
    total = len(dff)
    avg_age = dff["Age"].mean() if total else 0
    avg_bmi = dff["BMI"].mean() if total else 0
    diag_counts = dff["Primary_Diagnosis"].value_counts().to_dict()
    smoking_counts = dff["Smoking_Status"].value_counts().to_dict()
    insights = [
        html.P(f"Total patients in view: {total}"),
        html.P(f"Average Age: {avg_age:.1f} years"),
        html.P(f"Average BMI: {avg_bmi:.1f}"),
        html.H6("Diagnosis distribution:"),
        html.Ul([html.Li(f"{k}: {v}") for k, v in diag_counts.items()]),
        html.H6("Smoking status distribution:"),
        html.Ul([html.Li(f"{k}: {v}") for k, v in smoking_counts.items()]),
    ]
    return insights


@callback(
    Output("play_pause_button", "children"),
    Output("animation-interval", "disabled"),
    Input("play_pause_button", "n_clicks"),
    State("play_pause_button", "children"),
    State("animation-interval", "disabled"),
)
def toggle_animation(n_clicks, current_label, interval_disabled):
    if n_clicks is None:
        raise PreventUpdate
    if current_label == "Play":
        return "Pause", False
    return "Play", True


# --------------------------- Color Scheme ---------------------------
app.colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

# --------------------------- Main ---------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8050"))
    app.run(host="0.0.0.0", port=port, debug=False)