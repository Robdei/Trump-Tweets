from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import re

def clean_tweet(text):
    '''
    Utility function to clean the text in a tweet by removing
    links and special characters using regex.
    '''
    return ' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text).split())

def analize_sentiment(text):
    '''
    Utility function to classify the polarity of a tweet
    using vader sentiment analyzer.
    '''
    analyser = SentimentIntensityAnalyzer()
    score = analyser.polarity_scores(clean_tweet(text))
    return score

def analize_subjectivity(text):
    '''
    Utility function to classify the polarity of a tweet
    using textblob.
    '''
    analysis = TextBlob(clean_tweet(text))
    return(analysis.sentiment.subjectivity)

#_______________________________________________________________#
# Apply nlp functions to data

def get_sentiment_and_subjectivity(tweets_df):
    assert 'Text' in tweet_df.columns, "this is not a tweet dataframe"

    # remove hyperlink and non-text info from tweet
    clean = [clean_tweet(x) for x in tweets_df['Text']]

    # determine sentiment and subjectivity with vadersentiment and textblob, respectively
    subjectivity = [analize_subjectivity(x) for x in clean]
    polarity = [analize_sentiment(x) for x in clean]
    neg = [x['neg'] for x in polarity]
    pos = [x['pos'] for x in polarity]
    neu = [x['neu'] for x in polarity]
    compound = [x['compound'] for x in polarity]

    # append information onto tweet dataframe
    tweets_df['Subjectivity'] = subjectivity
    tweets_df['neg'] = neg
    tweets_df['neu'] = neu
    tweets_df['pos'] = pos
    tweets_df['Sentiment'] = compound

    return (tweet_df)

