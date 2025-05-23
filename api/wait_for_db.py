import time
import socket
import sys
import os
import asyncio
import ssl

from dotenv import load_dotenv

try:
    import asyncpg
except ImportError:
    print("Le module asyncpg n'est pas installé. Ajoutez-le à votre requirements.txt.", file=sys.stderr)
    sys.exit(1)

load_dotenv()

def wait_for_port(host: str, port: int, timeout: int = 60):
    start = time.monotonic()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"[wait_for_db] Database TCP port is open at {host}:{port}")
                return
        except OSError as e:
            if time.monotonic() - start > timeout:
                print(f"[wait_for_db] Timeout: Database TCP port not available after {timeout} seconds.", file=sys.stderr)
                sys.exit(1)
            print(f"[wait_for_db] Waiting for database TCP port at {host}:{port}... ({e})")
            time.sleep(2)

async def wait_for_pgsql(dsn: str, ssl_ctx, user: str, timeout: int = 60):
    start = time.monotonic()
    last_error = None
    attempt = 0
    while True:
        attempt += 1
        try:
            print(f"[wait_for_db] Attempting SQL connection (try {attempt}) as user '{user}' with SSL...")
            conn = await asyncpg.connect(dsn=dsn, timeout=5, ssl=ssl_ctx)
            await conn.execute("SELECT 1;")
            await conn.close()
            print("[wait_for_db] Database is ready to accept SQL connections.")
            return
        except Exception as e:
            last_error = e
            if time.monotonic() - start > timeout:
                print(f"[wait_for_db] Timeout: Database not ready for SQL after {timeout} seconds.\nLast error: {e}", file=sys.stderr)
                sys.exit(1)
            print(f"[wait_for_db] Waiting for database SQL connection... ({e})")
            await asyncio.sleep(2)

if __name__ == "__main__":
    db_host = os.environ.get("DB_HOST", "db")
    db_port = int(os.environ.get("DB_PORT", "5432"))
    db_user = os.environ.get("POSTGRES_USER", "user")
    db_pass = os.environ.get("POSTGRES_PASSWORD", "pass")
    db_name = os.environ.get("POSTGRES_DB", "xtremdb")
    timeout = int(os.environ.get("DB_WAIT_TIMEOUT", "60"))

    print(f"[wait_for_db] Using credentials: user='{db_user}', db='{db_name}', host='{db_host}', port={db_port}")

    # 1. Attendre que le port soit ouvert (TCP)
    wait_for_port(db_host, db_port, timeout)

    # 2. Tenter une vraie connexion PostgreSQL avec asyncpg et SSL explicite
    dsn = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    # Création du contexte SSL (équivalent à sslmode=require, sans vérification du certificat)
    ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    asyncio.run(wait_for_pgsql(dsn, ssl_ctx, db_user, timeout))
