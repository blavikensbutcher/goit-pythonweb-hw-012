"""Application configuration settings and logging setup."""

import logging
import os
from pathlib import Path

from pydantic import BaseModel
from pydantic.v1 import BaseSettings

BASE_DIR = Path(__file__).parent.parent


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


class Settings(BaseSettings):
    """Application settings loaded from environment variables and defaults."""

    auth_jwt: AuthJWT = AuthJWT()
    environment: EnvironmentSettings = EnvironmentSettings()
    mailgun: MailSettings = MailSettings()
    api: APISettings = APISettings()


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
