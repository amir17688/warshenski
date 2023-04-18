from typing import Any, Dict, Iterator, TypeVar

from typing_extensions import Protocol

T = TypeVar("T")


class SupportsSubQuery(Protocol):
    def __iter__(self) -> "Iterator[IRow]":
        ...


class SupportsFiltering(Protocol):
    def filter(self, expression: bool) -> bool:
        ...


class IRow(SupportsFiltering, SupportsSubQuery, Protocol):
    def __getattr__(self, name: str) -> Any:
        ...


class IQueryManager(Protocol):
    def __iter__(self) -> Iterator[IRow]:
        ...


class ISpy(IRow, Protocol):
    selected_fields: "Dict[str, ISpy]"
    is_subquery: bool


class IQueryModel(Protocol):
    name: str


class IQueryClient(Protocol):
    def query(self, query_string: str) -> Iterator[IRow]:
        ...
