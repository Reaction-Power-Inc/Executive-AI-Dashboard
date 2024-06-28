from dash import Dash, html, dcc, callback_context
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import callbacks
import process_data
from forecasting import create_forecast_layout, create_forecast_callbacks
from articles import create_articles_layout, create_articles_callbacks

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

engagements_raw, demographics_raw, followers_raw, top_posts_raw = process_data.read_data()
engagements, engagements_by_day = process_data.preprocess_engagements(engagements_raw)
demographics = process_data.preprocess_demographics(demographics_raw)
followers, total_followers, monthly_followers = process_data.preprocess_followers(followers_raw)
top_posts_preview_with_topics = process_data.preprocess_topposts(top_posts_raw)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, 'https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap'])
app.title = 'LinkedIn Analytics Dashboard'
server = app.server
# Define color scheme
colors = {
    'primary': '#0077B5',  # LinkedIn blue
    'secondary': '#00A0DC',
    'background': '#F3F6F8',
    'text': '#283E4A',
    'accent': '#7FC15E'
}

app.layout = dbc.Container([ 
    
    dbc.Row([
        dbc.Col(html.Img(src='/assets/img/Logo1.png', className='app-logo'), width=2),
        dbc.Col(html.H1("LinkedIn Analytics Dashboard", className='dashboard-title'), width=10)
    ], className='header'),

    dbc.Tabs([
        dbc.Tab(label='Overview', tab_id='overview', tabClassName='custom-tab', activeTabClassName='custom-tab-active', children=[
        dbc.Row([
            dbc.Col([
                html.H4("Select Date Range:", className='date-label'),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    min_date_allowed=engagements['Date'].min(),
                    max_date_allowed=engagements['Date'].max(),
                    initial_visible_month=engagements['Date'].max(),
                    start_date=engagements['Date'].min(),
                    end_date=engagements['Date'].max(),
                    className='date-picker'
                )
            ], width=12)
        ], className='date-range-row'),
        
        dbc.Row([
            dbc.Col(html.H2("Overview", className='section-title'), width=12)
        ]),
        
        dbc.Row([
            dbc.Col(dbc.Card(id='impressions', className='metric-card'), width=2),
            dbc.Col(dbc.Card(id='engagements', className='metric-card'), width=2),
            dbc.Col(dbc.Card(id='engagement_rate', className='metric-card'), width=2),
            dbc.Col(dbc.Card(id='emv_value', className='metric-card'), width=2),
            dbc.Col(dbc.Card([
                html.Div('Followers', className='metric-title'),
                html.Div(html.B(f"{total_followers:,.0f}", className='metric-value'))
            ], className='metric-card'), width=2)
        ], className='metrics-row'),
        
        dbc.Row([
            dbc.Col(html.H2("Follower Growth", className='section-title'), width=12)
        ]),
        
        dbc.Row([
            dbc.Col(dcc.Graph(
                figure=px.line(monthly_followers, x='YearMonth', y='New followers', 
                            title='Monthly Follower Growth',
                            labels={'YearMonth': 'Month', 'New followers': 'New Followers'},
                            color_discrete_sequence=[colors['primary']])
            ), width=12)
        ]),
        
        dbc.Row([
            dbc.Col(html.H2("Audience Demographics", className='section-title'), width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='audience-dropdown',
                    options=[
                        {'label': 'Job titles', 'value': 'Job titles'},
                        {'label': 'Locations', 'value': 'Locations'},
                        {'label': 'Industries', 'value': 'Industries'},
                        {'label': 'Seniority', 'value': 'Seniority'},
                        {'label': 'Company size', 'value': 'Company size'},
                        {'label': 'Companies', 'value': 'Companies'},
                    ],
                    value='Job titles',
                    className='audience-dropdown'
                )
            ], width=3),
            dbc.Col(dcc.Graph(id='audience-graph'), width=12)
        ]),
        
        dbc.Row([
            dbc.Col(html.H2("Engagement Analysis", className='section-title'), width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='variable-dropdown',
                    options=[
                        {'label': 'Engagements', 'value': 'Engagements'},
                        {'label': 'Impressions', 'value': 'Impressions'},
                        {'label': 'Engagement Rate', 'value': 'EngagementRate'},
                    ],
                    value='Engagements',
                    className='variable-dropdown'
                )
            ], width=3),
            dbc.Col(dcc.Graph(id='engagements-graph'), width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H3('What is the best day of week to post?', className='optimal-day-title'),
                    html.Div(id='best-day', className='optimal-day-value'),
                    html.Div(id='optimal-days', className='optimal-day-description')
                ], className='optimal-day-container')
            ], width=3),
            dbc.Col(dcc.Graph(id='optimal-graph'), width=9, ),

        ], className='optimal-day-row'),
        
        dbc.Row([
            dbc.Col(html.H2("Top Posts", className='section-title'), width=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='posts-dropdown',
                    options=[
                        {'label': 'Top engaging posts', 'value': 'Top engaging posts'},
                        {'label': 'Top posts by reach', 'value': 'Top posts by reach'},
                    ],
                    value='Top engaging posts',
                    className='posts-dropdown'
                )
            ], width=3)
        ]),
        
        dbc.Row([
            dbc.Col(
                html.Div(id='top-posts-table-container'),
                width=12
            )
        ])
        ]),
        dbc.Tab(label="Forecasting",  tab_id='forecasting', tabClassName='custom-tab', activeTabClassName='custom-tab-active', children=[
            create_forecast_layout()
        ]),
        dbc.Tab(label="Articles Analysis", tab_id='articles', tabClassName='custom-tab', activeTabClassName='custom-tab-active', children=[
            create_articles_layout()
        ])
    ], id='dashboard-tabs', active_tab='overview', className='custom-tabs'),
    
], fluid=True, className='dashboard-container')

