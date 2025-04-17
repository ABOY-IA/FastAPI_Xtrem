import os
import httpx
import pandas as pd
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

st.title("Administration – Liste des Utilisateurs")

if "user" not in st.session_state or "access_token" not in st.session_state:
    st.warning("Vous devez être connecté pour accéder à l’administration.")
    st.info("Allez d'abord sur la page Connexion !")
    st.stop()

if st.session_state.get("role") != "admin":
    st.error("Accès refusé : vous n'êtes pas administrateur.")
    st.stop()

try:
    headers = {
        "X-User":       st.session_state["user"],
        "Authorization": f"Bearer {st.session_state['access_token']}"
    }
    resp = httpx.get(f"{API_URL}/admin/users", headers=headers, timeout=10)
    if resp.status_code == 200:
        users = resp.json()
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df)
        else:
            st.info("Aucun utilisateur trouvé.")
    else:
        err = resp.json().get("detail", resp.text)
        st.error(f"Erreur lors de la récupération : {err}")
except httpx.RequestError as e:
    st.error(f"Erreur réseau : {e}")
