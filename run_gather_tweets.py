import gather_tweets
import nlp_functions
import pandas as pd

# grab tweets between the following years (inclusive)
start_year = 2016
end_year = 2020

#Tweepy credentials
consumer_key = "XXX"
consumer_secret = "XXX"
access_key = "XXX"
access_secret = "XXX"

# download tweet information
tweets_df = gather_tweets.gather_from_archive(start_year,end_year)

# convert to local time (EST)
tweets_df = gather_tweets.convert_to_est(tweets_df)

# determine sentiment and subjectivity
print('determining sentiment')
tweets_df = nlp_functions.get_sentiment_and_subjectivity(tweets_df)

# download trump vs staff classification labels
print('determining trump v staff classification')
gather_tweets.gather_trump_v_staff_classification(no_of_pagedowns=50,path_to_chromedriver='/Users/robbygottesman/Desktop/Twets/chromedriver')
tweets_df = gather_tweets.join_classifer_and_tweets(tweets_df)

print('applying NER')
tweets_df = nlp_functions.get_NER_parameters(tweets_df)
tweets_df.to_csv('Test.csv',index=False)

print('obtaining media attachments')
gather_tweets.tweepy_get_attachments(tweets_df, consumer_key, consumer_secret, access_key, access_secret)
tweets_df = pd.read_csv('Test.csv')
media = pd.read_csv('Attachments.csv')
tweets_df = tweets_df.merge(media, on = ['id_str','id_str_2'],how = 'left')

tweets_df.to_csv('Test2.csv',index=False)
