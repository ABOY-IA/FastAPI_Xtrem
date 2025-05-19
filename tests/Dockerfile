FROM python:3.12-slim

WORKDIR /app

# 1) Installer les dépendances de tests
COPY tests/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Copier le code de l’API et les tests
COPY api /app/api
COPY tests /app/tests

# 3) S’assurer que /app est dans PYTHONPATH
ENV PYTHONPATH=/app

# 4) Lancer pytest depuis /app
WORKDIR /app
ENTRYPOINT ["pytest", "-v", "--maxfail=1", "--disable-warnings", "tests"]
CMD []
