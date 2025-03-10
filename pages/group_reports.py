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
    html.H2("Group Reports", className="text-center text-white"),
    
    # Filters Section
    dbc.Container([
        dbc.Row([
            dbc.Col(dcc.Dropdown(id='group-group-filter', multi=True, placeholder="Select Group"), width=12, lg=4),
            dbc.Col(dcc.Dropdown(id='group-owner-filter', multi=True, placeholder="Select Owner"), width=12, lg=4),
            dbc.Col(dcc.Dropdown(id='group-source-filter', multi=True, placeholder="Select Lead Source"), width=12, lg=4),
        ], className="mb-3"),
    ]),

    # Loading Component
    dbc.Container([
        dcc.Loading(
            id="loading-group-reports",
            type="circle",
            children=[html.Div(id='group-reports-content', className="mt-3")]
        )
    ], className="mt-4"),

    # Download PDF Button
    dbc.Container([
        html.Button("Download Report as PDF", id="group-download-pdf", className="btn btn-primary mt-3 w-100"),
        dcc.Download(id="group-pdf-download-link")
    ], className="mt-3 text-center")
])

# Register Callbacks
def register_callbacks(app):
    @app.callback(
        [Output('group-group-filter', 'options'),
         Output('group-owner-filter', 'options'),
         Output('group-source-filter', 'options')],
        Input('processed-data-store', 'data')
    )
    def populate_filters(data):
        if not data:
            return [], [], []
        
        df = pd.read_json(data, orient='split')
        return [
            [{'label': group, 'value': group} for group in df['Group'].unique()],
            [{'label': owner, 'value': owner} for owner in df['Owner'].unique()],
            [{'label': source, 'value': source} for source in df['Lead Source'].unique()]
        ]

    @app.callback(
        Output('group-reports-content', 'children'),
        [Input('processed-data-store', 'data'),
         Input('group-group-filter', 'value'),
         Input('group-owner-filter', 'value'),
         Input('group-source-filter', 'value')]
    )
    def update_group_reports(data, selected_groups, selected_owners, selected_sources):
        if not data:
            return html.Div("No data available. Please upload a file on the Home Page.", className='text-warning')
        
        df = pd.read_json(data, orient='split')

        # Apply Filters
        if selected_groups:
            df = df[df['Group'].isin(selected_groups)]
        if selected_owners:
            df = df[df['Owner'].isin(selected_owners)]
        if selected_sources:
            df = df[df['Lead Source'].isin(selected_sources)]

        # Aggregate Data
        lead_counts = df.groupby(["Owner", "Lead Stage", "Group"]).size().reset_index(name="Lead Count")

        # Generate Charts
        charts = [
            px.sunburst(df.groupby(['Group', 'Owner', 'Lead Stage']).size().reset_index(name='Count'),
                        path=['Group', 'Owner', 'Lead Stage'], values='Count',
                        title="Group Hierarchy: Group → Caller → Lead Stage", template="plotly_dark"),
            px.scatter(lead_counts, x="Group", y="Owner", size="Lead Count", color="Lead Stage",
                       title="Bubble Chart: Caller Performance within Groups", hover_name="Owner", template="plotly_dark"),
            px.funnel(lead_counts, x="Lead Count", y="Lead Stage", color="Group",
                      title="Lead Stage Breakdown for Each Group", orientation="h", template="plotly_dark"),
            px.bar(lead_counts, x="Lead Count", y="Owner", color="Group", title="Top Performing Caller in Each Group",
                   orientation="h", text_auto=True, template="plotly_dark"),
            px.pie(lead_counts, values="Lead Count", names="Group", title="Lead Distribution by Group", hole=0.4,
                   template="plotly_dark"),
            px.treemap(lead_counts, path=["Group", "Owner"], values="Lead Count", title="Treemap: Owner Performance within Groups",
                       color_continuous_scale="blues", template="plotly_dark")
        ]

        return html.Div([dcc.Graph(figure=chart) for chart in charts])

    @app.callback(
        Output("group-pdf-download-link", "data"),
        Input("group-download-pdf", "n_clicks"),
        State('processed-data-store', 'data'),
        prevent_initial_call=True
    )
    def generate_pdf(n_clicks, data):
        if not data:
            return None

        df = pd.read_json(data, orient='split')
        lead_counts = df.groupby(["Owner", "Lead Stage", "Group"]).size().reset_index(name="Lead Count")

        # Generate Charts and Save as Images
        temp_dir = tempfile.gettempdir()
        chart_paths = []
        charts = [
            px.sunburst(df.groupby(['Group', 'Owner', 'Lead Stage']).size().reset_index(name='Count'),
                        path=['Group', 'Owner', 'Lead Stage'], values='Count',
                        title="Group Hierarchy", template="plotly_dark"),
            px.scatter(lead_counts, x="Group", y="Owner", size="Lead Count", color="Lead Stage", title="Caller Performance",
                       hover_name="Owner", template="plotly_dark"),
            px.funnel(lead_counts, x="Lead Count", y="Lead Stage", color="Group", title="Lead Stage Breakdown",
                      orientation="h", template="plotly_dark"),
            px.bar(lead_counts, x="Lead Count", y="Owner", color="Group", title="Top Performers", orientation="h",
                   text_auto=True, template="plotly_dark"),
        ]
        
        for i, chart in enumerate(charts):
            chart_path = os.path.join(temp_dir, f"chart_{i}.png")
            chart.write_image(chart_path, format='png')
            chart_paths.append(chart_path)

        # Create PDF
        pdf_path = os.path.join(temp_dir, "group_reports.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A3)
        y_position = A3[1] - 100
        for chart_path in chart_paths:
            if os.path.exists(chart_path):
                c.drawImage(ImageReader(chart_path), 50, y_position - 400, width=700, height=400)
                y_position -= 450
                if y_position < 100:
                    c.showPage()
                    y_position = A3[1] - 100
        c.save()

        return dcc.send_file(pdf_path)
