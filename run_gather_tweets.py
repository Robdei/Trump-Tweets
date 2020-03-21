import gather_tweets
import nlp_functions

tweets_df = gather_tweets.gather_from_archive(2015,2020)
gather_tweets.convert_to_est(tweets_df).to_csv('Tweets_local.csv',index=False)

