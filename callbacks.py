import pandas as pd
from datetime import timedelta
from dash import html
import dash_bootstrap_components as dbc
import plotly.express as px
import process_data
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

engagements_raw, demographics_raw, followers_raw, top_posts_raw = process_data.read_data()
engagements, engagements_by_day = process_data.preprocess_engagements(engagements_raw)
demographics = process_data.preprocess_demographics(demographics_raw)
followers, total_followers,monthly_followers = process_data.preprocess_followers(followers_raw)
top_posts_preview_with_topics = process_data.preprocess_topposts(top_posts_raw)

def update_engagements(start_date, end_date):

    filtered_engagements = engagements[(engagements['Date'] >= start_date) & (engagements['Date'] <= end_date)]
    total_engagements = filtered_engagements['Engagements'].sum()
    
    selected_period_start = pd.to_datetime(start_date)
    selected_period_end = pd.to_datetime(end_date)
    previous_period_start = selected_period_start - (selected_period_end - selected_period_start)
    previous_period_end = selected_period_start - timedelta(days=1)
    
    previous_period_engagements = engagements[(engagements['Date'] >= previous_period_start) & (engagements['Date'] <= previous_period_end)]
    previous_period_total_engagements = previous_period_engagements['Engagements'].sum()
    
    percentage_change = process_data.calculate_percentage_change(total_engagements, previous_period_total_engagements)
    
    if percentage_change < 0:
        change_class = 'percentage-change-negative'
        change_text = f"{percentage_change}%"
    elif percentage_change > 0:
        change_class = 'percentage-change-positive'
        change_text = f"{percentage_change}%"
    else:
        change_class = 'percentage-change-no-change'
        change_text = 'No change'
    
    return [
        'Engagements ',
        html.Br(),
        html.B(f"{total_engagements:,.0f}", className='metric-value'),
        html.Br(),
        html.P(change_text, className=f'percentage-change {change_class}')
    ]
    
def update_impressions(start_date, end_date):
    filtered_impressions = engagements[(engagements['Date'] >= start_date) & (engagements['Date'] <= end_date)]
    total_impressions = filtered_impressions['Impressions'].sum()

    selected_period_start = pd.to_datetime(start_date)
    selected_period_end = pd.to_datetime(end_date)
    previous_period_start = selected_period_start - (selected_period_end - selected_period_start)
    previous_period_end = selected_period_start - timedelta(days=1)  # End 1 day before the selected period start
    
    previous_period_impressions = engagements[(engagements['Date'] >= previous_period_start) & (engagements['Date'] <= previous_period_end)]
    previous_period_total_impressions = previous_period_impressions['Impressions'].sum()
    
    percentage_change = process_data.calculate_percentage_change(total_impressions, previous_period_total_impressions)

    if percentage_change < 0:
        change_class = 'percentage-change-negative'
        change_text = f"{percentage_change}%"
    elif percentage_change > 0:
        change_class = 'percentage-change-positive'
        change_text = f"{percentage_change}%"
    else:
        change_class = 'percentage-change-no-change'
        change_text = 'No change'
    
    return [
        'Impressions ',
        html.Br(),
        html.B(f"{total_impressions:,.0f}", className='metric-value'),
        html.Br(),
        html.P(change_text, className=f'percentage-change {change_class}')
    ]

def update_engagements_rate(start_date, end_date):
    filtered_impressions = engagements[(engagements['Date'] >= start_date) & (engagements['Date'] <= end_date)]
    total_impressions = filtered_impressions['Impressions'].sum()
    total_engagements = filtered_impressions['Engagements'].sum()
    engagement_rate = (total_engagements / total_impressions)*100
    return ['Engagement Rate', html.Br(), html.B("{:,.2f}%".format(engagement_rate), className='metric-value')]

 
def update_emv(start_date, end_date):
    filtered_impressions = engagements[(engagements['Date'] >= start_date) & (engagements['Date'] <= end_date)]
    total_impressions = filtered_impressions['Impressions'].sum()
    total_engagements = filtered_impressions['Engagements'].sum()
    engagement_rate = total_engagements / total_impressions
    emv = engagement_rate*total_impressions*6.59
    return ['Earned Media Value', html.Br(), html.B("${:,.0f}".format(emv),className='metric-value')]

def update_audience_graph(selected_variable):
    fig = px.bar(demographics[demographics['Top Demographics'] == selected_variable], x='Percentage', y='Value', orientation='h', title=f'Top audience by {selected_variable}', labels={'Percentage': 'Percentage (%)', 'Value': 'Top Values'},color_discrete_sequence=['#b51a00']).update_layout(plot_bgcolor='white', paper_bgcolor='white')
    return fig

