'''

GOAL: Poll all words that are NOT parts of speech from twitter to attempt to identify and capitalize on trends

PURPOSE:
    Potential upside for social media campaigning; trend identificiation => sudo apt-get free_pr

TODO:
    POSITIVE, NEGATIVE, HASHTAG most common words
    Sentiment scores for each

Max Gillespie
6/15/2018
'''

import nltk
import tweepy
import pprint
import json
import string
import operator
import time

from tweepy import OAuthHandler
from tweepy import Stream
from collections import Counter
from tweepy.streaming import StreamListener
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import vaderSentiment.vaderSentiment as sia


''' -------------------------- INSTANTIATIONS -------------------------------'''
consumer_key = 'Q5Eyxjj0HbffR43T7ouLtpPui'
consumer_secret = 'Ai0WjHlG2f8m3fDL7PmAJ4O52Z3WGNraNnEn4X9p6pt4wHJb1I'
access_token = '1006605731267796992-bqtWgA9GKTz1Xlx8pY8JDdz5Mt9uBO'
access_secret = '11TkXZVM1bW2QbWNb2xItwXqlx03NU55UPBnU1qMQ63bz'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

SIA = sia.SentimentIntensityAnalyzer()

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
        if not filter_tweet(t):
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

            if (tweets_collected > 30):
                return False

            return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True

    def on_error(self, status):
        print(status)
        return True


''' ---------------------------- FUNCTIONS ---------------------------------'''
def sync(topics):
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

        '''
        for t in topic:
            twitter_stream.filter(track=[t])
        '''
        twitter_stream.filter(track = topic)

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

        pos_sentiment.append(float(tok[1][0]/tok[2][0]))
        neg_sentiment.append(float(tok[1][1]/tok[2][1]))

        #print ("{}/{}".format(tok[1][0], tok[2][0] ))
        #print ("{}/{}".format(tok[1][1], tok[2][1] ))


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
    total_sentiment = [ 0, 0 ]
    f_pos = open('positive.json', 'r')
    f_neg = open('negative.json', 'r')
    files = [ f_pos, f_neg ]
    file_counter = 0
    count = list()
    total_tweets = list()

    for f in files:
        count_all = Counter()
        total_collected = 0

        for line in f:
            tweet = json.loads(line) # load it as Python dict

            terms_stop = [term for term in word_tokenize(tweet['text'].lower()) if \
                                    (term not in stop and term not in extra_stop)]
            count_all.update(terms_stop)
            total_sentiment[file_counter] += find_tweet_sentiment(tweet)
            total_collected += 1

        total_tweets.append(total_collected)
        count.append(count_all.most_common(5))
        file_counter += 1

    return ([count, total_sentiment, total_tweets])

def filter_tweet(tweet):
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


''' ------------------------------ MAIN -----------------------------------'''
# topics = [ ["Programming", "Python", "Computer Science"], ["Lego"], ]
# topics = [ ["World Cup", "Mesi"], ["Lego"] ]

'''
TEST FOR National Beverage Holding Co. (FIZZ)

topics = [ ["Shasta", "Faygo", "Everfresh", "La Croix", "Rip It", "Clearfruit", \
            "Mr. Pure", "Ritz", "Crystal Bay", "Cascadia", "Ohana", "Big Shot", \
            "St. Nick's", "Double Hit"] ]
'''

topics = [ [ "bitcoin" ], ["BMW"], ["Shasta", "Faygo", "Everfresh", "La Croix", "Rip It", "Clearfruit", \
            "Mr. Pure", "Ritz", "Crystal Bay", "Cascadia", "Ohana", "Big Shot", \
            "St. Nick's", "Double Hit"] ]
most_common_words = []     # list of most common words to match each topic
pos_sentiment = []
neg_sentiment = []
hash_sentiment = []
twitter_stream = Stream(auth, MyListener())
tweets_per_topic = []

sync(topics)

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
