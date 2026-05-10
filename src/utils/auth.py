import datetime

import jwt
from bcrypt import checkpw, gensalt, hashpw
from dotenv import load_dotenv

from src.config import Settings

load_dotenv()

settings = Settings()

# Cache for loaded keys
_private_key_cache = None
_public_key_cache = None


def get_private_key() -> str:
    """Get the private key, loading from file on first call."""
    global _private_key_cache
    if _private_key_cache is None:
        _private_key_cache = settings.auth_jwt.private_key_path.read_text()
    return _private_key_cache


def get_public_key() -> str:
    """Get the public key, loading from file on first call."""
    global _public_key_cache
    if _public_key_cache is None:
        _public_key_cache = settings.auth_jwt.public_key_path.read_text()
    return _public_key_cache


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
    private_key: str = None,
    algorithm: str = None,
    expire_minutes: int = None,
):
    """Encode a payload as a JWT with expiration claims."""
    if private_key is None:
        private_key = get_private_key()
    if algorithm is None:
        algorithm = settings.auth_jwt.algorithm
    if expire_minutes is None:
        expire_minutes = settings.auth_jwt.access_token_expires_in
    
    to_encode = payload.copy()
    now = datetime.datetime.now(datetime.UTC)
    expire = now + datetime.timedelta(minutes=expire_minutes)
    to_encode.update(exp=expire, iat=now)
    encoded = jwt.encode(to_encode, private_key, algorithm)
    return encoded


def decode_jwt(
    token: str | bytes,
    public_key: str = None,
    algorithm: str = None,
):
    """Decode a JWT and return its payload after signature verification."""
    if public_key is None:
        public_key = get_public_key()
    if algorithm is None:
        algorithm = settings.auth_jwt.algorithm
    
    decoded = jwt.decode(token, public_key, algorithms=[algorithm])
    return decoded
