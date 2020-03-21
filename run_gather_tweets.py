import gather_tweets
import nlp_functions

start_year = 2015
end_year = 2017

# download tweet information
tweets_df = gather_tweets.gather_from_archive(start_year,end_year)

# convert to local time (EST)
tweets_df = gather_tweets.convert_to_est(tweets_df)

# determine sentiment and subjectivity
tweets_df = nlp_functions.get_sentiment_and_subjectivity(tweets_df)
tweets_df.to_csv('Test.csv',index=False)

