from datetime import datetime, timezone

from fastapi import HTTPException
from jwt import InvalidTokenError


from src.constants.auth import auth_constants
from src.utils.auth import decode_jwt


async def validate_refresh_token(refresh_token: str) -> bool:
    """Validate that a refresh token is correct and has not expired."""
    try:
        decoded_token = decode_jwt(refresh_token)

        if decoded_token["type"] != auth_constants.TOKEN_TYPE.get("REFRESH"):
            raise HTTPException(400, "Incorrect token type")

        current_time = datetime.now(timezone.utc).timestamp()
        if decoded_token.get("exp") and decoded_token["exp"] < current_time:
            raise HTTPException(401, "Token has expired")

    except InvalidTokenError:
        raise HTTPException(400, "Can't update access token")

    return True


async def validate_access_token(access_token: str):
    """Validate an access token and return its decoded payload."""
    try:
        decoded_token = decode_jwt(access_token)
        if decoded_token["type"] != auth_constants.TOKEN_TYPE.get("ACCESS"):
            raise HTTPException(400, "Incorrect token type")

        current_time = datetime.now(timezone.utc).timestamp()
        if decoded_token.get("exp") and decoded_token["exp"] < current_time:
            raise HTTPException(401, "Token has expired")

    except InvalidTokenError:
        raise HTTPException(400, "Can't update access token")

    return decoded_token
