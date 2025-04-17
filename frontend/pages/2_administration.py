import os
import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

# ——— Bouton de déconnexion unique ———
if "user" in st.session_state and st.sidebar.button("Se déconnecter", key="logout"):
    for k in ["user", "role", "access_token", "refresh_token"]:
        st.session_state.pop(k, None)
    st.stop()

# ——— Vérification de la session et du rôle ———
if "user" not in st.session_state or "access_token" not in st.session_state:
    st.warning("Vous devez être connecté en tant qu'administrateur pour accéder à cette page.")
    st.stop()
if st.session_state.get("role") != "admin":
    st.error("Accès refusé : vous n'êtes pas administrateur.")
    st.stop()

st.title("Administration - Liste des Utilisateurs")

headers = {
    "X-User":        st.session_state["user"],
    "Authorization": f"Bearer {st.session_state['access_token']}"
}

# ——— Récupération de la liste des utilisateurs ———
try:
    resp = httpx.get(f"{API_URL}/admin/users", headers=headers, timeout=10)
    if resp.status_code != 200:
        err = resp.json().get("detail", resp.text)
        st.error(f"Erreur lors de la récupération : {err}")
        st.stop()
    users = resp.json()
    if not users:
        st.info("Aucun utilisateur trouvé.")
        st.stop()
except httpx.RequestError as e:
    st.error(f"Erreur réseau : {e}")
    st.stop()

# ——— Affichage + boutons de suppression ———
st.write("**Cliquer sur ❌ pour supprimer un utilisateur**")
for u in users:
    col1, col2 = st.columns([4,1])
    col1.write(f"{u['username']} — {u['email']} — rôle : {u['role']}")
    if col2.button("❌", key=f"del_{u['id']}"):
        st.session_state["to_delete"] = u["id"]

    # Confirmation en bas de la ligne
    if st.session_state.get("to_delete") == u["id"]:
        st.warning(f"Êtes-vous sûr de vouloir supprimer **{u['username']}** ? Cette action est irréversible.")
        c1, c2 = st.columns(2)
        if c1.button("Oui", key=f"yes_{u['id']}"):
            dresp = httpx.delete(f"{API_URL}/admin/users/{u['id']}", headers=headers, timeout=10)
            if dresp.status_code == 204:
                st.success(f"Utilisateur {u['username']} supprimé.")
                st.session_state.pop("to_delete", None)
                st.stop()  # stop + reload auto
            else:
                try:
                    derr = dresp.json().get("detail", dresp.text)
                except ValueError:
                    derr = dresp.text
                st.error(f"Échec de la suppression : {derr}")
        if c2.button("Annuler", key=f"no_{u['id']}"):
            st.session_state.pop("to_delete", None)
            st.info("Suppression annulée.")

# ——— (facultatif) on peut aussi afficher un tableau récapitulatif ———
# import pandas as pd
# df = pd.DataFrame(users)
# st.dataframe(df)
