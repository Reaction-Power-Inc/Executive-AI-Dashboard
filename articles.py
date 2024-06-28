import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import requests
import pandas as pd
import datetime
from textblob import TextBlob
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.util import ngrams
from collections import Counter
import re
import warnings

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
warnings.filterwarnings('ignore')

STOPWORDS = set(stopwords.words('english'))
NEWS_API_KEY = "f3c05b10396949ee935f4232c23d21f8"

def simple_tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

def get_sentiment(text):
    if pd.isna(text):
        return 0
    try:
        blob = TextBlob(str(text))
        return blob.sentiment.polarity
    except:
        return 0

def classify_sentiment(score):
    if score > 0.05:
        return "Positive"
    elif score < -0.05:
        return "Negative"
    else:
        return "Neutral"

EMOJI_MAPPING = {
    'Positive': '😃',
    'Neutral': '😐',
    'Negative': '😔',
}

def sentiment_to_emoji(sentiment_label):
    return EMOJI_MAPPING.get(sentiment_label, sentiment_label)

def apply_sentiment(df):
    df['sentiment_value'] = df['descriptions'].apply(get_sentiment)
    df['sentiment'] = df['sentiment_value'].apply(classify_sentiment)
    df['sentiment_emoji'] = df['sentiment'].apply(sentiment_to_emoji)
    return df.drop(['sentiment_value'], axis=1)

def fetch_articles(term, period):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=period)

    parameters = {
        "q": term,
        "sortBy": "popularity",
        "language": "en",
        "apiKey": NEWS_API_KEY,
        "from": start_date,
        "to": end_date
    }

    response = requests.get("https://newsapi.org/v2/everything", params=parameters)
    data = response.json()

    articles = data.get("articles", [])
    
    df = pd.DataFrame(articles)
    df['source'] = df['source'].apply(lambda x: x['name'] if isinstance(x, dict) else None)
    df['published_date'] = pd.to_datetime(df['publishedAt'])
    df = df.rename(columns={'title': 'titles', 'description': 'descriptions'})
    df = df[['titles', 'descriptions', 'source', 'published_date', 'url']].fillna('')
    return df

def generate_wordcloud(text):
    words = simple_tokenize(text)
    filtered_words = [word for word in words if word not in STOPWORDS and len(word) > 1]
    
    wordcloud = WordCloud(width=800, height=400, background_color='white', 
                          max_words=100, min_font_size=10).generate(' '.join(filtered_words))
    
    return wordcloud.to_image()

def get_word_frequency(texts, n=10):
    words = [word for text in texts for word in simple_tokenize(text) if word not in STOPWORDS and len(word) > 1]
    return Counter(words).most_common(n)

def get_bigrams(texts, n=10):
    bigrams = [b for text in texts for b in ngrams(simple_tokenize(text), 2) if b[0] not in STOPWORDS and b[1] not in STOPWORDS]
    return Counter(bigrams).most_common(n)

def create_articles_layout():
    return html.Div([
        html.H2("Article Insight Generator", className='section-title'),
        html.P("Uncover patterns and sentiments in recent publications.", className='section-description'),
        html.Div([
            html.Label("What topic intrigues you today?", className='input-label'),
            dcc.Input(id='keyword-input', type='text', placeholder='e.g., Renewable Energy, Space Exploration', value='Artificial Intelligence', className='text-input'),
        ], className='input-group'),
        html.Div([
            html.Label("How recent should our analysis be?", className='input-label'),
            dcc.Input(id='period-input', type='number', placeholder='Days (1-30)', value=7, min=1, max=30, className='number-input'),
            html.Span("days", className='input-suffix')
        ], className='input-group'),
        html.Button('Analyze', id='analyze-button', className='action-button'),
        html.Div(id='articles-note', className='analysis-note'),
        dcc.Loading(
            id="articles-loading",
            type="cube",
            color="#0077B5",
            children=html.Div(id='articles-output', className='output-container')
        )
    ], className='analysis-section')

def create_articles_callbacks(app):
    @app.callback(
        Output('articles-note', 'children'),
        Input('analyze-button', 'n_clicks')
    )
    def update_articles_note(n_clicks):
        if n_clicks:
            return "Analysis in progress. This may take a few moments..."
        return ""

    @app.callback(
        Output('articles-output', 'children'),
        Input('analyze-button', 'n_clicks'),
        State('keyword-input', 'value'),
        State('period-input', 'value'),
        prevent_initial_call=True
    )
    def update_articles(n_clicks, term, period):
        if n_clicks is None:
            return html.Div()

        data = fetch_articles(term, period)
        if data.empty:
            return html.Div("No articles found for the given keyword and time period.")

        data = apply_sentiment(data)

        source_counts = data['source'].value_counts().head(10)
        source_plot = dcc.Graph(
            figure=px.bar(source_counts, x=source_counts.index, y=source_counts.values, 
                          labels={'y': 'Count', 'index': 'Source'},
                          title='Top 10 Sources by Article Count')
        )

        sentiment_counts = data['sentiment'].value_counts()
        sentiment_plot = dcc.Graph(
            figure=px.pie(values=sentiment_counts.values, names=sentiment_counts.index, 
                          title='Sentiment Distribution', color_discrete_sequence=px.colors.sequential.RdBu)
        )

        text = ' '.join(data['descriptions'].dropna().astype(str))
        wordcloud_image = generate_wordcloud(text)
        wordcloud_plot = html.Img(src=wordcloud_image, style={'width': '100%'})

        word_freq = get_word_frequency(data['descriptions'].dropna())
        word_freq_plot = dcc.Graph(
            figure=px.bar(x=[w[0] for w in word_freq], y=[w[1] for w in word_freq],
                          labels={'x': 'Word', 'y': 'Frequency'},
                          title='Top 10 Most Frequent Words')
        )

        bigrams = get_bigrams(data['descriptions'].dropna())
        bigram_plot = dcc.Graph(
            figure=px.bar(x=[' '.join(b[0]) for b in bigrams], y=[b[1] for b in bigrams],
                          labels={'x': 'Bigram', 'y': 'Frequency'},
                          title='Top 10 Most Frequent Bigrams')
        )

        return html.Div([
            html.H3(f"Analyzed  articles on '{term}' for the past {period} days."),
            source_plot,
            sentiment_plot,
            wordcloud_plot,
            word_freq_plot,
            bigram_plot
        ])
