import os
import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table, Input, Output, State, callback, ctx
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate

# -------------------- Data Loading --------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, "dataset.csv")
df = pd.read_csv(dataset_path)

# -------------------- App Setup --------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
)
app.title = "Patient Health Insights Dashboard"

# -------------------- Layout --------------------
controls = dbc.Card(
    [
        dbc.CardHeader(html.H5("Filters", className="text-white")),
        dbc.CardBody(
            [
                dbc.Label("Gender", className="text-white-50"),
                dcc.Dropdown(
                    id="gender_filter",
                    options=[{"label": "All", "value": "All"}]
                    + [{"label": g, "value": g} for g in sorted(df["Gender"].unique())],
                    value="All",
                    clearable=False,
                    className="mb-3",
                ),
                dbc.Label("Age Range", className="text-white-50"),
                dcc.RangeSlider(
                    id="age_range",
                    min=df["Age"].min(),
                    max=df["Age"].max(),
                    step=1,
                    value=[df["Age"].min(), df["Age"].max()],
                    marks={i: str(i) for i in range(df["Age"].min(), df["Age"].max() + 1, 10)},
                    className="mb-3",
                ),
                dbc.Label("BMI Range", className="text-white-50"),
                dcc.RangeSlider(
                    id="bmi_range",
                    min=df["BMI"].min(),
                    max=df["BMI"].max(),
                    step=0.1,
                    value=[df["BMI"].min(), df["BMI"].max()],
                    marks={i: str(i) for i in range(int(df["BMI"].min()), int(df["BMI"].max()) + 1, 5)},
                    className="mb-3",
                ),
                dbc.Label("Smoking Status", className="text-white-50"),
                dcc.Checklist(
                    id="smoking_filter",
                    options=[
                        {"label": s, "value": s}
                        for s in sorted(df["Smoking_Status"].unique())
                    ],
                    value=sorted(df["Smoking_Status"].unique()),
                    className="mb-3",
                ),
                dbc.Label("Exercise Frequency", className="text-white-50"),
                dcc.Dropdown(
                    id="exercise_filter",
                    options=[{"label": "All", "value": "All"}]
                    + [{"label": e, "value": e} for e in sorted(df["Exercise_Frequency"].unique())],
                    value="All",
                    clearable=False,
                    className="mb-3",
                ),
                dbc.Label("Primary Diagnosis", className="text-white-50"),
                dcc.Dropdown(
                    id="diag_filter",
                    options=[{"label": "All", "value": "All"}]
                    + [{"label": d, "value": d} for d in sorted(df["Primary_Diagnosis"].unique())],
                    value="All",
                    clearable=False,
                ),
            ]
        ),
    ],
    className="h-100",
    style={"height": "auto"},
)

insights = dbc.Card(
    [
        dbc.CardHeader(html.H5("Dynamic Insights", className="text-white")),
        dbc.CardBody(
            html.Div(
                [
                    html.P("Key Trends: Rising hypertension and diabetes prevalence.", className="text-warning"),
                    html.P("Health Metric Correlations: BMI ↔ Blood Pressure.", className="text-warning"),
                    html.P("Lifestyle Impact: Smoking status linked to diagnosis.", className="text-warning"),
                    html.P("Healthcare Utilization: Hospital visits ↑ with hypertension.", className="text-warning"),
                ],
                id="insights_content",
                style={"color": "#f59e0b"},
            )
        ),
    ],
    className="h-100",
    style={"height": "auto"},
)

# Main visualizations
diag_bar = dcc.Graph(id="diag_bar", config={"displayModeBar": False})
bmi_scatter = dcc.Graph(id="bmi_bp_scatter", config={"displayModeBar": False})
exercise_box = dcc.Graph(id="exercise_box", config={"displayModeBar": False})
smoke_sankey = dcc.Graph(id="smoke_sankey", config={"displayModeBar": False})
patient_table = dash_table.DataTable(
    id="patient_table",
    columns=[{"name": c, "id": c} for c in df.columns],
    page_size=10,
    style_table={"overflowX": "auto"},
    style_header={"backgroundColor": "#374151", "fontSize": 14},
    style_cell={"backgroundColor": "#1f2937", "color": "#f9fafb", "fontSize": 12},
    row_selectable="single",
)

layout_main = dbc.Col(
    [
        dbc.Row([dbc.Col(diag_bar, width=6), dbc.Col(bmi_scatter, width=6)]),
        dbc.Row([dbc.Col(exercise_box, width=6), dbc.Col(smoke_sankey, width=6)]),
        dbc.Row(dbc.Col(patient_table, width=12)),
    ],
    width=7,
)

