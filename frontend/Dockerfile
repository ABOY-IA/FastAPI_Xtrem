FROM python:3.12-slim

WORKDIR /app

# Copier le fichier requirements.txt spécifique au frontend
COPY requirements.txt .

# Installer les dépendances nécessaires (Streamlit et autres)
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copier l’ensemble des fichiers du frontend
COPY . .

# Définir la commande de démarrage de Streamlit
CMD ["streamlit", "run", "app.py", "--server.enableCORS", "true"]
