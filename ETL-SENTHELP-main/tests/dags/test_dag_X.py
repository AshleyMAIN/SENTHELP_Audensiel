from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime, timedelta
import subprocess
import os
from pymongo import MongoClient
import json
from scripts.preprocessing import preprocess_single
from airflow.models import Variable

# Config
SCRIPT_MODULE = "scripts.Nouvelalgo"
CORPUS_PATH = "scripts/mots.json"
EXTRACTION_DIR = "/usr/local/airflow/"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


### ----- FONCTIONS PARTAGÉES -----
def initialize_data():
    if Variable.get("twitter_init_done", default_var="false") == "true":
        print("Initialisation déjà effectuée.")
        return
    date_fin = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    date_debut = "2025-05-26"
    n = 0
    cmd = [
        "python", "-m", SCRIPT_MODULE,
        CORPUS_PATH, "08:00", date_fin.strftime("%Y-%m-%d"),
        "08:00", date_debut,
        "bs4", f"{n}", "--finrecolte"
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    Variable.set("twitter_init_done", "true")

def extract_data():
    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    cmd = [
        "python", "-m", SCRIPT_MODULE,
        CORPUS_PATH, "08:00", today.strftime("%Y-%m-%d"),
        "08:00", yesterday.strftime("%Y-%m-%d"),
        "bs4", "0", "--finrecolte"
    ]
    subprocess.run(cmd, capture_output=True)

def transform_data():
    raw_path = os.path.join(EXTRACTION_DIR, "tweets_raw.json")
    clean_path = os.path.join(EXTRACTION_DIR, "tweets_clean.json") # peut être par mettre dan sjson
    with open(raw_path, "r", encoding="utf-8") as f:
        tweets = json.load(f)
    cleaned = [preprocess_single(t) for t in tweets]
    with open(clean_path, "w", encoding="utf-8") as f:
        for t in cleaned:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

def insert_into_mongo():
    hook = MongoHook(mongo_conn_id='mongoid')
    db = hook.get_conn().Tweets
    tweets_collection = db.tweets
    clean_path = os.path.join(EXTRACTION_DIR, "tweets_clean.json")
    with open(clean_path, "r", encoding="utf-8") as f:
        for line in f:
            tweet = json.loads(line)
            tweet['date_tweet_cleaned'] = datetime.strptime(tweet['date_tweet_cleaned'], "%Y-%m-%dT%H:%M:%S.%fZ")
            tweets_collection.insert_one(tweet)


### ----- DAG D’INITIALISATION (manuel) -----
with DAG(
    dag_id="twitter_etl_init_dag",
    default_args=default_args,
    start_date=datetime(2025, 5, 25),
    schedule_interval=None,
    catchup=False,
    tags=["init"],
) as init_dag:
    init = PythonOperator(task_id="initialize_data", python_callable=initialize_data)
    transform = PythonOperator(task_id="transform_data", python_callable=transform_data)
    insert = PythonOperator(task_id="insert_mongo", python_callable=insert_into_mongo)

    init >> transform >> insert


### ----- DAG QUOTIDIEN -----
with DAG(
    dag_id="twitter_etl_daily_dag",
    default_args=default_args,
    start_date=datetime(2025, 5, 26),
    schedule_interval="0 8 * * *",  # tous les jours à 8h
    catchup=False,
    tags=["daily"],
) as daily_dag:
    extract = PythonOperator(task_id="extract_data", python_callable=extract_data)
    transform = PythonOperator(task_id="transform_data", python_callable=transform_data)
    insert = PythonOperator(task_id="insert_mongo", python_callable=insert_into_mongo)

    extract >> transform >> insert

    