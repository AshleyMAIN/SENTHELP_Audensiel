# === IMPORT DES LIBRAIRIES ===
import os
import re                     # Pour les expressions régulières (nettoyage de texte)
import string                 # Pour accéder à la ponctuation
import numpy as np
import nltk                   # Bibliothèque pour le traitement du langage naturel
import tensorflow as tf
from nltk.corpus import stopwords           # Pour récupérer les stopwords français
from nltk.stem.snowball import FrenchStemmer  # Pour le stemming en français
import pandas as pd
import torch
import emoji                  # Pour transformer les emojis en texte

# === TÉLÉCHARGEMENT DES RESSOURCES NLTK ===
nltk.download('stopwords')   # Stopwords français
nltk.download('punkt')       # Tokeniseur de base

# === INITIALISATION DES OUTILS LINGUISTIQUES ===
stop_words = set(stopwords.words('french'))        # Liste des mots courants à ignorer
french_stemmer = FrenchStemmer()                   # Stemmatisateur pour le français

# === DICTIONNAIRE D’ABRÉVIATIONS DE LANGAGE SMS / CHAT EN FRANÇAIS ===
chat_words_dict_francais = {
    "tkt": "t'inquiète",
    "svp": "s'il vous plaît",
    "stp": "s'il te plaît",
    "pk": "pourquoi",
    "qd": "quand",
    "pcq": "parce que",
    "pck": "parce que",
    "tt": "tout",
    "mdr": "mort de rire",
    "lol": "laughing out loud",  # peut être remplacé par "mdr" si on veut rester en français
    "ptdr": "pété de rire",
    "jsp": "je sais pas",
    "jpp": "j'en peux plus",
    "tjr": "toujours",
    "dsl": "désolé",
    "bjr": "bonjour",
    "bcp": "beaucoup",
    "d'acc": "d'accord",
    "dac": "d'accord",
    "slt": "salut",
    "a+": "à plus",
    "vs": "vous",
    "msn": "messenger",  
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

# === FONCTION DE CONVERSION DES MOTS DE TYPE "CHAT" EN FRANÇAIS STANDARD ===
def convert_chat_words(text):
    """
    Remplace les mots d'argot ou abrégés par leur équivalent en français standard.
    """
    words = text.split()
    converted_words = []
    for word in words:
        if word.lower() in chat_words_dict_francais:
            converted_words.append(chat_words_dict_francais[word.lower()])
        else:
            converted_words.append(word)
    converted_text = " ".join(converted_words)
    return converted_text

# === FONCTION DE NETTOYAGE DU TEXTE ===
def clean_text(text):
    """
    Nettoie un texte brut :
    - le met en minuscules
    - supprime les emojis, urls, mentions, ponctuation, chiffres, balises HTML
    - applique la conversion des mots d'argot
    """
    text = str(text).strip()
    text = str(text).lower()
    text = emoji.demojize(text, language='fr')                     # Convertit les emojis en texte
    text = re.sub(r'@\w+', '', text)                               # Supprime les mentions (@utilisateur)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)              # Supprime les URLs
    text = re.sub(r'<.*?>+', '', text)                             # Supprime les balises HTML
    text = re.sub('\[.*?\]', '', text)                             # Supprime les textes entre crochets
    text = re.sub("\\W", " ", text)                                # Supprime les caractères non alphanumériques
    text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)  # Supprime la ponctuation
    text = re.sub(r'\n', ' ', text)                                # Supprime les sauts de ligne
    text = re.sub(r'\w*\d\w*', '', text)                           # Supprime les mots contenant des chiffres
    text = convert_chat_words(text)                                # Remplace les abréviations
    return text
