from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime, timedelta
import subprocess
import os
import json
import psutil
import csv
from pymongo import MongoClient
from airflow.models import Variable
import pandas as pd
import time
import os
from threading import Thread

SCRIPT_MODULE = "scripts.Nouvelalgo"
CORPUS_PATH = "scripts/corpus2.json"
EXTRACTION_DIR = "/usr/local/airflow/"
METRICS_CSV = "/usr/local/airflow/metrics.csv"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def monitoring(pid, results):
    process = psutil.Process(pid)
    print(f"Monitoring process {pid}...")
    cpu_set = set()
    mem_max = 0
    mem_max_system = 0
    cpu_percent_max_process = 0
    cpu_percent_max_system = 0
    while results["running"]:
        try:
            mem = process.memory_info().rss / 1024 ** 2  # en MB
            mem_max = max(mem_max, mem)

            mem_system = psutil.virtual_memory().used / 1024 ** 2  # en MB
            mem_max_system = max(mem_max_system, mem_system)

            cpu_set.update(process.cpu_affinity())  

            cpu_percent_process = process.cpu_percent(interval=0.1)
            cpu_percent_system = psutil.cpu_percent(interval=0.1)
        
            cpu_percent_max_process = max(cpu_percent_max_process, cpu_percent_process)
            cpu_percent_max_system = max(cpu_percent_max_system, cpu_percent_system)



            time.sleep(0.1)
        except psutil.NoSuchProcess:
            break

    results["cpu_percent_process"] = cpu_percent_max_process
    results["cpu_percent_system"] = cpu_percent_max_system
    results["mem_max_process"] = mem_max
    results["mem_max_system"] = mem_max_system

def append_metrics_to_csv(metrics, path=METRICS_CSV):
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=metrics.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(metrics)


def initialize_data(**kwargs):
    """
    Tâche Airflow : Exécute le script de collecte initialisante des données via un sous-processus et enregistre les métriques.

    - Lance un thread de monitoring de la consommation mémoire pendant l'exécution du script.
    - Exécute un script Python avec des arguments liés à la période d'extraction des tweets 25 juin 2026 au 1 janvier 2006 (création de Twitter).
    - Mesure la durée d’exécution et envoie le résultat dans XCom :
        * `start_time` : heure de début
        * `extract_time` : durée totale d’exécution
        * `status` : succès ou échec
    - Affiche la sortie standard et les erreurs si le script échoue.
    """

    # Enregistre l'heure de début d'exécution de la tâche
    start_time = datetime.now()

    # Récupère l'identifiant du processus courant (utile pour le monitoring)
    pid = os.getpid()
    print("🔍 Starting monitoring extract_data ...")

    # Démarre un thread pour surveiller la consommation mémoire du processus
    results = {"running": True}  # Drapeau de contrôle pour arrêter le thread ensuite
    monitor_thread = Thread(target=monitoring, args=(pid, results))
    monitor_thread.start()

    # Définit le début et la fin de la période d'extraction
    today = "2025-06-26"
    # Calcule la date d’hier à la même heure (10h30)
    day_ago = "2006-01-01"

    # Prépare la commande à exécuter pour lancer le script Python de scraping
    cmd = [
        "python", "-m", SCRIPT_MODULE,      # Lancement du module Python à exécuter
        CORPUS_PATH,                        # Chemin vers le corpus
        "10:30", today,    # Heure et date de fin d’extraction
        "10:30", day_ago,  # Heure et date de début d’extraction
        "bs4", "0", "--finrecolte"          # Paramètres supplémentaires : méthode bs4, index, etc.
    ]

    # Affiche la commande dans les logs Airflow
    print("Executing command:", " ".join(cmd))

    # Exécute le script en sous-processus et capture la sortie
    result = subprocess.run(cmd, capture_output=True)
    print("result:", result)

    # Enregistre l’heure de fin
    end_time = datetime.now()

    # Envoie l'heure de début et la durée d'exécution dans les XComs (pour analyse ou logs Airflow)
    kwargs["ti"].xcom_push(key="start_time", value=start_time.isoformat())
    kwargs["ti"].xcom_push(key="extract_time", value=(end_time - start_time).total_seconds())

    # Vérifie si l’exécution s’est bien passée (code de retour 0)
    if result.returncode == 0:
        status = "success"
    else:
        status = "failed"
        print("❌ Script failed:")
        print("STDOUT:", result.stdout)  # Affiche ce que le script a retourné
        print("STDERR:", result.stderr)  # Affiche les erreurs éventuelles

    # Envoie le statut (succès/échec) dans XCom pour d’autres tâches éventuelles
    kwargs["ti"].xcom_push(key="status", value=status)


    results["running"] = False  # arrêter la surveillance
    monitor_thread.join()

    # Résultats
    print("\n✅ Monitoring terminé extract_data.")
    print(f"pourcentage max CPU du processus : {results['cpu_percent_process']:.2f}%")
    print(f"pourcentage max CPU du système : {results['cpu_percent_system']:.2f}%")
    print(f"mémoire max du processus : {results ['mem_max_process']:.2f} MB")
    print(f"mémoire max du système : {results['mem_max_system']:.2f} MB")

    kwargs["ti"].xcom_push(key="pourcent_cpu_process", value=results['cpu_percent_process'])
    kwargs["ti"].xcom_push(key="pourcent_cpu_system", value=results['cpu_percent_system'])
    kwargs["ti"].xcom_push(key="mem_max_process", value=results['mem_max_process'])
    kwargs["ti"].xcom_push(key="mem_max_system", value=results['mem_max_system'])


