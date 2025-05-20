FROM python:3.12-slim

# Ajoute curl pour le healthcheck Docker
RUN apt-get update && apt-get install -y curl

WORKDIR /app

# Copier le fichier requirements.txt pour profiter du cache Docker
COPY requirements.txt .

# Installer les dépendances
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source de l’API
COPY . .

# Définir la commande de démarrage de l’API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
