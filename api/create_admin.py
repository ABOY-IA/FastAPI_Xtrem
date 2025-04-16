import os
from getpass import getpass
from api.db.session import SessionLocal
from api.db.services import create_user
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# Récupère la clé secrète
ADMIN_CREATION_SECRET = os.getenv("ADMIN_CREATION_SECRET")

# Récupère l'URL de la base
DATABASE_URL = os.getenv("DATABASE_URL")

def main():
    # Récupère la clé secrète pour la création d'un admin depuis les variables d'environnement
    admin_secret = os.getenv("ADMIN_CREATION_SECRET")
    if not admin_secret:
        print("Erreur : La variable d'environnement ADMIN_CREATION_SECRET n'est pas définie.")
        return

    # Demande à l'opérateur de saisir le secret d'administration de manière sécurisée
    provided_secret = getpass("Veuillez entrer le secret d'administration : ").strip()
    if provided_secret != admin_secret:
        print("Secret incorrect. Accès refusé.")
        return

    # Demande les informations du compte administrateur à créer
    print("Création du compte administrateur.")
    username = input("Nom d'utilisateur admin : ").strip()
    email = input("Email admin : ").strip()
    password = getpass("Mot de passe admin : ").strip()
    confirm_password = getpass("Confirmer le mot de passe admin : ").strip()
    if password != confirm_password:
        print("Les mots de passe ne correspondent pas.")
        return

    # Création du compte dans la base de données
    db = SessionLocal()
    try:
        admin_user = create_user(db, username, email, password, role="admin")
        logger.info(f"Compte administrateur créé avec succès : username='{admin_user.username}', id={admin_user.id}")
        print(f"Compte administrateur créé avec succès : {admin_user.username}")
    except Exception as e:
        logger.exception("Erreur lors de la création du compte administrateur")
        print("Erreur lors de la création du compte administrateur :", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()