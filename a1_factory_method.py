"""
Factory Method

Structure:
1. Product: Abstract interface superclass for concrete products
2. Creator: Abstract interface superclass for concrete creators
3. Concrete Products: Implementation of products operations
4. Concrete Creators: Create instances of products
"""
import logging
from abc import ABC, abstractmethod


# Product abstraction
class Sender(ABC):

    @abstractmethod
    def send(self, message: str):
        ...


# Creator abstraction
class SenderCreator(ABC):

    @abstractmethod
    def factory(self) -> Sender:
        ...

    def send(self, message: str) -> None:
        try:
            self.validate_message(message)
        except RuntimeError as ex:
            print(f"Validate Failed: {ex}")
            return

        sender = self.factory()
        print("Start to send ...")
        sender.send(message)
        self.log(message)

    @staticmethod
    def validate_message(message: str):
        print(f"Validate ... {message=}")
        if not (message.startswith("Hello") or message.startswith("Hi")):
            raise RuntimeError("Message should start with Hello or Hi.")

    @staticmethod
    def log(message: str):
        logging.log(f"Log message ... {message=}")


# Concrete products and Concrete creators
class EmailSender(Sender):
    def send(self, message: str):
        print(f"send email. {message=}")


class EmailCreator(SenderCreator):
    def factory(self):
        return EmailSender()


class SMSSender(Sender):
    def send(self, message: str):
        print(f"send SMS. {message=}")


class SMSCreator(SenderCreator):
    def factory(self):
        return SMSSender()


class PushSender(Sender):
    def send(self, message: str):
        print(f"send Push. {message=}")


class PushCreator(SenderCreator):
    def factory(self):
        return PushSender()


# Use products and creators
def client_code(creator: SenderCreator, message: str):
    creator.send(message)


print("Use Email:")
client_code(EmailCreator(), "Hello Peyman ...")

print("Use SMS:")
client_code(SMSCreator(), "Hi Peyman ...")

print("Use Push:")
client_code(PushCreator(), "Hi Peyman ...")
