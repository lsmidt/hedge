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

from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener

consumer_key = 'Q5Eyxjj0HbffR43T7ouLtpPui'
consumer_secret = 'Ai0WjHlG2f8m3fDL7PmAJ4O52Z3WGNraNnEn4X9p6pt4wHJb1I'
access_token = '1006605731267796992-bqtWgA9GKTz1Xlx8pY8JDdz5Mt9uBO'
access_secret = '11TkXZVM1bW2QbWNb2xItwXqlx03NU55UPBnU1qMQ63bz'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)

api = tweepy.API(auth)

tweets_collected = 0

class MyListener(StreamListener):

    def on_data(self, data):
        global tweets_collected

        try:
            with open('python.json', 'a') as f:
                f.write(data)

                tweets_collected += 1
                print(tweets_collected)
                if (tweets_collected >= 100):
                    return False

                return True
        except BaseException as e:
            print("Error on_data: %s" % str(e))
        return True

    def on_error(self, status):
        print(status)
        return True



twitter_stream = Stream(auth, MyListener())
twitter_stream.filter(track=['World Cup'])


'''
temp_trend_dictionary = dict()
temp_strings = { "I Love chipotle!" }

for str in temp_strings:
    tagged = nltk.tag.pos_tag(str.split(' '))

    for word in tagged:
        if (word[1] == 'NN'):
            removals = {'?', ',', '.', '!'}
            tmp = word[0]

            # strip word of any punctuation left from nltk fucking my shit
            for r in removals:
                tmp = tmp.replace(r, '')

            if not (word[0].lower() in temp_trend_dictionary.keys()):
                temp_trend_dictionary[ tmp ] = 1
            else:
                temp_trend_dictionary[ tmp ]+= 1


print (temp_trend_dictionary)
'''
