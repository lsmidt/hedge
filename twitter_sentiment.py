'''
HEDGE CAPITAL LLC.



TODO:
    (max) IEX moving 'n' day average and standard deviation
    (max) read tweetbase.db to plot connection between scores and price
    maximum score for any specific sample


Louis Smidt & Max Gillespie
FIRST COMMIT ----------------> 6/09/2018
MOST RECENT COMMIT ----------> 7/18/2018
PURPOSE:
'''

from twython import Twython # used for mentions
import tweepy # used for streaming
import dataset
import urllib.parse
import copy
import re
import json
from datetime import date
import pandas as pd
import pprint
import vaderSentiment.vaderSentiment as sia
import time
import datetime
from nltk.tag import StanfordNERTagger # used for Named Entity Resolution
from nltk.metrics.scores import accuracy
from nltk import word_tokenize
from nltk import pos_tag
from collections import defaultdict

from fuzzywuzzy import process
from fuzzywuzzy import fuzz
from textblob import TextBlob

db = dataset.connect("sqlite:///tweetbase.db") # connect Dataset to Tweetbase
db2 = dataset.connect("sqlite:///scorebase.db")

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
TWEEPY_API = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

running = True # start and stop search

index_dict = {} # hold twitter since_ids for each searched company

# hold sentiment and PI scores for each company
pi_scores = {}
sentiment_scores = {}

# open the companies JSON database -> Streaming
with open("companies.json", "r") as in_file:
    companies_db = json.load(in_file)

company_matches = {}
for company, brand_dict in companies_db.items():
    company_matches[company] = copy.copy(brand_dict)
    for brand in brand_dict.keys():
        company_matches[company][brand] = 0

# save settings for tweet filter -> Streaming
search_tms = []
accept_tms = []
reject_tms = []
search_tms_list = []

# timer -> Streaming
tweet_counter = 0
set_time = time.time()

# Constants
MINUTE_DELAY = 0.5
NUM_TWEETS_TO_FETCH = 500
LOOP_ITERATIONS = 10

# reference variables
ref_date = datetime.date.today()

class StreamListener(tweepy.StreamListener):
    """
    Override the StreamListener class to add custom filtering functionality to the stream listener
    """

    def on_status(self, status):
        global tweet_counter, set_time
        tweet_counter += 1

        if tweet_counter == 10:
            time_diff = time.time() - set_time
            print ("\n TIMER: {} \n".format(tweet_counter / time_diff))
            set_time = time.time()
            tweet_counter = 0


        if not filter_tweet( status):
            return

        # get polarity score of tweet contents
        polarity_score = find_text_sentiment(status.text)
        subj = get_subjectivity(status.text)

        # save tweet contents and polarity score to file
        # save_tweet_to_file("live_stream", status, polarity_score)

        # find the target of the tweet
        target = find_tweet_target(status.text)
        # sentiment[target] .append(polarity_score)

        # print tweet and score
        print("TEXT: {} \n (Polarity: {}) \n (Subjectivity: {}) \n (Target: {}) \n" \
        .format(status.text, polarity_score, subj, target))


    def on_error(self, error_code):
        print("Error" + str( error_code))
        if error_code == 420:
            print("420: Rate Limit Error")
            return False


######----------------- Live Stream Processing -------------------######

def get_tweet_date(date_str: str):
    """
    ['created_at']:'Wed Aug 01 01:11:10 +0000 2018'
    """
    dt = datetime.datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")

    return dt

def start_tweet_stream(search_terms: list = None, follow_user_id=None, filter_level="low"):
    """
    begin the streaming process. This method blocks the thread until the connection is closed by default
    """
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth, stream_listener)

    printer.pprint("STREAMING TWEETS")

    stream.filter(track=search_terms, filter_level=filter_level, \
                    languages = ["en"])

def find_tweet_target(tweet_text: str) -> str:
    """
    run tweet text through a database, return the companies it associates to.
    """
    split = tweet_text.split()
    highest_score = 0
    h_company = []
    h_brand = []

    for company, brand_dict in companies_db.items():
        for brand, tag_list in brand_dict.items():
            for tag in tag_list:
                score = fuzz.partial_token_sort_ratio(tag, tweet_text)
                if score > 90:
                    highest_score = score
                    h_company.append(company)
                    h_brand.append(brand)
                    #company_matches[h_company][h_brand] += 1
                # if tag in tweet_text:
                #     h_company = company
                #     h_brand = brand
                #     return (h_company, h_brand)

                # for tweet_word in split:
                #     score = fuzz.ratio(tag, tweet_word)
                #     if score > highest_score:
                #         highest_score = score
                #         h_company = company
                #         h_brand = brand

    return str(zip(h_company, h_brand))

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


