import os
import httpx

from src.config import Settings

settings = Settings()

class Mailer:
    """Mail delivery helper for sending emails through Mailgun."""

    @staticmethod
    async def send_simple_message(
        subject: str,
        sender: str,
        recipient: str,
        text: str | None = None,
        html: str | None = None,
    ):
        """Send plain text or HTML email via Mailgun."""
        data = {
            "from": sender,
            "to": recipient,
            "subject": subject,
        }

        if text:
            data["text"] = text
        if html:
            data["html"] = html

        api_key = os.getenv("API_KEY", settings.mailgun.API_KEY)
        
        if not api_key:
            raise ValueError("Mailgun API key is missing")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mailgun.net/v3/sandbox1d80231ac1fc46af98bb0318e730838a.mailgun.org/messages",
                auth=("api", api_key),
                data=data,
            )
            response.raise_for_status()
            return response