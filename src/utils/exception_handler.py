import logging
import os
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError, DatabaseError, SQLAlchemyError

load_dotenv(".env.development")
logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI):
    """Register common FastAPI exception handlers for validation and database errors."""
    env_value = os.getenv("ENV")

    @app.exception_handler(ValidationError)
    async def handle_pydantic_validation_error(_: Request, exc: ValidationError):
        if env_value == "development":
            logger.error("Validation error:\n%s", traceback.format_exc())
        return ORJSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": (
                    exc.errors() if env_value == "development" else "Validation error"
                ),
            },
        )

    @app.exception_handler(DatabaseError)
    async def handle_db_error(_: Request, exc: DatabaseError):
        logger.error("Database error:\n%s", traceback.format_exc())
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": (
                    str(exc.orig)
                    if env_value == "development"
                    else "Unexpected database error"
                )
            },
        )

    @app.exception_handler(DBAPIError)
    async def handle_dbapi_error(_: Request, exc: DBAPIError):
        logger.error("DBAPI error:\n%s", traceback.format_exc())
        return ORJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Database error",
                "detail": (
                    str(exc.orig)
                    if env_value == "development"
                    else "Invalid input for database"
                ),
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy_error(_: Request, exc: SQLAlchemyError):
        logger.error("SQLAlchemy error:\n%s", traceback.format_exc())
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": (
                    str(exc)
                    if env_value == "development"
                    else "Unexpected database error"
                ),
            },
        )
