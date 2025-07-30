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
- `Nouvelalgo.py` : 
Ce script est conçu pour être exécuté en sous-processus et permet de récolter des tweets sur une période donnée, selon des mots-clés définis et une méthode de scraping sélectionnée.

---

### Fonctionnement général

Le script fonctionne à partir d'une série d'arguments fournis en ligne de commande. Il permet :

* De spécifier une période de collecte (date et heure de début et de fin),
* D'indiquer la méthode de scraping à utiliser,
* De définir un nombre de tweets à récolter,
* Et d’opter pour une collecte continue jusqu’à la fin de la période définie.

---

### Arguments en entrée

* **`fichier`** : chemin vers un fichier JSON contenant les mots-clés à utiliser pour les recherches.
* **`heure`** et **`heurefin`** : heure de début et de fin de la collecte (au format HH\:MM).
* **`datedebut`** et **`datefin`** : date de début et de fin de la collecte (au format YYYY-MM-DD).
* **`methode`** : méthode de scraping choisie (`bs4`, `autoscraper`, etc.).
* **`nombre_tweets`** : nombre de tweets à récupérer (mettre `0` pour une collecte illimitée).
* **`--finrecolte`** *(optionnel)* : si activé, permet de continuer la collecte jusqu’à la fin de la période spécifiée.

---

### Déroulé du script

1. **Préparation des paramètres** :

   * Conversion des dates en timestamps.
   * Chargement des mots-clés depuis le fichier JSON.

2. **Lancement de la collecte** :

   * La fonction `main()` est appelée avec les paramètres fournis.
   * La collecte s'effectue via la fonction `recolte()` de manière asynchrone.

3. **Sauvegardes** :

   * Les tweets collectés sont enregistrés dans un fichier `tweets_raw.json`.
   * Les métadonnées de la requête (par exemple, `req_id`) sont sauvegardées dans `req.json`.

---

### `recolte()`

* Déclenche la méthode de scraping sélectionnée :

  * Utilise **Playwright** pour automatiser la navigation sur Twitter.
  * Si la méthode choisie est différente de `bs4`, les scrapers **AutoScraper** sont initialisés.
  * Utilise la fonction `login()` pour se connecter à Twitter.

* Pour chaque dictionnaire de mots combinés dans le corpus :
  * Génère la combinaison des mots-clés .
  * Affiche la page de recherche associé pour chaque combinaison.
  * Collecte les tweets à l’aide de la méthode choisie (`scraping_bs4()` ou `scraping_autoscraper()`).
  * Met à jour la liste des tweets récoltes, des identifiantes de tweets et les différents compteurs

* Conditions d'arrêt de la collecte pour chaque mot-clé :

  1. La fin de la période définie est atteinte.
  2. Le nombre de tweets souhaité a été collecté (si `--finrecolte` n’est pas activé).
  3. Plus aucun nouveau tweet n’est trouvé malgré le scroll de la page.

* **Défilement (scroll)** : effectué via `perform_scroll()` pour afficher de nouveaux tweets.

* En cas d’échec de la connexion à Twitter :

  * Jusqu’à **15 tentatives de reconnexion** sont effectuées.
  * Si l’échec persiste, la collecte est interrompue.

* Les sorties :
current_tweet_amount : nombre total de tweets récoltés jusqu’à présent.
scroll_count : nombre de scrolls effectués lors de la session.
termine : booléen indiquant si la collecte est terminée.
last_timestemp : timestamp du dernier tweet récolté, utile pour la continuité de la collecte.
lastdate : date du dernier tweet vu, au format lisible.
liste_tweets : liste des objets Tweet représentant les tweets collectés durant la session

---

### `login()`

Fonction dédiée à l’automatisation de la connexion à Twitter.

* Remplit automatiquement les champs d’identifiant, d’e-mail (si nécessaire) et de mot de passe.
* Valide le formulaire de connexion.
* Retourne `True` si la connexion est réussie, sinon `False`.

---

### `scraping_bs4()` et `scraping_autoscraper()`

Fonctions d’extraction des tweets pertinents selon les mots-clés.

* Extraient le texte et l’identifiant du tweet.
* Vérifient la présence des mots-clés dans le texte à l’aide de la fonction `contient_mots_espaces()`.
* S’assurent que le tweet n’a pas encore été récolté.
* Extraient la date et vérifient qu’elle appartient bien à la période de collecte.
* Si les conditions sont réunies, extraient les autres champs d’intérêt (likes, etc.).
* Créent un objet `Tweet` à partir des éléments récoltés ( avec la classe  `DonneeCollectee()` ).
* Rajoute l'objet à la liste des tweets.
* Retourne :
  * Les compteurs mis à jour (par mot-clé),
  * La liste des tweets récoltés,
  * La liste des identifiants des tweets associés,
  * Le dernier timestamp et la dernière date vue, pour permettre la reprise de la collecte ultérieurement.

---

### `perform_scroll()`

Fonction de défilement de la page pour charger de nouveaux tweets.

* Détecte et clique sur un éventuel bouton **"Retry"** pour relancer le chargement.
* Compare les nouveaux éléments chargés avec les tweets déjà récoltés.
* Retourne :

  * `True` si de nouveaux tweets ont été chargés,
  * `False` sinon, ce qui peut signaler une condition d’arrêt de la collecte.

---

* Une fois la collecte terminée, le script retourne un booléen `finderecolte`qui signale si la récolte s'est bien effectuée.

---

### Fichiers générés

* `tweets_raw.json` : contient les tweets bruts collectés.
* `req.json` : contient les métadonnées associées à la requête.


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

### 1. Lancement en une seule fois des trois services : 
Un script `start.sh` permet de démarrer automatiquement les trois services (ETL, inférence, dashboard) en parallèle :

```bash
start.sh
```
Ne pas oublier de mettre à jour les chemins dans les fichiers : "start.sh" et "docker-compose.override.yml" 
### 2. Lancement manuel (dans trois terminaux séparés)

Vous pouvez aussi lancer chaque service **séparément**, dans des terminaux différents :

#### Terminal 1 — Pipeline ETL (Airflow via Astronomer)

```bash
cd /SENTHELP/ETL-SENTHELP-main
astro dev start
```

#### Terminal 2 — Inférence continue

```bash
cd /SENTHELP/Inference-SENTHELP-main
docker compose up
```

#### Terminal 3 — Dashboard (FastAPI + React)

```bash
cd /SENTHELP/Serving-SENTHELP-main
docker compose up
```

---



