# FastAPI_Xtrem

# 🐍 Configuration de l’environnement Python (.venv)

Ce projet utilise un environnement virtuel Python pour isoler les dépendances.

## ✅ Prérequis

- Python 3.11 ou plus (recommandé)
- `pip` installé (inclus avec Python)
- Terminal ou shell (Linux, macOS, Windows PowerShell, Bash, etc)

---

## 📦 Création de l’environnement virtuel

```bash
# À la racine du projet
python3 -m venv .venv
```

## ▶️ Activation de l’environnement

Sous Linux / macOS :
```bash
source .venv/bin/activate
```

Sous Windows (PowerShell) :
```powershell
.venv\Scripts\Activate.ps1
```

Sous Windows (CMD) :
```cmd
.venv\Scripts\activate.bat
```

## ⛔ Désactivation de l’environnement

```bash
deactivate
```

## 🚀 Mise à jour de pip

```bash
python -m pip install --upgrade pip
```

## 📚 Installation des dépendances

```bash
pip install -r requirements.txt
```

## 📎 Générer ou mettre à jour le requirements.txt

```bash
pip freeze > requirements.txt
```

## 📦 Création de l’environnement Docker

A la racine du projet, créer un ficher `.env` qui contiendra les variables d'environnement nécessaire aux Dockerfiles et docker-compose

## Secret Création Compte Admin

Dans le fichier `.env` créer une ligne `ADMIN_CREATION_SECRET=` et ajouter son secret qui permettra de créer un compte admin.

## Commandes Docker

### Création des images, volumes et containers

```bash
export COMPOSE_BAKE=true
docker compose up
```

### Suppression

Pour supprimer toutes les images et les containers mais garder les données de la DB :
```bash
docker compose down --rmi all
```
Pour supprimer toutes les images, les containers et les volumes de la DB :
```bash
docker compose down -v --rmi all
```

### Lancement des fichiers via Docker

Pour executer les tests unitaires :
```bash
docker-compose run --rm tests
```
Pour créer un compte admin :
```bash
docker compose run --rm api python create_admin.py
```

## 📁 Arborescence du projet FastAPI Xtrem

```bash
FastAPI_Xtrem/
├── api/                         # Backend FastAPI
│   ├── main.py                  # Point d’entrée FastAPI
│   ├── config.py                # Chargement des settings/env
│   ├── deps/                    # Fonctions Depends (auth, DB, scopes...)
│   │   └── auth.py
│   ├── core/                    # Logique centrale : tokens, sécurité, chiffrement, utils
│   │   ├── security.py
│   │   ├── tokens.py
│   │   ├── crypto.py
│   │   └── utils.py
│   ├── db/                      # Base de données
│   │   ├── base.py              # Base SQLAlchemy
│   │   ├── models.py            # Modèles ORM
│   │   ├── schemas.py           # Modèles Pydantic
│   │   ├── session.py           # Connexion DB + événements
│   │   └── services.py          # Fonctions CRUD
│   ├── users/                   # Routes utilisateurs
│   │   └── routes.py
│   ├── auth/                    # Routes authentification
│   │   └── routes.py
│   ├── admin/                   # Routes admin sécurisées
│   │   └── routes.py
│   ├── monitoring/              # Route /health et métriques
│   │   └── routes.py
│   ├── middleware/              # Rate limiting, CORS, XSS, etc.
│   │   └── security_middleware.py
│   ├── Dockerfile               # Dockerfile API
│   ├── requirements.txt         # Librairies pour faire fonctionner l'API
│   ├── __init__.py              # Identifie ce dossier comme package python
│   └── routers.py               # Import central de tous les routers

├── frontend/                    # Interface utilisateur Streamlit
│   ├── app.py                   # Lancement Streamlit
│   ├── Dockerfile               # Dockerfile Streamlit
│   ├── requirements.txt         # Librairies pour faire fonctionner Streamlit
│   └── pages/
│       ├── 0_login.py
│       ├── 1_profil.py
│       └── 2_administration.py

├── logs/                        
│   ├── api.log                  # Généré automatiquement par Loguru

├── tests/                       # Tests unitaires et fonctionnels
│   ├── conftest.py              # Setup Pytest
│   ├── test_users.py            # Tests utilisateurs
│   ├── test_auth.py             # Tests d'auth
│   ├── test_admin.py            # Tests droits d’accès
│   ├── test_monitoring.py       # Test /health
│   ├── Dockerfile               # Dockerfile pytest
│   ├── requirements.txt         # Librairies pour faire fonctionner les tests unitaires
│   └── cassettes/               # (si VCR.py utilisé)

├── .env                         # Variables d’environnement (local)
├── .env.example                 # Modèle .env sans secrets
├── requirements.txt             # Dépendances Python
├── README.md                    # Documentation complète
├── create_admin.py              # Fichier de création compte administrateur
├── docker-compose.yml           # Services API, frontend, Prometheus, Grafana
├── docker-compose.override.yml  # Pour le dev local (montage auto)
├── pytest.ini
├── .gitignore
├── Makefile                     # Automatiser les commandes courantes (run, test, lint, ...)

└── vscode/                      
    ├── settings.json            # Pour détecter automatiquement le .venv dans VSCode

└── docs/                        # Documentation annexe
    ├── architecture.md
    ├── scopes_permissions.md
    ├── tokens_rotation.md
    └── diagramme_db.png
```

docker-compose down --rmi all --volumes --remove-orphans && \
export COMPOSE_BAKE=true && \
docker-compose up --build

