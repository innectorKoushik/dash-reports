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
            dbc.Col([
                dcc.Dropdown(id='group-group-filter', multi=True, placeholder="Select Group"),
            ], width=4),
            dbc.Col([
                dcc.Dropdown(id='group-owner-filter', multi=True, placeholder="Select Owner"),
            ], width=4),
            dbc.Col([
                dcc.Dropdown(id='group-source-filter', multi=True, placeholder="Select Lead Source"),
            ], width=4),
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
        html.Button("Download Report as PDF", id="group-download-pdf", className="btn btn-primary mt-3"),
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

        # Sunburst Chart
        sunburst_chart = px.sunburst(
            df.groupby(['Group', 'Owner', 'Lead Stage']).size().reset_index(name='Count'),
            path=['Group', 'Owner', 'Lead Stage'], values='Count',
            title="Group Hierarchy: Group → Caller → Lead Stage",
            template="plotly_dark",width=1000,height=550
        )

        bubble_chart= px.scatter(
            lead_counts,x="Group",y="Owner",size="Lead Count",color="Lead Stage",title="Bubble Chart: Caller Performance within Groups",
            hover_name="Owner",template="plotly_dark"
            )

        # Bar Chart for Top Performers
        top_performer_chart = px.bar(
            lead_counts, x="Lead Count", y="Owner", color="Group",
            title="Top Performing Caller in Each Group",
            orientation="h", text_auto=True, template="plotly_dark"
        )

        treemap_chart = px.treemap(
            df.groupby(['Group', 'Owner'])['Lead Stage'].count().reset_index(name='Count'),
            path=['Group', 'Owner'], 
            values='Count',
            title="Group-wise Performance Overview",
            template="plotly_dark"
            )
        
        lead_stage_chart = px.bar(
            lead_counts,  # ✅ Correct DataFrame
                x='Group', 
                y='Lead Count',  # ✅ This column now exists
                color='Lead Stage',
                title="Stacked Bar Chart: Leads per Group by Stage",
                barmode='stack',
                template="plotly_dark",
                text_auto=True
            )
        lead_tree_chart = px.treemap(
            lead_counts,path=["Group","Owner"],values="Lead Count",title="Treemap: Owner Performance within Groups",
            color_continuous_scale="blues",template="plotly_dark"
            )  
        
        lead_group_chart =  px.pie(
           lead_counts,values="Lead Count", hole=0.5, names="Group",title="Lead Distribution by Group",template="plotly_dark"
            )
        
        #Lead Stage Breakdown for each group funnel chart
        funnel_chart= px.funnel(
            lead_counts,x="Lead Count",y="Lead Stage",color="Group",title="Lead Stage Breakdown for Each Group",orientation="h",template="plotly_dark"
            )
        
        # Generate Report Layout
        report_layout = html.Div([
            dcc.Graph(figure=sunburst_chart),
            dcc.Graph(figure=bubble_chart),
            dcc.Graph(figure=funnel_chart),
            dcc.Graph(figure=lead_group_chart),
            dcc.Graph(figure=top_performer_chart),
            dcc.Graph(figure=lead_stage_chart),
            dcc.Graph(figure=treemap_chart),    
        ])

        

        return report_layout

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

        # Aggregate data properly
        lead_counts = df.groupby(["Owner", "Lead Stage", "Group"]).size().reset_index(name="Lead Count")

        # Generate Sunburst Chart with Correct Grouping
        sunburst_data = df.groupby(['Group', 'Owner', 'Lead Stage']).size().reset_index(name='Count')
        sunburst_chart = px.sunburst(
            sunburst_data,
            path=['Group', 'Owner', 'Lead Stage'],
            values='Count',
            title="Group Hierarchy: Group → Caller → Lead Stage",
            template="plotly_dark"
        )

        # Bubble Chart
        bubble_chart = px.scatter(
            lead_counts,
            x="Group", y="Owner", size="Lead Count",
            color="Lead Stage", title="Bubble Chart: Caller Performance within Groups",
            hover_name="Owner", template="plotly_dark"
        )

        # Funnel Chart
        funnel_chart = px.funnel(
            lead_counts,
            x="Lead Count", y="Lead Stage",
            color="Group",
            title="Lead Stage Breakdown for Each Group",
            orientation="h", template="plotly_dark"
        )

        # Top Performer Bar Chart
        bar_chart = px.bar(
            lead_counts, x="Lead Count", y="Owner",
            color="Group", title="Top Performing Caller in Each Group",
            orientation="h", text_auto=True, template="plotly_dark"
        )

        # Pie Chart
        lead_group_chart = px.pie(
            lead_counts, values="Lead Count", names="Group",
            title="Lead Distribution by Group", hole=0.4, template="plotly_dark"
        )

        # Treemap Chart
        treemap_chart = px.treemap(
            lead_counts, path=["Group", "Owner"],
            values="Lead Count", title="Treemap: Owner Performance within Groups",
            color_continuous_scale="blues", template="plotly_dark"
        )

        # Save Charts as Images
        temp_dir = tempfile.gettempdir()
        chart_paths = {
            "Sunburst Chart": os.path.join(temp_dir, "sunburst_chart.png"),
            "Bubble Chart": os.path.join(temp_dir, "bubble_chart.png"),
            "Funnel Chart": os.path.join(temp_dir, "funnel_chart.png"),
            "Top Performer Chart": os.path.join(temp_dir, "bar_chart.png"),
            "Pie Chart": os.path.join(temp_dir, "pie_chart.png"),
            "Treemap Chart": os.path.join(temp_dir, "treemap_chart.png")
        }

        # Save images
        sunburst_chart.write_image(chart_paths["Sunburst Chart"], format='png')
        bubble_chart.write_image(chart_paths["Bubble Chart"], format='png')
        funnel_chart.write_image(chart_paths["Funnel Chart"], format='png')
        bar_chart.write_image(chart_paths["Top Performer Chart"], format='png')
        lead_group_chart.write_image(chart_paths["Pie Chart"], format='png')
        treemap_chart.write_image(chart_paths["Treemap Chart"], format='png')

        # Create PDF
        pdf_path = os.path.join(temp_dir, "group_reports.pdf")
        
        # Use A3 for better readability (page size: 11.7 x 16.5 inches)
        c = canvas.Canvas(pdf_path, pagesize=A3)

        # Get A3 page dimensions
        page_width, page_height = A3

        # Set initial y-position near the top
        y_position = page_height - 100  

        # Define bigger chart size
        chart_width = 700  # Increase width
        chart_height = 500  # Increase height

        # Loop through saved charts and add to PDF
        for chart_name, chart_path in chart_paths.items():
            if os.path.exists(chart_path):
                x_center = (page_width - chart_width) / 2  # Center horizontally

                # Add Chart Title
                c.setFont("Helvetica-Bold", 18)
                c.drawString(x_center + 50, y_position + 20, chart_name)

                # Draw the chart image
                c.drawImage(ImageReader(chart_path), x_center, y_position - chart_height, width=chart_width, height=chart_height)

                # Update y_position for next chart
                y_position -= (chart_height + 70)  # Add more spacing between charts

                # If space runs out, add a new page
                if y_position < 100:
                    c.showPage()  # Create a new page
                    y_position = page_height - 100  # Reset y-position for new page

        # Save the PDF
        c.save()

        # ✅ Corrected Return Value for Dash
        return dcc.send_file(pdf_path)
