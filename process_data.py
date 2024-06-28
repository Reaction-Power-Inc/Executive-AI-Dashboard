import pandas as pd 
from openai import OpenAI
import requests
from bs4 import BeautifulSoup


client = OpenAI(api_key="")

def read_data(file_path='data/linkedin.xlsx'):
    """
    Reads data from an Excel file and returns dataframes for engagements,
    demographics, followers, and top posts.
    
    Parameters:
    file_path (str): The path to the Excel file.
    
    Returns:
    tuple: DataFrames for engagements, demographics, followers, and top posts.
    """
    try:
        fp = pd.ExcelFile(file_path)
        sheet_names = fp.sheet_names
        data = {sheet_name: pd.read_excel(fp, sheet_name, engine='openpyxl') for sheet_name in sheet_names}
        
        engagements = data.get('ENGAGEMENT')
        demographics = data.get('DEMOGRAPHICS')
        followers = data.get('FOLLOWERS')
        top_posts = data.get('TOP POSTS')
        
        return engagements, demographics, followers, top_posts
    except Exception as e:
        print(f"Error reading data: {e}")
        return None, None, None, None

def preprocess_engagements(engagements):
    """
    Preprocesses the engagements data.
    
    Parameters:
    engagements (DataFrame): The engagements data.
    
    Returns:
    tuple: Processed engagements DataFrame and aggregated data by day of the week.
    """
    if engagements is not None:
        try:
            engagements['Date'] = pd.to_datetime(engagements['Date'])
            engagements['DayOfWeek'] = engagements['Date'].dt.day_name()
            engagements['EngagementRate'] = (engagements['Engagements'] / engagements['Impressions']) * 100
            engagements['EngagementRate'] = engagements['EngagementRate'].round(2)

            engagements_by_day = engagements.groupby('DayOfWeek')[['Engagements', 'Impressions']].sum().reset_index()
            engagements_by_day['EngagementRate'] = (engagements_by_day['Engagements'] / engagements_by_day['Impressions']) * 100
            engagements_by_day['EngagementRate'] = engagements_by_day['EngagementRate'].round(2)
            engagements_by_day = engagements_by_day.sort_values(by='Engagements', ascending=False).reset_index(drop=True)
            
            return engagements, engagements_by_day
        except Exception as e:
            print(f"Error processing engagement data: {e}")
            return None, None
    else:
        print("No data provided.")
        return None, None
    
def preprocess_demographics(demographics):
    """
    Preprocesses the demographics data.
    
    Parameters:
    demographics (DataFrame): The demographics data.
    
    Returns:
    DataFrame: Processed demographics data.
    """
    if demographics is not None:
        try:
            demographics = demographics[demographics['Percentage'] != '< 1%'].copy()
            demographics.loc[:, 'Percentage'] = pd.to_numeric(demographics['Percentage'], errors='coerce') 
            return demographics
        except Exception as e:
            print(f"Error processing demographics data: {e}")
            return None
    else:
        print("No data provided.")
        return None

def preprocess_followers(followers):
    """
    Preprocesses the followers data.
    
    Parameters:
    followers (DataFrame): The followers data.
    
    Returns:
    tuple: Processed followers DataFrame and total followers column name.
    """
    if followers is not None:
        try:
            total_followers = followers.columns[1]
            new_header = followers.iloc[1]
            followers.columns = new_header
            followers = followers.drop([0, 1]).reset_index(drop=True)
            followers['Date'] = pd.to_datetime(followers['Date'])
            followers['YearMonth'] = followers['Date'].dt.to_period('M')
            followers['YearMonth'] = followers['YearMonth'].astype(str)
            monthly_followers = followers.groupby('YearMonth')['New followers'].sum().reset_index()
            return followers, total_followers, monthly_followers
        except Exception as e:
            print(f"Error processing followers data: {e}")
            return None, None
    else:
        print("No data provided.")
        return None, None

