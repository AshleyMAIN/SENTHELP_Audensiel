import pymongo
import os
import pprint
import pickle

# Connexion à la base de données MongoDB à l'aide du nom du service MongoDB défini dans Docker Compose
client = pymongo.MongoClient("mongodb+srv://cloe:Webscrap23@cluster0.qnvy73r.mongodb.net/?authMechanism=SCRAM-SHA-1")

#load modele de prétraitement et d'analyse de sentiment

model = None
#model = pickle.load(open("mon_modele.pkl", "rb"))  # adapte le chemin

# client = pymongo.MongoClient(os.getenv('MONGO_URL'))
# Sélection de la base de données
db = client['Tweets']

def preprocess_tweet(text):
    return text

def sentiment_analysis(text):

    if model is None : 
        return "Model not loaded"
    sentiment = model.predict(text)[0]
    return sentiment



def appretissage_continued():
    #prend le modèle et l'entraîne avec les nouveaux tweets
    new_tweets = db['tweets'].find({"sentiment": {"$exists": True}})
    if model is None:
        return "Model not loaded"
    for tweet in new_tweets:
        model.fit(tweet["cleaned_text"], tweet["sentiment"]) 
    # Ici, vous pouvez ajouter la logique pour entraîner le modèle avec les nouveaux tweets
    # debut d'enrainement

    # Enregistrer le modèle mis à jour
    with open("mon_modele.pkl", "wb") as f:
        pickle.dump(model, f)