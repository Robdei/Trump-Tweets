from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
import pandas as pd
from datetime import datetime as dt
import numpy as np
import re

path_to_chromedriver='/Users/robbygottesman/Desktop/Twets/chromedriver'

dates = set(pd.date_range('2017-01-20',dt.today()).astype(str))
politics_tweets = pd.read_csv('congressional_tweets.csv')
politics_tweets_dates = set(politics_tweets.Date)

dates = sorted(list(dates-politics_tweets_dates))
retval_array = np.array([0,0,0,0])

for date in dates[1:]:
    time_to_wait = 0 
    while True:
        time_to_wait += 1 
        try:
            browser = webdriver.Chrome(path_to_chromedriver)
            browser.get(f"http://www.tweetcongress.org/tweets?end={date}&start={date}")
            time.sleep(1)

            web_page = str(browser.page_source)
            browser.close()

            retval = [date]
            repub_index = re.search('Republicans</h1><p class="group-counts"><span>',web_page).end()
            dem_index  = re.search('Democrats</h1><p class="group-counts"><span>',web_page).end()
            tot_index  = re.search('Tweets for the period</h1><span class="tweet-total"><span>',web_page).end()
        except AttributeError:
            continue
        except:
        	politics_tweets_concat = pd.DataFrame(retval_array[1:,:],columns=['Date','Republicans','Democrats','Total'])
			politics_tweets = pd.concat([politics_tweets,politics_tweets_concat])
			politics_tweets.to_csv('congressional_tweets.csv',index=False)
        break
   
    for party in [repub_index,dem_index,tot_index]:
        temp_web_page = web_page[party:]
        temp_web_page = temp_web_page[:temp_web_page.find('</span>')]
        retval.append(temp_web_page.replace(',',''))
    retval_array = np.vstack((retval_array,retval))

