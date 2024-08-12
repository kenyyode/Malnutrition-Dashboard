import pandas as pd 
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import json, geopandas as gpd

with open('Geojson/ng.json') as f:
    nigeria_geojson = json.load(f)

# Load the GeoJSON file as a GeoDataFrame
gdf = gpd.read_file('Geojson/ng.json')

# Ensure that the GeoDataFrame has a column with state names
# Assuming the column with state names is 'name' in the GeoJSON properties
gdf['centroid'] = gdf.geometry.centroid

# Create the state_lat_lon dictionary
state_lat_lon = {row['name']: {"lat": row['centroid'].y, "lon": row['centroid'].x} for idx, row in gdf.iterrows()}

# Print the dictionary to see the centroids

# Read the airline data into pandas dataframe
df = pd.read_csv('data/here.csv', 
dtype={'States': str})

# Initialize the dash app 
app = Dash(__name__)
server = app.server 

# Create the dropdown options
state_options = [{'label': state, 'value': state} for state in df['State'].unique()]
#lga_options = [{'label': lga, 'value': lga} for lga in df['LGA'].unique()]

# Defining the app layout 
app.layout = html.Div(children=[
    # Title Section
    html.Div([html.H1("Analyzing Under-Five Malnutrition: Insights from Nigeria's IDSR Data (2013)", 
                      style={"font-size": 24, "color": "white", "text-align": "center"})], 
             style={"background-color": "#8250C4", "padding": "10px"}),
    
    # Main Content Area
    html.Div([
        # First Segment (Left Side) - Bar Graph and Line Plot
        html.Div([
            html.Div(dcc.Graph(id="bar-graph-states", config={'displayModeBar': False}, style={'height':'75vh', 'padding':"1px"}), style={'margin-bottom': "5px"}, className='graph-container'),  # Bar Chart
            html.Div(dcc.Graph(id='line-plot'), style={'margin-top': "5px"}, className='lineplot')  # Line Graph
        ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column'}),

        # Second Segment (Right Side) - Dropdowns, KPI Cards, and Map
        html.Div([
            # First Row - Dropdowns (side by side)
            html.Div([
                dcc.Dropdown(options=state_options, id='state-dropdown', style={'flex':'1'}),
                dcc.Dropdown(id='LGA-dropdown', style={'flex':'1'})
            ], style={'display': 'flex'}),
            
            # Second Row - KPI Cards (side by side)
            html.Div([
                html.Div(
                id='kpi-card-1', style={'background-color': 'white', 'flex': '1', 'padding': '10px'}, className='kpi'),
                html.Div(id='kpi-card-2', style={'background-color': 'white', 'flex': '1', 'padding': '10px'}, className='kpi'),
                html.Div(id='kpi-card-3', style={'background-color': 'white', 'flex': '1', 'padding': '10px'}, className='kpi')
            ], style={'display': 'flex', 'margin-top':'2px'}),

            # Third Row - Map
            html.Div(
                dcc.Graph(id='map'),
                style={'flex': '1', 'margin-top': '10px'}
            )
        ], style={'flex': '1', 'display': 'flex', 'flex-direction': 'column'})
    ], style={'display': 'flex', 'padding': '10px', 'background-color': '#31105D', 'gap':'10px'})
    
])

## this is a helper function to help format my KPI cards
def format_kpi(label, value):
    return html.Div([
        html.P(label, style={'font-weight': 'bold', 'margin-bottom': '2px'}),
        html.P(f"{value:,}", style={'font-size': '24px', 'margin-top': '1px'})  # Adds comma as thousand separator
    ], style={'padding': '5px'})

###  callback to update KPI cards 
@app.callback(
        Output('LGA-dropdown', 'options'),
        Input('state-dropdown', 'value')
)

def lga_options(state):
    if state is None:
        return []
    ## filter lgas based on state 
    filtered_lgas = df[df['State']==state]['LGA'].unique()
    return [{'label': lga, 'value': lga} for lga in filtered_lgas]


# Callback to update KPI cards
@app.callback(
    [Output('kpi-card-1', 'children'),
     Output('kpi-card-2', 'children'),
     Output('kpi-card-3', 'children')],
    [Input('state-dropdown', 'value'),
     Input('LGA-dropdown', 'value')]
)


def update_kpi(state, lga):
    # If neither state nor LGA is selected, return KPIs for the entire dataset
    if state is None and lga is None:
        total_cases = df['Total Cases'].sum()
        total_deaths = df['Total deaths'].sum()
        cases_investigated = df['Case Investigated Total'].sum()
        return format_kpi("Total Cases", total_cases), format_kpi("Total Deaths", total_deaths), format_kpi("Cases Investigated", cases_investigated)

    # If a state is selected but no specific LGA is selected
    if state is not None and lga is None:
        filtered_df = df[df['State'] == state]
        total_cases = filtered_df['Total Cases'].sum()
        total_deaths = filtered_df['Total deaths'].sum()
        cases_investigated = filtered_df['Case Investigated Total'].sum()
        return format_kpi("Total Cases", total_cases), format_kpi("Total Deaths", total_deaths), format_kpi("Cases Investigated", cases_investigated)

    # If both state and LGA are selected
    if state is not None and lga is not None:
        filtered_df = df[(df['State'] == state) & (df['LGA'] == lga)]
        total_cases = filtered_df['Total Cases'].sum()
        total_deaths = filtered_df['Total deaths'].sum()
        cases_investigated = filtered_df['Case Investigated Total'].sum()
        return format_kpi("Total Cases", total_cases), format_kpi("Total Deaths", total_deaths), format_kpi("Cases Investigated", cases_investigated)




@app.callback(
    Output('bar-graph-states', 'figure'),
    Input('state-dropdown', 'value')
) 
def bar_by_state(state):
    if state is None: 
        # Group by state and sort by Total Cases
        total_cases = df.groupby('State')['Total Cases'].sum().reset_index()
        total_cases_sorted = total_cases.sort_values(by='Total Cases', ascending=True)
        
        # Create the bar plot
        bar_plot = px.bar(total_cases_sorted, x='Total Cases', y='State', orientation='h')

        # Add data labels
        bar_plot.update_traces(
            text=total_cases_sorted['Total Cases'],  # Use aggregated data for labels
            textposition='outside', 
            marker_color='purple'
        )

        # Update layout to avoid label truncation
        bar_plot.update_layout(
            yaxis=dict(tickmode='linear', dtick=1),  # Ensure all labels are displayed
            margin=dict(l=150, r=20, t=40, b=20),  # Increase left margin for labels
            xaxis_title='Total Cases',
            yaxis_title='State',
            title='Total Cases By State'
        )


        
        return bar_plot
    else: 
        filtered_df = df[df['State'] == state]
        total_cases = filtered_df.groupby('LGA')['Total Cases'].sum().reset_index()
        sorted_total_cases = total_cases.sort_values(by='Total Cases', ascending=True)
        bar_plot = px.bar(sorted_total_cases, x='Total Cases', y='LGA', title='Total Cases by Local Government', orientation='h')

        # Set the bar color to purple and add data labels
        bar_plot.update_traces(
            marker_color='purple', 
            text=sorted_total_cases['Total Cases'],  # Use aggregated data for labels
            textposition='outside', 
        ) 

        bar_plot.update_layout(
            yaxis=dict(tickmode='linear', dtick=1),  # Ensure all labels are displayed
            margin=dict(l=150, r=20, t=40, b=20),  # Increase left margin for labels
            xaxis_title='Total Cases',
            yaxis_title='LGA',
        )
        return bar_plot
    
@app.callback(Output('line-plot', 'figure'),
               Input('state-dropdown', 'value'))

def line_plot(state):
    df['Month'] = pd.to_datetime(df['Month'], format='%b').apply(lambda x: x.replace(year=2013))

    if state is None:
        df_grouped = df.groupby('Month')['Total Cases'].sum().reset_index()
        sort_df = df_grouped.sort_values(by='Month', ascending=False)
        line_plot = px.line(sort_df, x='Month', y='Total Cases', markers=True)

        line_plot.update_traces(
            line_color='purple',
        )
        
        line_plot.update_layout(title='Total Cases Across the Months',
    height=270  # Adjust the height value as needed
)
        return line_plot
    
    else:
        filtered_df = df[df['State'] == state]
        grouped = filtered_df.groupby('Month').sum().reset_index()
        sorted_df = grouped.sort_values(by='Month', ascending=False)
        line_plot = px.line(sorted_df, x='Month', y='Total Cases', markers=True)

        line_plot.update_traces(
            line_color='purple',
        )

        line_plot.update_layout(title='Total Cases Across the Months',
    height=270  # Adjust the height value as needed
)

        return line_plot

@app.callback(
    Output('map', 'figure'),
    Input('state-dropdown', 'value'))
def display_choropleth(state):
    df['State'] = df['State'].str.strip()
    df_map = df.groupby('State')['Total deaths'].sum().reset_index()

    if state is None:
        fig = px.choropleth_mapbox(
        df_map, 
        geojson=nigeria_geojson, 
        featureidkey='properties.name',  # Ensure this matches your GeoJSON
        locations='State', 
        color='Total deaths',
        color_continuous_scale="Viridis",
        mapbox_style="open-street-map",  # Public style that does not require a token
        zoom=4,
        center={"lat": 9.0820, "lon": 8.6753},
        opacity=0.7,
        labels={'Total deaths': 'Total Deaths'})
        fig.update_layout(title='Total Deaths According to States')
        return fig
    else:
        filtered_df = df[df['State'] == state]
        df_map = filtered_df.groupby(['State', 'LGA'])['Total deaths'].sum().reset_index()
        fig = px.choropleth_mapbox(
        df_map, 
        geojson=nigeria_geojson, 
        featureidkey='properties.name',  # Ensure this matches your GeoJSON
        locations='State', 
        color='Total deaths',
        color_continuous_scale="Viridis",
        mapbox_style="open-street-map",  # Public style that does not require a token
        zoom=7,
        center={"lat": state_lat_lon[state]['lat'], "lon": state_lat_lon[state]['lon']}, #{"lat": 9.0820, "lon": 8.6753},
        opacity=0.7,
        labels={'Total deaths': 'Total Deaths'})

        # Update layout with a dynamic title and custom colorbar
        fig.update_layout(
            title=f'Total Deaths in {state} State',
            )
        return fig

# Run app 
if __name__ == "__main__":
    app.run_server(debug=True)
