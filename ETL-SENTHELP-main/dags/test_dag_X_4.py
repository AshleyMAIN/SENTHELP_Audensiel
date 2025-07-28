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

def extract_data(**kwargs):
    start_time = datetime.now()

    pid = os.getpid()
    print("🔍 Starting monitoring extract_data ...")

    # Démarrage du monitoring en parallèle
    results = {"running": True}
    monitor_thread = Thread(target=monitoring, args=(pid, results))
    monitor_thread.start()

    today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    cmd = [
        "python", "-m", SCRIPT_MODULE,
        CORPUS_PATH, "10:30", today.strftime("%Y-%m-%d"),
        "10:30", week_ago.strftime("%Y-%m-%d"),
        "bs4", "0", "--finrecolte"
    ]
    result = subprocess.run(cmd, capture_output=True)
    print("result:", result)
    end_time = datetime.now()
    kwargs["ti"].xcom_push(key="start_time", value=start_time.isoformat())
    kwargs["ti"].xcom_push(key="extract_time", value=(end_time - start_time).total_seconds())

    if result.returncode == 0:
        status = "success"
    else:
        status = "failed"
        print("❌ Script failed:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    # Push dans XCom
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
    date_datetime = pd.to_datetime(tweet['date_tweet'], format='%Y-%m-%dT%H:%M:%S.%fZ')
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
        "date_tweet_cleaned": str(date_datetime),
        'year': int(date_datetime.year),
        'month': int(date_datetime.month),
        'day': int(date_datetime.day),
        'hour': int(date_datetime.hour),
        'minute': int(date_datetime.minute),
        'second': int(date_datetime.second),
    }

def transform_data(**kwargs):

    start_transform = datetime.now()
    pid = os.getpid()
    print("🔍 Starting monitoring transform data ...")

    # Démarrage du monitoring en parallèle
    results = {"running": True}
    monitor_thread = Thread(target=monitoring, args=(pid, results))
    monitor_thread.start()

    raw_path = os.path.join(EXTRACTION_DIR, "tweets_raw.json")
    with open(raw_path, "r", encoding="utf-8") as f:
        tweets = json.load(f)

    if tweets:
        cleaned = [preprocess_single(t) for t in tweets]
        kwargs["ti"].xcom_push(key="n_records", value=len(cleaned))
        kwargs["ti"].xcom_push(key="transform_time", value=(datetime.now() - start_transform).total_seconds())
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
    
    start_insert = datetime.now()

    pid = os.getpid()
    print("🔍 Starting monitoring insert data ...")

    # Démarrage du monitoring en parallèle
    results = {"running": True}
    monitor_thread = Thread(target=monitoring, args=(pid, results))
    monitor_thread.start()


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

    req_path = os.path.join(EXTRACTION_DIR, "req.json")
    with open(req_path, "r", encoding="utf-8") as f:
        req_data = json.load(f)
    db.requests.insert_one(req_data)

    end_time = datetime.now()

    results["running"] = False  # arrêter la surveillance
    monitor_thread.join()

    # Résultats
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
    extract_cpu_process = ti.xcom_pull(task_ids="extract_data", key="pourcent_cpu_process")
    extract_cpu_system = ti.xcom_pull(task_ids="extract_data", key="pourcent_cpu_system")
    extract_mem_process = ti.xcom_pull(task_ids="extract_data", key="mem_max_process")
    extract_mem_system = ti.xcom_pull(task_ids="extract_data", key="mem_max_system")

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



# DAG QUOTIDIEN
with DAG(
    dag_id="twitter_etl_weekly_dag",
    default_args=default_args,
    start_date=datetime(2025, 5, 26, 8, 0),
    schedule_interval=timedelta(days=7),
    catchup=False,
    tags=["weekly"],
) as daily_dag:
    extract = PythonOperator(task_id="extract_data", python_callable=extract_data)
    transform = PythonOperator(task_id="transform_data", python_callable=transform_data)
    insert = PythonOperator(task_id="insert_mongo", python_callable=insert_into_mongo)
    failure = PythonOperator(task_id="compute_failure", python_callable=compute_failure_rate)

    extract >> transform >> insert >> failure
