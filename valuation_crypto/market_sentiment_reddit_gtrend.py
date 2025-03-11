import time
import praw
from textblob import TextBlob
from apikey import client_id, client_secret, user_agent
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError
import logging
import random

# Initialize Reddit API
reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

# Initialize Google Trends API
pytrends = TrendReq(hl='en-US', tz=360)

def fetch_mentions_and_sentiment_reddit(crypto_name, crypto_symbol, subreddits, time_filter):
    """
    Fetch mentions and sentiment score from Reddit posts about a cryptocurrency.
    """
    search_query = f"{crypto_name} OR {crypto_symbol}"
    total_mentions = 0
    sentiment_score_total = 0

    for subreddit in subreddits:
        try:
            mentions = reddit.subreddit(subreddit).search(search_query, time_filter=time_filter)
            for mention in mentions:
                total_mentions += 1
                analysis = TextBlob(mention.title + ' ' + mention.selftext)
                sentiment_score_total += analysis.sentiment.polarity

        except Exception as e:
            logging.warning(f"Reddit API error for {crypto_name} in r/{subreddit}: {e}")
            continue

    average_sentiment = sentiment_score_total / total_mentions if total_mentions > 0 else 0
    return total_mentions, average_sentiment

def fetch_trends_data(crypto_name, retries=5):
    """
    Fetch Google Trends data for a given cryptocurrency.
    Implements exponential backoff to handle TooManyRequestsError.
    """
    base_wait = 60  
    for i in range(retries):
        try:
            pytrends.build_payload([crypto_name], cat=0, timeframe='today 12-m', geo='', gprop='')
            trends_data = pytrends.interest_over_time()
            if not trends_data.empty:
                return trends_data[crypto_name].iloc[-1]  
            else:
                logging.warning(f"No trend data found for {crypto_name}. Returning 0.")
                return 0
        except TooManyRequestsError:
            wait_time = base_wait * (2 ** i) + random.uniform(0, base_wait)
            logging.warning(f"Google Trends API rate limit. Retrying in {wait_time:.2f} seconds... ({retries - i - 1} retries left)")
            time.sleep(wait_time)
        except Exception as e:
            logging.error(f"Failed to fetch Google Trends data for {crypto_name}: {e}")
            break
    return 0  

def calculate_acceleration(current_mentions, previous_mentions):
    """
    Calculate acceleration of mentions over time.
    """
    if previous_mentions == 0:
        return 0
    return (current_mentions - previous_mentions) / previous_mentions

def aggregate_sentiment_analysis(cryptocurrencies):
    """
    Aggregate sentiment analysis for a list of cryptocurrencies.
    - Fetch Reddit mentions & sentiment
    - Fetch Google Trends data
    - Calculate acceleration & combined sentiment score
    """
    subreddits = ['CryptoCurrency', 'Ethereum', 'ethtrader', 'eth', 'altcoin', 'CryptoMarkets']
    results = {}

    for crypto_name, crypto_symbol in cryptocurrencies:
        logging.info(f"🔍 Analyzing sentiment for {crypto_name} ({crypto_symbol})")

    
        current_mentions, current_sentiment = fetch_mentions_and_sentiment_reddit(crypto_name, crypto_symbol, subreddits, 'year')
        time.sleep(5)  

        # Fetch previous mentions (all-time)
        previous_total_mentions, _ = fetch_mentions_and_sentiment_reddit(crypto_name, crypto_symbol, subreddits, 'all')
        time.sleep(5)

        previous_mentions = previous_total_mentions - current_mentions
        acceleration = calculate_acceleration(current_mentions, previous_mentions)

        # Fetch Google Trends data
        google_trends_score = fetch_trends_data(crypto_name)
        time.sleep(5)

        normalized_google_trends_score = (google_trends_score / 100) * 2 - 1

        # Combine Reddit sentiment & Google Trends into an overall sentiment score
        combined_sentiment_score = (current_sentiment + normalized_google_trends_score) / 2

        results[crypto_symbol] = {
            'current_mentions': current_mentions,
            'average_sentiment': current_sentiment,
            'acceleration': acceleration,
            'previous_mentions': previous_mentions,
            'google_trends_score': google_trends_score,
            'normalized_google_trend_score': normalized_google_trends_score,
            'combined_sentiment_score': combined_sentiment_score,
        }

    return results




