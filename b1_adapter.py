"""
Adapter (Wrapper)
"""
import asyncio
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pytest
from requests.exceptions import Timeout
import re


# Providers:

class EmailProvider:
    def send_email(self, email, subject, body):
        return {
            "status": "sent",
            "email_id": "EMAIL-123"
        }


class SMSProvider:
    def send_sms(self, phone_number, message):
        return {
            "status_code": 200,
            "tracking_code": "SMS-456"
        }


class TelegramProvider:
    async def send_message(self, chat_id, text):
        return {
            "ok": True,
            "message_id": 789
        }


# Client:

@dataclass
class NotificationResult:
    success: bool
    tracking_id: str | None
    provider: str


class NotificationError(Exception):
    ...


class NotificationTimeoutError(NotificationError):
    ...


class InvalidRecipientError(NotificationError):
    ...


class NotificationSender(ABC):

    @abstractmethod
    async def send(
            self,
            recipient: str,
            content: str
    ) -> NotificationResult:
        pass


# Providers:

class EmailProviderAdapter(NotificationSender):

    def __init__(self, provider: EmailProvider):
        self.provider = provider

    @staticmethod
    def get_subject(content: str) -> str:
        return content[:32]

    @staticmethod
    def validate_recipient(recipient: str):
        pattern = r'[A-Za-z0-9]+@[\w]+\.[\w]+'
        if not re.fullmatch(pattern, recipient):
            raise InvalidRecipientError

    async def send(
            self,
            recipient: str,
            content: str
    ) -> NotificationResult:
        self.validate_recipient(recipient)

        subject = self.get_subject(content)

        try:
            email_result = await asyncio.to_thread(
                self.provider.send_email, email=recipient, subject=subject, body=content
            )

        except Timeout as ex:
            raise NotificationTimeoutError from ex
        except Exception as ex:
            traceback.print_exc()
            raise NotificationError from ex

        return NotificationResult(
            success=email_result.get("status") == "sent",
            tracking_id=str(email_result.get("email_id")) if "email_id" in email_result else None,
            provider="email",
        )


class SMSProviderAdapter(NotificationSender):

    def __init__(self, provider: SMSProvider):
        self.provider = provider

    @staticmethod
    def validate_recipient(recipient: str):
        if not (
                recipient.startswith("+98")
                and len(recipient) == 13
                and recipient[3:].isdigit()
        ):
            raise InvalidRecipientError

    async def send(
            self,
            recipient: str,
            content: str
    ) -> NotificationResult:
        self.validate_recipient(recipient)

        try:
            sms_result = await asyncio.to_thread(self.provider.send_sms, phone_number=recipient, message=content)
        except Timeout as ex:
            raise NotificationTimeoutError from ex
        except Exception as ex:
            traceback.print_exc()
            raise NotificationError from ex

        return NotificationResult(
            success=sms_result.get("status_code", False) == 200,
            tracking_id=str(sms_result.get("tracking_code")) if "tracking_code" in sms_result else None,
            provider="sms",
        )


class TelegramProviderAdapter(NotificationSender):

    def __init__(self, provider: TelegramProvider):
        self.provider = provider

    @staticmethod
    def validate_recipient(recipient: str):
        if not recipient.removeprefix("-").isdigit():
            raise InvalidRecipientError

    async def send(
            self,
            recipient: str,
            content: str
    ) -> NotificationResult:
        self.validate_recipient(recipient)

        try:
            message_result = await self.provider.send_message(chat_id=recipient, text=content)
        except (Timeout, asyncio.TimeoutError) as ex:
            raise NotificationTimeoutError from ex
        except Exception as ex:
            traceback.print_exc()
            raise NotificationError from ex

        return NotificationResult(
            success=message_result.get("ok", False),
            tracking_id=str(message_result.get("message_id")) if "message_id" in message_result else None,
            provider="telegram",
        )


# Client

class NotificationService:

    def __init__(self, sender: NotificationSender):
        self.sender = sender

    async def notify(self, recipient: str, content: str) -> NotificationResult:
        return await self.sender.send(recipient, content)


# Test

