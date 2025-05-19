# tests/test_auth.py
import pytest
from api.db.session import SessionLocal
from api.db.services import create_user
from api.core.crypto import generate_user_key

@pytest.fixture(scope="module")
def auth_user():
    db = SessionLocal()
    key = generate_user_key()
    user = create_user(
        db,
        username="eve",
        email="eve@example.com",
        password="EvePass!23",
        role="user",
        encryption_key=key
    )
    db.close()
    return user

def test_login_and_refresh_cycle(client, auth_user):
    # --- 1) Login ---
    resp = client.post(
        "/users/login",
        json={"username": auth_user.username, "password": "EvePass!23"}
    )
    assert resp.status_code == 200, resp.text
    tok = resp.json()
    access1 = tok["access_token"]
    refresh1 = tok["refresh_token"]

    # --- 2) Accès à une route protégée (ex: /users/profile) ---
    # Si vous avez un endpoint profil, sinon tombe à 200 sur /users/login guard…
    protected = client.get(
        "/users/profile",
        headers={"Authorization": f"Bearer {access1}"}
    )
    assert protected.status_code == 200

    # --- 3) Rotation du refresh ---
    resp2 = client.post(
        "/refresh",
        headers={"Authorization": f"Bearer {refresh1}"}
    )
    assert resp2.status_code == 200, resp2.text
    tok2 = resp2.json()
    assert tok2["access_token"] != access1
    assert tok2["refresh_token"] != refresh1

    # --- 4) Ancien refresh invalide ---
    resp3 = client.post(
        "/refresh",
        headers={"Authorization": f"Bearer {refresh1}"}
    )
    assert resp3.status_code == 401
