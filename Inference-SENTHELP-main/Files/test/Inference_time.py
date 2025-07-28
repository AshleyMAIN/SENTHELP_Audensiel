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
import time
# Connexion à la base de données MongoDB à l'aide du nom du service MongoDB défini dans Docker Compose


def temps_inference(model, db, tweets):
    #prendre 5 tweets dans la collection tweets

    inference_total = 0
    insert_total = 0
    for tweet in tweets:
        start_time = time.time()
        cleaned, emotion = sentiment_analysis(tweet.get('text_tweet', ''), model)
        end_time = time.time()
        inference_time = end_time - start_time
        inference_total += inference_time
        #print(f"Tweet ID: {tweet['_id']}, Emotion: {emotion}, Temps d'inférence: {inference_time:.4f} secondes")
        
        # Mettre à jour le tweet dans la base de données
        temps_insertion = time.time()
        db.tweets.update_one(
            {"_id": tweet["_id"]},
            {"$set": {
                "cleaned_text_tweet": cleaned,
                "emotion": emotion
            }}
        )
        temps_fin_insertion = time.time()
        insert_time = temps_fin_insertion - temps_insertion
        insert_total += insert_time
    
    print(f"Temps total d'insertion pour 6 tweets: {insert_total:.4f} secondes")
    print(f"Temps total d'inférence pour 6 tweets: {inference_total:.4f} secondes")
    

if __name__ == "__main__":
    temps_debut = time.time()
    client = pymongo.MongoClient("mongodb+srv://audensielrd:lNH4fO4YPqDjGJvd@recolte.2nowcyu.mongodb.net/")
    #mongodb+srv://audensielrd:lNH4fO4YPqDjGJvd@recolte.2nowcyu.mongodb.net/
    # client = pymongo.MongoClient(os.getenv('MONGO_URL')
    db = client['Recolte']
    tweet_collection = db['tweets']
    end_connection_time = time.time()
    print(f"Temps de connexion à la base de données : {end_connection_time - temps_debut} secondes")

    temps_deb_recup = time.time()
    tweets = tweet_collection.find().limit(6)
    end_recup_time = time.time()
    print(f"Temps de récupération des tweets : {end_recup_time - temps_deb_recup} secondes")
    
    temps_initmodel = time.time()
    model = initialize_model( r"./ELECTRA_Fed_CNN.h5")
    end_initmodel_time = time.time()
    print(f"Temps d'initialisation du modèle : {end_initmodel_time - temps_initmodel} secondes")

    temps_debut_inference = time.time()
    temps_inference(model,db, tweets)
    temps_fin = time.time()
    print(f"Temps d'inférence pour 6 tweets : {temps_fin - temps_debut_inference} secondes")
    temps_total = temps_fin - temps_debut
    print(f"Temps total pour 6 tweets : {temps_total} secondes")