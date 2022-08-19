from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

T = TypeVar("T")


class HasJsonReads(Generic[T], ABC):
    @staticmethod
    @abstractmethod
    def read_from_json(json: dict[str, Any]) -> T:
        pass


class HasJsonWrites(ABC):
    @abstractmethod
    def write_json(self) -> dict[str, Any]:
        pass


class HasJsonFormat(Generic[T], HasJsonReads[T], HasJsonWrites, ABC):
    pass
