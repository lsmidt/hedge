'''
GOAL: Poll all words that are NOT parts of speech from twitter to attempt to identify and capitalize on trends

PURPOSE:
    Potential upside for social media campaigning; trend identificiation => sudo apt-get free_pr
    understand most common words around a set of topics
    Inform decisions by understanding what people are talking about most frequently
        -Ability to look at most common words in POSITIVE tweets
        -Ability to look at most common words in NEGATIVE tweets
        -Average POSITIVE and NEGATIVE post scores

TODO:
    Phase out streaming functionality
    Begin using twitter's 7-day backsearch functionality

    Plotting purchase intent on twitter_sentiment.py?

Max Gillespie
6/15/2018 --------> FIRST COMMIT
7/16/2018 --------> MOST RECENT COMMIT
'''

''' ----------------------------- MODULES ----------------------------------'''
import nltk
import tweepy
import pprint
import json
import string
import operator
import time
import re

from twython import Twython # used for mentions
from tweepy import OAuthHandler
from tweepy import Stream
from collections import Counter
from nltk import pos_tag
from fuzzywuzzy import fuzz
from tweepy.streaming import StreamListener
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict
import vaderSentiment.vaderSentiment as sia


''' -------------------------- INSTANTIATIONS -------------------------------'''
consumer_key = 'Q5Eyxjj0HbffR43T7ouLtpPui'
consumer_secret = 'Ai0WjHlG2f8m3fDL7PmAJ4O52Z3WGNraNnEn4X9p6pt4wHJb1I'
access_token = '1006605731267796992-bqtWgA9GKTz1Xlx8pY8JDdz5Mt9uBO'
access_secret = '11TkXZVM1bW2QbWNb2xItwXqlx03NU55UPBnU1qMQ63bz'

CONSUMER_KEY = 'zQuVUVHVWNZd7yfMNdyXx4NgJ'
CONSUMER_SECRET = 'OBMTSJfy4UHuCDSslKzZdcgcm33NChTh1m3dJLX5OhRVY5EhUc'
AXS_TOKEN_KEY = '1005588267297853441-aYFOthzthNUwgHUvMJNDCcAMn0IfsC'
AXS_TOKEN_SECRET = 'e88p7236E3nrigW1pkvmyA6hUyUWrMDQd2D7ZThbnZvoQ'


auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

SIA = sia.SentimentIntensityAnalyzer()

TWY = Twython(app_key=CONSUMER_KEY, app_secret=CONSUMER_SECRET, \
oauth_token=AXS_TOKEN_KEY, oauth_token_secret=AXS_TOKEN_SECRET)

index_dict = {} # hold twitter since_ids for each searched company

punctuation = list(string.punctuation)
stop = stopwords.words('english') + punctuation + \
        ['rt', 'via', ':', 'https', '@', "'", "''", '...', '’', "'s", "n't", \
        '“', '”', '``', 'de', 'lol', 'haha']


''' ----------------------------- CLASSES ----------------------------------'''
class MyListener(StreamListener):

    def on_data(self, data):
        global tweets_collected
        global j_pos
        global j_neg

        t = json.loads(data)
        if not filter_tweet_stream(t):
            return

        try:
            # if positive sentiment, write to j_pos
            # else, write to j_neg
            if (find_tweet_sentiment(t) > 0):
                j_pos.write(data)
            else:
                j_neg.write(data)

            tweets_collected += 1
            print(tweets_collected)

            '''
            if (tweets_collected%20 == 0):
                elapsed_time = time.time() - start_time
                #print (elapsed_time)

                if (elapsed_time > 1800):  #THIS IS 'N' SECONDS OF TWEETS
                    return False
            '''

            if (tweets_collected > 50):
                return False

            return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True

    def on_error(self, status):
        print(status)
        return True


''' ---------------------------- FUNCTIONS ---------------------------------'''
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

        '''
        combined = combine_search_results(found_tweets, [], [])

        passed_tweets = []
        reject_count = 0 # count passed up tweets

        for tweet in combined:
            if filter_tweet(tweet, search_dict["search"], search_dict["accept"], search_dict["reject"]):

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

                polarity = find_tweet_sentiment(tweet)
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
        '''

    #return (sentiment, sentiment_magnitude, purchase_intent)

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

def lookup_user_id(screen_name: str) -> int:
    """
    Return the user_id of the account associated with the string
    """
    user = TWY.show_user(screen_name=screen_name)
    return user["id"]

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

def combine_search_results(first, second, third):
    """
    Combine search, account mentions, and timeline results. Three lists of tweets
    """
    combined = [tweet for tweet in first]
    a = [tweet for tweet in second]
    b = [tweet for tweet in third]

    return combined + a + b

def string_word_ratio(a_word, b_string):
    """
    RETURN max ratio of word match in substring of b_string
    """
    max_ratio = 0
    for b_word in b_string.split():
        ratio = fuzz.ratio(b_word, a_word)
        max_ratio = max(ratio, max_ratio)

    return max_ratio

def reduce_lengthening(text):
    """
    function to shorten words that have been made too long. IE "finallllllly"
    """
    pattern = re.compile(r"(.)\1{2,}")
    new_text = pattern.sub(r"\1\1", text)

    return new_text

