"""
Sentiment analysis of recent news headlines using NewsAPI and Python Natural Language Toolkit. 

Citation of VADER Sentiment Analysis Model:
Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. Eighth International Conference on Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.

News headlines powered by NewsAPI.org and IEX Trading API

Louis Smidt
05/28/2018
"""

import pprint
#import pandas as pd
import numpy as np
import requests
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mtd
from newsapi import newsapi_client
import vaderSentiment.vaderSentiment as SIA
import IEX_API_Client as IEX_Client

# set up IEX_API_Client
IEX = IEX_Client.IEX_API_Client()

# set up NewsAPI 
NEWS_API = newsapi_client.NewsApiClient(api_key='a76f5e16666f4e66aa4514ea27d425d9')

# set up sentiment analyzer VADER
sia = SIA.SentimentIntensityAnalyzer()


###-------- IEX Methods -----------###
    

def iex_format_data(symbol, data):
    """
    INPUT decoded JSON data from IEX news archive. Output of "get_news_data".
    RETURN {symbol : [(article text, polarity score, source, datetime)]} for SINGLE stock symbol
    """ 
    results_dict = {}

    results_dict[symbol] = []

    for article_dict in data:
        # combine headline and summary, get polarity score 
        if article_dict["summary"] == "No summary available.":
            full_text = article_dict["headline"]
        else:
            full_text = article_dict["headline"] + ". " + article_dict["summary"]

        polarity_score = get_polarity_score(full_text)

        # get source
        source = article_dict["source"]

        # get date/time stamp
        date_time = article_dict["datetime"]
        dt = date_to_datetime(date_time)

        # create results tuple
        results_dict[symbol].append((full_text, polarity_score, source, dt))

    print("Number of articles for" + symbol + "= " + str(len(results_dict[symbol])))

    return results_dict 


def run_iex_scan(query_list):
    """
    INPUT list of stock symbol queries
    Abstracts code to run multiple queries at once.
    """

    IEX_results_dict = {}
    IEX_aggregate_dict = {}
    for query in query_list:
        IEX_data = IEX.get_news_data(query)
        fmt_data = iex_format_data(query, IEX_data)

        avg = average_net_scores_over_time(fmt_data[query], find_earliest_time(fmt_data[query]))
        IEX_aggregate_dict[query] = avg

        IEX_results_dict.update(fmt_data)
        #bar_plot_scores(IEX_results_dict[query], query)
        scatter_plot_scores(IEX_results_dict[query], query)

    iex_final = classify_polarity_dictionary(IEX_aggregate_dict)

    printer = pprint.PrettyPrinter(width=40, compact=False)
    print("Aggregate News polarity score ")
    printer.pprint(IEX_aggregate_dict)

    return iex_final


###-------- Common Methods ----------###

def find_earliest_time(article_list):
    """
    RETURN datetime object of earliest article
    INPUT [(text, score, source, datetime object)]
    """

    dates_list = []
    for article_tuple in article_list:
        dates_list.append(article_tuple[3])

    return min(dates_list)

def find_latest_time(article_list):
    """
    RETURN datetime object of earliest article
    INPUT [(text, score, source, datetime object)]
    """

    dates_list = []
    for article_tuple in article_list:
        dates_list.append(article_tuple[3])

    return max(dates_list)


def classify_polarity_dictionary(aggregate_score_dict):
    """
    INPUT a polarity score dictionary {symbol : polarity score}
    RETURN 1 for positive, -1 for negative, 0 for neutral

    for single query
    """
    result_dict = {}

    for query, score in aggregate_score_dict.items():
        if type(score) == type("str"):
            result_dict[query] = "No Articles"
        elif score > 0.2:
            result_dict[query] = "1"
        elif score < -0.2:
            result_dict[query] = "0"
        else:
            result_dict[query] = "-1"

    return result_dict
    
def classify_polarity_score(score):
    """
    classify a single float
    RETURN 1, 0, -1
    """
    if score > 0.2 :
        return 1
    elif score < -0.2:
        return -1
    else:
        return 0

def average_net_scores_over_time(article_list, start, end=datetime.datetime.now()):
    """
    INPUT [(text, score, source, datetime object), (...)] as article_list; start datetime object, end datetime object
        if no end is given all until present moment are calculated

    RETURN average of the sentiment scores for each query over the timeframe from start forward to end

    Result is 0 if no articles are present OR if arithmetic average over timeframe is exactly 0. 

    for single queries
    """
    avg = 0.0
    article_count = 0

    for article_tuple in article_list:
        if (article_tuple[3] > start) & (article_tuple[3] < end):
            score = article_tuple[1]
            avg += score
            article_count += 1

    if(article_count > 0):
        avg = avg / article_count

    else:
        avg = 0

    return avg
    

# def average_daily_scores(article_list):
#     """
#     INPUT [(score, datetime)] for each article
#     RETURN [(score, datetime)] where each datetime is a unique day and score represents the 
#             average of all scores for articles on that day 
#     """

#     daily_list = []

#     for sd_tuple in article_list:
        


