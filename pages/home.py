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
    html.H2("Welcome to KEI Reports", className="text-center text-orange mt-3"),
    html.H3("Upload Dataset", className="text-left text-blue mt-2"),
    
    html.H6(
        "Dataset should have: ActivityEvent, Owner, Call Duration, Status, CreatedOn, Lead Stage, Lead Source, Phone Number, District, Course.",
        className="note text-muted text-center px-3"
    ),

    dbc.Container([
        dcc.Upload(
            id='upload-data',
            children=html.Div(['📂 Drag & Drop or ', html.A('Select Files', className="text-primary")]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '10px',
                'textAlign': 'center', 'margin': '10px auto',
                'backgroundColor': '#343a40', 'color': 'white'
            },
            multiple=False
        ),
        dcc.Loading(
            id="loading",
            type="circle",
            children=[html.Div(id='output-data-upload', className="mt-3")]
        )
    ], className="mt-4", fluid=True),

    html.Div(id='summary-cards', className='mt-4 container-fluid'),
    html.Div(id='charts', className='mt-4 container-fluid')
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
            return html.Div(['❌ Unsupported format. Upload CSV or Excel.'], className='text-danger')

        # Process data
        df = process_data(df)

        if df is None or df.empty:
            return html.Div(['⚠️ Error: Processed data is empty. Check your file.'], className='text-danger')

        return html.Div([
            html.H5(f'✅ File Uploaded: {filename}', className='text-success'),
            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns],
                style_table={'overflowX': 'auto', 'backgroundColor': '#212529', 'color': 'white'},
                style_header={'backgroundColor': 'black', 'color': 'white'},
                style_data={'backgroundColor': '#343a40', 'color': 'white'},
                page_size=10,  
                style_cell={'textAlign': 'left', 'padding': '5px'},
                sort_action="native",
                filter_action="native",
            )
        ], className="table-responsive")
    except Exception as e:
        return html.Div([f'❌ Error processing file: {str(e)}'], className='text-danger')

# Register callbacks
def register_callbacks(app):
    @app.callback(
        [Output('output-data-upload', 'children'),
         Output('summary-cards', 'children'),
         Output('charts', 'children'),
         Output('processed-data-store', 'data')],  
        [Input('upload-data', 'contents')],
        [State('upload-data', 'filename')]
    )
    def update_output(contents, filename):
        if contents is not None:
            parsed_data = parse_contents(contents, filename)

            try:
                df = pd.read_csv(io.StringIO(base64.b64decode(contents.split(',')[1]).decode('utf-8')))
                df = process_data(df)

                if df is None or df.empty:
                    return parsed_data, html.Div(), html.Div(), None
            except Exception as e:
                return html.Div([f'❌ Error reading file: {str(e)}'], className='text-danger'), html.Div(), html.Div(), None

            # Generate Summary Cards
            total_calls = len(df)
            total_duration = int((df["Call Duration Seconds"].sum()) / 60) if "Call Duration Seconds" in df.columns else 0
            unique_owners = df["Owner"].nunique() if "Owner" in df.columns else 0

            cards = html.Div(
                dbc.Row([
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H4("Total Calls", className="card-title text-center"),
                        html.H3(total_calls, className="values text-center")
                    ]), style={"width": "100%"}), xs=12, sm=6, md=3, className="mb-3 p-2"),
                    
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H4("Total Duration (min)", className="card-title text-center"),
                        html.H3(total_duration, className="values text-center")
                    ]), style={"width": "100%"}), xs=12, sm=6, md=3, className="mb-3 p-2"),
                    
                    dbc.Col(dbc.Card(dbc.CardBody([
                        html.H4("Unique Owners", className="card-title text-center"),
                        html.H3(unique_owners, className="values text-center")
                    ]), style={"width": "100%"}), xs=12, sm=6, md=3, className="mb-3 p-2"),
                ], className="justify-content-center"), className="cards-section container-fluid"
            )

            # Generate Charts
            pie_chart = dcc.Graph(
                figure=px.pie(df, names="ActivityEvent", title="Activity Event Distribution", hole=0.3, template="plotly_dark"),
                style={"width": "100%"}
            )

            donut_chart = dcc.Graph(
                figure=px.pie(df, names="Status", title="Status Distribution", hole=0.5, template="plotly_dark"),
                style={"width": "100%"}
            )

            charts = dbc.Row([
                dbc.Col(pie_chart, xs=12, sm=6, className="p-2"),
                dbc.Col(donut_chart, xs=12, sm=6, className="p-2")
            ], className="container-fluid justify-content-center")

            return parsed_data, cards, charts, df.to_json(date_format='iso', orient='split')

        return html.Div(), html.Div(), html.Div(), None