def preprocess_single(tweet):
    """
    Pré-traite un tweet individuel pour enrichir les informations temporelles et préparer la structure.

    Args:
        tweet (dict): Un dictionnaire représentant un tweet brut avec ses attributs.

    Returns:
        dict: Un dictionnaire enrichi contenant les mêmes champs que le tweet original, 
              plus des champs dérivés de la date (année, mois, jour, heure, minute, seconde),
              et un champ `date_tweet_cleaned` au format datetime string.
    """
    # Conversion de la date en objet datetime pandas pour faciliter les extractions
    date_datetime = pd.to_datetime(tweet['date_tweet'], format='%Y-%m-%dT%H:%M:%S.%fZ')

    # Renvoi d’un nouveau dictionnaire enrichi
    return {
        "text_tweet": tweet['text_tweet'],
        "cleaned_text_tweet": "",  # vide ici, à remplir après nettoyage
        "nombre_likes": tweet['nombre_likes'],
        "nombre_reposts": tweet['nombre_reposts'],
        "nombre_replies": tweet['nombre_replies'],
        "nombre_views": tweet['nombre_views'],
        "date_tweet": tweet['date_tweet'],
        "identifiant": tweet['identifiant'],
        "req_id": tweet['req_id'],
        "mot_cle": tweet['mot_cle'],
        "bool_analyse": tweet['bool_analyse'],
        "emotion": tweet['emotion'],
        "date_tweet_cleaned": str(date_datetime),  # date sous forme string
        'year': int(date_datetime.year),           # extraction de l'année
        'month': int(date_datetime.month),         # extraction du mois
        'day': int(date_datetime.day),             # extraction du jour
        'hour': int(date_datetime.hour),           # extraction de l'heure
        'minute': int(date_datetime.minute),       # extraction des minutes
        'second': int(date_datetime.second),       # extraction des secondes
    }

def transform_data(**kwargs):
    
    """
    Fonction Airflow pour transformer les données brutes extraites.

    Args:
        **kwargs: Paramètres de contexte passés automatiquement par Airflow.

    Returns:
        list: Liste des tweets transformés (pré-traités) ou liste vide si aucun tweet.

    Fonctionnalités :
    - Charge les tweets JSON bruts extraits.
    - Applique la fonction `preprocess_single` à chaque tweet.
    - Surveille en parallèle l'utilisation CPU et mémoire pendant la transformation.
    - Envoie des métriques (nombre de tweets, durée, consommation CPU/mémoire) dans XCom.
    - Affiche les statistiques de monitoring à la fin.
    """
     
    start_transform = datetime.now()  # heure de début
    pid = os.getpid()
    print("🔍 Starting monitoring transform data ...")

    # Démarrage du monitoring CPU/mémoire dans un thread séparé
    results = {"running": True}
    monitor_thread = Thread(target=monitoring, args=(pid, results))
    monitor_thread.start()

    # Chargement des tweets bruts depuis un fichier JSON
    raw_path = os.path.join(EXTRACTION_DIR, "tweets_raw.json")
    with open(raw_path, "r", encoding="utf-8") as f:
        tweets = json.load(f)

    if tweets:
        # Pré-traitement de chaque tweet
        cleaned = [preprocess_single(t) for t in tweets]
        # Push dans XCom le nombre de tweets traités
        kwargs["ti"].xcom_push(key="n_records", value=len(cleaned))
        # Push dans XCom la durée totale de transformation
        kwargs["ti"].xcom_push(key="transform_time", value=(datetime.now() - start_transform).total_seconds())
        # Arrêt du monitoring
        results["running"] = False
        monitor_thread.join()

        # Affichage des résultats de monitoring
        # Résultats
        print("\n✅ Monitoring terminé extract_data.")
        print(f"pourcentage max CPU du processus : {results['cpu_percent_process']:.2f}%")
        print(f"pourcentage max CPU du système : {results['cpu_percent_system']:.2f}%")
        print(f"mémoire max du processus : {results ['mem_max_process']:.2f} MB")
        print(f"mémoire max du système : {results['mem_max_system']:.2f} MB")
        kwargs["ti"].xcom_push(key="pourcent_cpu_process", value=results['cpu_percent_process'])
        kwargs["ti"].xcom_push(key="pourcent_cpu_system", value=results['cpu_percent_system'])
        kwargs["ti"].xcom_push(key="mem_max_process", value=results['mem_max_process'])
        kwargs["ti"].xcom_push(key="mem_max_system", value=results['mem_max_system'])
        return cleaned
    else:
        print("Aucun tweet à traiter.")
        kwargs["ti"].xcom_push(key="n_records", value=0)
        kwargs["ti"].xcom_push(key="transform_time", value=(datetime.now() - start_transform).total_seconds())
        results["running"] = False  # arrêter la surveillance
        monitor_thread.join()

        # Résultats
        print("\n✅ Monitoring terminé transform data.")
        print(f"pourcentage max CPU du processus : {results['cpu_percent_process']:.2f}%")
        print(f"pourcentage max CPU du système : {results['cpu_percent_system']:.2f}%")
        print(f"mémoire max du processus : {results ['mem_max_process']:.2f} MB")
        print(f"mémoire max du système : {results['mem_max_system']:.2f} MB")
        kwargs["ti"].xcom_push(key="pourcent_cpu_process", value=results['cpu_percent_process'])
        kwargs["ti"].xcom_push(key="pourcent_cpu_system", value=results['cpu_percent_system'])
        kwargs["ti"].xcom_push(key="mem_max_process", value=results['mem_max_process'])
        kwargs["ti"].xcom_push(key="mem_max_system", value=results['mem_max_system'])
        return []