app.layout = dbc.Container(
    [
        dcc.Store(id="filtered-data"),
        dcc.Store(id="selected-diagnosis"),
        dcc.Store(id="selected-sankey"),
        dcc.Store(id="selected-patient"),
        dbc.Row(
            [
                dbc.Col(controls, width=2, style={"background": "#111827", "padding": "20px"}),
                layout_main,
                dbc.Col(insights, width=3, style={"background": "#111827", "padding": "20px"}),
            ],
            style={"minHeight": "100vh"},
        )
    ],
    fluid=True,
    className="bg-dark",
)

# -------------------- Callbacks --------------------
@callback(
    Output("filtered-data", "data"),
    Input("gender_filter", "value"),
    Input("age_range", "value"),
    Input("bmi_range", "value"),
    Input("smoking_filter", "value"),
    Input("exercise_filter", "value"),
    Input("diag_filter", "value"),
)
def filter_data(gender, age_range, bmi_range, smoking, exercise, diagnosis):
    try:
        d = df.copy()
        if gender != "All":
            d = d[d["Gender"] == gender]
        d = d[(d["Age"] >= age_range[0]) & (d["Age"] <= age_range[1])]
        d = d[(d["BMI"] >= bmi_range[0]) & (d["BMI"] <= bmi_range[1])]
        d = d[d["Smoking_Status"].isin(smoking)]
        if exercise != "All":
            d = d[d["Exercise_Frequency"] == exercise]
        if diagnosis != "All":
            d = d[d["Primary_Diagnosis"] == diagnosis]
        return d.to_dict("records")
    except Exception as e:
        print(f"Error in filter_data: {e}")
        raise PreventUpdate

@callback(
    Output("selected-diagnosis", "data"),
    Input("diag_bar", "clickData"),
    State("filtered-data", "data"),
)
def store_selected_diag(click, data):
    try:
        if not click:
            raise PreventUpdate
        diag = click["points"][0]["label"]
        return diag
    except Exception as e:
        print(f"Error in store_selected_diag: {e}")
        raise PreventUpdate

@callback(
    Output("selected-sankey", "data"),
    Input("smoke_sankey", "clickData"),
    State("filtered-data", "data"),
)
def store_selected_sankey(click, data):
    try:
        if not click:
            raise PreventUpdate
        src = click["points"][0]["source"]
        tgt = click["points"][0]["target"]
        src_label = click["points"][0]["label"]
        tgt_label = click["points"][0]["targetLabel"]
        return {"smoking": src_label, "diagnosis": tgt_label}
    except Exception as e:
        print(f"Error in store_selected_sankey: {e}")
        raise PreventUpdate

@callback(
    Output("selected-patient", "data"),
    Input("patient_table", "selected_rows"),
    State("filtered-data", "data"),
)
def store_selected_patient(rows, data):
    try:
        if rows is None or len(rows) == 0:
            raise PreventUpdate
        rec = data[rows[0]]
        return rec["Patient_ID"]
    except Exception as e:
        print(f"Error in store_selected_patient: {e}")
        raise PreventUpdate

@callback(
    Output("diag_bar", "figure"),
    Input("filtered-data", "data"),
    Input("selected-diagnosis", "data"),
)
def update_diag_bar(data, sel_diag):
    try:
        d = pd.DataFrame(data)
        fig = px.bar(
            d["Primary_Diagnosis"].value_counts().reset_index(),
            x="index",
            y="Primary_Diagnosis",
            labels={"index": "Diagnosis", "Primary_Diagnosis": "Count"},
            color_discrete_sequence=["#f59e0b"],
            title="Primary Diagnosis Distribution",
        )
        fig.update_layout(
            clickmode="event+select",
            transition={"duration": 500},
            plot_bgcolor="#1f2937",
            paper_bgcolor="#1f2937",
            font_color="#f9fafb",
            margin=dict(l=20, r=20, t=40, b=20),
        )
        if sel_diag:
            fig.update_traces(
                marker_color=[
                    "#f59e0b" if d == sel_diag else "#4b5563" for d in fig.data[0].x
                ]
            )
        return fig
    except Exception as e:
        print(f"Error in update_diag_bar: {e}")
        raise PreventUpdate

