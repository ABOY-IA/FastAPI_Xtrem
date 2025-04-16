FROM python:3.12-slim

# Mettre à jour pip et définir le répertoire de travail
WORKDIR /app
RUN pip install --upgrade pip

# Copier le fichier de dépendances et installer les librairies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'intégralité du projet dans le conteneur
COPY . .

# Exposer le port 8000 (pour l'API)
EXPOSE 8000

# Commande par défaut (elle peut être surchargée par docker-compose)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]