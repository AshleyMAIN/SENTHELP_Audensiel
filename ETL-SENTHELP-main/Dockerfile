FROM quay.io/astronomer/astro-runtime:12.6.0

USER root

# Installer Playwright et ses dépendances système
RUN python -m pip install --no-cache-dir playwright && \
    playwright install-deps && \
    playwright install


USER astro

# Lancer Airflow + ton script au démarrage

RUN pip install apache-airflow-providers-mongo
RUN pip install 'apache-airflow[statsd]'
RUN python -m playwright install
# Installer SpaCy et le modèle français
RUN python -m spacy download fr_core_news_sm


