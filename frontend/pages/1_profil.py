import streamlit as st
import httpx
import os

API_URL   = os.getenv("API_URL", "http://api:8000")
TOKEN_KEY = "token"  # assurez‑vous que vous stockez le token sous cette clé

st.title("FastAPI Xtrem – Modification du Profil")

if "user" not in st.session_state or TOKEN_KEY not in st.session_state:
    st.warning("Vous devez être connecté pour modifier votre profil.")
    st.stop()

st.subheader("Mettre à jour votre profil")
with st.form("profil_form"):
    new_email        = st.text_input("Nouvel email")
    new_password     = st.text_input("Nouveau mot de passe", type="password")
    confirm_password = st.text_input("Confirmer le mot de passe", type="password")
    bio              = st.text_area("Bio")
    submit_profile   = st.form_submit_button("Mettre à jour")

if submit_profile:
    if new_password and new_password != confirm_password:
        st.error("Les mots de passe ne correspondent pas.")
    else:
        update_data = {}
        if new_email:    update_data["email"] = new_email
        if new_password: update_data["password"] = new_password
        if bio:          update_data["bio"] = bio

        if not update_data:
            st.info("Aucune information à mettre à jour.")
        else:
            try:
                headers = {
                    "X-User": st.session_state.user,
                    "Authorization": f"Bearer {st.session_state.token}"
                }
                response = httpx.patch(
                    f"{API_URL}/users/profile",
                    json=update_data,
                    headers=headers,
                    timeout=10,
                )
                if response.status_code == 200:
                    st.success("Profil mis à jour avec succès.")
                else:
                    detail = response.json().get("detail", "Erreur lors de la mise à jour.")
                    st.error(f"Échec de la mise à jour : {detail}")
            except Exception as e:
                st.error(f"Erreur lors de la requête : {e}")