import gather_tweets
import nlp_functions
import remove_deletes_and_duplicates
import pandas as pd
from download_sched import download_sched
import tweepy_keys

# grab tweets between the following years (inclusive)
start_year = 2016
end_year = 2020

#Tweepy credentials
consumer_key = tweepy_keys.consumer_key
consumer_secret = tweepy_keys.consumer_secret
access_key = tweepy_keys.access_key
access_secret = tweepy_keys.access_secret

# download tweet information
tweets_df = gather_tweets.gather_from_archive(start_year,end_year)

# convert to local time (EST)
tweets_df = gather_tweets.convert_to_est(tweets_df)

# determine sentiment and subjectivity
print('determining sentiment')
tweets_df = nlp_functions.get_sentiment_and_subjectivity(tweets_df)

# download trump vs staff classification labels
print('determining trump v staff classification')
try:
    gather_tweets.gather_trump_v_staff_classification(no_of_pagedowns=50, path_to_chromedriver='/Users/robbygottesman/Desktop/Twets/chromedriver')
    tweets_df = gather_tweets.join_classifer_and_tweets(tweets_df)
except ValueError:
    print('Classifier error')

print('applying NER')
tweets_df = nlp_functions.get_NER_parameters(tweets_df)

print('removing deleted and duplicate tweets')
tweets_df = remove_deletes_and_duplicates.gather_deleted_tweets(tweets_df, no_of_pagedowns=15)

print('obtaining media attachments')
gather_tweets.tweepy_get_attachments(tweets_df, consumer_key, consumer_secret, access_key, access_secret)
tweets_df = remove_deletes_and_duplicates.remove_duplicates(tweets_df)

#join media types onto regular dataframe
tweets_df = gather_tweets.join_media_and_tweets(tweets_df, name_of_dataframe='Trump_tweets')

print('downloading schedule')
download_sched()

print('Merging Threads')
merged_tweets_df = gather_tweets.gather_diff_merge_threads(tweets_df)
merged_tweets_df.to_csv('Trump_tweets_merged.csv', index=False)

