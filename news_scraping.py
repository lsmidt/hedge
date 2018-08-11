# Goals:    combine wikipedia trends, scorebase.db, hedge_neural_net, and
#           trends_twitter in a meaningful way;
#           1. read in data from wikipedia trends and scorebase
#           2. TWO Options:
#                a) [EASY] plot last 90 days, scan every hour for breaks from
#                   90 day standard deviation of moving average
#                b) [HARDER] based on prediation from hedge_neural_net, scan
#                   every hour to predict breaks before they happen
#           3. Based on predictions, write to an easy to understand file
#              with conceptual news posts to make on social with a topic,
#              followed by the top 10 keywords from that topic on tweets in the
#              last hour

import matplotlib.pyplot as plt
import dataset
import dbapi
import time
import datetime

from iexfinance import Stock, get_historical_data
from collections import defaultdict
from wikipedia_trends import WikiTrends as WT
