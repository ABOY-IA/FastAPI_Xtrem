import pytest
import pytest_asyncio
from uuid import uuid4
from api.core.crypto import generate_user_key
from api.db.services import create_user
from tests.logger import logger

@pytest_asyncio.fixture
async def admin_user(db_session):
    unique = str(uuid4())[:8]
    logger.info(f"Création d'un utilisateur admin pour le test : admin_{unique}")
    return await create_user(
        db_session,
        username=f"admin_{unique}",
        email=f"admin_{unique}@example.com",
        password="AdminPass!23",
        role="admin",
        encryption_key=generate_user_key()
    )

@pytest_asyncio.fixture
async def normal_user(db_session):
    unique = str(uuid4())[:8]
    logger.info(f"Création d'un utilisateur normal pour le test : bob_{unique}")
    return await create_user(
        db_session,
        username=f"bob_{unique}",
        email=f"bob_{unique}@example.com",
        password="BobPass!23",
        role="user",
        encryption_key=generate_user_key()
    )

@pytest.mark.asyncio
async def test_list_all_users(async_client, admin_user):
    headers = {"X-User": admin_user.username}
    resp = await async_client.get("/admin/users", headers=headers)
    assert resp.status_code == 200, resp.text
    usernames = [u["username"] for u in resp.json()]
    assert admin_user.username in usernames
    logger.info(f"Vérification de la présence de l'admin {admin_user.username} dans la liste des utilisateurs")

@pytest.mark.asyncio
async def test_delete_user(async_client, admin_user, normal_user):
    headers = {"X-User": admin_user.username}
    resp = await async_client.delete(f"/admin/users/{normal_user.id}", headers=headers)
    assert resp.status_code == 204, resp.text
    resp2 = await async_client.get("/admin/users", headers=headers)
    assert normal_user.username not in [u["username"] for u in resp2.json()]
    logger.info(f"Suppression de l'utilisateur {normal_user.username} vérifiée par l'admin {admin_user.username}")
