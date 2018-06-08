"""
Sentiment analysis of recent news headlines using IEX Trading News and Python Natural Language Toolkit. 

Citation of VADER Sentiment Analysis Model:
Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text. Eighth International Conference on Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.

News headlines powered by NewsAPI.org and IEX Trading API

Louis Smidt
05/28/2018
"""

import pprint
import datetime
#import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mtd
from newsapi import newsapi_client
import vaderSentiment.vaderSentiment as sia
import IEX_API_Client as IEX_Client

# set up IEX_API_Client
IEX = IEX_Client.IEX_API_Client()

# set up NewsAPI 
NEWS_API = newsapi_client.NewsApiClient(api_key='a76f5e16666f4e66aa4514ea27d425d9')

# set up sentiment analyzer VADER
SIA = sia.SentimentIntensityAnalyzer()


###-------------------- IEX Methods -------------------###
    
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
        datetime_string = article_dict["datetime"]
        datetime_object = date_to_datetime(datetime_string)

        # create results tuple
        results_dict[symbol].append((full_text, polarity_score, source, datetime_object))

    print("Number of articles for" + symbol + "= " + str(len(results_dict[symbol])))

    return results_dict 


def run_iex_scan(query_list):
    """
    INPUT list of stock symbol queries
    Abstracts code to run multiple queries at once.
    """
    
    iex_results_dict = {}
    iex_aggregate_dict = {}

    for query in query_list:
        # for each query, get news data, format it, add to results dictionary
        iex_data = IEX.get_news_data(query)
        fmt_data = iex_format_data(query, iex_data)
        iex_results_dict.update(fmt_data)

        # find the combined average sentiment score over the time period of the news, for each query
        avg = average_net_scores_over_time(fmt_data[query], find_earliest_date(fmt_data[query]))
        iex_aggregate_dict[query] = avg

        # plot scores
        # TODO: in this method, calculate normalized scores before passing to plot methods
        bar_plot_scores(iex_results_dict[query], query)
        # scatter_plot_scores(iex_results_dict[query], query)

    iex_final = classify_polarity_dictionary(iex_aggregate_dict)

    printer = pprint.PrettyPrinter(width=40, compact=False)
    print("Aggregate News polarity score ")
    printer.pprint(iex_aggregate_dict)

    return iex_final


###------------------ Common Methods --------------------###

def find_earliest_date(article_list):
    """
    RETURN datetime object of earliest article
    INPUT [(text, score, source, datetime object)]
    """

    dates_list = []
    for article_tuple in article_list:
        dates_list.append(article_tuple[3])

    return min(dates_list).date()

def find_latest_date(article_list):
    """
    RETURN datetime object of earliest article
    INPUT [(text, score, source, datetime object)]
    """

    dates_list = []
    for article_tuple in article_list:
        dates_list.append(article_tuple[3])

    return max(dates_list)

def get_polarity_score(text):
    """
    RETURN VADER result on text block
    """

    scores = SIA.polarity_scores(text)
    return scores["compound"]


def classify_polarity_dictionary(aggregate_score_dict):
    """
    INPUT a polarity score dictionary {symbol : polarity score}
    RETURN 1 for positive, -1 for negative, 0 for neutral

    for single query
    """
    result_dict = {}

    for query, score in aggregate_score_dict.items():
        if isinstance(score, str):
            result_dict[query] = "No Articles"
        elif score > 0.2:
            result_dict[query] = "1"
        elif score < -0.2:
            result_dict[query] = "-1"
        else:
            result_dict[query] = "0"

    return result_dict
    

def average_net_scores_over_time(article_list, start_date, end_date=datetime.date.today()):
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
        if (article_tuple[3].date() > start_date) & (article_tuple[3].date() < end_date):
            score = article_tuple[1]
            avg += score
            article_count += 1

    if article_count > 0:
        avg = avg / article_count

    else:
        avg = 0

    return avg
        
def daterange(start_date, end_date):
    """
    Produces a generator for dates, allowing for easy iteration over a range of dates. 
    """
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

def date_to_datetime(date_time):
    """
    INPUT combined datetime string output from IEX API
    RETURN (date, time)
    """
    split = date_time.split(sep="T", maxsplit=1)

    short_time = split[1].split(sep="-")[0]

    time = datetime.datetime.strptime(split[0] + " " + short_time, "%Y-%m-%d %H:%M:%S")

    return time

def classify_score(change_percentage: float, confidence_interval=0.2) -> float:
    """
    Classify the change percentage of a stock as Positive, Negative or Neutral (1, -1, 0)
    """
    if change_percentage > confidence_interval:
        return 1.0
    elif change_percentage < -confidence_interval:
        return -1.0
    
    return 0.0