def sync_stream(topics):
    global most_common_words
    global tweets_per_topic
    global tweets_collected
    global j_pos
    global j_neg
    global pos_sentiment
    global neg_sentiment

    for topic in topics:
        total_sentiment = 0
        tweets_collected = 0
        j_pos = open('positive.json', 'w')
        j_neg = open('negative.json', 'w')

        # start_time = time.time()

        for t in topic:
            twitter_stream.filter(track=[t])

        # twitter_stream.filter(track = topic)

        tweets_per_topic.append(tweets_collected)

        j_pos.close()
        j_neg.close()

        extra_stop = list()
        for t in topic:
            temp = word_tokenize(t.lower())

            if len(temp) == 1:
                extra_stop.append(temp[0])
            else:
                for i in range(0, len(temp)):
                    extra_stop.append(temp[i])

        tok = tokenize_tweets(extra_stop)
        most_common_words.append(tok[0])
        pos_sentiment.append( float(tok[1][0]/tok[2][0]) )
        neg_sentiment.append( float(tok[1][1]/tok[2][1]) )

def find_tweet_sentiment(tweet) -> float:
    """
    determine the sentiment of a tweet for a specific company
    """
    if type(tweet) is dict:
        text = tweet["text"]
    else:
        text = tweet.text

    return SIA.polarity_scores(text)["compound"]

def tokenize_tweets(extra_stop = []):
    f_pos = open('positive.json', 'r')
    f_neg = open('negative.json', 'r')
    files = [ f_pos, f_neg ]
    file_counter = 0
    count = list()
    num_collected = list()
    total_sentiment = [ 0, 0 ]

    for f in files:
        count_all = Counter()
        tweets_collected = 0

        for line in f:
            tweet = json.loads(line) # load it as Python dict
            tweets_collected += 1

            terms_stop = [term for term in word_tokenize(tweet['text'].lower()) if \
                                    (term not in stop and term not in extra_stop)]
            count_all.update(terms_stop)
            total_sentiment[file_counter] += find_tweet_sentiment(tweet)

        num_collected.append(tweets_collected)
        count.append(count_all.most_common(5))
        file_counter += 1

    return ([count, total_sentiment, num_collected])

def filter_tweet_stream(tweet):
    """
    filter the tweet from the stream if it is not useful
    """

    if 'retweeted' in tweet:
        if tweet['retweeted']:
            return False
    if 'friends_count' in tweet:
        if tweet['friends_count'] < 1000:
            return False

    return True

def filter_tweet(tweet, search_terms="", accept_terms="", reject_terms=""):
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
        naked cock cocks dick gloryhole tits anal horny cum penis"

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

    flag = True
    search_passed = False
    pos_count = 0
    neg_count = 0
    for term in search_terms.split():
        if term == "OR":
                continue

        for word_tup in pos_list:

            if fuzz.token_set_ratio(term, word_tup[0]) > 85:
                pos_count += 1

                if (word_tup[1] == "NOUN" or word_tup[1] == "PRON"):
                    pos_count += 2
                    #flag = False

            if string_word_ratio(word_tup[0], reject_terms) >= 95:
                neg_count += 1

            if string_word_ratio(word_tup[0], accept_terms) > 95:
                print ("ACCEPT TERM: " + word_tup[0])
                pos_count += 1

    if pos_count > neg_count:
        flag = False

    if flag and (not search_terms is None):
        print ("REJECTED")
    print("pos {} neg {}".format(pos_count, neg_count))

    # if "http" in text:
    #     print ("REJECT: URL in text")
    #     print (text)
    #    return False
    # if not tweet_shows_purchase_intent(text):
    #     return False

    return True


''' ------------------------------ MAIN -----------------------------------'''
# topics = [ ["Programming", "Python", "Computer Science"], ["Lego"], ]
# topics = [ ["World Cup", "Mesi"], ["Lego"] ]

'''
TEST FOR National Beverage Holding Co. (FIZZ)

topics = [ ["Shasta", "Faygo", "Everfresh", "La Croix", "Rip It", "Clearfruit", \
            "Mr. Pure", "Ritz", "Crystal Bay", "Cascadia", "Ohana", "Big Shot", \
            "St. Nick's", "Double Hit"] ]
'''

# topics = [ ["World Cup", "Mesi"], [ "crypto", "cryptocurrency", "bitcoin", "coinbase"]]
topics = [ ["Netflix"], [ "crypto", "cryptocurrency", "bitcoin", "coinbase"], [ "snapchat", "snap inc" ] ]
most_common_words = list()     # list of most common words to match each topic
pos_sentiment = list()
neg_sentiment = list()
hash_sentiment = list()
twitter_stream = Stream(auth, MyListener())
tweets_per_topic = list()
search_dict = {#("AAPL", "Apple") : {"search" : "iphone OR iPad OR ios", \
               #                     "accept" : "apple",
               #                     "reject" : "pie"},
                ("SNAP", "Snap"): { "search" : "Snap OR Snapchat", \
                                    "accept" : "Snapchat snap-story on-snap our-snap snap-me",
                                    "reject" : ""}
               }
index_dict = {x : {} for x in search_dict.keys()}


search_tweets(search_dict)

'''
sync_stream(topics)

# PARSING
for i in range(len(topics)):
    print ("---------------------------------------------------")
    print ("TWEETS COLLECTED:", tweets_per_topic[i])
    for t in topics[i]:
        print(t)
    print("POS SENTIMENT: ({})".format(pos_sentiment[i]))
    print(most_common_words[i][0])
    print("NEG SENTIMENT: ({})".format(neg_sentiment[i]))
    print(most_common_words[i][1])
'''
