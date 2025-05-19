import pytest
from api.core.crypto import generate_user_key
from api.db.services import create_user
from api.db.session import SessionLocal

@pytest.fixture(scope="module")
def admin_user(event_loop):
    async def _make():
        async with SessionLocal() as db:
            return await create_user(
                db,
                username="admin",
                email="admin@example.com",
                password="AdminPass!23",
                role="admin",
                encryption_key=generate_user_key()
            )
    return event_loop.run_until_complete(_make())

@pytest.fixture(scope="module")
def normal_user(event_loop):
    async def _make():
        async with SessionLocal() as db:
            return await create_user(
                db,
                username="bob",
                email="bob@example.com",
                password="BobPass!23",
                role="user",
                encryption_key=generate_user_key()
            )
    return event_loop.run_until_complete(_make())

def test_list_all_users(client, admin_user):
    headers = {"X-User": admin_user.username}
    resp = client.get("/admin/users", headers=headers)
    assert resp.status_code == 200, resp.text
    usernames = [u["username"] for u in resp.json()]
    assert admin_user.username in usernames

def test_delete_user(client, admin_user, normal_user):
    headers = {"X-User": admin_user.username}
    resp = client.delete(f"/admin/users/{normal_user.id}", headers=headers)
    assert resp.status_code == 204, resp.text
    resp2 = client.get("/admin/users", headers=headers)
    assert normal_user.username not in [u["username"] for u in resp2.json()]
