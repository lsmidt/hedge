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
import re
from datetime import date
import pandas as pd
import pprint
import vaderSentiment.vaderSentiment as sia
from nltk.tag import StanfordNERTagger # used for Named Entity Resolution
from nltk.metrics.scores import accuracy
from nltk import word_tokenize
from nltk import pos_tag
from collections import defaultdict

from fuzzywuzzy import process
from fuzzywuzzy import fuzz
from textblob import TextBlob

db = dataset.connect("sqlite:///tweetbase.db") # connect Dataset to Tweetbase

printer = pprint.PrettyPrinter() # printer object

SIA = sia.SentimentIntensityAnalyzer() # VADER Senitiment object

# Twitter Keys
CONSUMER_KEY = 'zQuVUVHVWNZd7yfMNdyXx4NgJ'
CONSUMER_SECRET = 'OBMTSJfy4UHuCDSslKzZdcgcm33NChTh1m3dJLX5OhRVY5EhUc'
AXS_TOKEN_KEY = '1005588267297853441-aYFOthzthNUwgHUvMJNDCcAMn0IfsC'
AXS_TOKEN_SECRET = 'e88p7236E3nrigW1pkvmyA6hUyUWrMDQd2D7ZThbnZvoQ'

# python-witter API Object
TWY = Twython(app_key=CONSUMER_KEY, app_secret=CONSUMER_SECRET, oauth_token=AXS_TOKEN_KEY, \
oauth_token_secret=AXS_TOKEN_SECRET)

# tweepy object
auth = tweepy.OAuthHandler(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET)
auth.set_access_token(key=AXS_TOKEN_KEY, secret=AXS_TOKEN_SECRET)
TWEEPY_API = tweepy.API(auth)

running = True # start and stop search

index_dict = {} # hold twitter since_ids for each searched company

# hold sentiment and purchase intent scores for each company
pi_scores = {}
sentiment_scores = {}

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
        # target = find_tweet_target(status.text)
        # sentiment[target] .append(polarity_score)

        # print tweet and score
        print(status.text, '(', polarity_score, ')')


    def on_error(self, error_code):
        print("Error" + str( error_code))
        if error_code == 420:
            return False


######----------------- Live Stream Processing -------------------######

def start_tweet_stream(search_terms: list, follow_user_id=None, filter_level="low"):
    """
    begin the streaming process. This method blocks the thread until the connection is closed by default
    """
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth, stream_listener)

    printer.pprint("STREAMING TWEETS")
    
    stream.filter(track=search_terms, filter_level=filter_level, \
                    languages = ["en"])


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

def find_text_sentiment(text) -> float:
    """
    determine the sentiment of a tweet for a specific company
    """
    negative_words = ["crash", "crashing", "problems", "not working", "fix", "shutting down"]

    score = SIA.polarity_scores(text)["compound"]

    for word_tup in negative_words:
        if fuzz.partial_ratio(word_tup, text) > 90:
            score = -0.4

    return score

def find_tweet_target(tweet_text: str) -> str:
    """
    perform Named Entity Resolution to determine what company a tweet is most likely talking about.
    RETURN str representing company ticker symbol
    """
    pass

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
    
    search_result = TWY.search(q=search_terms, result_type="recent", since_id=since_id, count=100, lang="en")
    tweets = []

    _max_id = search_result["search_metadata"]["max_id"]
    _since_id = search_result["search_metadata"]["since_id"]

    highest_id = _since_id
    lowest_id = _max_id

    # paginate results by updating max_id variable
    while len(search_result["statuses"]) != 0 and len(tweets) < 500: 

        for tweet in search_result["statuses"]:
            lowest_id = min(lowest_id, tweet["id"])
            highest_id = max(highest_id, tweet["id"])
            tweets.append(tweet)

        search_result = TWY.search(q=search_terms, result_type="recent", max_id=lowest_id-1, since_id=since_id, count=100, lang="en")

    return (tweets, highest_id)