@app.callback(
    Output('engagements', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_engagements(start_date, end_date):
    return callbacks.update_engagements(start_date, end_date)

@app.callback(
    Output('impressions', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)    
def update_impressions(start_date, end_date):
    return callbacks.update_impressions(start_date, end_date)

@app.callback(
    Output('engagement_rate', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
) 
def update_engagements_rate(start_date, end_date):
    return callbacks.update_engagements_rate(start_date, end_date)

@app.callback(
    Output('emv_value', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)   
def update_emv(start_date, end_date):   
    return callbacks.update_emv(start_date, end_date)

@app.callback(
    Output('audience-graph', 'figure'),
    [Input('audience-dropdown', 'value')]
)
def update_audience_graph(selected_variable):
    return callbacks.update_audience_graph(selected_variable)

@app.callback(
    Output('engagements-graph', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('variable-dropdown', 'value')]
)
def update_engagements_graph(start_date, end_date, selected_variable):
    return callbacks.update_engagements_graph(start_date, end_date, selected_variable)

@app.callback(
    Output('optimal-graph', 'figure'),
    Output('best-day', 'children'),
    Output('optimal-days', 'children'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('variable-dropdown', 'value')]
)
def update_optimal_graph(start_date, end_date, selected_variable):
    return callbacks.update_optimal_graph(start_date, end_date, selected_variable)

@app.callback(
    Output('top-posts-table-container', 'children'),
    [Input('posts-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')]
)
def update_top_posts_table(selected_variable, start_date, end_date):
    filtered_data = top_posts_preview_with_topics[
        (top_posts_preview_with_topics['Post publish date'] >= start_date) & 
        (top_posts_preview_with_topics['Post publish date'] <= end_date)
    ]
    
    if selected_variable == 'Top engaging posts':
        data = filtered_data.sort_values(by='Engagements', ascending=False).head(5)
    else:
        data = filtered_data.sort_values(by='Impressions', ascending=False).head(5)
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("Published on"),
            html.Th("Posts"),
            html.Th("Description"),
            html.Th("Impressions"),
            html.Th("Reactions"),
            html.Th("Post Link"),
            html.Th("Topics")
        ]))
    ]

    table_body = [html.Tbody([
        html.Tr([
            html.Td(row['Post publish date']),
            html.Td(html.Img(src=row['Thumbnail'], height=100) if row['Thumbnail'] else "No thumbnail"),
            html.Td(row['Description']),
            html.Td(f"{row['Impressions']:,}"),
            html.Td(f"{row['Engagements']:,}"),
            html.Td(html.A("View on LinkedIn", href=row['Post URL'], target="_blank")),
            html.Td(row['Topics'])
        ]) for _, row in data.iterrows()
    ])]

    return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True, className='top-posts-table')

# Create callbacks for forecasting and articles
create_forecast_callbacks(app)
create_articles_callbacks(app)

# Add CSS styles
app.css.append_css({
    "external_url": "/assets/styles.css"
})

if __name__ == '__main__':
    app.run_server(debug=True)
