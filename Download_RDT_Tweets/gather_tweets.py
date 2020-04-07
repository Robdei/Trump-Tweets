import re
from subprocess import Popen
from datetime import datetime
from datetime import timedelta
import pandas as pd
import json
import pytz
import os
from dateutil import parser
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
import tweepy
import numpy as np
from tqdm import tqdm
import warnings
from collections import Counter


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
    ID2 = []

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
            ID.append(str(tweet['id_str'])[:11])
            ID2.append(str(tweet['id_str'])[11:])
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
    tweets_df['id_str_2'] = ID2

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

def link(text):
    if 'https' in text:
        return True
    else:
        return False

def tweepy_get_attachments(tweets_df, consumer_key, consumer_secret, access_key, access_secret, only_new=True):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    error_codes = np.array([0,0,0])
    data = tweets_df
    data['contains_link'] = data['Text'].apply(link)
    data = data[(data.contains_link == True) & (data.is_retweet == False) & (data.deleted == 1)]
    ids = [int(str(x) + str(y)) for x, y in zip(data['id_str'], data['id_str_2'])]

    url_df = pd.read_csv('Attachments.csv')
    url_ids = [int(str(int(x)) + str(int(y))) for x, y in zip(url_df['id_str'], url_df['id_str_2'])]
    # obtain only id strings not in the attachment dataframe
    ids_to_download = list(set(ids) - set(url_ids))

    url_df = pd.DataFrame()

    id_str = []
    id_str_2 = []
    media_type = []
    urls = []
    text = []
    date = []
    is_quote = []
    quote = []
    time_of_quote = []

    if not only_new:
        ids_to_download = ids

    print(f'{len(ids_to_download)} new tweets to download')

    for id in ids_to_download:
        print(id)
        try:
            tweet = api.get_status(id)
            id_str.append(str(id)[:11])
            id_str_2.append(str(id)[11:])
            try:
                urls.append(tweet.entities['media'][0]['expanded_url'])
            except KeyError:
                urls.append(np.nan)
            try:
                media_type.append(tweet.entities['media'][0]['type'])
            except KeyError:
                media_type.append(np.nan)

            text.append(tweet.text)
            date.append(tweet.created_at)
            is_quote.append(tweet.is_quote_status)
            if tweet.is_quote_status:
                try:
                    quote.append(tweet.quoted_status.text)
                    time_of_quote.append(tweet.quoted_status.created_at)
                except AttributeError:
                    quote.append('attribute_error')
                    time_of_quote.append(np.nan)
            else:
                quote.append(np.nan)
                time_of_quote.append(np.nan)
        except tweepy.TweepError as e:
            print(f'error code {e.api_code}')
            error_codes = np.vstack((error_codes,np.array([str(id)[:11],str(id)[11:],e.api_code])))
            if e.api_code == None:
                url_df = pd.DataFrame()
                url_df['date'] = date
                url_df['id_str'] = id_str
                url_df['id_str_2'] = id_str_2
                url_df['text'] = text
                url_df['media_type'] = media_type
                url_df['url'] = urls
                url_df['is_quote'] = is_quote
                url_df['quote'] = quote
                url_df['quote_date'] = time_of_quote
                if only_new:
                    url_df = pd.concat([url_df, pd.read_csv('Attachments.csv')])
                    url_df.to_csv('Attachments.csv', index=False)
                else:
                    url_df.to_csv('Attachments.csv', index=False)
                print(f'RateLimitError. Pause for 1000 seconds. Restart at {dt.now() + timedelta(seconds=1000)}')
                time.sleep(1000)

    url_df = pd.DataFrame()
    url_df['date'] = date
    url_df['id_str'] = id_str
    url_df['id_str_2'] = id_str_2
    url_df['text'] = text
    url_df['media_type'] = media_type
    url_df['url'] = urls
    url_df['is_quote'] = is_quote
    url_df['quote'] = quote
    url_df['quote_date'] = time_of_quote
    error_df = pd.DataFrame(error_codes,columns = ['id_str','id_str_2','error_code'])
    url_df = pd.concat([url_df, error_df])
    if only_new:
        url_df = pd.concat([url_df, pd.read_csv('Attachments.csv')])
        url_df.to_csv('Attachments.csv', index=False)
    else:
        url_df.to_csv('Attachments.csv', index=False)