def combine_search_results(first, second, third):
    """
    Combine search, account mentions, and timeline results. Three lists of tweets
    """
    combined = [tweet for tweet in first]
    a = [tweet for tweet in second]
    b = [tweet for tweet in third]

    return combined + a + b

def get_recent_mentions(screen_name: str, since_id:int) -> list:
    """
    find recent mentions of an account given its screen name by searching "@screen_name"
    """
    mentions = TWY.search(q="@" + screen_name, count=100, since_id=since_id, lang="en")
    tweets = []
    
    _max_id = mentions["search_metadata"]["max_id"]
    _since_id = mentions["search_metadata"]["since_id"]

    lowest_id = _max_id
    highest_id = _since_id
    
    while (len(mentions["statuses"]) != 0) and len(tweets) < 100:

        for tweet in mentions["statuses"]:
            lowest_id = min(lowest_id, tweet["id"])
            highest_id = max(highest_id, tweet["id"])
            tweets.append(tweet)

        mentions = TWY.search(q="@"+screen_name, max_id=lowest_id-1, since_id=since_id, count=100, lang="en")

    return (tweets, highest_id)

def get_user_timeline(account_id: int, since_id: int):
    """
    RETURN the tweets on a users timeline that have an id greater than since_id
    RETURN the new highest ID tweet found in the timeline
    """
    timeline_tweets = TWY.get_user_timeline(user_id=account_id)
    tweets = []

    if len(timeline_tweets) == 0: # user has never tweeted
        return ([], 0)

    _max_id = mentions["search_metadata"]["max_id"]
    _since_id = search_result["search_metadata"]["since_id"]

    lowest_id = _max_id
    highest_id = _since_id
    
    while len(timeline_tweets["statuses"]) != 0:

        for tweet in timeline_tweets["statuses"]:
            lowest_id = min(lowest_id, tweet["id"])
            highest_id = max(highest_id, tweet["id"])
            if tweet["id"] > since_id:
               tweets.append(tweet)

    timeline_tweets = TWY.get_user_timeline(user_id=account_id)

    return (timeline_tweets, highest_id)

def lookup_user_id(screen_name: str) -> int:
    """
    Return the user_id of the account associated with the string
    """
    user = TWY.show_user(screen_name=screen_name)
    return user["id"]

def get_subjectivity(text):
    """
    RETURN subjectivity of sentence
    """
    return TextBlob(text).subjectivity

def tweet_shows_purchase_intent(tweet_text) -> bool:
    """
    Return true if the tweet text indicates that a customer used or bought 
        a product
    """
    fp_verb_list = ["bought", "used", "got", "had", "flew", "ate", "use", "carry", "have"]

    fp_pron = ["i", "we", "me", "my", "our", "ours", "us", "mine", "myself", "this"]
    other_pron = ["you", "your", "their", "they"]

    text = word_tokenize(tweet_text)
    pos_list = pos_tag(text, tagset='universal')

    # TODO: work in the filter_text method here to make subjectivity more reliable
    subj = get_subjectivity(tweet_text)
    net_score = subj

    fp_pron_used = []

    for word_tup in pos_list:
        lower = word_tup[0].lower()
        if lower in fp_pron:
            fp_pron_used.append(lower)

    if len(fp_pron_used) == 0:
        net_score -= 0.1
    else:
        net_score += 0.2 * len(fp_pron_used)

    return True if net_score > 0.2 else False

    
def filter_text(text):
    """
    spell check, remove @mentions
    """
    # FIXME: This shit doesn't work
    mention_expression = re.compile(r"\s([@#][\w_-]+)")

    short = reduce_lengthening(text)
    no_mentions = re.sub(mention_expression, short)
    pass
    
