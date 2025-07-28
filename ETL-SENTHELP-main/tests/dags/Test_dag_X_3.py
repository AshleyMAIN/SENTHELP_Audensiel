from airflow import DAG
from airflow.decorators import task
from airflow.providers.mongo.hooks.mongo import MongoHook
from datetime import datetime, timedelta
import subprocess
import os
import json
import psutil
import csv
from scripts.preprocessing import traitement_date
from airflow.utils.dates import days_ago

SCRIPT_MODULE = "scripts.Nouvelalgo"
CORPUS_PATH = "scripts/corpus1.json"
EXTRACTION_DIR = "/usr/local/airflow/"
METRICS_CSV = "/usr/local/airflow/metrics.csv"

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def log_resources(tag="default"):
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    print(f"[{tag}] CPU: {cpu}% | RAM: {mem}%")

def append_metrics_to_csv(metrics, path=METRICS_CSV):
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=metrics.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(metrics)

with DAG(
    dag_id="twitter_etl_daily_dag_X_3",
    default_args=default_args,
    start_date=datetime(2025, 5, 26, 8, 0),
    schedule_interval=timedelta(days=7),
    catchup=False,
    tags=["weekly"],
) as dag:

    @task
    def initialize_data():
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

    @task
    def extract_data():
        log_resources("before_extract")
        start_time = datetime.now()

        today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)
        cmd = [
            "python", "-m", SCRIPT_MODULE,
            CORPUS_PATH, "08:00", today.strftime("%Y-%m-%d"),
            "08:00", week_ago.strftime("%Y-%m-%d"),
            "bs4", "0", "--finrecolte"
        ]
        subprocess.run(cmd, capture_output=True)
        log_resources("after_extract")
        return {
            "start_time": start_time.isoformat(),
            "extract_time": (datetime.now() - start_time).total_seconds(),
            "status": "success",
        }

    def preprocess_single(tweet):
        date_datetime = traitement_date(tweet['date_tweet'])
        return {
            "text_tweet": tweet['text_tweet'],
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
            "date_tweet_cleaned": date_datetime,
            'year': int(date_datetime.year),
            'month': int(date_datetime.month),
            'day': int(date_datetime.day),
            'hour': int(date_datetime.hour),
            'minute': int(date_datetime.minute),
            'second': int(date_datetime.second),
        }

    @task
    def transform_data():
        log_resources("before_transform")
        start_transform = datetime.now()

        raw_path = os.path.join(EXTRACTION_DIR, "tweets_raw.json")
        with open(raw_path, "r", encoding="utf-8") as f:
            tweets = json.load(f)

        if tweets:
            cleaned = [preprocess_single(t) for t in tweets]
            log_resources("after_transform")
            return {
                "cleaned_data": cleaned,
                "n_records": len(cleaned),
                "transform_time": (datetime.now() - start_transform).total_seconds(),
                "status": "success",
            }
        else:
            print("Aucun tweet à traiter.")
            return {
                "cleaned_data": [],
                "n_records": 0,
                "transform_time": (datetime.now() - start_transform).total_seconds(),
                "status": "success",
            }

    @task
    def insert_into_mongo(transform_result: dict, extract_result: dict):
        log_resources("before_insert")
        start_insert = datetime.now()

        cleaned_data = transform_result["cleaned_data"]

        hook = MongoHook(mongo_conn_id='mongoid')
        db = hook.get_conn().Tweets
        db.tweets.insert_many(cleaned_data)

        req_path = os.path.join(EXTRACTION_DIR, "req.json")
        with open(req_path, "r", encoding="utf-8") as f:
            req_data = json.load(f)
        db.requests.insert_one(req_data)

        end_time = datetime.now()
        start_time = datetime.fromisoformat(extract_result["start_time"])

        latency_s = (end_time - start_time).total_seconds()
        duration_s = (end_time - start_insert).total_seconds()
        n_records = transform_result["n_records"]
        throughput = n_records / latency_s if latency_s > 0 else 0
        extract_s = extract_result["extract_time"]
        transform_s = transform_result["transform_time"]

        print(f"[LATENCY] Total: {latency_s:.2f}s")
        print(f"[THROUGHPUT] {throughput:.2f} records/sec")
        print(f"[INSERT TIME] {duration_s:.2f}s")

        metrics = {
            "n_records": n_records,
            "latency_s": latency_s,
            "throughput_rps": throughput,
            "insert_time_s": duration_s,
            "transform_time_s": transform_s,
            "extract_time_s": extract_s,
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent
        }

        append_metrics_to_csv(metrics)
        log_resources("after_insert")

        return {"status": "success"}

    @task
    def compute_failure_rate(extract_result: dict, transform_result: dict, insert_result: dict):
        statuses = [
            extract_result.get("status"),
            transform_result.get("status"),
            insert_result.get("status"),
        ]
        failure_rate = statuses.count("fail") / len(statuses)
        print(f"[FAILURE RATE] : {failure_rate*100:.2f}%")

    # Orchestration
    init = initialize_data()
    extract = extract_data()
    transform = transform_data()
    insert = insert_into_mongo(transform, extract)
    failure = compute_failure_rate(extract, transform, insert)

    init >> extract >> transform >> insert >> failure
