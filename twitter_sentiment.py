# Hedge
 
# GOAL: To return a confidence index of specific company stock price longevity based on major macroeconomic changes noted by 'influential' twitter users (1,000,000+ followers)
#
# Max Gillespie & Louis Smidt
# Hedge Team
# 6/09/18


# Action Items:
#
# 2 Functions:
##     Mentions: Analyze sentiment of a standard person @ing a company account
# #    Company Score: Analyze macroeconomic factors from influential individuals
#
# Analyze Tweets from speficic list of individuals
# Quantify value of tweet content based on number of followers
# Can you find a tweet @ an account?

# dictionaries: positive correlation keywords, negative correlation keywords


import twitter
import nltk
from datetime import date
import csv
import pprint
import vaderSentiment.vaderSentiment as sia
from nltk.tag import StanfordNERTagger
from nltk.metrics.scores import accuracy

SIA = sia.SentimentIntensityAnalyzer()

API = twitter.Api(consumer_key='zQuVUVHVWNZd7yfMNdyXx4NgJ', consumer_secret='OBMTSJfy4UHuCDSslKzZdcgcm33NChTh1m3dJLX5OhRVY5EhUc', access_token_key='1005588267297853441-aYFOthzthNUwgHUvMJNDCcAMn0IfsC', access_token_secret='e88p7236E3nrigW1pkvmyA6hUyUWrMDQd2D7ZThbnZvoQ')

def csv_to_dict_list(csv_file) -> list:
    """
    parse csv file into a list of dictionaries
    """
    pass


######----------------- Company Score -------------------######

def get_relevant_tweets(number: int, from_date: date, to_date: date) -> list:
    """
    RETURN the 'number' most influential tweets after 'from_date' and before 'to_date'
    """
    pass

def stream_from_user(user_id: int):
    """
    Open a streaming connection from a user and save all tweets to a database
    """
    pass

def find_tweet_sentiment(tweet_text: str) -> float:
    """
    determine the sentiment of a tweet for a specific company
    """
    return SIA.polarity_scores(tweet_text)["compound"]

def find_tweet_target(tweet_text: str) -> str:
    """
    perform Named Entity Resolution to determine what company a tweet is most likely talking about.
    RETURN str representing company ticker symbol
    """
    pass


######----------------- Mentions ----------------#######

def get_recent_mentions(account_id: str, number: int) -> list:
    """
    find the 'number' most recent mentions of an account
    """
    pass

def tweet_shows_purchase_intent(tweet_text) -> bool:
    """
    check tweet text for indication that customer purchased product from the target company
    """
    pass

def get_account_id_from_name(account_screen_name: str) -> int:
    """
    RETURN the numeric id associated with an account
    """
    pass



#####--------------- Run program -----------------######

def run_scan(stock_symbol: str):
    """
    
    """
    pass


USER = API.GetUser(screen_name="Snapchat")
STATUS = API.GetUserTimeline(USER)
# response = GET https://api.twitter.com/1.1/statuses/mentions_timeline.json?count=2&since_id=14927799

TEST = API.GetTrendsCurrent()

printer = pprint.PrettyPrinter()
printer.pprint(STATUS)
#printer.pprint(TEST)