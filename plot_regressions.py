#           PLOT REGRESSIONS                        #
#
# Purpose: analyze data inside of our database,     #
# relevant plots using matplotlib                   #

import matplotlib.pyplot as plt
import numpy as np
import datetime as DT
import dataset
import dbapi
import sqlalchemy
import pymysql
import time
import datetime

from iexfinance import Stock, get_historical_data
from collections import defaultdict
from wikipedia_trends import WikiTrends as WT

today = DT.date.today() - DT.timedelta(days = 1)
week_ago = today - DT.timedelta(days = 7)

class Analytics():
    # AWS CREDENTIALS
    HOST = "hedgedb.c288vca6ravj.us-east-2.rds.amazonaws.com"
    PORT = 3306
    DB_NAME = "scores_timeseries"
    DB_USER = "hedgeADMIN"
    DB_PW = "bluefootedboobie123"

    # connect to Datasets
    scores_db = dataset.connect("sqlite:///scorebase.db")
    AWS_RDS = dataset.connect("mysql+pymysql://{}:{}@{}/{}".format\
    (DB_USER, DB_PW, HOST, DB_NAME), engine_kwargs = {'pool_recycle': 3600})
    scores = defaultdict(float)

    # function to plot stock's last opening and closing prices across a timeframe.
    # DEFAULT TIMEFRAME IS ONE WEEK
    def score_regression(self, symbol, mode):

        if (mode == "last_week"):
            start = week_ago
            end = today
        elif (mode == "match_AWS"):
            tmp = self.get_dates_for_table(symbol)
            start = tmp[0]
            end   = tmp[1] + DT.timedelta(days = 1)

        log = get_historical_data(symbol, start = start, end = end + DT.timedelta(days = 1) , \
                                                        output_format = 'pandas')
        # print(log)

        '''
        LOG STORES:
            open, high, low, close, and volume
        PLOT DIFFERENT CHARACTERISTICS BY REFERENCING TERM AS YOU WOULD A DICTIONARY
        ex. log.plot(log["close"])
        '''

        difference = (log["close"] - log["open"])*100/log["open"]

        plt.plot(difference, color = 'g', label = 'pct change in price', marker = 'd')

        plt.legend(loc = "best")
        plt.ylabel('CHANGE (in %)')
        plt.xlabel('DATE')
        plt.xticks(rotation = 70)

        ## UNDER DEV ##
        self.get_PI_pctChng(symbol)  # return [ datetime, pct change ]
        #plt.plot(tmp[0], tmp[1], color = 'r', label = 'pct change in purchase intent', marker = 'd')
        ## UNDER DEV ##

        # normalized = normalize_PI("TSLA", start, end)

        # plt.plot(log["close"], color = 'r', label = "close")
        # plt.plot(log["open"], color = 'g', label = 'open')

        plt.show()

    def get_PI_pctChng(self, symbol):
        table_dates = []
        PI_change = []
        for date in self.scores[symbol].keys():
            table_dates.append(date)

        # PI_df = pd.DataFrame()

        for date in self.scores[symbol]:
            print (date)

        #plt.plot([ DT.date.today() ], [ 1 ], color = 'r', label = 'pct change in purchase intent')

        # exit(0)

    def get_dates_for_table(self, symbol):
        # print (len(self.scores[symbol]))
        tmp_keys = []
        for key in self.scores[symbol].keys():
            tmp_keys.append(key)

        return ( [tmp_keys[0], tmp_keys[-1]] )

    # function that returns a dataframe object with dates that are the same as
    # those in the difference log
    def normalize_PI(self, symbol, start = week_ago, end = today):
        data = dict()
        data['PI'] = list()
        data['datetime'] = list()
        for SYM in scores_db[symbol]:
            data['PI'].append(SYM['purchase_intent'])
            data['datetime'].append(SYM['datetime'])


    # TODO: enter scores based on TWEETS.
    # one entry per day???
    def populate_scores(self):
        table = scores_db["TSLA"]

        table.insert( dict (
            date = "2018_7_16",
            score = 1100
        ) )

    def AWS_refresh(self):
        print ("- - - - - - - - - -  AWS  - - - - - - - - - -")
        print ("- - - - - - - - - - - - - - - - - - - - - - -\n")

        for TABLE in self.AWS_RDS.tables:
            if (TABLE.find("WIKI") != -1):
                continue

            #print (TABLE)
            self.scores[TABLE] = defaultdict(float)   # initialize dict of scores associated with a date
                                      # { 'date': score }
            for SYM in self.AWS_RDS[TABLE]:
                #print ( "  %s | %3.2f | %i " % (SYM["timestamp"].date(), SYM["score"], SYM["num_tweets"]) )

                if (SYM["timestamp"].date() in self.scores[TABLE].keys()):
                    tmp_score = self.scores[TABLE][SYM["timestamp"].date()][0]
                    tmp_num_tweets = self.scores[TABLE][SYM["timestamp"].date()][1]

                    num_tweets = tmp_num_tweets + SYM["num_tweets"]
                    if (num_tweets == 0):
                        continue

                    score = (tmp_score * tmp_num_tweets + SYM["score"] * SYM["num_tweets"])/num_tweets

                    self.scores[TABLE][SYM["timestamp"].date()] = (score, num_tweets)
                else:
                    self.scores[TABLE][SYM["timestamp"].date()] = \
                                (SYM["score"], SYM["num_tweets"])


        for key in self.scores.keys():
            print (key, "   |            |        |")

            for SYM in self.scores[key].keys():
                print ("\t| %s | %.2f | %i" % (SYM, self.scores[key][SYM][0], self.scores[key][SYM][1]) )



# ---------------------------- MAIN -------------------------------------


an = Analytics()

#while True:
print ("\n- - - - - - - - - - - - - - - - - - - - - - -")
print ("- - - -  %s - - - - -" % datetime.datetime.now())

an.AWS_refresh()

an.score_regression("SBUX", "match_AWS")


# -------------

#wiki_poll()

#time.sleep(10)



# populate_scores()



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
