'''
GOAL: To return a confidence index of specific company stock price longevity based on major macroeconomic changes
noted by 'influential' twitter users (1,000,000+ followers)

Max Gillespie & Louis Smidt
6/09/18
'''

'''
Action Items:

2 Functions:
    Analyze sentiment of a standard person @ing a company account
    Analyze macroeconomic factors from influential individuals

Analyze Tweets from speficic list of individuals
Quantify value of tweet content based on number of followers
Can you find a tweet @ an account?

dictionaries: positive correlation keywords, negative correlation keywords
'''

import twitter
import requests
import datetime

api = twitter.Api(consumer_key='zQuVUVHVWNZd7yfMNdyXx4NgJ', consumer_secret='OBMTSJfy4UHuCDSslKzZdcgcm33NChTh1m3dJLX5OhRVY5EhUc',
    access_token_key='1005588267297853441-aYFOthzthNUwgHUvMJNDCcAMn0IfsC',  access_token_secret='e88p7236E3nrigW1pkvmyA6hUyUWrMDQd2D7ZThbnZvoQ')


def get_relevant_tweets(number: int, from_date: datetime) -> list:
    """
    RETURN the 'number' most influential tweets after 'from_date'
    """
    pass

def find_tweet_sentiment(tweet: str) -> float:
    """
    determine the sentiment of a tweet for a specific company
    """
    pass

def find_tweet_target(tweet: str) -> str:
    """
    determine what company a tweet is most likely talking about.
    """
    pass

def get_recent_mentions(account: str) -> list:
    """
    find the recent mentions of an account
    """
    pass



status = api.GetUserTimeline('snap')
# response = GET https://api.twitter.com/1.1/statuses/mentions_timeline.json?count=2&since_id=14927799
