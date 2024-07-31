import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from datetime import timedelta
from dash import html,dcc
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
        change_text = None
    
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
        change_text = None
    
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
     # Filter and sort the data
    data = demographics[demographics['Top Demographics'] == selected_variable].sort_values('Percentage', ascending=True)
    
    # Create the bar trace
    bar_trace = go.Bar(
        y=data['Value'],
        x=data['Percentage'],
        orientation='h',
        marker=dict(
            color='#b51a00',
            line=dict(color='#8a1500', width=1.5)
        ),
        # text=data['Percentage'].apply(lambda x: f'{x:.0f}%'),
        # textposition='outside',
        # hoverinfo='text',
        # hovertext=[f'{value}: {percentage:.1f}%' for value, percentage in zip(data['Value'], data['Percentage'])]
    )

    # Create the layout
    layout = go.Layout(
        title=dict(
            text=f'Top Audience by {selected_variable}',
            font=dict(size=24, color='#333333'),
            x=0.5,
            y=0.95
        ),
        xaxis=dict(
            title='Percentage (%)',
            # tickformat='.1f',
            ticksuffix='%',
            showgrid=True,
            gridcolor='#e0e0e0',
            zeroline=False
        ),
        yaxis=dict(
            title=selected_variable,
            automargin=True,
            tickfont=dict(size=12)
        ),
        margin=dict(l=20, r=20, t=80, b=20),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,
        bargap=0.2
    )

    # Create and return the figure
    fig = go.Figure(data=[bar_trace], layout=layout)
    
    # Add percentage labels to the end of each bar
    # for i, percentage in enumerate(data['Percentage']):
    #     fig.add_annotation(
    #         x=percentage,
    #         y=i,
    #         text=f'{percentage:.1f}%',
    #         showarrow=False,
    #         xanchor='left',
    #         xshift=10,
    #         font=dict(size=10, color='#333333')
    #     )

    return fig

def update_engagements_graph(start_date, end_date, selected_variable):
    filtered_data = engagements[(engagements['Date'] >= start_date) & (engagements['Date'] <= end_date)]
    
    # Calculate rolling average
    window = 7  # 7-day rolling average
    filtered_data[f'{selected_variable}_Rolling_Avg'] = filtered_data[selected_variable].rolling(window=window).mean()
    
    # Calculate overall trend
    filtered_data['Trend'] = filtered_data[selected_variable].rolling(window=len(filtered_data), center=True).mean()
    
    # Create subplot with two rows
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, 
                        subplot_titles=(f'{selected_variable} Over Time', 'Daily Change'))

    # Add traces for main graph
    fig.add_trace(go.Scatter(x=filtered_data['Date'], y=filtered_data[selected_variable],
                             mode='lines', name=selected_variable,
                             line=dict(color='#b51a00', width=2)), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=filtered_data['Date'], y=filtered_data[f'{selected_variable}_Rolling_Avg'],
                             mode='lines', name=f'{window}-Day Rolling Average',
                             line=dict(color='#ff6b52', width=2, dash='dash')), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=filtered_data['Date'], y=filtered_data['Trend'],
                             mode='lines', name='Overall Trend',
                             line=dict(color='#333333', width=2, dash='dot')), row=1, col=1)

    # Calculate and add daily change
    daily_change = filtered_data[selected_variable].diff()
    fig.add_trace(go.Bar(x=filtered_data['Date'], y=daily_change,
                         name='Daily Change', marker_color='#b51a00'), row=2, col=1)

    # Update layout
    fig.update_layout(
        height=800,  # Increase height to accommodate two graphs
        title_text=f"{selected_variable} Analysis",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="#333"),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text=selected_variable, row=1, col=1)
    fig.update_yaxes(title_text="Daily Change", row=2, col=1)

    # Calculate insights
    total_value = filtered_data[selected_variable].sum()
    avg_value = filtered_data[selected_variable].mean()
    max_value = filtered_data[selected_variable].max()
    max_date = filtered_data.loc[filtered_data[selected_variable].idxmax(), 'Date']
    min_value = filtered_data[selected_variable].min()
    min_date = filtered_data.loc[filtered_data[selected_variable].idxmin(), 'Date']
    
    # Add annotations with insights
    insights = f"""
    Total {selected_variable}: {total_value:,.0f}
    Average Daily {selected_variable}: {avg_value:,.0f}
    Highest {selected_variable}: {max_value:,.0f} on {max_date.strftime('%Y-%m-%d')}
    Lowest {selected_variable}: {min_value:,.0f} on {min_date.strftime('%Y-%m-%d')}
    """
    
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.01, y=0.97,
        text=insights,
        showarrow=False,
        font=dict(size=10),
        align="left",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1,
    )

    return fig

