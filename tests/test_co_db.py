import pytest
from api.db.session import connect_to_db

@pytest.mark.asyncio
async def test_database_connection():
    try:
        await connect_to_db()
    except Exception as e:
        pytest.fail(f"DB connection failed with error: {e}")

