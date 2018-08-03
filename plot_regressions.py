import matplotlib.pyplot as plt
import datetime as DT
import dataset

from iexfinance import Stock, get_historical_data
from collections import defaultdict


today = DT.date.today() - DT.timedelta(days = 1)
week_ago = today - DT.timedelta(days = 7)
scores_db = dataset.connect("sqlite:///scorebase.db") # connect Dataset to Tweetbase


# function to plot stock's last opening and closing prices across a timeframe.
# DEFAULT TIMEFRAME IS ONE WEEK
def score_regression(symbol, start = week_ago, end = today):

    log = get_historical_data(symbol, start = start, end = end + DT.timedelta(days = 1) , \
                                                    output_format = 'pandas')
    print(log)

    # LOG STORES:
    #          open, high, low, close, and volume
    # PLOT DIFFERENT CHARACTERISTICS BY REFERENCING TERM AS YOU WOULD A DICTIONARY
    # ex. log.plot(log["close"])

    difference = (log["close"] - log["open"])*100/log["open"]
    plt.plot(difference, color = 'g', label = 'percent change in price', marker = 'd')

    # normalized = normalize_PI("TSLA", start, end)

    # plt.plot(log["close"], color = 'r', label = "close")
    # plt.plot(log["open"], color = 'g', label = 'open')
    plt.legend(loc = "best")
    plt.ylabel('CHANGE (in %)')
    plt.xlabel('DATE')

    plt.show()

# function that returns a dataframe object with dates that are the same as
# those in the difference log
def normalize_PI(symbol, start = week_ago, end = today):
    data = dict()
    data['PI'] = list()
    data['datetime'] = list()
    for SYM in scores_db[symbol]:
        data['PI'].append(SYM['purchase_intent'])
        data['datetime'].append(SYM['datetime'])


# TODO: enter scores based on TWEETS.
# one entry per day???
def populate_scores():
    table = scores_db["TSLA"]

    table.insert( dict (
        date = "2018_7_16",
        score = 1100
    ) )


# ---------------------------- MAIN -------------------------------------
# new datetime object: DT.datetime(2018, 7, 10)  <== {YR, MM, DD}

score_regression("SBUX")

# populate_scores()

'''
******************** DATABASE VISUALIZATION *********************
'''


#print (scores_db.tables)                                # > TSLA
#print (scores_db["AAPL"].columns)

'''
scores = defaultdict(float)
for TABLE in scores_db.tables:
    print (TABLE)
    # scores[TABLE] = defaultdict(int)   # initialize dict of scores associated with a date
                              # { 'date': score }
    for SYM in scores_db[TABLE]:
        print ( SYM["timestamp"].date(), SYM["score"] )
        # scores[SYM["timestamp"].date()] += SYM["score"]
'''
'''
print (scores_db.tables)
for table in scores:
    print(table)
'''
    #for date in scores[table]:
    #    print (string(date))




'''
for AAPL in scores_db["AAPL"]:
    print (AAPL["score"])
'''

'''
******************** DATABASE VISUALIZATION ********************
'''

'''
tsla = Stock('TSLA')
tsla.get_open()
tsla.get_price()
'''