######-----------------Moving Average Sentiment and PI Scores----------------#######

def get_search_results(screen_name: str, ticker: str, search_terms: str, since_id: int = None) -> list:
    """
    RETURN the 'number' most influential tweets after 'from_date' and before 'to_date'
    """
    # Method 1: Search for tweets matching search_terms
    if since_id is None:
        since_id = 0

    print ("Grabbing Tweets for query {}".format(search_terms))
    search_result = TWY.search(q=search_terms, result_type="recent", since_id=since_id, count=200, lang="en")
    tweets = []

    _max_id = search_result["search_metadata"]["max_id"]
    _since_id = search_result["search_metadata"]["since_id"]

    highest_id = _since_id
    lowest_id = _max_id

    # paginate results by updating max_id variable
    while len(search_result["statuses"]) != 0 and len(tweets) <= NUM_TWEETS_TO_FETCH:
        print("Returned {} Tweets from Search".format(len(tweets)))

        for tweet in search_result["statuses"]:
            lowest_id = min(lowest_id, tweet["id"])
            highest_id = max(highest_id, tweet["id"])
            tweets.append(tweet)

        search_result = TWY.search(q=search_terms, result_type="recent", max_id=lowest_id-1, since_id=since_id, count=200, lang="en")

    return (tweets, highest_id)

def combine_search_results(first, second, third):
    """
    Combine search, account mentions, and timeline results. Three lists of tweets
    """
    combined = [tweet for tweet in first]
    a = [tweet for tweet in second]
    b = [tweet for tweet in third]

    return combined + a + b

def get_recent_mentions(screen_name: str, since_id: int) -> list:
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

    fp_pron = ["i", "we", "me", "my", "our", "ours", "us", "mine", "myself", "this", "anyone"]
    other_pron = ["you", "your", "their", "they", "u"]

    text = word_tokenize(tweet_text)
    pos_list = pos_tag(text, tagset='universal')

    # TODO: work in the filter_text method here to make subjectivity more reliable
    subj = get_subjectivity(tweet_text)
    net_score = subj

    fp_pron_used = []
    other_pron_used = []

    for word_tup in pos_list:
        lower = word_tup[0].lower()
        if lower in fp_pron:
            fp_pron_used.append(lower)
        if lower in other_pron:
            other_pron_used.append(lower)


    if len(fp_pron_used) == 0:
        net_score -= 0.3
    else:
        net_score += 0.25 * len(fp_pron_used)

    if len(other_pron_used) > 0:
        net_score += 0.1 * len(other_pron_used)

    return True if net_score >= 0.25 else False

def filter_text(text):
    """
    spell check, remove @mentions
    """
    # FIXME: This shit doesn't work
    mention_expression = re.compile(r"\s([@#][\w_-]+)")

    short = reduce_lengthening(text)
    no_mentions = re.sub(mention_expression, short)
    pass

def get_datetime(text):
    """
    return datetime object
    ['created_at']:'Wed Jul 18 21:24:32 +0000 2018'

    """
    time = datetime.datetime.strptime()
    pass