def normalize_date_scores(scores, start_date, end_date=datetime.date.today()):
    """
    RETURN {datetime : score , ...} for each datetime in given daterange, where score is an average of the daily scores
    INPUT [(date, score), (date, score), ...]
    """
    
    date_scores = {}
    final_dict = {}

    # build final dict with all dates in range
    for n in daterange(start_date, end_date):
        final_dict[n] = 0
        date_scores[n] = []

    # fill score dictionary
    for score in scores:
        score_date = score[0]
        if (score_date >= start_date) & (score_date <= end_date):
            date_scores[score_date].append(score[1])

    # normalize score dictionary into finals dict
    for date, score_list in date_scores.items():
        avg = 0
        num = 0
        for score in score_list:
            avg += score
            num += 1
        avg = 0 if num == 0 else float(avg / num)
        final_dict[date] = avg

    return final_dict
        

def scatter_plot_scores(article_list, symbol):
    """
    plot article dates with their polarity scores
    INPUT [(text, polarity score, source, datetime object), (...)]
    """
    date_list = []
    score_list = []
    classified_score_list = []

    for article_tuple in article_list:
        date_list.append(article_tuple[3])
        score_list.append(article_tuple[1])
        classified_score_list.append(classify_score((article_tuple)[1]))

    # TODO Add support for plotting normalized date-scores

    plot_dates = mtd.date2num(date_list)
    plt.plot_date(plot_dates, score_list)
    plt.title(symbol)

    x_tick_locator = mtd.AutoDateLocator(maxticks=50, minticks=2, interval_multiples=True)
    x_tick_formatter = mtd.AutoDateFormatter(x_tick_locator)

    axis = plt.axes()
    axis.xaxis.set_major_locator(x_tick_locator)
    axis.xaxis.set_major_formatter(x_tick_formatter)

    plt.show()


def bar_plot_scores(article_list, symbol):
    """
    Create bar plot of scores

    INPUT: [(title, score, source, datetime), (...), ...]
    """

    # unpack atricle_list into a classified score list and a date list, both lists of Date objects
    date_list = [x.date() for x in list(zip(*article_list))[3]]
    classified_score_list = [classify_score(x) for x in list(zip(*article_list))[1]]

    # create the normalized dict, such that every date has only one score associated 
    normalized_dict = normalize_date_scores(list(zip(date_list, classified_score_list)), min(date_list))

    # determine the error between the sentiment and the actual percent changes
    error_dict = error_stock_prediction(symbol, normalized_dict)
    error = average_error(error_dict)
    print("Error is" + str(error))

    # TODO: create a bar plot of the dates to the sentiment score on that date
    axis = plt.subplot(111)
    #axis.bar(normalized_dict.keys(), normalized_dict.values())
    axis.bar(error_dict.keys(), error_dict.values())
    plt.title(symbol)

    plt.show()

def error_stock_prediction(symbol: str, script_results: dict) -> dict:
    """
    RETURN the mean squared error between a stock's percent daily change and
            a script's results over the same time period

    INPUT script_results as {date: 1 OR -1 OR 0, ... } for sequential dates
    """
    # get percent changes of the symbol in the given period
    from_date = min(script_results.keys())
    change_percentages = IEX.get_percent_change_from_date(symbol, from_date)

    # build dict of classified percent changes for each date
    changes_classified = {}
    for date, percent in change_percentages.items():
        changes_classified[date] = classify_score(percent, 1)

    # find the error between sentiment and classified changes for each day (that there exists a known percent change)
    error_dict = {}

    for date, change in changes_classified.items():
        try:
            day_sentiment = script_results[date]
        except KeyError:
            day_sentiment = 0

        day_difference = change - day_sentiment
        error_dict[date] = day_difference

    return error_dict

def average_error(error_dict: dict) -> float:
    """
    RETURN float value of mean squared error present in the error dictionary
    """
    return sum(error_dict.values()) / len(error_dict)

    

def run_news_scan(queries):
    """
    Run the scan on list of queries
    RETURN categorized scores dictionary. {Symbol : score}
    """
    # -------- run IEX scan --------- #

    iex_final = run_iex_scan(queries)
   
    # combine results dictionaries
    #final.update(iex_final)


    #----- run NewsAPI scan -------#
    #scores_dict = news_api_get_scores(queries)
    #agg = average_net_scores_over_time(scores_dict)
    #final = classify_polarity_dictionary(agg)

    return iex_final




###---------------------- NewsAPI Methods ----------------------###

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

RESULT = run_news_scan(["AA", "TIVO"])
# print(RESULT)