def insert_into_mongo(**kwargs):
    """
    Insère les données nettoyées dans la base MongoDB et enregistre la requête.

    Fonction utilisée dans un contexte Airflow, qui récupère les données transformées 
    via XCom, convertit les dates, puis insère les tweets et la requête dans la base MongoDB.
    Parallèlement, un monitoring de consommation CPU/mémoire est lancé.

    Args:
        **kwargs: Paramètres de contexte Airflow contenant notamment 'ti' pour accéder aux XCom.

    Fonctionnalités :
    - Démarre un thread pour monitorer l’usage CPU/mémoire du processus.
    - Récupère les données nettoyées de la tâche précédente ('transform_data') via XCom.
    - Convertit la date de chaque tweet en datetime (format pandas).
    - Connexion à MongoDB via un hook Airflow.
    - Insère les données dans la collection 'tweets'.
    - Insère les informations de la requête dans la collection 'requests'.
    - Arrête le monitoring à la fin.
    """

    start_insert = datetime.now()  # Temps de début de l'insertion

    pid = os.getpid()  # ID du processus actuel
    print("🔍 Starting monitoring insert data ...")

    # Démarrer un thread de monitoring CPU/mémoire en parallèle
    results = {"running": True}
    monitor_thread = Thread(target=monitoring, args=(pid, results))
    monitor_thread.start()

    # Récupérer le contexte Airflow pour accéder aux données via XCom
    ti = kwargs['ti']
    cleaned_data = ti.xcom_pull(task_ids='transform_data')  # Données transformées
    hook = MongoHook(mongo_conn_id='mongo_id_audensiel')
    db = hook.get_conn().Recolte  # Accès à la base Recolte
    if not cleaned_data:
        print("Aucune donnée à insérer dans MongoDB.")
    else : 
    # Conversion des dates des tweets en objets datetime pandas
        for tweet in cleaned_data:
            tweet['date_tweet_cleaned'] = pd.to_datetime(tweet['date_tweet'], format='%Y-%m-%dT%H:%M:%S.%fZ')
        db.tweets.insert_many(cleaned_data)
    
    # Chargement des informations de requête depuis un fichier JSON
    req_path = os.path.join(EXTRACTION_DIR, "req.json")
    with open(req_path, "r", encoding="utf-8") as f:
        req_data = json.load(f)

    # Insertion de la requête dans la collection 'requests'
    db.requests.insert_one(req_data)

    # Chargement des informations de requête depuis un fichier JSON
    req_path = os.path.join(EXTRACTION_DIR, "req.json")
    with open(req_path, "r", encoding="utf-8") as f:
        req_data = json.load(f)

    # Insertion de la requête dans la collection 'requests'
    db.requests.insert_one(req_data)

    end_time = datetime.now()  # Temps de fin de l'insertion

    # Arrêter le monitoring CPU/mémoire
    results["running"] = False
    monitor_thread.join()

    print("\n✅ Monitoring terminé insert data.")
    print(f"pourcentage max CPU du processus : {results['cpu_percent_process']:.2f}%")
    print(f"pourcentage max CPU du système : {results['cpu_percent_system']:.2f}%")
    print(f"mémoire max du processus : {results ['mem_max_process']:.2f} MB")
    print(f"mémoire max du système : {results['mem_max_system']:.2f} MB")
    
    start_time_str = ti.xcom_pull(task_ids="extract_data", key="start_time")
    start_time = datetime.fromisoformat(start_time_str)
    
    latency_s = (end_time - start_time).total_seconds()
    duration_s = (end_time - start_insert).total_seconds()
    n_records = ti.xcom_pull(task_ids="transform_data", key="n_records")
    throughput = n_records / latency_s if latency_s > 0 else 0
    extract_s = ti.xcom_pull(task_ids="extract_data", key="extract_time")
    transform_s = ti.xcom_pull(task_ids="transform_data", key="transform_time")

    #memoire et cpu
    #extract
    extract_cpu_process = ti.xcom_pull(task_ids="initialize", key="pourcent_cpu_process")
    extract_cpu_system = ti.xcom_pull(task_ids="initialize", key="pourcent_cpu_system")
    extract_mem_process = ti.xcom_pull(task_ids="initialize", key="mem_max_process")
    extract_mem_system = ti.xcom_pull(task_ids="initialize", key="mem_max_system")

    transform_cpu_process = ti.xcom_pull(task_ids="transform_data", key="pourcent_cpu_process")
    transform_cpu_system = ti.xcom_pull(task_ids="transform_data", key="pourcent_cpu_system")
    transform_mem_process = ti.xcom_pull(task_ids="transform_data", key="mem_max_process")
    transform_mem_system = ti.xcom_pull(task_ids="transform_data", key="mem_max_system")

    insert_cpu_process = results['cpu_percent_process']
    insert_cpu_system = results['cpu_percent_system']
    insert_mem_process = results['mem_max_process']
    insert_mem_system = results['mem_max_system']

    pipeline_cpu_process_max = max(extract_cpu_process, transform_cpu_process, insert_cpu_process)
    pipeline_cpu_system_max = max(extract_cpu_system, transform_cpu_system, insert_cpu_system)
    pipeline_mem_process_max = max(extract_mem_process, transform_mem_process, insert_mem_process)
    pipeline_mem_system_max = max(extract_mem_system, transform_mem_system, insert_mem_system)

    metrics = {
        "n_records": n_records,
        "latency_s": latency_s,
        "throughput_rps": throughput,
        "insert_time_s": duration_s,
        "transform_time_s" : transform_s,
        "extract_time_s" : extract_s,
        "cpu_percent_process": pipeline_cpu_process_max,
        "cpu_percent_system": pipeline_cpu_system_max,
        "mem_max_process": pipeline_mem_process_max,
        "mem_max_system": pipeline_mem_system_max,
    }
    

    append_metrics_to_csv(metrics)
    ti.xcom_push(key="status", value="success")


