import pytest
from unittest.mock import Mock, patch
from src.utils.mailer import Mailer

class TestMailer:
    @pytest.mark.asyncio
    @patch("src.utils.mailer.os.getenv")
    @patch("httpx.AsyncClient")
    async def test_send_simple_message(self, mock_client, mock_getenv):
        mock_getenv.return_value = "fake_test_key"
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        await Mailer.send_simple_message(
            subject="Test",
            sender="test@example.com",
            recipient="recipient@example.com",
            text="Hello"
        )

        mock_client.return_value.__aenter__.return_value.post.assert_called_once()