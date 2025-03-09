from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import base64
import io
from utils.data_processing import process_data

# Layout for Home Page
layout = html.Div([
    dcc.Store(id='processed-data-store'),  # Store processed data
    html.H2("Welcome to KEI Reports", className="text-center text-orange"),
    html.H3("Upload Dataset", className="text-left text-blue"),
    html.H6("Kindly Note: The Dataset Should have these Columns(ActivityEvent,Owner,Call Duration,Status,CreatedOn,Lead Stage,Lead Source,Lead | Phone Number,Lead | Permanent District,Lead | Course)",className="note"),
    dbc.Container([
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ', html.A('Select Files', className="text-primary")
            ]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'margin': '10px', 'backgroundColor': '#343a40', 'color': 'white'
            },
            multiple=False
        ),
        dcc.Loading(
            id="loading",
            type="circle",
            children=[html.Div(id='output-data-upload', className="mt-3")]
        )
    ], className="mt-4"),

    html.Div(id='summary-cards', className='mt-4'),
    html.Div(id='charts', className='mt-4')
])

# Function to parse contents
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div(['Unsupported file format. Please upload a CSV or Excel file.'], className='text-danger')

        # Process data
        df = process_data(df)

        if df is None or df.empty:
            return html.Div(['Error: Processed data is empty. Please check the uploaded file.'], className='text-danger')

        return html.Div([
            html.H5(f'File Uploaded: {filename}', className='text-success'),
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                style_table={'overflowX': 'auto', 'backgroundColor': '#212529', 'color': 'white'},
                style_header={'backgroundColor': 'black', 'color': 'white'},
                style_data={'backgroundColor': '#343a40', 'color': 'white'},
                page_size=10, 
                style_cell={'textAlign': 'left'},
                sort_action="native",
                filter_action="native",
            )
        ])
    except Exception as e:
        return html.Div([f'Error processing file: {str(e)}'], className='text-danger')

# Register callbacks
def register_callbacks(app):
    @app.callback(
        [Output('output-data-upload', 'children'),
         Output('summary-cards', 'children'),
         Output('charts', 'children'),
         Output('processed-data-store', 'data')],  # Store processed data
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename')]
    )
    def update_output(contents, filename):
        if contents is not None:
            parsed_data = parse_contents(contents, filename)
            df = process_data(pd.read_csv(io.StringIO(base64.b64decode(contents.split(',')[1]).decode('utf-8'))))
            
            if df is None or df.empty:
                return parsed_data, None, None
            
            total_calls = len(df)
            total_duration = int((df["Call Duration Seconds"].sum())/60)
            unique_owners = df["Owner"].nunique()

            cards = html.Div(
                dbc.Row([
                dbc.Col(dbc.Card([dbc.CardBody([html.H4("Total Calls", className="card-title"), html.H3(total_calls,className="values")])]), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([html.H4("Total Duration (min)", className="card-title"), html.H3(total_duration,className="values")])]), width=3),
                dbc.Col(dbc.Card([dbc.CardBody([html.H4("Total Unique Owners", className="card-title"), html.H3(unique_owners,className="values")])]), width=3),
            ]),className="cards-section"
            )

            pie_chart = dcc.Graph(
                figure=px.pie(df, names="ActivityEvent", title="Activity Event Distribution", hole=0.3, template="plotly_dark",color="ActivityEvent").update_traces(textinfo="label+percent+value") 
            )

            donut_chart = dcc.Graph(
                figure=px.pie(df, names="Status", title="Status Distribution", hole=0.5, template="plotly_dark").update_traces(textinfo="label+percent+value") 
            )

            charts = dbc.Row([
                dbc.Col(pie_chart, width=6),
                dbc.Col(donut_chart, width=6)
            ])

            return parsed_data, cards, charts, df.to_json(date_format='iso', orient='split') 
        return html.Div(), None, None,None
