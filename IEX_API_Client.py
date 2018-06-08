"""
Basic IEXTrading Python API wrapper

Louis Smidt
06/06/2018
"""

import requests
import datetime
import dateutil.relativedelta as relativedelta
import matplotlib.pyplot as plt


class IEX_API_Client:

    @staticmethod
    def get_news_data(symbol, length=50):
        """
        RETURN JSON of last 50 news articles from IEX API
        INPUT stock symbol as string; length of article list as integer 
        """
        # create Requests object
        url_string = "https://api.iextrading.com/1.0/stock/" + symbol + "/news/last/" + str(length)
        r = requests.get(url_string)

        data = r.json()
    
        return data

    def get_single_stock_data(self, symbol):
        """
        RETURN parsed JSON of stock data as Python dictionary
        """
        url_string = "https://api.iextrading.com/1.0/stock/" + symbol + "/quote"
        r = requests.get(url_string)

        data = r.json()
        return data
    
    def get_percent_change(self, symbol):
        """
        INPUT stock symbol query as string; start datetime object
        RETURN latest percent change of stock 
        """

        data = self.get_single_stock_data(symbol)

        return data["changePercent"] * 100

    def get_latest_price(self, symbol):
        """
        RETURN latest IEX price for symbol
        """
        data = self.get_single_stock_data(symbol)

        return data["latestPrice"]
        
        
    def get_percent_change_from_date(self, symbol, from_date):
        """
        RETURN percent change of symbol on specific date (ignoring time)
        """

        # TODO: Change the time_range properly for larger or smaller than 2 years
        # diff_date = today - relativedelta.relativedelta(date)
        # diff_yr = today - relativedelta.relativedelta(years=1)

        change_data = self.get_chart_data(symbol, time_range="1y")

        change_dict = {}

        for day_data_dict in change_data:
            date_string_stamp = day_data_dict["date"]
            datetime_stamp = datetime.datetime.strptime(date_string_stamp, "%Y-%m-%d")
            date_stamp = datetime_stamp.date()

            if date_stamp > from_date :
                change_dict[date_stamp] = day_data_dict["changePercent"]

        return change_dict

    @staticmethod
    def get_chart_data(symbol, time_range="1y", filter_field=""):
        """
        RETURN JSON data parsed as a Python dictionary 
        INPUT filter_field string to filter result
        time_range string to select chart

        TODO: implement filter_field
        """	

        url_str = "https://api.iextrading.com/1.0/stock/" + symbol + "/chart/" + time_range 

        r = requests.get(url_str)
        data = r.json()

        return data

    def plot_stock_chart(self, symbol, time_range="1y"):
        """
        TODO: Generate a matplotlib of a stock symbol over the given range
        """

        pass
    




IEX = IEX_API_Client()

#print(IEX.get_stock_quote("AAPL"))
print(IEX.get_percent_change_from_date("AAPL", datetime.date(2018, 2, 11)))