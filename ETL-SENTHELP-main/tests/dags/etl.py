from airflow import DAG
from airflow.decorators import task
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.dates import days_ago
import json

# Define the DAG
with DAG(
    dag_id="x_tweets_postgres",
    start_date=days_ago(1), # 1 jour avant aujourd'hui
    schedule_interval="@daily",
    catchup=False, #
) as dag:

    # Step 1: Create the table if it does not exist
    @task
    def create_table():
        """
        Create the 'tweets' table if it doesn't already exist in PostgreSQL.
        """
        postgres_hook = PostgresHook(postgres_conn_id="my_postgres_connection") #connecter Airflow à ta base de données PostgreSQL via une connexion configurée dans l’UI d’Airflow
        create_table_query = """
            CREATE TABLE IF NOT EXISTS tweets (
                tweet_id VARCHAR(50) PRIMARY KEY, -- Stores the ID of the tweet
                created_at TIMESTAMP,             -- Timestamp of when the tweet was created
                text TEXT,                        -- Text content of the tweet
                author_id VARCHAR(50),            -- ID of the author of the tweet
                username VARCHAR(50),             -- Username of the author
                includes JSON,                    -- Stores the 'includes' section as JSON
                meta JSON,                        -- Stores the 'meta' section as JSON
                errors JSON                       -- Stores the 'errors' section as JSON, if present
            );
        """
        postgres_hook.run(create_table_query)

    # Step 2: Fetch tweets using Airflow's SimpleHttpOperator
    query = "python"
    tweet_fields = "author_id,created_at,id,text"
    user_fields = "username"
    url = f"/2/tweets/search/recent?query={query}&tweet.fields={tweet_fields}&user.fields={user_fields}"

    fetch_tweets = SimpleHttpOperator( # activer connexion d'Airflow à l'API DE x et lancer des requêtes vers l'API
        task_id="fetch_tweets",
        http_conn_id="twitter_api",  # The connection ID defined in Airflow UI
        endpoint=url,
        method="GET",
        headers={"Authorization": "Bearer {{ conn.twitter_api.extra_dejson.bearer_token }}"},
        response_filter=lambda response: response.json(),  # Convert response to JSON
        log_response=True,
    )

    # Step 3: Transform the data
    @task
    def transform_tweets(response):
        """
        Transform the raw API response into a list of tweet dictionaries.
        """
        tweets = response.get("data", [])
        includes = response.get("includes", {})
        errors = response.get("errors", [])
        meta = response.get("meta", {})

        transformed_tweets = []
        for tweet in tweets:
            transformed_tweets.append({
                "tweet_id": tweet["id"],
                "created_at": tweet["created_at"],
                "text": tweet["text"],
                "author_id": tweet["author_id"],
                "username": includes.get("users", [{}])[0].get("username", None),  # Assumes one user
                "includes": json.dumps(includes),  # Store the entire includes object
                "meta": json.dumps(meta),          # Store the entire meta object
                "errors": json.dumps(errors) if errors else None,  # Store errors, if any
            })
        print(f"Transformed Tweets: {json.dumps(transformed_tweets, indent=2)}")
        return transformed_tweets

    # Step 4: Save the data into PostgreSQL
    @task
    def load_to_postgres(tweets):
        """
        Save transformed tweets to PostgreSQL database.
        """
        postgres_hook = PostgresHook(postgres_conn_id="my_postgres_connection")
        insert_query = """
            INSERT INTO tweets (tweet_id, created_at, text, author_id, username, includes, meta, errors)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (tweet_id) DO NOTHING;  -- Avoid duplicates
        """
        connection = postgres_hook.get_conn()
        cursor = connection.cursor()
        try:
            for tweet in tweets:
                cursor.execute(insert_query, (
                    tweet["tweet_id"],
                    tweet["created_at"],
                    tweet["text"],
                    tweet["author_id"],
                    tweet["username"],
                    tweet["includes"],
                    tweet["meta"],
                    tweet["errors"],
                ))
            connection.commit()
            print(f"Inserted {len(tweets)} tweets into the database.")
        except Exception as e:
            connection.rollback()
            print(f"Error inserting tweets: {e}")
        finally:
            cursor.close()

    # Step 5: Define the task dependencies
    create_table_task = create_table()  # Ensure the table is created before extraction
    api_response = fetch_tweets.output  # Fetch tweets from API
    transformed_data = transform_tweets(api_response)  # Transform the fetched data
    create_table_task >> fetch_tweets >> transformed_data >> load_to_postgres(transformed_data)
