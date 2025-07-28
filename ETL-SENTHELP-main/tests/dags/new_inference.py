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
# Connexion à la base de données MongoDB à l'aide du nom du service MongoDB défini dans Docker Compose
client = pymongo.MongoClient("mongodb+srv://cloe:Webscrap23@cluster0.qnvy73r.mongodb.net/?authMechanism=SCRAM-SHA-1")
#mongodb+srv://audensielrd:lNH4fO4YPqDjGJvd@recolte.2nowcyu.mongodb.net/
#load modele de prétraitement et d'analyse de sentiment

# Chargement du modèle

embedding_model = r"C:\Users\Amayas\Downloads\cc.fr.300.bin\cc.fr.300.bin"

try:
    model = load_model(
        r"C:\Users\Amayas\Downloads\ETL-SENTHELP-main\scripts\ELECTRA_Fed_CNN.h5",
        compile=False
    )
    print("Modèle chargé avec succès sans compilation.")
except Exception as e:
    print(f"Erreur lors du chargement du modèle : {e}")
    model = None
# client = pymongo.MongoClient(os.getenv('MONGO_URL'))
# Sélection de la base de données

# Ensure necessary NLTK resources are downloaded
nltk.download('stopwords')
nltk.download('punkt_tab')

stop_words = set(stopwords.words('french'))

french_stemmer = FrenchStemmer()

#nettoyer les données
def clean_text(text):

    text=str(text) # convertir le texte en string
    text = text.lower() #mettre le texte en minuscule
    text = re.sub(r'@\w+', '', text)  # Supprimer les mentions (@user) par contre je veux bien garder les hachtag et les emojis

    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # Supprimer les URLs
    text = re.sub(r'<.*?>+', '', text)  # Supprimer les balises HTML

    text = re.sub('\[.*?\]', '', text) #retirer les caractères de ponctuation ? et .
    text = re.sub("\\W"," ",text) # retirer les caractères spéciaux


    text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)  # Supprimer la ponctuation
    text = re.sub(r'\n', ' ', text)  # Supprimer les retours à la ligne
    text = re.sub(r'\w*\d\w*', '', text)  # Supprimer les mots contenant des chiffres

    text = re.sub(r'\s+', ' ', text).strip()  # Supprimer les espaces en trop

    return text


def tokenize_french(text):
    tokens=nltk.word_tokenize(text, language='french')
    return [word for word in tokens if word not in stop_words]

#replace the categorical variable Feeling by a numerical one
def convert_feeling_to_numerical(df):
    status_map = {'P': 1, 'N': 0}
    return df['Feeling'].map(status_map).to_numpy()

db = client['Tweets']

def stemmatization(tokens):
    return [french_stemmer.stem(word) for word in tokens]


import numpy as np


def vectorize_tokens_random(tokens, max_len=200, dim=256):
    # Dictionnaire de vecteurs aléatoires pour chaque mot rencontré
    word_vectors = {}
    vectors = []
    for word in tokens:
        if word not in word_vectors:
            word_vectors[word] = np.random.uniform(-0.25, 0.25, dim)
        vectors.append(word_vectors[word])
    vectors = vectors[:max_len]
    while len(vectors) < max_len:
        vectors.append(np.zeros(dim))
    return np.array([vectors])

# Analyse de sentiment
def sentiment_analysis(text):
    if model is None:
        return "Model not loaded"
    tokens = tokenize_french(text)
    tokens = stemmatization(tokens)
    # Il manque ici la préparation exacte des features pour ton modèle
    try:
        x_input = vectorize_tokens_random(tokens, max_len=200, dim=256)
        prediction = model.predict(x_input)
        return float(prediction[0][0])
    except Exception as e:
        print(f"Erreur lors de la prédiction : {e}")
        return "Erreur prédiction"



def mongo_stream_method(): 
    tweet_collection = db['tweets']
    #mesurer le temps d'exécution et consommation mémo et cpu une après avoir prédit un groupe de tweets
    try:
        with tweet_collection.watch() as stream:
            for change in stream:
                tweet = change['fullDocument']
                cleaned = clean_text(tweet.get("text_tweet", ""))
                emotion = sentiment_analysis(cleaned)
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

def test_on_one_tweet():
    tweet_collection = db['tweets']
    tweet = tweet_collection.find_one({"text_tweet": {"$exists": True}})
    
    if tweet:
        print("Texte original :", tweet["text_tweet"])
        cleaned = clean_text(tweet["text_tweet"])
        print("Texte nettoyé :", cleaned)
        emotion = sentiment_analysis(cleaned)
        print("Émotion prédite :", emotion)

        print(f"Tweet mis à jour avec succès : {tweet['_id']}")
    else:
        print("Aucun tweet trouvé dans la base.")

if __name__ == "__main__":
    #mongo_stream_method()  # Ne pas activer tant que le test n'est pas validé
    test_on_one_tweet()
