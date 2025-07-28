import pymongo  # Pour interagir avec MongoDB
import os
import pprint  # Pour afficher joliment les résultats dans la console
import pickle

import re
import string
import nltk
from nltk.stem.snowball import FrenchStemmer  # Pour la racinisation des mots en français
from nltk.corpus import stopwords               # Liste de mots vides (stopwords) à exclure
from nltk.tokenize import word_tokenize         # Pour découper le texte en mots
from tensorflow import keras
import tensorflow as tf
from tensorflow.keras.models import load_model
from model import sentiment_analysis, initialize_model  # Fonctions personnalisées pour analyse de sentiment

# Connexion à la base MongoDB via URI (MongoDB Atlas dans ce cas)
client = pymongo.MongoClient(
    "mongodb+srv://audensielrd:lNH4fO4YPqDjGJvd@recolte.2nowcyu.mongodb.net/"
)

# Sélection de la base de données 'Recolte'
db = client['Recolte']

# Chargement et initialisation du modèle de classification de sentiment (basé sur ELECTRA + CNN)
model = initialize_model(r"./ELECTRA_Fed_CNN.h5")

def mongo_stream_method():
    """
    Fonction qui écoute en temps réel les changements dans la collection 'tweets' de MongoDB.
    Lorsqu'un nouveau tweet est inséré ou modifié, si son champ 'emotion' est vide,
    on effectue l'analyse de sentiment et on met à jour le document dans la base.
    il necessite que mongodb soit lancé en mode replica set cela peut se faire en ajoutant --replSet "rs0" 
    dans la commande de lancement de mongodb 
      """
    tweet_collection = db['tweets']

    try:
        # Utilisation d'un change stream MongoDB pour écouter les modifications en temps réel
        with tweet_collection.watch() as stream:
            for change in stream:
                tweet = change['fullDocument']  # Récupère le document complet modifié ou inséré

                # Vérifie si le tweet n'a pas encore d'émotion attribuée
                if tweet.get('emotion') == "":
                    # Effectue l'analyse de sentiment sur le texte du tweet
                    cleaned, emotion = sentiment_analysis(tweet.get('text_tweet', ''), model)

                    # Met à jour le document avec le texte nettoyé et l'émotion détectée
                    tweet_collection.update_one(
                        {"_id": tweet["_id"]},  # Filtre par identifiant unique du document
                        {"$set": {
                            "cleaned_text_tweet": cleaned,
                            "emotion": emotion
                        }}
                    )

                    # Affiche dans la console l'ID du tweet mis à jour
                    pprint.pprint(f"Tweet mis à jour : {tweet['_id']}")

    except Exception as e:
        print(f"Erreur dans le stream MongoDB : {e}")

def addemotion():
    tweet_collection = db['tweets']
    for tweet in tweet_collection.find({"emotion": ""}):
        cleaned, emotion = sentiment_analysis(tweet.get('text_tweet', ''), model)
        tweet_collection.update_one(
            {"_id": tweet["_id"]},
            {"$set": {
                "cleaned_text_tweet": cleaned,
                "emotion": emotion
            }}
        )
        pprint.pprint(f"Tweet mis à jour : {tweet['_id']}")

if __name__ == "__main__":
    # Exécute la fonction d'écoute en continu des tweets à analyser
    mongo_stream_method()
    #addemotion()

   
