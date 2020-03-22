import re
from subprocess import Popen
from datetime import datetime
import pandas as pd
import json
import pytz
import os
from dateutil import parser
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys

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
    # define timezone (covert from UTC to EST)
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
    tweets_df['DateTime'] = [x[:-6] for x in tweets_df['DateTime']]
    tweets_df.sort_values(by=['DateTime'], inplace = True, ascending = False)
    return tweets_df

def f7(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def gather_trump_v_staff_classification(no_of_pagedowns=50, path_to_chromedriver='/Users/robbygottesman/Desktop/Twets/chromedriver'):
    '''
    gathers trump vs staff info from https://blog.trumptweettrack.com/tagged/tweet_analysis
    '''

    classifier = pd.read_csv('Trump Classifier.csv')
    browser = webdriver.Chrome(path_to_chromedriver)
    browser.get("https://blog.trumptweettrack.com/tagged/tweet_analysis")
    time.sleep(1)

    elem = browser.find_element_by_tag_name("body")

    while no_of_pagedowns:
        elem.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.15)
        no_of_pagedowns -= 1

    web_page = str(browser.page_source)
    browser.close()
    Probabilities = [m.start() for m in re.finditer('Our Analysis</h2><p>', web_page)]
    PostDate = [m.start() for m in re.finditer('<br>Posted at:', web_page)]
    Text = [m.start() for m in re.finditer('<blockquote><p><i>', web_page)]

    probs = [web_page[x + web_page[x:].find(' chance') - 3:x + web_page[x:].find(' chance')] for x in Probabilities][
            :len(f7([web_page[x + 18:x + 44] for x in PostDate]))]

    probs = [int(x[:2]) / 100 if x[0].isdigit() else int(x[1]) / 100 for x in probs]

    new_classifications = pd.DataFrame()
    new_classifications['DateTime'] = f7([web_page[x + 18:x + 44] for x in PostDate])
    try:
        new_classifications['Text'] = f7([web_page[x + 26:x + web_page[x:].find('</i></p><p><i>')] for x in Text])
    except ValueError:
        new_classifications['Text'] = (f7([web_page[x + 26:x + web_page[x:].find('</i></p><p><i>')] for x in Text])
                                       [:len(new_classifications)]
                                      )
    new_classifications['Probability that Trump Wrote it'] = probs
    newdata = pd.concat([new_classifications, classifier], axis=0).drop_duplicates('DateTime', keep='last')
    newdata.reset_index(inplace=True)
    newdata.drop('index', axis=1, inplace=True)
    newdata['DateTime'] = newdata['DateTime'].apply(parser.parse)
    newdata.to_csv('Trump Classifier.csv', index=False)
    return('Classifications Downloaded')

def join_classifer_and_tweets(tweets_df):
    classifier = pd.read_csv('Trump Classifier.csv')
    classifier['DateTime'] = classifier['DateTime'].apply(str)
    tweets_df['DateTime'] = tweets_df['DateTime'].apply(str)
    tweets_df = tweets_df.merge(classifier[['DateTime', 'Probability that Trump Wrote it']], on='DateTime', how='left')
    tweets_df['trump_wrote_this'] = [1 if x >= .5 else 0 for x in tweets_df['Probability that Trump Wrote it']]

    return tweets_df