@callback(
    Output("bmi_bp_scatter", "figure"),
    Input("filtered-data", "data"),
    Input("selected-diagnosis", "data"),
    Input("selected-patient", "data"),
)
def update_scatter(data, sel_diag, sel_patient):
    try:
        d = pd.DataFrame(data)
        if sel_diag:
            d = d[d["Primary_Diagnosis"] == sel_diag]
        fig = px.scatter(
            d,
            x="BMI",
            y="Blood_Pressure_Systolic",
            color="Blood_Sugar_Level",
            color_continuous_scale=px.colors.sequential.Inferno,
            labels={
                "BMI": "Body Mass Index",
                "Blood_Pressure_Systolic": "Systolic Blood Pressure",
                "Blood_Sugar_Level": "Blood Sugar Level"
            },
            title="BMI vs. Systolic Blood Pressure",
        )
        fig.update_layout(
            transition={"duration": 500},
            plot_bgcolor="#1f2937",
            paper_bgcolor="#1f2937",
            font_color="#f9fafb",
            margin=dict(l=20, r=20, t=40, b=20),
        )
        if sel_patient:
            mask = d["Patient_ID"] == sel_patient
            fig.add_trace(
                go.Scatter(
                    x=d.loc[mask, "BMI"],
                    y=d.loc[mask, "Blood_Pressure_Systolic"],
                    mode="markers",
                    marker=dict(size=12, color="#f59e0b", line=dict(width=2)),
                    name="Selected Patient",
                )
            )
        return fig
    except Exception as e:
        print(f"Error in update_scatter: {e}")
        raise PreventUpdate

@callback(
    Output("exercise_box", "figure"),
    Input("filtered-data", "data"),
    Input("selected-diagnosis", "data"),
    Input("selected-patient", "data"),
)
def update_box(data, sel_diag, sel_patient):
    try:
        d = pd.DataFrame(data)
        if sel_diag:
            d = d[d["Primary_Diagnosis"] == sel_diag]
        fig = px.box(
            d,
            x="Exercise_Frequency",
            y="BMI",
            points="all",
            color="Exercise_Frequency",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title="BMI Distribution by Exercise Frequency",
        )
        fig.update_layout(
            transition={"duration": 500},
            plot_bgcolor="#1f2937",
            paper_bgcolor="#1f2937",
            font_color="#f9fafb",
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
        )
        if sel_patient:
            patient_row = d[d["Patient_ID"] == sel_patient]
            if not patient_row.empty:
                fig.add_trace(
                    go.Box(
                        x=patient_row["Exercise_Frequency"],
                        y=patient_row["BMI"],
                        marker=dict(color="#f59e0b", size=12),
                        name="Selected Patient",
                        boxpoints="all",
                    )
                )
        return fig
    except Exception as e:
        print(f"Error in update_box: {e}")
        raise PreventUpdate

@callback(
    Output("smoke_sankey", "figure"),
    Input("filtered-data", "data"),
    Input("selected-sankey", "data"),
    Input("selected-patient", "data"),
)
def update_sankey(data, sel_sankey, sel_patient):
    try:
        d = pd.DataFrame(data)
        src = d["Smoking_Status"]
        tgt = d["Primary_Diagnosis"]
        label_list = list(pd.concat([src, tgt]).unique())
        src_idx = src.apply(lambda x: label_list.index(x))
        tgt_idx = tgt.apply(lambda x: label_list.index(x))
        counts = d.groupby(["Smoking_Status", "Primary_Diagnosis"]).size().reset_index(name="count")
        
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=label_list,
                        color="#4b5563",
                    ),
                    link=dict(
                        source=counts["Smoking_Status"].apply(lambda x: label_list.index(x)),
                        target=counts["Primary_Diagnosis"].apply(lambda x: label_list.index(x)),
                        value=counts["count"],
                        color="#f59e0b",
                    ),
                )
            ]
        )
        fig.update_layout(
            title="Smoking Status → Primary Diagnosis",
            transition={"duration": 500},
            plot_bgcolor="#1f2937",
            paper_bgcolor="#1f2937",
            font_color="#f9fafb",
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return fig
    except Exception as e:
        print(f"Error in update_sankey: {e}")
        raise PreventUpdate

@callback(
    Output("patient_table", "data"),
    Input("filtered-data", "data"),
    Input("selected-sankey", "data"),
    Input("selected-patient", "data"),
)
def update_table(data, sel_sankey, sel_patient):
    try:
        d = pd.DataFrame(data)
        return d.to_dict("records")
    except Exception as e:
        print(f"Error in update_table: {e}")
        raise PreventUpdate

# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(debug=True)