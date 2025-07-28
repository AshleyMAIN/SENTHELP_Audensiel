from scripts.db_connection import db


# Sélection des collections à partir de db qui est la base de tweets
tweet_collection = db['tweets']
req_collection = db['requests']

#print("connexion réussie")
#print(tweet_collection)
#print(req_collection)