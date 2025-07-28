import pymongo
import os
import pprint
import pickle

# Connexion à la base de données MongoDB à l'aide du nom du service MongoDB défini dans Docker Compose
client = pymongo.MongoClient("mongodb+srv://audensielrd:lNH4fO4YPqDjGJvd@recolte.2nowcyu.mongodb.net")
#mongodb+srv://cloe:Webscrap23@cluster0.qnvy73r.mongodb.net/?authMechanism=SCRAM-SHA-1
#load modele de prétraitement et d'analyse de sentiment

model = None
#model = pickle.load(open("mon_modele.pkl", "rb"))  # adapte le chemin

# client = pymongo.MongoClient(os.getenv('MONGO_URL'))
# Sélection de la base de données
db = client['Recolte']

def preprocess_tweet(text):
    return text

def sentiment_analysis(text):
    return 

def mongo_stream_method() :  # tester et ok ça fonctionne 
    # Create your models here.
    tweet_collection = db['tweets']
    print("✅ inference_test.py est bien lancé")
    with tweet_collection.watch() as stream:
        for change in stream: # si on veut récupérer les tweets il sont dans fullDocument
            pprint.pprint(change['fullDocument'])# ➜ ne marche PAS sans replica set
                

if __name__ == "__main__":
    mongo_stream_method()