def compute_failure_rate(**kwargs):
    ti = kwargs['ti']
    statuses = [
        ti.xcom_pull(task_ids="extract_data", key="status"),
        ti.xcom_pull(task_ids="transform_data", key="status"),
        ti.xcom_pull(task_ids="insert_mongo", key="status")
    ]
    failure_rate = statuses.count("fail") / len(statuses)
    print(f"[FAILURE RATE] : {failure_rate*100:.2f}%")


# Définition du DAG quotidien pour le pipeline ETL Twitter
with DAG(
    dag_id="twitter_etl_init_dag",               # Identifiant unique du DAG
    default_args=default_args,                     # Arguments par défaut (retries, owner, etc.)
    start_date=datetime(2025, 5, 26, 8, 0),       # Date et heure de démarrage du DAG
    schedule_interval=None,               # Planification : tous les jours à 10h30
    catchup=False,                                 # Pas d’exécution rétroactive des dates manquées
    tags=["manuel"]                               # Tag pour catégoriser ce DAG dans l’interface Airflow
) as daily_dag:

    # Tâche d’extraction des données Twitter
    initialize = PythonOperator(
        task_id="extract_data",
        python_callable=initialize_data,
        provide_context=True  # Permet de passer le contexte Airflow à la fonction
    )
    # Tâche de transformation des données extraites
    transform = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data
    )

    # Tâche d’insertion des données transformées dans MongoDB
    insert = PythonOperator(
        task_id="insert_mongo",
        python_callable=insert_into_mongo
    )

    # Tâche pour calculer le taux d’échec (monitoring ou alerting)
    failure = PythonOperator(
        task_id="compute_failure",
        python_callable=compute_failure_rate
    )

    # Ordonnancement des tâches : initialisation → transformation → insertion → calcul des échecs
    initialize >> transform >> insert >> failure
