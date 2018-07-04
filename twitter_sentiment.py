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


from twython import Twython # used for mentions
import tweepy # used for streaming
import dataset
import urllib.parse
import copy
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

global running = False

class StreamListener(tweepy.StreamListener):
    """
    Override the StreamListener class to add custom filtering functionality to the stream listener
    """

    def on_status(self, status):
        if not filter_tweet( status):
            return

        # get polarity score of tweet contents
        polarity_score = find_tweet_sentiment(status)

        # save tweet contents and polarity score to file
        save_tweet_to_file("live_stream", status, polarity_score)

        # find the target of the tweet
        find_tweet_target(status.text)

        # print tweet and score
        print(status.text, '(', polarity_score, ')')


    def on_error(self, error_code):
        print("Error" + str( error_code))
        if error_code == 420:
            return False


######----------------- Company Score (Live Stream Sentiment) -------------------######

def start_tweet_stream(search_terms: list, follow_user_id=None, filter_level="low"):
    """
    begin the streaming process. This method blocks the thread until the connection is closed by default
    """
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth, stream_listener)

    printer.pprint("NOW STREAMING")
    stream.filter(track=search_terms, filter_level=filter_level, languages = ["en"])

def filter_tweet(tweet):
    """
    filter the tweet from the stream if it is not useful
    """
    if type(tweet) is dict:
        text = tweet["text"]
        friends_count = tweet["user"]["friends_count"]
        if "retweeted_status" in tweet:
            return False
    else:
        text = tweet.text
        friends_count = tweet.user.friends_count
        if hasattr(tweet, "retweeted_status"):
            return False

    if friends_count < 1000:
        return False
    if "http" in text:
        return False
    # if not tweet_shows_purchase_intent(text):
    #     return False

    return True


def save_tweet_to_file(db_title: str, tweet, polarity_score: float):
    """
    save the tweet to a SQLite DB using Dataset
    """
    table = db[db_title]

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
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth, stream_listener)
    printer.pprint( "NOW STREAMING FROM" + str( lookup_user_id( user_id)))
    stream.filter(follow=user_id, languages=["en"])

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
    # tag_list = tagger.tag( tweet_text)
    # split_list = tag_list.split()
    # # account for non grouping by grouping consecutive orgs
    # found_org_list = []

    # for word_tuple in split_list:
    #     if word_tuple[1] == "ORGANIZATION":
    #         found_org_list.append(word_tuple[0])

    # # fuzzy string match words in a csv of stock tickers we track
    # org_score = {}
    
    # df = pd.read_csv("stock_ticker_subset.csv")
    # org_names = df.Name
    # org_tickers = df.Ticker

    # for org in found_org_list:
    #     org_score[org] = process.extractOne(org, org_names, scorer=fuzz.partial_token_sort_ratio)

    return None  

######----------------- Mentions (Moving Average Sentiment)----------------#######
# Iterate over a list of company and product names, for each, produce a search search_terms, load a page of 100 tweets 
# save the highest id per page, use that to advance pages. Save the lowest id encountered, then close the connection
# and advance to the next symbol. Use the max_id and since parameters to keep track of back logged tweets when reconnecting. 
# Experiment with number of tweets you can fetch to produce a strictly quantized dataset. 
# Generate the moving average. 

def get_search_results(screen_name: str, ticker: str, search_terms: str, since_id: int=None) -> list:
    """
    RETURN the 'number' most influential tweets after 'from_date' and before 'to_date'
    """
    # Method 1: Search for tweets matching search_terms
    if since_id is None: 
        since_id = 0
    
    search_result = TWY.search(q=search_terms, result_type="mixed", since_id=since_id, count=50, lang="en")
    tweets = []

    _max_id = search_result["search_metadata"]["max_id"]
    _since_id = search_result["search_metadata"]["since_id"]

    highest_id = _since_id
    lowest_id = _max_id

    # paginate results by updating max_id variable
    for i in range(0, 5): 
        if len(search_result["statuses"]) == 0:
            break


        for tweet in search_result["statuses"]:
            lowest_id = min(lowest_id, tweet["id"])
            highest_id = max(highest_id, tweet["id"])
            tweets.append(tweet)

        search_result = TWY.search(q=search_terms, max_id=lowest_id-1, since_id=since_id, count=50, lang="en")
   

    ### Method 2: search timeline and mentions of account of company
    # user_id = lookup_user_id(screen_name)
    # timeline = get_user_timeline(user_id)
    # mentions = get_recent_mentions(screen_name)

    return (tweets, highest_id)

