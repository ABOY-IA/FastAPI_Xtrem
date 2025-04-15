import streamlit as st
import httpx

# URL de base de l'API backend
API_URL = "http://127.0.0.1:8000"

st.title("FastAPI Xtrem - Modification du Profil")

# Vérifier que l'utilisateur est connecté
if "user" not in st.session_state:
    st.warning("Vous devez être connecté pour modifier votre profil.")
    st.info("Veuillez vous rendre sur la page de connexion/inscription dans le menu latéral.")
    st.stop()

st.subheader("Mettre à jour votre profil")

with st.form("profil_form"):
    # Pré-remplir les champs si nécessaire ou laisser vide
    new_email = st.text_input("Nouvel email")
    new_password = st.text_input("Nouveau mot de passe", type="password")
    confirm_password = st.text_input("Confirmer le mot de passe", type="password")
    bio = st.text_area("Bio")
    submit_profile = st.form_submit_button("Mettre à jour")

if submit_profile:
    if new_password and new_password != confirm_password:
        st.error("Les mots de passe ne correspondent pas.")
    else:
        update_data = {}
        if new_email:
            update_data["email"] = new_email
        if new_password:
            update_data["password"] = new_password
        if bio:
            update_data["bio"] = bio
        
        if not update_data:
            st.info("Aucune information à mettre à jour.")
        else:
            try:
                # Ajout du header "X-User" avec la valeur de l'utilisateur connecté
                headers = {"X-User": st.session_state.user}
                response = httpx.patch(f"{API_URL}/users/profile", json=update_data, headers=headers)
                if response.status_code == 200:
                    st.success("Profil mis à jour avec succès.")
                else:
                    error_detail = response.json().get("detail", "Erreur lors de la mise à jour du profil.")
                    st.error(f"Échec de la mise à jour : {error_detail}")
            except Exception as e:
                st.error(f"Erreur lors de la requête : {e}")
