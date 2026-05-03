import datetime

import jwt
from bcrypt import checkpw, gensalt, hashpw
from dotenv import load_dotenv

from src.config import Settings

load_dotenv()

settings = Settings()


def hash_password(password: str) -> str:
    """Hash a plain password for secure storage."""
    if password is None:
        raise Exception("Cant hash an empty password")

    hashed = hashpw(password.encode("utf-8"), gensalt())
    return hashed.decode("utf-8")


def check_password(user_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a stored bcrypt hash."""
    if user_password is None:
        raise Exception("Input password trouble")
    if hashed_password is None:
        raise Exception("BE password trouble")

    return checkpw(user_password.encode("utf-8"), hashed_password.encode("utf-8"))


def encode_jwt(
    payload: dict,
    private_key: str = settings.auth_jwt.private_key_path.read_text(),
    algorithm: str = settings.auth_jwt.algorithm,
    expire_minutes: int = settings.auth_jwt.access_token_expires_in,
):
    """Encode a payload as a JWT with expiration claims."""
    to_encode = payload.copy()
    now = datetime.datetime.now(datetime.UTC)
    expire = now + datetime.timedelta(minutes=expire_minutes)
    to_encode.update(exp=expire, iat=now)
    encoded = jwt.encode(to_encode, private_key, algorithm)
    return encoded


def decode_jwt(
    token: str | bytes,
    public_key: str = settings.auth_jwt.public_key_path.read_text(),
    algorithm: str = settings.auth_jwt.algorithm,
):
    """Decode a JWT and return its payload after signature verification."""
    decoded = jwt.decode(token, public_key, algorithms=[algorithm])
    return decoded
