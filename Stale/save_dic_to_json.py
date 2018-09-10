import json

ticker_keyword_dict = { "AAPL" : {"name" : "Apple Inc.",
    "search" : "apple OR iphone OR iPad OR ios OR Macbook OR iMac OR apple watch OR airpods", \
                                    "search_list" : ["apple", "iPhone", "iPad", "iPod", "Mac", "macOS", "Apple watch", "iTunes"],
                                    "accept" : ["airpods"],
                                    "reject" : ["pie", "big mac", "juice", "miller", "makeup", "fleetwood", "macaroni", "cheese", "cider"]},
                "SNAP": {"name" : "Snapchat",
                    "search" : "Snap OR Snapchat", \
                                    "search_list": ["Snap", "Snapchat", "snap chat"],
                                   "accept" : ["snapchat", "snap chat", "snap story", "on snap", "our snap", "snap me", "snapped me"],
                                   "reject" : ["oh snap", "snap out", "snap on", "low-income", "SNAP benefits", "SNAP program"]},
                "AMZN": {"name" : "Amazon",
                    "search" : "Amazon OR Amazon Basics OR Audible OR Zappos",  \
                                    "search_list" : ["Amazon", "Amazon Basics", "Audible", "Zappos"],
                                    "accept" : [ "amazon" ],
                                    "reject" : ["rain forest", "river"]},
                "SBUX" : {"name" : "Starbucks",
                    "search": "Starbucks OR Starbs",
                                         "search_list" : ["Starbucks", "starbs"],
                                         "accept" : ["coffee"],
                                          "reject" : [""]
                }
               }


with open("ticker_keywords.json", "w") as f:
    json.dump(ticker_keyword_dict, f, sort_keys=True, indent=4)




               