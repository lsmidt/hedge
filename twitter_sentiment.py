# Hedge

# GOAL: To return a confidence index of specific company stock price longevity based on major macroeconomic changes noted by 'influential' twitter users (1,000,000+ followers)
#
# Max Gillespie & Louis Smidt
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


import twitter # used for mentions
import tweepy # used for streaming
import nltk
import dataset
from datetime import date
import csv
import pprint
import vaderSentiment.vaderSentiment as sia
from nltk.tag import StanfordNERTagger # used for Named Entity Resolution
from nltk.metrics.scores import accuracy

# connect Dataset to Tweetbase
db = dataset.connect("sqlite:///tweetbase.db")

# make pretty printer
printer = pprint.PrettyPrinter()

# Vader sentiment object
SIA = sia.SentimentIntensityAnalyzer()

# read CSV file of tickers to names
# tickers = csv_to_dict_list(stock_tickers.csv)

CONSUMER_KEY = 'zQuVUVHVWNZd7yfMNdyXx4NgJ'
CONSUMER_SECRET = 'OBMTSJfy4UHuCDSslKzZdcgcm33NChTh1m3dJLX5OhRVY5EhUc'
AXS_TOKEN_KEY = '1005588267297853441-aYFOthzthNUwgHUvMJNDCcAMn0IfsC'
AXS_TOKEN_SECRET = 'e88p7236E3nrigW1pkvmyA6hUyUWrMDQd2D7ZThbnZvoQ'

# python-witter API Object
PT_API = twitter.Api(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET, access_token_key=AXS_TOKEN_KEY, access_token_secret=AXS_TOKEN_SECRET)

# tweepy object
auth = tweepy.OAuthHandler(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET)
auth.set_access_token(key=AXS_TOKEN_KEY, secret=AXS_TOKEN_SECRET)
TWEEPY_API = tweepy.API(auth)

class StreamListener(tweepy.StreamListener):
    """
    Override the StreamListener class to add custom filtering functionality to the stream listener
    """

    def on_status(self, status):
        if not filter_tweet(status):
            return

        # get polarity score of tweet contents
        polarity_score = find_tweet_sentiment(status)

        # save tweet contents and polarity score to file
        save_tweet_to_file(status, polarity_score)

        # print tweet and score
        print(status.text, '(', polarity_score, ')')


    def on_error(self, error_code):
        print("Error" + str(error_code))
        if error_code == 420:
            return False


######----------------- Company Score (Live Stream) -------------------######

def start_tweet_stream(search_terms: list, filter_level="low"):
    """
    begin the streaming process. This method blocks the thread until the connection is closed by default
    """
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth, stream_listener)

    # couple database for storage

    printer.pprint("NOW STREAMING")
    stream.filter(track=search_terms, filter_level = filter_level, languages = ["en"])


def filter_tweet(tweet):
    """
    filter the tweet from the stream if it is not useful
    """
    if hasattr(tweet, "retweeted_status"):
        return False
    if tweet.user.friends_count < 100:
        return False

    return True

def save_tweet_to_file(tweet, polarity_score):
    """
    save the tweet to a SQLite DB using Dataset
    """
    table = db["tweets"]

    tweet_contents = dict(
    user_description=tweet.user.description,
    user_location=tweet.user.location,
    text=tweet.text,
    user_name=tweet.user.screen_name,
    tweet_date=str(tweet.created_at),
    user_followers=tweet.user.followers_count,
    id_str=tweet.id_str,
    retweet_count=tweet.retweet_count,
    polarity=polarity_score
    )

    table.insert(tweet_contents)


def save_stream_from_user(user_id: int):
    """
    Open a streaming connection from a user and save all tweets to a database for post_processing
    """
    pass

def find_tweet_sentiment(tweet) -> float:
    """
    determine the sentiment of a tweet for a specific company
    """
    return SIA.polarity_scores(tweet.text)["compound"]

def find_tweet_target(tweet_text: str) -> str:
    """
    perform Named Entity Resolution to determine what company a tweet is most likely talking about.
    RETURN str representing company ticker symbol
    """
    pass


######----------------- Mentions (Average Sentiment)----------------#######

def get_relevant_tweets(number: int, from_date: date, to_date: date) -> list:
    """
    RETURN the 'number' most influential tweets after 'from_date' and before 'to_date'
    """
    pass

def get_recent_mentions(account_id: str, number: int) -> list:
    """
    find the 'number' most recent mentions of an account
    """
    pass

def tweet_shows_purchase_intent(tweet_text) -> bool:
    """
    check tweet text for indication that customer purchased product from the target company.
    Look for a noun and a verb in the sentence.
    """
    pass

def get_account_id_from_name(screen_name: str) -> int:
    """
    RETURN the numeric id associated with an account
    """
    return PT_API.GetUser(screen_name=screen_name).id



#####--------------- Run program -----------------######

def run_scan(stock_symbol: str):
    file = open('stock_tickers.csv')
    for line in file:
        data = line.split(',')
        if data[0] == stock_symbol:
            start_tweet_stream(data[0:4])


# USER = PT_API.GetUser(screen_name="Snapchat")
# STATUS = PT_API.GetUserTimeline(get_account_id_from_name("Snapchat"))
# # response = GET https://api.twitter.com/1.1/statuses/mentions_timeline.json?count=2&since_id=14927799

# TEST = PT_API.GetTrendsCurrent()

# printer = pprint.PrettyPrinter()
# for item in STATUS:
#     printer.pprint(item.text)
# #printer.pprint(TEST)

run_scan('AA')

#start_tweet_stream(["@Snap", "Trump"])
