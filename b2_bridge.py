"""
Bridge Design Pattern
"""
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from unittest.mock import Mock
import pytest


# === Exceptions ===
class InvalidProviderError(Exception):
    ...


class NativeSchedulingUnsupported(Exception):
    ...


# === Providers ===

class Provider(ABC):

    @abstractmethod
    def send(self, recipient: str, message: str) -> str:
        ...


class SchedulableProvider(Provider):

    @abstractmethod
    def send_at(self, recipient: str, message: str, send_time: datetime) -> str:
        ...


class EmailProvider(Provider):
    ...


class SMSProvider(Provider):
    ...


class PushProvider(Provider):
    ...


class SendGridProvider(EmailProvider):

    def send(self, recipient: str, message: str):
        return f"SendGrid send: {recipient=} {message=}"


class TwilioProvider(SMSProvider, SchedulableProvider):

    def send(self, recipient: str, message: str):
        return f"Twilio send: {recipient=} {message=}"

    def send_at(self, recipient: str, message: str, send_time: datetime):
        return f"Twilio send_at: {recipient=} {message=} {send_time=}"


class FirebaseProvider(PushProvider, SchedulableProvider):

    def send(self, recipient: str, message: str):
        return f"Firebase send: {recipient=} {message=}"

    def send_at(self, recipient: str, message: str, send_time: datetime):
        return f"Firebase send_at: {recipient=} {message=} {send_time=}"


# === Notifications ===

class Notification:
    VALID_PROVIDERS = ()

    def __init__(self, provider: Provider):
        self.provider = provider
        self.validate_provider()

    def validate_provider(self):
        if not isinstance(self.provider, self.VALID_PROVIDERS):
            raise InvalidProviderError

    def notify(self, recipient: str, message: str) -> str:
        result = "notify now ...\n"
        result += self.provider.send(recipient, message)
        return result


class EmailNotification(Notification):
    VALID_PROVIDERS = (EmailProvider,)


class SMSNotification(Notification):
    VALID_PROVIDERS = (SMSProvider,)


class PushNotification(Notification):
    VALID_PROVIDERS = (PushProvider,)


# === Scheduling ===

class NotificationScheduler(ABC):
    @abstractmethod
    def schedule(self, notification: Notification, recipient: str, message: str, send_time: datetime) -> str:
        ...


class NativeNotificationScheduler(NotificationScheduler):
    def schedule(self, notification: Notification, recipient: str, message: str, send_time: datetime) -> str:
        if not isinstance(notification.provider, SchedulableProvider):
            raise NativeSchedulingUnsupported
        result = "Use native scheduling ...\n"
        result += notification.provider.send_at(recipient, message, send_time)
        return result


class CeleryNotificationScheduler(NotificationScheduler):
    def schedule(self, notification: Notification, recipient: str, message: str, send_time: datetime) -> str:
        result = f"Notification will send at: {send_time} ...\n"
        # TODO: Use Celery in real project. This is a practice code
        # send_notification.apply_async(
        #     args=[notification_id, recipient, message],
        #     eta=send_time,
        # )
        return result


class SchedulingManager:

    def __init__(self, native_scheduler: NotificationScheduler, external_scheduler: NotificationScheduler):
        self.native_scheduler = native_scheduler
        self.external_scheduler = external_scheduler

    def schedule(self, notification: Notification, recipient: str, message: str, send_time: datetime) -> str:
        if isinstance(notification.provider, SchedulableProvider):
            return self.native_scheduler.schedule(notification, recipient, message, send_time)
        else:
            return self.external_scheduler.schedule(notification, recipient, message, send_time)

    def force_external_schedule(
            self, notification: Notification, recipient: str, message: str, send_time: datetime
    ) -> str:
        return self.external_scheduler.schedule(notification, recipient, message, send_time)


# === Tests ===

class TestNotification:
    def test_invalid_provider(self):
        with pytest.raises(InvalidProviderError):
            PushNotification(SendGridProvider())

    def test_notify(self):
        recipient = "+989123456789"
        message = "Hello"
        provider = SendGridProvider()
        notification = EmailNotification(provider)
        result = notification.notify(recipient, message)
        assert result == f"notify now ...\nSendGrid send: {recipient=} {message=}"

    def test_native_schedule(self):
        recipient = "abc123"
        message = "Hello"
        provider = FirebaseProvider()
        notification = PushNotification(provider)
        send_time = datetime.now() + timedelta(hours=1)
        result = SchedulingManager(
            NativeNotificationScheduler(),
            CeleryNotificationScheduler()
        ).schedule(notification, recipient, message, send_time)
        assert result == f"Use native scheduling ...\nFirebase send_at: {recipient=} {message=} {send_time=}"

    def test_force__external_schedule(self):
        recipient = "abc123"
        message = "Hello"
        provider = FirebaseProvider()
        provider.send = Mock(return_value="sent")
        notification = PushNotification(provider)
        send_time = datetime.now() + timedelta(hours=1)
        result = SchedulingManager(
            NativeNotificationScheduler(),
            CeleryNotificationScheduler()
        ).force_external_schedule(notification, recipient, message, send_time)
        provider.send.assert_not_called()
        assert result == f"Notification will send at: {send_time} ...\n"

    def test_unsupported_native_scheduling(self):
        notification = EmailNotification(SendGridProvider())
        recipient = "abc@def.com"
        message = "Hello"
        send_time = datetime.now() + timedelta(hours=1)
        with pytest.raises(NativeSchedulingUnsupported):
            NativeNotificationScheduler().schedule(notification, recipient, message, send_time)

    def test_external_schedule(self):
        recipient = "abc@def.com"
        message = "Hello"
        provider = SendGridProvider()
        provider.send = Mock(return_value="sent")
        notification = EmailNotification(provider)
        send_time = datetime.now() + timedelta(hours=1)
        result = SchedulingManager(
            NativeNotificationScheduler(),
            CeleryNotificationScheduler()
        ).schedule(notification, recipient, message, send_time)
        provider.send.assert_not_called()
        assert result == f"Notification will send at: {send_time} ...\n"


# === main ===

if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
