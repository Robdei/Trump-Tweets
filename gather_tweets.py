import re
from subprocess import Popen
from datetime import datetime
import pandas as pd
import json
import pytz
import os
from dateutil import parser

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
    print(f'Downloading {year} tweets...')
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

    #append tweet information onto base dataframe
    for year in list(range(start_year, end_year + 1)):
        # The JSON somtimes doesn't download, so retry if it doesn't
        while True:
            try:
                tweets_df = pd.concat([tweets_df,
                                       gather_year_from_archive(year)]
                                      )
            except json.decoder.JSONDecodeError:
                print('Retrying JSON download')
                continue
            break


    tweets_df.reset_index(inplace=True,drop=True)

    return tweets_df


def convert_to_est(tweets_df):
    old_timezone = pytz.timezone("UTC")
    new_timezone = pytz.timezone("US/Eastern")
    tweets_df['DateTime'] = tweets_df['Date'].apply(parser.parse)

    tweets_df['DateTime'] = [x.strftime("%Y-%m-%d %H:%M:%S") for x in tweets_df['DateTime']]
    tweets_df['DateTime'] = tweets_df['DateTime'].apply(parser.parse)

    tweets_df['DateTime'] = [old_timezone.localize(x).astimezone(new_timezone) for x in tweets_df['DateTime']]
    tweets_df['DateTime'] = [str(x) for x in tweets_df['DateTime']]

    tweets_df['Time'] = [tweets_df['DateTime'][x][11:-6] for x in range(len(tweets_df['DateTime']))]
    tweets_df['Date'] = [tweets_df['DateTime'][x][:10] for x in range(len(tweets_df['DateTime']))]

    tweets_df['Date'] = [datetime.strptime(tweets_df['Date'][x], '%Y-%m-%d') for x in range(len(tweets_df['DateTime']))]
    tweets_df.sort_values(by=['DateTime'], inplace = True)
    return tweets_df


