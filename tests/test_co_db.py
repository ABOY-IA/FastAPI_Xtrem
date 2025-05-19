import pytest
from api.db.session import connect_to_db

@pytest.mark.asyncio
async def test_database_connection_does_not_fail():
    try:
        await connect_to_db()
    except Exception as e:
        pytest.fail(f"Échec de la connexion à la DB : {e}")