def filter_tweet(tweet, search_terms="", accept_terms=[], reject_terms=[]):
    """
    filter the tweet from the stream if it is not of high quality
    """
    if type(tweet) is dict:
        if "retweeted_status" in tweet:
            return False

        text = tweet["text"]
        friends_count = tweet["user"]["friends_count"]
        #qry_type = tweet["metadata"]["result_type"]
        rt_count = tweet["retweet_count"]
        is_reply = False if tweet["in_reply_to_status_id"] is None else True
        num_mentions = len( tweet["entities"]["user_mentions"])
        url_list = tweet["entities"]["urls"]
        timestamp = get_tweet_date(tweet["created_at"])

    else:
        if hasattr(tweet, "retweeted_status"):
            return False

        text = tweet.text
        friends_count = tweet.user.friends_count
        #qry_type = tweet.metadata.result_type
        rt_count = tweet.retweet_count
        is_reply = False if tweet.in_reply_to_status_id is None else True
        num_mentions = len(tweet.entities['user_mentions'])
        url_list = tweet.entities['urls']
        search_terms = search_tms
        accept_terms = accept_tms
        reject_terms = reject_tms

    if timestamp.date() != datetime.date.today():
        return False

    bad_words = "porn pussy babe nude pornstar sex \
        naked cock cocks dick gloryhole tits anal horny cum penis"

    for word_tup in bad_words.split():

        if word_tup in text:
            return False

    if friends_count < 5:
        return False
    if num_mentions > 4:
        return False

    text_tok = word_tokenize(text)
    pos_list = pos_tag(text_tok, tagset='universal')

    flag = True
    pos_count = 0
    neg_count = 0
    for term in search_terms.split():
        if term == "OR":
            continue

        for word_tup in pos_list:

            if fuzz.token_set_ratio(term, word_tup[0]) > 85:
                pos_count += 1

                if (word_tup[1] == "NOUN" or word_tup[1] == "PRON"):
                    pos_count += 1

    if string_word_ratio(text, reject_terms) >= 90:
        neg_count += 1

    if string_word_ratio(text, accept_terms) > 85:
        pos_count += 1
    else:
        neg_count += 1

    if pos_count > neg_count:
        flag = False

    if flag and (not search_terms is None):
        return False

    return True

#####--------------- Main methods -----------------######
def string_word_ratio(a_string, b_list):
    """
    RETURN max ratio of word match in substring of b_string
    """
    a_string = a_string.lower()
    max_ratio = 0
    for b_word in b_list:
        b_word = b_word.lower()
        if b_word in a_string:
            max_ratio = 100
            break
        ratio = fuzz.token_sort_ratio(b_word, a_string)
        max_ratio = max(ratio, max_ratio)
    return max_ratio

def scan_realtime_tweets(stock_symbol: str, account_id: int = None):
    """
    Begin streaming tweets matching the stock symbol or from the account in real time.
    """
    file = open('stock_ticker_subset.csv')
    for line in file:
        data = line.split(',')
        if data[0] == stock_symbol:
            start_tweet_stream(data[1], follow_user_id=account_id)

def save_to_file(db_name: str, query: tuple, tweet: dict, polarity_score: float):
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

def search_tweets(ticker_symbol, search_terms_dic: dict):
    """
    Manage the tweet search for each company
    RETURN sentiment and purchase intent information for each company

    # TODO: perform spell correcting before passing into polarity/subjecitivty
    # TODO: Code below for "search" if-else can be condensed.
    """
    # hold sentiment and PI results for each target company
    sentiment = []
    sentiment_magnitude = []
    purchase_intent = []

    ### Search Tweets

    # if a since_id already exists, use it. else use 0 as since_id
    if "search" in index_dict[ticker_symbol]:
        found_tweets, since_id = get_search_results(search_terms_dic["name"], ticker_symbol, search_terms_dic["search"], \
                                                    since_id=index_dict[ticker_symbol]["search"])
        index_dict[ticker_symbol]["search"] = since_id
    else:
        found_tweets, since_id = get_search_results(search_terms_dic["name"], ticker_symbol, search_terms_dic["search"], since_id=0)
        index_dict[ticker_symbol]["search"] = since_id


    screen_name = search_terms_dic["name"]
    user_id = lookup_user_id(screen_name) # assume screen_name from TSD is always correct


    ### Mentions
    men_since_id = index_dict[ticker_symbol]["mentions"] if "mentions" in index_dict[ticker_symbol] else 0
    men_tweets, new_men_since_id = get_recent_mentions(screen_name, men_since_id)
    index_dict[ticker_symbol]["mentions"] = new_men_since_id

    ### Timeline
    # tl_since_id = index_dict[ticker_symbol]["timeline"] if "timeline" in index_dict[ticker_symbol] else 0
    # tl_tweets, new_tl_since_id = get_user_timeline(user_id, tl_since_id)
    # index_dict[ticker_symbol]["timeline"] = new_tl_since_id


    combined = combine_search_results(found_tweets, [], [])

    passed_tweets = []
    reject_count = 0 # count passed up tweets

    if len(combined) == 0:
        return (None, None, None, datetime.date.today())

    for tweet in combined:

        date = get_tweet_date(tweet["created_at"]).date()

        if filter_tweet(tweet, search_terms_dic["search"], search_terms_dic["accept"], search_terms_dic["reject"]):

            # check if tweet is a close copy of one already seen
            copy = False
            for passed_tweet in passed_tweets:
                if fuzz.ratio(tweet["text"], passed_tweet) > 80:
                    copy = True
                    break

            if copy == True:
                reject_count += 1
                continue


            polarity = find_text_sentiment(tweet["text"])
            subjectivity = get_subjectivity(tweet["text"])


            print ( tweet["text"] )
            print ("Polarity: " + str(polarity))
            print ("Subjectivity: " + str( subjectivity))

            shows_pi = tweet_shows_purchase_intent(tweet["text"])

            print ("Purchase Intent: " + str(shows_pi) + "\n")
            # save_to_file( "searched_tweets", ticker_symbol, tweet, polarity)

            passed_tweets.append(tweet["text"])

            sentiment.append(polarity)
            sentiment_magnitude.append(score_magnitude(polarity, 0.2))
            purchase_intent.append(1 if shows_pi else 0)

        else:
            reject_count += 1



    print ("Total Tweets found"  + str( len( combined)))
    print ("Rejected: " + str(reject_count))

    return (sentiment, sentiment_magnitude, purchase_intent, date)


