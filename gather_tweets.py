import re
from subprocess import Popen
from datetime import datetime
import pandas as pd
import json
import os

def gather_year_from_archive(year):
    max_year = datetime.now().year
    year = int(year)
    assert year in list(range(2010,max_year+1)),f'year variable must be an integer between 2010 and {max_year}, inclusive'

    #initialize cell information for dataframe
    source = []
    date = []
    text = []
    retweets = []
    favorites = []
    isretweet = []
    ID = []

    #Download json of tweet info
    p = Popen(f'curl http://www.trumptwitterarchive.com/data/realdonaldtrump/{year}.json > Tweets.txt', shell=True)
    p.wait()

    with open('Tweets.txt') as json_file:
        archive_json = json.load(json_file)
        for tweet in archive_json:
            source.append(tweet['source'])
            date.append(tweet['created_at'])
            text.append(tweet['text'])
            retweets.append(tweet['retweet_count'])
            favorites.append(tweet['favorite_count'])
            isretweet.append(tweet['is_retweet'])
            ID.append(tweet['id_str'])
    os.remove('Tweets.txt')

    #create df of tweet information
    tweets_df = pd.DataFrame()
    tweets_df['Source'] = source
    tweets_df['Text'] = text
    tweets_df['Date'] = date
    tweets_df['retweet_count'] = retweets
    tweets_df['favorite_count'] = favorites
    tweets_df['is_retweet'] = isretweet
    tweets_df['id_str'] = ID

    return tweets_df

def gather_from_archive(start_year, end_year):

    #years should be between 2010 and the current year
    assert start_year > 2009
    assert end_year <= datetime.now().year

    #blank df to append tweet information to
    tweets_df = pd.DataFrame()

    #append tweet information
    for year in list(pd.date_range(start_year,end_year)):
        tweets_df = pd.concat([tweets_df,gather_year_from_archive(year)])

    return tweets_df

print(gather_from_archive(2015,2020))