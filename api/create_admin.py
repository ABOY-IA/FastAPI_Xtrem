import os
from getpass import getpass
from api.db.session import SessionLocal
from api.db.services import create_user
from api.core.crypto import generate_user_key
from api.logger import logger
from dotenv import load_dotenv

load_dotenv()

ADMIN_CREATION_SECRET = os.getenv("ADMIN_CREATION_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")

def main():
    admin_secret = os.getenv("ADMIN_CREATION_SECRET")
    if not admin_secret:
        logger.error("La variable d'environnement ADMIN_CREATION_SECRET n'est pas définie.")
        return

    provided_secret = getpass("Veuillez entrer le secret d'administration : ").strip()
    if provided_secret != admin_secret:
        logger.warning("Secret incorrect. Accès refusé.")
        return

    logger.info("Début de la création du compte administrateur.")
    username = input("Nom d'utilisateur admin : ").strip()
    email = input("Email admin : ").strip()
    password = getpass("Mot de passe admin : ").strip()
    confirm_password = getpass("Confirmer le mot de passe admin : ").strip()
    if password != confirm_password:
        logger.warning("Les mots de passe ne correspondent pas.")
        return

    db = SessionLocal()
    encryption_key = generate_user_key()
    try:
        admin_user = create_user(db, username, email, password, role="admin", encryption_key=encryption_key)
        logger.info(f"Compte administrateur créé avec succès : username='{admin_user.username}', id={admin_user.id}")
        print(f"Compte administrateur créé avec succès : {admin_user.username}")
    except Exception as e:
        logger.exception("Erreur lors de la création du compte administrateur")
        print("Erreur lors de la création du compte administrateur :", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()
