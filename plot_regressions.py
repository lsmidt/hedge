import matplotlib.pyplot as plt
import datetime as DT
import dataset
import dbapi
import sqlalchemy
import pymysql
import time
import datetime

from iexfinance import Stock, get_historical_data
from collections import defaultdict


today = DT.date.today() - DT.timedelta(days = 1)
week_ago = today - DT.timedelta(days = 7)

# AWS CREDENTIALS
HOST = "hedgedb.c288vca6ravj.us-east-2.rds.amazonaws.com"
PORT = 3306
DB_NAME = "scores_timeseries"
DB_USER = "hedgeADMIN"
DB_PW = "bluefootedboobie123"

# connect to Datasets
scores_db = dataset.connect("sqlite:///scorebase.db")
AWS_RDS =  dataset.connect("mysql+pymysql://{}:{}@{}/{}".format\
(DB_USER, DB_PW, HOST, DB_NAME), engine_kwargs = {'pool_recycle': 3600})

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

# score_regression("SBUX")

# populate_scores()

'''
******************** DATABASE VISUALIZATION *********************
'''


#print (scores_db.tables)                                # > TSLA
#print (scores_db["AAPL"].columns)

scores = defaultdict(float)

'''
print ("- - - - - - - - - - - - - - - - - - - - - - -")
print ("- - - - - - - - - - LOCAL - - - - - - - - - -")
print ("- - - - - - - - - - - - - - - - - - - - - - -\n")

print ("-------------------- PRE --------------------")

for TABLE in scores_db.tables:
    print (TABLE)
    scores[TABLE] = defaultdict(float)   # initialize dict of scores associated with a date
                              # { 'date': score }
    for SYM in scores_db[TABLE]:
        print ( "  %s | %3.2f | %i " % (SYM["timestamp"].date(), SYM["score"], SYM["num_tweets"]) )

        if (SYM["timestamp"].date() in scores[TABLE].keys()):
            tmp_score = scores[TABLE][SYM["timestamp"].date()][0]
            tmp_num_tweets = scores[TABLE][SYM["timestamp"].date()][1]

            num_tweets = tmp_num_tweets + SYM["num_tweets"]
            if (num_tweets == 0):
                continue

            score = (tmp_score * tmp_num_tweets + SYM["score"] * SYM["num_tweets"])/num_tweets

            scores[TABLE][SYM["timestamp"].date()] = (score, num_tweets)
        else:
            scores[TABLE][SYM["timestamp"].date()] = \
                        (SYM["score"], SYM["num_tweets"])


print ("-------------------- POST --------------------")
print (" STOCK  |    DATE    | SCORE  | # TWEETS")
print ("-----------------------------------------")
for key in scores.keys():
    print (key, "   |            |        |")

    for SYM in scores[key].keys():
        print ("\t| %s | %.2f | %i" % (SYM, scores[key][SYM][0], scores[key][SYM][1]) )
'''

while True:
    print ("\n- - - - - - - - - - - - - - - - - - - - - - -")
    print ("- - - - - - - - - -  AWS  - - - - - - - - - -")
    print ("- - - -  %s - - - - -" % datetime.datetime.now())
    print ("- - - - - - - - - - - - - - - - - - - - - - -")
    for TABLE in AWS_RDS.tables:
        if (TABLE.find("WIKI") != -1):
            continue

        #print (TABLE)
        scores[TABLE] = defaultdict(float)   # initialize dict of scores associated with a date
                                  # { 'date': score }
        for SYM in AWS_RDS[TABLE]:
            #print ( "  %s | %3.2f | %i " % (SYM["timestamp"].date(), SYM["score"], SYM["num_tweets"]) )

            if (SYM["timestamp"].date() in scores[TABLE].keys()):
                tmp_score = scores[TABLE][SYM["timestamp"].date()][0]
                tmp_num_tweets = scores[TABLE][SYM["timestamp"].date()][1]

                num_tweets = tmp_num_tweets + SYM["num_tweets"]
                if (num_tweets == 0):
                    continue

                score = (tmp_score * tmp_num_tweets + SYM["score"] * SYM["num_tweets"])/num_tweets

                scores[TABLE][SYM["timestamp"].date()] = (score, num_tweets)
            else:
                scores[TABLE][SYM["timestamp"].date()] = \
                            (SYM["score"], SYM["num_tweets"])


    for key in scores.keys():
        print (key, "   |            |        |")

        for SYM in scores[key].keys():
            print ("\t| %s | %.2f | %i" % (SYM, scores[key][SYM][0], scores[key][SYM][1]) )

    time.sleep(10)



#print (scores_db.tables)
#print (AWS_RDS.tables)

#for table in scores:
#    print(table)



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
