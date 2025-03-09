import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import os

# Importing page modules
from pages import home, caller_reports, group_reports, district_reports, source_reports, course_reports


# Initialize Dash app with a dark theme
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

home.register_callbacks(app)
caller_reports.register_callbacks(app)
group_reports.register_callbacks(app)
district_reports.register_callbacks(app)
source_reports.register_callbacks(app)

# Sidebar navigation
sidebar = dbc.Nav(
    [
        html.H2("Reports Links"),
        dbc.NavLink("Home", href="/", active="exact"),
        dbc.NavLink("Caller Reports", href="/caller-reports", active="exact"),
        dbc.NavLink("Group Reports", href="/group-reports", active="exact"),
        dbc.NavLink("District Reports", href="/district-reports", active="exact"),
        dbc.NavLink("Source Reports", href="/source-reports", active="exact"),
        dbc.NavLink("Course Reports", href="/course-reports", active="exact"),
    ],
    vertical=True,
    pills=True,
    className="bg-dark text-white p-3",
)

# Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='processed-data-store'), 
    dbc.Row([
        dbc.Col(sidebar, width=2, className="bg-secondary"),
        dbc.Col(html.Div(id='page-content'), width=10)
    ])
], className="bg-dark text-white vh-100")

# Callback to update page content
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/caller-reports':
        return caller_reports.layout
    elif pathname == '/group-reports':
        return group_reports.layout
    elif pathname == '/district-reports':
        return district_reports.layout
    elif pathname == '/source-reports':
        return source_reports.layout
    elif pathname == '/course-reports':
        return course_reports.layout
    else:
        return home.layout

if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

