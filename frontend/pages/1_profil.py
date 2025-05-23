import os
import httpx
import streamlit as st
from frontend.logger import logger

API_URL = os.getenv("API_URL", "http://api:8000")

# ——— Bouton de déconnexion unique ———
if "user" in st.session_state and st.sidebar.button("Se déconnecter", key="logout"):
    for k in ["user", "role", "access_token", "refresh_token"]:
        st.session_state.pop(k, None)
    logger.info("Utilisateur déconnecté depuis la page profil.")
    st.stop()

# ——— Vérification de la connexion ———
if "user" not in st.session_state or "access_token" not in st.session_state:
    st.warning("Vous devez être connecté pour accéder à cette page.")
    logger.warning("Tentative d'accès à la page profil sans être connecté.")
    st.stop()

st.title("FastAPI Xtrem – Modification du Profil")
st.subheader(f"Profil de {st.session_state['user']}")

with st.form("profil_form"):
    new_email = st.text_input("Nouvel email")
    new_password = st.text_input("Nouveau mot de passe", type="password")
    confirm_password = st.text_input("Confirmer le mot de passe", type="password")
    bio = st.text_area("Bio")
    submitted = st.form_submit_button("Mettre à jour")
if submitted:
    if new_password and new_password != confirm_password:
        st.error("Les mots de passe ne correspondent pas.")
        logger.warning(f"Échec mise à jour profil : mots de passe non concordants pour {st.session_state['user']}")
    else:
        update_data = {}
        if new_email: update_data["email"] = new_email
        if new_password: update_data["password"] = new_password
        if bio: update_data["bio"] = bio
        if not update_data:
            st.info("Aucune information à mettre à jour.")
            logger.info(f"Aucune modification envoyée pour le profil de {st.session_state['user']}")
        else:
            try:
                headers = {
                    "X-User": st.session_state["user"],
                    "Authorization": f"Bearer {st.session_state['access_token']}"
                }
                resp = httpx.patch(
                    f"{API_URL}/users/profile",
                    json=update_data,
                    headers=headers,
                    timeout=10,
                )
                if resp.status_code == 200:
                    st.success("Profil mis à jour avec succès.")
                    logger.info(f"Profil mis à jour pour {st.session_state['user']}")
                else:
                    try:
                        detail = resp.json().get("detail", resp.text)
                    except ValueError:
                        detail = resp.text
                    st.error(f"Échec de la mise à jour : {detail}")
                    logger.warning(f"Échec mise à jour profil pour {st.session_state['user']} : {detail}")
            except httpx.RequestError as e:
                st.error(f"Erreur réseau : {e}")
                logger.error(f"Erreur réseau lors de la mise à jour du profil : {e}")
