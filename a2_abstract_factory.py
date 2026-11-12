"""
Abstract Factory

Structure:
1. Abstract Products: Interface for products
2. Concrete Products: Implementation of products
3. Abstract Factories: Interface for factories
4. Concrete Factories: Create and instantiate related products in a family
5. Client (Service): Use needed factory

"""
from abc import ABC, abstractmethod


class AbstractFileStorage(ABC):

    @abstractmethod
    def save(self, file_id: str, content: bytes) -> None:
        ...

    @abstractmethod
    def get(self, file_id: str) -> bytes | None:
        ...


class AbstractStorageMetadata(ABC):

    @abstractmethod
    def save_metadata(self, file_id: str, size: int) -> None:
        ...

    @abstractmethod
    def get_metadata(self, file_id: str) -> int | None:
        ...


class AbstractStorageFactory(ABC):

    @abstractmethod
    def create_file_storage(self) -> AbstractFileStorage:
        ...

    @abstractmethod
    def create_storage_metadata(self) -> AbstractStorageMetadata:
        ...


class LocalFileStorage(AbstractFileStorage):
    all_contents = {}

    def save(self, file_id: str, content: bytes) -> None:
        print(f"LocalFileStorage save {file_id=} {content=}")
        self.all_contents[file_id] = content

    def get(self, file_id: str) -> bytes | None:
        print(f"LocalFileStorage get {file_id=}")
        return self.all_contents.get(file_id)


class LocalStorageMetadata(AbstractStorageMetadata):
    all_metadata = {}

    def save_metadata(self, file_id: str, size: int) -> None:
        print(f"LocalStorageMetadata save_metadata {file_id=} {size}")
        self.all_metadata[file_id] = size

    def get_metadata(self, file_id: str) -> int | None:
        print(f"LocalStorageMetadata get_metadata {file_id=}")
        return self.all_metadata.get(file_id)


class LocalFactory(AbstractStorageFactory):

    def create_file_storage(self) -> AbstractFileStorage:
        return LocalFileStorage()

    def create_storage_metadata(self) -> AbstractStorageMetadata:
        return LocalStorageMetadata()


class CloudFileStorage(AbstractFileStorage):
    all_contents = {}

    def save(self, file_id: str, content: bytes) -> None:
        print(f"CloudFileStorage save {file_id=} {content=}")
        self.all_contents[file_id] = content

    def get(self, file_id: str) -> bytes | None:
        print(f"CloudFileStorage get {file_id=}")
        return self.all_contents.get(file_id)


class CloudStorageMetadata(AbstractStorageMetadata):
    all_metadata = {}

    def save_metadata(self, file_id: str, size: int) -> None:
        print(f"CloudStorageMetadata save_metadata {file_id=} {size}")
        self.all_metadata[file_id] = size

    def get_metadata(self, file_id: str) -> int | None:
        print(f"CloudStorageMetadata get_metadata {file_id=}")
        return self.all_metadata.get(file_id)


class CloudFactory(AbstractStorageFactory):

    def create_file_storage(self) -> AbstractFileStorage:
        return CloudFileStorage()

    def create_storage_metadata(self) -> AbstractStorageMetadata:
        return CloudStorageMetadata()


class FileService:

    def __init__(self, storage_factory: AbstractStorageFactory):
        self.storage_factory = storage_factory
        self.file_storage = self.storage_factory.create_file_storage()
        self.metadata_storage = self.storage_factory.create_storage_metadata()

    def save_file(self, file_id: str, content: bytes):
        self.file_storage.save(file_id, content)

    def test_storage(self, file_id: str, content: bytes):
        assert self.file_storage.get(file_id) == content

    def save_metadata(self, file_id: str, size: int):
        self.metadata_storage.save_metadata(file_id, size)

    def test_metadata(self, file_id: str, size: int):
        assert self.metadata_storage.get_metadata(file_id) == size

    def save_file_with_metadata(self, file_id: str, content: bytes):
        self.save_file(file_id, content)
        self.save_metadata(file_id, len(content))

    def test_file_and_metadata(self, file_id: str, content: bytes):
        self.test_metadata(file_id, len(content))


print("Use Local Storage ...")
local_file_service = FileService(LocalFactory())
file_id, content = "abc", b"My local content"
local_file_service.save_file_with_metadata(file_id, content)
local_file_service.test_file_and_metadata(file_id, content)

print("=" * 80)

print("Use Cloud Storage ...")
cloud_file_service = FileService(CloudFactory())
file_id, content = "xyz", b"This is my cloud content!"
cloud_file_service.save_file_with_metadata(file_id, content)
cloud_file_service.test_file_and_metadata(file_id, content)
