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


from twython import Twython # used for mentions
import tweepy # used for streaming
import dataset
import urllib.parse
from datetime import date
import pandas as pd
import pprint
import vaderSentiment.vaderSentiment as sia
from nltk.tag import StanfordNERTagger # used for Named Entity Resolution
from nltk.metrics.scores import accuracy

from fuzzywuzzy import process
from fuzzywuzzy import fuzz

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
TWY = Twython(app_key=CONSUMER_KEY, app_secret=CONSUMER_SECRET, oauth_token=AXS_TOKEN_KEY, oauth_token_secret=AXS_TOKEN_SECRET)

# tweepy object
auth = tweepy.OAuthHandler(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET)
auth.set_access_token(key=AXS_TOKEN_KEY, secret=AXS_TOKEN_SECRET)
TWEEPY_API = tweepy.API(auth)

# Stanford NER Object
jar = '/Users/louissmidt/Documents/Software/stanford-english-corenlp-2018-02-27-models.jar'
model = '/Users/louissmidt/Documents/Software/stanford-ner-2018-02-27/classifiers/english.all.3class.distsim.crf.ser.gz'
tagger = StanfordNERTagger(model, jar)

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

        # find the target of the tweet
        # find_tweet_target(status.text)

        # print tweet and score
        print(status.text, '(', polarity_score, ')')


    def on_error(self, error_code):
        print("Error" + str(error_code))
        if error_code == 420:
            return False


######----------------- Company Score (Live Stream Sentiment) -------------------######

def start_tweet_stream(search_terms: list, follow_user_id=None, filter_level="low"):
    """
    begin the streaming process. This method blocks the thread until the connection is closed by default
    """
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth, stream_listener)

    # couple database for storage

    printer.pprint("NOW STREAMING")
    if follow_user_id is None:
        stream.filter(track=search_terms, filter_level=filter_level, languages = ["en"])
    else:
        stream.filter(track=search_terms, follow=follow_user_id, filter_level=filter_level, languages=["en"])

def filter_tweet(tweet):
    """
    filter the tweet from the stream if it is not useful
    """
    if hasattr(tweet, "retweeted_status"):
        return False
    if tweet.user.friends_count < 10000:
        return False
    if "http" in tweet.text:
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
    tweet_date=tweet.created_at,
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
    # FIXME: tagger.tag crashes with a tokenizer error.
    tag_list = tagger.tag(tweet_text)
    split_list = tag_list.split()
    # account for non grouping by grouping consecutive orgs
    found_org_list = []

    for word_tuple in split_list:
        if word_tuple[1] == "ORGANIZATION":
            found_org_list.append(word_tuple[0])

    # fuzzy string match words in a csv of stock tickers we track
    org_score = {}
    
    df = pd.read_csv("stock_ticker_subset.csv")
    org_names = df.Name
    org_tickers = df.Ticker

    for org in found_org_list:
        org_score[org] = process.extractOne(org, org_names, scorer=fuzz.partial_token_sort_ratio)

    return None  

######----------------- Mentions (Moving Average Sentiment)----------------#######
# Iterate over a list of company and product names, for each, produce a search query, load a page of 100 tweets 
# save the highest id per page, use that to advance pages. Save the lowest id you encounter, then close the connection
# and advance to the next symbol. Use the max_id and since parameters to keep track of back logged tweets when reconnecting. 
# Experiment with number of tweets you can fetch to produce a strictly quantized dataset. 
# Generate the moving average. 

def get_search_results(company_name: str, query: str, max_id: int=None, since_id: int=None) -> list:
    """
    RETURN the 'number' most influential tweets after 'from_date' and before 'to_date'
    """
    tweets= {}

    # Search tweets matching query
    query_result = TWY.search(q=query, result_type="popular", count=50, lang="en")
    
    # find account matching 
    
    
    
    #tweets.update(query_result["statuses"])

    _max_id = query_result["search_metadata"]["max_id"]
    _since_id = query_result["search_metadata"]["since_id"]
    _next_page_query = query_result["search_metadata"]["refresh_url"]


    for i in range(0, 5): 
        next_result = TWY.search(q=query, since_id=_since_id, max_id=_max_id, count=50, lang="en")
        _next_page_query = next_result["search_metadata"]["refresh_url"]   
        tweets.update(next_result["statuses"])
    return None

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


#####--------------- Run program -----------------######

def scan_realtime_tweets(stock_symbol: str, account_id: int=None):
    """
    Begin streaming tweets matching the stock symbol or from the account in real time. 
    """
    file = open('stock_tickers.csv')
    for line in file:
        data = line.split(',')
        if data[0] == stock_symbol:
            start_tweet_stream(data[1], follow_user_id=account_id)

def search_tweets(ticker_search_dict: dict): 
    """
    Begin the tweet search loop with the companies in the ticker_search_dict
    """
    index_dict = dict.fromkeys(ticker_search_dict, {"max_id": 0, "since_id": 0})

    for ticker, search_list in ticker_search_dict.items():
        get_search_results(ticker, search_list)


# USER = PT_API.GetUser(screen_name="Snapchat")
# STATUS = PT_API.GetUserTimeline(get_account_id_from_name("Snapchat"))
# # response = GET https://api.twitter.com/1.1/statuses/mentions_timeline.json?count=2&since_id=14927799

# TEST = PT_API.GetTrendsCurrent()

# for item in STATUS:
#     printer.pprint(item.text)
# #printer.pprint(TEST)

# scan_realtime_tweets('SNAP')

search_dict = {"AAPL" : "Apple Mac iPhone iOS"}
search_tweets(search_dict)
