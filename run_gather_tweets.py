import gather_tweets
import nlp_functions

# grab tweets between the following years (inclusive)
start_year = 2015
end_year = 2017

# download tweet information
tweets_df = gather_tweets.gather_from_archive(start_year,end_year)

# convert to local time (EST)
tweets_df = gather_tweets.convert_to_est(tweets_df)

# determine sentiment and subjectivity
tweets_df = nlp_functions.get_sentiment_and_subjectivity(tweets_df)

# download trump vs staff classification labels
gather_tweets.gather_trump_v_staff_classification()

#tweets_df.to_csv('Test.csv',index=False)
