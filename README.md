# 🚀 Projet SENTHELP

SENTHELP est un projet de pipeline complet pour la **récolte, l’analyse et la visualisation de tweets** en lien avec le secteur de l’assurance. Il se compose de trois grandes étapes :

1. Pipeline ETL avec Airflow  
2. Inférence continue sur les nouveaux tweets  
3. Application Web pour visualiser les résultats (backend FastAPI + frontend React)

---

## Étape 1 : Pipeline ETL avec Airflow

Dossier : `SENTHELP/ETL-SENTHELP-main`

### Outils utilisés

- **Apache Airflow** : orchestration de la pipeline ETL (extraction, transformation, chargement).
- **MongoDB** : base de données NoSQL pour stocker les tweets nettoyés.
- **Grafana** et **Prometheus**: Pour le monitoring de la pipeline


### Fonctionnement de la pipeline

La pipeline ETL orchestrée par Airflow suit trois étapes principales :

1. **Extraction (Extract)** 
   - Cette tâche est orchestrée avec le `PythonOperator` dans Airflow.
   - Utilise la fonction extract_data/initialised_data pour extraire les tweets correspondant à une période donnée.

2. **Transformation (Transform)**  
   - Utilisation également du `PythonOperator`.
   - Utilise la fonction transform_data pour extraire les tweets correspondant à une période donnée.

3. **Chargement (Load)**  
   - Orchestration avec le `PythonOperator`.
   - Utilise la fonction insert_mongo pour inserer des tweets dans une collection MongoDB.
   
---

### Fichiers importants

#### Dossier `dags/` – Fichiers de définition des workflows Airflow

| Fichier | Description |
|--------|-------------|
| `test_dag_X_0.py` | DAG d’initialisation pour l’extraction complète de l’historique (2006 à juin 2026). |
| `test_dag_X_2.py` | DAG d’extraction quotidienne. |
| `test_dag_X_4.py` | DAG d’extraction hebdomadaire. |

> Chaque DAG est composé de trois tâches principales, créées à partir des fonctions Python suivantes :

- **`initialize_data`** ou **`extract_data`**  
  - Exécute le script `Nouvelalgo.py` en sous-processus.
  - Permet de récupérer les tweets sur la période définie.
  - Les tweets récupérés sont sauvegardés dans un fichier `.json` temporaire.

- **`transform_data`**  
  - Charge les tweets extraits.
  - Applique un prétraitement à chaque tweet.
  - Retourne une liste de tweets transformés (stockée dans XCom).

- **`insert_mongo`**  
  - Récupère les données nettoyées depuis `XCom`.
  - Convertit les formats de date et enrichit les métadonnées.
  - Insère les documents dans la base de données MongoDB.

#### Script Python d’extraction (`/scripts`)
- `Nouvelalgo.py` : script exécuté en sous-processus. Permet de récupérer les tweets selon une période donnée.


---

## Étape 2 : Inférence Continue

Dossier : `SENTHELP/Inference-SENTHELP-main`

### Fonctionnement

- Utilisation des **MongoDB Change Streams** pour surveiller les nouvelles insertions de tweets dans la base.
- À chaque nouvel enregistrement, une tâche d’inférence (analyse de sentiment) est déclenchée automatiquement.

### ⚠️ Prérequis
MongoDB doit être configurée en **mode replica set** (obligatoire pour le fonctionnement des change streams).

---

## Étape 3 : Application de Visualisation (Serving)

Dossier : `SENTHELP/Serving-SENTHELP-main`

###  Outils
- **Backend** : FastAPI : expose des endpoints pour interroger MongoDB.
- **Frontend** : ReactJS : permet une interface utilisateur interactive pour visualiser les résultats.

---

### Backend (FastAPI)

Fichier principal :  
`Serving-SENTHELP-main/mongodb-with-fastapi/app.py`

- Fournit des routes API pour récupérer les tweets
- Connecté à la base MongoDB.

---

### Frontend (React)

Dossier : `Serving-SENTHELP-main/frontend/src/components/`

| Composant | Fonction |
|----------|----------|
| `Cards.js` | Affiche les indicateurs statiques (score, pourcentage apr sentiments, etc.). |
| `Charts.js` | Composants graphiques pour les tendances. |
| `kpiFunctions.js` | Fonctions de calcul des KPI (Key Performance Indicators). |
| `Navbar.js` | Barre de navigation avec filtres temporels. |
| `Sidebar.js` | Menu latéral pour naviguer dans l’application. |
| `Timeline.js` | Série temporelle des tweets par date. |
| `toptweets.js` | Tableau des tweets les plus interactifs (likes, retweets, réponses). |
| `wordcloud.js` | Nuage de mots basé sur les contenus des tweets. |

Autres fichiers importants :
- `App.js` : composant racine de l’application React.
- `App.css` : feuille de style globale.

---

## Lancement des composants

### Lancement en une seule fois des trois services : 
start.sh

#### Lancer les services une par une dans trois terminaux distincts :

1. Lancer le pipeline ETL (Airflow via Astronomer) : \\
(cd C:/Users/Amayas/Downloads/SENTHELP/ETL-SENTHELP-main && astro dev start)\\
\\
2. Lancer l'inférence : \\
(cd C:/Users/Amayas/Downloads/SENTHELP/Inference-SENTHELP-main && docker compose up)\\
\\
3. Lancer le dashboard : \\
(cd C:/Users/Amayas/Downloads/SENTHELP/Serving-SENTHELP-main && docker compose up) 


