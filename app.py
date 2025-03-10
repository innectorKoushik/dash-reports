import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import os

# Importing page modules
from pages import home, caller_reports, group_reports, district_reports, source_reports, course_reports

# Initialize Dash app with DARKLY theme
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

home.register_callbacks(app)
caller_reports.register_callbacks(app)
group_reports.register_callbacks(app)
district_reports.register_callbacks(app)
source_reports.register_callbacks(app)

# Sidebar Navigation (Collapsible for Mobile)
sidebar_content = dbc.Nav(
    [
        html.H2("Reports Links", className="text-white"),
        dbc.NavLink("Home", href="/", active="exact", className="text-white"),
        dbc.NavLink("Caller Reports", href="/caller-reports", active="exact", className="text-white"),
        dbc.NavLink("Group Reports", href="/group-reports", active="exact", className="text-white"),
        dbc.NavLink("District Reports", href="/district-reports", active="exact", className="text-white"),
        dbc.NavLink("Source Reports", href="/source-reports", active="exact", className="text-white"),
        dbc.NavLink("Course Reports", href="/course-reports", active="exact", className="text-white"),
    ],
    vertical=True,
    pills=True,
)

# Offcanvas Sidebar (for mobile)
sidebar = dbc.Offcanvas(
    sidebar_content,
    id="sidebar",
    title="Navigation",
    is_open=False,
    className="bg-dark",
)

# Toggle Sidebar Button
toggle_button = dbc.Button("☰ Menu", id="toggle-sidebar", n_clicks=0, color="primary", className="mb-2 d-md-none")

# Layout
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='processed-data-store'),

    # Sidebar Toggle Button (only visible on mobile)
    dbc.Row([dbc.Col(toggle_button, width="auto")], className="mb-2"),

    sidebar,  # Mobile Sidebar

    dbc.Row([
        # Desktop Sidebar (hidden on mobile)
        dbc.Col(sidebar_content, width=2, className="bg-secondary d-none d-md-block vh-100"),  

        # Main Content
        dbc.Col(html.Div(id='page-content', className="p-3"), width=12, md=10)
    ], className="g-0"),  # Remove row gap
], fluid=True, className="bg-dark text-white vh-100")

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

# Callback to toggle sidebar on mobile
@app.callback(
    Output("sidebar", "is_open"),
    Input("toggle-sidebar", "n_clicks"),
    State("sidebar", "is_open")
)
def toggle_sidebar(n, is_open):
    if n:
        return not is_open
    return is_open

if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
