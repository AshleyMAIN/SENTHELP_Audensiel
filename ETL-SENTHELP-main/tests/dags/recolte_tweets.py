from django.http import HttpResponse
from bs4 import BeautifulSoup
import time
from datetime import datetime
import traceback
from django.shortcuts import render
from twittersearch.models import tweet_collection, req_collection
from playwright.async_api import async_playwright
import asyncio
from datetime import datetime
from django.http import JsonResponse
from bson.json_util import dumps
import aiohttp
from decouple import config
from django.http import HttpResponse
from db_connection import db
import pandas as pd
import json
from unidecode import unidecode
import argparse
import json

# Variables d'environnement pour stocker les identifiants Twitter
USER_ID = config('USER_ID')
USER_PASSWORD = config('USER_PASSWORD')

# fonction pour faire une pause aléatoire
def random_sleep():
    """Réalise une pause aléatoire entre 2 et 5 secondes. 
    """
    time.sleep(3)

# Date extraite du tweet
def conversion_timestamp(tweet_date) : 
    # Conversion en objet datetime
    dt_object = datetime.strptime(tweet_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    # et si en format : YYYY-MM-DD : 
    # Conversion en timestamp (secondes depuis l'époque Unix)
    timestamp = (dt_object.timestamp())

    return timestamp

def isodate(date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

class Commentaires: # Classe pour stocker les commentaires d'un tweet
    def __init__(self, commentaires=None, timelist=None):
        self.commentaires = commentaires if commentaires else [] # Liste des commentaires
        self.date_commentaire = timelist if timelist else [] # Liste des dates des commentaires

    def add_comment(self,comment, timelist): 
        """
        Ajouter un commentaire à la liste des commentaires
        """
        for comm, time in zip(comment, timelist):
            self.commentaires.append(comm)
            self.date_commentaire.append(time)

    def to_dict(self): 
        """
        Convertir l'objet en dictionnaire
        """
        #if not empty
        if self.commentaires:
            return [{"commentaire": c, "date_commentaire": d} for c, d in zip(self.commentaires, self.date_commentaire)]

        else:
            return [{"commentaire": "", "date_commentaire": ""}]

class DonneeCollectee: # Classe pour stocker les données d'un tweet
    
    def __init__(self, text_tweet, nombre_likes, nombre_reposts, nombre_replies, nombre_views, date_tweet, identifiant_tweet, req_id, mot_cle):
        self.text_tweet = text_tweet
        self.date_tweet = date_tweet
        self.identifiant = int(identifiant_tweet)
        self.req_id = req_id
        self.mot_cle = mot_cle
        if nombre_likes == "":
            self.nombre_likes = 0
        else:
            self.nombre_likes = self.convert_number(nombre_likes)

        if nombre_reposts == "":
            self.nombre_reposts = 0
        else:
            self.nombre_reposts = self.convert_number(nombre_reposts)

        if nombre_replies == "":
            self.nombre_replies = 0
        else:
            self.nombre_replies = self.convert_number(nombre_replies)

        if nombre_views == "":
            self.nombre_views = 0
        else:
            self.nombre_views = self.convert_number(nombre_views)
        self.bool_analyse = False
        self.comment_tweet = Commentaires() 
        #elf.reaction = None
        self.emotion = ""

    # === PRIVATE METHODS === # 
    def convert_number(self, value):  # Convertir les nombres en entiers # Convertir les nombres en entiers
        if value[-1] == "K":
            return int(float(value[:-1]) * 1000)
        elif value[-1] == "M":
            return int(float(value[:-1]) * 1000000)
        else:
            return int(value)

    def add_comment(self, comment):  # Ajouter un commentaire à la liste des commentaires
        self.comment_tweet.append(comment)

    # === PUBLIC METHODS === #
    def to_dict(self):  # Convertir l'objet en dictionnaire # Convertir l'objet en dictionnaire
        return {
            "text_tweet": self.text_tweet,
            "nombre_likes": self.nombre_likes,
            "nombre_reposts": self.nombre_reposts,
            "nombre_replies": self.nombre_replies,
            "nombre_views": self.nombre_views,
            "timestamp_tweet": self.date_tweet, #faire en iso date car timestamp 
            "identifiant": self.identifiant,
            "comment_tweet": self.comment_tweet.to_dict(),
            "req_id": self.req_id,
            "mot_cle": self.mot_cle,
            "bool_analyse": self.bool_analyse,
            #reaction":self.reaction,
            "emotion":self.emotion
        }


async def confirmation_mail(page) : 
    #regarde la page et si on trouve qu'on est passé à la page d'acceuil ou pas
    try : 
        if await page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').is_visible(timeout=5000):
            return False
        else : 
            return True 
    except:
        return True  
    
async def login(page):
    try:
        print("🟡 Début du processus de connexion...")
        await page.goto('https://twitter.com/i/flow/login')
        print("✅ Page de connexion chargée.")

        # Remplissage de l'identifiant
        user_id_input = await page.wait_for_selector('.r-1yadl64', timeout=12000)
        await user_id_input.fill(USER_ID)
        print("✅ Identifiant rempli.")

        # Clic sur le bouton de connexion
        login_button = await page.wait_for_selector(
            'div.css-175oi2r.r-1ny4l3l.r-6koalj.r-16y2uox div.css-175oi2r.r-16y2uox.r-f8sm7e.r-13qz1uu button:nth-child(6)',
            timeout=12000
        )
        await login_button.click()
        print("✅ Bouton de connexion cliqué.")

        # Remplissage du mot de passe
        password_input = await page.wait_for_selector('div.css-175oi2r input[type="password"]', timeout=12000)
        await password_input.fill(USER_PASSWORD)
        await page.keyboard.press("Enter")
        print("✅ Mot de passe rempli et validation en cours...")

        random_sleep()

        # Vérification de la page de confirmation par email
        if await confirmation_mail(page):
            print("🟡 Demande de confirmation par email détectée.")
            email_input = await page.locator('input[name="email"]').is_visible(timeout=5000) # à vérifier si c'est vraiment ce selecteur 
            if email_input:
                await page.locator('input[name="email"]').fill(USER_EMAIL)
                await page.keyboard.press("Enter")
                print("✅ Email de confirmation rempli et soumis.")
                random_sleep()

        # Vérifier si on est connecté après la confirmation
        is_connected = await page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').is_visible(timeout=5000)
        if is_connected:
            print("🎉 Connexion réussie !")
        else:
            print("❌ Échec de la connexion après validation.")

        return is_connected

    except Exception as e:
        print(f"❌ Erreur : {e}")
        return False
    
async def perform_scroll(page, previous_tweets_elements):

    await page.evaluate(f"window.scrollBy(0, window.innerHeight)")  # Scroll égal à la hauteur de la fenêtre
    await page.wait_for_timeout(5000)

    # Récupérer les éléments de tweet
    html_content = await page.content()
    soup = BeautifulSoup(html_content, 'html.parser')

    tweet_elements = soup.select('[data-testid="tweet"]')
    for tweet_element in tweet_elements:
        tweet_div = tweet_element.find(attrs={'data-testid': 'tweetText'})
        if tweet_div is not None:
            tweet_text =  tweet_div.get_text(strip=False)
        else:
            continue
   
    if tweet_elements != previous_tweets_elements:
        return True
    else:
	# verifier si message n'apparait pas 
        print("Aucun nouveau tweet n'a été chargé. Arrêt de l'extraction.")
        #print(f"\nTemps de verification : {(datetime.now()-start).total_seconds():.10f}")
        return False


async def contient_mots_espaces(tweet_text, mot_cle):
    mots_clés = mot_cle.split()  # Découpe le mot-clé en plusieurs mots et met en minuscule
    return any(mot in tweet_text for mot in mots_clés)  
               
  
async def scrap_tweets(tweet_elements, mot_cle, current_tweet_amount, req_id, liste_tweets,
                       utilisateurs):
    lasttimestemp = 0.0
    date = ""
    for tweet_element in tweet_elements:
        tweet_div_text = tweet_element.find(attrs={'data-testid': 'tweetText'})
        if tweet_div_text is not None:
            tweet_text = tweet_div_text.get_text(strip=False)
        else:
            continue
        mot_cle  = unidecode(mot_cle.lower())  
        tweet_text = unidecode(tweet_text.lower())  # Enlève les accents et met en minuscule
        user_info = tweet_element.find(attrs={'data-testid': 'User-Name'})
        user_info2 = user_info.find_all('a', href=True)
        user_info2 = user_info2[2]['href']
        url_segments = user_info2.split("/")
        identifiant = url_segments[3]
        if (await contient_mots_espaces(tweet_text, mot_cle) and ( identifiant not in processed_tweets )) : 
            details = tweet_element.find_all(attrs={'data-testid': 'app-text-transition-container'})
            replies = details[0].get_text(strip=True)
            reposts = details[1].get_text(strip=True)
            likes = details[2].get_text(strip=True)
            views = details[3].get_text(strip=True) if len(details) >= 4 else ""
            user_info = user_info.find('time')
            date = user_info['datetime'][0:24]
            print(date)
            lasttimestemp = conversion_timestamp(date)
            print(lasttimestemp)
            utilisateur = url_segments[1]
            tweets_instance = DonneeCollectee(tweet_text, likes, reposts, replies, views, lasttimestemp, identifiant,
                                            req_id, mot_cle)
            save_tweets(tweets_instance, req_id)
            liste_tweets.append(tweets_instance)
            utilisateurs.append(utilisateur)
            current_tweet_amount += 1
            processed_tweets.add(identifiant)

    return current_tweet_amount, liste_tweets, utilisateurs, lasttimestemp, date

def save_tweets(tweets,req_id): # Fonction pour enregistrer les tweets dans la base de données
    element = tweets.to_dict()
    # print(element)
    if tweet_collection.find_one({"identifiant": element["identifiant"]}):  # Vérifier si l'élément existe déjà # Vérifier si l'élément existe déjà
        print("L'élément existe déjà")
        tweet_collection.update_one({"identifiant": element["identifiant"]},
                                     {"$set": {"nombre_views": element["nombre_views"],
                                               "nombre_likes": element["nombre_likes"],
                                               "nombre_reposts": element["nombre_reposts"],
                                               "nombre_replies": element["nombre_replies"]},
                                      "$addToSet": {"comment_tweet": {"$each": element["comment_tweet"]}} # Ajouter les nouveaux commentaires à la liste des commentaires existants
                                      },
                                      upsert=False
                                    )

    else: 
        print("L'élément n'existe pas")
        tweet_collection.insert_one(element)

async def recolte(lasttimestemp, datedebut, timestamp_fin, motclé, finderecolte, req_id) : 

    processed_tweets = set()
    termine = False
    #transformer dates en timestamp
    until_date =  datetime.strptime(datedebut, "%Y-%m-%dT%H:%M:%S.%fZ")
    until_date = until_date.strftime("%Y-%m-%d")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await login(page)
        search_url = f'https://twitter.com/search?f=live&q={motclé}-filter%3Aimages%20-filter%3Avideos%20lang%3Afr%20until%3A{until_date}&src=typed_query'
        await page.goto(search_url)
        await asyncio.sleep(5)
        # 5. Scraping des tweets
        scroll_count, current_tweet_amount = 20, 0
        liste_tweets, utilisateurs = [], []
        while True : 
            # Extraction des tweets sur une page
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            # Extraction des informations des tweets
            tweet_elements = soup.select('[data-testid="tweet"]')
            current_tweet_amount, liste_tweets, utilisateurs, lasttimestemp, lastdate = await scrap_tweets(
                tweet_elements, motclé, current_tweet_amount, req_id, liste_tweets, utilisateurs
            )
            # Scrolling
            print(lasttimestemp)
            if lasttimestemp <timestamp_fin and finderecolte : #chnager la condition d'arrêt et prendre la date des tweets parcouru
                #total_time["scrolling"] += (datetime.now() - start3).total_seconds()
                print("nous avons récupéré les tweets de la période donnée")
                termine = True
                break
            if not await perform_scroll(page, tweet_elements):
                print("fin de scroll")
                if (await page.keyboard.press("Réessayer")) : #verifier si y'a un message d'erreur ou pas 
                    termine = False
                break
            scroll_count += 1

    #saubegarde des tweets 
    return current_tweet_amount, scroll_count, termine , lasttimestemp, lastdate

# Fonction pour générer l'URL de recherche Twitter
def generate_twitter_search_url(principal, associated_keywords,until_date):
    query = f'"{principal}" AND (' + " OR ".join(f'"{mot}"' for mot in associated_keywords) + ")"
    search_url = f'https://twitter.com/search?f=live&q={query}-filter%3Aimages%20-filter%3Avideos%20lang%3Afr%20until%3A{until_date}&src=typed_query'
    return search_url

def generate_twitter_search_query(mot_cle_principal, mots_associes):
    """
    Génère une requête Twitter pour un mot-clé principal et une liste de mots associés.
    """
    if not mots_associes:
        return f'"{mot_cle_principal}"'
    
    mots_associes_str = " OR ".join(f'"{mot}"' for mot in mots_associes)
    return f'"{mot_cle_principal}" AND ({mots_associes_str})'

processed_tweets = set()
def main(fichier, datedebut, datefin, finrecolte) : 
    #initialiser la requêtre dans la fonction main 
    timestampdebut = conversion_timestamp(datedebut)
    timestampfin = conversion_timestamp(datefin)
    print(timestampfin)
    print(timestampdebut)

    #parcours du fichier :
    nb_tweets = 0
    nb_scrolls = 0
    with open(fichier, "r", encoding="utf-8") as f:
        mot = json.load(f)
        for (principal, associated) in mot.items() : 
            time = datetime.now()
            termine = False
            url = generate_twitter_search_url(principal, associated,datedebut)
            mot_cle = generate_twitter_search_query(principal, associated)
            processed_tweets = set()
            lastimestamptweet = timestampdebut
            lastdatetweet = datedebut
            req_id = datetime.now().strftime("%Y%m%d%H%M")
            req_doc = {
                "req_id": req_id,
                "mot_cle": mot_cle,
                "timestamp_debut": timestampdebut,
                "timestamp_fin": timestampfin,
                "nb_tweets": 0,
                "nb_scrolls": 0,
                "fin_recolte": False,
                "bool_group_analysis": False,
            }
            param_req = req_collection.insert_one(req_doc)
            req_id = str(param_req.inserted_id)
            req_collection.update_one({"_id": param_req.inserted_id}, {"$set": {"req_id": req_id}})
            while not termine : 
                nb_tweets_temp , nb_scrolls_temp, termine, lastimestamptweet, lastdatetweet = asyncio.run(recolte(lastimestamptweet, lastdatetweet, timestampfin, mot_cle, finrecolte, req_id))
                nb_tweets = nb_tweets + nb_tweets_temp
                nb_scrolls = nb_scrolls + nb_scrolls_temp
            req_collection.update_one({"_id": param_req.inserted_id},{"$set": {"nb_tweets": nb_tweets, "nb_scrolls": nb_scrolls}})
            print(f"temps d'exécution pour {mot_cle} : {datetime.now()-time}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script de collecte de tweets.")
    parser.add_argument("fichier", type=str, help="Fichier contenant les mots-clés (un par ligne).")
    parser.add_argument("heure", type=str, help="heure de début de collecte")
    parser.add_argument("datedebut", type=str, help="Date de début de collecte (format YYYY-MM-DD).")
    parser.add_argument("heurefin", type=str, help= "heure de fin de collecte")
    parser.add_argument("datefin", type=str, help="Date de fin de collecte (format YYYY-MM-DD).")
    parser.add_argument("--finrecolte", action="store_true", help="Indique si la collecte est terminée.")

    args = parser.parse_args()
    datedebut = isodate(args.datedebut, args.heure)
    datefin = isodate(args.datefin, args.heurefin)
    main(args.fichier, datedebut, datefin, args.finrecolte)
