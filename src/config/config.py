"""Application configuration settings and logging setup."""

import logging
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from pydantic import BaseModel
from pydantic.v1 import BaseSettings

BASE_DIR = Path(__file__).parent.parent


def generate_rsa_key_pair():
    """Generate RSA key pair if it doesn't exist."""
    certs_dir = BASE_DIR / "certs"
    certs_dir.mkdir(exist_ok=True)
    
    private_key_path = certs_dir / "jwt-private.pem"
    public_key_path = certs_dir / "jwt-public.pem"
    
    # Only generate if keys don't exist
    if not private_key_path.exists() or not public_key_path.exists():
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Serialize private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            private_key_path.write_bytes(private_pem)
            
            # Serialize public key
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            public_key_path.write_bytes(public_pem)
            
            logging.info("Generated JWT RSA key pair successfully")
        except Exception as e:
            logging.error(f"Failed to generate RSA key pair: {e}")
            raise


class EnvironmentSettings(BaseModel):
    """Environment-specific configuration values."""

    ENV: str = os.environ.get("ENV", "development")


class MailSettings(BaseModel):
    """Mail provider settings for sending email notifications."""

    API_KEY: str | None = os.environ.get("MAILGUN_API_KEY")


class AuthJWT(BaseModel):
    """JWT configuration values for token generation and validation."""

    private_key_path: Path = BASE_DIR / "certs" / "jwt-private.pem"
    refresh_token_key_path: Path = BASE_DIR / "certs" / "jwt-refresh-token.pem"
    public_key_path: Path = BASE_DIR / "certs" / "jwt-public.pem"
    algorithm: str = "RS256"
    access_token_expires_in: int = int(
        os.environ.get("EXPIRES_IN_ACCESS_TOKEN") or 1440
    )
    refresh_token_expires_in: int = int(
        os.environ.get("EXPIRES_IN_REFRESH_TOKEN") or 10080
    )
    verify_token_expires_in: int = int(
        os.environ.get("EXPIRES_IN_VERIFY_TOKEN") or 1440
    )


class APISettings(BaseModel):
    """API-related configuration values, including the base URL."""

    base_url: str = os.environ.get("BASE_URL", "http://localhost:8090/api/v1/")


class RedisSettings(BaseModel):
    """Redis settings used for application-level caching."""

    url: str | None = os.environ.get("REDIS_URL")
    host: str = os.environ.get("REDIS_HOST", "localhost")
    port: int = int(os.environ.get("REDIS_PORT") or 6379)
    username: str | None = os.environ.get("REDIS_USERNAME")
    password: str | None = os.environ.get("REDIS_PASSWORD")
    db: int = int(os.environ.get("REDIS_DB") or 0)
    ssl: bool = os.environ.get("REDIS_SSL", "").lower() in {"1", "true", "yes"}
    user_cache_ttl: int = int(os.environ.get("REDIS_USER_CACHE_TTL") or 900)


class Settings(BaseSettings):
    """Application settings loaded from environment variables and defaults."""

    auth_jwt: AuthJWT = AuthJWT()
    environment: EnvironmentSettings = EnvironmentSettings()
    mailgun: MailSettings = MailSettings()
    api: APISettings = APISettings()
    redis: RedisSettings = RedisSettings()
    
    def __init__(self, **data):
        """Initialize settings and generate keys if needed."""
        super().__init__(**data)
        # Generate JWT keys on startup if they don't exist
        generate_rsa_key_pair()


def configure_logging(level: int = logging.INFO):
    """Configure global logging settings for the application."""
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format=(
            "[%(asctime)s.%(msecs)03d] %(funcName)20s %(module)s:%(lineno)d "
            "%(levelname) -8s - %(message)s"
        ),
    )
