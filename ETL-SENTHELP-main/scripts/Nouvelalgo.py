from bs4 import BeautifulSoup
import time
from datetime import datetime
from scripts.models import tweet_collection, req_collection
from playwright.async_api import async_playwright
import asyncio
from datetime import datetime
from bson.json_util import dumps
from decouple import config
import pandas as pd
import json
from unidecode import unidecode
import argparse
import re
import json
import os
import psutil
from autoscraper import AutoScraper

# Variables d'environnement pour stocker les identifiants Twitter
USER_ID="@UserNumber59901"         # Identifiant utilisateur Twitter
USER_PASSWORD="aMkiuzi77/P"        # Mot de passe associé
USER_EMAIL = "scrapapiS7@gmail.com" # Adresse email liée au compte Twitter


def sleep():
    """Fait une pause de 3 secondes. 
    Utile pour éviter d'aller trop vite lors des interactions automatisées."""
    time.sleep(3)


# Date extraite du tweet
def conversion_timestamp(tweet_date) : 
    """Convertit une date ISO 8601 (ex: '2024-06-01T14:00:00.000Z') 
    en timestamp Unix (secondes depuis 1970)."""
    dt_object = datetime.strptime(tweet_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp = (dt_object.timestamp())
    return timestamp

def isodate(date_str, time_str):
    """Prend une date 'YYYY-MM-DD' et une heure 'HH:MM' et les transforme 
    en format ISO 8601 sous la forme 'YYYY-MM-DDTHH:MM:SS.sssZ'."""

    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class DonneeCollectee:
    """Classe représentant un tweet collecté avec tous ses attributs utiles pour stockage et traitement."""
    
    def __init__(self, text_tweet, nombre_likes, nombre_reposts, nombre_replies, nombre_views,
                 date_tweet, identifiant_tweet, req_id, mot_cle, timestamp): 
        self.text_tweet = text_tweet                    # Contenu brut du tweet
        self.cleaned_text_tweet = ""                    # Contenu nettoyé (à remplir plus tard)
        self.date_tweet = date_tweet                    # Date du tweet
        self.identifiant = int(identifiant_tweet)       # ID unique du tweet
        self.req_id = req_id                            # ID de la requête
        self.mot_cle = mot_cle                          # Mot-clé utilisé pour trouver ce tweet
        self.timestamp = timestamp                      # Timestamp de la date du tweet
        self.emotion = ""                               # Champ vide pour l’émotion prédite (à remplir)
        self.bool_analyse = False                       # Booléen indiquant si l’analyse a été faite

        # Gestion des compteurs (likes, reposts, etc.), conversion si sous format '3K' ou '1.2M'
        self.nombre_likes = self.convert_number(nombre_likes) if nombre_likes else 0
        self.nombre_reposts = self.convert_number(nombre_reposts) if nombre_reposts else 0
        self.nombre_replies = self.convert_number(nombre_replies) if nombre_replies else 0
        self.nombre_views = self.convert_number(nombre_views) if nombre_views else 0

    def convert_number(self, value):
        """Convertit une chaîne comme '3K' ou '1.2M' en entier."""
        if value[-1] == "K":
            return int(float(value[:-1]) * 1000)
        elif value[-1] == "M":
            return int(float(value[:-1]) * 1000000)
        else:
            return int(value)

    def add_comment(self, comment):
        """Ajoute un commentaire au tweet (fonction non encore utilisée)."""
        self.comment_tweet.append(comment)

    def to_dict(self):
        """Retourne l’objet tweet sous forme de dictionnaire pour insertion en base ou sérialisation."""
        return {
            "text_tweet": self.text_tweet,
            "cleaned_text_tweet": self.cleaned_text_tweet,
            "nombre_likes": self.nombre_likes,
            "nombre_reposts": self.nombre_reposts,
            "nombre_replies": self.nombre_replies,
            "nombre_views": self.nombre_views,
            "date_tweet": self.date_tweet,
            "timestamp_tweet": self.timestamp,
            "identifiant": self.identifiant,
            "req_id": self.req_id,
            "mot_cle": self.mot_cle,
            "bool_analyse": self.bool_analyse,
            "emotion": self.emotion
        }

async def confirmation_mail(page) : 
    """
    Vérifie si Twitter demande une confirmation d'e-mail pendant la connexion.
    Si l’input email est visible, retourne True.
    """
    try : 
        if await page.wait_for_selector('input[data-testid="ocfEnterTextTextInput"]', timeout=5000) :
            return True
        else : 
            return False
    except:
        return False
    
async def login(page):
    """
    Automatisation de la connexion à Twitter.
    Remplit les champs d’identifiant, email (si requis), mot de passe, puis valide.
    Retourne True si la connexion est réussie, sinon False
    """
    try:
        print("Début du processus de connexion...")
        await page.goto('https://twitter.com/i/flow/login')

        # Remplir l'identifiant
        user_id_input = await page.wait_for_selector('.r-1yadl64', timeout=12000)
        await user_id_input.fill(USER_ID)

        # Clic sur le bouton 'Suivant'
        login_button = await page.wait_for_selector(
            'div.css-175oi2r.r-1ny4l3l.r-6koalj.r-16y2uox div.css-175oi2r.r-16y2uox.r-f8sm7e.r-13qz1uu button:nth-child(6)',
            timeout=12000
        )
        await login_button.click()
        
        # Si Twitter demande une confirmation par e-mail
        if await confirmation_mail(page):
            await page.fill('input[data-testid="ocfEnterTextTextInput"]', USER_EMAIL)
            await page.keyboard.press("Enter")

        # Remplir le mot de passe
        password_input = await page.wait_for_selector('div.css-175oi2r input[type="password"]', timeout=5000)
        await password_input.fill(USER_PASSWORD)
        await page.keyboard.press("Enter")
        sleep()

        # Vérifie si l’utilisateur est connecté sur la page d’accueil
        is_connected = await page.locator('[data-testid="SideNav_AccountSwitcher_Button"]').is_visible()
        return is_connected

    except Exception as e:
        print(f"Erreur : {e}")
        return False

async def retry_function(page):
    """Si Twitter affiche un bouton 'Retry' (à cause d’une erreur de chargement), 
    on attend puis on clique dessus avce un compteur de tentatives."""
    retry_cnt = 0
    
    while retry_cnt < 15:
        try:
            # Recherche du bouton 'Retry'
            retry_button = await page.wait_for_selector('text="Retry"', timeout=5000)  # 5 secondes             
            # Attendre 10 minutes (600 secondes)
            await page.wait_for_timeout(600000)  # en millisecondes
            
            # Cliquer sur le bouton retry
            await retry_button.click()
            
            # Incrémenter le compteur
            retry_cnt += 1
            
            # Attendre 2 secondes après le clic
            await page.wait_for_timeout(2000)  # en millisecondes
        
        except Exception as e:
            # Si le bouton n'est plus présent ou autre erreur
            print(f"Erreur lors de la tentative de retry {retry_cnt}: {e}")
            break

async def perform_scroll(page, previous_tweets_elements):
    """
    Scrolle la page pour charger de nouveaux tweets. Si un bouton 'Retry' est détecté, on l'utilise.
    Compare les nouveaux tweets à ceux déjà récoltés avant pour voir si on a chargé de nouveaux tweets.
    Dans ce cas on retourne True, sinon False.
    """

    # Vérifie d'abord si le bouton Retry est présent
    try:
        retry_button = await page.wait_for_selector("//button[.//span[text()='Retry']]", timeout=2000)# 5 secondes de timeout
        if retry_button:
            await retry_function()
            print("Bouton Retry cliqué avec succès")
            return True  # On suppose que retry relance un chargement, donc on retourne ici True
    except:
        print("Bouton Retry non trouvé dans le délai imparti")

    # Si pas de bouton Retry, on continue avec le scroll
    await page.evaluate("window.scrollBy(0, window.innerHeight)")
    await page.wait_for_timeout(3000)

    # Récupérer les éléments des tweets de la page après le scroll
    html_content = await page.content()
    soup = BeautifulSoup(html_content, 'html.parser')
    tweet_elements = soup.select('[data-testid="tweet"]')
    for tweet_element in tweet_elements:
        tweet_div = tweet_element.find(attrs={'data-testid': 'tweetText'})
        if tweet_div is not None:
            tweet_text = tweet_div.get_text(strip=False)
        else:
            continue
    
    # Comparer les nouveaux tweets avec les précédents
    if tweet_elements != previous_tweets_elements:
        return True
    else:
        print("Aucun nouveau tweet n'a été chargé. Arrêt de l'extraction.")
        return False

async def contient_mots_espaces(tweet_text, principal, associated):
    """
    Vérifie la présence de mots-clés dans le texte du tweet.
    ex pour un mot-clé principal 'RSA' And ('allocations' or 'CAF'):
    Vérifie si le texte du tweet contient :
    - le mot principal exact (ex: 'RSA')
    - au moins un mot de la liste 'associated' (ex: ['allocations', 'CAF'])
    Retourne True si les conditions sont remplies, sinon False.
    """

    # Vérifie la présence exacte du mot principal
    principal_match = re.search(r'\b' + re.escape(principal) + r'\b', tweet_text)
    # Vérifie qu'au moins un mot associé est présent en entier
    assoc_found = False
    for asso in associated:
        pattern = r'\b' + re.escape(asso) + r'\b'
        match = re.search(pattern, tweet_text)
        if match:
            assoc_found = True
            break  # on s'arrête au premier trouvé

    return bool(principal_match and assoc_found)
               
  
async def scrap_tweets(nb_tweets,tweet_elements, mot_cle, principal, associated, current_tweet_amount, nb_tweets_par_mot, req_id, liste_tweets, utilisateurs, timestamp_fin, finrecolte, exception_count):

    """Fonction pour extraire les tweets pertinents en fonction des mots-clés.
    Prend en entrée
    - nb_tweets : nombre de tweets à récolter (si on souhaite faire une récolte limitée , finrecolte=False)
    - tweet_elements : liste des éléments de tweets extraits de la page HTML
    - mot_cle : mot-clé à rechercher dans les tweets
    - principal : mot-clé principal à vérifier
    - associated : liste de mots associés à vérifier
    - current_tweet_amount : compteur de tweets déjà collectés
    - nb_tweets_par_mot : compteur de tweets collectés pour le mot-clé actuel
    - req_id : identifiant de la requête pour le suivi
    - liste_tweets : liste pour stocker les tweets collectés
    - utilisateurs : liste pour stocker les identifiants des utilisateurs
    - timestamp_fin : timestamp de fin pour arrêter la récolte si nécessaire
    - finrecolte : booléen pour indiquer si la récolte doit se terminer à la fin de la période ou après un nombre de tweets
    - exception_count : compteur d'exceptions rencontrées pendant l'extraction
    Retourne les compteurs mis à jour et les listes de tweets et utilisateurs.
    Retourne aussi le dernier timestamp et la dernière date vue pour continuer la récolte plus tard.
    """

    last_timestamp = 0.0         # Pour mémoriser le timestamp du dernier tweet extrait
    last_tweet_date = ""         # Pour garder en mémoire la date du dernier tweet
    periode_atteinte = False     # Pour gérer l’arrêt de la récolte si la période est atteinte

    # Parcours des éléments de tweets extraits et extraction des informations pertinentes
    for tweet_element in tweet_elements:
        tweet_text_bis = ""
        tweet_div_text = tweet_element.find(attrs={'data-testid': 'tweetText'})  # Extraction du texte du tweet
        if tweet_div_text is None:  # Vérification de l'existence du texte du tweet sinon on passe au suivant
            exception_count += 1
            continue
        
        user_info = tweet_element.find(attrs={'data-testid': 'User-Name'}) # Extraction des informations de l'utilisateur
        if user_info is None:
            exception_count += 1
            continue
        user_links = user_info.find_all('a', href=True) # Extraction des liens de l'utilisateur
        if len(user_links) < 3:
            exception_count += 1
            continue

        user_href = user_links[2]['href'] 
        url_segments = user_href.split("/")
        if len(url_segments) < 4:
            exception_count += 1
            continue

        identifiant = url_segments[3] # Extraction de l'identifiant du tweet
        
        mot_cle = unidecode(mot_cle.lower())

        tweet_text = tweet_div_text.get_text(strip=False)
        tweet_text_bis = unidecode(tweet_text.lower())

        principal_clean = unidecode(principal.lower())
        associated_clean = [unidecode(asso.lower()) for asso in associated]
        
        # Vérification du mot-clé et de l'identifiant déjà traité
        if (await contient_mots_espaces(tweet_text_bis, principal_clean, associated_clean)) and (identifiant not in processed_tweets):
            time_tag = user_info.find('time') # Extraction de la date du tweet
            if time_tag is None:
                exception_count += 1
                continue
            date_str = time_tag['datetime'][0:24]

            last_timestamp = conversion_timestamp(date_str) # Conversion de la date en timestamp

            if last_timestamp < timestamp_fin and finrecolte: # Vérification de la période de récolte
                break
            if nb_tweets_par_mot == nb_tweets and not finrecolte :  # si on ne fait une récolte limitée dans le temps et qu'on a atteint le nombre de tweets voulu
                break
            details = tweet_element.find_all(attrs={'data-testid': 'app-text-transition-container'}) # Extraction des détails du tweet
            if len(details) < 3:
                exception_count += 1
                continue
            replies = details[0].get_text(strip=True) # Extraction du nombre de réponses
            reposts = details[1].get_text(strip=True) # Extraction du nombre de reposts
            likes = details[2].get_text(strip=True) # Extraction du nombre de likes
            views = details[3].get_text(strip=True) if len(details) >= 4 else "" # Extraction du nombre de vues
            utilisateur = url_segments[1] # Extraction de l'identifiant de l'utilisateur

            # Création de l'instance de DonneeCollectee avec les informations extraites
            tweet_instance = DonneeCollectee(tweet_text, likes, reposts, replies, views, date_str, identifiant,
                                             req_id, mot_cle, last_timestamp)
            
            # ajoute tweet dans un json pour le suivie 
            with open("test_memo.json", "a", encoding="utf-8") as f:
                f.write(dumps(tweet_instance.to_dict(), indent = 4, ensure_ascii=False))

            # Ajout de l'instance de tweet à la liste et de l'utilisateur à la liste des utilisateurs
            liste_tweets.append(tweet_instance)
            utilisateurs.append(utilisateur)

            # Ajout de l'identifiant du tweet traité pour éviter les doublons
            processed_tweets.add(identifiant)

            # Mise à jour des compteurs
            current_tweet_amount +=  1
            nb_tweets_par_mot += 1

            # Mise à jour de la dernière date vue
            last_tweet_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    return current_tweet_amount, nb_tweets_par_mot, liste_tweets, utilisateurs, last_timestamp, last_tweet_date, exception_count



async def scrape_autoscraper(nb_tweets,html_content, mot_cle, principal, associated, current_tweet_amount, 
nb_tweets_par_mot, req_id, liste_tweets, utilisateurs, timestamp_fin, finrecolte, exception_count,
scraper_content=None, scraper_url=None, scraper_date=None, scraper_stats=None, scraper_views=None):
    
    """Fonction pour extraire les tweets pertinents en fonction des mots-clés utilisant AutoScraper.
    Prend en entrée
    - nb_tweets : nombre de tweets à récolter (si on souhaite faire une récolte limitée , finrecolte=False)
    - tweet_elements : liste des éléments de tweets extraits de la page HTML
    - mot_cle : mot-clé à rechercher dans les tweets
    - principal : mot-clé principal à vérifier
    - associated : liste de mots associés à vérifier
    - current_tweet_amount : compteur de tweets déjà collectés
    - nb_tweets_par_mot : compteur de tweets collectés pour le mot-clé actuel
    - req_id : identifiant de la requête pour le suivi
    - liste_tweets : liste pour stocker les tweets collectés
    - utilisateurs : liste pour stocker les identifiants des utilisateurs
    - timestamp_fin : timestamp de fin pour arrêter la récolte si nécessaire
    - finrecolte : booléen pour indiquer si la récolte doit se terminer à la fin de la période ou après un nombre de tweets
    - exception_count : compteur d'exceptions rencontrées pendant l'extraction
    - scraper_content : AutoScraper utilisé pour extraire le texte du tweet
    - scraper_url : URL extraite par l'AutoScraper
    - scraper_date : date extraite par l'AutoScraper
    - scraper_stats : statistiques extraites par l'AutoScraper
    - scraper_views : vues extraites par l'AutoScraper
    Retourne les compteurs mis à jour et les listes de tweets et utilisateurs.
    Retourne aussi le dernier timestamp et la dernière date vue pour continuer la récolte plus tard.
    """
    last_timestamp = 0.0  # Pour mémoriser le timestamp du dernier tweet extrait
    last_tweet_date = ""  # Pour garder en mémoire la date du dernier tweet

    # Extraction des informations des tweets
    soup = BeautifulSoup(html_content, 'html.parser')
    tweet_elements = soup.select('[data-testid="tweet"]')
        
    temps_charge = datetime.now()
    # Écrire les éléments extraits dans un fichier HTML
   
    #print(f"temps de chargement : {datetime.now() - temps_charge}")

    # Parcours des éléments de tweets extraits et extraction des informations pertinentes
    for html_tweet in tweet_elements :
        tweet_html = str(html_tweet)
        if len(tweet_html) < 1:
            exception_count += 1
            continue  
        tweet_text = (scraper_content.get_result(html =tweet_html)[0]) # Extraction du texte du tweet
        if len(tweet_text) < 1:
            exception_count += 1
            continue
        tweet_text = tweet_text[0]
        url = scraper_url.get_result(html = tweet_html)[0] # Extraction de l'URL du tweet
        if len(url) < 1:
            exception_count += 1
            continue
        identifiant = url[0].split("/")[-1] # Extraction de l'identifiant du tweet
        tweet_text = unidecode(tweet_text.lower())
        principal_clean = unidecode(principal.lower())
        associated_clean = [unidecode(asso.lower()) for asso in associated]
    
        # Vérification du mot-clé et de l'identifiant déjà traité
        if (await contient_mots_espaces(tweet_text, principal_clean, associated_clean)) and (identifiant not in processed_tweets):
            
            # Extraction de l'utilisateur et de la date du tweet
            utilisateur = url[0].split("/")[1].replace("@", "")
            date = scraper_date.get_result(html = tweet_html)[0]
            date_str = date[0]
            last_timestamp = conversion_timestamp(date_str)

            if last_timestamp < timestamp_fin and finrecolte: # Vérification de la période de récolte est atteinte
                break
            
            if nb_tweets_par_mot == nb_tweets and not finrecolte : 
                break

            stats_list = (scraper_stats.get_result(html = tweet_html))[0] # Extraction des statistiques du tweet (likes, reposts, replies)
            if len(stats_list) < 1:
                exception_count += 1
                continue
            views = (scraper_views.get_result(html = tweet_html))[0] # Extraction des vues du tweet
            if len(views) < 1: 
                exception_count += 1
                continue
            views_text = views[0]

            replies = reposts = likes = views = 0 
            # Extraction des nombres de likes, reposts et replies
            for item in stats_list:
                if "Reply" in item:
                    replies = extract_number(item)
                elif "repost" in item.lower():
                    reposts = extract_number(item)
                elif "like" in item.lower():
                    likes = extract_number(item)
            if len(replies) < 1 or len(reposts) < 1 or len(likes) < 1:
                exception_count += 1
                continue
            
            # Si les vues sont présentes, on les extrait
            views = extract_views(views_text)
            

            # Création de l'instance de DonneeCollectee avec les informations extraites
            tweet_instance = DonneeCollectee(tweet_text, likes, reposts, replies, views, date_str, identifiant,
                                             req_id, mot_cle, last_timestamp)
            
            # Met à jour la liste des tweets et des utilisateurs
            liste_tweets.append(tweet_instance)
            utilisateurs.append(utilisateur)
            processed_tweets.add(identifiant)

            # mise à jour des compteurs
            current_tweet_amount +=  1
            nb_tweets_par_mot += 1

            # Met à jour la dernière date vue
            last_tweet_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")

    return current_tweet_amount, nb_tweets_par_mot, liste_tweets, utilisateurs, last_timestamp, last_tweet_date, exception_count


def extract_number(text):
    """Extrait un nombre d'une chaîne de texte.
    """
    print(text)
    match = re.search(r'\d+', text) # Recherche d'un nombre dans le texte
    return str(match.group()) if match else "" 

def extract_views(text):
    """Extrait le nombre de vues d'une chaîne de texte.
    """
    numbers = re.findall(r'\d+', text)
    return str(numbers[-1]) if numbers else ""


async def recolte(methode, nbtweets, lasttimestemp, datedebut, timestamp_fin, dictionnaire, finderecolte, req_id):
    """
    Fonction asynchrone de récolte des tweets.

    Paramètres :
    - methode : fonction à utiliser pour la recherche de tweets (ex : recherche avec mots-clés, hashtags, etc.)
    - nbtweets : nombre de tweets à collecter
    - lasttimestemp : timestamp du dernier tweet collecté précédemment
    - datedebut : date de début de la collecte (format : yyyy-mm-dd)
    - timestamp_fin : timestamp de fin de la période à couvrir
    - dictionnaire : dictionnaire dans lequel stocker les tweets collectés
    - finderecolte : évènement asynchrone permettant de signaler la fin de la récolte
    - req_id : identifiant de la requête, utile pour tracer la collecte

    Fonctionnement :
    - Lance la méthode de collecte fournie en paramètre.
    - Utilise Playwright pour automatiser la navigation et la collecte de tweets.
    - Connexion à Twitter, effectue des recherches basées sur les mots-clés du dictionnaire.
    - Scrappe les tweets pertinents en fonction des mots-clés et de la méthode choisie.
    - Met à jour le dictionnaire avec les nouveaux tweets.
    - Gère les erreurs et les cas limites.
    - Signale la fin de la collecte via l'événement `finderecolte`.
    """
    # Initialisation des variables de suivi
    termine = False
    scroll_count, current_tweet_amount = 0, 0
    liste_tweets, utilisateurs = [], []
    lastdate = ""
    last_timestemp = lasttimestemp
    nb_tweets = nbtweets
    exception_count = 0
    
    # Convertir le dictionnaire {mot_clé: [mots_associés]} en liste pour traitement par lots
    items_list = list(dictionnaire.items())
    total_items = len(items_list)
    
    # Si la méthode utilisée n'est pas BS4, initialiser et charger les scrapers AutoScraper
    if methode != "bs4":
        scraper_url = AutoScraper()
        scraper_date = AutoScraper()
        scraper_author = AutoScraper()
        scraper_content = AutoScraper()
        scraper_stats = AutoScraper()
        scraper_views = AutoScraper()

        # Charger les modèles AutoScraper
        scraper_url.load("scripts/scraper_url.json")
        scraper_date.load("scripts/scraper_date.json")
        scraper_author.load("scripts/scraper_author.json")
        scraper_content.load("scripts/scraper_content.json")
        scraper_stats.load("scripts/scraper_stats.json")
        scraper_views.load("scripts/scraper_views.json")

    # Boucle sur les mots-clés par lots de 20
    for i in range(0, total_items, 20):
        max_retries = 5
        debut = datetime.now()  # Chronométrer la durée du lot
        current_batch = items_list[i:min(total_items, i + 20)]  # Sous-liste des mots-clés à traiter

        #print(f"Traitement du lot {i//20 + 1} ({len(current_batch)} mots-clés)")

        try:
            # Démarrage du navigateur avec Playwright
            async with async_playwright() as p:
                print("Lancement du navigateur...")
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                print("Nouveau navigateur lancé.")
                page = await browser.new_page()
                print("Nouvelle page créée.")

                termine = False
                retry = 0
                while not termine:
                    # Connexion à Twitter
                    if await login(page):
                        print("Connexion réussie, début du scraping...")

                        # Traitement de chaque mot-clé du lot
                        for (principal, associated) in current_batch:
                            temps_scrap = datetime.now()
                            last_timestemp = lasttimestemp
                            mot_cle = generate_twitter_search_query(principal, associated)
                            processed_tweets = set()

                            # Construire l'URL de recherche
                            search_url = f'https://twitter.com/search?f=live&q={mot_cle}-filter%3Aimages%20-filter%3Avideos%20lang%3Afr%20until%3A{datedebut}&src=typed_query'
                            await page.goto(search_url)
                            await asyncio.sleep(5)

                            terminer_mot_cle = False
                            nb_tweets_par_mot = 0

                            # Boucle de scraping pour un mot-clé
                            while not terminer_mot_cle:
                                html_content = await page.content()  # Récupération du HTML
                                soup = BeautifulSoup(html_content, 'html.parser')
                                tweet_elements = soup.select('[data-testid="tweet"]')  # Sélection des tweets

                                if len(tweet_elements) != 0:
                                    # Traitement avec la méthode BS4
                                    if methode == "bs4":
                                        current_tweet_amount, nb_tweets_par_mot, liste_tweets, utilisateurs, last_timestemp, lastdate , exception_count = await scrap_tweets(
                                            nb_tweets, tweet_elements, mot_cle, principal, associated,
                                            current_tweet_amount, nb_tweets_par_mot, req_id, liste_tweets,
                                            utilisateurs, timestamp_fin, finderecolte, exception_count
                                        )
                                    # Traitement avec AutoScraper
                                    else:
                                        current_tweet_amount, nb_tweets_par_mot, liste_tweets, utilisateurs, last_timestemp, lastdate, exception_count = await scrape_autoscraper(
                                            nbtweets, html_content, mot_cle, principal, associated,
                                            current_tweet_amount, nb_tweets_par_mot, req_id, liste_tweets,
                                            utilisateurs, timestamp_fin, finderecolte, exception_count,
                                            scraper_content, scraper_url, scraper_date, scraper_stats, scraper_views
                                        )

                                # Condition d'arrêt 1 : période atteinte
                                if last_timestemp < timestamp_fin and finderecolte:
                                    print("Nous avons récupéré les tweets de la période donnée pour ce mot-clé")
                                    #print(f"nb de tweets pour {principal}: {nb_tweets_par_mot}")
                                    terminer_mot_cle = True
                                    break

                                # Condition d’arrêt 2 : nombre de tweets suffisant atteint
                                if not finderecolte and nb_tweets_par_mot >= nb_tweets:
                                    print(f"Nous avons récupéré le nombre de tweets voulus pour {principal}")
                                    #print(f"nb de tweets: {nb_tweets_par_mot}")
                                    terminer_mot_cle = True
                                    break

                                # Condition d’arrêt 3 : plus de nouveaux tweets après scroll
                                if not await perform_scroll(page, tweet_elements):
                                    print(f"Plus de nouveau tweets pour {principal}")
                                    terminer_mot_cle = True
                                    break

                                scroll_count += 1  # Incrémentation du nombre de scrolls
                            #print(f"temps de scrapping : {datetime.now() - temps_scrap}")
                        termine = True  # Fin du traitement du lot
                    else:
                        # En cas d'échec de connexion, retenter jusqu'à 5 fois
                        if retry < max_retries:
                            #print(f"Échec de la connexion. Nouvelle tentative dans {5}s...")
                            await asyncio.sleep(5)
                            retry += 1
                        else:
                            # Abandon si trop d'échecs
                            return current_tweet_amount, scroll_count, termine, last_timestemp, lastdate, liste_tweets

                # Fermer le navigateur à la fin du lot
                await browser.close()
                #print(f"Navigateur fermé après le traitement du lot {i//20 + 1}")
                #print(f"temps : {datetime.now() - debut}")
        except Exception as e:
            print("Erreur lors du lancement du navigateur :", str(e))
    
    # Fin du processus de récolte
    print(f"Récolte terminée. Total de tweets récupérés: {len(liste_tweets)}")
    print(f"Nombre d'exceptions rencontrées: {exception_count}")

    return current_tweet_amount, scroll_count, termine, last_timestemp, lastdate, liste_tweets


def generate_twitter_search_query(mot_cle_principal, mots_associes):
    """
    Génère une requête Twitter pour un mot-clé principal et une liste de mots associés.
    """
    if not mots_associes:
        return f'"{mot_cle_principal}"'
    
    mots_associes_str = " OR ".join(f'"{mot}"' for mot in mots_associes)
    return f'"{mot_cle_principal}" AND ({mots_associes_str})'



processed_tweets = set()

def main(fichier, datedebut, heure, datefin, heurefin, methode, nombre_tweets, finrecolte) :
    """
    Fonction principale de lancement de la collecte de tweets.

    Paramètres :
    ----------
    fichier : str
        Chemin vers le fichier JSON contenant les mots-clés à utiliser pour la collecte.
    datedebut : str
        Date de début de la période de collecte (format YYYY-MM-DD).
    heure : str
        Heure de début de la collecte (format HH:MM).
    datefin : str
        Date de fin de la période de collecte (format YYYY-MM-DD).
    heurefin : str
        Heure de fin de la collecte (format HH:MM).
    methode : str
        Méthode de scraping utilisée pour la collecte (ex: BeautifulSoup, AutoScraper).
    nombre_tweets : int
        Nombre de tweets à collecter (0 pour tout récupérer jusqu'à la fin de la période).
    finrecolte : bool
        Si True, la collecte continue jusqu'à atteindre la date de fin ou le dernier tweet disponible.

    Fonctionnement :
    ---------------
    - Convertit les dates de début et de fin au format timestamp.
    - Charge les mots-clés depuis le fichier donné.
    - Lance la fonction de récolte `recolte()` de manière asynchrone.
    - Sauvegarde les tweets récoltés dans un fichier JSON (`tweets_raw.json`).
    - Sauvegarde les métadonnées de la requête (req_id) dans `req.json`.

    Retour :
    -------
    termine : bool
        Indique si la collecte a atteint son objectif (nombre de tweets ou date limite).
    """
         
    debut = datetime.now()

    # Convertit les dates et heures en timestamp (secondes depuis epoch)
    timestampdebut = conversion_timestamp(isodate(datedebut, heure))
    timestampfin = conversion_timestamp(isodate(datefin, heurefin))

    print(finrecolte)  # Affiche le mode de fin de récolte (booléen)

    # Chargement du fichier contenant les mots-clés (dictionnaire)
    with open(fichier, "r", encoding="utf-8") as f:
        dictionnaire = json.load(f)

        # Génère un identifiant de requête unique basé sur la date et l'heure
        req_id = datetime.now().strftime("%Y%m%d%H%M")

        # Initialise la position de départ pour la collecte (au début de l'intervalle)
        lastimestamptweet = timestampdebut
        lastdatetweet = datedebut

        # Lance la fonction asynchrone de récolte
        nb_tweets, nb_scrolls, termine, lastimestamptweet, lastdatetweet, tweetscollection = asyncio.run(
            recolte(methode, nombre_tweets, lastimestamptweet, lastdatetweet, timestampfin, dictionnaire, finrecolte, req_id)
        )
        # Supprime le contenu du fichier de suivi des tweets pour éviter les doublons
        with open("./tweets_raw.json", "w", encoding="utf-8") as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        # Si des tweets ont été collectés, les sauvegarder dans un fichier JSON
        if len(tweetscollection) != 0:
            tweets_to_save = [tweet.to_dict() for tweet in tweetscollection]
            with open("./tweets_raw.json", "w", encoding="utf-8") as f:
                json.dump(tweets_to_save, f, indent=4, ensure_ascii=False)
                print(f"chemin : {os.path.abspath(f.name)}")
            print(f"Nombre de tweets récoltés : {len(tweetscollection)}")

        # Enregistre les métadonnées de la requête dans un fichier json pour les étapes suivantes du pipeline
        req_doc = {
            "req_id": req_id,
            "corpus": dictionnaire,
            "timestamp_debut": timestampdebut,
            "timestamp_fin": timestampfin,
            "nb_tweets": nb_tweets,
            "nb_scrolls": nb_scrolls,
            "fin_recolte": False,
            "bool_group_analysis": False,
        }

        with open("./req.json", "w", encoding="utf-8") as f:
            json.dump(req_doc, f, indent=4, ensure_ascii=False)
            print(f"chemin : {os.path.abspath(f.name)}")

        # Indique si la récolte est terminée (True/False)
        return termine

        

if __name__ == "__main__":
    process = psutil.Process(os.getpid())  # Récupère le processus actuel pour suivi éventuel (mémoire, etc.)

    # Initialise l'analyseur d’arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Script de collecte de tweets.")

    # Ajoute les arguments obligatoires
    parser.add_argument("fichier", type=str, help="Fichier contenant les mots-clés (JSON).")
    parser.add_argument("heure", type=str, help="Heure de début de collecte (HH:MM).")
    parser.add_argument("datedebut", type=str, help="Date de début (format YYYY-MM-DD).")
    parser.add_argument("heurefin", type=str, help="Heure de fin de collecte (HH:MM).")
    parser.add_argument("datefin", type=str, help="Date de fin (format YYYY-MM-DD).")
    parser.add_argument("methode", type=str, help="Méthode de récolte (e.g., bs4, autoscraper).")
    parser.add_argument("nombre_tweets", type=int, help="Nombre de tweets à récolter (0 pour tous).")

    # Argument optionnel : True si on souhaite continuer jusqu'à la fin de la période définie
    parser.add_argument("--finrecolte", action="store_true", help="Collecte tous les tweets jusqu'à la fin de la période.")

    # Analyse les arguments passés en ligne de commande
    args = parser.parse_args()

    # Appelle la fonction principale avec les arguments du CLI
    termine = main(args.fichier, args.datedebut, args.heure, args.datefin, args.heurefin, args.methode, args.nombre_tweets, args.finrecolte)

    