def filter_tweet(tweet, search_terms=[], accept_terms=""):
    """
    filter the tweet from the stream if it is not of high quality
    """
    if type(tweet) is dict:
        if "retweeted_status" in tweet:
            return False
        
        text = tweet["text"]
        friends_count = tweet["user"]["friends_count"]
        qry_type = tweet["metadata"]["result_type"]
        rt_count = tweet["retweet_count"]
        is_reply = False if tweet["in_reply_to_status_id"] is None else True
        num_mentions = len( tweet["entities"]["user_mentions"])

    else:
        if hasattr(tweet, "retweeted_status"):
            return False

        text = tweet.text
        friends_count = tweet.user.friends_count
        qry_type = tweet.metadata.result_type
        rt_count = tweet.metadata.retweet_count
        is_reply = False if tweet.in_reply_to_status_id is None else True
        num_mentions = len(tweet.entities.user_mentions)

    stop_words = "porn pussy babe nude pornstar sex \
        naked cock cocks gloryhole tits anal horny cum penis"
    
    for word_tup in stop_words.split():

        if word_tup in text:
            return False

    if friends_count < 15:
        return False

    if num_mentions > 3:
        return False
    if "$" in text:
        return False

    text_tok = word_tokenize(text)
    pos_list = pos_tag(text_tok, tagset='universal')

    # at least one search term should be pronoun if search term is a product
    flag = True
    count_occ = 0
    for term in search_terms.split():
        if term == "OR":
                continue

        for word_tup in pos_list:

            ratio = fuzz.token_set_ratio(term, word_tup[0])
            if ratio > 85:
                count_occ += 1
                # FIXME: This may reinclude non-nouns. Use a tokenizer or avoid ambiguous cases in accept_terms
                if fuzz.partial_token_sort_ratio(word_tup[0], accept_terms) > 85:
                    flag = False
                    break

                if (word_tup[1] == "NOUN" or word_tup[1] == "PRON") or count_occ > 1: 
                    flag = False
                    break
                else:
                    print (word_tup[0] + " is a " + word_tup[1])
    
    if flag and (not search_terms is None):
        print ("REJECTED")

    # if "http" in text:
    #     print ("REJECT: URL in text")
    #     print (text)
    #    return False
    # if not tweet_shows_purchase_intent(text):
    #     return False

    return True

#####--------------- Main methods -----------------######

def scan_realtime_tweets(stock_symbol: str, account_id: int=None):
    """
    Begin streaming tweets matching the stock symbol or from the account in real time. 
    """
    file = open('stock_ticker_subset.csv')
    for line in file:
        data = line.split(',')
        if data[0] == stock_symbol:
            start_tweet_stream(data[1], follow_user_id=account_id)

def save_to_file(db_name: str, query: tuple,  tweet: dict, polarity_score: float):
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

def score_magnitude(score: float, threshold: float):
    """
    threshold is positive value
    """
    if score > threshold:
        return 1
    elif score < -1 * threshold:
        return -1
    else:
        return 0

