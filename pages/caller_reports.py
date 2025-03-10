import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px

# Layout
layout = html.Div([
    dcc.Store(id='processed-data-store'), 
    html.H2("Caller Reports", className="text-center text-white mt-3"),

    dbc.Container(fluid=True, children=[
        dbc.Row([
            dbc.Col(dcc.Dropdown(id='owner-filter', options=[], multi=True, placeholder="Select Owners"), width=12, md=6, lg=3, className="mb-2"),
            dbc.Col(dcc.Dropdown(id='source-filter', options=[], multi=True, placeholder="Select Source"), width=12, md=6, lg=3, className="mb-2"),
            dbc.Col(dcc.Dropdown(id='course-filter', options=[], multi=True, placeholder="Select Course"), width=12, md=6, lg=3, className="mb-2"),
            dbc.Col(dcc.Dropdown(id='district-filter', options=[], multi=True, placeholder="Select Permanent District"), width=12, md=6, lg=3, className="mb-2"),
            dbc.Col(dcc.Dropdown(id='activity-filter', options=[], multi=True, placeholder="Select Activity Event"), width=12, md=6, lg=3, className="mb-2"),
            dbc.Col(dcc.Dropdown(id='status-filter', options=[], multi=True, placeholder="Select Status"), width=12, md=6, lg=3, className="mb-2"),
            dbc.Col(dcc.Dropdown(id='group-filter', options=[], multi=True, placeholder="Select Group"), width=12, md=6, lg=3, className="mb-2"),
        ], className="mt-3"),

        dcc.Loading(
            id="loading-caller-reports",
            type="circle",
            children=[html.Div(id='caller-reports-content', className="mt-3")]
        )
    ], className="mt-4")
])

# Register Callbacks
def register_callbacks(app):
    """ Function to register Dash callbacks """

    @app.callback(
        [
            Output('owner-filter', 'options'),
            Output('source-filter', 'options'),
            Output('course-filter', 'options'),
            Output('district-filter', 'options'),
            Output('activity-filter', 'options'),
            Output('status-filter', 'options'),
            Output('group-filter', 'options'),
        ],
        Input('processed-data-store', 'data')
    )
    def update_dropdown_options(data):
        if not data:
            return [[], [], [], [], [], [], []]  

        df = pd.read_json(data, orient='split')

        return [
            [{"label": i, "value": i} for i in df["Owner"].dropna().unique()],
            [{"label": i, "value": i} for i in df["Lead Source"].dropna().unique()],
            [{"label": i, "value": i} for i in df["Lead | Course"].dropna().unique()],
            [{"label": i, "value": i} for i in df["Lead | Permanent District"].dropna().unique()],
            [{"label": i, "value": i} for i in df["ActivityEvent"].dropna().unique()],
            [{"label": i, "value": i} for i in df["Lead Stage"].dropna().unique()],
            [{"label": i, "value": i} for i in df["Group"].dropna().unique()],
        ]

    @app.callback(
        Output('caller-reports-content', 'children'),
        [
            Input('processed-data-store', 'data'),
            Input('owner-filter', 'value'),
            Input('source-filter', 'value'),
            Input('course-filter', 'value'),
            Input('district-filter', 'value'),
            Input('activity-filter', 'value'),
            Input('status-filter', 'value'),
            Input('group-filter', 'value')
        ]
    )
    def update_caller_reports(data, owners, sources, courses, districts, activities, statuses, groups):
        if not data:
            return html.Div("No data available. Please upload a file on the Home Page.", className='text-warning')

        df = pd.read_json(data, orient='split')

        # Apply Filters
        if owners:
            df = df[df['Owner'].isin(owners)]
        if sources:
            df = df[df['Lead Source'].isin(sources)]
        if courses:
            df = df[df['Course'].isin(courses)]
        if districts:
            df = df[df['PermanentDistrict'].isin(districts)]
        if activities:
            df = df[df['Activity Event'].isin(activities)]
        if statuses:
            df = df[df['Lead Stage'].isin(statuses)]
        if groups:
            df = df[df['Group'].isin(groups)]

        # Caller Summary Table
        caller_summary = df.groupby('Owner').agg({
            'Call Duration Seconds': 'sum',
            'Status': 'count'
        }).reset_index()

        caller_summary['Total Duration (min)'] = (caller_summary['Call Duration Seconds'] / 60).round(2)
        caller_summary.rename(columns={'Status': 'Total Calls'}, inplace=True)
        caller_summary.drop(columns=['Call Duration Seconds'], inplace=True)

        table = dbc.Table.from_dataframe(
            caller_summary, striped=True, bordered=True, hover=True, className="table-responsive text-white"
        )

        # Lead Stage Breakdown
        lead_stage_summary = df.groupby(['Owner', 'Lead Stage']).size().reset_index(name='Stage Count')

        # Create the bar chart
        stage_chart = dcc.Graph(
            figure=px.bar(
                lead_stage_summary, x="Owner", y="Stage Count", color="Lead Stage",
                title="Total Calls by Caller (Lead Stage Breakdown)",
                template="plotly_dark"
            ),
            style={'width': '100%', 'height': 'auto'}
        )

        # Line Chart for Call Counts Over Time
        df['CreatedOn'] = pd.to_datetime(df['CreatedOn'])
        call_counts_over_time = df.resample('h', on='CreatedOn').size().reset_index(name='Call Count')

        line_chart = dcc.Graph(
            figure=px.line(
                call_counts_over_time, x='CreatedOn', y='Call Count', title="Call Counts Over Time",
                template="plotly_dark", markers=True
            ),
            style={'width': '100%', 'height': 'auto'}
        )

        # Stacked Bar Chart for Lead Stages
        lead_stage_chart = dcc.Graph(
            figure=px.bar(
                lead_stage_summary, x="Owner", y="Stage Count", color="Lead Stage",
                title="Lead Stage Distribution by Owner", template="plotly_dark",
                text_auto=True, barmode="stack"
            ),
            style={'width': '100%', 'height': 'auto'}
        )

        # Funnel Chart for Lead Stages
        funnel_chart = dcc.Graph(
            figure=px.funnel(
                df.groupby('Lead Stage').size().reset_index(name='Count'), 
                x='Lead Stage', y='Count', title="Funnel Chart of Lead Stages",
                template="plotly_dark"
            ),
            style={'width': '100%', 'height': 'auto'}
        )

        return html.Div([
            table, line_chart, lead_stage_chart, funnel_chart
        ], className="container-fluid")