def get_completion(prompt, model="gpt-3.5-turbo"):
    """
    Get a completion from the OpenAI API based on the given prompt.
    """
    messages = [
        {"role": "system", "content": "You are a topic modelling system"},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content

def get_post_info(url):
    """
    Fetches the Open Graph meta tags (title, description, and image) from a given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('meta', property='og:title')
        description = soup.find('meta', property='og:description')
        image = soup.find('meta', property='og:image')
        
        return (
            title['content'] if title else "Title not found",
            description['content'] if description else "Description not found",
            image['content'] if image else None
        )
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None, None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None, None

def suggest_topics(top_posts_preview):
    """
    Suggests topics for social media posts based on their descriptions.
    """
    for index, row in top_posts_preview.iterrows():
        prompt = f"""
        Suggest up to five single or two-word topics for a social media post
        related to {row['Description']}. Print them in one line separated by a comma.
        """
        response = get_completion(prompt)
        top_posts_preview.at[index, 'Topics'] = response
    return top_posts_preview

def preprocess_topposts(top_posts,  csv_path='data/top_posts_with_topics.csv'):
    """
    Preprocesses the top posts  data.
    
    Parameters:
    top_posts (DataFrame): The top posys data.
    
    Returns:
    tuple: Processed top posts DataFrame with topics and thumbnails.
    """
   
    try:
        # Try to load the preprocessed data from the CSV file if it exists
        top_posts_preview_with_topics = pd.read_csv(csv_path)
        return top_posts_preview_with_topics
    except FileNotFoundError:
        print(f"{csv_path} not found, processing top posts data from scratch.")
    except Exception as e:
        print(f"Error loading preprocessed top posts data: {e}")
        return None
    
    if top_posts is not None:
        try:
            # Rename columns based on the second row and drop unnecessary rows
            new_header = top_posts.iloc[1]
            top_posts.columns = new_header
            top_posts = top_posts.drop([0, 1]).reset_index(drop=True)
            top_posts = top_posts.dropna(axis=1, how='all')
            
            # Split into engagements and impressions data
            top_posts_engagements = top_posts.iloc[:, :3]
            top_posts_impressions = top_posts.iloc[:, 3:]

            # Merge the data on 'Post URL'
            merged_data = pd.merge(
                top_posts_engagements, 
                top_posts_impressions, 
                on='Post URL', 
                how='inner'
            )
            merged_data = merged_data.rename(columns={
                'Engagements_x': 'Engagements',
                'Engagements_y': 'Impressions',
                'Post publish date_x': 'Post publish date'
            })
            merged_data = merged_data.drop(columns=['Post publish date_y'])

            # Get post information for each URL
            titles, descriptions, thumbnails = [], [], []
            for url in merged_data['Post URL']:
                title, description, thumbnail_url = get_post_info(url)
                titles.append(title)
                descriptions.append(description)
                thumbnails.append(thumbnail_url)

            # Create a DataFrame for the post preview information
            data_post_preview = pd.DataFrame({
                'Title': titles,
                'Description': descriptions,
                'Thumbnail': thumbnails
            })

            # Concatenate the preview information with the merged data
            top_posts_preview = pd.concat([merged_data, data_post_preview], axis=1)

            # Suggest topics for the posts
            top_posts_preview_with_topics = suggest_topics(top_posts_preview)
            
            return top_posts_preview_with_topics

        except Exception as e:
            print(f"Error processing top posts: {e}")
            return None
    else:
        print("No valid files uploaded or error occurred during processing.")
        return None
    
def calculate_percentage_change(current_value, previous_value):
    """
    Calculate the percentage change between two values.

    Args:
        current_value (float or int): The current value.
        previous_value (float or int): The previous value.

    Returns:
        float: The percentage change rounded to two decimal places.
               Returns float('inf') if previous_value is zero, indicating an infinite percentage increase.
               Raises ValueError for invalid inputs.
    """
    if previous_value != 0:
        return round(((current_value - previous_value) / previous_value) * 100, 2)
    else:
        return 0
