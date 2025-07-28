# Étape 1 : build de l'app React
FROM node:18 as build

WORKDIR /app

COPY package*.json ./
RUN npm install --legacy-peer-deps

COPY . .

# Définir NODE_OPTIONS pour tous les processus du conteneur
ENV NODE_OPTIONS=--openssl-legacy-provider

EXPOSE 3001

CMD ["npm", "start"]


