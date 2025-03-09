# pages/stream_reports.py
from dash import html, dcc

layout = html.Div([
    html.H1("Stream-Wise Reports"),
    dcc.Graph(id="stream-graph")
])
