FROM python:3.12-slim

WORKDIR /app

# Installer les dépendances de tests
COPY tests/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source de l’API et les tests
COPY api /app/api
COPY tests /app/tests

# S’assurer que /app est dans PYTHONPATH pour l'import des modules
ENV PYTHONPATH=/app

# Lancer pytest depuis /app
WORKDIR /app
ENTRYPOINT ["pytest", "-v", "--maxfail=1", "--disable-warnings", "tests"]
CMD []
