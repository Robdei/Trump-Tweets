from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import re
import pandas as pd
from dateutil import parser

def gather_deleted_tweets(tweets_df,
                          no_of_pagedowns=10,
                          path_to_chromedriver='/Users/robbygottesman/Desktop/Twets/chromedriver'):

    browser = webdriver.Chrome(path_to_chromedriver)
    browser.get("https://factba.se/topic/deleted-tweets")
    time.sleep(1)
    elem = browser.find_element_by_tag_name("body")

    while no_of_pagedowns:
        for i in range(8):
            time.sleep(.25)
            elem.send_keys(Keys.PAGE_DOWN)
        time.sleep(3)
        no_of_pagedowns -= 1

    web_page = str(browser.page_source)
    browser.close()

    tweet = [m.end() for m in re.finditer('<a href="https://media-cdn.factba.se/realdonaldtrump-twitter/', web_page)]
    ids = [web_page[x:x + web_page[x:].find('.jpg')] for x in tweet]

    Deleted = pd.DataFrame()
    Deleted['id_str'] = [x[:11] for x in ids]
    Deleted['id_str_2'] = [x[11:] for x in ids]
    Deleted['deleted'] = 1
    Deleted.drop_duplicates(inplace=True)
    Deleted.to_csv('Deleted_Tweets.csv', index = False)

    tweets_df = tweets_df.merge(Deleted,
                                on=['id_str','id_str_2'],
                                how='left'
                                )
    tweets_df['deleted'] = tweets_df['deleted'].fillna(value = 0)
    return tweets_df

def remove_duplicates(tweets_df):
    tweets_df.drop_duplicates(subset = ['Text'],inplace=True)
    url_df = pd.read_csv('Attachments.csv')
    url_df.drop_duplicates(subset=['id_str','id_str_2'], inplace=True)
    url_df.to_csv('Attachments.csv', index=False)
    return tweets_df