FROM python:3.12-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt spécifique au frontend
COPY requirements.txt .

# Installer les dépendances (ici pour Streamlit et toute autre librairie Frontend)
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade streamlit

# Copier l’ensemble des fichiers du frontend
COPY . .

# Définir la commande de démarrage de Streamlit
CMD ["streamlit", "run", "app.py", "--server.enableCORS", "true"]
