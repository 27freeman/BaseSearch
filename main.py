import requests
import logging,os
from datetime import datetime
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


API_KEY =  os.environ.get('ApiKey')
BASE_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"
app = FastAPI()

header = {
            "X-API-Key": API_KEY
        }

def search(params):
    all_tweets = []
    try:
        while True:
            # Make the GET request to the TwitterAPI.io endpoint
            response = requests.get(BASE_URL, headers=header, params=params)
            data = response.json()
            tweets = data.get('tweets', [])
            if not tweets:
                logging.info("No tweets found for the given query. Checking Next Hours Tweets")
                if all_tweets:
                    return all_tweets
                break
            for tweet in tweets:
                tweet_info = {
                    "userName": tweet.get("author", {}).get("userName"),
                    "text": tweet.get("text"),
                    "createdAt": tweet.get("createdAt"),
                    'tweet_link': tweet.get('url')
                }
                all_tweets.append(tweet_info)
            if not data['next_cursor']:
                logging.warning("No more tweets found or reached the end of results.")
                return all_tweets

            params['cursor'] = data['next_cursor']
            logging.info(f"Fetched {len(data['tweets'])} tweets, moving to next page...") 
    
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        logging.error(f"Error occurred: {err}")
    except ValueError as json_err:
        logging.error(f"Error parsing JSON response: {json_err}")

@app.get('/search/{keyword}/{date}')
def search_tweets(keyword:str,date:str,from_date:str|None = None,limit:int = 1,checkAlive:bool = False):
    if from_date:
        keyword = f"{keyword} since:{from_date}"
    EarlyTweets = []
    if checkAlive:
        logging.info('Checking if Api is Alive')
        return {'Status':200}
    hour = 0
    while True:
        hour += 1
        keyword_date = f"{keyword} until:{date}_{hour}:00:00_UTC"
        params = {
            "query": keyword_date,
            'cursor':"",
            'hash_next_page':True
            }
        params['query'] = keyword_date
        if hour == 24:
            logging.warning("Reached 24 hours limit, stopping search.")
            return {'Error': 'No tweets found for the given query. Change the keyword or date.'}
        all_tweets= search(params)
        if all_tweets:
            logging.info(f"Fetched {len(all_tweets)} tweets for keyword: {keyword_date}")
            break
    for tweet in reversed(all_tweets):
        if len(EarlyTweets) == limit:
            break
        EarlyTweets.append(tweet)
    return EarlyTweets     








