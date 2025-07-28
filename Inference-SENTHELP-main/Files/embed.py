# === Import des bibliothèques nécessaires ===
import os
import re
import string
import numpy as np
import nltk
import tensorflow as tf
from transformers import ElectraTokenizer, ElectraModel
import pandas as pd
import torch

# === Détection automatique de l'appareil (GPU si disponible, sinon CPU) ===
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# === Chargement du tokenizer et du modèle Electra en français ===
# Le tokenizer est utilisé pour convertir le texte en tokens adaptés au modèle
tokenizer_emb = ElectraTokenizer.from_pretrained(
    'dbmdz/electra-base-french-europeana-cased-generator'
)
# Le modèle pré-entraîné Electra génère des représentations vectorielles (embeddings)
model_emb = ElectraModel.from_pretrained(
    'dbmdz/electra-base-french-europeana-cased-generator'
)
model_emb = model_emb.to(device)  # Envoie le modèle sur le GPU si disponible

# === Fonction pour générer les embeddings d'un texte donné ===
def embedding(text, model=model_emb, tokenizer=tokenizer_emb, device=device):
    """
    Cette fonction génère et sauvegarde les embeddings d'une phrase (text) en utilisant le modèle Electra.

    Args:
        text (str): Le texte à encoder.
        model: Le modèle Electra chargé.
        tokenizer: Le tokenizer Electra correspondant.
        device: Le périphérique d'exécution (CPU ou GPU).

    Returns:
        np.ndarray: Les embeddings sous forme de tableau numpy.
    """
    
    # Tokenisation du texte avec ajout de tokens spéciaux, padding et troncature
    tokens = tokenizer.encode_plus(
        text,
        add_special_tokens=True,
        truncation=True,
        max_length=200,
        padding='max_length',
        return_tensors='pt'  # Retourne un tenseur PyTorch
    )

    # Déplacement des tenseurs vers le GPU (ou CPU selon disponibilité)
    input_ids = tokens['input_ids'].to(device)
    attention_mask = tokens['attention_mask'].to(device)

    # Passage du texte dans le modèle sans calcul de gradient (plus rapide, pas d'entraînement)
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)

    # Récupération de la dernière couche cachée (représentation contextuelle des tokens)
    embeddings = outputs.last_hidden_state  # Shape: (1, max_len, hidden_dim)
    embeddings = embeddings.squeeze(0)  # Supprime la dimension batch -> (max_len, hidden_dim)

    # Passage des embeddings du GPU vers le CPU, puis conversion en array numpy
    embeddings = embeddings.cpu().numpy()

    # Sauvegarde des embeddings localement dans un fichier .npy
    np.save("electra_embeddings.npy", embeddings)
    print("Embeddings sauvegardés avec succès dans 'electra_embeddings.npy'")

    return embeddings
