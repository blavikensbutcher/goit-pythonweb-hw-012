import pytest
import uuid
from datetime import date, timedelta
from fastapi import HTTPException

from src.services.contacts import ContactsService
from src.types.contact import ContactDto, UpdateContactDto
from src.models.user import UserModel
from src.utils.auth import hash_password

class TestContactsService:
    @pytest.fixture
    async def test_user_id(self, db_session):
        # We must create a real user in the test database first to satisfy the Foreign Key constraint
        user_id = uuid.uuid4()
        user = UserModel(
            id=user_id,
            email=f"contact-owner-{user_id.hex}@example.com",
            password=hash_password("password123"),
            name="Contact Owner",
            isVerified=True,
            accessToken="fake_token",
            refreshToken="fake_refresh"
        )
        db_session.add(user)
        await db_session.commit()
        return user_id
        
    @pytest.fixture
    def contact_dto(self):
        # Generate a unique email for every test to avoid UniqueViolationError
        unique_email = f"john.doe+{uuid.uuid4().hex}@example.com"
        return ContactDto(
            first_name="John",
            last_name="Doe",
            email=unique_email,
            phone="1234567890",
            birthday=date.today(),
            additional_info="Test info"
        )

    @pytest.mark.asyncio
    async def test_create_contact(self, db_session, contact_dto, test_user_id):
        # test_user_id is already the resolved UUID object from the fixture
        contact = await ContactsService.create_contact(db_session, contact_dto, test_user_id)
        
        assert contact.id is not None
        assert contact.first_name == "John"
        assert contact.email == contact_dto.email
        assert contact.user_id == test_user_id

    @pytest.mark.asyncio
    async def test_get_contacts_filters(self, db_session, contact_dto, test_user_id):
        await ContactsService.create_contact(db_session, contact_dto, test_user_id)
        
        contacts_by_name = await ContactsService.get_contacts(db_session, name="John")
        assert len(contacts_by_name) >= 1
        assert contacts_by_name[-1].first_name == "John"

    @pytest.mark.asyncio
    async def test_get_contact_by_id_success(self, db_session, contact_dto, test_user_id):
        created_contact = await ContactsService.create_contact(db_session, contact_dto, test_user_id)
        
        found_contact = await ContactsService.get_contact_by_id(db_session, str(created_contact.id))
        assert found_contact.id == created_contact.id

    @pytest.mark.asyncio
    async def test_get_contact_by_id_not_found(self, db_session):
        fake_id = str(uuid.uuid4())
        with pytest.raises(HTTPException) as exc:
            await ContactsService.get_contact_by_id(db_session, fake_id)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_contact_success(self, db_session, contact_dto, test_user_id):
        contact = await ContactsService.create_contact(db_session, contact_dto, test_user_id)
        
        update_data = UpdateContactDto(first_name="Jane", additional_info="Updated info")
        updated_contact = await ContactsService.update_contact(db_session, str(contact.id), update_data, test_user_id)
        
        assert updated_contact.first_name == "Jane"
        assert getattr(updated_contact, "additional_info", None) in ("Updated info", None)

    @pytest.mark.asyncio
    async def test_update_contact_not_found(self, db_session, test_user_id):
        update_data = UpdateContactDto(first_name="Jane")
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(HTTPException) as exc:
            await ContactsService.update_contact(db_session, fake_id, update_data, test_user_id)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_remove_contact_success(self, db_session, contact_dto, test_user_id):
        contact = await ContactsService.create_contact(db_session, contact_dto, test_user_id)
        
        result = await ContactsService.remove_contact_by_id(db_session, str(contact.id), test_user_id)
        assert result is True
        
        with pytest.raises(HTTPException):
            await ContactsService.get_contact_by_id(db_session, str(contact.id))

    @pytest.mark.asyncio
    async def test_remove_contact_not_found(self, db_session, test_user_id):
        fake_id = str(uuid.uuid4())
        
        with pytest.raises(HTTPException) as exc:
            await ContactsService.remove_contact_by_id(db_session, fake_id, test_user_id)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_find_contacts_birthday_in_week(self, db_session, contact_dto, test_user_id):
        await ContactsService.create_contact(db_session, contact_dto, test_user_id)
        
        birthdays = await ContactsService.find_contacts_birthday_in_week(db_session)
        assert isinstance(birthdays, list)