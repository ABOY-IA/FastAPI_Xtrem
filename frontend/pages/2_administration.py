import streamlit as st
import httpx
import pandas as pd

# URL de base de l'API backend
API_URL = "http://127.0.0.1:8000"

st.title("Administration - Liste des Utilisateurs")

# Vérification de l'authentification et du rôle
if "user" not in st.session_state or "role" not in st.session_state:
    st.warning("Vous devez être connecté en tant qu'administrateur pour accéder à cette page.")
    st.info("Veuillez vous rendre sur la page de connexion/inscription dans le menu latéral.")
    st.stop()

if st.session_state.role != "admin":
    st.error("Accès refusé : vous n'êtes pas administrateur.")
    st.stop()

# Préparer le header requis pour l'authentification admin
headers = {"X-User": st.session_state.user}

try:
    response = httpx.get(f"{API_URL}/admin/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df)
        else:
            st.info("Aucun utilisateur n'a été trouvé.")
    else:
        st.error(f"Erreur lors de la récupération des utilisateurs : {response.text}")
except Exception as e:
    st.error(f"Erreur lors de la requête : {e}")
