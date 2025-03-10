import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A3
import os
from flask import send_file

# Layout
layout = html.Div([
    dcc.Store(id='processed-data-store'),
    html.H2("District Reports", className="text-center text-white"),
    
    # Filters Section
    dbc.Container([
        dbc.Row([
            dbc.Col(dcc.Dropdown(id='district-group-filter', multi=True, placeholder="Select Group"), xs=12, sm=6, md=3),
            dbc.Col(dcc.Dropdown(id='district-owner-filter', multi=True, placeholder="Select Owner"), xs=12, sm=6, md=3),
            dbc.Col(dcc.Dropdown(id='district-source-filter', multi=True, placeholder="Select Source"), xs=12, sm=6, md=3),
            dbc.Col(dcc.Dropdown(id='district-course-filter', multi=True, placeholder="Select Course"), xs=12, sm=6, md=3),
        ], className="mb-3"),     
    ]),   
    
    # Loading Component
    dbc.Container([
        dcc.Loading(
            id="loading-district-reports",
            type="circle",
            children=[html.Div(id='district-reports-content', className="mt-3")]
        )
    ], className="mt-4"),

    # Download PDF Button
    dbc.Container([
        html.Div(html.Button("Download Report as PDF", id="district-download-pdf", className="btn btn-primary mt-3"), className="text-center"),
        dcc.Download(id="district-pdf-download-link")
    ], className="mt-3")
])

# Register Callbacks
def register_callbacks(app):
    @app.callback(
        [Output('district-group-filter', 'options'),
         Output('district-owner-filter', 'options'),
         Output('district-course-filter', 'options'),
         Output('district-source-filter', 'options')],
        Input('processed-data-store', 'data')
    )
    def populate_filters(data):
        if not data:
            return [], [], [], []
        df = pd.read_json(data, orient='split')
        return [
            [{'label': group, 'value': group} for group in df['Group'].dropna().unique()],
            [{'label': owner, 'value': owner} for owner in df['Owner'].dropna().unique()],
            [{'label': course, 'value': course} for course in df['Lead | Course'].dropna().unique()],
            [{'label': source, 'value': source} for source in df['Lead Source'].dropna().unique()]
        ]
    
    @app.callback(
        Output('district-reports-content', 'children'),
        [Input('processed-data-store', 'data'),
         Input('district-group-filter', 'value'),
         Input('district-owner-filter', 'value'),
         Input('district-course-filter', 'value'),
         Input('district-source-filter', 'value')]
    )
    def update_district_reports(data, selected_groups, selected_owners, selected_sources, selected_course):
        if not data:
            return html.Div("No data available. Please upload a file on the Home Page.", className='text-warning')
        df = pd.read_json(data, orient='split')

        # Apply Filters
        if selected_groups:
            df = df[df['Group'].isin(selected_groups)]
        if selected_owners:
            df = df[df['Owner'].isin(selected_owners)]
        if selected_course:
            df = df[df['Lead | Course'].isin(selected_course)]
        if selected_sources:
            df = df[df['Lead Source'].isin(selected_sources)]
        
        lead_counts = df.groupby(["Lead | Permanent District", "Lead | Course", "Lead Stage"]).size().reset_index(name="Lead Count")
        pivot_counts = df.groupby(["Lead | Permanent District", "Lead | Course"]).size().reset_index(name="Pivot Count")
        pivot_df = pivot_counts.pivot(index="Lead | Permanent District", columns="Lead | Course", values="Pivot Count").fillna(0)
        
        return html.Div([
            dcc.Graph(figure=px.bar(lead_counts, x='Lead | Permanent District', y='Lead Count', color='Lead Stage', barmode='stack', title="District-Wise & Course-Wise Lead Distribution", template="plotly_dark"), style={"width": "100%", "height": "auto"}),
            dcc.Graph(figure=px.imshow(pivot_df, color_continuous_scale="viridis", title="Lead Distribution Heatmap (District vs Course)", labels={'color': "Lead Count"}, template="plotly_dark"), style={"width": "100%", "height": "auto"}),
            dcc.Graph(figure=px.sunburst(lead_counts, path=["Lead | Permanent District", "Lead | Course", "Lead Stage"], values='Lead Count', title="Hierarchical View: District → Course → Lead Stage", template="plotly_dark"), style={"width": "100%", "height": "auto"}),
            dcc.Graph(figure=px.treemap(lead_counts, path=['Lead | Permanent District','Lead | Course','Lead Stage'], values ='Lead Count', title="Treemap: Lead Distribution by District & Course", color_continuous_scale="blues", template="plotly_dark"), style={"width": "100%", "height": "auto"})
        ])
