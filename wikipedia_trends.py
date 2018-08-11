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

class WikiTrends():

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


    def _to_datetime(self, wiki_date : str):
        """
        convert wikipedia date string to python datetime
        """
        dt = datetime.datetime.strptime(wiki_date, "%Y%m%d00")
        return dt

    def _to_wiki_date_string(self, datetime_obj):
        """
        go the other way with the dates
        """
        return datetime_obj.strftime("%Y%m%d")


    def get_wiki_views(self, article: str, start_date, end_date):
        """
        return dict of datetime : views for the period between start and end date (both inclusive)
        """

        _st = self._to_wiki_date_string(start_date)
        _nd = self._to_wiki_date_string(end_date)

        try:
            full_result = pageviewapi.per_article('en.wikipedia', article, _st, _nd,\
                            access='all-access', agent='all-agents', granularity='daily') 
        except pageviewapi.client.ZeroOrDataNotLoadedException as e:
            full_result = dict(items=[])

        result_subset = {}
        
        for item in full_result["items"]:
            py_dt = self._to_datetime(item["timestamp"] )
            result_subset[py_dt] = item["views"]

        return result_subset

    def run_wiki(self):
        """
        run the wikipedia scan, save for today
        """
        for ticker, terms in self.ticker_keyword_dict.items():
            article_list = terms["wiki"]

            total_views = 0

            for article in article_list:
                today = datetime.datetime.today()
                yesterday = today - datetime.timedelta(1)
                
                # td = self._to_wiki_date_string(today)
                # ys = self._to_wiki_date_string(yesterday)

                wiki_views_dict = self.get_wiki_views(article, yesterday.date(), today.date())

                for date, score in wiki_views_dict.items():
                    total_views += score
                
            # save to database 
            name = "WIKI: {}".format(ticker)
            table = self.AWS_RDS[name]

            save_info = dict(
                timestamp=date,
                views=total_views
            )
            print ("{}: ({}, {})".format(ticker, date, total_views))
            
            table.insert(save_info)


    


