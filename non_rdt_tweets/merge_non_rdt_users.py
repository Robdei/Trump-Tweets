import pandas as pd
import os, glob
from datetime import datetime as dt
from dateutil import parser

os.chdir('Tweets_logs')

start_date = max([parser.parse(pd.read_csv(csv).Date.iloc[0]) for csv in glob.glob('*.csv')])
end_date = dt.today()
dates = pd.date_range(start_date, end_date)

# total number of tweets non-rdt users
merged_df = pd.DataFrame(index=dates[:-1])

for user in glob.glob('*.csv'):
    tweets = pd.read_csv(user)
    tweets.DateTime = tweets.DateTime.apply(parser.parse)
    tweets.set_index('DateTime', inplace=True)

    merged_df[user.split('_')[0]] = [len(tweets.loc[dates[x]:dates[x + 1]]) for x in range(len(dates) - 1)]


# function to see if @RDT if mentioned in a tweet
def mention(text):
    if '@realDonaldTrump' in text:
        return 1
    else:
        return 0


# total number of tweets mentioning @RDT
merged_df_mentions = pd.DataFrame(index=dates[:-1])

for user in glob.glob('*.csv'):
    tweets = pd.read_csv(user)
    tweets['mention'] = tweets.Text.apply(mention)

    tweets = tweets[tweets.mention == 1]

    tweets.DateTime = tweets.DateTime.apply(parser.parse)
    tweets.set_index('DateTime', inplace=True)

    merged_df_mentions[user.split('_')[0]] = [len(tweets.loc[dates[x]:dates[x + 1]]) for x in range(len(dates) - 1)]

os.chdir('..')

merged_df.to_csv('rdt_aligned_users.csv')
merged_df_mentions.to_csv('rdt_aligned_users_mentions.csv')