'''

GOAL: Poll all words that are NOT parts of speech from twitter to attempt to identify and capitalize on trends

PURPOSE:
    Potential upside for social media campaigning; trend identificiation => sudo apt-get free_pr

TODO:
    Track sentiment in most_common_words; move toward understanding holding companies

    How can this be used in the best way possible? *** LET'S TALK ABOUT THIS ***
        1. Social Media
        2. Informing additional search items in another program?
        3. Figure out a way to identify trends for a specific company?


Max Gillespie
6/15/2018
'''

import nltk
import tweepy
import pprint
import json
import string
import operator

from tweepy import OAuthHandler
from tweepy import Stream
from collections import Counter
from tweepy.streaming import StreamListener
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


''' -------------------------- INSTANTIATIONS -------------------------------'''
consumer_key = 'Q5Eyxjj0HbffR43T7ouLtpPui'
consumer_secret = 'Ai0WjHlG2f8m3fDL7PmAJ4O52Z3WGNraNnEn4X9p6pt4wHJb1I'
access_token = '1006605731267796992-bqtWgA9GKTz1Xlx8pY8JDdz5Mt9uBO'
access_secret = '11TkXZVM1bW2QbWNb2xItwXqlx03NU55UPBnU1qMQ63bz'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

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
            if (tweets_collected >= 10):
                return False

            return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True

    def on_error(self, status):
        print(status)
        return True


''' ---------------------------- FUNCTIONS ---------------------------------'''
def tokenize_tweets(extra_stop = []):
    f = open('python.json', 'r')
    count_all = Counter()

    for line in f:
        tweet = json.loads(line) # load it as Python dict

        terms_stop = [term for term in word_tokenize(tweet['text'].lower()) if \
                                    (term not in stop and term not in extra_stop)]
        count_all.update(terms_stop)
        # print(word_tokenize(tweet["text"].lower())) # pretty-print

    # print(count_all.most_common(5)) # print 5 most common words
    return (count_all.most_common(5))

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
topics = [ ["World Cup", "Russia"] ]
# topics = [ "snapchat" ]
most_common_words = list()     # list of most common words to match each topic
twitter_stream = Stream(auth, MyListener())

for topic in topics:
    tweets_collected = 0
    j = open('python.json', 'w')

    for t in topic:
        twitter_stream.filter(track=[t])

    j.close()

    most_common_words.append(tokenize_tweets())

''' PARSING '''
for i in range(len(topics)):
    print ("---------------------------------------------------")
    for t in topics[i]:
        print(t)
    print('\t', most_common_words[i])
