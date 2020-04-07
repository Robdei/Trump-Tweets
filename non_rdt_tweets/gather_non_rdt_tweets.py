import tweepy
import pandas as pd
import time
import list_of_twitter_users
import tweepy_keys
import glob
import os
from tqdm import tqdm
import pytz
from dateutil import parser

#Tweepy credentials
consumer_key = tweepy_keys.consumer_key
consumer_secret = tweepy_keys.consumer_secret
access_key = tweepy_keys.access_key
access_secret = tweepy_keys.access_secret

def get_all_tweets(screen_name):
    #Twitter only allows access to a users most recent 3240 tweets with this method
    #retval = pd.DataFrame()
    #authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    #initialize a list to hold all the tweepy Tweets
    alltweets = []

    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = screen_name,count=200)

    #save most recent tweets
    alltweets.extend(new_tweets)

    #save the id of the oldest tweet less one
    oldest = alltweets[-1].id - 1
    count=0
    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        #print("getting tweets before %s" % (oldest))

        #all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name = screen_name,count=200,max_id=oldest)

        #save most recent tweets
        alltweets.extend(new_tweets)

        #update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1

        #print("...%s tweets downloaded so far" % (len(alltweets)))

    #transform the tweepy tweets into a 2D array that will populate the csv
    outtweets = [[str(tweet.id)[:11],str(tweet.id)[11:],tweet.created_at, tweet.text] for tweet in alltweets]
    print(screen_name+' downloaded')
    return pd.DataFrame(outtweets,columns=['id_str_1','id_str_2','DateTime','Text'])

#change directory to Tweet_logs
os.chdir('Tweets_logs')

old_timezone = pytz.timezone("UTC")
new_timezone = pytz.timezone("US/Eastern")

for user in list_of_twitter_users.users_list:
    if f'{user}_tweets.csv' not in glob.glob('*.csv'):
        tweets = get_all_tweets(user)
        # tweets.DateTime = tweets.DateTime.apply(parser.parse)
        tweets['DateTime'] = [old_timezone.localize(x).astimezone(new_timezone) for x in tweets['DateTime']]
        tweets['DateTime'] = [str(x)[:-6] for x in tweets['DateTime']]
        tweets.to_csv(f'{user}_tweets.csv',index=False)

    else:
        tweets_old = pd.read_csv(f'{user}_tweets.csv')
        tweets = get_all_tweets(user)
        # tweets.DateTime = tweets.DateTime.apply(parser.parse)
        tweets['DateTime'] = [old_timezone.localize(x).astimezone(new_timezone) for x in tweets['DateTime']]
        tweets['DateTime'] = [str(x)[:-6] for x in tweets['DateTime']]
        retdf = pd.concat([tweets_old, tweets],axis=0)
        retdf.drop_duplicates('Text').reset_index(drop=True).to_csv(f'{user}_tweets_temp.csv',index=False)
        pd.read_csv(f'{user}_tweets_temp.csv').sort_values('DateTime').to_csv(f'{user}_tweets.csv',index=False)
        os.remove(f'{user}_tweets_temp.csv')

for csv in tqdm(glob.glob('*.csv')):
    tweets = pd.read_csv(csv)
    tweets['Date'] = [date.split()[0] for date in tweets['DateTime']]
    tweets['Time'] = [date.split()[1] for date in tweets['DateTime']]
    tweets.to_csv(csv, index=False)