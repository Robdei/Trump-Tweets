from robobrowser import RoboBrowser
import json
import os
browser = RoboBrowser(history=True)
from selenium import webdriver
import re
import pandas as pd
import pytz
from datetime import datetime
from selenium.webdriver.common.keys import Keys

path_to_chromedriver = '/Users/robbygottesman/Desktop/Twets/chromedriver'

def download_reddit_info(url, csv_name):

    browser = webdriver.Chrome(path_to_chromedriver)
    browser.get(url)
    web_page = str(browser.page_source)
    web_page = web_page[web_page.find('<p>') + 3:web_page.find('</p>')]
    browser.close()
    file = open("RedditCount.txt", "w")
    file.write(web_page)
    file.close()
    file = open("RedditCount.txt", "r")
    file_str = file.readlines()
    file.close()
    New_file = "".join([x.rstrip() for x in file_str[1:-1]])
    New_file = '{' + re.sub('\s+', ' ', New_file) + '}'

    file = open("RedditJson.txt", "w")
    file.write(New_file)
    file.close()

    with open('RedditJson.txt') as json_file:
        dates = []
        comments = []
        apps = json.load(json_file)['aggs']['created_utc']
        # print(apps)
        app = pd.DataFrame()
        for p in apps:
            dates.append(p['key'])
            comments.append(p['doc_count'])

    app['Date (UTC)'] = dates
    app['Comment Count'] = comments
    app['Date (EST)'] = [datetime.utcfromtimestamp(app['Date (UTC)'][x]) for x in range(len(app))]
    old_timezone = pytz.timezone("UTC")
    new_timezone = pytz.timezone("US/Eastern")
    app['Date (EST)'] = [old_timezone.localize(x).astimezone(new_timezone) for x in app['Date (EST)']]
    app.drop(app.index[0], inplace=True)
    os.remove("RedditCount.txt")
    os.remove("RedditJson.txt")
    try: os.chdir('reddit_csvs')
    except: print(' ')
    app.to_csv(f'{csv_name}.csv', index=False)

url = 'https://api.pushshift.io/reddit/search/comment/?q=trump&after=1300d&aggs=created_utc&frequency=hour&subreddit=politics&size=0'
download_reddit_info(url, csv_name='reddit_trump_politics_comments')

url = 'https://api.pushshift.io/reddit/search/submission/?q=trump&after=1300d&aggs=created_utc&frequency=hour&subreddit=politics&size=0'
download_reddit_info(url, csv_name='reddit_trump_politics_submissions')

url = 'https://api.pushshift.io/reddit/search/comment/?q=trump&after=1300d&aggs=created_utc&frequency=hour&subreddit=conservative&size=0'
download_reddit_info(url, csv_name='reddit_trump_conservative_comments')

url = 'https://api.pushshift.io/reddit/search/submission/?q=trump&after=1300d&aggs=created_utc&frequency=hour&subreddit=conservative&size=0'
download_reddit_info(url, csv_name='reddit_trump_conservative_submissions')