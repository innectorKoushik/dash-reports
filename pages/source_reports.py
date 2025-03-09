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
    html.H2("Source-Wise Reports", className="text-center text-white"),
    
    # Filters Section
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(id='source-source-filter', multi=True, placeholder="Select Source"),
            ], width=4),
            dbc.Col([
                dcc.Dropdown(id='source-lead-stage-filter', multi=True, placeholder="Select Lead Stage"),
            ], width=4),
        ], className="mb-3"),
    ]),   
    
    # Loading Component
    dbc.Container([
        dcc.Loading(
            id="loading-source-reports",
            type="circle",
            children=[html.Div(id='source-reports-content', className="mt-3")]
        )
    ], className="mt-4"),

    # Download PDF Button
    dbc.Container([
        html.Button("Download Report as PDF", id="source-download-pdf", className="btn btn-primary mt-3"),
        dcc.Download(id="source-pdf-download-link")
    ], className="mt-3 text-center")
])

# Register Callbacks
def register_callbacks(app):
    @app.callback(
        [Output('source-source-filter', 'options'),
         Output('source-lead-stage-filter', 'options')],
        Input('processed-data-store', 'data')
    )
    def populate_filters(data):
        if not data:
            return [], []
        
        df = pd.read_json(data, orient='split')
        return [
            [{'label': source, 'value': source} for source in df['Lead Source'].dropna().unique()],
            [{'label': stage, 'value': stage} for stage in df['Lead Stage'].dropna().unique()]
        ]
    
    @app.callback(
        Output('source-reports-content', 'children'),
        [Input('processed-data-store', 'data'),
         Input('source-source-filter', 'value'),
         Input('source-lead-stage-filter', 'value')]
    )
    def update_source_reports(data, selected_sources, selected_stages):
        if not data:
            return html.Div("No data available. Please upload a file on the Home Page.", className='text-warning')
        
        df = pd.read_json(data, orient='split')
        if selected_sources:
            df = df[df['Lead Source'].isin(selected_sources)]
        if selected_stages:
            df = df[df['Lead Stage'].isin(selected_stages)]
        
        # Pivot Table Data
        pivot_df = df.pivot_table(index='Lead Source', columns='Lead Stage', values='Lead | Phone Number', aggfunc='count', fill_value=0)
        lead_count = df.groupby(['Lead Source','Lead Stage']).size().reset_index(name='Lead Count')
        
        # Charts
        source_heatmap = px.imshow(
            pivot_df, color_continuous_scale="blues",
            title="Source vs Lead Stage Heatmap", labels={'x': 'Lead Stage', 'y': 'Source', 'color': 'Lead Count'}, template="plotly_dark"
        )
        
        source_bar_chart = px.bar(
            lead_count,
            x='Lead Source', y='Lead Count', color='Lead Stage', title="Lead Distribution by Source and Stage",
            barmode="stack", template="plotly_dark"
        )

        source_grouped_bar_chart = px.bar(
            lead_count, x="Lead Stage", y="Lead Count", color="Lead Source",
            title="Lead Stage Comparison Across Sources",
            barmode="group", template="plotly_dark"
        )

        source_sunburst_chart = px.sunburst(
            lead_count, path=["Lead Source", "Lead Stage"], values="Lead Count",
            title="Source Breakdown by Lead Stages",template = "plotly_dark",height=600
        )
        
        source_treemap_chart = px.treemap(
            lead_count, path=["Lead Source", "Lead Stage"], values="Lead Count",
            title="Lead Count Distribution by Source",template = "plotly_dark",height=600
        )

        return html.Div([
            dcc.Graph(figure=source_heatmap),
            dcc.Graph(figure=source_bar_chart),
            dcc.Graph(figure=source_grouped_bar_chart),
            dcc.Graph(figure=source_sunburst_chart),
            dcc.Graph(figure=source_treemap_chart)
        ])
    
    @app.callback(
        Output("source-pdf-download-link", "data"),
        Input("source-download-pdf", "n_clicks"),
        State('processed-data-store', 'data'),
        prevent_initial_call=True
    )
    def generate_pdf(n_clicks, data):
        if not data:
            return None

        df = pd.read_json(data, orient='split')
        lead_counts = df.groupby(['Lead Source', 'Lead Stage']).size().reset_index(name='Lead Count')
        pivot_df = df.pivot_table(index='Lead Source', columns='Lead Stage', values='Lead | Phone Number', aggfunc='count', fill_value=0)

        # Generate Charts
        charts = {
            "Heatmap": px.imshow(pivot_df, color_continuous_scale="viridis", title="Lead Stage Distribution Heatmap by Source"),
            "Stacked Bar Chart": px.bar(lead_counts, x='Lead Source', y='Lead Count', color='Lead Stage', barmode='stack', title="Source-Wise Lead Distribution"),
            "Grouped Bar Chart": px.bar(lead_counts, x="Lead Stage", y="Lead Count", color="Lead Source", barmode='group', title="Lead Stage Comparison Across Sources"),
            "Sunburst Chart": px.sunburst(lead_counts, path=["Lead Source", "Lead Stage"], values="Lead Count", title="Source Breakdown by Lead Stages"),
            "Treemap Chart": px.treemap(lead_counts, path=["Lead Source", "Lead Stage"], values="Lead Count", title="Lead Count Distribution by Source")
        }

        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, "source_reports.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A3)
        page_width, page_height = A3
        y_position = page_height - 100
        chart_width, chart_height = 700, 500

        for chart_name, fig in charts.items():
            chart_path = os.path.join(temp_dir, f"{chart_name}.png")
            fig.write_image(chart_path, format='png')
            x_center = (page_width - chart_width) / 2
            c.setFont("Helvetica-Bold", 18)
            c.drawString(x_center + 50, y_position + 20, chart_name)
            c.drawImage(ImageReader(chart_path), x_center, y_position - chart_height, width=chart_width, height=chart_height)
            y_position -= (chart_height + 70)
            if y_position < 100:
                c.showPage()
                y_position = page_height - 100
        
        c.save()
        return dcc.send_file(pdf_path)
