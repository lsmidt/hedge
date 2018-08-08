"""
Return Wikipedia trends score daily. 
"""


import pageviewapi
import datetime
import json
import attrdict
import dataset
import sqlalchemy
import pymysql
import dbapi

###------- GLOBAL VARS --------####

# Set up AWS Database for storage
HOST = "hedgedb.c288vca6ravj.us-east-2.rds.amazonaws.com"
PORT = 3306
DB_NAME = "scores_timeseries"
DB_USER = "hedgeADMIN"
DB_PW = "bluefootedboobie123"

AWS_RDS = dataset.connect("mysql+pymysql://{}:{}@{}/{}".format\
(DB_USER, DB_PW, HOST, DB_NAME))

###------READ IN SEARCH TERMS ---------####
with open("ticker_keywords.json") as tdk:
    try:
        ticker_keyword_dict = json.load(tdk)
    except json.decoder.JSONDecodeError as JSON_error:
        ticker_keyword_dict = {}
        print("Error reading ticker_keyword dicitonary.")


def _to_datetime(wiki_date : str):
    """
    convert wikipedia date string to python datetime
    """
    dt = datetime.datetime.strptime(wiki_date, "%Y%m%d00")
    return dt

def _to_wiki_date_string(datetime_obj):
    """
    go the other way with the dates
    """
    return datetime_obj.strftime("%Y%m%d")



def get_wiki_views(article: str, start_date: str, end_date: str):
    """
    return dict of datetime : views for the period between start and end date (both inclusive)
    """
    full_result = pageviewapi.per_article('en.wikipedia', article, start_date, end_date,\
                         access='all-access', agent='all-agents', granularity='daily') 

    result_subset = {}
    
    for item in full_result["items"]:
        py_dt = _to_datetime( item["timestamp"] )
        result_subset[py_dt] = item["views"]

    return result_subset


###------RUN PROGRAM ---------###

for ticker, terms in ticker_keyword_dict.items():
    article_list = terms["wiki"]

    for article in article_list:
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(1)
        
        td = _to_wiki_date_string(today)
        ys = _to_wiki_date_string(yesterday)

        wiki_views_dict = get_wiki_views(article, ys, ys)

        # save to database 
        name = "WIKI: {}".format(ticker)
        table = AWS_RDS[name]

        for date, views in wiki_views_dict.items():

            save_info = dict(
                timestamp=date,
                views=views
            )

            table.insert(save_info)


   

