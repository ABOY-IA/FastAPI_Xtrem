import pytest
from api.db.services import create_user
from api.core.crypto import generate_user_key

@pytest.fixture(scope="module")
def auth_user(event_loop, db_session):
    async def _make():
        return await create_user(
            db_session,
            username="eve",
            email="eve@example.com",
            password="EvePass!23",
            role="user",
            encryption_key=generate_user_key()
        )
    return event_loop.run_until_complete(_make())

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
    protected = client.get(
        "/users/profile",
        headers={"X-User": auth_user.username, "Authorization": f"Bearer {access1}"}
    )
    assert protected.status_code == 200

    # --- 3) Rotation du refresh ---
    resp2 = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh1}"}
    )
    assert resp2.status_code == 200, resp2.text
    tok2 = resp2.json()
    assert tok2["access_token"] != access1
    assert tok2["refresh_token"] != refresh1

    # --- 4) Ancien refresh invalide ---
    resp3 = client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh1}"}
    )
    assert resp3.status_code == 401
