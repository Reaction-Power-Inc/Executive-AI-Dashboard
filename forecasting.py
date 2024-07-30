import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from pytrends.request import TrendReq
import pandas as pd
import plotly.graph_objs as go
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import plotly.express as px
from datetime import datetime, timedelta
import time
import random
import warnings
warnings.filterwarnings('ignore')

def get_pytrends():
    return TrendReq(hl='en-US', tz=360, timeout=(10, 25), retries=2, backoff_factor=0.1)

def fetch_interest_over_time(_pytrends, search_term, timeframe='today 5-y', retries=5):
    for attempt in range(retries):
        try:
            # Initialize pytrends with backoff_factor
            pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25), retries=2, backoff_factor=0.1)
            
            # Add a delay before making the request
            time.sleep(random.uniform(1, 5))  # Random delay between 1 and 5 seconds
            
            # Build payload
            pytrends.build_payload(kw_list=[search_term], timeframe=timeframe)
            
            # Get interest over time
            data = pytrends.interest_over_time()
            if data.empty:
                return None

            return data
        
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                # Calculate exponential backoff wait time
                wait_time = (2 ** attempt) + random.random()
                print(f"Waiting for {wait_time:.2f} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Unable to fetch data.")
                return None

def plot_interest_over_time(df, search_term):
    fig = px.line(df, x=df.index, y=search_term, title=f'{search_term} Interest Over Time')
    fig.update_layout(xaxis_title="Date", yaxis_title="Interest", hovermode="x unified")
    return fig

def prepare_data_for_prophet(df, search_term):
    df_prophet = df.reset_index().rename(columns={'date': 'ds', search_term: 'y'})
    df_prophet['ds'] = pd.to_datetime(df_prophet['ds'])
    return df_prophet

def train_and_forecast(df, periods=365):
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False,
                    changepoint_prior_scale=0.05, seasonality_prior_scale=10)
    model.fit(df)
    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    return model, forecast

def plot_forecast(model, forecast):
    fig = plot_plotly(model, forecast)
    fig.update_layout(title='Forecast of Interest Over Time', xaxis_title='Date', yaxis_title='Interest')
    return fig

def plot_trend_components(model, forecast):
    return plot_components_plotly(model, forecast)

def calculate_trend_change(forecast, days=30):
    recent_trend = forecast['trend'].iloc[-1] - forecast['trend'].iloc[-days]
    percent_change = (recent_trend / forecast['trend'].iloc[-days]) * 100
    return percent_change

def get_related_topics(pytrends, search_term):
    pytrends.build_payload(kw_list=[search_term])
    return pytrends.related_topics()[search_term]

def plot_related_topics(related_topics):
    if 'top' in related_topics:
        top_topics = related_topics['top'].head(10)
        fig = px.bar(top_topics, x='topic_title', y='value', title='Top Related Topics')
        fig.update_layout(xaxis_title="Topic", yaxis_title="Value", xaxis={'categoryorder':'total descending'})
        return fig
    return None

def create_forecast_layout():
    return html.Div([
        html.H2('Trend Explorer: Uncover Future Insights', className='section-title'),
        html.P("Dive into the world of trending topics and predict their future trajectory.", className='section-description'),
        html.Div([
            html.Label("What's on your mind? Enter a topic to explore:", className='input-label'),
            dcc.Input(id='search-term', type='text', placeholder='e.g., Artificial Intelligence, Climate Change', value='', className='text-input'),
        ], className='input-group'),
        html.Div([
            html.Label("How far back should we look?", className='input-label'),
            dcc.Dropdown(
                id='timeframe-dropdown',
                options=[
                    {'label': 'Last 5 years - For long-term patterns', 'value': 'today 5-y'},
                    {'label': 'Past year - Recent yearly trends', 'value': 'today 12-m'},
                    {'label': 'Last 3 months - Quarterly snapshot', 'value': 'today 3-m'},
                    {'label': 'Past month - Recent hot topics', 'value': 'today 1-m'}
                ],
                value='today 5-y',
                className='dropdown-input'
            ),
        ], className='input-group'),
        html.Button('Analyze', id='forecast-button', className='action-button'),
        html.Div(id='forecast-note', className='analysis-note'),
        dcc.Loading(
            id="forecast-loading",
            type="cube",
            color="#0077B5",
            children=html.Div(id='forecast-output', className='output-container')
        )
    ], className='analysis-section')

def create_forecast_callbacks(app):
    @app.callback(
        Output('forecast-note', 'children'),
        Input('forecast-button', 'n_clicks')
    )
    def update_forecast_note(n_clicks):
        if n_clicks:
            return "Analysis in progress. This may take a few moments..."
        return ""
    
    @app.callback(
        Output('forecast-output', 'children'),
        Input('forecast-button', 'n_clicks'),
        State('search-term', 'value'),
        State('timeframe-dropdown', 'value'),
        prevent_initial_call=True
    )
    def update_forecast(n_clicks, search_term, timeframe):
        if n_clicks is None:
            return html.Div()

        pytrends = get_pytrends()
        df = fetch_interest_over_time(pytrends, search_term, timeframe)

        if df is None or df.empty:
            return html.Div("No data available for the given search term and timeframe.")

        historical_trend = dcc.Graph(figure=plot_interest_over_time(df, search_term))

        df_prophet = prepare_data_for_prophet(df, search_term)
        model, forecast = train_and_forecast(df_prophet)

        forecast_plot = dcc.Graph(figure=plot_forecast(model, forecast))
        components_plot = dcc.Graph(figure=plot_trend_components(model, forecast))

        recent_trend = calculate_trend_change(forecast)
        future_trend = calculate_trend_change(forecast, days=365)

        if 'yearly' in forecast.columns:
            peak_month = forecast.groupby(forecast['ds'].dt.month)['yearly'].mean().idxmax()

        if 'weekly' in forecast.columns:
            peak_day = forecast.groupby(forecast['ds'].dt.dayofweek)['weekly'].mean().idxmax()
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        insights = html.Div([
            html.H3('Key Insights'),
            html.Ul([
                html.Li(f"The trend for '{search_term}' has changed by {recent_trend:.2f}% over the last 30 days."),
                html.Li(f"The model predicts a {future_trend:.2f}% change in interest over the next year."),
                html.Li(f"Interest typically peaks in month {peak_month}."),
                html.Li(f" Interest is usually highest on {days[peak_day]}s."),

            ])
        ])

        related_topics = get_related_topics(pytrends, search_term)
        related_topics_plot = dcc.Graph(figure=plot_related_topics(related_topics)) if plot_related_topics(related_topics) else html.Div("No related topics data available.")

        return html.Div([
            historical_trend,
            forecast_plot,
            components_plot,
            insights,
            related_topics_plot
        ])