def reduce_lengthening(text):
    """
    function to shorten words that have been made too long. IE "finallllllly"
    """
    pattern = re.compile(r"(.)\1{2,}")
    new_text = pattern.sub(r"\1\1", text)

    return new_text

####---------- Run Program --------------#####

with open("ticker_keywords.json") as tdk:
    ticker_keyword_dict = json.load(tdk)

# ------ STREAM ----- #
# for ticker_symbol, search_terms_dict in ticker_keyword_dic.items():

#     search_tms = search_terms_dict["search"]
#     search_tms_list = search_terms_dict["search_list"]
#     reject_tms = search_terms_dict["reject"]
#     accept_tms = search_terms_dict["accept"]
#     start_tweet_stream(search_tms_list)


# -------- SEARCH ------- #
index_dict = {x : {} for x in ticker_keyword_dict.keys()} # index's since_id's for twitter API

search_count = 0 # keep track of number of iterations of loop

# generate the score based on the search information
sentiment_score = defaultdict(float)
pi_count = defaultdict(float)
score = defaultdict(float)

ref_date_2 = datetime.date.today()

avg_sent = 0.0
num_records = 0

while running:

    search_count += 1

    for ticker_symbol, search_terms_dict in ticker_keyword_dict.items():

        set_time = time.time() #reset loop timer

        (sent, sent_mag, pi, searched_date) = search_tweets(ticker_symbol, search_terms_dict)

        num_records = len(sent)

        if searched_date > ref_date_2: # date changed, clear existing scores
            sentiment_score.clear()
            pi_count.clear()
            score.clear()
            ref_date_2 = searched_date
            num_records = 0
            avg_sent = 0.0


        avg_sent = sum(sent) / len(sent) if len(sent) != 0 else 0
        score[ticker_symbol] += 500 * avg_sent #greater score for greater avg sentiment


        pi_count[ticker_symbol] += sum(pi)

        score[ticker_symbol] += (pi_count[ticker_symbol] / len(pi) * 500) if len(pi) != 0 else 0 #greater score for larger percent PI

        sentiment_score[ticker_symbol] = sum(sent_mag)

        print ("{}: Sentiment Score: {}, Avg Sent: {}, PI count : {}, Score: {}"\
        .format(ticker_symbol, sentiment_score[ticker_symbol], avg_sent, pi_count[ticker_symbol], score[ticker_symbol]))

        # save score to database
        table = db2[ticker_symbol[0]]

        save_data = dict (
            timestamp=datetime.datetime.now(),
            score=score[ticker_symbol],
            avg_sent_float=avg_sent,
            avg_sent_mag=sentiment_score[ticker_symbol],
            pi_count=pi_count[ticker_symbol],
            iteration=search_count,
            num_tweets=num_records
        )
        table.insert(save_data)

        # pause time of loop execution until MINUTE_DELAY passes between each search_tweets call
        time_diff = time.time() - set_time
        if time_diff < (MINUTE_DELAY * 60):
            time.sleep( MINUTE_DELAY * 60 - time_diff)

    # after every complete iteration, print scores and save to file
    for company_tuple in score:
        print ("{}: Sentiment Score: {}, PI count : {}, Score: {}".format(company_tuple, sentiment_score[company_tuple] \
                                        , pi_count[company_tuple], score[company_tuple]))

    if search_count > LOOP_ITERATIONS:
        running = False
        break

    score.clear()
    sentiment_score.clear()
    pi_count.clear()

