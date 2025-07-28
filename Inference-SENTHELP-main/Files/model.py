# Importation des bibliothèques nécessaires
import os
import re
import string
import numpy as np
import nltk
import tensorflow as tf
from nltk.corpus import stopwords
from nltk.stem.snowball import FrenchStemmer
from nltk.tokenize import word_tokenize
from tensorflow.keras.models import load_model
from transformers import AutoTokenizer
from transformers import TFAutoModel
from transformers import ElectraTokenizer, ElectraModel
import pandas as pd
import torch

# Importation des fonctions personnalisées de nettoyage de texte et d'embedding
from clean import clean_text
from embed import embedding

# Téléchargement des ressources nécessaires de NLTK (stopwords et tokenizer)
nltk.download('stopwords')
nltk.download('punkt')

# Initialisation de l'ensemble de stopwords français et du stemmer pour le français
stop_words = set(stopwords.words('french'))
french_stemmer = FrenchStemmer()

# Fonction pour construire le modèle CNN si aucun modèle pré-entraîné n’est chargé
def build_model(input_shape=(200, 256), dense_units=256, dropout_rate=0.1, output_units=1, activ='relu'):
    """
    Construit un modèle de réseau de neurones convolutionnel pour l'analyse de sentiment.
    - input_shape : dimensions de l’entrée (longueur de la séquence, taille des vecteurs d’embedding)
    - dense_units : nombre de neurones dans la couche dense
    - dropout_rate : taux de dropout pour régularisation
    - output_units : sortie binaire (1 neurone)
    - activ : fonction d’activation
    """
    initializer = tf.keras.initializers.GlorotUniform()  # Initialisation Xavier
    model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(32, 2, activation=activ, input_shape=input_shape, kernel_initializer=initializer),
        tf.keras.layers.Conv1D(64, 2, activation=activ, kernel_initializer=initializer),
        tf.keras.layers.MaxPooling1D(),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(dense_units, activation=activ, kernel_initializer=initializer),
        tf.keras.layers.Dropout(dropout_rate),
        tf.keras.layers.Dense(output_units, activation='sigmoid', kernel_initializer=initializer)  # Pour classification binaire
    ])
    return model

# Fonction pour charger un modèle : tente d’abord de charger un modèle complet, sinon les poids uniquement
def initialize_model(model_path):
    """
    Charge le modèle à partir du chemin donné. Si échec du chargement complet, reconstruit la structure et charge uniquement les poids.
    """
    try:
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully using load_model")
    except:
        model = build_model()
        model.load_weights(model_path)
        print("Model weights loaded successfully using load_weights")
    return model

# Fonction de prédiction du sentiment à partir des embeddings
def predict_sentiment(embeddings, model):
    """
    Prend des embeddings de texte et prédit un score de sentiment avec le modèle.
    Retourne 'Positive' ou 'Negative' selon le score.
    """
    embeddings_np = np.frombuffer(embeddings, dtype=np.float32).reshape(1, 200, 256)  # Mise en forme
    embeddings_tensor = torch.tensor(embeddings_np)  # Conversion en tenseur PyTorch (inutile ici mais présent)
    embeddings_np = embeddings_tensor.numpy()  # Reconversion en tableau NumPy
    prediction = model.predict(embeddings_np)
    print("Prédiction brute :", prediction[0][0])
    label = "Positive" if prediction[0][0] < 0.5 else "Negative"  # Seuil de 0.5
    return label

# Fonction complète de pipeline de prédiction de sentiment
def sentiment_analysis(text, model):
    """
    Pipeline complet pour analyser un texte :
    1. Nettoyage
    2. Embedding
    3. Prédiction
    Retourne le texte nettoyé et le label de sentiment.
    """
    clean  = clean_text(text)
    print("Texte nettoyé :", clean)
    embeddings = embedding(clean)
    label_sentiment = predict_sentiment(embeddings, model)
    print("Label de sentiment prédit :", label_sentiment)
    return clean, label_sentiment
