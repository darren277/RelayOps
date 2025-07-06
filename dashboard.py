"""
Dash dashboard for ContextRelay / InterOpSight
Mounts at /dashboard/ on the existing Flask server.
"""

import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import datetime as dt


# ------------------------------------------------
# Dummy-data loaders – swap with real queries
# ------------------------------------------------
def load_github_issues():
    return [
        {"id": 101, "title": "Memory leak in worker", "state": "open",
         "labels": "bug", "updated": "2025-06-12 14:20"},
    ]

def load_sentry_issues():
    return [
        {"id": "SEN-55", "event": "UnhandledPromiseRejection",
         "env": "prod", "users": 7, "last_seen": "2025-06-13 02:03"},
    ]

def load_openproject_issues():
    return [
        {"id": 2315, "subject": "Payment portal 500", "priority": "High",
         "status": "New", "updated": "2025-06-12 23:48"},
    ]


def to_df(loader):
    return pd.DataFrame(loader())


# ------------------------------------------------
# Layout
# ------------------------------------------------
layouts = []

operational_issues_dashboard = html.Div(
    [
        html.H2("Operational Issue Dashboard", className="mt-4 mb-2"),
        dcc.Tabs(
            id="source-tabs",
            value="github",
            children=[
                dcc.Tab(label="GitHub", value="github"),
                dcc.Tab(label="Sentry", value="sentry"),
                dcc.Tab(label="OpenProject", value="openproject"),
            ],
        ),
        html.Div(id="table-container", className="mt-3"),
        # Poll every 60 s; adjust as needed
        dcc.Interval(id="refresh-interval", interval=60_000, n_intervals=0),
        html.Footer(
            f"Last refresh: {dt.datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC",
            id="last-refresh",
            className="text-muted mt-4",
        ),
    ],
    className="p-4",
)

layouts.append(operational_issues_dashboard)

# ------------------------------------------------
# Callbacks
# ------------------------------------------------
callbacks = []

callback1_decorator = (
    Output("table-container", "children"),
    Output("last-refresh", "children"),
    Input("source-tabs", "value"),
    Input("refresh-interval", "n_intervals"),
)

def update_table(selected_tab, _):
    loaders = {
        "github": load_github_issues,
        "sentry": load_sentry_issues,
        "openproject": load_openproject_issues,
    }
    df = to_df(loaders[selected_tab]())

    table = dash_table.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": c.capitalize(), "id": c} for c in df.columns],
        style_table={"overflowX": "auto"},
        style_cell={"padding": "4px 8px", "textAlign": "left"},
        style_header={"fontWeight": "bold"},
        page_size=10,
    )
    timestamp = f"Last refresh: {dt.datetime.utcnow():%Y-%m-%d %H:%M:%S} UTC"
    return table, timestamp


def create_dash_app(flask_app):
    dash_app = dash.Dash(
        __name__,
        server=flask_app,
        url_base_pathname='/dashboard/',
        title="RelayOps: Ops Dashboard",
        update_title=None,        # no "Updating..." banner
    )
    
    return dash_app

def register_dash_app(flask_app):
    dash_app = create_dash_app(flask_app)
    for layout in layouts:
        dash_app.layout = layout
    for callback in callbacks:
        dash_app.callback(*callback1_decorator)(update_table)
    return dash_app

