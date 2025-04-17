import os
import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

st.title("FastAPI Xtrem – Modification du Profil")

if "user" not in st.session_state or "access_token" not in st.session_state:
    st.warning("Vous devez être connecté pour modifier votre profil.")
    st.info("Allez d'abord sur la page Connexion !")
    st.stop()

st.subheader("Mettre à jour votre profil")
with st.form("profil_form"):
    new_email        = st.text_input("Nouvel email", value=st.session_state.get("email", ""))
    new_password     = st.text_input("Nouveau mot de passe", type="password")
    confirm_password = st.text_input("Confirmer le mot de passe", type="password")
    bio              = st.text_area("Bio", value=st.session_state.get("bio", ""))
    submit_profile   = st.form_submit_button("Mettre à jour")

if submit_profile:
    if new_password and new_password != confirm_password:
        st.error("Les mots de passe ne correspondent pas.")
    else:
        payload = {}
        if new_email:    payload["email"] = new_email
        if new_password: payload["password"] = new_password
        if bio:          payload["bio"] = bio

        if not payload:
            st.info("Aucune modification détectée.")
        else:
            try:
                headers = {
                    "X-User":       st.session_state["user"],
                    "Authorization": f"Bearer {st.session_state['access_token']}"
                }
                resp = httpx.patch(
                    f"{API_URL}/users/profile",
                    json=payload,
                    headers=headers,
                    timeout=10,
                )
                if resp.status_code == 200:
                    st.success("Profil mis à jour avec succès ✅")
                else:
                    detail = resp.json().get("detail", resp.text)
                    st.error(f"Échec de la mise à jour : {detail}")
            except httpx.RequestError as e:
                st.error(f"Erreur réseau : {e}")
