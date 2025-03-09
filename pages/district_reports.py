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
            dbc.Col([
                dcc.Dropdown(id='district-group-filter', multi=True, placeholder="Select Group"),
            ], width=4),
            dbc.Col([
                dcc.Dropdown(id='district-owner-filter', multi=True, placeholder="Select Owner"),
            ], width=4),
            dbc.Col([
                dcc.Dropdown(id='district-source-filter', multi=True, placeholder="Select Source"),
            ], width=4),
            dbc.Col([
                dcc.Dropdown(id='district-course-filter', multi=True, placeholder="Select Course"),
            ], width=4),
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
        html.Button("Download Report as PDF", id="district-download-pdf", className="btn btn-primary mt-3"),
        dcc.Download(id="district-pdf-download-link")
    ], className="mt-3 text-center")
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
            return [], [], [],[]
        
        df = pd.read_json(data, orient='split')

         # Remove any None or NaN values
        clean_courses = df['Lead | Course'].dropna().unique()
        clean_sources = df['Lead Source'].dropna().unique()
        clean_groups = df['Group'].dropna().unique()
        clean_owners = df['Owner'].dropna().unique()

        return [
            [{'label': group, 'value': group} for group in clean_groups],
            [{'label': owner, 'value': owner} for owner in clean_owners],
            [{'label': course, 'value': course} for course in clean_courses],
            [{'label': source, 'value': source} for source in clean_sources]
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
        

        # Aggregate Data
        # ✅ Aggregate Lead Count
        lead_counts = df.groupby(["Lead | Permanent District", "Lead | Course", "Lead Stage"]).size().reset_index(name="Lead Count")

        #stacked bar chart
        district_stacked_bar_chart= px.bar(
            lead_counts,
            x='Lead | Permanent District', y='Lead Count',color='Lead Stage',facet_col="Lead | Course", barmode='stack',
            title="District-Wise & Course-Wise Lead Distribution",
            template="plotly_dark"
        )

        #District-heatmap
        pivot_counts = df.groupby(["Lead | Permanent District", "Lead | Course"]).size().reset_index(name="Pivot Count")

        pivot_df = pivot_counts.pivot(index="Lead | Permanent District", columns="Lead | Course", values="Pivot Count").fillna(0)
        district_heatmap = px.imshow(
            pivot_df,color_continuous_scale="viridis",
            title="Lead Distribution Heatmap (District vs Course)",
            labels={'color': "Lead Count"},template="plotly_dark"
        )

        # Sunburst Chart
        district_sunburst_chart = px.sunburst(
            lead_counts, path=["Lead | Permanent District", "Lead | Course", "Lead Stage"], values='Lead Count',
            title="Hierarchical View: District → Course → Lead Stage",
            template="plotly_dark",width=1000,height=550
        )

        district_treemap_chart= px.treemap(
            lead_counts,path=['Lead | Permanent District','Lead | Course','Lead Stage'], values ='Lead Count',title="Treemap: Lead Distribution by District & Course",
            color_continuous_scale="blues",template="plotly_dark"
            )

        # Bar Chart for Top Performers
        district_grouped_bar_chart = px.bar(
            lead_counts, x="Lead Stage", y="Lead Count", color="Lead | Permanent District",
            title="Lead Stage Distribution per District",
            barmode='group', template="plotly_dark"
        )

        
        # Generate Report Layout
        report_layout = html.Div([
            dcc.Graph(figure=district_grouped_bar_chart),
            dcc.Graph(figure=district_sunburst_chart),
            dcc.Graph(figure=district_treemap_chart),    
            dcc.Graph(figure=district_stacked_bar_chart),
            dcc.Graph(figure=district_heatmap)
            ])
        return report_layout
            

    @app.callback(
    Output("district-pdf-download-link", "data"),
    Input("district-download-pdf", "n_clicks"),
    State('processed-data-store', 'data'),
    prevent_initial_call=True
)


    def generate_pdf(n_clicks, data):
        if not data:
            return None

        df = pd.read_json(data, orient='split')

        # ✅ Step 1: Aggregate Data
        lead_counts = df.groupby(["Lead | Permanent District", "Lead | Course", "Lead Stage"]).size().reset_index(name="Lead Count")
        pivot_counts = df.groupby(["Lead | Permanent District", "Lead | Course"]).size().reset_index(name="Pivot Count")

        # ✅ Step 2: Generate Charts

        # 1️⃣ Stacked Bar Chart
        district_stacked_bar_chart = px.bar(
            lead_counts, x='Lead | Permanent District', y='Lead Count', color='Lead Stage',
            facet_col="Lead | Course", barmode='stack', title="District-Wise & Course-Wise Lead Distribution",
            template="plotly_dark"
        )

        # 2️⃣ Heatmap
        pivot_df = pivot_counts.pivot(index="Lead | Permanent District", columns="Lead | Course", values="Pivot Count").fillna(0)
        district_heatmap = px.imshow(
            pivot_df, color_continuous_scale="viridis",
            title="Lead Distribution Heatmap (District vs Course)", labels={'color': "Lead Count"}
        )

        # 3️⃣ Sunburst Chart
        district_sunburst_chart = px.sunburst(
            lead_counts, path=["Lead | Permanent District", "Lead | Course", "Lead Stage"], values='Lead Count',
            title="Hierarchical View: District → Course → Lead Stage", template="plotly_dark"
        )

        # 4️⃣ Treemap
        district_treemap_chart = px.treemap(
            lead_counts, path=['Lead | Permanent District', 'Lead | Course', 'Lead Stage'], values='Lead Count',
            title="Treemap: Lead Distribution by District & Course", color_continuous_scale="blues",
            template="plotly_dark"
        )

        # 5️⃣ Grouped Bar Chart
        district_grouped_bar_chart = px.bar(
            lead_counts, x="Lead Stage", y="Lead Count", color="Lead | Permanent District",
            title="Lead Stage Distribution per District", barmode='group', template="plotly_dark"
        )

        # ✅ Step 3: Save Charts as Images
        temp_dir = tempfile.gettempdir()
        chart_paths = {
            "Stacked Bar Chart": os.path.join(temp_dir, "stacked_bar_chart.png"),
            "Heatmap": os.path.join(temp_dir, "heatmap.png"),
            "Sunburst Chart": os.path.join(temp_dir, "sunburst_chart.png"),
            "Treemap": os.path.join(temp_dir, "treemap_chart.png"),
            "Grouped Bar Chart": os.path.join(temp_dir, "grouped_bar_chart.png"),
        }

        # Save images
        district_stacked_bar_chart.write_image(chart_paths["Stacked Bar Chart"], format='png')
        district_heatmap.write_image(chart_paths["Heatmap"], format='png')
        district_sunburst_chart.write_image(chart_paths["Sunburst Chart"], format='png')
        district_treemap_chart.write_image(chart_paths["Treemap"], format='png')
        district_grouped_bar_chart.write_image(chart_paths["Grouped Bar Chart"], format='png')

        # ✅ Step 4: Generate PDF
        pdf_path = os.path.join(temp_dir, "district_reports.pdf")
        c = canvas.Canvas(pdf_path, pagesize=A3)
        page_width, page_height = A3
        y_position = page_height - 100  
        chart_width = 700
        chart_height = 500  

        # Loop through saved charts and add them to the PDF
        for chart_name, chart_path in chart_paths.items():
            if os.path.exists(chart_path):
                x_center = (page_width - chart_width) / 2  

                # Add Chart Title
                c.setFont("Helvetica-Bold", 18)
                c.drawString(x_center + 50, y_position + 20, chart_name)

                # Draw the chart image
                c.drawImage(ImageReader(chart_path), x_center, y_position - chart_height, width=chart_width, height=chart_height)

                # Update y_position for next chart
                y_position -= (chart_height + 70)

                # If space runs out, add a new page
                if y_position < 100:
                    c.showPage()  
                    y_position = page_height - 100  

        # Save PDF
        c.save()

        return dcc.send_file(pdf_path)