def join_media_and_tweets(tweets_df, name_of_dataframe):
    media = pd.read_csv('Attachments.csv')

    # media atatchments are in UTC. convert to EST.
    old_timezone = pytz.timezone("UTC")
    new_timezone = pytz.timezone("US/Eastern")
    media['quote_date'] = [old_timezone.localize(parser.parse(x)).astimezone(new_timezone) if type(x) == str else np.nan
                           for x in media['quote_date']]
    media['date'] = [old_timezone.localize(parser.parse(x)).astimezone(new_timezone) if type(x) == str else np.nan
                           for x in media['date']]

    #join dataframes
    tweets_df.to_csv(name_of_dataframe+'.csv', index=False)
    tweets_df = pd.read_csv(name_of_dataframe+'.csv')
    tweets_df = tweets_df.merge(media, on=['id_str', 'id_str_2'], how='left')

    tweets_df.to_csv(f'{name_of_dataframe}.csv', index=False)
    return tweets_df

def gather_diff_merge_threads(tweets_df):
    " merges threads together and aggregates their statistics "
    #find time elapsed between tweets
    tweets_df.reset_index(inplace=True, drop=True)
    tweets_df.DateTime = tweets_df.DateTime.apply(parser.parse)
    tweets_df['Diff'] = [np.nan] + [(tweets_df['DateTime'][tweet] -
                                     tweets_df['DateTime'][tweet + 1]).seconds for tweet in range(len(tweets_df) - 1)]

    #non-retweet tweets with less than 10 seconds elapsed between them are considered part of the same thread
    datetimes = tweets_df['DateTime']
    tweets_df['Thread Length'] = 1
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        indices = tweets_df[tweets_df['is_retweet'] == False][tweets_df['Diff'] <= 10]
    cols = ['Text', 'Subjectivity', 'neg', 'neu', 'pos', 'Sentiment', 'CC', 'CD', 'DT', 'EX', 'FW', 'IN', 'JJ', 'JJR',
            'JJS', 'MD', 'NN', 'NNP', 'NNPS', 'NNS', 'PDT', 'POS', 'PRP', 'PRP$', 'RB', 'RBR', 'RBS', 'RP', 'UH', 'VB',
            'VBD', 'VBG', 'VBN', 'VBP', 'VBZ', 'WDT', 'WP', 'WP$', 'WRB', 'Len', 'Thread Length']

    #conduct merge
    rowstodrop = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for i in tqdm(indices.index):
            # data.iloc[i] = pd.Series((np.array(data.iloc[i])+np.array(data.iloc[i-1])),index=data.columns)
            # data.iloc[i][cols] =
            nums = pd.Series(np.array(tweets_df.iloc[i][cols]) + np.array(tweets_df.iloc[i - 1][cols]), index=cols)
            for c in cols:
                tweets_df[c][i] = nums[c]
            rowstodrop.append(i - 1)
        tweets_df.drop(rowstodrop, axis=0, inplace=True)
    tweets_df.reset_index(inplace=True, drop=True)
    tweets_df['Diff'] = [np.nan] + [(tweets_df['DateTime'][tweet] -
                                     tweets_df['DateTime'][tweet + 1]).seconds for tweet in range(len(tweets_df) - 1)]
    tweets_df['Text'] = tweets_df['Text'].replace('\.+', '.', regex=True)
    RTdict = list(np.zeros(len(tweets_df[tweets_df['is_retweet'] == True])))
    for n, i in enumerate(tweets_df[tweets_df['is_retweet'] == True]['Text']):
        RTdict[n] = i.split()[1]
    RTdict = dict((k, v) for k, v in Counter(RTdict).items() if v >= 50)
    for i in list(RTdict.keys()):
        tweets_df[i] = 0
    tweets_df['Contains Link'] = ['https' in i for i in tweets_df['Text']]
    tweets_df['Contains Quote'] = ['"' in i for i in tweets_df['Text']]
    for n, i in enumerate(tweets_df['Text']):
        try:
            rter = i.split()[1]
            if rter in list(RTdict.keys()):
                tweets_df[i.split()[1]][n] = 1
        except IndexError:
            continue
    tweets_df[['Subjectivity', 'neg', 'neu', 'pos', 'Sentiment']] = (np.array(tweets_df[['Subjectivity', 'neg', 'neu', 'pos', 'Sentiment']]) /
                                                                     np.array(tweets_df['Thread Length'])[:, None])

    return tweets_df