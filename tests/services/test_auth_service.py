import pytest
import uuid
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from sqlalchemy import select

from src.services.auth_service import AuthService
from src.models.user import CreateUserModel, AuthCredentials, UserModel


class TestAuthService:
    @pytest.fixture
    def service(self):
        return AuthService()

    @pytest.fixture
    def unique_email(self):
        return f"test+{uuid.uuid4().hex}@example.com"

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session, service, unique_email):
        user_data = CreateUserModel(name="Test User", email=unique_email, password="password123")
        
        with patch('src.utils.mailer.Mailer.send_simple_message', new_callable=AsyncMock):
            user = await service.create_user(db_session, user_data)
            
        assert user.email == unique_email
        assert user.name == "Test User"
        assert user.isVerified is False

    @pytest.mark.asyncio
    async def test_create_user_conflict(self, db_session, service, unique_email):
        user_data = CreateUserModel(name="Test User", email=unique_email, password="password123")
        
        with patch('src.utils.mailer.Mailer.send_simple_message', new_callable=AsyncMock):
            await service.create_user(db_session, user_data)
            
            with pytest.raises(HTTPException) as exc:
                await service.create_user(db_session, user_data)
            
            assert exc.value.status_code == 409
            assert exc.value.detail == "User already registered"

    @pytest.mark.asyncio
    async def test_login_success(self, db_session, service, unique_email):
        user_data = CreateUserModel(name="Login User", email=unique_email, password="password123")
        
        with patch('src.utils.mailer.Mailer.send_simple_message', new_callable=AsyncMock):
            await service.create_user(db_session, user_data)
            
        creds = AuthCredentials(email=unique_email, password="password123")
        response = await service.login(db_session, creds)
        
        assert response.type == "Bearer"
        assert response.accessToken is not None
        assert response.refreshToken is not None

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, db_session, service):
        creds = AuthCredentials(email="notfound@example.com", password="password123")
        
        with pytest.raises(HTTPException) as exc:
            await service.login(db_session, creds)
            
        assert exc.value.status_code == 404
        assert exc.value.detail == "User not found"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db_session, service, unique_email):
        user_data = CreateUserModel(name="Wrong Pwd", email=unique_email, password="password123")
        
        with patch('src.utils.mailer.Mailer.send_simple_message', new_callable=AsyncMock):
            await service.create_user(db_session, user_data)
            
        creds = AuthCredentials(email=unique_email, password="wrongpassword")
        with pytest.raises(HTTPException) as exc:
            await service.login(db_session, creds)
            
        assert exc.value.status_code == 401
        assert exc.value.detail == "Email or password is wrong"

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, db_session, service):
        with pytest.raises(HTTPException) as exc:
            await service.verify_email(db_session, "invalid.token.string")
            
        assert exc.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_access_token_invalid_token(self, db_session, service):
        with patch('src.services.auth_service.validate_refresh_token', return_value=False):
            with pytest.raises(HTTPException) as exc:
                await service.update_access_token(db_session, "bad_token")
                
            assert exc.value.status_code == 400
            assert exc.value.detail == "Token invalid"

    @pytest.mark.asyncio
    async def test_update_access_token_success(self, db_session, service, unique_email):
        user_data = CreateUserModel(name="Token User", email=unique_email, password="password123")
        with patch('src.utils.mailer.Mailer.send_simple_message', new_callable=AsyncMock):
            await service.create_user(db_session, user_data)
            
        creds = AuthCredentials(email=unique_email, password="password123")
        login_resp = await service.login(db_session, creds)
        
        with patch('src.services.auth_service.validate_refresh_token', return_value=True):
            new_access_token = await service.update_access_token(db_session, login_resp.refreshToken)
            
        assert new_access_token is not None
        assert isinstance(new_access_token, str)

    @pytest.mark.asyncio
    async def test_verify_email_success(self, db_session, service, unique_email):
        user_data = CreateUserModel(name="Verify User", email=unique_email, password="password123")
        with patch('src.utils.mailer.Mailer.send_simple_message', new_callable=AsyncMock):
            user = await service.create_user(db_session, user_data)
            

        user_id = user.id
            
        with patch('src.services.auth_service.decode_jwt', return_value={"sub": str(user_id)}):
            await service.verify_email(db_session, "fake_valid_token")
            

        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await db_session.execute(stmt)
        updated_user = result.scalar_one()
        
        assert updated_user.isVerified is True