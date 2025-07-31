#!/bin/bash

# Étape 1 : Lancer l'inférence
echo "Lancement de l'inférence..."
cd "C:/Users/abidr/OneDrive/Bureau/Audensiel/Stage Ashley SENT HELP 2025/Code source/SENTHELP_Audensiel/Inference-SENTHELP-main" || exit 1
docker compose up -d  # -d pour détacher et passer à l'étape suivante (ajouter --build si première fois ou modification de l'image) 

# Étape 2 : Lancer le serving
echo "Lancement du serving..."
cd "C:/Users/abidr/OneDrive/Bureau/Audensiel/Stage Ashley SENT HELP 2025/Code source/SENTHELP_Audensiel/Serving-SENTHELP-main" || exit 1
docker compose up -d --build #  (ajouter --build si première fois) 

# Étape 3 : Lancer Astro + configuration réseau
echo "Démarrage d'Astro..."
cd "C:/Users/abidr/OneDrive/Bureau/Audensiel/Stage Ashley SENT HELP 2025/Code source/SENTHELP_Audensiel/ETL-SENTHELP-main" || exit 1
#docker compose -f 'docker-compose.override.yml' up -d --build 'installation_service' #si première fois
astro dev start  # démarré en fond car il bloque sinon

# Attendre que tous les conteneurs Astro soient "healthy"
echo "Attente du démarrage complet des services Astro..."

# Connexion des conteneurs Astro au bon réseau
echo "Recherche du réseau Airflow..."
NETWORK_NAME=$(docker network ls --format '{{.Name}}' | grep '_airflow_network')

if [ -z "$NETWORK_NAME" ]; then
  echo "Réseau Astro non trouvé. Vérifie que les services sont bien démarrés."
  exit 1
fi

echo "Connexion des services Astro au réseau $NETWORK_NAME"
for SERVICE in webserver scheduler triggerer; do
  CONTAINER_NAME=$(docker ps --format '{{.Names}}' | grep "$SERVICE")
  if [ -n "$CONTAINER_NAME" ]; then
    echo "Connexion de $CONTAINER_NAME"
    docker network connect "$NETWORK_NAME" "$CONTAINER_NAME" 2>/dev/null
  else
    echo "Conteneur $SERVICE introuvable."
  fi
done

# Redémarrage final d'Astro pour s'assurer de la prise en compte du réseau
echo "Redémarrage des services Astro..."
astro dev restart

