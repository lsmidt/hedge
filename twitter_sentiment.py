'''
GOAL: To return a confidence index of specific company stock price longevity based on major macroeconomic changes
noted by 'influential' twitter users (1,000,000+ followers)

Max Gillespie & Louis Smidt
6/09/18
'''

'''
Action Items:

2 Functions:
    Analyze sentiment of a standard person @ing a company account
    Analyze macroeconomic factors from influential individuals

Twitter Consumer Key
Analyze Tweets from speficic list of individuals
Quantify value of tweet content based on number of followers
Can you find a tweet @ an account?

dictionaries: positive correlation keywords, negative correlation keywords
'''

import twitter
api = twitter.Api(consumer_key='consumer_key',      consumer_secret='consumer_secret',
                  access_token_key='access_token',  access_token_secret='access_token_secret')


status = api.GetUserTimeline('snap')
#response = GET https://api.twitter.com/1.1/statuses/mentions_timeline.json?count=2&since_id=14927799