class TimeoutEmailProvider(EmailProvider):
    def send_email(self, email, subject, body):
        from requests.exceptions import Timeout
        raise Timeout("Email provider timeout")


class FailedTelegramProvider(TelegramProvider):
    async def send_message(self, chat_id, text):
        raise asyncio.TimeoutError("Telegram timeout")


class BrokenSMSProvider(SMSProvider):
    def send_sms(self, phone_number, message):
        raise RuntimeError("Unexpected provider error")


class TestNotificationService:

    @pytest.mark.asyncio
    async def test_success_email(self):
        provider = EmailProvider()
        sender = EmailProviderAdapter(provider)
        service = NotificationService(sender)
        result = await service.notify(
            recipient="user@example.com",
            content="Hello!"
        )
        assert isinstance(result, NotificationResult)
        assert result.success
        assert result.tracking_id == "EMAIL-123", result.tracking_id
        assert result.provider == "email", result.provider

    @pytest.mark.asyncio
    async def test_invalid_email(self):
        provider = EmailProvider()
        sender = EmailProviderAdapter(provider)
        service = NotificationService(sender)
        with pytest.raises(InvalidRecipientError):
            await service.notify(
                recipient="invalid_email_address",
                content="Hello!"
            )

    @pytest.mark.asyncio
    async def test_success_sms(self):
        provider = SMSProvider()
        sender = SMSProviderAdapter(provider)
        service = NotificationService(sender)
        result = await service.notify(
            recipient="+989123456789",
            content="Hello!"
        )
        assert isinstance(result, NotificationResult)
        assert result.success
        assert result.tracking_id == "SMS-456", result.tracking_id
        assert result.provider == "sms", result.provider

    @pytest.mark.asyncio
    async def test_invalid_phone(self):
        provider = SMSProvider()
        sender = SMSProviderAdapter(provider)
        service = NotificationService(sender)
        with pytest.raises(InvalidRecipientError):
            await service.notify(
                recipient="09123456789",
                content="Hello!"
            )

    @pytest.mark.asyncio
    async def test_success_telegram(self):
        provider = TelegramProvider()
        sender = TelegramProviderAdapter(provider)
        service = NotificationService(sender)
        result = await service.notify(
            recipient="123",
            content="Hello!"
        )
        assert isinstance(result, NotificationResult)
        assert result.success
        assert result.tracking_id == "789", result.tracking_id
        assert result.provider == "telegram", result.provider

    @pytest.mark.asyncio
    async def test_invalid_telegram_chat(self):
        provider = TelegramProvider()
        sender = TelegramProviderAdapter(provider)
        service = NotificationService(sender)
        with pytest.raises(InvalidRecipientError):
            await service.notify(
                recipient="my-channel",
                content="Hello!"
            )

    # -------------------------
    # Provider Failure Tests
    # -------------------------

    @pytest.mark.asyncio
    async def test_email_timeout(self):
        adapter = EmailProviderAdapter(TimeoutEmailProvider())

        with pytest.raises(NotificationTimeoutError):
            await adapter.send("user@example.com", "Hello!")

    @pytest.mark.asyncio
    async def test_telegram_timeout(self):
        adapter = TelegramProviderAdapter(FailedTelegramProvider())

        with pytest.raises(NotificationTimeoutError):
            await adapter.send("123456789", "Hello!")

    @pytest.mark.asyncio
    async def test_sms_unexpected_error(self):
        adapter = SMSProviderAdapter(BrokenSMSProvider())

        with pytest.raises(NotificationError) as exc_info:
            await adapter.send("+989121234567", "Hello!")

        assert isinstance(exc_info.value.__cause__, RuntimeError)

    # -------------------------
    # Dependency Injection Test
    # -------------------------

    @pytest.mark.asyncio
    async def test_notification_service_accepts_different_adapters(self):
        email_service = NotificationService(
            EmailProviderAdapter(EmailProvider())
        )

        sms_service = NotificationService(
            SMSProviderAdapter(SMSProvider())
        )

        email_result = await email_service.notify(
            "user@example.com",
            "Hello!"
        )

        sms_result = await sms_service.notify(
            "+989121234567",
            "Hello!"
        )

        assert email_result.provider == "email"
        assert sms_result.provider == "sms"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