def update_optimal_graph(start_date, end_date, selected_variable):
    filtered_data = engagements[(engagements['Date'] >= start_date) & (engagements['Date'] <= end_date)]
    filtered_data['DayOfWeek'] = filtered_data['Date'].dt.day_name()
    engagements_by_day = filtered_data.groupby('DayOfWeek')[['Engagements', 'Impressions']].sum().reset_index()
    engagements_by_day['EngagementRate'] = (engagements_by_day['Engagements'] / engagements_by_day['Impressions']) * 100
    engagements_by_day['EngagementRate'] = engagements_by_day['EngagementRate'].round(2)

    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    engagements_by_day['DayOfWeek'] = pd.Categorical(engagements_by_day['DayOfWeek'], categories=days_order, ordered=True)
    engagements_by_day = engagements_by_day.sort_values('DayOfWeek')

    if selected_variable == 'Engagements':
        optimal_day = engagements_by_day.loc[engagements_by_day['Engagements'].idxmax(), 'DayOfWeek']
        second_best = engagements_by_day.loc[engagements_by_day['Engagements'].nlargest(2).index[1], 'DayOfWeek']
        fig = px.bar(engagements_by_day, x='DayOfWeek', y='Engagements', 
                     title='Engagement Distribution by Day of Week',
                     labels={'Engagements': 'Total Engagements', 'DayOfWeek': 'Day of Week'},
                     color='Engagements', color_continuous_scale='Greys')
        insight = html.Div([
            html.Strong("Optimal Posting Day for Engagement"),
            html.P(f"{optimal_day} is your best day for engagement, with {engagements_by_day.loc[engagements_by_day['DayOfWeek'] == optimal_day, 'Engagements'].values[0]:,} total engagements."),
            html.P(f"{second_best} is your second-best option, providing additional opportunities for high engagement.")
        ])
    elif selected_variable == 'Impressions':
        optimal_day = engagements_by_day.loc[engagements_by_day['Impressions'].idxmax(), 'DayOfWeek']
        second_best = engagements_by_day.loc[engagements_by_day['Impressions'].nlargest(2).index[1], 'DayOfWeek']
        fig = px.bar(engagements_by_day, x='DayOfWeek', y='Impressions', 
                     title='Impression Distribution by Day of Week',
                     labels={'Impressions': 'Total Impressions', 'DayOfWeek': 'Day of Week'},
                     color='Impressions', color_continuous_scale='Greys')
        insight = html.Div([
            html.Strong("Optimal Posting Day for Reach"),
            html.P(f"To maximize your reach, consider posting on {optimal_day}s, which historically yield {engagements_by_day.loc[engagements_by_day['DayOfWeek'] == optimal_day, 'Impressions'].values[0]:,} impressions."),
            html.P(f"{second_best} is also a strong contender for high visibility.")
        ])
    else:  # EngagementRate
        optimal_day = engagements_by_day.loc[engagements_by_day['EngagementRate'].idxmax(), 'DayOfWeek']
        second_best = engagements_by_day.loc[engagements_by_day['EngagementRate'].nlargest(2).index[1], 'DayOfWeek']
        fig = px.bar(engagements_by_day, x='DayOfWeek', y='EngagementRate', 
                     title='Engagement Rate by Day of Week',
                     labels={'EngagementRate': 'Engagement Rate (%)', 'DayOfWeek': 'Day of Week'},
                     color='EngagementRate', color_continuous_scale='Greys')
        insight = html.Div([
            html.Strong("Optimal Posting Day for Engagement Rate"),
            html.P(f"For the highest engagement rate, {optimal_day} stands out with {engagements_by_day.loc[engagements_by_day['DayOfWeek'] == optimal_day, 'EngagementRate'].values[0]:.2f}%."),
            html.P(f"{second_best} follows closely, offering another opportunity for high-quality interactions.")
        ])

    fig.update_layout(
        xaxis_title="Day of Week",
        yaxis_title=selected_variable,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial, sans-serif", size=12, color="#333"),
        margin=dict(l=40, r=40, t=40, b=40),
    )
    fig.update_xaxes(tickangle=45)

    return fig, f"Best day: {optimal_day}", insight

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
