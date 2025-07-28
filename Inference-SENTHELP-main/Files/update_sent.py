import pymongo
import os
import pprint
import pickle

import re
import string
import nltk
from nltk.stem.snowball import FrenchStemmer
from nltk.corpus import stopwords #importation de la liste de stopwords
from nltk.tokenize import word_tokenize
from tensorflow import keras
import tensorflow as tf
from tensorflow.keras.models import load_model
from model import sentiment_analysis, initialize_model
# Connexion à la base de données MongoDB à l'aide du nom du service MongoDB défini dans Docker Compose
client = pymongo.MongoClient("mongodb+srv://audensielrd:lNH4fO4YPqDjGJvd@recolte.2nowcyu.mongodb.net/")
#mongodb+srv://audensielrd:lNH4fO4YPqDjGJvd@recolte.2nowcyu.mongodb.net/

# client = pymongo.MongoClient(os.getenv('MONGO_URL'))




db = client['Recolte']

model = initialize_model( r"./ELECTRA_Fed_CNN.h5")

def mongo_stream_method(): 
    tweet_collection = db['tweets']
    #mesurer le temps d'exécution et consommation mémo et cpu une après avoir prédit un groupe de tweets
    try:
        with tweet_collection.watch() as stream:
            for change in stream:
                tweet = change['fullDocument']
                cleaned, emotion = sentiment_analysis(tweet.get('text_tweet', ''), model)
                tweet_collection.update_one(
                    {"_id": tweet["_id"]},
                    {"$set": {
                        "cleaned_text_tweet": cleaned,
                        "emotion": emotion
                    }}
                )
                pprint.pprint(f"Tweet mis à jour : {tweet['_id']}")
    except Exception as e:
        print(f"Erreur dans le stream MongoDB : {e}")

def update_sentiment() : 
    tweet_collection = db['tweets']
    # Récupérer tous les tweets non analysés
    tweets = tweet_collection.find({"emotion": ""})
    for tweet in tweets:
        cleaned, emotion = sentiment_analysis(tweet.get('text_tweet', ''), model)
        tweet_collection.update_one(
            {"_id": tweet["_id"]},
            {"$set": {
                "cleaned_text_tweet": cleaned,
                "emotion": emotion
            }}
        )
        pprint.pprint(f"Tweet mis à jour : {tweet['_id']}")

def affiche_tweets(mois, jour, an):
    tweet_collection = db['tweets']

    tweets = tweet_collection.find({"month": mois, "day": jour, "year": an})
    for tweet in tweets:
        pprint.pprint(tweet.get('text_tweet', '') + " | Emotion: " + tweet.get('emotion', 'Non analysé'))

if __name__ == "__main__":
    #update_sentiment()
    affiche_tweets(6, 29, 2025)

