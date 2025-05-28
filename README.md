# FastAPI_Xtrem

## 🚀 Présentation

FastAPI_Xtrem est un projet fullstack sécurisé basé sur **FastAPI**, **PostgreSQL** (SCRAM-SHA-256 + SSL/TLS), et **Streamlit**, entièrement orchestré avec Docker Compose.  
Il intègre une gestion avancée de l’authentification, des tests unitaires, une interface utilisateur et une configuration professionnelle pour le développement et la production.

---

## 🐍 Environnement Python

### Prérequis

- Python 3.11 ou plus (recommandé)
- `pip` installé (inclus avec Python)
- Terminal ou shell (Linux, macOS, Windows PowerShell, Bash, etc.)

### Création et activation de l’environnement virtuel

À la racine du projet :

```
python3 -m venv .venv
```

Activation :
- Sous Linux / macOS :
    ```
    source .venv/bin/activate
    ```
- Sous Windows (PowerShell) :
    ```
    .venv\Scripts\Activate.ps1
    ```
- Sous Windows (CMD) :
    ```
    .venv\Scripts\activate.bat
    ```

Désactivation :
```
deactivate
```

Mettre à jour pip :
```
python -m pip install --upgrade pip
```

Installer les dépendances :
```
pip install -r requirements.txt
```

Générer ou mettre à jour le requirements.txt :
```
pip freeze > requirements.txt
```

---

## ⚙️ Configuration du fichier `.env`

Le fichier `.env` doit être créé à la racine du projet.  
Il contient toutes les variables d’environnement nécessaires au fonctionnement de l’application et à la configuration de Docker Compose.

**Exemple de contenu minimal :**
```
# Clé secrète utilisée pour signer et vérifier les JWT (doit être identique partout)
SECRET_KEY=supersecretkey123

# Algorithme utilisé pour les JWT (par défaut: HS256)
ALGORITHM=HS256

# Durée de vie des tokens access/refresh (en minutes/jours)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Clé de création admin (si utilisée)
ADMIN_CREATION_SECRET=MonSecretSuperSecurise

# Connexion à la base Postgres
DATABASE_URL=postgresql://user:pass@db:5432/xtremdb

# Configuration de la base de données
DB_HOST=db
DB_PORT=5432
DB_WAIT_TIMEOUT=120
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
POSTGRES_DB=xtremdb

# URL de l'API (pour le frontend ou les tests)
API_URL=http://api:8000

# Désactive la télémétrie Streamlit
STREAMLIT_BROWSER_GATHERUSAGESTATS=false

# Compose bake (optionnel, selon ton usage)
COMPOSE_BAKE=true
```

---

## 🔒 Sécurité PostgreSQL

La base PostgreSQL est configurée pour :
- Authentification SCRAM-SHA-256
- Chiffrement SSL/TLS (certificats auto-signés par défaut)
- Connexions réseau sécurisées entre les services Docker

Les fichiers de configuration et certificats sont dans le dossier `postgres-custom/`, injectés automatiquement à l’initialisation.

---

## 🐳 Commandes Docker Compose

### Nettoyer entièrement (images, volumes, orphelins)
```
docker-compose down --rmi all --volumes --remove-orphans
```

### Build complet et lancement de la stack
```
export COMPOSE_BAKE=true
docker-compose up --build
```

### Relancer simplement (si déjà build)
```
docker-compose up
```

### Arrêter la stack (tous les services)
```
docker-compose down
```

### Lancer les tests unitaires
```
docker-compose run --rm tests
```

### Créer un compte admin
```
docker-compose run --rm api python create_admin.py
```

---

## 📁 Arborescence du projet

```
.
├── README.md
├── .env
├── .gitignore
├── .venv/
├── api/
│   ├── Dockerfile
│   ├── __init__.py
│   ├── __pycache__/
│   ├── admin/
│   │   ├── __pycache__/
│   │   └── routes.py
│   ├── auth/
│   │   ├── __pycache__/
│   │   └── routes.py
│   ├── core/
│   │   ├── __pycache__/
│   │   ├── crypto.py
│   │   ├── security.py
│   │   └── tokens.py
│   ├── create_admin.py
│   ├── db/
│   │   ├── __pycache__/
│   │   ├── base.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── session.py
│   ├── events.py
│   ├── logger.py
│   ├── main.py
│   ├── requirements.txt
│   ├── users/
│   │   ├── __pycache__/
│   │   └── routes.py
│   └── wait_for_db.py
├── docker-compose.yml
├── frontend/
│   ├── Dockerfile
│   ├── app.py
│   ├── logger.py
│   ├── pages/
│   │   ├── 0_login.py
│   │   ├── 1_profil.py
│   │   └── 2_administration.py
│   └── requirements.txt
├── logs/
│   ├── api.2025-04-14_18-48-03_484480.log
│   ├── api.2025-04-15_15-28-22_724762.log
│   ├── api.log
│   └── app.log
├── postgres-custom/
│   ├── Dockerfile
│   ├── docker-entrypoint-init-custom.sh
│   ├── pg_hba.conf
│   ├── postgresql.conf
│   ├── server.crt
│   └── server.key
├── pytest.ini
└── tests/
    ├── Dockerfile
    ├── conftest.py
    ├── logger.py
    ├── requirements.txt
    ├── test_admin.py
    ├── test_auth.py
    ├── test_co_db.py
    ├── test_monitoring.py
    ├── test_users.py
    └── wait_for_api.py
```

---

## 📝 Conseils et bonnes pratiques

- **Créer le `.env` avec les noms de variables indiqués dans l'exemple**
- **Vérifiez la cohérence des variables d’environnement entre le `.env` et le `docker-compose.yml`.**
- **Pour toute modification de la configuration PostgreSQL (SCRAM, SSL, etc.), nettoyez les volumes avant de rebuild.**
- **Pour ajouter des dépendances Python, modifiez le `requirements.txt` du dossier concerné puis rebuildez l’image correspondante.**
- **Consultez les logs dans le dossier `logs/` pour le debug.**

---

## 👨‍💻 Pour aller plus loin

- Ajoutez une CI/CD pour automatiser les tests et le déploiement.
- Ajoutez Prometheus/Grafana pour la supervision.
- Sécurisez les certificats SSL pour la production (utilisez une vraie CA).
- Ajoutez des scripts de migration si vous faites évoluer le schéma de la base.

---

**Pour toute question ou contribution, ouvrez une issue ou une pull request sur le dépôt GitHub du projet.**

---

**Bon développement avec FastAPI_Xtrem !**

# **By KaRn1zC**
