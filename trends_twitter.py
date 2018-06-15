'''

GOAL: Poll all words that are NOT parts of speech from twitter to attempt to identify and capitalize on trends

PURPOSE:
    Potential upside for social media campaigning; trend identificiation => sudo apt-get free_pr


Max Gillespie
6/15/2018
'''

#from nltk.tokenize import TweetTokenizer
import nltk

#from nltk.tokenize import TweetTokenizer
#tknzr = nltk.tokenize.TweetTokenizer()



s1 = "I Love chipotle!"
#tokens = tknzr.tag(s1)
tagged = nltk.tag.pos_tag(s1.split(' '))

print (tagged)
