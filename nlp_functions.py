from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import pandas as pd
from collections import Counter

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
# Apply sentiment functions to data

def get_sentiment_and_subjectivity(tweets_df):
    assert 'Text' in tweets_df.columns, "this is not a tweet dataframe"

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

    return (tweets_df)

#_______________________________________________________________#
# Apply sentiment functions to data

def word_extraction(sentence):
    ignore = set(stopwords.words('english'))
    words = re.sub("[^\w]", " ",  sentence).split()
    cleaned_text = [w.lower() for w in words if w not in ignore]
    return cleaned_text

lemmatizer = WordNetLemmatizer()

def Lemmatize(wordlist):
    return [lemmatizer.lemmatize(word) for word in wordlist]

def preprocess(text):
    text = clean_tweet(text)
    tknzr = nltk.TweetTokenizer()
    text = tknzr.tokenize(text)
    ignore_words = set(stopwords.words('english'))
    # lowercase, remove words less than len 2 & remove numbers in tokenized list
    return [word.lower() for word in text if len(word) > 2 and not word.isdigit() and not word in ignore_words]

def get_NER_parameters(tweets_df):
    texts = tweets_df['Text'].apply(preprocess)

    texts = texts.apply(Lemmatize)
    texts = texts.reset_index(drop=True)

    NER = pd.DataFrame([Counter([x[1] for x in nltk.pos_tag(texts[index])]) for index in range(len(texts))])
    NER = NER.fillna(0)
    NER['Len'] = [len(i) for i in texts]
    tweets_df[NER.columns] = NER

    return tweets_df