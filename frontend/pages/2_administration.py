import streamlit as st
import httpx
import pandas as pd
import os

# URL de base de l'API backend
API_URL = os.getenv("API_URL", "http://api:8000")

st.title("Administration - Liste des Utilisateurs")

# Vérifier connexion + rôle admin
token = st.session_state.get("access_token")
role  = st.session_state.get("role")
if not token or role != "admin":
    st.warning("Vous devez être connecté en tant qu'administrateur pour accéder à cette page.")
    st.info("Veuillez vous rendre sur la page de connexion/inscription dans le menu latéral.")
    st.stop()

try:
    # 🔄 on envoie le Bearer token
    headers = {
    "X-User": st.session_state.user,
    "Authorization": f"Bearer {st.session_state.token}"
}
    response = httpx.get(f"{API_URL}/admin/users", headers=headers, timeout=10)
    if response.status_code == 200:
        users = response.json()
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df)
        else:
            st.info("Aucun utilisateur n'a été trouvé.")
    else:
        error_detail = response.json().get("detail", response.text)
        st.error(f"Erreur lors de la récupération des utilisateurs : {error_detail}")
except Exception as e:
    st.error(f"Erreur lors de la requête : {e}")