def date_to_datetime(date_time):
    """
    INPUT combined datetime string output from IEX API
    RETURN (date, time)
    """
    split = date_time.split(sep="T", maxsplit=1)

    short_time = split[1].split(sep="-")[0]

    time = datetime.datetime.strptime(split[0] + " " + short_time, "%Y-%m-%d %H:%M:%S")

    return time

def classify_change_percentage(change_percentage):
    """
    Classify the change percentage of a stock as Positive, Negative or Neutral (1, -1, 0)
    """
    if change_percentage > 0.2 :
        return 1
    elif change_percentage < -0.2:
        return 0
    else:
        return -1


def scatter_plot_scores(article_list, title):
    """
    plot article dates with their polarity scores
    INPUT [(text, polarity score, source, datetime object), (...)]
    """
    date_list = []
    score_list = []
    classified_list = []

    for article_tuple in article_list:
        date_list.append(article_tuple[3])
        score_list.append(article_tuple[1])
        classified_list.append(classify_polarity_score((article_tuple)[1]))
        

    # TODO: normalize date range so only one score exists per day. Not finished

    # remove_date_indicies = []

    # for i in range(0, len(date_list)):
    #     date = date_list[i].date()
    #     avg = score_list[i]
    #     num_on_day = 1
    #     for j in range(0, len(date_list)):
    #         other_date = date_list[j].date()
    #         if (date == other_date) & (i != j):
    #             avg += score_list[j]
    #             num_on_day += 1
    #             remove_date_indicies.append(j)
    #             score_list.pop(j)
        
    #     for index in range(0, len(remove_date_indicies)):
    #         date_list.pop(index)

    #     remove_date_indicies.clear()
        
    #     score_list[i] = float(avg / num_on_day)


    plot_dates = mtd.date2num(date_list)
    plt.plot_date(plot_dates, score_list)
    plt.title(title)

    x_tick_locator = mtd.AutoDateLocator(maxticks=50,minticks=2, interval_multiples=True)
    x_tick_formatter = mtd.AutoDateFormatter(x_tick_locator)

    axis = plt.axes()
    axis.xaxis.set_major_locator(x_tick_locator)
    axis.xaxis.set_major_formatter(x_tick_formatter)

    plt.show()


def bar_plot_scores(article_list, title):
    """
    Create bar plot of scores
    """
    classified_list = []
    date_list = []

    for article_tuple in article_list:
        classified_list.append(classify_polarity_score((article_tuple)[1]))
        date_list.append(article_tuple[3])


    axis = plt.subplot(111)
    axis.bar(date_list, classified_list, width=1)
    axis.xaxis_date()
    plt.title(title)

    plt.show()

def get_polarity_score(text):
    """
    RETURN VADER result on text block
    """

    sia2 = SIA.SentimentIntensityAnalyzer()
    scores = sia2.polarity_scores(text)
    return scores["compound"]


def run_news_scan(queries):
    """
    Run the scan on list of queries
    RETURN categorized scores dictionary. {Symbol : score}
    """

    # first run NewsAPI scan 
    #scores_dict = news_api_get_scores(queries)
    #agg = average_net_scores_over_time(scores_dict)
    #final = classify_polarity_dictionary(agg)

    printer = pprint.PrettyPrinter(width=40)
    #printer.pprint("Aggregate NewsAPI" + str(agg))

    # then run IEX scan

    iex_final = run_iex_scan(queries)
   
    # combine results dictionaries
    #final.update(iex_final)

    return iex_final



###------------ NewsAPI Methods -----------###

def news_api_format_data(news_api_object):
    """
    Extract the headlines and descriptions from a NewsAPI Headlines object into two lists

    INPUT JSON data file of articles of fromat returned by NewsAPI.get_top_headlines()
    RETURN [(title, description), (..., ...) ] for each article

    works on single query
    """
    title = []
    desc = []    
    date_time = []
    source = []

    for key, value in news_api_object.items():
        if key == "articles":
            for article_dict in value:
                    title.append(article_dict["title"])
                    desc.append(article_dict["description"])
                    date_time.append(article_dict["publishedAt"])
                    source.append(article_dict["source"]["name"])


    return list(zip(title, desc, source, date_time))


def news_api_get_scores(query_list):
    """
    INPUT the news query
    RETURN query : [(article, score), (...)]
    
    multiple queries
    """
    results_dict = {}
    
    # iterate over every stock symbol query 
    for query in query_list:
        headline_obj = NEWS_API.get_top_headlines(language="en", q=query, country="us")
    
        headline_list = news_api_format_data(headline_obj)
        results_dict[query] = []
        print("Number of articles for " + query + str(len(headline_list)))
        
        # extract headlines, get scores
        for td_tuple in headline_list:
            combined_txt = td_tuple[0] + ". " +  td_tuple[1]
            article_polarity = get_polarity_score(combined_txt)
            results = (td_tuple[0], article_polarity, td_tuple[2], td_tuple[3])
            results_dict[query].append(results)

    return results_dict





# run program

result = run_news_scan(["AA", "TIVO"])
print(result)




