import os
import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

st.title("FastAPI Xtrem – Connexion / Inscription")

page = st.sidebar.selectbox("Navigation", ["Connexion", "Inscription"])

if page == "Connexion":
    st.subheader("Connexion")
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit_login = st.form_submit_button("Se connecter")

    if submit_login:
        try:
            resp = httpx.post(
                f"{API_URL}/users/login",
                json={"username": username, "password": password},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Stockage en session
                st.session_state["user"]          = data["username"]
                st.session_state["role"]          = data.get("role")
                st.session_state["access_token"]  = data["access_token"]
                st.session_state["refresh_token"] = data.get("refresh_token")
                st.success(f"Connexion réussie ! Bienvenue {data['username']} 🎉")
                # tentative de relance automatique, sinon on continue
                try:
                    st.experimental_rerun()
                except AttributeError:
                    # votre version de Streamlit n'a pas experimental_rerun
                    pass
            else:
                err = resp.json().get("detail", resp.text)
                st.error(f"Échec de la connexion : {err}")
        except httpx.RequestError as e:
            st.error(f"Erreur réseau : {e}")

elif page == "Inscription":
    st.subheader("Inscription")
    with st.form("register_form"):
        new_username     = st.text_input("Nom d'utilisateur")
        new_email        = st.text_input("Email")
        new_password     = st.text_input("Mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password")
        submit_register  = st.form_submit_button("S'inscrire")

    if submit_register:
        if new_password != confirm_password:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            try:
                resp = httpx.post(
                    f"{API_URL}/users/register",
                    json={
                        "username": new_username,
                        "email":    new_email,
                        "password": new_password,
                    },
                    timeout=10,
                )
                if resp.status_code == 201:
                    user = resp.json()
                    st.success(f"Inscription réussie ! Bienvenue {user['username']} 🎉")
                else:
                    err = resp.json().get("detail", resp.text)
                    st.error(f"Échec de l'inscription : {err}")
            except httpx.RequestError as e:
                st.error(f"Erreur réseau : {e}")