def update_engagements_graph(start_date, end_date, selected_variable):
    filtered_data = engagements[(engagements['Date'] >= start_date) & (engagements['Date'] <= end_date)]
    fig = px.line(filtered_data, x='Date', y=selected_variable, color_discrete_sequence=['#b51a00'])
    return fig

def update_optimal_graph(start_date, end_date, selected_variable):
    filtered_data = engagements[(engagements['Date'] >= start_date) & (engagements['Date'] <= end_date)]
    filtered_data['DayOfWeek'] = filtered_data['Date'].dt.day_name()
    engagements_by_day = filtered_data.groupby('DayOfWeek')[['Engagements','Impressions']].sum().reset_index()
    engagements_by_day['EngagementRate'] = (engagements_by_day['Engagements'] / engagements_by_day['Impressions']) * 100
    engagements_by_day['EngagementRate'] = engagements_by_day['EngagementRate'].map("{:.2f}".format)
    if selected_variable == 'Engagements':
        engagements_by_day = engagements_by_day.sort_values(by='Engagements', ascending=False).reset_index(drop=True)
        optimal_day = engagements_by_day.loc[0, 'DayOfWeek']
        fig = px.pie(engagements_by_day, names='DayOfWeek', values=selected_variable, color_discrete_sequence=['#b51a00']).update_layout(paper_bgcolor='#F3F6F8', plot_bgcolor='#F3F6F8')
        return (fig, f"Engagement", ["With a total of ", html.B(engagements_by_day.loc[0, 'Engagements']), " reactions, the best day to post on LinkedIn to maximize your engagement is ", html.B(optimal_day), ". The second best day is ", html.B(engagements_by_day.loc[1, 'DayOfWeek'])])
    elif selected_variable == 'Impressions':
        engagements_by_day = engagements_by_day.sort_values(by='Impressions', ascending=False).reset_index(drop=True)
        optimal_day = engagements_by_day.loc[0, 'DayOfWeek']
        fig = px.pie(engagements_by_day, names='DayOfWeek', values=selected_variable, color_discrete_sequence=['#b51a00']).update_layout(paper_bgcolor='#F3F6F8', plot_bgcolor='#F3F6F8')
        return (fig, f"Reach", ["The best day to maximize the reach of your LinkedIn posts is ", html.B(optimal_day), " with total of ", html.B(engagements_by_day.loc[0, 'Impressions']), " impressions. The second best day is", html.B(engagements_by_day.loc[1, 'DayOfWeek']), "."])
    else:
        engagements_by_day = engagements_by_day.sort_values(by='EngagementRate', ascending=False).reset_index(drop=True)
        optimal_day = engagements_by_day.loc[0, 'DayOfWeek']
        fig = px.pie(engagements_by_day, names='DayOfWeek', values=selected_variable, color_discrete_sequence=['#b51a00']).update_layout(paper_bgcolor='#F3F6F8', plot_bgcolor='#F3F6F8')
        return (fig, f"Engagement rate", [ "Increase your engagement rate on your LinkedIn posts by posting on ", html.B(optimal_day), " with (", html.B(engagements_by_day.loc[0, 'EngagementRate']), "%) engagement rate."])


def get_table_children(start_date, end_date, selected_variable):
    filtered_data = top_posts_preview_with_topics[(top_posts_preview_with_topics['Post publish date'] >= start_date) & (top_posts_preview_with_topics['Post publish date'] <= end_date)]
    if selected_variable == 'Top engaging posts':
        data = filtered_data.sort_values(by='Engagements', ascending=False).reset_index(drop=True).head()
    else:
        data = filtered_data.sort_values(by='Impressions', ascending=False).reset_index(drop=True).head(10)
    children = [
        html.Tr([
            html.Th("Published on"),
            html.Th("Posts"),
            html.Th(""),
            html.Th("Impressions"),
            html.Th("Reactions"),
            html.Th("Post Link"),
            html.Th("Topics"),
        ], style={'background-color': 'lightgray'}),  # Header row styling
    ] + [
        html.Tr([
            html.Td(row['Post publish date'], style={'width':'200px', 'margin-left': '10px'}),
            html.Td(html.Img(src=row['Thumbnail'], height=100) if row['Thumbnail'] else html.P('Thumbnail not found.')),
            html.Td(row['Description'],style={'width':'800px', 'margin-left': '10px'}),
            html.Td(row['Impressions'], style={'width':'200px', 'margin-left': '10px'}),
            html.Td(row['Engagements'],style={'width':'200px',}),
            html.Td(html.A("View on LI", href=row['Post URL']), style={'width':'200px',}),
            html.Td(row['Topics'],style={'width':'300px',}),
        ], style={'border-bottom': '1px solid gray', 'padding': '10px','width':'1700px'}) for _, row in data.iterrows()
    ]
    return children
