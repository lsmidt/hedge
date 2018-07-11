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
        global j

        t = json.loads(data)
        if not filter_tweet(t):
            return

        try:
            j.write(data)

            tweets_collected += 1
            print(tweets_collected)

            '''
            if (tweets_collected%20 == 0):
                elapsed_time = time.time() - start_time
                #print (elapsed_time)

                if (elapsed_time > 1800):  #THIS IS 'N' SECONDS OF TWEETS
                    return False
            '''

            if (tweets_collected > 10):
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
    global avg_sentiment
    global j

    for topic in topics:
        total_sentiment = 0
        tweets_collected = 0
        j = open('python.json', 'w')

        # start_time = time.time()

        for t in topic:
            twitter_stream.filter(track=[t])

        # twitter_stream.filter(track = topic)

        tweets_per_topic.append(tweets_collected)

        j.close()

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
        avg_sentiment.append(float(tok[1]/tweets_collected))

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
    total_sentiment = 0
    f = open('python.json', 'r')
    count_all = Counter()

    for line in f:
        tweet = json.loads(line) # load it as Python dict

        terms_stop = [term for term in word_tokenize(tweet['text'].lower()) if \
                                (term not in stop and term not in extra_stop)]
        count_all.update(terms_stop)
        total_sentiment += find_tweet_sentiment(tweet)

    return ([count_all.most_common(5), total_sentiment])

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

topics = [ ["World Cup", "Mesi"], ["apple"] ]
most_common_words = list()     # list of most common words to match each topic
avg_sentiment = list()
twitter_stream = Stream(auth, MyListener())
tweets_per_topic = list()

sync(topics)

# PARSING
for i in range(len(topics)):
    print ("---------------------------------------------------")
    print ("TWEETS COLLECTED:", tweets_per_topic[i])
    for t in topics[i]:
        print(t)
    print("AVG SENTIMENT: ", avg_sentiment[i])
    print('\t', most_common_words[i])
