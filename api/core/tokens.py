import os
from datetime import datetime, timedelta, timezone
from jose import jwt
import uuid

SECRET_KEY = os.getenv("SECRET_KEY", "mon_secret_default")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    to_encode.update({"iat": datetime.now(timezone.utc)})  # Ajoute l'instant de création
    to_encode.update({"jti": str(uuid.uuid4())})           # Ajoute un identifiant unique
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
