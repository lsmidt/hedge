'''

GOAL: Poll all words that are NOT parts of speech from twitter to attempt to identify and capitalize on trends

PURPOSE:
    Potential upside for social media campaigning; trend identificiation => sudo apt-get free_pr


Max Gillespie
6/15/2018
'''

import nltk
import tweepy

temp_trend_dictionary = dict()

s1 = "I Love chipotle!"

tagged = nltk.tag.pos_tag(s1.split(' '))

for word in tagged:
    if (word[1] == 'NN'):
        if not (word[0].lower() in temp_trend_dictionary.keys()):
            temp_trend_dictionary[ word[0] ] = 1
        else:
            temp_trend_dictionary[word[0]]+= 1


print (temp_trend_dictionary)