def get_recent_mentions(screen_name: str) -> list:
    """
    find recent mentions of an account given its screen name by searching "@screen_name"
    """
    mentions = TWY.search(q="@" + screen_name, count=100, lang="en")
    tweets = []
    
    for i in range(0, 5):
        if len(mentions["statuses"]) == 0:
            break 

        _max_id = mentions["search_metadata"]["max_id"]

        lowest_id = _max_id
        for tweet in mentions["statuses"]:
            lowest_id = min(lowest_id, tweet["id"])
            tweets.append(tweet)

        mentions = TWY.search(q="@"+screen_name, max_id=lowest_id-1, count=100, lang="en")

    return mentions

def get_user_timeline(account_id: int):
    """
    find a user's timeline
    """
    timeline_tweets = TWY.get_user_timeline(user_id=account_id)

    # TODO: Paginate the timeline results, add results of this to search results

    return timeline_tweets

def lookup_user_id(screen_name: str) -> int:
    """
    Return the user_id of the account associated with the string
    """
    user = TWY.show_user(screen_name=screen_name)
    return user["id"]

def tweet_shows_purchase_intent(tweet_text) -> bool:
    """
    check tweet text for indication that customer purchased product from the target company.
    Look for a noun and a verb in the sentence.
    return true if word is found, false else
    """
    pi_list = ["bought", "used", "new", "my", "got", "had", "flew", "ate", "use"] 
    # simple test words before POS tagging implemented
    for word in tweet_text.split():
        if word.lower() in pi_list:
            return True
    return False

    
#####--------------- Run program -----------------######

def scan_realtime_tweets(stock_symbol: str, account_id: int=None):
    """
    Begin streaming tweets matching the stock symbol or from the account in real time. 
    """
    file = open('stock_ticker_subset.csv')
    for line in file:
        data = line.split(',')
        if data[0] == stock_symbol:
            start_tweet_stream(data[1], follow_user_id=account_id)


def save_to_file(db_name: str, query: tuple  tweet: dict, polarity_score: float):
    """
    save_tweet_to_file analog for tweets that are dictionaries instead of Status objects
    """

    table = db[db_name]

    tweet_contents = dict(
    text=tweet["text"],
    ticker=query[0],
    company_name=query[1],
    user_name=tweet["user"]["screen_name"],
    tweet_date=tweet["created_at"],
    user_followers=tweet["user"]["followers_count"],
    id_str=tweet["id_str"],
    retweet_count=tweet["retweet_count"],
    polarity=polarity_score
    )
        
    table.insert(tweet_contents)



def search_tweets(ticker_search_dict: dict): 
    """
    Begin the tweet search loop with the companies in the ticker_search_dict
    """
    # make dict to keep track of since_id
    index_dict = {x : {"since_id" : 0} for x in ticker_search_dict.keys()}


    while running == True:

        for id_tuple, search_list in ticker_search_dict.items():
            found_tweets, since_id = get_search_results(id_tuple[1], id_tuple[0], search_list, since_id=index_dict[id_tuple]["since_id"])
            index_dict[id_tuple["since_id"] = since_id 
            c = 0 # counter for number of passed up tweets
    
            for tweet in found_tweets:
                if (filter_tweet(tweet)):
                    print (tweet["text"])
                    polarity = SIA.polarity_scores(tweet["text"])["compound"]
                    save_to_file("searched_tweets", id_tuple, tweet, polarity)

                else:
                    c += 1;
                    print (c);
            
            print ("Total Tweets found"  + str( len( found_tweets)))


# scan_realtime_tweets('SNAP')

search_dict = {("AAPL", "Apple") : "Apple Mac iPhone",
                ("SNAP", "Snap"): "Snap Snapchat",
                ("FIZZ", "National Beverage"): "LaCroix lacroix"}
search_tweets(search_dict)

