FROM python:3.12-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier uniquement le fichier requirements.txt pour profiter du cache de Docker
COPY requirements.txt .

# Installer les dépendances sans version fixe (elles seront compatibles avec Python 3.12)
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source de l’API
COPY . /app/api
COPY create_admin.py /app

# Définir la commande de démarrage de l’API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]