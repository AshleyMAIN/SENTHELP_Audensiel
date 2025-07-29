#!/bin/bash

# Lancer Docker Compose 1
(cd C:/Users/Amayas/Downloads/SENTHELP/Inference-SENTHELP-main && docker compose up) &

# Lancer Docker Compose 2
(cd C:/Users/Amayas/Downloads/SENTHELP/Serving-SENTHELP-main && docker compose up) &

# Lancer Astro dans un sous-processus

(cd C:/Users/Amayas/Downloads/SENTHELP/ETL-SENTHELP-main && astro dev start) &
# Attendre que les processus enfants terminent (optionnel)
wait
