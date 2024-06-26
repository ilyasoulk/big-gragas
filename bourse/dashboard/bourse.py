import dash
from dash import dcc
from dash import html
import dash.dependencies as ddep
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import sqlalchemy
import logging

logging.basicConfig(level=logging.DEBUG,  # Set minimum log level to DEBUG
                    format='%(asctime)s - %(levelname)s - %(message)s',  # Include timestamp, log level, and message
                    handlers=[
                        logging.FileHandler("debug.log"),  # Log to a file
                        logging.StreamHandler()  # Log to standard output (console)
                    ])

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

DATABASE_URI = 'timescaledb://ricou:monmdp@db:5432/bourse'    # inside docker
# DATABASE_URI = 'timescaledb://ricou:monmdp@localhost:5432/bourse'  # outisde docker
engine = sqlalchemy.create_engine(DATABASE_URI)

companies_df = pd.read_sql_query("SELECT name FROM companies;", engine)
companies = companies_df['name'].to_numpy()

app = dash.Dash(__name__,  title="Bourse", suppress_callback_exceptions=True) # , external_stylesheets=external_stylesheets)
server = app.server
app.layout = html.Div([
        html.H2(f"Welcome to our project", style={"textAlign": "center", "color": "#fff"} ),
        html.Div([
            dcc.RadioItems(
                id="chandelier",
                options=[
                    {"label": "Ligne", "value": "Ligne"},
                    {"label": "Chandelier", "value": "Chandelier"},
                ],
                value="Ligne",
                style={"flex": 1, "background-color": "#d1c4e9", "border-radius": "5px", "padding": "10px"}
            ),

            dcc.DatePickerRange(
                id="date-range",
                min_date_allowed=pd.to_datetime("2019-01-01"),
                max_date_allowed=pd.to_datetime("today"),
                initial_visible_month=pd.to_datetime("today"),
                start_date=pd.to_datetime("2020-01-01"),
                end_date=pd.to_datetime("today"),
                display_format="YYYY-MM-DD",
                clearable=True,
                style={"flex": 1, "background-color": "#d1c4e9", "border-radius": "5px", "padding": "10px"}
            ),
            dcc.Dropdown(
                id="checklist",
                options=companies,
                value=companies[:1],
                multi=True,
                style={"flex": 1, "background-color": "#d1c4e9", "border-radius": "5px", "padding": "10px"}
            ), 
            dcc.Checklist(
                id="markets",
                options=["amsterdam", "bruxelle", "paris"],
                value=['bruxelle', "amsterdam", "paris"],  
                inline=True,
                style={
                    "flex": 1, "background-color": "#d1c4e9", "border-radius": "5px", "padding": "10px", "align-items": "center", "display": "flex", 
                },
            )
            ],
            style={"display": "flex", "flex-direction": "row", "row-gap": "10px", "column-gap": "10px", "margin-bottom": "20px"}
        ),
        html.Div(id="graphs"),
        html.Div([
            html.H2(f"Query:", style={"textAlign": "center", "color": "#fff"} ),
            html.Div([
                dcc.Textarea(
                    id='sql-query',
                    value='',
                    style={'width': '100%', 'height': 100},
                ),
                html.Button('Execute', id='execute-query', n_clicks=0)],
                style={"display":"flex", "flex-direction": "row", "gap": "10px" }
            ),
            html.Div(
                id='query-result',
                style={"background-color": "white", "border-radius": "5px", "padding": "10px" }
            )],
            style={"display": "flex", "flex-direction": "column", "row-gap": "10px", "column-gap": "10px", "margin-bottom": "20px", "padding": "20px"}
        ),


    ],
    style={
        "background": "linear-gradient(to bottom, #471463, #1f072b)",
        "padding": "20px",  # Remplissage autour du contenu
        "min-height": "100vh",
    }
)

