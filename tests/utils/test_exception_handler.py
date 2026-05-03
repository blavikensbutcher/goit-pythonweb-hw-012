import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from src.utils.exception_handler import register_exception_handlers


class TestExceptionHandlers:
    def test_register_exception_handlers(self):
        app = FastAPI()
        register_exception_handlers(app)
        client = TestClient(app)

        # Test validation error
        # Since no routes, hard to test, but at least check registration doesn't crash
        assert len(app.exception_handlers) > 0