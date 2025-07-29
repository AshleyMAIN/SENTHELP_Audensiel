#!/bin/bash

#!/bin/bash

# Lancer le Docker Compose pour l'inférence
(
  cd "C:/Users/Amayas/Downloads/SENTHELP/Inference-SENTHELP-main" || exit 1
  docker compose up
) &

# Lancer le Docker Compose pour le serving
(
  cd "C:/Users/Amayas/Downloads/SENTHELP/Serving-SENTHELP-main" || exit 1
  docker compose up
) &

# Lancer Astro + configuration réseau
(
  cd "C:/Users/Amayas/Downloads/SENTHELP/ETL-SENTHELP-main" || exit 1

  echo "🚀 Démarrage d'Astro..."
  astro dev start

  # Attendre un peu pour s'assurer que les conteneurs sont bien démarrés
  sleep 10

  echo "🔍 Recherche du réseau Airflow..."
  NETWORK_NAME=$(docker network ls --format '{{.Name}}' | grep '_airflow_network')

  if [ -z "$NETWORK_NAME" ]; then
    echo "❌ Réseau Astro non trouvé. Vérifie que les services sont bien démarrés."
    exit 1
  fi

  echo "🔗 Connexion des services Astro au réseau $NETWORK_NAME"
  for SERVICE in webserver scheduler triggerer; do
    CONTAINER_NAME=$(docker ps --format '{{.Names}}' | grep "$SERVICE")
    if [ -n "$CONTAINER_NAME" ]; then
      echo "✅ Connexion de $CONTAINER_NAME"
      docker network connect "$NETWORK_NAME" "$CONTAINER_NAME" 2>/dev/null
    else
      echo "⚠️ Conteneur $SERVICE introuvable."
    fi
  done

  echo "🔄 Redémarrage des services Astro..."
  astro dev restart
) &

# Optionnel : attendre que tous les sous-processus se terminent
wait