@app.callback(ddep.Output('graphs', 'children'),
               [
                ddep.Input('chandelier', 'value'),
                ddep.Input('checklist', 'value'),
                ddep.Input('markets', 'value'),
                ddep.Input('date-range', 'start_date'),
                ddep.Input('date-range', 'end_date'),
            ],
            ddep.State('sql-query', 'value')
)
def update_graph(style, companies, markets, start_date, end_date, n_clicks, query = ""):
        graphs = []
        if style == "Chandelier":

            for company in companies:
                if not query:
                    current_query = f"""SELECT date, open, close, high, low, volume FROM daystocks ds
                                JOIN companies c ON ds.cid = c.id
                                JOIN markets m ON c.mid = m.id
                                WHERE c.name = '{company}'"""

                    if markets:
                        markets_condition = "('" + "', '".join(markets) + "')"
                        current_query += f" AND m.alias IN {markets_condition}"

                    if start_date and end_date:
                        current_query += f" AND date BETWEEN '{start_date}' AND '{end_date}';"
                    else:
                        current_query += ";"
                else:
                    current_query = query

                df = pd.read_sql_query(current_query, engine)

                df['date'] = pd.to_datetime(df['date'])
                df.sort_values(by='date', inplace=True)

                ma_size = 10
                bol_size = 2

                df['bollinger_bands'] = df['close'].rolling(ma_size).mean()

                df['upper_band'] = df['bollinger_bands'] + df['close'].rolling(ma_size).std() * bol_size
                df['lower_band'] = df['bollinger_bands'] - df['close'].rolling(ma_size).std() * bol_size

                candlestick = {
                    'x': df['date'],
                    'open': df['open'],
                    'close': df['close'],
                    'high': df['high'],
                    'low': df['low'],
                    'type': 'candlestick',
                    'name': f'Candlestick - {company}',
                    'legendgroup': company,
                    'increasing': {'line': {'color': '#B7C9E2'}},
                    'decreasing': {'line': {'color': '#8E9CB0'}}
                }

                bollinger_traces = []
                for parameter, color in zip(['bollinger_bands', 'lower_band', 'upper_band'], ['#ADD8E6', '#FF7F7F', '#90EE90']):
                    bollinger_traces.append(go.Scatter(x=df['date'],
                                                    y=df[parameter],
                                                    showlegend=True,
                                                    name=f"{parameter.replace('_', ' ').title()} - {company}",
                                                    line_color=color,
                                                    mode='lines',
                                                    line={'dash': 'dash'},
                                                    marker_line_width=2,
                                                    marker_size=10,
                                                    opacity=0.8))

                volume_trace = go.Bar(x=df['date'],
                              y=df['volume'],
                              name=f'Volume - {company}',
                              marker_color='rgba(0, 0, 255, 0.5)')

                graphs.append(dcc.Graph(
                    id=f"{company}-Candlestick",
                    figure={
                        'data': [candlestick] + bollinger_traces,
                        'layout': {
                            'legend': {'x': 0},
                            'title': f'Candlestick - {company}',
                            'xaxis': {'rangeslider': {'visible': True}}
                        }
                    },
                ))

                graphs.append(dcc.Graph(
                    id=f"{company}-Volume",
                    figure={
                        'data': [volume_trace],
                        'layout': {
                            'legend': {'x': 0},
                            'title': f'Volume - {company}',
                            'xaxis': {'rangeslider': {'visible': True}}
                        }
                    },
                ))

        else:


            for company in companies:
                current_query = query if query else f"""SELECT s.date, s.value, c.name
                        FROM stocks s
                        JOIN companies c ON s.cid = c.id
                        JOIN markets m ON c.mid = m.id
                        WHERE c.name = '{company}'"""

                if markets:
                    markets_condition = "('" + "', '".join(markets) + "')"
                    current_query += f" AND m.alias IN {markets_condition};"
                else:
                    current_query += ";"

                df = pd.read_sql_query(current_query, engine)

                if df.empty:
                    logging.info(f"Current query : {current_query}")

                df['date'] = pd.to_datetime(df['date'])
                df.sort_values(by='date', inplace=True)
                fig = px.line(df, x='date', y='value', color='name')
                fig.update_layout(title=company,
                    xaxis_title='Date',
                    yaxis_title='Price',
                )
                graphs.append(dcc.Graph(
                    id=f'{company} - Line',
                    figure=fig,
                ))

        return graphs



@app.callback( ddep.Output('query-result', 'children'),
               ddep.Input('execute-query', 'n_clicks'),
               ddep.State('sql-query', 'value'),
             )
def run_query(n_clicks, query):
    if n_clicks > 0:
        try:
            result_df = pd.read_sql_query(query, engine)
            return html.Pre(result_df.to_string())
        except Exception as e:
            return html.Pre(str(e))
    return "Enter a query and press execute."
            


if __name__ == '__main__':
    app.run(debug=True)


