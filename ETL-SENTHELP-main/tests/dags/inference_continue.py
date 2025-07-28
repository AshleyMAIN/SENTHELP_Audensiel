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
from electra_classifier import ElectraClassifier
from transformers import TFAutoModel
from transformers import ElectraTokenizer, ElectraModel
import pandas as pd
import torch

# Téléchargement des ressources nécessaires
nltk.download('stopwords')
nltk.download('punkt')

# Initialisation
stop_words = set(stopwords.words('french'))
french_stemmer = FrenchStemmer()


# Nettoyage du texte
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>+', '', text)
    text = re.sub('\[.*?\]', '', text)
    text = re.sub("\\W", " ", text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), ' ', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\w*\d\w*', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Tokenisation
def tokenize_french(text):
    tokens = word_tokenize(text, language='french')
    return [word for word in tokens if word not in stop_words]

# Stemmatisation
def stemmatization(tokens):
    return [french_stemmer.stem(word) for word in tokens]

def build_model(input_shape=(200, 256), dense_units=256, dropout_rate=0.1, output_units=1, activ='relu'):
    initializer = tf.keras.initializers.GlorotUniform()
    model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(32, 2, activation=activ, input_shape=input_shape, kernel_initializer=initializer),
        tf.keras.layers.Conv1D(64, 2, activation=activ, kernel_initializer=initializer),
        tf.keras.layers.MaxPooling1D(),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(dense_units, activation=activ, kernel_initializer=initializer),
        tf.keras.layers.Dropout(dropout_rate),
        tf.keras.layers.Dense(output_units, activation='sigmoid', kernel_initializer=initializer)
    ])
    return model

def initialize_model(model_path):
    try:
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully using load_model")
    except:
        model = build_model()
        model.load_weights(model_path)
        print("Model weights loaded successfully using load_weights")
    return model



device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
#instantiate le tokenizer et le model
tokenizer_emb = ElectraTokenizer.from_pretrained('dbmdz/electra-base-french-europeana-cased-generator')
model_emb = ElectraModel.from_pretrained('dbmdz/electra-base-french-europeana-cased-generator')
model_emb = model_emb.to(device)

def embedding(text, model=model_emb, tokenizer=tokenizer_emb, device=device):
    tokens = tokenizer.encode_plus(text, add_special_tokens=True, truncation=True,
                                   max_length=200, padding='max_length',
                                   return_tensors='pt')
    input_ids = tokens['input_ids'].to(device)
    attention_mask = tokens['attention_mask'].to(device)

    with torch.no_grad():
        outputs = model(input_ids, attention_mask=attention_mask)
    embeddings = outputs.last_hidden_state
    embeddings = embeddings.squeeze(0)
    embeddings = embeddings.cpu().numpy()
    return embeddings

def predict_sentiment(embeddings,model):
    embeddings_np = np.frombuffer(embeddings, dtype=np.float32).reshape(1, 200, 256)
    embeddings_tensor = torch.tensor(embeddings_np)
    embeddings_np = embeddings_tensor.numpy()
    prediction = model.predict(embeddings_np)
    label = "Positive" if prediction[0][0] < 0.5 else "Negative"
    return label

def sentiment_analysis(text):
    clean  = clean_text(text)
    print("Texte nettoyé :", clean)
    model = initialize_model( r"C:\Users\Amayas\Downloads\ETL-SENTHELP-main\scripts\ELECTRA_Fed_CNN.h5")
    embeddings = embedding(clean)
    print("Embeddings générés :", embeddings.shape)
    label_sentiment = predict_sentiment(embeddings,model)
    print("Label de sentiment prédit :", label_sentiment)



    
# Exemple
if __name__ == "__main__":
    test_text = "Axa c'est une très bonne compagnie"
    sentiment_analysis(test_text)
    
    