def search_tweets(ticker_search_dict: dict): 
    """
    Manage the tweet search loop with the companies in the ticker_search_dict
    RETURN sentiment and purchase intent information for each company
    """
    # hold sentiment and PI results for each target company
    sentiment = defaultdict(list)
    sentiment_magnitude = defaultdict(list)
    purchase_intent = defaultdict(list)

    for id_tuple, search_dict in ticker_search_dict.items():
        #TODO: Code below for "search" if-else can be condensed. 

        ### Search Tweets

        # if a since_id already exists, use it. else use 0 as since_id
        if "search" in index_dict[id_tuple]:
            found_tweets, since_id = get_search_results(id_tuple[1], id_tuple[0], search_dict["search"], \
                                                        since_id=index_dict[id_tuple]["search"])
            index_dict[id_tuple]["search"] = since_id
        else:
            found_tweets, since_id = get_search_results(id_tuple[1], id_tuple[0], search_dict["search"], since_id=0)
            index_dict[id_tuple]["search"] = since_id


        screen_name = id_tuple[1]
        user_id = lookup_user_id(screen_name) # assume screen_name from TSD is always correct


        ### Mentions
        men_since_id = index_dict[id_tuple]["mentions"] if "mentions" in index_dict[id_tuple] else 0
        men_tweets, new_men_since_id = get_recent_mentions(screen_name, men_since_id)
        index_dict[id_tuple]["mentions"] = new_men_since_id

        ### Timeline
        # tl_since_id = index_dict[id_tuple]["timeline"] if "timeline" in index_dict[id_tuple] else 0
        # tl_tweets, new_tl_since_id = get_user_timeline(user_id, tl_since_id)
        # index_dict[id_tuple]["timeline"] = new_tl_since_id

        combined = combine_search_results(found_tweets, [], [])
        
        passed_tweets = []
        reject_count = 0 # count passed up tweets

        for tweet in combined:
            if filter_tweet(tweet, search_dict["search"], search_dict["accept"]):
                
                # check if tweet is a close copy of one already seen
                copy = False
                
                for passed_tweet in passed_tweets:
                    if fuzz.ratio(tweet["text"], passed_tweet) > 80:
                        copy = True
                        break

                if copy == True:
                    reject_count += 1
                    continue

                
                # TODO: perform spell correcting
                short_text = reduce_lengthening(tweet["text"])

                polarity = find_text_sentiment(short_text)
                subjectivity = get_subjectivity(short_text)

                print ( tweet["text"] )
                print ("Polarity: " + str(polarity))
                print ("Subjectivity: " + str( subjectivity))
                shows_pi = tweet_shows_purchase_intent(tweet["text"])

                print ("Purchase Intent: " + str(shows_pi) + "\n")
                # save_to_file( "searched_tweets", id_tuple, tweet, polarity)

                passed_tweets.append(tweet["text"])

                sentiment[id_tuple].append(polarity)
                sentiment_magnitude[id_tuple].append(score_magnitude(polarity, 0.2))
                purchase_intent[id_tuple].append(1 if shows_pi else 0)

            else:
                reject_count += 1


        print ("Total Tweets found"  + str( len( combined)))
        print ("Rejected: " + str(reject_count))

    return (sentiment, sentiment_magnitude, purchase_intent)

def reduce_lengthening(text):
    """
    function to shorten words that have been made too long. IE "finallllllly"
    """
    pattern = re.compile(r"(.)\1{2,}")
    new_text = pattern.sub(r"\1\1", text)

    return new_text

####---------- Run Program --------------#####

# scan_realtime_tweets('SNAP')

search_dict = {("AAPL", "Apple") : {"search" : "iphone OR iPad OR ios OR Apple Pencil", \
                                    "accept" : "iPad iPhone"},
                ("SNAP", "Snap"): {"search" : "Snap OR Snapchat", \
                                    "accept" : "Snapchat story"}
               }

index_dict = {x : {} for x in search_dict.keys()}

search_count = 0 # keep track of number of iterations of loop

while running == True:
    search_count += 1

    (sent, sent_mag, pi) = search_tweets(search_dict)

    # generate the score based on the search information
    sentiment_score = defaultdict(float)
    pi_count = defaultdict(float)
    score = defaultdict(float)

    for company in sent:
        avg_sent = sum(sent[company]) / len(sent[company]) if len(sent[company]) != 0 else 0 
    
    # TODO: This scoring system is uniquely retarded

        if score_magnitude(avg_sent, 0.2) == 1:
            score[company] += 300
        elif score_magnitude(avg_sent, 0.2) == -1:
            score[company] -= 300
    
    for company in pi:
        for pi_score in pi[company]:
            if pi_score == 1:
                score[company] += 5

    for company in sent_mag:
        for sent_score in sent_mag[company]:
            if sent_score == 1:
                score[company] += 5
            elif sent_score == -1:
                score[company] -= 5


    #print ( str( search_count) + "th iteration of search_tweets")
        
    if search_count > 0:
        running = False

for company in score:
    print ("SCORE: " + str(company) + ": " + str(score[company]))