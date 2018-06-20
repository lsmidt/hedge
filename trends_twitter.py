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


''' ---------------------------- INSTANTIATIONS --------------------------------'''
CONSUMER_KEY = 'zQuVUVHVWNZd7yfMNdyXx4NgJ'
CONSUMER_SECRET = 'OBMTSJfy4UHuCDSslKzZdcgcm33NChTh1m3dJLX5OhRVY5EhUc'
AXS_TOKEN_KEY = '1005588267297853441-aYFOthzthNUwgHUvMJNDCcAMn0IfsC'
AXS_TOKEN_SECRET = 'e88p7236E3nrigW1pkvmyA6hUyUWrMDQd2D7ZThbnZvoQ'

printer = pprint.PrettyPrinter()

auth = tweepy.OAuthHandler(consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET)
auth.set_access_token(key=AXS_TOKEN_KEY, secret=AXS_TOKEN_SECRET)
TWEEPY_API = tweepy.API(auth)

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
        # find_tweet_target(status.text)

        # print tweet and score
        print(status.text, '(', polarity_score, ')')


    def on_error(self, error_code):
        print("Error" + str( error_code))
        if error_code == 420:
            return False


''' ---------------------------- FUNCTIONS ------------------------------------ '''
def start_tweet_stream(search_terms: list, follow_user_id=None, filter_level="low"):
    """
    begin the streaming process. This method blocks the thread until the connection is closed by default
    """
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth, stream_listener)

    printer.pprint("NOW STREAMING")
    stream.filter(track=search_terms, filter_level=filter_level, languages = ["en"])


''' ---------------------------------- MAIN ---------------------------------- '''

start_tweet_stream( ["snap"] )

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
