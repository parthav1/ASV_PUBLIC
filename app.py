import dash
import pandas as pd
from dash import dcc, html
from ASV_New import ASV
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import webbrowser
from threading import Timer

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
all_data = pd.DataFrame()
obj = ASV()   
graph_data = obj.create_domain_dataframe()
    
figure = obj.plot_county(graph_data)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
    }
}

# Define the layout of the Dash app
app.layout = html.Div(style={'display': 'grid', 'gridTemplateColumns': '3fr 1fr', 'height': '100vh'}, children=[
    dcc.Graph(id='chloropeth_chart', figure=figure),  # Graph component for the choropleth chart
    html.Div(id="debug"),  # Container for dynamic content based on interactions
])

# Define a callback to handle interactions with the choropleth chart
@app.callback(
    Output("debug", "children"),  # Output to the "debug" Div
    Input('chloropeth_chart', 'clickData'))  # Input from the chart click event
def display_clicked_data(data):
    if data:
        # Extract county and state information from the click data
        county = data['points'][0]["customdata"][0]
        state = data['points'][0]["customdata"][2]
        print(str(county) + ', ' + str(state))

        # Filter the record corresponding to the clicked area
        record = obj.all_domain_data[(obj.all_domain_data["County"] == county) & (obj.all_domain_data["state_name"] == state)]
        
        headers = ['Number of Domains', 'Number of Ips', 'Number of Open Ports', 'DNS MDNS', 'POSTGRES MSSQL MYSQL', 
                   'TELNET FTP TFTP RDP SSH', 'NETBIOS SMB', 'Severity']
        values = [record[col] for col in headers]

        fig = go.Figure(data=[go.Table(
            columnorder = [1,2],
            columnwidth = [120, 25],
            header = dict(
                values = ['Category', 'Value'],
                line_color='darkslategray',
                fill_color='royalblue',
                align='center',
                font=dict(color='white', size=12),
                height=37
            ),
            cells=dict(
                values=[headers, values],
                line_color='darkslategray',
                fill=dict(color=['white', 'lightgray']),
                align='center',
                font_size=12,
                height=30)
                )
            ])
        
        fig.update_layout(height=800, title_text=(str(county) + ', ' + str(state)), title_font=dict(size=15), title_x=0.5, title_y=0.9)

        # Return the table figure wrapped in a Div for display
        return html.Div(style={'display': 'block', 'overflowY': 'auto', 'overflowX': 'auto'}, children=dcc.Graph(id='basic-interactions', figure=fig))
    else:
        return ""
    
def open_browser():
    webbrowser.open_new('http://127.0.0.1:8050')

if __name__ == '__main__':
    Timer(1, open_browser).start()
    app.run_server()
    