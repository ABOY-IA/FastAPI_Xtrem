import streamlit as st
import httpx

# URL de base de l'API backend
API_URL = "http://127.0.0.1:8000"

st.title("FastAPI Xtrem - Connexion / Inscription")

# Menu de navigation dans la barre latérale
page = st.sidebar.selectbox("Navigation", ["Connexion", "Inscription"])

if page == "Connexion":
    st.subheader("Connexion")
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit_login = st.form_submit_button("Se connecter")
    if submit_login:
        try:
            response = httpx.post(f"{API_URL}/users/login", json={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                data = response.json()
                st.success(f"{data['message']}")
                # Enregistre éventuellement les tokens dans la session Streamlit pour les appels authentifiés ultérieurs
                st.session_state.user = username
                if "role" in data:
                    st.session_state.role = data["role"]
            else:
                error_detail = response.json().get("detail", "Erreur lors de la connexion.")
                st.error(f"Échec de connexion : {error_detail}")
        except Exception as e:
            st.error(f"Erreur lors de la requête : {e}")

elif page == "Inscription":
    st.subheader("Inscription")
    with st.form("register_form"):
        new_username = st.text_input("Nom d'utilisateur")
        new_email = st.text_input("Email")
        new_password = st.text_input("Mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")
        submit_register = st.form_submit_button("S'inscrire")
    if submit_register:
        if new_password != confirm_password:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            try:
                response = httpx.post(f"{API_URL}/users/register", json={
                    "username": new_username,
                    "email": new_email,
                    "password": new_password
                })
                if response.status_code == 201:
                    data = response.json()
                    st.success(f"Inscription réussie, bienvenue {data['username']} !")
                    # Optionnel : enregistrer le nom d'utilisateur dans la session pour la suite
                    st.session_state.user = data['username']
                else:
                    error_detail = response.json().get("detail", "Erreur lors de l'inscription.")
                    st.error(f"Échec de l'inscription : {error_detail}")
            except Exception as e:
                st.error(f"Erreur lors de la requête : {e}")
