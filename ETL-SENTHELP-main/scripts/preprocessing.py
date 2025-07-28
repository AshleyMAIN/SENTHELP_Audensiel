import numpy as np
import pandas as pd
#reading
from scripts.models import tweet_collection, req_collection
import json
import re
from bs4 import BeautifulSoup
import string
import emoji
from langdetect import detect
from nltk.tokenize import word_tokenize
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import spacy
from spacy.cli import download

download("fr_core_news_sm")  # Télécharge le modèle si besoin
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')  # ou 'omw-1.4' si nécessaire
nltk.download('omw-1.4')

stop_words = set(nltk.corpus.stopwords.words('french'))
#nltk.download('averaged_perceptron_tagger_eng')
# Chargement du modèle spaCy pour le traitement du langage naturel 
nlp = spacy.load("fr_core_news_sm")  # ou "en_core_web_sm" pour l'anglais

chat_words_dict_francais = {
    "c": "c'est",
    "tkt": "t'inquiète",
    "svp": "s'il vous plaît",
    "stp": "s'il te plaît",
    "pk": "pourquoi",
    "qd": "quand",
    "pcq": "parce que",
    "pck": "parce que",
    "tt": "tout",
    "mdr": "mort de rire",
    "lol": "laughing out loud",  # peut rester "mdr" si tu veux garder le français
    "ptdr": "pété de rire",
    "jsp": "je sais pas",
    "jpp": "j'en peux plus",
    "tjr": "toujours",
    "dsl": "désolé",
    "svp": "s'il vous plaît",
    "bjr": "bonjour",
    "bcp": "beaucoup",
    "d'acc": "d'accord",
    "dac": "d'accord",
    "slt": "salut",
    "a+": "à plus",
    "vs": "vous",
    "msn": "messenger",  # à adapter
    "ttf": "tout à fait",
    "g": "j'ai",
    "t": "tu es",
    "jsuis": "je suis",
    "jvais": "je vais",
    "ya": "il y a",
    "y'a": "il y a",
    "yavait": "il y avait",
    "faudra": "il faudra",
    "faut": "il faut",
    "koi": "quoi",
    "komment": "comment",
    "ki": "qui",
}

def convert_chat_words(text):
    words = text.split()
    converted_words = []
    for word in words:
        if word.lower() in chat_words_dict_francais:
            converted_words.append(chat_words_dict_francais[word.lower()])
        else:
            converted_words.append(word)
    converted_text = " ".join(converted_words)
    return converted_text

def traitement(tweet):
    text = tweet

    # Minuscule
    text = text.lower()

    # Supprimer les URLs
    text = re.sub(r'http\S+|www.\S+', '', text)

    # Supprimer les mentions
    # Nouveau (supprime uniquement le caractère @)
    text = re.sub(r'@', '', text) #text = re.sub(r'@\w+', '', text)

    # Supprimer HTML
    text = BeautifulSoup(text, "lxml").text

    # Convertir emojis
    text = emoji.demojize(text, language='fr')

    # Convertir les abréviations
    text = convert_chat_words(text)

    # Supprimer ponctuation
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Supprimer les chiffres
    text = re.sub(r'\d+', '', text)

    # Supprimer les caractères spéciaux
    text = re.sub(r'[^\w\s]', '', text)

    # Supprimer les espaces en trop
    text = ' '.join(text.split())

    # (Optionnel) vérifier que le texte est bien en français
    try:
        if detect(text) != 'fr':
            return ''  # ou None
    except:
        return ''
    

    return text


def traitement_date(date):
    """
    Convertit une date au format ISO 8601 (chaîne) en objet datetime.

    Paramètre :
    ----------
    date : str
        Date sous forme de chaîne au format '%Y-%m-%dT%H:%M:%S.%fZ',
        typiquement extraite d'un tweet ou d'une API.

    Retour :
    -------
    datetime.datetime
        Objet datetime correspondant à la date fournie.
    """
    date = pd.to_datetime(date, format='%Y-%m-%dT%H:%M:%S.%fZ')
    return date

# POS tag mapping dictionary
wordnet_map = {"N": wordnet.NOUN, "V": wordnet.VERB, "J": wordnet.ADJ, "R": wordnet.ADV}

# Function to perform Lemmatization on a text
def lemmatize_text(text_toke):
    # Convertir la liste de mots en une phrase
    text_token = word_tokenize(text_toke)
    tokens = [word for word in text_token if word not in stop_words]
    text = ' '.join(tokens)
    # Appliquer spaCy
    doc = nlp(text)
    # Retourner la liste des lemmes
    return [token.lemma_ for token in doc if not token.is_punct and not token.is_space]


def preproces() : 
    tweets = tweet_collection.find().limit(20)
    #appliquer le traitement et rajouter les tweets traités dans la collectionen ajoutant les attributs
    
    for tweet in tweets:
        # Convertir le tweet en dictionnaire
        # Appliquer le traitement
        text = traitement(tweet['text_tweet'])
        text_toke = word_tokenize(text)
        # Supprimer les stop words
        text_toke = [word for word in text_toke if word not in stop_words]
        # Appliquer la lemmatisation
        text_toke = lemmatize_text(text_toke)
        date_datetime = traitement_date(tweet['date_tweet'])
        tweet_dict = {
            'text_tweet': tweet['text_tweet'],
            'date_tweet': tweet['date_tweet'],
            'text_cleaned': text,
            'text_token': text_toke,
            'date_tweet_cleaned': date_datetime,
            'year': date_datetime.year,
            'month': date_datetime.month,
            'day': date_datetime.day,
            'hour': date_datetime.hour,
            'minute': date_datetime.minute,
            'second': date_datetime.second,
        }

        # Mise à jour dans la base
        tweet_collection.update_one(
            {"identifiant": tweet["identifiant"]},
            {"$set": tweet_dict}
        )

    return tweet_dict