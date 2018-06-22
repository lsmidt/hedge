'''

GOAL: Poll all words that are NOT parts of speech from twitter to attempt to identify and capitalize on trends

PURPOSE:
    Potential upside for social media campaigning; trend identificiation => sudo apt-get free_pr


Max Gillespie
6/15/2018
'''

import nltk
import tweepy
import pprint
import json
import string

from nltk.corpus import stopwords
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
from nltk.tokenize import word_tokenize


''' -------------------------- INSTANTIATIONS -------------------------------'''
consumer_key = 'Q5Eyxjj0HbffR43T7ouLtpPui'
consumer_secret = 'Ai0WjHlG2f8m3fDL7PmAJ4O52Z3WGNraNnEn4X9p6pt4wHJb1I'
access_token = '1006605731267796992-bqtWgA9GKTz1Xlx8pY8JDdz5Mt9uBO'
access_secret = '11TkXZVM1bW2QbWNb2xItwXqlx03NU55UPBnU1qMQ63bz'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

punctuation = list(string.punctuation)
stop = stopwords.words('english') + punctuation + ['rt', 'via']

tweets_collected = 0

''' ----------------------------- CLASSES ----------------------------------'''
class MyListener(StreamListener):

    def on_data(self, data):
        global tweets_collected
        global j

        try:
            j.write(data)

            tweets_collected += 1
            print(tweets_collected)
            if (tweets_collected >= 2):
                return False

            return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True

    def on_error(self, status):
        print(status)
        return True


''' ---------------------------- FUNCTIONS ---------------------------------'''
def tokenize_tweets():
    f = open('python.json', 'r')
    for line in f:
        tweet = json.loads(line) # load it as Python dict
        print(word_tokenize(tweet["text"].lower())) # pretty-print


''' ------------------------------ MAIN -----------------------------------'''
topics = list()
twitter_stream = Stream(auth, MyListener())

topics.append("World Cup")

for topic in topics:
    j = open('python.json', 'w')

    twitter_stream.filter(track=[topic])
    j.close()

    tokenize_tweets()
