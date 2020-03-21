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
