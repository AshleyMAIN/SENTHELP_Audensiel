# Utiliser une image de base avec Python
FROM python:3.9


# Copier les fichiers nécessaires dans le conteneur
COPY /Files .
COPY Files/requirements.txt .

RUN apt-get update --fix-missing
# Installation des dépendances Python
RUN pip install -r requirements.txt

# Expose port 8000 for Django app