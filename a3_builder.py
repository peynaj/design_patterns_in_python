"""
Builder

Structure:
1. Builder interface
2. Concrete builders
3. Products: result of concrete builders
4. Director: order in call of construction steps
5. Client: pass builder instance to director
"""

import re
import pytest
from datetime import datetime, timedelta


class Email:
    to: str
    subject: str
    text: str | None
    html: str | None
    attachments: list[str]
    cc: list[str] | None
    bcc: list[str] | None
    scheduled_at: datetime | None

    def __init__(self, to: str, subject: str):
        self.to = to
        self.subject = subject
        self.text = None
        self.html = None
        self.attachments = []
        self.cc = None
        self.bcc = None
        self.scheduled_at = None


class EmailBuilder:
    email: Email

    def __init__(self, to: str, subject: str):
        self._validate_email_address(to)
        self.email = Email(to, subject)

    def set_text(self, text: str) -> "EmailBuilder":
        self.email.text = text
        return self

    def set_html(self, html: str) -> "EmailBuilder":
        self.email.html = html
        return self

    def add_attachment(self, file: str) -> "EmailBuilder":
        self.email.attachments.append(file)
        return self

    def set_cc(self, cc: list[str]) -> "EmailBuilder":
        for email in cc:
            self._validate_email_address(email)
        self.email.cc = cc.copy()
        return self

    def set_bcc(self, bcc: list[str]) -> "EmailBuilder":
        for email in bcc:
            self._validate_email_address(email)
        self.email.bcc = bcc.copy()
        return self

    def schedule(self, scheduled_at: datetime) -> "EmailBuilder":
        if scheduled_at <= datetime.now():
            raise ValueError("scheduled_at can not be past time")
        self.email.scheduled_at = scheduled_at
        return self

    def _validate(self):
        email = self.email
        if not (email.text or email.html):
            raise ValueError("one of text or html is required")

    def _create_product(self) -> Email:
        email = self.email
        result = Email(email.to, email.subject)
        result.text = email.text
        result.html = email.html
        result.attachments = email.attachments.copy()
        result.cc = email.cc.copy() if email.cc is not None else None
        result.bcc = email.bcc.copy() if email.bcc is not None else None
        result.scheduled_at = email.scheduled_at
        return result

    def build(self) -> Email:
        self._validate()
        return self._create_product()

    @staticmethod
    def _validate_email_address(email):
        pattern = r'[A-Za-z0-9]+@[\w]+\.[\w]+'
        if not re.fullmatch(pattern, email):
            raise ValueError("Invalid email address")


class TestEmailBuilder:

    def test_build_valid_email(self):
        email = (
            EmailBuilder("user@example.com", "Welcome")
            .set_text("Hello!")
            .add_attachment("guide.pdf")
            .build()
        )

        assert email.to == "user@example.com"
        assert email.subject == "Welcome"
        assert email.text == "Hello!"
        assert email.html is None
        assert email.attachments == ["guide.pdf"]
        assert email.cc is None
        assert email.bcc is None
        assert email.scheduled_at is None

    def test_invalid_recipient(self):
        with pytest.raises(ValueError, match="Invalid email address"):
            EmailBuilder("user", "Welcome")

    def test_invalid_cc(self):
        with pytest.raises(ValueError, match="Invalid email address"):
            EmailBuilder("user@example.com", "Welcome").set_cc(["user2"])

    def test_build_without_content(self):
        with pytest.raises(
                ValueError,
                match="one of text or html is required",
        ):
            EmailBuilder("user@example.com", "Welcome").build()

    def test_schedule_in_past(self):
        with pytest.raises(
                ValueError,
                match="scheduled_at can not be past time",
        ):
            (
                EmailBuilder("user@example.com", "Welcome")
                .set_text("Hello!")
                .schedule(datetime.now() - timedelta(hours=1))
            )

    def test_build_creates_independent_products(self):
        builder = (
            EmailBuilder("a@example.com", "Welcome")
            .set_text("First message")
            .add_attachment("guide.pdf")
        )

        email1 = builder.build()
        email2 = builder.set_text("Second message").build()

        assert email1 is not email2
        assert email1.text == "First message"
        assert email2.text == "Second message"

        assert email1.attachments == ["guide.pdf"]
        assert email2.attachments == ["guide.pdf"]

        email1.attachments.append("other.pdf")
        assert email2.attachments == ["guide.pdf"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
