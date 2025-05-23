FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances de tests
COPY tests/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip show pytest-asyncio

# Copier le code source de l’API et les tests
COPY api /app/api
COPY tests /app/tests

# Copier le script d'attente de l’API et de la base de données
COPY tests/wait_for_api.py /app/wait_for_api.py
COPY api/wait_for_db.py /app/wait_for_db.py


# S’assurer que /app est dans PYTHONPATH pour l'import des modules
ENV PYTHONPATH=/app

WORKDIR /app
# Pas d'ENTRYPOINT ici : il sera défini dans docker-compose.yml
